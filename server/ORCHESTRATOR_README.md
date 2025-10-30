# Orchestrator Agent - AI Image Generation

## Overview

The Orchestrator Agent coordinates the creative generation pipeline, including automatic image generation for products without uploaded images. When you upload a brief without product images, the orchestrator uses OpenAI's image generation API to create product images based on the prompts you provide.

## What Was Implemented

### 1. Optional Product Images
- **Brief upload** now accepts briefs without product images
- Products must have either:
  - An uploaded image file, OR
  - A generation prompt (and optional negative prompt)

### 2. Orchestrator Agent (`src/orchestrator.py`)
Core pipeline coordinator that:
- Loads campaign briefs
- Generates missing product images using GenAI
- Updates brief status throughout the process
- Stores generated images in Dropbox

### 3. New API Endpoint
- `POST /api/generate` - Trigger creative generation for a campaign

## Quick Start

### Prerequisites

1. **OpenAI API Key** - Set in your `.env` file:
```bash
OPENAI_API_KEY=sk-your-api-key-here
GENAI_PROVIDER=openai
```

2. **Dropbox Access Token** - Already configured in `.env`

### Upload a Brief Without Images

#### Option 1: Using the Web Form
1. Go to http://localhost:1854/upload-brief.html
2. Fill in the campaign details
3. Add products with prompts (skip image uploads)
4. Submit the form

#### Option 2: Using cURL
```bash
curl -X POST http://localhost:1854/briefs \
  -H "Content-Type: application/json" \
  -d @examples/brief-no-images.json
```

Response:
```json
{
  "campaign_id": "ai-generated-winter-2025",
  "brief_path": "/briefs/ai-generated-winter-2025/brief.json",
  "metadata_path": "/briefs/ai-generated-winter-2025/metadata.json",
  "uploaded_at": "2025-10-30T14:30:00.000Z",
  "status": "pending"
}
```

### Trigger Image Generation

```bash
curl -X POST http://localhost:1854/api/generate \
  -F "campaign_id=ai-generated-winter-2025"
```

Response:
```json
{
  "campaign_id": "ai-generated-winter-2025",
  "status": "completed",
  "products_processed": 3,
  "total_creatives": 9,
  "generated_at": "2025-10-30T14:31:00.000Z"
}
```

### Check Generation Status

```bash
# Get brief to see updated status
curl http://localhost:1854/briefs/ai-generated-winter-2025

# List all briefs with status
curl http://localhost:1854/briefs
```

## Brief Status Lifecycle

1. **pending** - Brief uploaded, waiting for generation
2. **processing** - Orchestrator is generating images and creatives
3. **completed** - All assets generated successfully
4. **failed** - Generation encountered an error

## How It Works

### Product Image Generation

When a brief is processed:

1. **Orchestrator loads brief** from Dropbox
2. **For each product** without an image:
   - Uses the `prompt` field to describe the desired image
   - Uses optional `negative_prompt` to specify what to avoid
   - Calls OpenAI's image generation API
   - Generates a 1024x1024 base image
   - Stores it in `/briefs/{campaign_id}/assets/{product_id}-generated.png`
3. **Updates brief** with new image paths
4. **Updates status** to "completed"

### Image Generation Parameters

From your brief:
```json
{
  "id": "winter-jacket-pro",
  "name": "Professional Winter Jacket",
  "prompt": "A high-quality professional winter jacket...",
  "negative_prompt": "blurry, low quality, distorted...",
  "image_path": "placeholder"
}
```

The orchestrator:
- Generates a 1:1 (1024x1024) master image
- Uses your prompt and negative prompt
- Stores as: `/briefs/ai-generated-winter-2025/assets/winter-jacket-pro-generated.png`

## Example Brief

See `examples/brief-no-images.json` for a complete example with:
- 3 products with detailed generation prompts
- 3 locales (en-US, es-MX, fr-CA)
- 3 aspect ratios (1:1, 9:16, 16:9)
- Total: 27 creatives to be generated (3 × 3 × 3)

## Configuration

### Environment Variables

```bash
# Required for image generation
OPENAI_API_KEY=sk-your-key-here
GENAI_PROVIDER=openai

# Already configured
DROPBOX_ACCESS_TOKEN=your-token
DROPBOX_ROOT_PATH=/
```

### Supported GenAI Providers

Currently supported:
- **OpenAI** (recommended) - `gpt-image-1` model
- **Gemini** (planned) - Google's Imagen model

To switch providers:
```bash
GENAI_PROVIDER=openai  # or gemini (when supported)
```

## Storage Structure

After generation, your Dropbox will contain:

