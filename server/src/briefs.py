"""
Campaign brief management service.

This module provides functionality for storing and retrieving campaign briefs
from Dropbox, treating it as a document database.
"""

import json
from datetime import datetime, UTC
from typing import List, Optional, Dict
from pathlib import Path

from .storage import DropboxStorage
from .models import (
    CampaignBrief,
    BriefMetadata,
    BriefUploadResponse,
    BriefListItem,
)


class BriefService:
    """Service for managing campaign briefs in Dropbox storage."""

    def __init__(self, storage: DropboxStorage):
        """
        Initialize the brief service.

        Args:
            storage: Dropbox storage adapter for file operations
        """
        self.storage = storage
        self.briefs_root = "/briefs"

    def upload_brief(
        self,
        brief: CampaignBrief,
        product_images: Optional[Dict[str, bytes]] = None
    ) -> BriefUploadResponse:
        """
        Upload a campaign brief to Dropbox storage.

        Args:
            brief: Validated campaign brief to store
            product_images: Optional dict mapping product_id to image bytes

        Returns:
            Upload response with paths and metadata

        Raises:
            ValueError: If product images are missing for any product
            Exception: If upload fails
        """
        campaign_id = brief.campaign
        campaign_folder = f"{self.briefs_root}/{campaign_id}"
        assets_folder = f"{campaign_folder}/assets"

        # Ensure folders exist
        self.storage.ensure_folder(campaign_folder)
        self.storage.ensure_folder(assets_folder)

        # Upload product images if provided
        if product_images:
            for product in brief.products:
                product_id = product.id

                if product_id not in product_images:
                    raise ValueError(f"Missing image for product: {product_id}")

                # Determine file extension from image bytes (basic check)
                image_bytes = product_images[product_id]
                if image_bytes[:2] == b'\xff\xd8':
                    ext = 'jpg'
                elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                    ext = 'png'
                elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
                    ext = 'webp'
                else:
                    ext = 'jpg'  # default

                # Upload image
                image_path = f"{assets_folder}/{product_id}.{ext}"
                self.storage.upload_image(
                    path=image_path,
                    data=image_bytes,
                )

                # Update product image_path to point to stored location
                product.image_path = image_path

        # Prepare brief JSON (with updated image paths)
        brief_json = brief.model_dump_json(indent=2)
        brief_path = f"{campaign_folder}/brief.json"

        # Create metadata
        metadata = BriefMetadata(
            campaign_id=campaign_id,
            uploaded_at=datetime.now(UTC),
        )
        metadata_json = metadata.model_dump_json(indent=2)
        metadata_path = f"{campaign_folder}/metadata.json"

        # Upload both files
        self.storage.upload_bytes(
            path=brief_path,
            data=brief_json.encode("utf-8"),
        )

        self.storage.upload_bytes(
            path=metadata_path,
            data=metadata_json.encode("utf-8"),
        )

        return BriefUploadResponse(
            campaign_id=campaign_id,
            brief_path=brief_path,
            metadata_path=metadata_path,
            uploaded_at=metadata.uploaded_at,
            status=metadata.status,
        )

    def get_brief(self, campaign_id: str) -> Optional[CampaignBrief]:
        """
        Retrieve a campaign brief by ID.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign brief if found, None otherwise

        Raises:
            Exception: If retrieval fails
        """
        brief_path = f"{self.briefs_root}/{campaign_id}/brief.json"

        try:
            # Download brief JSON from Dropbox
            brief_bytes = self.storage.download_bytes(brief_path)
            brief_json = brief_bytes.decode("utf-8")
            brief_data = json.loads(brief_json)

            return CampaignBrief(**brief_data)
        except Exception:
            # Brief not found or invalid
            return None

    def get_brief_metadata(self, campaign_id: str) -> Optional[BriefMetadata]:
        """
        Retrieve brief metadata by campaign ID.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Brief metadata if found, None otherwise
        """
        metadata_path = f"{self.briefs_root}/{campaign_id}/metadata.json"

        try:
            metadata_bytes = self.storage.download_bytes(metadata_path)
            metadata_json = metadata_bytes.decode("utf-8")
            metadata_data = json.loads(metadata_json)

            return BriefMetadata(**metadata_data)
        except Exception:
            return None

    def list_briefs(self) -> List[BriefListItem]:
        """
        List all campaign briefs in storage.

        Returns:
            List of brief summary items

        Raises:
            Exception: If listing fails
        """
        # Ensure briefs root exists
        self.storage.ensure_folder(self.briefs_root)

        # List all campaign folders
        try:
            paths = list(self.storage.list_paths(self.briefs_root))
        except Exception:
            # If briefs folder doesn't exist yet, return empty list
            return []

        # Filter for folders only (campaign IDs)
        campaign_folders = [
            p for p in paths
            if p.startswith(f"{self.briefs_root}/") and p.count("/") == 2
        ]

        # Extract campaign IDs from folder paths
        campaign_ids = [
            Path(folder).name
            for folder in campaign_folders
        ]

        # Fetch brief and metadata for each campaign
        brief_items = []
        for campaign_id in campaign_ids:
            brief = self.get_brief(campaign_id)
            metadata = self.get_brief_metadata(campaign_id)

            if brief and metadata:
                brief_items.append(
                    BriefListItem(
                        campaign_id=campaign_id,
                        target_region=brief.target_region,
                        target_audience=brief.target_audience,
                        uploaded_at=metadata.uploaded_at,
                        status=metadata.status,
                        product_count=len(brief.products),
                        locale_count=len(brief.locales),
                    )
                )

        # Sort by upload time, most recent first
        brief_items.sort(key=lambda x: x.uploaded_at, reverse=True)

        return brief_items

    def delete_brief(self, campaign_id: str) -> bool:
        """
        Delete a campaign brief and its metadata.

        Args:
            campaign_id: Campaign identifier

        Returns:
            True if deleted successfully, False if not found
        """
        campaign_folder = f"{self.briefs_root}/{campaign_id}"

        try:
            self.storage.delete_path(campaign_folder)
            return True
        except Exception:
            return False

    def update_brief_status(
        self, campaign_id: str, status: str
    ) -> Optional[BriefMetadata]:
        """
        Update the status of a campaign brief.

        Args:
            campaign_id: Campaign identifier
            status: New status value

        Returns:
            Updated metadata if successful, None if brief not found
        """
        metadata = self.get_brief_metadata(campaign_id)

        if not metadata:
            return None

        # Update status
        metadata.status = status

        # Save back to Dropbox
        metadata_path = f"{self.briefs_root}/{campaign_id}/metadata.json"
        metadata_json = metadata.model_dump_json(indent=2)

        self.storage.upload_bytes(
            path=metadata_path,
            data=metadata_json.encode("utf-8"),
        )

        return metadata
