# Creative Automation API (Server)

A minimal FastAPI server scaffold for the Creative Automation System. You can run it locally to verify the `/` and `/health` endpoints before wiring in the full orchestration flow.

## Prerequisites
- Python 3.10+
- `pip` or another Python package manager

## Setup & Run
```bash
# from the repo root
cd creative-gen-pipeline/server

# (optional) create & activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# start the development server (auto-reload enabled)
uvicorn app:app --reload --port 1854
```

The server listens on `http://localhost:1854` by default in this project. Need a different port? adjust the flag, e.g. `--port 5000`.

Sample checks:
```bash
curl http://localhost:1854/
curl http://localhost:1854/health
```
Use `CTRL+C` to stop the server.
