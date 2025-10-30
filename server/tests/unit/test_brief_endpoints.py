"""Unit tests for campaign brief API endpoints."""

from unittest.mock import Mock, patch
from datetime import datetime, UTC

import pytest
from fastapi.testclient import TestClient

from src.app import create_app
from src.models import (
    CampaignBrief,
    BriefMetadata,
    BriefUploadResponse,
    BriefListItem,
    Product,
    Brand,
)


@pytest.fixture
def sample_brief_data():
    """Sample campaign brief data for testing."""
    return {
        "campaign": "summer-2025-promo",
        "target_region": "North America",
        "target_audience": "Young professionals 25-35",
        "locales": ["en-US", "es-MX"],
        "message": {
            "en-US": "Summer savings are here!",
            "es-MX": "¡Llegaron los ahorros de verano!"
        },
        "cta": {
            "en-US": "Shop Now",
            "es-MX": "Comprar Ahora"
        },
        "products": [
            {
                "id": "product-1",
                "name": "Wireless Headphones",
                "prompt": "sleek wireless headphones in modern setting",
                "negative_prompt": "blurry, distorted",
                "image_path": "/briefs/summer-2025-promo/assets/product-1.jpg"
            },
            {
                "id": "product-2",
                "name": "Smart Watch",
                "prompt": "elegant smart watch on wrist",
                "negative_prompt": "low quality",
                "image_path": "/briefs/summer-2025-promo/assets/product-2.jpg"
            }
        ],
        "brand": {
            "primary_hex": "#FF5733",
            "logo_path": "/brandlib/acme/logo.png"
        },
        "aspect_ratios": ["1:1", "9:16"],
        "template": "bottom-cta@1.3.0"
    }


@pytest.fixture
def mock_brief_service():
    """Create a mock BriefService for testing."""
    with patch("src.app.BriefService") as mock:
        yield mock


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


def test_upload_brief_success(client, sample_brief_data, mock_brief_service):
    """Test successful brief upload."""
    # Setup mock
    mock_service_instance = Mock()
    mock_brief_service.return_value = mock_service_instance

    upload_time = datetime.now(UTC)
    mock_service_instance.upload_brief.return_value = BriefUploadResponse(
        campaign_id="summer-2025-promo",
        brief_path="/briefs/summer-2025-promo/brief.json",
        metadata_path="/briefs/summer-2025-promo/metadata.json",
        uploaded_at=upload_time,
        status="pending"
    )

    # Make request
    response = client.post("/briefs", json=sample_brief_data)

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["campaign_id"] == "summer-2025-promo"
    assert data["brief_path"] == "/briefs/summer-2025-promo/brief.json"
    assert data["status"] == "pending"


def test_upload_brief_validation_error(client):
    """Test brief upload with invalid data."""
    invalid_brief = {
        "campaign": "test-campaign",
        # Missing required fields
    }

    response = client.post("/briefs", json=invalid_brief)
    assert response.status_code == 422  # Unprocessable Entity


def test_upload_brief_invalid_aspect_ratio(client, sample_brief_data):
    """Test brief upload with invalid aspect ratio."""
    sample_brief_data["aspect_ratios"] = ["1:1", "invalid-ratio"]

    response = client.post("/briefs", json=sample_brief_data)
    assert response.status_code == 422


def test_upload_brief_missing_locale_translation(client, sample_brief_data):
    """Test brief upload with missing locale translations."""
    # Add locale but don't provide translation
    sample_brief_data["locales"].append("fr-FR")

    response = client.post("/briefs", json=sample_brief_data)
    assert response.status_code == 422


def test_upload_brief_invalid_template_format(client, sample_brief_data):
    """Test brief upload with invalid template format."""
    sample_brief_data["template"] = "invalid-template"

    response = client.post("/briefs", json=sample_brief_data)
    assert response.status_code == 422


def test_upload_brief_insufficient_products(client, sample_brief_data):
    """Test brief upload with less than 2 products."""
    sample_brief_data["products"] = [sample_brief_data["products"][0]]

    response = client.post("/briefs", json=sample_brief_data)
    assert response.status_code == 422


def test_list_briefs_success(client, mock_brief_service):
    """Test successful listing of briefs."""
    # Setup mock
    mock_service_instance = Mock()
    mock_brief_service.return_value = mock_service_instance

    upload_time = datetime.now(UTC)
    mock_service_instance.list_briefs.return_value = [
        BriefListItem(
            campaign_id="campaign-1",
            target_region="North America",
            target_audience="Young adults",
            uploaded_at=upload_time,
            status="pending",
            product_count=2,
            locale_count=2
        ),
        BriefListItem(
            campaign_id="campaign-2",
            target_region="Europe",
            target_audience="Professionals",
            uploaded_at=upload_time,
            status="completed",
            product_count=3,
            locale_count=3
        )
    ]

    # Make request
    response = client.get("/briefs")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["campaign_id"] == "campaign-1"
    assert data[1]["campaign_id"] == "campaign-2"


def test_list_briefs_empty(client, mock_brief_service):
    """Test listing briefs when none exist."""
    # Setup mock
    mock_service_instance = Mock()
    mock_brief_service.return_value = mock_service_instance
    mock_service_instance.list_briefs.return_value = []

    # Make request
    response = client.get("/briefs")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_brief_success(client, sample_brief_data, mock_brief_service):
    """Test successful retrieval of a specific brief."""
    # Setup mock
    mock_service_instance = Mock()
    mock_brief_service.return_value = mock_service_instance

    brief = CampaignBrief(**sample_brief_data)
    mock_service_instance.get_brief.return_value = brief

    # Make request
    response = client.get("/briefs/summer-2025-promo")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["campaign"] == "summer-2025-promo"
    assert data["target_region"] == "North America"
    assert len(data["products"]) == 2


def test_get_brief_not_found(client, mock_brief_service):
    """Test retrieval of non-existent brief."""
    # Setup mock
    mock_service_instance = Mock()
    mock_brief_service.return_value = mock_service_instance
    mock_service_instance.get_brief.return_value = None

    # Make request
    response = client.get("/briefs/nonexistent-campaign")

    # Assertions
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
