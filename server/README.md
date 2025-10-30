# Creative Automation API (Server)

A minimal FastAPI server scaffold for the Creative Automation System. The server currently integrates with Dropbox for artifact storage and will later connect to Google Gemini for creative generation. Code style guidance: favor pure functional Python where practical; keep side effects localized to integration boundaries (HTTP handlers, storage adapters).

## Prerequisites
- Python 3.10+
- `pip` or another Python package manager
- A Dropbox app access token with `files.metadata.read/write` and `files.content.read/write` scopes

## Setup & Run
```bash
# from the repo root
cd creative-gen-pipeline/server

# (optional) create & activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# configure environment
cp .env.example .env  # edit values with your Dropbox credentials

# start the development server (auto-reload enabled)
uvicorn app:app --reload --port 1854
```

The server listens on `http://localhost:1854` by default in this project. Need a different port? adjust the flag, e.g. `--port 5000`.

## Endpoints
```bash
curl http://localhost:1854/
curl http://localhost:1854/health
curl "http://localhost:1854/storage/temporary-link?path=campaigns/demo/creative.png"
```
`/storage/temporary-link` returns a temporary Dropbox download link for the requested path relative to the configured root.

## Configuration
Environment variables (or `.env`) recognised by the server:
- `DROPBOX_ACCESS_TOKEN`: OAuth access token for Dropbox API calls.
- `DROPBOX_ROOT_PATH`: Base folder for creative assets (default `/`).
- `TEMPORARY_LINK_TTL_SECONDS`: Desired lifetime for generated temporary links (Dropbox enforces a 4-hour maximum).

## Integration Tests
Run `pytest tests/integration` (or `make test-integration`) to execute live checks.
- Dropbox test uploads a temporary artifact, generates a download link, and cleans up. It fails fast if `DROPBOX_ACCESS_TOKEN` is missing.
- Gemini test sends a lightweight prompt to the Google AI Studio API (defaults to `models/gemini-2.5-flash`) and asserts a text response. It fails fast if `GEMINI_API_KEY` is missing or the configured model returns 404—set `GEMINI_MODEL` when you need a different model.

## Next Steps
As additional agents are implemented, expand this server with `/api/generate` and `/api/report` endpoints, reuse the Dropbox helper to persist outputs, and introduce the Google Gemini adapter for deterministic creative generation.
