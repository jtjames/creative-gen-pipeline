"""
Orchestrator Agent for creative generation pipeline.

Coordinates the multi-step process of generating creative assets:
1. Load campaign brief
2. Generate missing product images using GenAI
3. Expand images to multiple aspect ratios
4. Apply templates and branding
5. Run compliance checks
6. Store artifacts and reports
"""

from __future__ import annotations

import time
from typing import Any, Dict
from datetime import datetime, timezone

from .briefs import BriefService
from .storage import DropboxStorage
from .models import CampaignBrief, Product
from .genai_providers import select_genai_client, GenAIClient
from .config import Settings, get_settings
from .assets import needs_generation
from .generation_logs import GenerationLogService


class OrchestratorAgent:
    """Orchestrates the creative generation pipeline."""

    def __init__(
        self,
        brief_service: BriefService,
        storage: DropboxStorage,
        settings: Settings | None = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            brief_service: Service for managing briefs
            storage: Dropbox storage adapter
            settings: Application settings
        """
        self.brief_service = brief_service
        self.storage = storage
        self.settings = settings or get_settings()
        self.log_service = GenerationLogService(storage)

    async def generate_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Generate all creative assets for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Generation report with artifact paths and metadata

        Raises:
            ValueError: If brief not found or invalid
            RuntimeError: If generation fails
        """
        # Update status to processing
        self.brief_service.update_brief_status(campaign_id, "processing")

        start_time = time.time()
        products_generated = 0

        try:
            # Load campaign brief
            brief = self.brief_service.get_brief(campaign_id)
            if not brief:
                raise ValueError(f"Brief not found: {campaign_id}")

            # Log campaign start with asset completeness check
            start_log = self.log_service.log_campaign_start(campaign_id, brief)

            # Generate missing product images
            products_generated = await self._generate_missing_images(campaign_id, brief)

            # Reload brief to get updated image paths
            brief = self.brief_service.get_brief(campaign_id)
            if not brief:
                raise ValueError(f"Brief not found after generation: {campaign_id}")

            # Calculate total creatives to generate
            total_creatives = len(brief.products) * len(brief.locales) * len(brief.aspect_ratios)
            total_duration = time.time() - start_time

            # Log campaign completion with final asset status
            completion_log = self.log_service.log_campaign_complete(
                campaign_id, brief, products_generated, total_duration
            )

            # For now, just update status to completed
            # Full template/rendering pipeline will be added later
            self.brief_service.update_brief_status(campaign_id, "completed")

            return {
                "campaign_id": campaign_id,
                "status": "completed",
                "products_processed": len(brief.products),
                "products_generated": products_generated,
                "total_creatives": total_creatives,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": round(total_duration, 2),
                "asset_status": completion_log["final_asset_status"],
            }

        except Exception as exc:
            # Mark as failed
            self.brief_service.update_brief_status(campaign_id, "failed")
            raise RuntimeError(f"Campaign generation failed: {str(exc)}") from exc

    async def _generate_missing_images(
        self, campaign_id: str, brief: CampaignBrief
    ) -> int:
        """
        Generate images for products that don't have uploaded images.

        Args:
            campaign_id: Campaign identifier
            brief: Campaign brief with products

        Returns:
            Number of products that had images generated

        Raises:
            RuntimeError: If image generation fails
        """
        genai_client = select_genai_client(self.settings)

        campaign_folder = f"/briefs/{campaign_id}"
        assets_folder = f"{campaign_folder}/assets"

        generated_count = 0

        # Generate images for products marked as pending
        for product in brief.products:
            if needs_generation(product.image_path):
                await self._generate_product_image(
                    campaign_id, genai_client, product, assets_folder
                )
                generated_count += 1

        # Update the brief with new image paths
        brief_json = brief.model_dump_json(indent=2)
        brief_path = f"{campaign_folder}/brief.json"
        self.storage.upload_bytes(
            path=brief_path,
            data=brief_json.encode("utf-8"),
        )

        return generated_count

    async def _generate_product_image(
        self,
        campaign_id: str,
        genai_client: GenAIClient,
        product: Product,
        assets_folder: str,
    ) -> None:
        """
        Generate a single product image using GenAI.

        Args:
            campaign_id: Campaign identifier
            genai_client: Configured GenAI image client
            product: Product to generate image for
            assets_folder: Folder to store generated image

        Raises:
            RuntimeError: If generation fails
        """
        # Determine model name
        model_name = getattr(genai_client, "DEFAULT_OPENAI_IMAGE_MODEL", "unknown")
        if hasattr(genai_client, "_settings") and hasattr(genai_client._settings, "genai_provider"):
            provider = genai_client._settings.genai_provider
            if provider == "openai":
                model_name = "dall-e-3"
            elif provider == "gemini":
                model_name = "gemini-2.0-flash-preview"

        try:
            # Log generation initiated
            self.log_service.log_generation_initiated(
                campaign_id, product, model_name
            )

            start_time = time.time()

            # Generate image using product prompt
            artifact = await genai_client.generate_image(
                prompt=product.prompt,
                negative_prompt=product.negative_prompt,
                aspect_ratio="1:1",  # Generate square master image
            )

            # Store generated image
            image_path = f"{assets_folder}/{product.id}-generated.png"
            self.storage.upload_image(
                path=image_path,
                data=artifact.image_bytes,
            )

            # Update product image path
            product.image_path = image_path

            duration = time.time() - start_time

            # Log generation completed
            self.log_service.log_generation_completed(
                campaign_id, product, model_name, image_path, duration
            )

        except Exception as exc:
            # Log generation failed
            self.log_service.log_generation_failed(
                campaign_id, product, str(exc)
            )
            raise RuntimeError(
                f"Failed to generate image for product {product.id}: {str(exc)}"
            ) from exc


async def run_campaign_generation(
    campaign_id: str,
    brief_service: BriefService,
    storage: DropboxStorage,
    settings: Settings | None = None,
) -> Dict[str, Any]:
    """
    Run campaign generation (convenience function).

    Args:
        campaign_id: Campaign identifier
        brief_service: Brief service instance
        storage: Storage instance
        settings: Application settings

    Returns:
        Generation report
    """
    orchestrator = OrchestratorAgent(brief_service, storage, settings)
    return await orchestrator.generate_campaign(campaign_id)
