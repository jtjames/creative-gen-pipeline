# Product Images Implementation

## Summary

Updated the campaign brief upload system to **require product images** for each product in a campaign. Product images are essential input assets for the creative generation pipeline.

## Changes Made

### 1. Data Model Updates

**`src/models.py`** - Added `image_path` field to Product:
```python
class Product(BaseModel):
    id: str
    name: str
    prompt: str
    negative_prompt: Optional[str]
    image_path: str  # NEW: Path to product source image
```

### 2. Storage Structure Enhancement

**New folder structure:**
```
/briefs/
  /{campaign_id}/
    /brief.json          # Campaign brief with image_path references
    /metadata.json       # Upload metadata
    /assets/             # NEW: Product images folder
      /{product_id}.jpg
      /{product_id}.png
      ...
```

### 3. Brief Service Updates

**`src/briefs.py`** - Enhanced `upload_brief()` to handle product images:

- Accepts `product_images: Dict[str, bytes]` parameter
- Validates that all products have corresponding images
- Automatically detects image format (JPEG, PNG, WEBP)
- Uploads images to `/briefs/{campaign_id}/assets/`
- Updates `image_path` in Product models before saving brief

```python
def upload_brief(
    self,
    brief: CampaignBrief,
    product_images: Optional[Dict[str, bytes]] = None
) -> BriefUploadResponse:
    # Validates all products have images
    # Uploads images to /assets/ folder
    # Updates image_path fields automatically
    ...
```

### 4. API Endpoint Changes

**`src/app.py`** - Modified POST /briefs to accept multipart/form-data:

**Old (JSON body):**
```python
async def upload_brief(brief: CampaignBrief, ...):
```

**New (Multipart form-data):**
```python
async def upload_brief(
    brief_json: str = Form(...),
    product_images: List[UploadFile] = File(...),
    ...
):
```

**Features:**
- Accepts `brief_json` as form field
- Accepts multiple `product_images` files
- Validates image size (10MB max per image)
- Extracts product_id from filename (e.g., `product-1.jpg` → `product-1`)
- Returns 422 if any product is missing an image
- Returns 413 if any image exceeds size limit

### 5. Testing Updates

**Unit Tests** (`tests/unit/test_brief_endpoints.py`):
- Updated sample data to include `image_path` fields
- Maintained mock-based testing approach

**Integration Tests** (`tests/integration/test_brief_workflow.py`):
- Added `sample_product_images` fixture with test JPEG data
- Updated all test functions to pass `product_images` parameter
- Tests verify image upload and path resolution

### 6. Example Upload Script

**`examples/upload_brief.py`** - Complete working example:

```python
# Creates placeholder images using Pillow
# Demonstrates multipart/form-data upload
# Handles multiple images with same field name
# Includes error handling and response validation
```

Usage:
```bash
python examples/upload_brief.py
```

### 7. Documentation

**`docs/BRIEF_API_WITH_IMAGES.md`** - Comprehensive guide:
- Multipart form-data upload examples
- Image requirements and guidelines
- curl, Python requests, and script examples
- Error handling documentation
- Integration workflow details

### 8. Example Data

**`examples/sample-brief.json`** - Updated with `image_path` placeholders:
```json
{
  "products": [
    {
      "id": "wh-9000",
      "name": "Wireless Headphones Premium",
      "prompt": "...",
      "image_path": "placeholder - will be set during upload"
    }
  ]
}
```

## Image Requirements

- **Format**: JPEG, PNG, or WEBP
- **Size**: Maximum 10MB per image
- **Naming**: Filename must match product ID (e.g., `wh-9000.jpg` for product ID `wh-9000`)
- **Quantity**: One image required per product
- **Dimensions**: Recommended 1200x1200px or larger

## API Usage Examples

### Using curl:
```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=@examples/sample-brief.json;type=application/json" \
  -F "product_images=@wh-9000.jpg" \
  -F "product_images=@sw-elite.jpg" \
  -F "product_images=@bt-speaker.jpg"
```

### Using Python:
```python
import json
import requests

files = [
    ('brief_json', (None, json.dumps(brief_data), 'application/json')),
    ('product_images', ('wh-9000.jpg', open('wh-9000.jpg', 'rb'), 'image/jpeg')),
    ('product_images', ('sw-elite.jpg', open('sw-elite.jpg', 'rb'), 'image/jpeg')),
]

response = requests.post('http://localhost:1854/briefs', files=files)
```

### Using the upload script:
```bash
python examples/upload_brief.py
```

## Image Processing Flow

1. **Client uploads** multipart form with brief JSON + images
2. **API validates** all products have corresponding images
3. **Service detects** image format from magic bytes
4. **Service uploads** images to `/briefs/{campaign_id}/assets/{product_id}.{ext}`
5. **Service updates** `image_path` in Product models
6. **Service saves** brief.json with updated paths
7. **Response returns** campaign metadata

## Image Path Resolution

**Before upload:**
```json
{"id": "wh-9000", "image_path": "placeholder"}
```

**After upload:**
```json
{"id": "wh-9000", "image_path": "/briefs/summer-2025-promo/assets/wh-9000.jpg"}
```

These paths can be used to:
- Generate temporary download links via `/storage/temporary-link`
- Reference images in the creative generation pipeline
- Display product thumbnails in the UI

## Error Handling

**Missing images (422):**
```json
{"detail": "Missing images for products: wh-9000, sw-elite"}
```

**Image too large (413):**
```json
{"detail": "Image for product wh-9000 exceeds 10MB limit"}
```

**Invalid JSON (422):**
```json
{"detail": "Invalid JSON in brief_json: ..."}
```

## Files Modified

1. `src/models.py` - Added `image_path` to Product model
2. `src/briefs.py` - Enhanced upload_brief() for image handling
3. `src/app.py` - Changed POST /briefs to multipart/form-data
4. `examples/sample-brief.json` - Added image_path placeholders
5. `tests/unit/test_brief_endpoints.py` - Updated test data
6. `tests/integration/test_brief_workflow.py` - Added image fixtures

## Files Created

1. `examples/upload_brief.py` - Upload script with Pillow integration
2. `docs/BRIEF_API_WITH_IMAGES.md` - Complete API documentation

## Testing

Run unit tests (no Dropbox required):
```bash
python -m pytest tests/unit/test_brief_endpoints.py -v
```

Run integration tests (requires valid Dropbox token):
```bash
python -m pytest tests/integration/test_brief_workflow.py -v
```

Test upload script (requires running server):
```bash
# Terminal 1
make run

# Terminal 2
python examples/upload_brief.py
```

## Next Steps

To integrate with the creative generation pipeline:

1. **Use product images as reference** for AI generation
2. **Apply image expansion** for different aspect ratios
3. **Composite with templates** to create final creatives
4. **Track source images** in report.json metadata

## Notes

- All product images are **mandatory** - no upload without images
- Image format detection uses magic bytes (JPEG: `\xff\xd8`, PNG: `\x89PNG`, WEBP: `RIFF...WEBP`)
- Images stored with detected extension or default to `.jpg`
- 10MB size limit is configurable in `src/app.py` line 84
- FastAPI auto-generates OpenAPI docs at `/docs` showing the multipart schema
