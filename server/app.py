"""Minimal FastAPI application for the Creative Automation API scaffold."""
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from config import get_settings
from storage import DropboxStorage

DEFAULT_PORT = 1854

app = FastAPI(title="Creative Automation API")


def get_storage() -> DropboxStorage:
    """Provide a Dropbox storage instance for request handlers."""
    settings = get_settings()
    try:
        return DropboxStorage(settings=settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.get("/")
async def root():
    """Return a friendly status message for smoke testing."""
    return JSONResponse({"message": "Creative Automation API says hello!"})


@app.get("/health")
async def health():
    """Expose a lightweight liveness endpoint."""
    return JSONResponse({"status": "ok"})


@app.get("/storage/temporary-link")
async def temporary_link(path: str, storage: DropboxStorage = Depends(get_storage)):
    """Generate a temporary download link for a Dropbox file path."""
    try:
        link = storage.generate_temporary_link(path)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return {"path": path, "link": link}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
