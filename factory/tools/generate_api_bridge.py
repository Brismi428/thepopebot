"""
Generate API Bridge — Reads system_interface.json and generates a FastAPI app wrapping each tool.

For each tool: generates a Pydantic model from its argparse schema, creates a POST /api/{tool-name}
endpoint that calls the tool's main() directly via Python import.

Also generates:
- POST /api/run-pipeline (chains all tools per workflow.md ordering)
- GET /api/health, CORS middleware, file upload/download support
- Pydantic models in api/models/
- requirements.txt and Dockerfile

Inputs:
    - system_dir (str): Path to the system directory
    - manifest (str): Path to system_interface.json (default: system_dir/system_interface.json)

Outputs:
    - api/main.py — FastAPI application
    - api/models/*.py — Pydantic models per tool
    - api/requirements.txt — API dependencies
    - api/Dockerfile — Container definition

Usage:
    python generate_api_bridge.py --system-dir systems/invoice-generator/
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Type mapping from argparse types to Python/Pydantic types
ARGPARSE_TO_PYDANTIC = {
    "str": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "": "str",
}


def generate_pydantic_model(tool: dict) -> str:
    """Generate a Pydantic model for a tool's arguments."""
    tool_name = tool["name"]
    class_name = "".join(word.capitalize() for word in tool_name.split("_")) + "Request"

    fields = []
    for arg in tool.get("arguments", []):
        name = arg["name"]
        # Skip output-path args — the API manages output
        if name in ("output", "output_file", "output_dir", "output_path"):
            continue

        py_type = ARGPARSE_TO_PYDANTIC.get(arg.get("type", "str"), "str")
        required = arg.get("required", False)
        default = arg.get("default")
        help_text = arg.get("help", "")
        choices = arg.get("choices")

        if arg.get("action") in ("store_true", "store_false"):
            py_type = "bool"
            default = arg["action"] == "store_true"  # store_true defaults to False
            default = False if arg["action"] == "store_true" else True

        if choices:
            # Use Literal type for choices
            choices_str = ", ".join(f'"{c}"' if isinstance(c, str) else str(c) for c in choices)
            py_type = f"Literal[{choices_str}]"

        if arg.get("nargs") in ("+", "*"):
            py_type = f"list[{py_type}]"

        if required and default is None:
            field_str = f'    {name}: {py_type} = Field(..., description="{help_text}")'
        elif default is not None:
            if isinstance(default, str):
                field_str = f'    {name}: {py_type} = Field(default="{default}", description="{help_text}")'
            elif isinstance(default, bool):
                field_str = f'    {name}: {py_type} = Field(default={default}, description="{help_text}")'
            else:
                field_str = f'    {name}: {py_type} = Field(default={default}, description="{help_text}")'
        else:
            field_str = f'    {name}: {py_type} | None = Field(default=None, description="{help_text}")'

        fields.append(field_str)

    if not fields:
        fields.append("    pass  # No input arguments")

    # Check if we need Literal import
    needs_literal = any("Literal[" in f for f in fields)
    literal_import = "\nfrom typing import Literal" if needs_literal else ""

    return f'''"""Pydantic model for {tool_name} tool."""

from pydantic import BaseModel, Field{literal_import}


class {class_name}(BaseModel):
    """{tool.get("docstring", f"Request model for {tool_name}").split(chr(10))[0]}"""
{chr(10).join(fields)}
'''


