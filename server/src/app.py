"""FastAPI application for the Creative Automation API scaffold."""
from __future__ import annotations

import json
from typing import List
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

from .config import Settings, get_settings
from .storage import DropboxStorage
from .briefs import BriefService
from .models import (
    CampaignBrief,
    BriefUploadResponse,
    BriefListItem,
)

DEFAULT_PORT = 1854


def build_storage(settings: Settings = Depends(get_settings)) -> DropboxStorage:
    return DropboxStorage(settings=settings)


def build_brief_service(storage: DropboxStorage = Depends(build_storage)) -> BriefService:
    return BriefService(storage=storage)


def create_app() -> FastAPI:
    """Construct the FastAPI application using functional dependencies."""
    app = FastAPI(title="Creative Automation API")

    # Mount static files
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():  # pragma: no cover - trivial route
        """Serve the home page."""
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/upload-brief.html")
    async def upload_form():  # pragma: no cover
        """Serve the upload form."""
        return FileResponse(str(static_dir / "upload-brief.html"))

    @app.get("/briefs.html")
    async def briefs_list():  # pragma: no cover
        """Serve the briefs list page."""
        return FileResponse(str(static_dir / "briefs.html"))

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

    @app.post("/briefs", response_model=BriefUploadResponse, status_code=status.HTTP_201_CREATED)
    async def upload_brief(
        brief_json: str = Form(..., description="Campaign brief JSON"),
        product_images: List[UploadFile] = File(..., description="Product images (one per product)"),
        brief_service: BriefService = Depends(build_brief_service)
    ):
        """
        Upload a new campaign brief with product images.

        Accepts multipart/form-data with:
        - brief_json: JSON string containing the campaign brief
        - product_images: File uploads for each product (filename should match product_id)

        Validates the brief against the schema and stores it in Dropbox along with product images.
        Returns the upload metadata including storage paths.
        """
        try:
            # Parse and validate brief JSON
            brief_data = json.loads(brief_json)
            brief = CampaignBrief(**brief_data)

            # Read product images into memory
            product_image_map = {}
            for upload_file in product_images:
                # Extract product_id from filename (e.g., "product-1.jpg" -> "product-1")
                product_id = upload_file.filename.rsplit('.', 1)[0] if '.' in upload_file.filename else upload_file.filename
                image_bytes = await upload_file.read()

                # Validate image size (10MB max)
                if len(image_bytes) > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Image for product {product_id} exceeds 10MB limit"
                    )

                product_image_map[product_id] = image_bytes

            # Verify all products have images
            missing_images = [p.id for p in brief.products if p.id not in product_image_map]
            if missing_images:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Missing images for products: {', '.join(missing_images)}"
                )

            # Upload brief and images
            response = brief_service.upload_brief(brief, product_images=product_image_map)
            return response

        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid JSON in brief_json: {str(exc)}"
            ) from exc
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors()
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc)
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload brief: {str(exc)}"
            ) from exc

    @app.get("/briefs", response_model=List[BriefListItem])
    async def list_briefs(brief_service: BriefService = Depends(build_brief_service)):
        """
        List all campaign briefs.

        Returns a summary of all briefs stored in the system,
        sorted by upload time (most recent first).
        """
        try:
            briefs = brief_service.list_briefs()
            return briefs
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list briefs: {str(exc)}"
            ) from exc

    @app.get("/briefs/{campaign_id}", response_model=CampaignBrief)
    async def get_brief(
        campaign_id: str,
        brief_service: BriefService = Depends(build_brief_service)
    ):
        """
        Retrieve a specific campaign brief by ID.

        Returns the full brief JSON for the specified campaign.
        """
        try:
            brief = brief_service.get_brief(campaign_id)
            if not brief:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Brief not found for campaign: {campaign_id}"
                )
            return brief
        except HTTPException:
            raise
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve brief: {str(exc)}"
            ) from exc

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("src.app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
