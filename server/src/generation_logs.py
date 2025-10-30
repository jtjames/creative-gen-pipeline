"""
Generation logging service for tracking GenAI asset creation.

This module provides structured logging for campaign asset generation,
writing detailed logs to Dropbox for audit and monitoring purposes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from .storage import DropboxStorage
from .models import CampaignBrief, Product
from .assets import needs_generation


class GenerationStatus(str, Enum):
    """Status values for generation events."""

    INITIATED = "initiated"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GenerationLogService:
    """Service for tracking and persisting generation events."""

    def __init__(self, storage: DropboxStorage):
        """
        Initialize the generation log service.

        Args:
            storage: Dropbox storage adapter
        """
        self.storage = storage

    def log_campaign_start(
        self,
        campaign_id: str,
        brief: CampaignBrief,
    ) -> Dict[str, Any]:
        """
        Log the start of campaign generation with asset completeness check.

        Args:
            campaign_id: Campaign identifier
            brief: Campaign brief with products

        Returns:
            Summary of asset status
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Analyze asset completeness
        total_products = len(brief.products)
        products_needing_generation = []
        products_with_assets = []

        for product in brief.products:
            if needs_generation(product.image_path):
                products_needing_generation.append({
                    "id": product.id,
                    "name": product.name,
                    "has_prompt": bool(product.prompt and product.prompt.strip()),
                })
            else:
                products_with_assets.append({
                    "id": product.id,
                    "name": product.name,
                    "image_path": product.image_path,
                })

        needs_generation_count = len(products_needing_generation)
        has_assets_count = len(products_with_assets)
        is_complete = needs_generation_count == 0

        # Create campaign start log
        log_entry = {
            "event": "campaign_generation_started",
            "campaign_id": campaign_id,
            "timestamp": timestamp,
            "asset_status": {
                "is_complete": is_complete,
                "total_products": total_products,
                "products_with_assets": has_assets_count,
                "products_needing_generation": needs_generation_count,
                "completion_percentage": round((has_assets_count / total_products) * 100, 1),
            },
            "products_needing_generation": products_needing_generation,
            "products_with_assets": products_with_assets,
            "target_creatives": len(brief.products) * len(brief.locales) * len(brief.aspect_ratios),
            "locales": brief.locales,
            "aspect_ratios": brief.aspect_ratios,
        }

        # Write to Dropbox
        log_path = f"/briefs/{campaign_id}/logs/generation-start-{self._timestamp_slug(timestamp)}.json"
        self.storage.upload_bytes(
            path=log_path,
            data=json.dumps(log_entry, indent=2).encode("utf-8"),
        )

        return log_entry

    def log_generation_initiated(
        self,
        campaign_id: str,
        product: Product,
        model: str,
    ) -> Dict[str, Any]:
        """
        Log the initiation of a single product image generation.

        Args:
            campaign_id: Campaign identifier
            product: Product being generated
            model: GenAI model being used

        Returns:
            Log entry
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        log_entry = {
            "event": "generation_initiated",
            "campaign_id": campaign_id,
            "timestamp": timestamp,
            "status": GenerationStatus.INITIATED.value,
            "product": {
                "id": product.id,
                "name": product.name,
                "prompt": product.prompt,
                "negative_prompt": product.negative_prompt,
            },
            "generation_config": {
                "model": model,
                "aspect_ratio": "1:1",
                "size": "1024x1024",
            },
        }

        # Write to Dropbox
        log_path = f"/briefs/{campaign_id}/logs/{product.id}-initiated-{self._timestamp_slug(timestamp)}.json"
        self.storage.upload_bytes(
            path=log_path,
            data=json.dumps(log_entry, indent=2).encode("utf-8"),
        )

        return log_entry

    def log_generation_completed(
        self,
        campaign_id: str,
        product: Product,
        model: str,
        image_path: str,
        duration_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Log the successful completion of a product image generation.

        Args:
            campaign_id: Campaign identifier
            product: Product that was generated
            model: GenAI model used
            image_path: Path where generated image was stored
            duration_seconds: Time taken for generation

        Returns:
            Log entry
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        log_entry = {
            "event": "generation_completed",
            "campaign_id": campaign_id,
            "timestamp": timestamp,
            "status": GenerationStatus.COMPLETED.value,
            "product": {
                "id": product.id,
                "name": product.name,
            },
            "result": {
                "image_path": image_path,
                "model": model,
                "aspect_ratio": "1:1",
                "size": "1024x1024",
            },
        }

        if duration_seconds is not None:
            log_entry["duration_seconds"] = round(duration_seconds, 2)

        # Write to Dropbox
        log_path = f"/briefs/{campaign_id}/logs/{product.id}-completed-{self._timestamp_slug(timestamp)}.json"
        self.storage.upload_bytes(
            path=log_path,
            data=json.dumps(log_entry, indent=2).encode("utf-8"),
        )

        return log_entry

    def log_generation_failed(
        self,
        campaign_id: str,
        product: Product,
        error: str,
    ) -> Dict[str, Any]:
        """
        Log a failed product image generation.

        Args:
            campaign_id: Campaign identifier
            product: Product that failed to generate
            error: Error message

        Returns:
            Log entry
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        log_entry = {
            "event": "generation_failed",
            "campaign_id": campaign_id,
            "timestamp": timestamp,
            "status": GenerationStatus.FAILED.value,
            "product": {
                "id": product.id,
                "name": product.name,
            },
            "error": error,
        }

        # Write to Dropbox
        log_path = f"/briefs/{campaign_id}/logs/{product.id}-failed-{self._timestamp_slug(timestamp)}.json"
        self.storage.upload_bytes(
            path=log_path,
            data=json.dumps(log_entry, indent=2).encode("utf-8"),
        )

        return log_entry

    def log_campaign_complete(
        self,
        campaign_id: str,
        brief: CampaignBrief,
        products_generated: int,
        total_duration_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Log the completion of campaign generation with final asset status.

        Args:
            campaign_id: Campaign identifier
            brief: Updated campaign brief
            products_generated: Number of products that were generated
            total_duration_seconds: Total time for all generations

        Returns:
            Summary log entry
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check final asset status
        total_products = len(brief.products)
        still_needing_generation = []

        for product in brief.products:
            if needs_generation(product.image_path):
                still_needing_generation.append({
                    "id": product.id,
                    "name": product.name,
                })

        is_complete = len(still_needing_generation) == 0

        log_entry = {
            "event": "campaign_generation_completed",
            "campaign_id": campaign_id,
            "timestamp": timestamp,
            "final_asset_status": {
                "is_complete": is_complete,
                "total_products": total_products,
                "products_generated_this_run": products_generated,
                "products_still_pending": len(still_needing_generation),
            },
            "products_still_needing_generation": still_needing_generation,
            "summary": {
                "all_assets_available": is_complete,
                "ready_for_rendering": is_complete,
                "message": (
                    "All campaign assets are available. Ready for template rendering."
                    if is_complete
                    else f"{len(still_needing_generation)} product(s) still need assets generated."
                ),
            },
        }

        if total_duration_seconds is not None:
            log_entry["total_duration_seconds"] = round(total_duration_seconds, 2)

        # Write to Dropbox
        log_path = f"/briefs/{campaign_id}/logs/generation-complete-{self._timestamp_slug(timestamp)}.json"
        self.storage.upload_bytes(
            path=log_path,
            data=json.dumps(log_entry, indent=2).encode("utf-8"),
        )

        return log_entry

    def _timestamp_slug(self, iso_timestamp: str) -> str:
        """
        Convert ISO timestamp to filesystem-friendly slug.

        Args:
            iso_timestamp: ISO 8601 timestamp

        Returns:
            Slugified timestamp (e.g., "20250130-143045")
        """
        # Convert "2025-01-30T14:30:45.123456+00:00" to "20250130-143045"
        return iso_timestamp[:19].replace(":", "").replace("-", "").replace("T", "-")
