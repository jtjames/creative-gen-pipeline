"""FastAPI application for the Creative Automation API scaffold."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from config import Settings, get_settings
from storage import DropboxStorage

DEFAULT_PORT = 1854

StorageFactory = Callable[[Settings], DropboxStorage]
SettingsProvider = Callable[[], Settings]


def create_app(
    *,
    settings_provider: SettingsProvider = get_settings,
    storage_factory: StorageFactory = lambda settings: DropboxStorage(settings=settings),
) -> FastAPI:
    """Application factory to allow functional dependency injection."""
    app = FastAPI(title="Creative Automation API")

    def get_storage() -> DropboxStorage:
        settings = settings_provider()
        try:
            return storage_factory(settings)
        except RuntimeError as exc:  # pragma: no cover - defensive guard
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    @app.get("/")
    async def root():  # pragma: no cover - trivial route
        """Return a friendly status message for smoke testing."""
        return JSONResponse({"message": "Creative Automation API says hello!"})

    @app.get("/health")
    async def health():  # pragma: no cover - trivial route
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

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
