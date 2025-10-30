# Campaign Brief API Documentation

## Overview

The Campaign Brief API provides endpoints for managing campaign briefs that drive creative generation. Briefs are stored in Dropbox and treated as a document database, with each campaign stored in its own folder structure.

## Storage Structure

Briefs are stored in Dropbox with the following hierarchy:

```
/briefs/
  /{campaign_id}/
    /brief.json          # Campaign brief data
    /metadata.json       # Upload timestamp, version, status
```

This structure allows for:
- Easy organization by campaign
- Atomic updates per campaign
- Simple backup and replication
- Clear separation from generated assets

## API Endpoints

### 1. Upload Campaign Brief

**Endpoint:** `POST /briefs`

**Description:** Upload a new campaign brief to the system.

**Request Body:**
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
      "negative_prompt": "string (optional)"
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

**Validation Rules:**
- Campaign ID must be unique
- At least 2 products required
- All locales must have corresponding message and CTA translations
- Aspect ratios must be from: `["1:1", "9:16", "16:9"]`
- Template must match pattern: `name@major.minor.patch`
- Brand primary_hex must be valid hex color: `#RRGGBB`

**Error Responses:**
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Storage error

**Example:**
```bash
curl -X POST http://localhost:1854/briefs \
  -H "Content-Type: application/json" \
  -d @examples/sample-brief.json
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
  },
  {
    "campaign_id": "holiday-2025",
    "target_region": "Europe",
    "target_audience": "Families with children",
    "uploaded_at": "2025-10-29T10:20:30.456Z",
    "status": "completed",
    "product_count": 5,
    "locale_count": 4
  }
]
```

**Status Values:**
- `pending` - Brief uploaded, generation not started
- `processing` - Creative generation in progress
- `completed` - Generation completed successfully
- `failed` - Generation failed

**Example:**
```bash
curl http://localhost:1854/briefs
```

---

### 3. Get Campaign Brief

**Endpoint:** `GET /briefs/{campaign_id}`

**Description:** Retrieve the full campaign brief for a specific campaign.

**Path Parameters:**
- `campaign_id` - The campaign identifier

**Response:** `200 OK`
```json
{
  "campaign": "summer-2025-promo",
  "target_region": "North America",
  "target_audience": "Young professionals aged 25-35",
  "locales": ["en-US", "es-MX"],
  "message": {
    "en-US": "Summer savings are here!",
    "es-MX": "¡Llegaron los ahorros de verano!"
  },
  "cta": {
    "en-US": "Shop Now",
    "es-MX": "Comprar Ahora"
  },
  "products": [...],
  "brand": {...},
  "aspect_ratios": ["1:1", "9:16"],
  "template": "bottom-cta@1.3.0"
}
```

**Error Responses:**
- `404 Not Found` - Campaign brief does not exist
- `500 Internal Server Error` - Storage error

**Example:**
```bash
curl http://localhost:1854/briefs/summer-2025-promo
```

---

## Data Models

### CampaignBrief

The main campaign brief schema.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| campaign | string | Yes | Unique campaign identifier |
| target_region | string | Yes | Geographic target region |
| target_audience | string | Yes | Target audience description |
| locales | string[] | Yes | List of locale codes (min 1) |
| message | object | Yes | Localized headline messages |
| cta | object | Yes | Localized call-to-action text |
| products | Product[] | Yes | Products to feature (min 2) |
| brand | Brand | Yes | Brand identity configuration |
| aspect_ratios | string[] | Yes | Target aspect ratios (min 1) |
| template | string | Yes | Template version (format: name@x.y.z) |

### Product

Product configuration for creative generation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique product identifier |
| name | string | Yes | Product display name |
| prompt | string | Yes | Image generation prompt |
| negative_prompt | string | No | Negative prompt for generation |

### Brand

Brand identity configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| primary_hex | string | Yes | Primary brand color (#RRGGBB) |
| logo_path | string | Yes | Path to logo in brand library |

### BriefMetadata

Metadata about a stored campaign brief.

| Field | Type | Description |
|-------|------|-------------|
| campaign_id | string | Campaign identifier |
| uploaded_at | datetime | Upload timestamp (UTC) |
| version | string | Brief format version |
| status | string | Processing status |

---

## Workflow Example

### 1. Upload a Brief
```bash
curl -X POST http://localhost:1854/briefs \
  -H "Content-Type: application/json" \
  -d @examples/sample-brief.json
```

### 2. List All Briefs
```bash
curl http://localhost:1854/briefs
```

### 3. Retrieve Specific Brief
```bash
curl http://localhost:1854/briefs/summer-2025-promo
```

### 4. Generate Creatives (Future Endpoint)
```bash
# This will trigger the orchestrator to generate creatives
curl -X POST http://localhost:1854/api/generate \
  -F "brief_id=summer-2025-promo"
```

---

## Integration with Generation Pipeline

Once a brief is uploaded:

1. **Brief Upload** → Stored in `/briefs/{campaign_id}/brief.json`
2. **Status: pending** → Brief is validated and ready
3. **Generation Trigger** → Orchestrator processes the brief
4. **Status: processing** → Creatives being generated
5. **Assets Created** → Stored in `/campaigns/{campaign_id}/...`
6. **Status: completed** → Generation finished successfully

The brief serves as the input contract for the entire creative generation pipeline as defined in AGENTS.md.

---

## Error Handling

### Validation Errors (422)

When validation fails, the response includes detailed error information:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "campaign"],
      "msg": "Field required"
    },
    {
      "type": "value_error",
      "loc": ["body", "aspect_ratios", 0],
      "msg": "Invalid aspect ratio 'invalid'. Must be one of {'1:1', '9:16', '16:9'}"
    }
  ]
}
```

### Storage Errors (500)

When Dropbox storage operations fail:

```json
{
  "detail": "Failed to upload brief: Unable to ensure Dropbox folder"
}
```

---

## Testing

### Unit Tests
```bash
cd creative-gen-pipeline/server
source .venv/bin/activate
python -m pytest tests/unit/test_brief_endpoints.py -v
```

### Integration Tests
```bash
# Requires DROPBOX_ACCESS_TOKEN environment variable
python -m pytest tests/integration/test_brief_workflow.py -v
```

---

## Notes

- All timestamps are in UTC
- Brief IDs (campaign field) must be unique
- Briefs are immutable once uploaded (updates require new upload)
- Storage paths are relative to configured Dropbox root
- All API responses use JSON format
- FastAPI provides automatic OpenAPI documentation at `/docs`
