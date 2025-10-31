"""FastAPI application for the Creative Automation API scaffold."""
from __future__ import annotations

import json
from typing import List
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

from .config import Settings, get_settings
from .storage import DropboxStorage
from .briefs import BriefService
from .orchestrator import OrchestratorAgent
from .assets import needs_generation
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


def build_orchestrator(
    brief_service: BriefService = Depends(build_brief_service),
    settings: Settings = Depends(get_settings),
) -> OrchestratorAgent:
    """Construct an orchestrator using the shared brief service and settings."""

    return OrchestratorAgent(
        brief_service=brief_service,
        storage=brief_service.storage,
        settings=settings,
    )


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
    async def health(storage: DropboxStorage = Depends(build_storage), settings: Settings = Depends(get_settings)):  # pragma: no cover - trivial route
        """Expose a lightweight liveness endpoint."""
        from datetime import datetime, timezone
        import platform

        # Gather system information
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        python_version = platform.python_version()
        system = platform.system()

        # Check Dropbox connectivity
        dropbox_status = "Connected"
        try:
            storage.ensure_folder("/briefs")
            dropbox_status = "✅ Connected"
        except Exception:
            dropbox_status = "❌ Connection Failed"

        # Check GenAI provider
        genai_provider = settings.genai_provider or "Not configured"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Health Check - Creative Automation</title>
            <link rel="stylesheet" href="/static/css/bootstrap.min.css">
            <style>
                :root {{
                    --brand-primary: #4f46e5;
                }}

                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }}

                .health-card {{
                    background: white;
                    border-radius: 1.5rem;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 600px;
                    width: 100%;
                    overflow: hidden;
                }}

                .health-header {{
                    background: linear-gradient(135deg, var(--brand-primary) 0%, #6366f1 100%);
                    color: white;
                    padding: 2rem;
                    text-align: center;
                }}

                .health-header h1 {{
                    font-size: 2rem;
                    font-weight: 700;
                    margin: 0 0 0.5rem 0;
                }}

                .status-badge {{
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 0.5rem 1.5rem;
                    border-radius: 2rem;
                    font-weight: 600;
                    font-size: 1.125rem;
                    backdrop-filter: blur(10px);
                }}

                .health-body {{
                    padding: 2rem;
                }}

                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 1rem 0;
                    border-bottom: 1px solid #e5e7eb;
                }}

                .info-row:last-child {{
                    border-bottom: none;
                }}

                .info-label {{
                    color: #6b7280;
                    font-weight: 500;
                }}

                .info-value {{
                    color: #111827;
                    font-weight: 600;
                }}

                .pulse {{
                    animation: pulse 2s ease-in-out infinite;
                }}

                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.6; }}
                }}

                .footer-links {{
                    background: #f9fafb;
                    padding: 1.5rem 2rem;
                    text-align: center;
                }}

                .footer-links a {{
                    color: var(--brand-primary);
                    text-decoration: none;
                    margin: 0 1rem;
                    font-weight: 500;
                }}

                .footer-links a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="health-card">
                <div class="health-header">
                    <h1>Creative Automation API</h1>
                    <div class="status-badge pulse">
                        ✅ System Operational
                    </div>
                </div>

                <div class="health-body">
                    <div class="info-row">
                        <span class="info-label">Status</span>
                        <span class="info-value">Healthy</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Timestamp</span>
                        <span class="info-value">{current_time}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Python Version</span>
                        <span class="info-value">{python_version}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Platform</span>
                        <span class="info-value">{system}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Dropbox Storage</span>
                        <span class="info-value">{dropbox_status}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">GenAI Provider</span>
                        <span class="info-value">{genai_provider}</span>
                    </div>
                </div>

                <div class="footer-links">
                    <a href="/">Home</a>
                    <a href="/briefs.html">View Briefs</a>
                    <a href="/upload-brief.html">Upload Brief</a>
                    <a href="/docs">API Docs</a>
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    @app.get("/storage/temporary-link")
    async def temporary_link(path: str, storage: DropboxStorage = Depends(build_storage)):
        """Generate a temporary download link for a Dropbox file path."""
        try:
            link = storage.generate_temporary_link(path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        return {"path": path, "link": link}

    @app.post("/briefs", response_model=BriefUploadResponse, status_code=status.HTTP_201_CREATED)
    async def upload_brief(
        background_tasks: BackgroundTasks,
        brief_json: str = Form(..., description="Campaign brief JSON"),
        product_images: List[UploadFile] = File(default=[], description="Product images (optional - will generate if missing)"),
        brand_logo: UploadFile | None = File(None, description="Optional brand logo image"),
        brief_service: BriefService = Depends(build_brief_service),
        orchestrator: OrchestratorAgent = Depends(build_orchestrator),
    ):
        """
        Upload a new campaign brief with optional product images.

        Accepts multipart/form-data with:
        - brief_json: JSON string containing the campaign brief
        - product_images: File uploads for each product (optional - will be generated if missing)
        - brand_logo: Optional brand logo image

        Products without uploaded images must have prompts for AI generation.
        Validates the brief against the schema and stores it in Dropbox.
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

            # Mark products without images as needing generation
            # Products can either have uploaded images OR prompts for generation
            for product in brief.products:
                if product.id in product_image_map:
                    continue

                if needs_generation(product.image_path):
                    if not product.prompt or not product.prompt.strip():
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=(
                                f"Product {product.id} must have either an uploaded image or a generation prompt"
                            )
                        )
                    product.image_path = "pending-generation"

            # Read brand logo if provided
            brand_logo_data = None
            if brand_logo is not None:
                logo_bytes = await brand_logo.read()
                if logo_bytes:
                    if len(logo_bytes) > 10 * 1024 * 1024:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Brand logo exceeds 10MB limit"
                        )
                    brand_logo_data = (brand_logo.filename or "brand-logo", logo_bytes)

            # Upload brief and images
            response = brief_service.upload_brief(
                brief,
                product_images=product_image_map if product_image_map else None,
                brand_logo=brand_logo_data
            )

            # Check if any products need generation
            has_pending_generation = any(
                needs_generation(product.image_path) for product in brief.products
            )

            # If assets need generation, trigger it automatically in the background
            if has_pending_generation:
                campaign_id = response.campaign_id
                background_tasks.add_task(
                    orchestrator.generate_campaign,
                    campaign_id
                )
                # Convert to dict to add new fields
                response_dict = response.model_dump()
                response_dict["generation_triggered"] = True
                response_dict["message"] = f"Brief uploaded. Generating {sum(1 for p in brief.products if needs_generation(p.image_path))} missing product image(s) in background."
                return response_dict
            else:
                # Convert to dict to add new fields
                response_dict = response.model_dump()
                response_dict["generation_triggered"] = False
                response_dict["message"] = "Brief uploaded. All product images provided."
                return response_dict

        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid JSON in brief_json: {str(exc)}"
            ) from exc
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=json.loads(exc.json())
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
            # Convert to dict format for JSONResponse
            briefs_data = [
                {
                    "campaign_id": b.campaign_id,
                    "target_region": b.target_region,
                    "target_audience": b.target_audience,
                    "uploaded_at": b.uploaded_at.isoformat(),
                    "status": b.status,
                    "product_count": b.product_count,
                    "locale_count": b.locale_count,
                    "product_image_paths": b.product_image_paths,
                }
                for b in briefs
            ]
            return JSONResponse(
                content=briefs_data,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
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

    @app.post("/api/generate")
    async def trigger_generation(
        campaign_id: str = Form(..., description="Campaign identifier to generate"),
        orchestrator: OrchestratorAgent = Depends(build_orchestrator),
    ):
        """Kick off creative generation for a stored campaign brief."""

        try:
            return await orchestrator.generate_campaign(campaign_id)
        except RuntimeError as exc:
            detail = str(exc)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if "not found" in detail.lower():
                status_code = status.HTTP_404_NOT_FOUND
            raise HTTPException(status_code=status_code, detail=detail) from exc

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("src.app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
