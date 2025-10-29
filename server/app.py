"""Minimal FastAPI application for the Creative Automation API scaffold."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

DEFAULT_PORT = 1854

app = FastAPI(title="Creative Automation API")


@app.get("/")
async def root():
    """Return a friendly status message for smoke testing."""
    return JSONResponse({"message": "Creative Automation API says hello!"})


@app.get("/health")
async def health():
    """Expose a lightweight liveness endpoint."""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=DEFAULT_PORT, reload=True)
