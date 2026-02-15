"""
Instagram Publisher WAT System — API Bridge

FastAPI application that wraps each Python tool as an HTTP endpoint.
Serves the Next.js static export at / and the API at /api/*.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import json
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

# Add the api directory to Python path so models can be imported
API_DIR = Path(__file__).parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Import Pydantic models
from models.validate_content import ValidateContentRequest
from models.enrich_content import EnrichContentRequest
from models.instagram_create_container import InstagramCreateContainerRequest
from models.instagram_publish_container import InstagramPublishContainerRequest
from models.write_result import WriteResultRequest
from models.generate_report import GenerateReportRequest
from models.git_commit import GitCommitRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("Instagram Publisher WAT System API bridge starting up")
    yield
    logger.info("Instagram Publisher WAT System API bridge shutting down")


app = FastAPI(
    title="Instagram Publisher WAT System API",
    description="API bridge for Instagram Publisher WAT System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8001").split(","),
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
            "detail": "An unexpected error occurred.",
        },
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system": "Instagram Publisher WAT System",
    }


@app.post("/api/validate-content")
async def run_validate_content(request: ValidateContentRequest):
    """Run the validate_content tool."""
    try:
        from tools.validate_content import main as tool_main

        content = json.loads(request.content)
        result = tool_main(content=content)
        return JSONResponse(content=result)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON content: {e}")
    except Exception as e:
        logger.error("validate_content error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enrich-content")
async def run_enrich_content(request: EnrichContentRequest):
    """Run the enrich_content tool."""
    try:
        from tools.enrich_content import main as tool_main

        content = json.loads(request.content)
        kwargs = {"content": content}
        if request.enhancement_type:
            kwargs["enhancement_type"] = request.enhancement_type

        result = tool_main(**kwargs)
        return JSONResponse(content=result)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON content: {e}")
    except Exception as e:
        logger.error("enrich_content error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/instagram-create-container")
async def run_instagram_create_container(request: InstagramCreateContainerRequest):
    """Run the instagram_create_container tool."""
    try:
        from tools.instagram_create_container import main as tool_main

        kwargs = {
            "image_url": request.image_url,
            "caption": request.caption,
            "business_account_id": request.business_account_id,
        }
        if request.access_token:
            kwargs["access_token"] = request.access_token

        result = tool_main(**kwargs)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error("instagram_create_container error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/instagram-publish-container")
async def run_instagram_publish_container(request: InstagramPublishContainerRequest):
    """Run the instagram_publish_container tool."""
    try:
        from tools.instagram_publish_container import main as tool_main

        kwargs = {
            "creation_id": request.creation_id,
            "business_account_id": request.business_account_id,
        }
        if request.access_token:
            kwargs["access_token"] = request.access_token

        result = tool_main(**kwargs)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error("instagram_publish_container error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/write-result")
async def run_write_result(request: WriteResultRequest):
    """Run the write_result tool."""
    try:
        from tools.write_result import main as tool_main

        result_data = json.loads(request.result_json)
        kwargs = {"result": result_data}
        if request.output_dir:
            kwargs["output_dir"] = request.output_dir

        result = tool_main(**kwargs)
        return JSONResponse(content=result)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON result: {e}")
    except Exception as e:
        logger.error("write_result error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-report")
async def run_generate_report(request: GenerateReportRequest):
    """Run the generate_report tool."""
    try:
        from tools.generate_report import main as tool_main

        kwargs = {}
        if request.published_dir:
            kwargs["published_dir"] = request.published_dir
        if request.failed_dir:
            kwargs["failed_dir"] = request.failed_dir

        result = tool_main(**kwargs)
        # generate_report returns a string (markdown), wrap it
        if isinstance(result, str):
            return JSONResponse(content={"status": "success", "report": result})
        return JSONResponse(content=result)

    except Exception as e:
        logger.error("generate_report error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/git-commit")
async def run_git_commit(request: GitCommitRequest):
    """Run the git_commit tool."""
    try:
        from tools.git_commit import main as tool_main

        # Split comma-separated files into a list
        files = [f.strip() for f in request.files.split(",") if f.strip()]

        kwargs = {
            "files": files,
            "push": request.push,
            "auto_message": request.auto_message,
        }
        if request.message:
            kwargs["message"] = request.message

        result = tool_main(**kwargs)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error("git_commit error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run-pipeline")
async def run_pipeline(request: dict = {}):
    """Run the full tool pipeline in workflow order."""
    steps_completed = []

    try:
        # Step 1: validate_content
        logger.info("Pipeline step 1: validate_content")
        try:
            from tools.validate_content import main as validate_content_main
            result = validate_content_main(content=request)
            steps_completed.append({
                "step": 1,
                "tool": "validate_content",
                "status": "success",
                "result": result,
            })
            # If validation failed, stop the pipeline
            if result and not result.get("is_valid", True):
                return JSONResponse(content={
                    "status": "failed",
                    "steps": steps_completed,
                    "message": "Pipeline stopped: content validation failed",
                })
        except Exception as e:
            steps_completed.append({
                "step": 1,
                "tool": "validate_content",
                "status": "failed",
                "error": str(e),
            })
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed at step 1 (validate_content): {e}",
            )

        # Step 2: enrich_content
        logger.info("Pipeline step 2: enrich_content")
        try:
            from tools.enrich_content import main as enrich_content_main
            enriched = enrich_content_main(content=request, enhancement_type="all")
            enriched_content = enriched.get("enhanced_content", request) if isinstance(enriched, dict) else request
            steps_completed.append({
                "step": 2,
                "tool": "enrich_content",
                "status": "success",
                "result": enriched,
            })
        except Exception as e:
            # Enrichment is optional, continue on failure
            enriched_content = request
            steps_completed.append({
                "step": 2,
                "tool": "enrich_content",
                "status": "skipped",
                "error": str(e),
            })

        # Step 3: instagram_create_container
        logger.info("Pipeline step 3: instagram_create_container")
        try:
            from tools.instagram_create_container import main as create_container_main
            create_result = create_container_main(
                image_url=enriched_content.get("image_url", ""),
                caption=enriched_content.get("caption", ""),
                business_account_id=enriched_content.get("business_account_id", ""),
                access_token=enriched_content.get("access_token"),
            )
            steps_completed.append({
                "step": 3,
                "tool": "instagram_create_container",
                "status": "success",
                "result": create_result,
            })
        except Exception as e:
            steps_completed.append({
                "step": 3,
                "tool": "instagram_create_container",
                "status": "failed",
                "error": str(e),
            })
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed at step 3 (instagram_create_container): {e}",
            )

        # Step 4: instagram_publish_container
        logger.info("Pipeline step 4: instagram_publish_container")
        try:
            from tools.instagram_publish_container import main as publish_container_main
            creation_id = create_result.get("creation_id", "") if isinstance(create_result, dict) else ""
            publish_result = publish_container_main(
                creation_id=creation_id,
                business_account_id=enriched_content.get("business_account_id", ""),
                access_token=enriched_content.get("access_token"),
            )
            steps_completed.append({
                "step": 4,
                "tool": "instagram_publish_container",
                "status": "success",
                "result": publish_result,
            })
        except Exception as e:
            steps_completed.append({
                "step": 4,
                "tool": "instagram_publish_container",
                "status": "failed",
                "error": str(e),
            })
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed at step 4 (instagram_publish_container): {e}",
            )

        # Step 5: write_result
        logger.info("Pipeline step 5: write_result")
        try:
            from tools.write_result import main as write_result_main
            write_data = publish_result if isinstance(publish_result, dict) else {}
            write_out = write_result_main(result=write_data)
            steps_completed.append({
                "step": 5,
                "tool": "write_result",
                "status": "success",
                "result": write_out,
            })
        except Exception as e:
            steps_completed.append({
                "step": 5,
                "tool": "write_result",
                "status": "failed",
                "error": str(e),
            })

        # Step 6: generate_report
        logger.info("Pipeline step 6: generate_report")
        try:
            from tools.generate_report import main as generate_report_main
            report = generate_report_main()
            steps_completed.append({
                "step": 6,
                "tool": "generate_report",
                "status": "success",
                "result": report if isinstance(report, dict) else {"report": report},
            })
        except Exception as e:
            steps_completed.append({
                "step": 6,
                "tool": "generate_report",
                "status": "failed",
                "error": str(e),
            })

        # Step 7: git_commit
        logger.info("Pipeline step 7: git_commit")
        try:
            from tools.git_commit import main as git_commit_main
            commit_result = git_commit_main(
                files=["output/*.json", "logs/*.md"],
                auto_message=True,
                push=True,
            )
            steps_completed.append({
                "step": 7,
                "tool": "git_commit",
                "status": "success",
                "result": commit_result,
            })
        except Exception as e:
            steps_completed.append({
                "step": 7,
                "tool": "git_commit",
                "status": "failed",
                "error": str(e),
            })

        return JSONResponse(content={
            "status": "success",
            "steps": steps_completed,
            "message": "Pipeline completed successfully",
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Static file serving — Next.js export (must be last)
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "out"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
