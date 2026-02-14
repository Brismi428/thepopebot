"""
FastAPI bridge template — serves as the base for generated API bridges.

This template provides:
- CORS middleware configuration
- Health check endpoint
- Error handling middleware
- Static file serving for the Next.js frontend
- File upload/download support patterns

Generated API bridges extend this with tool-specific endpoints.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
import sys
import time
import traceback
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the system root to Python path so tools can be imported
SYSTEM_ROOT = Path(__file__).parent.parent
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("API bridge starting up")
    yield
    logger.info("API bridge shutting down")


app = FastAPI(
    title="{SYSTEM_NAME} API",
    description="API bridge for {SYSTEM_NAME} WAT system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin in development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch unhandled exceptions and return structured error."""
    logger.error("Unhandled error: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "detail": "An unexpected error occurred. Check server logs for details.",
        },
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system": "{SYSTEM_NAME}",
    }


# --- Tool endpoints are generated below this line ---
# {TOOL_ENDPOINTS}

# --- Pipeline endpoint ---
# {PIPELINE_ENDPOINT}

# --- Static file serving (must be last) ---
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "out"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
