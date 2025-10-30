"""
Data models for campaign briefs and related entities.

This module defines Pydantic models for validating campaign briefs
that are uploaded to the system and stored in Dropbox.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator


class Product(BaseModel):
    """A product to be featured in the campaign."""

    id: str = Field(..., min_length=1, description="Unique product identifier")
    name: str = Field(..., min_length=1, description="Product display name")
    prompt: str = Field(..., min_length=1, description="Image generation prompt")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt for generation")
    image_path: str = Field(..., min_length=1, description="Path to product source image")


class Brand(BaseModel):
    """Brand identity configuration."""

    primary_hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Primary brand color")
    secondary_hex: Optional[str] = Field(
        None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Secondary brand color (optional)"
    )
    logo_path: str = Field(..., min_length=1, description="Path to logo in brand library")


class CampaignBrief(BaseModel):
    """
    Campaign brief schema matching the data contract defined in AGENTS.md.

    This represents the input JSON that clients submit to generate
    localized social media creatives at scale.
    """

    campaign: str = Field(..., min_length=1, description="Campaign identifier")
    target_region: str = Field(..., min_length=1, description="Target geographic region")
    target_audience: str = Field(..., min_length=1, description="Target audience description")
    locales: List[str] = Field(..., min_length=1, description="List of locale codes (e.g., en-US, es-MX)")
    message: Dict[str, str] = Field(..., description="Localized headline messages")
    cta: Dict[str, str] = Field(..., description="Localized call-to-action text")
    products: List[Product] = Field(..., min_length=2, description="Products to feature (minimum 2)")
    brand: Brand = Field(..., description="Brand identity configuration")
    aspect_ratios: List[str] = Field(..., min_length=1, description="Target aspect ratios")
    template: str = Field(..., pattern=r"^[\w-]+@\d+\.\d+\.\d+$", description="Template version (e.g., bottom-cta@1.3.0)")

    @field_validator("aspect_ratios")
    @classmethod
    def validate_aspect_ratios(cls, v: List[str]) -> List[str]:
        """Ensure aspect ratios are from the allowed set."""
        allowed = {"1:1", "9:16", "16:9"}
        for ratio in v:
            if ratio not in allowed:
                raise ValueError(f"Invalid aspect ratio '{ratio}'. Must be one of {allowed}")
        return v

    @field_validator("locales")
    @classmethod
    def validate_locales(cls, v: List[str]) -> List[str]:
        """Ensure locales follow expected format."""
        for locale in v:
            if not locale or len(locale) < 2:
                raise ValueError(f"Invalid locale '{locale}'")
        return v

    @model_validator(mode="after")
    def validate_locale_consistency(self) -> "CampaignBrief":
        """Ensure message and cta dicts contain all specified locales."""
        missing_message_locales = set(self.locales) - set(self.message.keys())
        missing_cta_locales = set(self.locales) - set(self.cta.keys())

        if missing_message_locales:
            raise ValueError(f"Missing message translations for locales: {missing_message_locales}")
        if missing_cta_locales:
            raise ValueError(f"Missing CTA translations for locales: {missing_cta_locales}")

        return self


class BriefMetadata(BaseModel):
    """Metadata about a stored campaign brief."""

    campaign_id: str = Field(..., description="Campaign identifier")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Upload timestamp (UTC)")
    version: str = Field(default="1.0.0", description="Brief format version")
    status: str = Field(default="pending", description="Processing status")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is from allowed values."""
        allowed = {"pending", "processing", "completed", "failed"}
        if v not in allowed:
            raise ValueError(f"Invalid status '{v}'. Must be one of {allowed}")
        return v


class BriefUploadResponse(BaseModel):
    """Response from uploading a campaign brief."""

    campaign_id: str = Field(..., description="Campaign identifier")
    brief_path: str = Field(..., description="Dropbox path to stored brief")
    metadata_path: str = Field(..., description="Dropbox path to metadata")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Brief status")
    generation_triggered: Optional[bool] = Field(None, description="Whether automatic generation was triggered")
    message: Optional[str] = Field(None, description="Status message about upload and generation")


class BriefListItem(BaseModel):
    """Brief list item for GET /briefs endpoint."""

    campaign_id: str = Field(..., description="Campaign identifier")
    target_region: str = Field(..., description="Target region")
    target_audience: str = Field(..., description="Target audience")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Processing status")
    product_count: int = Field(..., description="Number of products")
    locale_count: int = Field(..., description="Number of locales")
