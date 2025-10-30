"""Integration tests for campaign brief upload and retrieval workflow."""

import pytest
from datetime import datetime

from src.storage import DropboxStorage
from src.briefs import BriefService
from src.models import CampaignBrief, Product, Brand


@pytest.fixture
def storage():
    """Create a DropboxStorage instance for testing."""
    return DropboxStorage()


@pytest.fixture
def brief_service(storage):
    """Create a BriefService instance for testing."""
    return BriefService(storage)


@pytest.fixture
def sample_brief():
    """Create a sample campaign brief for testing."""
    return CampaignBrief(
        campaign="test-summer-2025-promo",
        target_region="North America",
        target_audience="Young professionals 25-35",
        locales=["en-US", "es-MX"],
        message={
            "en-US": "Summer savings are here!",
            "es-MX": "¡Llegaron los ahorros de verano!"
        },
        cta={
            "en-US": "Shop Now",
            "es-MX": "Comprar Ahora"
        },
        products=[
            Product(
                id="product-1",
                name="Wireless Headphones",
                prompt="sleek wireless headphones in modern setting",
                negative_prompt="blurry, distorted",
                image_path="placeholder"
            ),
            Product(
                id="product-2",
                name="Smart Watch",
                prompt="elegant smart watch on wrist",
                negative_prompt="low quality",
                image_path="placeholder"
            )
        ],
        brand=Brand(
            primary_hex="#FF5733",
            logo_path="/brandlib/acme/logo.png"
        ),
        aspect_ratios=["1:1", "9:16"],
        template="bottom-cta@1.3.0"
    )


@pytest.fixture
def sample_product_images():
    """Create sample product images for testing."""
    # Create simple 1x1 pixel JPEG images
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    return {
        "product-1": jpeg_header + b'\x00' * 100,
        "product-2": jpeg_header + b'\x00' * 100,
    }


def test_upload_and_retrieve_brief(brief_service, sample_brief, sample_product_images):
    """Test uploading a brief and then retrieving it."""
    # Upload the brief
    upload_response = brief_service.upload_brief(sample_brief, product_images=sample_product_images)

    # Verify upload response
    assert upload_response.campaign_id == "test-summer-2025-promo"
    assert upload_response.brief_path == "/briefs/test-summer-2025-promo/brief.json"
    assert upload_response.metadata_path == "/briefs/test-summer-2025-promo/metadata.json"
    assert upload_response.status == "pending"
    assert isinstance(upload_response.uploaded_at, datetime)

    # Retrieve the brief
    retrieved_brief = brief_service.get_brief("test-summer-2025-promo")

    # Verify retrieved brief matches original
    assert retrieved_brief is not None
    assert retrieved_brief.campaign == sample_brief.campaign
    assert retrieved_brief.target_region == sample_brief.target_region
    assert retrieved_brief.target_audience == sample_brief.target_audience
    assert retrieved_brief.locales == sample_brief.locales
    assert retrieved_brief.message == sample_brief.message
    assert retrieved_brief.cta == sample_brief.cta
    assert len(retrieved_brief.products) == len(sample_brief.products)
    assert retrieved_brief.products[0].id == sample_brief.products[0].id
    assert retrieved_brief.brand.primary_hex == sample_brief.brand.primary_hex
    assert retrieved_brief.aspect_ratios == sample_brief.aspect_ratios
    assert retrieved_brief.template == sample_brief.template

    # Retrieve metadata
    metadata = brief_service.get_brief_metadata("test-summer-2025-promo")
    assert metadata is not None
    assert metadata.campaign_id == "test-summer-2025-promo"
    assert metadata.status == "pending"

    # Clean up
    brief_service.delete_brief("test-summer-2025-promo")


def test_list_briefs(brief_service, sample_brief, sample_product_images):
    """Test listing briefs."""
    # Upload a brief
    brief_service.upload_brief(sample_brief, product_images=sample_product_images)

    # List briefs
    briefs = brief_service.list_briefs()

    # Verify the brief appears in the list
    assert len(briefs) > 0
    test_brief = next(
        (b for b in briefs if b.campaign_id == "test-summer-2025-promo"),
        None
    )
    assert test_brief is not None
    assert test_brief.target_region == "North America"
    assert test_brief.product_count == 2
    assert test_brief.locale_count == 2
    assert test_brief.status == "pending"

    # Clean up
    brief_service.delete_brief("test-summer-2025-promo")


def test_update_brief_status(brief_service, sample_brief, sample_product_images):
    """Test updating brief status."""
    # Upload a brief
    brief_service.upload_brief(sample_brief, product_images=sample_product_images)

    # Update status
    updated_metadata = brief_service.update_brief_status(
        "test-summer-2025-promo",
        "processing"
    )

    # Verify update
    assert updated_metadata is not None
    assert updated_metadata.status == "processing"

    # Verify persistence
    metadata = brief_service.get_brief_metadata("test-summer-2025-promo")
    assert metadata.status == "processing"

    # Clean up
    brief_service.delete_brief("test-summer-2025-promo")


def test_delete_brief(brief_service, sample_brief, sample_product_images):
    """Test deleting a brief."""
    # Upload a brief
    brief_service.upload_brief(sample_brief, product_images=sample_product_images)

    # Verify it exists
    brief = brief_service.get_brief("test-summer-2025-promo")
    assert brief is not None

    # Delete it
    result = brief_service.delete_brief("test-summer-2025-promo")
    assert result is True

    # Verify it's gone
    brief = brief_service.get_brief("test-summer-2025-promo")
    assert brief is None


def test_get_nonexistent_brief(brief_service):
    """Test retrieving a brief that doesn't exist."""
    brief = brief_service.get_brief("nonexistent-campaign")
    assert brief is None


def test_delete_nonexistent_brief(brief_service):
    """Test deleting a brief that doesn't exist."""
    # Should return False but not raise an error
    result = brief_service.delete_brief("nonexistent-campaign")
    assert result is False


def test_multiple_briefs(brief_service, sample_brief, sample_product_images):
    """Test working with multiple briefs."""
    # Create variations of the sample brief
    brief1 = sample_brief.model_copy(deep=True)
    brief1.campaign = "test-campaign-1"

    brief2 = sample_brief.model_copy(deep=True)
    brief2.campaign = "test-campaign-2"
    brief2.target_region = "Europe"

    # Upload both
    brief_service.upload_brief(brief1, product_images=sample_product_images)
    brief_service.upload_brief(brief2, product_images=sample_product_images)

    # List briefs
    briefs = brief_service.list_briefs()
    test_briefs = [
        b for b in briefs
        if b.campaign_id in ["test-campaign-1", "test-campaign-2"]
    ]
    assert len(test_briefs) == 2

    # Retrieve each individually
    retrieved1 = brief_service.get_brief("test-campaign-1")
    retrieved2 = brief_service.get_brief("test-campaign-2")

    assert retrieved1 is not None
    assert retrieved2 is not None
    assert retrieved1.campaign == "test-campaign-1"
    assert retrieved2.campaign == "test-campaign-2"
    assert retrieved2.target_region == "Europe"

    # Clean up
    brief_service.delete_brief("test-campaign-1")
    brief_service.delete_brief("test-campaign-2")
