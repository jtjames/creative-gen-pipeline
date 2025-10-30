# Campaign Brief API with Product Images

## Overview

The Campaign Brief API provides endpoints for managing campaign briefs with product images. Each product in a campaign brief **must** have an associated source image that will be used in the creative generation pipeline.

Briefs and their associated product images are stored in Dropbox and treated as a document database.

## Storage Structure

```
/briefs/
  /{campaign_id}/
    /brief.json          # Campaign brief data (with image_path references)
    /metadata.json       # Upload timestamp, version, status
    /assets/
      /{product_id}.jpg  # Product source images
      /{product_id}.png
      ...
```

## API Endpoints

### 1. Upload Campaign Brief with Product Images

**Endpoint:** `POST /briefs`

**Content-Type:** `multipart/form-data`

**Description:** Upload a new campaign brief with product source images.

**Form Fields:**
- `brief_json` (required): JSON string containing the campaign brief
- `product_images` (required): File uploads for each product

**Image Requirements:**
- One image file per product
- Filename must match product ID (e.g., `product-1.jpg`, `wh-9000.png`)
- Supported formats: JPEG, PNG, WEBP
- Maximum size: 10MB per image
- Recommended dimensions: 1200x1200px or larger

**Brief JSON Schema:**
```json
{
  "campaign": "string (required)",
  "target_region": "string (required)",
  "target_audience": "string (required)",
  "locales": ["locale-code", ...] (required, min 1),
  "message": {
    "locale-code": "localized message text"
  },
  "cta": {
    "locale-code": "localized CTA text"
  },
  "products": [
    {
      "id": "string (required)",
      "name": "string (required)",
      "prompt": "string (required)",
      "negative_prompt": "string (optional)",
      "image_path": "placeholder - will be set automatically during upload"
    }
  ] (required, min 2),
  "brand": {
    "primary_hex": "#RRGGBB (required)",
    "logo_path": "string (required)"
  },
  "aspect_ratios": ["1:1", "9:16", "16:9"] (required, min 1),
  "template": "name@version (e.g., bottom-cta@1.3.0)"
}
```

**Response:** `201 Created`
```json
{
  "campaign_id": "summer-2025-promo",
  "brief_path": "/briefs/summer-2025-promo/brief.json",
  "metadata_path": "/briefs/summer-2025-promo/metadata.json",
  "uploaded_at": "2025-10-30T12:34:56.789Z",
  "status": "pending"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=@examples/sample-brief.json;type=application/json" \
  -F "product_images=@/path/to/wh-9000.jpg" \
  -F "product_images=@/path/to/sw-elite.jpg" \
  -F "product_images=@/path/to/bt-speaker.jpg"
```

**Example using Python (requests):**
```python
import json
import requests

# Load brief JSON
with open('examples/sample-brief.json', 'r') as f:
    brief_data = json.load(f)

# Prepare multipart form data
files = [
    ('brief_json', (None, json.dumps(brief_data), 'application/json')),
    ('product_images', ('wh-9000.jpg', open('wh-9000.jpg', 'rb'), 'image/jpeg')),
    ('product_images', ('sw-elite.jpg', open('sw-elite.jpg', 'rb'), 'image/jpeg')),
    ('product_images', ('bt-speaker.jpg', open('bt-speaker.jpg', 'rb'), 'image/jpeg')),
]

response = requests.post('http://localhost:1854/briefs', files=files)
print(response.json())
```

**Example using the provided script:**
```bash
cd creative-gen-pipeline/server
source .venv/bin/activate
python examples/upload_brief.py
```

**Validation Rules:**
- Campaign ID must be unique
- At least 2 products required
- **Every product must have a corresponding image file**
- Image filenames must match product IDs
- All locales must have corresponding message and CTA translations
- Aspect ratios must be from: `["1:1", "9:16", "16:9"]`
- Template must match pattern: `name@major.minor.patch`
- Brand primary_hex must be valid hex color: `#RRGGBB`
- Images must be under 10MB each

**Error Responses:**

`422 Unprocessable Entity` - Missing images:
```json
{
  "detail": "Missing images for products: wh-9000, sw-elite"
}
```

`422 Unprocessable Entity` - Invalid JSON:
```json
{
  "detail": "Invalid JSON in brief_json: Expecting value: line 1 column 1 (char 0)"
}
```

`413 Request Entity Too Large` - Image too large:
```json
{
  "detail": "Image for product wh-9000 exceeds 10MB limit"
}
```

`500 Internal Server Error` - Storage error:
```json
{
  "detail": "Failed to upload brief: Unable to ensure Dropbox folder"
}
```

---

### 2. List Campaign Briefs

**Endpoint:** `GET /briefs`

**Description:** List all campaign briefs in the system, sorted by upload time (most recent first).

**Response:** `200 OK`
```json
[
  {
    "campaign_id": "summer-2025-promo",
    "target_region": "North America",
    "target_audience": "Young professionals 25-35",
    "uploaded_at": "2025-10-30T12:34:56.789Z",
    "status": "pending",
    "product_count": 3,
    "locale_count": 2
  }
]
```

**Example:**
```bash
curl http://localhost:1854/briefs
```

---

### 3. Get Campaign Brief

**Endpoint:** `GET /briefs/{campaign_id}`

**Description:** Retrieve the full campaign brief for a specific campaign, including image paths.

