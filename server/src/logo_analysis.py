"""Logo analysis utilities for extracting visual characteristics."""

from __future__ import annotations

import io
from typing import Dict, List, Tuple
from collections import Counter

from PIL import Image
import colorsys


def analyze_logo(logo_bytes: bytes) -> Dict[str, any]:
    """
    Analyze a logo image to extract visual characteristics.

    Args:
        logo_bytes: Logo image as bytes

    Returns:
        Dictionary containing:
        - dominant_colors: List of (hex, percentage) tuples for top colors
        - brightness: Overall brightness (0-1)
        - style_description: Text description of visual style
        - color_palette: List of hex colors
    """
    img = Image.open(io.BytesIO(logo_bytes))

    # Convert to RGB if necessary
    if img.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize for faster processing
    img.thumbnail((200, 200), Image.Resampling.LANCZOS)

    # Extract dominant colors
    dominant_colors = _extract_dominant_colors(img, num_colors=5)

    # Calculate overall brightness
    brightness = _calculate_brightness(img)

    # Generate style description
    style_description = _generate_style_description(dominant_colors, brightness)

    # Extract color palette
    color_palette = [color for color, _ in dominant_colors]

    return {
        "dominant_colors": dominant_colors,
        "brightness": brightness,
        "style_description": style_description,
        "color_palette": color_palette,
    }


def _extract_dominant_colors(img: Image.Image, num_colors: int = 5) -> List[Tuple[str, float]]:
    """
    Extract dominant colors from an image.

    Args:
        img: PIL Image
        num_colors: Number of dominant colors to extract

    Returns:
        List of (hex_color, percentage) tuples
    """
    # Get all pixels
    pixels = list(img.getdata())

    # Filter out very light colors (likely background)
    pixels = [p for p in pixels if sum(p) < 700]  # Not too close to white

    if not pixels:
        return [("#000000", 1.0)]

    # Count color frequencies
    color_counts = Counter(pixels)

    # Get most common colors
    most_common = color_counts.most_common(num_colors * 2)

    # Filter similar colors and convert to hex
    unique_colors = []
    for rgb, count in most_common:
        # Check if this color is significantly different from already selected colors
        is_unique = True
        for existing_rgb, _ in unique_colors:
            if _color_distance(rgb, existing_rgb) < 50:  # Threshold for similarity
                is_unique = False
                break

        if is_unique:
            hex_color = _rgb_to_hex(rgb)
            percentage = count / len(pixels)
            unique_colors.append((hex_color, percentage))

        if len(unique_colors) >= num_colors:
            break

    # Normalize percentages
    total = sum(pct for _, pct in unique_colors)
    normalized = [(color, pct / total) for color, pct in unique_colors]

    return normalized


def _calculate_brightness(img: Image.Image) -> float:
    """
    Calculate overall brightness of an image.

    Args:
        img: PIL Image

    Returns:
        Brightness value from 0 (dark) to 1 (light)
    """
    pixels = list(img.getdata())
    avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)
    return avg_brightness / 255.0


def _generate_style_description(
    dominant_colors: List[Tuple[str, float]], brightness: float
) -> str:
    """
    Generate a text description of the visual style based on colors and brightness.

    Args:
        dominant_colors: List of (hex, percentage) tuples
        brightness: Overall brightness value

    Returns:
        Text description of style
    """
    descriptions = []

    # Describe brightness
    if brightness > 0.7:
        descriptions.append("bright and vibrant")
    elif brightness > 0.4:
        descriptions.append("balanced")
    else:
        descriptions.append("bold and dark")

    # Describe color scheme
    if len(dominant_colors) >= 2:
        primary_color = dominant_colors[0][0]
        color_name = _get_color_name(primary_color)

        if len(dominant_colors) >= 3:
            descriptions.append(f"multi-colored with {color_name} prominence")
        else:
            descriptions.append(f"{color_name}-toned")
    else:
        descriptions.append("monochromatic")

    # Describe color saturation
    primary_rgb = _hex_to_rgb(dominant_colors[0][0])
    h, s, v = colorsys.rgb_to_hsv(primary_rgb[0] / 255, primary_rgb[1] / 255, primary_rgb[2] / 255)

    if s > 0.6:
        descriptions.append("highly saturated")
    elif s > 0.3:
        descriptions.append("moderately saturated")
    else:
        descriptions.append("muted tones")

    return ", ".join(descriptions)


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _color_distance(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """
    Calculate Euclidean distance between two RGB colors.

    Args:
        rgb1: First RGB color
        rgb2: Second RGB color

    Returns:
        Distance value
    """
    return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5


def _get_color_name(hex_color: str) -> str:
    """
    Get a general color name from hex value.

    Args:
        hex_color: Hex color string

    Returns:
        Color name (e.g., "red", "blue", "green")
    """
    rgb = _hex_to_rgb(hex_color)
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # Low saturation = grayscale
    if s < 0.2:
        if v > 0.8:
            return "white"
        elif v < 0.3:
            return "black"
        else:
            return "gray"

    # Determine hue-based color
    hue_degree = h * 360

    if hue_degree < 15 or hue_degree >= 345:
        return "red"
    elif hue_degree < 45:
        return "orange"
    elif hue_degree < 75:
        return "yellow"
    elif hue_degree < 155:
        return "green"
    elif hue_degree < 255:
        return "blue"
    elif hue_degree < 285:
        return "purple"
    else:
        return "pink"


def create_logo_enhanced_prompt(base_prompt: str, logo_analysis: Dict[str, any], has_reference_image: bool = False) -> str:
    """
    Enhance a product prompt with logo visual characteristics.

    Args:
        base_prompt: Original product description
        logo_analysis: Results from analyze_logo()
        has_reference_image: Whether a logo reference image is provided to the model

    Returns:
        Enhanced prompt incorporating logo style
    """
    style_desc = logo_analysis["style_description"]
    color_palette = logo_analysis["color_palette"]

    # Build enhancement
    enhancements = []

    # Add reference to provided image if available
    if has_reference_image:
        enhancements.append(
            "using the provided brand logo image as a visual reference for style, colors, and branding"
        )

    # Add style description
    enhancements.append(f"with {style_desc} brand aesthetic")

    # Add color palette
    if len(color_palette) >= 2:
        top_colors = color_palette[:3]
        color_list = ", ".join(top_colors)
        enhancements.append(f"incorporating brand colors ({color_list})")

    # Add branding instruction
    enhancements.append(
        "featuring the brand logo or brand elements integrated naturally into the product design, "
        "styled as a premium branded product photograph"
    )

    enhancement_text = ", " + ", ".join(enhancements)
    return f"{base_prompt}{enhancement_text}"
