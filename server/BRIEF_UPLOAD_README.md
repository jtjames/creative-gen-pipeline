# Campaign Brief Upload System

## Overview

A complete REST API for uploading and managing campaign briefs using Dropbox as a document database. Campaign briefs serve as input contracts for the creative generation pipeline.

## What Was Implemented

### 1. Data Models (`src/models.py`)
- **CampaignBrief**: Full brief schema with validation
  - Minimum 2 products required
  - Aspect ratios must be from: `["1:1", "9:16", "16:9"]`
  - Template must follow `name@major.minor.patch` format
  - All locales must have translations for messages and CTAs
- **Product**: Product configuration for generation
- **Brand**: Brand identity (colors, logo path)
- **BriefMetadata**: Upload tracking and status
- **Response Models**: BriefUploadResponse, BriefListItem

### 2. Brief Service (`src/briefs.py`)
Business logic layer for brief management:
- `upload_brief()` - Store brief and metadata in Dropbox
- `get_brief()` - Retrieve specific brief by campaign ID
- `get_brief_metadata()` - Get brief status and upload info
- `list_briefs()` - List all briefs with summaries
- `delete_brief()` - Remove brief from storage
- `update_brief_status()` - Update processing status

### 3. Storage Enhancement (`src/storage.py`)
Added `download_bytes()` method to DropboxStorage for retrieving files.

### 4. API Endpoints (`src/app.py`)
Three new REST endpoints:
- `POST /briefs` - Upload new campaign brief (201 Created)
- `GET /briefs` - List all briefs with summaries
- `GET /briefs/{campaign_id}` - Get full brief details

### 5. Tests
**Unit Tests** (`tests/unit/test_brief_endpoints.py`):
- 10 tests covering all endpoints
- Validation error scenarios
- Mock-based for fast execution

**Integration Tests** (`tests/integration/test_brief_workflow.py`):
- 8 tests with real Dropbox operations
- Upload, retrieve, list, delete workflows
- Multi-brief scenarios

### 6. Documentation
- **API Documentation** (`docs/BRIEF_API.md`)
  - Complete endpoint reference
  - Request/response examples
  - Validation rules
  - Error handling guide
  - Workflow examples
- **Example Brief** (`examples/sample-brief.json`)
  - 3 products, 3 locales, 3 aspect ratios
  - Fully annotated

## Storage Structure

```
/briefs/
  /{campaign_id}/
    /brief.json          # Campaign brief data
    /metadata.json       # Upload timestamp, version, status
```

## Quick Start

### Start the Server
```bash
cd creative-gen-pipeline/server
source .venv/bin/activate
make run
```

### Upload a Brief
```bash
curl -X POST http://localhost:1854/briefs \
  -H "Content-Type: application/json" \
  -d @examples/sample-brief.json
```

### List All Briefs
```bash
curl http://localhost:1854/briefs
```

### Get Specific Brief
```bash
curl http://localhost:1854/briefs/summer-2025-promo
```

## Running Tests

### Unit Tests (Fast)
```bash
source .venv/bin/activate
python -m pytest tests/unit/test_brief_endpoints.py -v
```

### Integration Tests (Requires Dropbox)
```bash
# Ensure DROPBOX_ACCESS_TOKEN is set in .env
python -m pytest tests/integration/test_brief_workflow.py -v
```

## API Features

### Validation
- **Comprehensive schema validation** using Pydantic
- **Locale consistency checks** - all locales must have translations
- **Product count** - minimum 2 required
- **Aspect ratio validation** - only allowed values
- **Template format** - must match semver pattern
- **Brand color** - must be valid hex (#RRGGBB)

### Error Responses
- `422 Unprocessable Entity` - Validation errors with details
- `404 Not Found` - Brief doesn't exist
- `500 Internal Server Error` - Storage errors

### Status Tracking
Briefs have four states:
- `pending` - Uploaded, awaiting generation
- `processing` - Generation in progress
- `completed` - Successfully generated
- `failed` - Generation failed

## Architecture Integration

This brief upload system integrates with the Creative Automation System architecture defined in `AGENTS.md`:

1. **Brief Upload** (This System) → Validates and stores briefs
2. **API Gateway Agent** → Routes generation requests
3. **Orchestrator Agent** → Loads brief and triggers pipeline
4. **Generation Pipeline** → Creates assets per brief spec
5. **Reporting Agent** → Links briefs to generated assets

## Files Created/Modified

### New Files
- `src/models.py` - Pydantic data models
- `src/briefs.py` - Brief service logic
- `tests/unit/test_brief_endpoints.py` - Unit tests
- `tests/integration/test_brief_workflow.py` - Integration tests
- `examples/sample-brief.json` - Example brief
- `docs/BRIEF_API.md` - API documentation

### Modified Files
- `src/app.py` - Added 3 new endpoints
- `src/storage.py` - Added download_bytes() method

## Next Steps

To integrate with the generation pipeline:

1. **Add Generation Trigger**
   ```python
   POST /api/generate
   {
     "campaign_id": "summer-2025-promo"
   }
   ```

2. **Update Brief Status During Generation**
   ```python
   brief_service.update_brief_status(campaign_id, "processing")
   ```

3. **Link Generated Assets to Briefs**
   - Store brief_id in report.json
   - Reference brief metadata in /api/report endpoint

4. **Add Brief Validation Endpoint**
   ```python
   POST /briefs/validate
   # Returns validation results without storing
   ```

## API Documentation

View interactive API docs when server is running:
- **Swagger UI**: http://localhost:1854/docs
- **ReDoc**: http://localhost:1854/redoc

For detailed documentation, see `docs/BRIEF_API.md`.
