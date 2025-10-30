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
        products_folder = f"{campaign_folder}/products"

        # Download logo if available for use as reference image
        logo_bytes = None
        if brief.brand and brief.brand.logo_path and not needs_generation(brief.brand.logo_path):
            try:
                logo_bytes = self.storage.download_bytes(brief.brand.logo_path)
                print(f"Logo downloaded for image-to-image generation ({len(logo_bytes)} bytes)")
            except Exception as exc:
                # Log warning but continue without logo
                print(f"Warning: Could not download logo: {exc}")

        generated_count = 0

        # Generate images for products marked as pending
        for product in brief.products:
            if needs_generation(product.image_path):
                await self._generate_product_image(
                    campaign_id, genai_client, product, products_folder, logo_bytes, brief
                )
                generated_count += 1

        # Generate aspect ratio variations for products that already have images
        if brief.aspect_ratios and len(brief.aspect_ratios) > 0:
            from .openai_image import OpenAIImageClient
            openai_client = OpenAIImageClient(self.settings)

            for product in brief.products:
                # Skip products that don't have images yet
                if needs_generation(product.image_path):
                    continue

                # Download the existing product image
                try:
                    existing_image_bytes = self.storage.download_bytes(product.image_path)
                    print(f"Generating aspect ratio variations for existing product: {product.id}")

                    # Build the same enhanced prompt that would be used for generation
                    enhanced_prompt = product.prompt or f"Product image for {product.name}"

                    # Add brand context if available
                    if brief.brand:
                        brand_context_parts = []
                        if brief.brand.primary_hex:
                            brand_context_parts.append(f"featuring brand color {brief.brand.primary_hex}")
                        if logo_bytes:
                            brand_context_parts.append(
                                "incorporating the brand logo and visual identity, "
                                "styled as an official branded product photograph"
                            )
                        if brand_context_parts:
                            brand_context = ", " + ", ".join(brand_context_parts)
                            enhanced_prompt = f"{enhanced_prompt}{brand_context}"

                    # Add CTA if available
                    if brief.cta:
                        cta_text = brief.cta.get("en-US") or next(iter(brief.cta.values()), None)
                        if cta_text:
                            cta_instruction = (
                                f". Include the call-to-action text '{cta_text}' prominently displayed "
                                "in bold, modern typography at the bottom of the image with high contrast "
                                "against the background for readability"
                            )
                            enhanced_prompt = f"{enhanced_prompt}{cta_instruction}"

                    product_folder = f"{products_folder}/{product.id}"
                    await self._generate_aspect_ratio_variations(
                        campaign_id,
                        product,
                        enhanced_prompt,
                        existing_image_bytes,
                        brief.aspect_ratios,
                        product_folder,
                        logo_bytes
                    )
                except Exception as exc:
                    print(f"Warning: Could not generate variations for {product.id}: {exc}")

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
        products_folder: str,
        logo_bytes: bytes | None = None,
        brief: CampaignBrief | None = None,
    ) -> None:
        """
        Generate a single product image using GenAI.

        Args:
            campaign_id: Campaign identifier
            genai_client: Configured GenAI image client
            product: Product to generate image for
            products_folder: Base products folder path
            logo_bytes: Optional brand logo to use as reference image
            brief: Campaign brief containing brand information

        Raises:
            RuntimeError: If generation fails
        """
        # Determine model name based on client type
        from .gemini import GeminiClient
        from .openai_image import OpenAIImageClient

        if isinstance(genai_client, GeminiClient):
            model_name = "gemini-2.5-flash-image-preview"
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

            # Build enhanced prompt with brand context and CTA
            enhanced_prompt = product.prompt

            # Add brand context if available
            if brief and brief.brand:
                brand_context_parts = []

                # Add brand color
                if brief.brand.primary_hex:
                    brand_context_parts.append(f"featuring brand color {brief.brand.primary_hex}")

                # Add logo reference instruction if logo is provided
                if logo_bytes:
                    brand_context_parts.append(
                        "incorporating the brand logo and visual identity shown in the reference image, "
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

            # Use the generated image directly (logo incorporated via Gemini reference image)
            final_image_bytes = artifact.image_bytes

            # Store base generated image in products/{product-id}/1-1/
            product_folder = f"{products_folder}/{product.id}"
            aspect_folder_1_1 = f"{product_folder}/1-1"
            base_image_path = f"{aspect_folder_1_1}/{product.id}.png"

            self.storage.upload_image(
                path=base_image_path,
                data=final_image_bytes,
            )

            # Update product image path
            product.image_path = base_image_path

            duration = time.time() - start_time

            # Log generation completed
            self.log_service.log_generation_completed(
                campaign_id, product, model_name, base_image_path, duration
            )

            # Generate additional aspect ratios using OpenAI
            if brief and brief.aspect_ratios:
                await self._generate_aspect_ratio_variations(
                    campaign_id,
                    product,
                    enhanced_prompt,
                    final_image_bytes,
                    brief.aspect_ratios,
                    product_folder,
                    logo_bytes
                )

        except Exception as exc:
            # Log generation failed
            self.log_service.log_generation_failed(
                campaign_id, product, str(exc)
            )
            raise RuntimeError(
                f"Failed to generate image for product {product.id}: {str(exc)}"
            ) from exc

    async def _generate_aspect_ratio_variations(
        self,
        campaign_id: str,
        product: Product,
        prompt: str,
        base_image_bytes: bytes,
        aspect_ratios: list[str],
        product_folder: str,
        logo_bytes: bytes | None = None,
    ) -> None:
        """
        Generate images at different aspect ratios using OpenAI.

        Args:
            campaign_id: Campaign identifier
            product: Product being generated
            prompt: Enhanced prompt used for base generation
            base_image_bytes: Base 1:1 image bytes
            aspect_ratios: List of aspect ratios to generate (e.g., ["1:1", "9:16", "16:9"])
            product_folder: Product-specific folder path (e.g., /campaign-id/products/product-id)
            logo_bytes: Optional logo to overlay on generated images
        """
        from .openai_image import OpenAIImageClient

        # Use OpenAI for aspect ratio variations
        openai_client = OpenAIImageClient(self.settings)

        for aspect_ratio in aspect_ratios:
            # Skip 1:1 as it's already generated by Gemini
            if aspect_ratio == "1:1":
                continue

            try:
                print(f"Generating {aspect_ratio} variation for {product.id}")

                # Generate image at target aspect ratio
                artifact = await openai_client.generate_image(
                    prompt=prompt,
                    negative_prompt=product.negative_prompt,
                    aspect_ratio=aspect_ratio,
                )

                # Use the generated image directly
                final_image_bytes = artifact.image_bytes

                # Store aspect ratio variation in products/{product-id}/{aspect-ratio}/
                aspect_folder = aspect_ratio.replace(":", "-")  # 9:16 -> 9-16
                aspect_folder_path = f"{product_folder}/{aspect_folder}"
                variation_path = f"{aspect_folder_path}/{product.id}.png"

                self.storage.upload_image(
                    path=variation_path,
                    data=final_image_bytes,
                )

                print(f"Generated {aspect_ratio} variation: {variation_path}")

            except Exception as exc:
                # Log warning but continue with other aspect ratios
                print(f"Warning: Failed to generate {aspect_ratio} variation for {product.id}: {exc}")


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