**Response:** `200 OK`
```json
{
  "campaign": "summer-2025-promo",
  "target_region": "North America",
  "products": [
    {
      "id": "wh-9000",
      "name": "Wireless Headphones Premium",
      "prompt": "sleek matte black wireless headphones...",
      "negative_prompt": "blurry, distorted...",
      "image_path": "/briefs/summer-2025-promo/assets/wh-9000.jpg"
    }
  ],
  ...
}
```

**Example:**
```bash
curl http://localhost:1854/briefs/summer-2025-promo
```

---

## Product Image Workflow

### 1. Prepare Product Images

Each product in your campaign needs a source image:

```
product_images/
  ├── wh-9000.jpg       (Wireless Headphones)
  ├── sw-elite.png      (Smart Watch)
  └── bt-speaker.jpg    (Bluetooth Speaker)
```

**Image Guidelines:**
- Use high-quality product photography
- Clean, uncluttered backgrounds work best
- Minimum 1200x1200px recommended
- JPEG (85%+ quality) or PNG formats
- Keep file sizes under 10MB

### 2. Prepare Brief JSON

Create a JSON file with product details. The `image_path` field will be automatically populated during upload:

```json
{
  "products": [
    {
      "id": "wh-9000",
      "name": "Wireless Headphones Premium",
      "prompt": "sleek wireless headphones on desk",
      "image_path": "placeholder - will be set during upload"
    }
  ]
}
```

### 3. Upload via API

**Option A: Use the Python upload script**
```bash
python examples/upload_brief.py
```

**Option B: Use curl**
```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=$(cat examples/sample-brief.json)" \
  -F "product_images=@product_images/wh-9000.jpg" \
  -F "product_images=@product_images/sw-elite.png" \
  -F "product_images=@product_images/bt-speaker.jpg"
```

**Option C: Use Python requests library**

See `examples/upload_brief.py` for a complete example with:
- Multipart form data handling
- Automatic placeholder image generation
- Error handling
- Response validation

### 4. Verify Upload

The API returns the stored paths:

```json
{
  "campaign_id": "summer-2025-promo",
  "brief_path": "/briefs/summer-2025-promo/brief.json",
  "metadata_path": "/briefs/summer-2025-promo/metadata.json",
  "uploaded_at": "2025-10-30T12:34:56.789Z",
  "status": "pending"
}
```

Product images are stored at:
```
/briefs/summer-2025-promo/assets/wh-9000.jpg
/briefs/summer-2025-promo/assets/sw-elite.png
/briefs/summer-2025-promo/assets/bt-speaker.jpg
```

---

## Image Path Resolution

After upload, each product's `image_path` field is automatically updated to point to the stored location:

**Before upload:**
```json
{
  "id": "wh-9000",
  "image_path": "placeholder"
}
```

**After upload:**
```json
{
  "id": "wh-9000",
  "image_path": "/briefs/summer-2025-promo/assets/wh-9000.jpg"
}
```

These paths can be used to:
1. **Generate temporary download links** via `/storage/temporary-link`
2. **Reference images in the generation pipeline**
3. **Display thumbnails in the UI**

---

## Integration with Generation Pipeline

Once a brief is uploaded with product images:

1. **Brief Upload** → Brief + images stored in `/briefs/{campaign_id}/`
2. **Status: pending** → Ready for creative generation
3. **Generation Trigger** → Orchestrator loads brief and product images
4. **Image Processing** → Product images used as:
   - Reference for AI generation
   - Base for image expansion/reframing
   - Source for composite creatives
5. **Asset Creation** → Final creatives stored in `/campaigns/{campaign_id}/`
6. **Status: completed** → Generation finished

---

## Testing

### Run Integration Tests

The integration tests verify the complete upload workflow with images:

```bash
cd creative-gen-pipeline/server
source .venv/bin/activate

# Requires DROPBOX_ACCESS_TOKEN in .env
python -m pytest tests/integration/test_brief_workflow.py -v
```

Tests include:
- Upload brief with product images
- Verify image storage and path resolution
- Retrieve brief with correct image paths
- List briefs with product counts
- Delete briefs and cleanup assets

### Test Upload Script

```bash
# Start the server
make run

# In another terminal
source .venv/bin/activate
python examples/upload_brief.py
```

This creates placeholder images for testing and uploads them with the sample brief.

---

## Notes

- All product images are **required** - uploads will fail if any are missing
- Image filenames **must match** product IDs exactly (excluding extension)
- Supported formats: JPEG, PNG, WEBP (detected automatically)
- Images are stored with original format (or JPEG if detection fails)
- Maximum 10MB per image (configurable in `src/app.py`)
- All timestamps are in UTC
- FastAPI provides automatic OpenAPI documentation at `/docs`

---

## Troubleshooting

**Error: "Missing images for products: ..."**
- Ensure filename (without extension) matches product ID exactly
- Check that all products have corresponding images

**Error: "Image for product X exceeds 10MB limit"**
- Compress images before upload
- Use JPEG with 85% quality for photos
- Consider resizing to 1200x1200px

**Error: "Failed to upload brief: Unable to ensure Dropbox folder"**
- Check DROPBOX_ACCESS_TOKEN is set correctly
- Verify Dropbox permissions allow folder creation
- Check network connectivity