def generate_tool_endpoint(tool: dict) -> str:
    """Generate a FastAPI endpoint function for a tool."""
    tool_name = tool["name"]
    class_name = "".join(word.capitalize() for word in tool_name.split("_")) + "Request"
    route_name = tool_name.replace("_", "-")
    output_formats = tool.get("output", {}).get("formats", ["json"])

    # Build the args list to pass to main()
    # Indented at 8 spaces to sit inside the try: block of the endpoint
    arg_mapping_lines = []
    for arg in tool.get("arguments", []):
        name = arg["name"]
        if name in ("output", "output_file", "output_dir", "output_path"):
            continue
        cli_flag = arg.get("cli_flag", f"--{name.replace('_', '-')}")
        if arg.get("action") in ("store_true", "store_false"):
            arg_mapping_lines.append(
                f'        if request.{name}:\n            argv.append("{cli_flag}")'
            )
        else:
            arg_mapping_lines.append(
                f'        if request.{name} is not None:\n            argv.extend(["{cli_flag}", str(request.{name})])'
            )

    arg_mapping = "\n".join(arg_mapping_lines)

    # Determine response type (indented at 8 spaces for inside try block)
    if "pdf" in output_formats:
        response_handling = '''
        # Check for generated file
        output_files = list(Path(tmp_dir).glob("*.pdf"))
        if output_files:
            return FileResponse(
                path=str(output_files[0]),
                media_type="application/pdf",
                filename=output_files[0].name,
            )'''
    elif "csv" in output_formats:
        response_handling = '''
        # Check for generated file
        output_files = list(Path(tmp_dir).glob("*.csv"))
        if output_files:
            return FileResponse(
                path=str(output_files[0]),
                media_type="text/csv",
                filename=output_files[0].name,
            )'''
    else:
        response_handling = ""

    return f'''
@app.post("/api/{route_name}")
async def run_{tool_name}(request: {class_name}):
    """Run the {tool_name} tool."""
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, "output.json")

    try:
        argv = ["{tool_name}.py", "--output", output_path]
{arg_mapping}

        original_argv = sys.argv
        sys.argv = argv
        try:
            from tools.{tool_name} import main as tool_main
            result = tool_main()
        except SystemExit as e:
            if e.code and e.code != 0:
                raise HTTPException(status_code=400, detail=f"{tool_name} failed with exit code {{e.code}}")
            result = None
        finally:
            sys.argv = original_argv
{response_handling}

        # Return JSON result
        if result is not None:
            return JSONResponse(content=result)

        # Try reading output file
        if os.path.isfile(output_path):
            with open(output_path, "r") as f:
                return JSONResponse(content=json.load(f))

        return JSONResponse(content={{"status": "success", "message": "{tool_name} completed"}})

    except HTTPException:
        raise
    except Exception as e:
        logger.error("{tool_name} error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
'''


def generate_pipeline_endpoint(tools: list[dict], pipeline_order: list[str]) -> str:
    """Generate the /api/run-pipeline endpoint that chains tools."""
    # Filter tools to those in pipeline order
    ordered_tools = []
    tool_map = {t["name"]: t for t in tools}
    for name in pipeline_order:
        if name in tool_map:
            ordered_tools.append(tool_map[name])

    if not ordered_tools:
        ordered_tools = tools

    step_code_lines = []
    for i, tool in enumerate(ordered_tools):
        tool_name = tool["name"]
        step_code_lines.append(f'''
        # Step {i+1}: {tool_name}
        logger.info("Pipeline step {i+1}: {tool_name}")
        try:
            from tools.{tool_name} import main as {tool_name}_main
            original_argv = sys.argv
            step_output = os.path.join(tmp_dir, "{tool_name}_output.json")
            sys.argv = ["{tool_name}.py", "--output", step_output]
            # Pass pipeline_input as the input if the tool accepts it
            if pipeline_input and os.path.isfile(pipeline_input):
                sys.argv.extend(["--input", pipeline_input] if "--input" not in " ".join(sys.argv) else [])
            result = {tool_name}_main()
            sys.argv = original_argv
            pipeline_input = step_output
            steps_completed.append({{
                "step": {i+1},
                "tool": "{tool_name}",
                "status": "success",
                "result": result,
            }})
        except SystemExit as e:
            sys.argv = original_argv
            if e.code and e.code != 0:
                steps_completed.append({{
                    "step": {i+1},
                    "tool": "{tool_name}",
                    "status": "failed",
                    "error": f"Exit code {{e.code}}",
                }})
                raise HTTPException(
                    status_code=400,
                    detail=f"Pipeline failed at step {i+1} ({tool_name}): exit code {{e.code}}",
                )
            steps_completed.append({{
                "step": {i+1},
                "tool": "{tool_name}",
                "status": "success",
            }})
        except HTTPException:
            raise
        except Exception as e:
            steps_completed.append({{
                "step": {i+1},
                "tool": "{tool_name}",
                "status": "failed",
                "error": str(e),
            }})
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed at step {i+1} ({tool_name}): {{e}}",
            )''')

    step_code = "\n".join(step_code_lines)

    return f'''
@app.post("/api/run-pipeline")
async def run_pipeline(request: dict = {{}}):
    """Run the full tool pipeline in workflow order."""
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    steps_completed = []
    pipeline_input = None

    # If request includes input data, write it to a temp file
    if request:
        pipeline_input = os.path.join(tmp_dir, "pipeline_input.json")
        with open(pipeline_input, "w") as f:
            json.dump(request, f)

    try:
{step_code}

        return JSONResponse(content={{
            "status": "success",
            "steps": steps_completed,
            "message": "Pipeline completed successfully",
        }})
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
'''


