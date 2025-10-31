# Creative Automation API

A FastAPI-based creative generation pipeline that automates the creation of localized marketing assets at scale. Built with an async-first architecture (FastAPI + Uvicorn ASGI), the system efficiently handles concurrent requests and background processing, enabling both vertical and horizontal scaling. The pipeline uses AI image generation (Gemini/OpenAI DALL-E 3), Dropbox storage, and orchestrates multi-step workflows to generate campaign assets across multiple products, locales, and aspect ratios.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Example Usage](#example-usage)
- [Key Design Decisions](#key-design-decisions)
- [Assumptions & Limitations](#assumptions--limitations)
- [Testing](#testing)
- [Project Structure](#project-structure)

## Features

- **Campaign Brief Management**: Upload and store campaign briefs with product details, brand identity, and localization requirements
- **AI Image Generation**: Automatically generate product images using Gemini 2.5 Flash Image or OpenAI DALL-E 3
- **Multi-Aspect Ratio Support**: Generate images in 1:1, 9:16, and 16:9 aspect ratios
- **Brand Integration**: Support for brand logos and colors in generated images
- **Dropbox Storage**: Persistent artifact storage with organized folder structure
- **Background Processing**: Asynchronous generation pipeline with status tracking
- **Web UI**: Interactive interface for uploading briefs and viewing campaigns
- **Generation Logs**: Detailed logging of generation events for debugging and monitoring

## Prerequisites

- **Python 3.10+**
- **Dropbox App** with access token (scopes: `files.metadata.read/write`, `files.content.read/write`)
- **Google Gemini API Key** (for Gemini image generation)
- **OpenAI API Key** (for DALL-E 3 image generation)

## Setup & Installation

### 1. Clone the repository and navigate to the server directory

```bash
cd creative-gen-pipeline/server
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the server directory with the following variables:

```bash
# Dropbox Configuration
DROPBOX_ACCESS_TOKEN=your_dropbox_access_token_here
DROPBOX_ROOT_PATH=/
TEMPORARY_LINK_TTL_SECONDS=300

# GenAI Provider (choose 'openai' or 'gemini')
GENAI_PROVIDER=openai

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Note**: The `DROPBOX_ROOT_PATH` should be `/` since Dropbox App tokens are automatically scoped to `/Apps/your-app-name/`.

## Running the Application

### Start the development server

```bash
PYTHONPATH=src uvicorn src.app:app --reload --port 1854
```

The server will be available at `http://localhost:1854`.

### Access the Web UI

- **Home Page**: `http://localhost:1854/`
- **Upload Brief**: `http://localhost:1854/upload-brief.html`
- **View Briefs**: `http://localhost:1854/briefs.html`
- **Health Check**: `http://localhost:1854/health`
- **API Documentation**: `http://localhost:1854/docs` (Swagger UI)

## API Endpoints

### Campaign Brief Management

#### `POST /briefs`
Upload a new campaign brief with optional product images and brand logo.

**Request**: `multipart/form-data`
- `brief_json` (string, required): JSON string containing the campaign brief
- `product_images` (files, optional): Product images (filename must match product ID)
- `brand_logo` (file, optional): Brand logo image

**Response**:
```json
{
  "campaign_id": "winter-campaign-2025",
  "brief_path": "/briefs/winter-campaign-2025/brief.json",
  "metadata_path": "/briefs/winter-campaign-2025/metadata.json",
  "uploaded_at": "2025-10-31T00:00:00Z",
  "status": "pending",
  "generation_triggered": true,
  "message": "Brief uploaded. Generating 3 missing product image(s) in background."
}
```

#### `GET /briefs`
List all campaign briefs with status information.

**Response**:
```json
[
  {
    "campaign_id": "winter-campaign-2025",
    "target_region": "North America",
    "target_audience": "Tech-savvy millennials",
    "uploaded_at": "2025-10-31T00:00:00Z",
    "status": "completed",
    "product_count": 3,
    "locale_count": 3,
    "product_image_paths": [
      "/briefs/winter-campaign-2025/products/product-1/1-1/product-1.png",
      "/briefs/winter-campaign-2025/products/product-2/1-1/product-2.png"
    ]
  }
]
```

#### `GET /briefs/{campaign_id}`
Retrieve a specific campaign brief.

#### `POST /api/generate`
Manually trigger generation for a campaign.

**Request**: `application/x-www-form-urlencoded`
- `campaign_id` (string): Campaign identifier

### Storage

#### `GET /storage/temporary-link`
Generate a temporary download link for a Dropbox file.

**Query Parameters**:
- `path` (string): Dropbox file path relative to root

**Response**:
```json
{
  "path": "/briefs/campaign-id/products/product-1/1-1/product-1.png",
  "link": "https://dl.dropboxusercontent.com/..."
}
```

## Example Usage

### Example 1: Upload a brief with AI-generated images

**1. Create a campaign brief JSON file** (`example-briefs/brief-no-images.json`):

```json
{
  "campaign": "ai-generated-winter-2025",
  "target_region": "North America",
  "target_audience": "Tech-savvy millennials aged 25-40",
  "locales": ["en-US", "es-MX", "fr-CA"],
  "message": {
    "en-US": "Winter Adventures Await",
    "es-MX": "Aventuras de Invierno Te Esperan",
    "fr-CA": "Les Aventures d'Hiver Vous Attendent"
  },
  "cta": {
    "en-US": "Shop Now",
    "es-MX": "Comprar Ahora",
    "fr-CA": "Magasiner Maintenant"
  },
  "products": [
    {
      "id": "winter-jacket-pro",
      "name": "Professional Winter Jacket",
      "prompt": "A high-quality professional winter jacket in deep navy blue, studio lighting, product photography",
      "negative_prompt": "blurry, low quality, distorted",
      "image_path": "placeholder"
    },
    {
      "id": "thermal-gloves-elite",
      "name": "Elite Thermal Gloves",
      "prompt": "Premium black thermal gloves, studio product photography",
      "negative_prompt": "blurry, low quality",
      "image_path": "placeholder"
    }
  ],
  "brand": {
    "primary_hex": "#1E3A8A",
    "secondary_hex": "#F59E0B",
    "logo_path": "placeholder"
  },
  "aspect_ratios": ["1:1", "9:16", "16:9"],
  "template": "bottom-cta@1.3.0"
}
```

**2. Upload using the Web UI**:
- Navigate to `http://localhost:1854/upload-brief.html`
- Select the JSON file
- Optionally upload brand logo
- Click "Upload Campaign Brief"

**3. Monitor progress**:
- View status at `http://localhost:1854/briefs.html`
- Status will change from `pending` → `processing` → `completed`

**4. Result structure in Dropbox**:
```
/briefs/
  ai-generated-winter-2025/
    brief.json                           # Campaign brief
    metadata.json                        # Status and timestamps
    logo.png                            # Brand logo (if uploaded)
    products/
      winter-jacket-pro/
        1-1/
          winter-jacket-pro.png         # Square (1:1) variant
        9-16/
          winter-jacket-pro.png         # Vertical (9:16) variant
        16-9/
          winter-jacket-pro.png         # Horizontal (16:9) variant
      thermal-gloves-elite/
        1-1/
          thermal-gloves-elite.png
        9-16/
          thermal-gloves-elite.png
        16-9/
          thermal-gloves-elite.png
    logs/
      generation-start-*.json           # Generation start logs
      generation-initiated-*.json       # Per-product generation logs
      generation-completed-*.json       # Per-product completion logs
      generation-complete-*.json        # Campaign completion log
```

### Example 2: Upload with existing product images

```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=@example-briefs/winners-sports/brief.json" \
  -F "product_images=@example-briefs/winners-sports/products/product-1.jpg" \
  -F "product_images=@example-briefs/winners-sports/products/product-2.jpg" \
  -F "brand_logo=@example-briefs/winners-sports/logo.png"
```

**Response**:
```json
{
  "campaign_id": "winners-sports-fall-2025",
  "brief_path": "/briefs/winners-sports-fall-2025/brief.json",
  "metadata_path": "/briefs/winners-sports-fall-2025/metadata.json",
  "uploaded_at": "2025-10-31T00:00:00Z",
  "status": "pending",
  "generation_triggered": true,
  "message": "Brief uploaded. Generating aspect ratio variations."
}
```

## Key Design Decisions

### 1. **Orchestrator Pattern**
- **Decision**: Centralized orchestration agent coordinates the multi-step generation pipeline
- **Rationale**: Separates business logic from API handlers, enables background processing, simplifies testing
- **Implementation**: `OrchestratorAgent` in `src/orchestrator.py`

### 2. **Dropbox as Document Database**
- **Decision**: Use Dropbox folder structure as a lightweight document store
- **Rationale**: Simplifies deployment (no database setup), provides built-in versioning, enables easy asset access
- **Trade-off**: Not suitable for high-frequency writes or complex queries

### 3. **Hybrid Image Generation Strategy**
- **Decision**: Use Gemini for image-to-image (when logo present), OpenAI for text-to-image
- **Rationale**:
  - Gemini 2.5 Flash Image supports multimodal input (image + text) for brand consistency
  - OpenAI DALL-E 3 excels at pure text-to-image generation
  - Provides fallback options if one service is unavailable
- **Implementation**: `select_genai_client()` in `src/genai_providers.py`

### 4. **Async-First Architecture (FastAPI + Uvicorn)**
- **Decision**: Use FastAPI with Uvicorn ASGI server instead of synchronous frameworks (Flask, Django)
- **Rationale**:
  - **Async-first**: Built on Python's `async`/`await` enables concurrent request handling without thread-per-request overhead
  - **Vertical scalability**: Single server can handle thousands of concurrent connections efficiently
  - **Horizontal scalability**: Stateless design allows easy load balancing across multiple instances
  - **Background tasks**: Native support for non-blocking background tasks (image generation) without blocking API responses
  - **Modern Python**: Leverages ASGI standard for high-performance async I/O
- **Performance benefits**:
  - Can serve multiple upload requests while generation tasks run in background
  - Dropbox/GenAI API calls don't block other requests (async I/O)
  - Lower memory footprint than thread-based servers
- **Implementation**: FastAPI framework + Uvicorn server (ASGI)

### 5. **Background Task Processing**
- **Decision**: Use FastAPI BackgroundTasks for async generation
- **Rationale**:
  - Prevents API timeouts for long-running generation tasks
  - Improves user experience (immediate response)
  - Simpler than setting up Celery/Redis for this scale
- **Trade-off**: No task persistence across server restarts

### 6. **Functional Core, Imperative Shell**
- **Decision**: Pure functions for business logic, side effects at boundaries
- **Rationale**: Easier testing, better reasoning about code, clear separation of concerns
- **Examples**:
  - `needs_generation()` - pure function checking image path status
  - `BriefService` - encapsulates all Dropbox side effects

### 7. **Pydantic for Validation**
- **Decision**: Use Pydantic models for all data structures
- **Rationale**: Automatic validation, JSON serialization, clear type contracts, great IDE support
- **Implementation**: All models in `src/models.py`

### 8. **Generation Logs as JSON Files**
- **Decision**: Store generation events as structured JSON logs in Dropbox
- **Rationale**:
  - Queryable logs without database
  - Timestamped audit trail
  - Easy to parse for analytics
- **Implementation**: `GenerationLogService` in `src/generation_logs.py`

### 9. **No Browser Caching for Status**
- **Decision**: Add `Cache-Control: no-cache` headers to `/briefs` endpoint
- **Rationale**: Ensure UI always shows current status, prevent stale data issues
- **Implementation**: Custom headers in `src/app.py`

## Assumptions & Limitations

### Assumptions

1. **Dropbox App Folder Scoping**: The Dropbox access token is scoped to an app folder (e.g., `/Apps/creative-gen-automation-assets/`), so `DROPBOX_ROOT_PATH=/` is correct

2. **Product Image Requirements**:
   - Products must have either uploaded images OR generation prompts (not both)
   - Image filenames must match product IDs for proper association

3. **Brand Logo Usage**:
   - Logo is used as a reference image for Gemini (visual conditioning)

4. **Aspect Ratio Generation**:
   - Base 1:1 image is generated first using Gemini (when logo present) or OpenAI
   - Additional aspect ratios (9:16, 16:9) are generated using OpenAI DALL-E 3
   - All aspect ratios use the same enhanced prompt for consistency

5. **Locale Handling**:
   - Call-to-action (CTA) text uses English (en-US) locale for image generation
   - Other locales are stored in the brief but not currently used in rendering

6. **Template Format**:
   - Template version must follow semantic versioning (e.g., `bottom-cta@1.3.0`)
   - Templates are validated but not currently applied (future feature)

### Limitations

1. **Concurrency**:
   - Background tasks run sequentially within a campaign
   - Multiple campaigns can process in parallel (thanks to async architecture)
   - Async-first design (FastAPI + Uvicorn) allows vertical scaling to handle many concurrent users
   - Horizontal scaling supported via stateless design (can run multiple server instances behind load balancer)
   - No distributed task queue (not needed at current scale)

2. **Generation Time**:
   - Each product image takes 5-15 seconds to generate
   - Aspect ratio variations add 5-10 seconds per variant
   - Total time scales linearly with: `products × (1 + aspect_ratios)`

3. **Error Recovery**:
   - If generation fails mid-campaign, entire campaign is marked `failed`
   - No automatic retry mechanism (must manually re-trigger)
   - Partial results are preserved in Dropbox

4. **Storage Costs**:
   - All artifacts stored permanently in Dropbox
   - No automatic cleanup of old campaigns
   - Large campaigns (many products/locales) consume significant storage

5. **API Rate Limits**:
   - Gemini API: 2 requests/minute (free tier), 1000/minute (paid)
   - OpenAI API: 5 requests/minute (tier 1), 500/minute (tier 5)
   - No built-in rate limiting or backoff (relies on API errors)

6. **Image Quality**:
   - Generated images may not perfectly match brand guidelines
   - Text rendering in images can be inconsistent (AI limitation)
   - Manual review recommended before publishing

7. **Localization**:
   - CTA text is embedded in generated images (not editable post-generation)
   - No support for right-to-left (RTL) languages
   - Font selection is controlled by AI model, not configurable

8. **Browser Support**:
   - Web UI requires modern browser with ES6+ support
   - Bootstrap 5.3.3 for styling
   - No IE11 support

9. **Security**:
   - API keys stored in `.env` file (not encrypted)
   - No authentication on API endpoints
   - Intended for internal use only (not production-ready for public access)

10. **Testing**:
    - Integration tests require live API keys
    - Some tests make real API calls (consume quota)
    - No mocking of external services in current test suite

## Testing

### Run all tests
```bash
PYTHONPATH=src pytest tests/ -v
```

### Run specific test suites
```bash
# Unit tests only (no API calls)
PYTHONPATH=src pytest tests/unit/ -v

# Integration tests (requires API keys)
PYTHONPATH=src pytest tests/integration/ -v

# Specific test file
PYTHONPATH=src pytest tests/unit/test_briefs_pure.py -v
```

### Integration Test Requirements
Integration tests require valid API credentials in `.env`:
- `DROPBOX_ACCESS_TOKEN` - for Dropbox tests
- `GEMINI_API_KEY` - for Gemini tests
- `OPENAI_API_KEY` - for OpenAI tests

## Project Structure

```
server/
├── src/
│   ├── app.py                    # FastAPI application and endpoints
│   ├── orchestrator.py           # Orchestrator agent for generation pipeline
│   ├── briefs.py                # Campaign brief management service
│   ├── storage.py               # Dropbox storage adapter
│   ├── gemini.py                # Google Gemini API client
│   ├── openai_image.py          # OpenAI DALL-E 3 client
│   ├── genai_providers.py       # GenAI provider selection logic
│   ├── generation_logs.py       # Generation event logging service
│   ├── models.py                # Pydantic data models
│   ├── config.py                # Configuration management
│   └── assets.py                # Asset path utilities
├── static/
│   ├── index.html               # Home page
│   ├── upload-brief.html        # Brief upload form
│   ├── briefs.html              # Briefs list view
│   └── css/                     # Bootstrap styles
├── tests/
│   ├── unit/                    # Unit tests (no external dependencies)
│   └── integration/             # Integration tests (live API calls)
├── example-briefs/              # Example campaign briefs
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment configuration
└── README.md                    # This file
```

## Support & Contributing

For questions or issues:
1. Check the [API documentation](http://localhost:1854/docs) (Swagger UI)
2. Review example briefs in `example-briefs/`
3. Check generation logs in Dropbox under `/briefs/{campaign-id}/logs/`