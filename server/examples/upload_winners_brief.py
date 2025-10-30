#!/usr/bin/env python3
"""
Upload Winners Sports Brand campaign brief.

This script uploads the Winners Spring Performance 2025 campaign brief
with product images for the North American sports brand.

Usage:
    python examples/upload_winners_brief.py
"""

import json
import io
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# API endpoint
API_URL = "http://localhost:1854/briefs"


def create_product_placeholder(product_id: str, product_name: str, width: int = 1200, height: int = 1200) -> bytes:
    """
    Create a placeholder product image with branding.

    In production, replace these with actual product photography.
    """
    # Color scheme for Winners brand
    colors = {
        "bolt-runner-pro": {
            "bg": (0, 0, 0),  # Black
            "accent": (0, 128, 255),  # Electric blue
            "text": (255, 255, 255)  # White
        },
        "lightning-compression": {
            "bg": (0, 0, 0),
            "accent": (0, 128, 255),
            "text": (255, 255, 255)
        },
        "power-training-gear": {
            "bg": (0, 0, 0),
            "accent": (0, 128, 255),
            "text": (255, 255, 255)
        }
    }

    color_scheme = colors.get(product_id, colors["bolt-runner-pro"])

    # Create image
    img = Image.new('RGB', (width, height), color=color_scheme["bg"])
    draw = ImageDraw.Draw(img)

    # Draw lightning bolt accent (simplified)
    # Top triangle
    draw.polygon([
        (width//2 - 100, height//2 - 200),
        (width//2 + 50, height//2 - 200),
        (width//2 - 50, height//2)
    ], fill=color_scheme["accent"])

    # Bottom triangle
    draw.polygon([
        (width//2 - 50, height//2),
        (width//2 + 100, height//2 + 200),
        (width//2 + 50, height//2 + 200)
    ], fill=color_scheme["accent"])

    # Add product text
    try:
        # Try to use a nice font if available
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Product name
    text_bbox = draw.textbbox((0, 0), product_name, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2

    draw.text((text_x, height - 200), product_name,
              fill=color_scheme["text"], font=font_large)

    # Winners brand text
    brand_text = "WINNERS"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_large)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_x = (width - brand_width) // 2

    draw.text((brand_x, 100), brand_text,
              fill=color_scheme["text"], font=font_large)

    # Product ID
    draw.text((50, height - 80), f"SKU: {product_id.upper()}",
              fill=color_scheme["accent"], font=font_small)

    # Add border accent
    border_width = 10
    draw.rectangle([0, 0, width, border_width], fill=color_scheme["accent"])
    draw.rectangle([0, height - border_width, width, height], fill=color_scheme["accent"])
    draw.rectangle([0, 0, border_width, height], fill=color_scheme["accent"])
    draw.rectangle([width - border_width, 0, width, height], fill=color_scheme["accent"])

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)

    return img_bytes.read()


def upload_winners_brief():
    """Upload the Winners Sports campaign brief with product images."""

    # Load brief JSON
    brief_path = Path(__file__).parent / "winners-spring-performance-brief.json"

    if not brief_path.exists():
        print(f"❌ Brief file not found: {brief_path}")
        return

    with open(brief_path, 'r') as f:
        brief_data = json.load(f)

    print("=" * 60)
    print("🏆 WINNERS SPORTS - Campaign Brief Upload")
    print("=" * 60)
    print(f"\nCampaign: {brief_data['campaign']}")
    print(f"Region: {brief_data['target_region']}")
    print(f"Target: {brief_data['target_audience']}")
    print(f"\nLocales: {', '.join(brief_data['locales'])}")
    print(f"Products: {len(brief_data['products'])}")
    print(f"Aspect Ratios: {', '.join(brief_data['aspect_ratios'])}")

    # Prepare multipart form data
    files = [
        ('brief_json', (None, json.dumps(brief_data), 'application/json')),
    ]

    # Create and add product images
    print("\n" + "-" * 60)
    print("Creating product images...")
    print("-" * 60)

    for product in brief_data['products']:
        product_id = product['id']
        product_name = product['name']

        print(f"\n⚡ {product_name}")
        print(f"   ID: {product_id}")

        # Check if actual image exists
        image_path = Path(__file__).parent / "assets" / f"{product_id}.jpg"

        if image_path.exists():
            print(f"   ✓ Using actual image: {image_path.name}")
            with open(image_path, 'rb') as img_file:
                files.append(
                    ('product_images', (f'{product_id}.jpg', img_file.read(), 'image/jpeg'))
                )
        else:
            print(f"   ⚠ Creating placeholder image")
            image_bytes = create_product_placeholder(product_id, product_name)
            files.append(
                ('product_images', (f'{product_id}.jpg', image_bytes, 'image/jpeg'))
            )

    # Upload to API
    print("\n" + "-" * 60)
    print(f"Uploading to {API_URL}...")
    print("-" * 60)

    try:
        response = requests.post(API_URL, files=files, timeout=30)

        if response.status_code == 201:
            result = response.json()
            print("\n" + "=" * 60)
            print("✅ UPLOAD SUCCESSFUL!")
            print("=" * 60)
            print(f"\nCampaign ID: {result['campaign_id']}")
            print(f"Brief Path: {result['brief_path']}")
            print(f"Status: {result['status']}")
            print(f"Uploaded: {result['uploaded_at']}")
            print("\n" + "-" * 60)
            print("View your brief at:")
            print(f"  http://localhost:1854/briefs.html")
            print("-" * 60)
        else:
            print("\n❌ Upload failed")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error")
        print("Make sure the server is running:")
        print("  cd creative-gen-pipeline/server")
        print("  make run")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    try:
        upload_winners_brief()
    except KeyboardInterrupt:
        print("\n\n⚠ Upload cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
