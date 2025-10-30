#!/usr/bin/env python3
"""
Script to upload a campaign brief with product images.

Usage:
    python examples/upload_brief.py

This script demonstrates how to upload a campaign brief with product images
to the Creative Automation API.
"""

import json
import io
import requests
from pathlib import Path
from PIL import Image

# API endpoint
API_URL = "http://localhost:1854/briefs"


def create_placeholder_image(product_id: str, width: int = 800, height: int = 600) -> bytes:
    """Create a simple placeholder image for testing."""
    # Create a colored rectangle
    colors = {
        "wh-9000": (100, 149, 237),  # Cornflower blue
        "sw-elite": (60, 179, 113),   # Medium sea green
        "bt-speaker": (255, 140, 0),  # Dark orange
    }
    color = colors.get(product_id, (128, 128, 128))

    img = Image.new('RGB', (width, height), color=color)

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)

    return img_bytes.read()


def upload_brief():
    """Upload a campaign brief with product images."""

    # Load brief JSON
    brief_path = Path(__file__).parent / "sample-brief.json"
    with open(brief_path, 'r') as f:
        brief_data = json.load(f)

    # Prepare multipart form data
    product_ids = ["wh-9000", "sw-elite", "bt-speaker"]

    # Create list of files for multipart/form-data
    # Note: We use a list to allow multiple files with the same field name
    files = [
        ('brief_json', (None, json.dumps(brief_data), 'application/json')),
    ]

    # Add product images
    for product_id in product_ids:
        image_bytes = create_placeholder_image(product_id)
        files.append(
            ('product_images', (f'{product_id}.jpg', image_bytes, 'image/jpeg'))
        )

    # Alternative: If you have actual image files
    # for product_id in product_ids:
    #     image_path = Path(__file__).parent / "assets" / f"{product_id}.jpg"
    #     if image_path.exists():
    #         files.append(
    #             ('product_images', (f'{product_id}.jpg', open(image_path, 'rb'), 'image/jpeg'))
    #         )

    print(f"Uploading brief to {API_URL}...")
    print(f"Brief: {brief_data['campaign']}")
    print(f"Products: {', '.join(product_ids)}")

    # Make request
    response = requests.post(API_URL, files=files)

    if response.status_code == 201:
        result = response.json()
        print("\n✅ Upload successful!")
        print(f"Campaign ID: {result['campaign_id']}")
        print(f"Brief path: {result['brief_path']}")
        print(f"Metadata path: {result['metadata_path']}")
        print(f"Status: {result['status']}")
    else:
        print(f"\n❌ Upload failed with status {response.status_code}")
        print(f"Error: {response.text}")


if __name__ == "__main__":
    try:
        upload_brief()
    except Exception as e:
        print(f"Error: {e}")
