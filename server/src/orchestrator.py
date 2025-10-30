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
from .image_processing import overlay_logo_on_image
from .logo_analysis import analyze_logo, create_logo_enhanced_prompt


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
        # Check if logo is available for image-to-image generation
        has_logo = (
            brief.brand
            and brief.brand.logo_path
            and not needs_generation(brief.brand.logo_path)
        )

        # Use Gemini for image-to-image when logo is present
        # Gemini supports multimodal input (image + text), OpenAI DALL-E 3 does not
        if has_logo:
            from .gemini import GeminiClient
            print("Logo detected - using Gemini for image-to-image generation")
            genai_client = GeminiClient(self.settings)
        else:
            genai_client = select_genai_client(self.settings)

        campaign_folder = f"/briefs/{campaign_id}"
        assets_folder = f"{campaign_folder}/assets"

        # Download and analyze logo if available
        logo_bytes = None
        logo_analysis = None
        if brief.brand and brief.brand.logo_path and not needs_generation(brief.brand.logo_path):
            try:
                logo_bytes = self.storage.download_bytes(brief.brand.logo_path)
                # Analyze logo to extract visual characteristics
                logo_analysis = analyze_logo(logo_bytes)
                print(f"Logo analysis: {logo_analysis['style_description']}")
                print(f"Dominant colors: {[c for c, _ in logo_analysis['dominant_colors'][:3]]}")
            except Exception as exc:
                # Log warning but continue without logo
                print(f"Warning: Could not download/analyze logo: {exc}")

        generated_count = 0

        # Generate images for products marked as pending
        for product in brief.products:
            if needs_generation(product.image_path):
                await self._generate_product_image(
                    campaign_id, genai_client, product, assets_folder, logo_bytes, brief, logo_analysis
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
        logo_bytes: bytes | None = None,
        brief: CampaignBrief | None = None,
        logo_analysis: dict | None = None,
    ) -> None:
        """
        Generate a single product image using GenAI.

        Args:
            campaign_id: Campaign identifier
            genai_client: Configured GenAI image client
            product: Product to generate image for
            assets_folder: Folder to store generated image
            logo_bytes: Optional brand logo to overlay on the generated image
            brief: Campaign brief containing brand information
            logo_analysis: Analysis results from logo (colors, style, etc.)

        Raises:
            RuntimeError: If generation fails
        """
        # Determine model name based on client type
        from .gemini import GeminiClient
        from .openai_image import OpenAIImageClient

        if isinstance(genai_client, GeminiClient):
            model_name = "gemini-2.0-flash-preview-image-generation"
        elif isinstance(genai_client, OpenAIImageClient):
            model_name = "dall-e-3"
        else:
            model_name = "unknown"

        try:
            # Log generation initiated
            self.log_service.log_generation_initiated(
                campaign_id, product, model_name
            )

            start_time = time.time()

            # Enhance prompt with brand identity and logo analysis
            enhanced_prompt = product.prompt

            if logo_analysis:
                # Use logo analysis to create highly detailed brand-aware prompt
                # Pass has_reference_image=True since we're providing logo bytes to the model
                enhanced_prompt = create_logo_enhanced_prompt(
                    product.prompt,
                    logo_analysis,
                    has_reference_image=bool(logo_bytes)
                )
                print(f"Enhanced prompt for {product.id}: {enhanced_prompt[:150]}...")
            elif brief and brief.brand:
                # Fallback to basic brand information if logo analysis not available
                brand_color = brief.brand.primary_hex
                brand_context_parts = []

                if brand_color:
                    brand_context_parts.append(f"featuring brand color {brand_color}")

                if logo_bytes:
                    brand_context_parts.append(
                        "with subtle brand elements or logo visible on the product itself, "
                        "styled as an official branded product photograph"
                    )

                if brand_context_parts:
                    brand_context = ", " + ", ".join(brand_context_parts)
                    enhanced_prompt = f"{product.prompt}{brand_context}"

            # Add call-to-action text to the image (English only for now)
            if brief and brief.cta:
                # Get English CTA (en-US) or first available CTA
                cta_text = brief.cta.get("en-US") or next(iter(brief.cta.values()), None)
                if cta_text:
                    cta_instruction = (
                        f". Include the call-to-action text '{cta_text}' prominently displayed "
                        "in bold, modern typography at the bottom of the image with high contrast "
                        "against the background for readability"
                    )
                    enhanced_prompt = f"{enhanced_prompt}{cta_instruction}"
                    print(f"Including CTA in image: '{cta_text}'")

            # Generate image using enhanced product prompt
            # Pass logo as reference image for visual conditioning (Gemini supports this)
            artifact = await genai_client.generate_image(
                prompt=enhanced_prompt,
                negative_prompt=product.negative_prompt,
                aspect_ratio="1:1",  # Generate square master image
                reference_image_bytes=logo_bytes,  # Logo as visual reference
            )

            # Composite logo on generated image if available
            final_image_bytes = artifact.image_bytes
            if logo_bytes:
                try:
                    final_image_bytes = overlay_logo_on_image(
                        product_image_bytes=artifact.image_bytes,
                        logo_image_bytes=logo_bytes,
                        logo_position="bottom-right",
                        logo_scale=0.15,  # 15% of image width
                        padding=30,
                    )
                except Exception as logo_exc:
                    # Log warning but use image without logo
                    print(f"Warning: Could not overlay logo on {product.id}: {logo_exc}")
                    final_image_bytes = artifact.image_bytes

            # Store generated image (with or without logo)
            image_path = f"{assets_folder}/{product.id}-generated.png"
            self.storage.upload_image(
                path=image_path,
                data=final_image_bytes,
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