```
/briefs/
  /ai-generated-winter-2025/
    /brief.json                           # Updated with generated image paths
    /metadata.json                        # Status: "completed"
    /assets/
      /winter-jacket-pro-generated.png    # AI-generated
      /thermal-gloves-elite-generated.png # AI-generated
      /insulated-boots-generated.png      # AI-generated
```

## Writing Good Prompts

### Good Product Prompts

✅ **Specific and detailed**:
```json
"prompt": "Professional winter jacket in navy blue, studio lighting, white background, product photography style, detailed texture"
```

✅ **Include important details**:
- Product type and key features
- Color and materials
- Lighting style (studio, natural, dramatic)
- Background (white, clean, minimalist)
- Photography style (product, lifestyle, editorial)

✅ **Use negative prompts**:
```json
"negative_prompt": "blurry, low quality, distorted, people, text, watermark, busy background"
```

### Avoid

❌ **Vague prompts**:
```json
"prompt": "A jacket"  // Too simple
```

❌ **Complex scenes**:
```json
"prompt": "Person wearing jacket climbing mountain in winter storm"  // Too complex for product imagery
```

## Limitations & Future Work

### Current Limitations

1. **Image generation only** - Template application and rendering not yet implemented
2. **Single aspect ratio** - Generates 1:1 master images (expansion to other ratios planned)
3. **No compliance checks** - Quality validation coming soon
4. **OpenAI only** - Gemini integration planned

### Planned Features

1. **Aspect Ratio Expansion**
   - Generate/expand to 9:16 and 16:9
   - Smart cropping and composition

2. **Template & Layout**
   - Apply brand templates
   - Overlay localized text
   - Position logos and CTAs

3. **Rendering Pipeline**
   - Composite final creatives
   - Export in multiple formats
   - Optimize for social platforms

4. **Compliance Checks**
   - Logo presence validation
   - Brand color verification
   - Legal content scanning
   - Quality scoring

5. **Multi-Provider Support**
   - Gemini/Imagen integration
   - Provider fallback logic
   - Cost optimization

## Testing

### Run Tests
```bash
cd creative-gen-pipeline/server

# Unit tests
pytest tests/unit -v

# Integration tests (requires API keys)
pytest tests/integration -v
```

### Manual Testing

1. **Start the server**:
```bash
make run
# or
PYTHONPATH=. uvicorn src.app:app --reload --port 1854
```

2. **Upload brief without images**:
```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=@examples/brief-no-images.json"
```

3. **Trigger generation**:
```bash
curl -X POST http://localhost:1854/api/generate \
  -F "campaign_id=ai-generated-winter-2025"
```

4. **Check status**:
```bash
curl http://localhost:1854/briefs
```

## Troubleshooting

### "GenAI provider does not support async image generation"

**Solution**: Set `GENAI_PROVIDER=openai` in your `.env` file.

### "OPENAI_API_KEY is not configured"

**Solution**: Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### "Product must have either an uploaded image or a generation prompt"

**Solution**: Ensure all products in your brief have a non-empty `prompt` field if you're not uploading images.

### Generation takes a long time

**Expected**: OpenAI image generation can take 5-15 seconds per image. For 3 products, expect 15-45 seconds total.

## Cost Estimation

### OpenAI Image Generation Pricing
- Model: `gpt-image-1`
- Size: 1024x1024
- Cost: ~$0.040 per image

**Example**:
- 3 products = 3 images = $0.12
- 10 products = 10 images = $0.40

*Note: Prices subject to change. Check OpenAI pricing for current rates.*

## API Reference

### POST /api/generate

**Description**: Trigger creative generation for a campaign

**Request**:
```bash
Content-Type: multipart/form-data

campaign_id: string (required)
```

**Response** (200 OK):
```json
{
  "campaign_id": "string",
  "status": "completed" | "failed",
  "products_processed": number,
  "total_creatives": number,
  "generated_at": "ISO 8601 timestamp"
}
```

**Errors**:
- `404 Not Found` - Campaign brief doesn't exist
- `422 Unprocessable Entity` - Invalid campaign data
- `500 Internal Server Error` - Generation failed

## Next Steps

1. **Test with your own brief**
   - Create a brief with products you want to visualize
   - Write detailed prompts
   - Run generation

2. **Experiment with prompts**
   - Try different prompt styles
   - Test negative prompts
   - Refine for your use case

3. **Monitor in Dropbox**
   - Check `/briefs/{campaign_id}/assets/` for generated images
   - Review image quality
   - Iterate on prompts as needed

## Support

For issues or questions:
1. Check this README
2. Review error messages in server logs
3. Verify environment variables are set correctly
4. Check Dropbox storage quotas
