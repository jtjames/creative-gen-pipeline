"""FastAPI application for the Creative Automation API scaffold."""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from .config import Settings, get_settings
from .storage import DropboxStorage

DEFAULT_PORT = 1854


def build_storage(settings: Settings = Depends(get_settings)) -> DropboxStorage:
    return DropboxStorage(settings=settings)


def create_app() -> FastAPI:
    """Construct the FastAPI application using functional dependencies."""
    app = FastAPI(title="Creative Automation API")

    @app.get("/")
    async def root():  # pragma: no cover - trivial route
        """Return a friendly status message for smoke testing."""
        return JSONResponse({"message": "Creative Automation API says hello!"})

    @app.get("/health")
    async def health():  # pragma: no cover - trivial route
        """Expose a lightweight liveness endpoint."""
        return JSONResponse({"status": "ok"})

    @app.get("/storage/temporary-link")
    async def temporary_link(path: str, storage: DropboxStorage = Depends(build_storage)):
        """Generate a temporary download link for a Dropbox file path."""
        try:
            link = storage.generate_temporary_link(path)
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        return {"path": path, "link": link}

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("src.app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
