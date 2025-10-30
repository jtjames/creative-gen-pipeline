"""Image processing utilities for compositing logos and other visual elements."""

from __future__ import annotations

import io
from typing import Optional

from PIL import Image


def overlay_logo_on_image(
    product_image_bytes: bytes,
    logo_image_bytes: bytes,
    logo_position: str = "bottom-right",
    logo_scale: float = 0.15,
    padding: int = 20,
) -> bytes:
    """
    Overlay a logo on a product image.

    Args:
        product_image_bytes: Product image as bytes (PNG/JPEG)
        logo_image_bytes: Logo image as bytes (PNG/JPEG)
        logo_position: Position for logo placement
            Options: "bottom-right", "bottom-left", "top-right", "top-left"
        logo_scale: Logo size as fraction of image width (default: 0.15 = 15%)
        padding: Padding from edges in pixels

    Returns:
        Composited image as PNG bytes
    """
    # Load images
    product_img = Image.open(io.BytesIO(product_image_bytes))
    logo_img = Image.open(io.BytesIO(logo_image_bytes))

    # Convert to RGBA for transparency support
    if product_img.mode != "RGBA":
        product_img = product_img.convert("RGBA")
    if logo_img.mode != "RGBA":
        logo_img = logo_img.convert("RGBA")

    # Calculate logo size
    product_width, product_height = product_img.size
    target_logo_width = int(product_width * logo_scale)

    # Resize logo maintaining aspect ratio
    logo_aspect = logo_img.height / logo_img.width
    target_logo_height = int(target_logo_width * logo_aspect)
    logo_resized = logo_img.resize(
        (target_logo_width, target_logo_height),
        Image.Resampling.LANCZOS
    )

    # Calculate position
    logo_x, logo_y = _calculate_logo_position(
        product_width,
        product_height,
        target_logo_width,
        target_logo_height,
        logo_position,
        padding
    )

    # Create a composite with the logo
    composite = product_img.copy()
    composite.paste(logo_resized, (logo_x, logo_y), logo_resized)

    # Convert back to RGB for PNG output (removes alpha channel)
    final_img = Image.new("RGB", composite.size, (255, 255, 255))
    final_img.paste(composite, mask=composite.split()[3] if composite.mode == "RGBA" else None)

    # Save to bytes
    output_buffer = io.BytesIO()
    final_img.save(output_buffer, format="PNG", optimize=True)
    return output_buffer.getvalue()


def _calculate_logo_position(
    img_width: int,
    img_height: int,
    logo_width: int,
    logo_height: int,
    position: str,
    padding: int,
) -> tuple[int, int]:
    """
    Calculate logo position coordinates.

    Args:
        img_width: Product image width
        img_height: Product image height
        logo_width: Resized logo width
        logo_height: Resized logo height
        position: Position identifier
        padding: Padding from edges

    Returns:
        Tuple of (x, y) coordinates for logo placement
    """
    if position == "bottom-right":
        x = img_width - logo_width - padding
        y = img_height - logo_height - padding
    elif position == "bottom-left":
        x = padding
        y = img_height - logo_height - padding
    elif position == "top-right":
        x = img_width - logo_width - padding
        y = padding
    elif position == "top-left":
        x = padding
        y = padding
    else:
        # Default to bottom-right
        x = img_width - logo_width - padding
        y = img_height - logo_height - padding

    return x, y


def add_watermark_to_image(
    image_bytes: bytes,
    watermark_text: str,
    position: str = "bottom-center",
    font_size: int = 24,
    opacity: float = 0.7,
) -> bytes:
    """
    Add a text watermark to an image.

    Args:
        image_bytes: Image as bytes
        watermark_text: Text to display
        position: Position for watermark
        font_size: Font size for watermark
        opacity: Watermark opacity (0.0 to 1.0)

    Returns:
        Image with watermark as PNG bytes
    """
    from PIL import ImageDraw, ImageFont

    # Load image
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGBA
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Create transparent overlay
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to use a better font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()

    # Calculate text size and position
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    img_width, img_height = img.size

    if position == "bottom-center":
        x = (img_width - text_width) // 2
        y = img_height - text_height - 20
    elif position == "center":
        x = (img_width - text_width) // 2
        y = (img_height - text_height) // 2
    else:
        x = (img_width - text_width) // 2
        y = img_height - text_height - 20

    # Draw text with opacity
    alpha = int(255 * opacity)
    draw.text((x, y), watermark_text, fill=(255, 255, 255, alpha), font=font)

    # Composite
    watermarked = Image.alpha_composite(img, overlay)

    # Convert to RGB
    final_img = Image.new("RGB", watermarked.size, (255, 255, 255))
    final_img.paste(watermarked, mask=watermarked.split()[3] if watermarked.mode == "RGBA" else None)

    # Save to bytes
    output_buffer = io.BytesIO()
    final_img.save(output_buffer, format="PNG", optimize=True)
    return output_buffer.getvalue()