def generate_main_py(manifest: dict) -> str:
    """Generate the complete api/main.py file."""
    system_name = manifest.get("system", {}).get("system_name", "WAT System")
    tools = manifest.get("tools", [])
    pipeline_order = manifest.get("pipeline_order", [t["name"] for t in tools])

    # Collect model imports
    model_imports = []
    for tool in tools:
        class_name = "".join(word.capitalize() for word in tool["name"].split("_")) + "Request"
        model_imports.append(f"from models.{tool['name']} import {class_name}")

    model_import_block = "\n".join(model_imports)

    # Generate tool endpoints
    tool_endpoints = "\n".join(generate_tool_endpoint(tool) for tool in tools)

    # Generate pipeline endpoint
    pipeline_endpoint = generate_pipeline_endpoint(tools, pipeline_order)

    return f'''"""
{system_name} — API Bridge

Auto-generated FastAPI application that wraps each Python tool as an HTTP endpoint.
Serves the Next.js static export at / and the API at /api/*.

Generated by WAT Factory generate_api_bridge.py
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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
{model_import_block}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("{system_name} API bridge starting up")
    yield
    logger.info("{system_name} API bridge shutting down")


app = FastAPI(
    title="{system_name} API",
    description="API bridge for {system_name}",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
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
    logger.error("Unhandled error: %s\\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={{
            "status": "error",
            "message": str(exc),
            "detail": "An unexpected error occurred.",
        }},
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {{
        "status": "healthy",
        "timestamp": time.time(),
        "system": "{system_name}",
    }}

{tool_endpoints}
{pipeline_endpoint}

# Static file serving — Next.js export (must be last)
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "out"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
'''


def generate_requirements() -> str:
    """Generate api/requirements.txt."""
    return """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
"""


def generate_dockerfile(system_name: str) -> str:
    """Generate api/Dockerfile."""
    return f"""FROM python:3.11-slim

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \\
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \\
    apt-get install -y nodejs && \\
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
COPY api/requirements.txt ./api/
RUN pip install --no-cache-dir -r requirements.txt -r api/requirements.txt

# Copy system files
COPY . .

# Build frontend
RUN cd frontend && npm install && npm run build

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def main() -> dict[str, Any]:
    """Generate FastAPI bridge for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate FastAPI API bridge")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    parser.add_argument("--manifest", default=None, help="Path to system_interface.json")
    args = parser.parse_args()

    logger.info("Generating API bridge for: %s", args.system_dir)

    try:
        system_dir = Path(args.system_dir)
        if not system_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {system_dir}"}

        # Load manifest
        manifest_path = args.manifest or str(system_dir / "system_interface.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        tools = manifest.get("tools", [])
        if not tools:
            return {"status": "error", "data": None, "message": "No tools found in manifest"}

        # Create api/ directory
        api_dir = system_dir / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        # Create models/ directory
        models_dir = api_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Write __init__.py for models
        init_path = models_dir / "__init__.py"
        init_path.write_text("", encoding="utf-8")

        # Generate Pydantic models
        for tool in tools:
            model_code = generate_pydantic_model(tool)
            model_path = models_dir / f"{tool['name']}.py"
            model_path.write_text(model_code, encoding="utf-8")
            logger.info("Generated model: %s", model_path.name)

        # Generate main.py
        main_code = generate_main_py(manifest)
        main_path = api_dir / "main.py"
        main_path.write_text(main_code, encoding="utf-8")
        logger.info("Generated api/main.py")

        # Generate requirements.txt
        req_path = api_dir / "requirements.txt"
        req_path.write_text(generate_requirements(), encoding="utf-8")
        logger.info("Generated api/requirements.txt")

        # Generate Dockerfile
        system_name = manifest.get("system", {}).get("system_name", "wat-system")
        dockerfile_path = api_dir / "Dockerfile"
        dockerfile_path.write_text(generate_dockerfile(system_name), encoding="utf-8")
        logger.info("Generated api/Dockerfile")

        return {
            "status": "success",
            "data": {
                "models_generated": len(tools),
                "files": ["api/main.py", "api/requirements.txt", "api/Dockerfile"]
                         + [f"api/models/{t['name']}.py" for t in tools],
            },
            "message": f"API bridge generated with {len(tools)} tool endpoints",
        }

    except Exception as e:
        logger.error("API bridge generation failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
