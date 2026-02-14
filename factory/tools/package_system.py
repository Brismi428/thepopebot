"""
Package System — Bundles a completed WAT system into a deployable directory.

Collects all generated artifacts (workflow.md, tools, GitHub Actions, CLAUDE.md)
and packages them into a self-contained system directory ready for deployment.

Inputs:
    - system_name (str): Name of the system
    - source_dir (str): Directory containing generated artifacts
    - output_dir (str): Target directory (typically systems/{system_name}/)
    - system_description (str): Brief description for the README

Outputs:
    - Complete system directory with all required files
    - README.md with setup instructions for all three execution paths

Usage:
    python package_system.py --system-name "my-system" --source-dir build/ --output-dir systems/my-system/
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    "CLAUDE.md",
    "workflow.md",
    "requirements.txt",
]

REQUIRED_DIRS = [
    "tools",
    ".claude/agents",
    ".github/workflows",
]


def has_frontend(source: Path) -> bool:
    """Check if the system has a generated front-end."""
    return (source / "frontend").is_dir() and (source / "api").is_dir()


def generate_readme(system_name: str, description: str, secrets: list[str], with_frontend: bool = False) -> str:
    """Generate a README.md for the packaged system."""
    secrets_table = "\n".join(
        f"| `{s}` | Required |" for s in secrets
    ) if secrets else "| (none beyond ANTHROPIC_API_KEY) | |"

    frontend_section = ""
    frontend_structure = ""
    if with_frontend:
        frontend_section = f"""
### Option D: Interactive Front-End (Web UI)

```bash
# Install Python dependencies
pip install -r requirements.txt -r api/requirements.txt

# Start the API server
uvicorn api.main:app --reload --port 8000

# In another terminal, start the frontend dev server
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000 in your browser.

#### Docker Deployment

```bash
docker compose -f docker-compose.frontend.yml up --build
```

The app will be available at http://localhost:8000 (API + frontend served together).

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/run-pipeline` | Run the full tool pipeline |
| POST | `/api/{{tool-name}}` | Run individual tools |
"""
        frontend_structure = """├── api/               # FastAPI bridge (wraps tools as HTTP endpoints)
│   ├── main.py
│   ├── models/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # Next.js web interface
│   ├── src/
│   ├── package.json
│   └── next.config.js
├── docker-compose.frontend.yml  # Docker deployment
├── system_interface.json        # Tool schemas (source of truth for frontend)
├── frontend_design.json         # UI design configuration
"""

    return f"""# {system_name}

{description}

## Quick Start

This WAT system can be run three ways:

### Option A: Claude Code CLI (Local)

```bash
# Clone the repo
git clone <repo-url>
cd {system_name}

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here
# Set any additional required secrets as env vars

# Install dependencies
pip install -r requirements.txt

# Run via Claude Code
claude "Read CLAUDE.md for context, then execute workflow.md"
```

### Option B: GitHub Actions (Automated)

1. Push this repo to GitHub
2. Go to **Settings > Secrets and variables > Actions**
3. Add the required secrets (see table below)
4. Go to **Actions** tab and trigger the workflow manually, or wait for the cron schedule

To trigger via API (e.g., from n8n):
```bash
curl -X POST \\
  -H "Authorization: Bearer $GITHUB_PAT" \\
  -H "Accept: application/vnd.github.v3+json" \\
  https://api.github.com/repos/OWNER/REPO/dispatches \\
  -d '{{"event_type": "{system_name}-run", "client_payload": {{"task_input": "your input here"}}}}'
```

### Option C: GitHub Agent HQ (Issue-Driven)

1. Create an issue in the repo with your task in the body
2. Assign the issue to `@claude`
3. The agent will process the request and open a draft PR with results
4. Leave comments mentioning `@claude` for iterations
{frontend_section}
## Required Secrets

| Secret | Status |
|--------|--------|
| `ANTHROPIC_API_KEY` | Required |
{secrets_table}

## System Structure

```
{system_name}/
├── CLAUDE.md          # Operating instructions for Claude Code / Agent HQ
├── workflow.md        # Step-by-step workflow
├── tools/             # Python tool implementations
├── .claude/agents/    # Specialist subagent definitions
├── .github/workflows/ # GitHub Actions for automated execution
├── requirements.txt   # Python dependencies
{frontend_structure}├── output/            # Execution results (auto-generated)
└── README.md          # This file
```

## Workflow Overview

See `workflow.md` for the complete step-by-step process.
See `CLAUDE.md` for system configuration and MCP details.

---
*Built by [WAT Systems Factory](https://github.com/your-org/wat-systems-factory)*
"""


def validate_package(output_dir: Path) -> list[str]:
    """Validate that all required files and directories exist."""
    issues = []

    for req_file in REQUIRED_FILES:
        if not (output_dir / req_file).is_file():
            issues.append(f"Missing required file: {req_file}")

    for req_dir in REQUIRED_DIRS:
        if not (output_dir / req_dir).is_dir():
            issues.append(f"Missing required directory: {req_dir}")

    # Check for hardcoded secrets (basic scan)
    for py_file in output_dir.rglob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for common secret patterns
        for pattern in ["sk-", "api_key = \"", "password = \"", "token = \""]:
            if pattern in content.lower():
                issues.append(f"Possible hardcoded secret in {py_file.relative_to(output_dir)}")

    return issues


def main() -> dict[str, Any]:
    """Package a WAT system into a deployable directory."""
    parser = argparse.ArgumentParser(description="Package a WAT system")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--source-dir", required=True, help="Directory with generated artifacts")
    parser.add_argument("--output-dir", required=True, help="Target output directory")
    parser.add_argument("--description", default="A WAT system.", help="System description for README")
    parser.add_argument("--secrets", default="", help="Comma-separated list of required secret names")
    args = parser.parse_args()

    logger.info("Packaging system: %s", args.system_name)

    try:
        source = Path(args.source_dir)
        output = Path(args.output_dir)

        if not source.is_dir():
            return {"status": "error", "data": None, "message": f"Source dir not found: {source}"}

        # Create output directory
        output.mkdir(parents=True, exist_ok=True)

        # Copy all files from source to output
        for item in source.rglob("*"):
            if item.is_file():
                relative = item.relative_to(source)
                dest = output / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                logger.info("Copied: %s", relative)

        # Create output directory for results
        (output / "output").mkdir(exist_ok=True)
        (output / "output" / ".gitkeep").touch()

        # Generate README
        secrets = [s.strip() for s in args.secrets.split(",") if s.strip()]
        readme = generate_readme(args.system_name, args.description, secrets, with_frontend=has_frontend(source))
        with open(output / "README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        logger.info("README.md generated")

        # Validate
        issues = validate_package(output)
        if issues:
            logger.warning("Package validation issues:")
            for issue in issues:
                logger.warning("  - %s", issue)

        file_count = sum(1 for _ in output.rglob("*") if _.is_file())
        logger.info("Package complete: %d files in %s", file_count, output)

        return {
            "status": "success",
            "output_dir": str(output),
            "file_count": file_count,
            "validation_issues": issues,
        }

    except Exception as e:
        logger.error("Packaging failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
