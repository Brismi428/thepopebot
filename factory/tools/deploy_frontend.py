"""
Deploy Frontend — Generates deployment configs for a WAT system with front-end.

Produces:
- docker-compose.frontend.yml (single container: FastAPI + Next.js static export)
- Caddy route snippet for the system
- .env.example for required secrets

Supports both standalone deployment and integration with existing services stack.

Inputs:
    - system_dir (str): Path to the system directory
    - domain (str): Domain for the deployment (default: localhost)
    - port (int): Port for the service (default: 8000)

Outputs:
    - docker-compose.frontend.yml
    - caddy_snippet.txt
    - .env.example (updated if exists)

Usage:
    python deploy_frontend.py --system-dir systems/invoice-generator/ --domain invoice.example.com
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


def extract_env_vars(manifest: dict) -> list[dict[str, Any]]:
    """Extract all environment variables from the manifest."""
    env_vars = []
    seen = set()

    for tool in manifest.get("tools", []):
        for ev in tool.get("env_vars", []):
            name = ev["name"]
            if name not in seen:
                seen.add(name)
                env_vars.append(ev)

    return env_vars


def generate_docker_compose(system_name: str, port: int, env_vars: list[dict]) -> str:
    """Generate docker-compose.frontend.yml."""
    env_lines = []
    for ev in env_vars:
        env_lines.append(f"      - {ev['name']}=${{{{ {ev['name']} }}}}")

    env_block = "\n".join(env_lines) if env_lines else "      # No additional environment variables"

    return f"""# docker-compose.frontend.yml
# Single-container deployment for {system_name}
# FastAPI serves API at /api/* and Next.js static export at /*

services:
  {system_name}:
    build:
      context: .
      dockerfile: api/Dockerfile
    container_name: {system_name}
    ports:
      - "{port}:8000"
    environment:
      - CORS_ORIGINS=http://localhost:{port},https://${{DOMAIN:-localhost}}
{env_block}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
"""


def generate_caddy_snippet(system_name: str, port: int, domain: str) -> str:
    """Generate Caddy route snippet for reverse proxying to the system."""
    return f"""# Caddy route snippet for {system_name}
# Option A: Subdomain routing
{domain} {{
    reverse_proxy localhost:{port}
}}

# Option B: Sub-path routing (add to existing Caddyfile)
# handle_path /{system_name}/* {{
#     reverse_proxy localhost:{port}
# }}
"""


def generate_env_example(env_vars: list[dict], system_name: str) -> str:
    """Generate .env.example with all required variables."""
    lines = [
        f"# {system_name} — Environment Variables",
        f"# Copy to .env and fill in values",
        "",
        "# Deployment",
        f"DOMAIN=localhost",
        f"PORT=8000",
        "CORS_ORIGINS=http://localhost:3000,http://localhost:8000",
        "",
    ]

    if env_vars:
        lines.append("# System secrets")
        for ev in env_vars:
            required = "REQUIRED" if ev.get("required") else "optional"
            default = ev.get("default", "")
            lines.append(f"# {required}")
            lines.append(f"{ev['name']}={default or ''}")

    return "\n".join(lines) + "\n"


def main() -> dict[str, Any]:
    """Generate deployment configs for a WAT system with front-end."""
    parser = argparse.ArgumentParser(description="Generate deployment configs")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    parser.add_argument("--domain", default="localhost", help="Domain for the deployment")
    parser.add_argument("--port", type=int, default=8000, help="Port for the service")
    args = parser.parse_args()

    logger.info("Generating deployment configs for: %s", args.system_dir)

    try:
        system_dir = Path(args.system_dir)
        if not system_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {system_dir}"}

        # Load manifest
        manifest_path = system_dir / "system_interface.json"
        manifest = {}
        if manifest_path.is_file():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        system_name = manifest.get("system", {}).get("system_name", system_dir.name)
        # Slugify system name for Docker
        system_slug = system_name.lower().replace(" ", "-").replace("_", "-")

        env_vars = extract_env_vars(manifest)
        files_written = []

        # Generate docker-compose.frontend.yml
        compose = generate_docker_compose(system_slug, args.port, env_vars)
        compose_path = system_dir / "docker-compose.frontend.yml"
        compose_path.write_text(compose, encoding="utf-8")
        files_written.append("docker-compose.frontend.yml")
        logger.info("Generated docker-compose.frontend.yml")

        # Generate Caddy snippet
        caddy = generate_caddy_snippet(system_slug, args.port, args.domain)
        caddy_path = system_dir / "caddy_snippet.txt"
        caddy_path.write_text(caddy, encoding="utf-8")
        files_written.append("caddy_snippet.txt")
        logger.info("Generated caddy_snippet.txt")

        # Generate or update .env.example
        env_example = generate_env_example(env_vars, system_name)
        env_path = system_dir / ".env.example"
        if env_path.is_file():
            # Append frontend section if it exists
            existing = env_path.read_text(encoding="utf-8")
            if "CORS_ORIGINS" not in existing:
                existing += "\n# Frontend deployment\nCORS_ORIGINS=http://localhost:3000,http://localhost:8000\n"
                env_path.write_text(existing, encoding="utf-8")
                logger.info("Updated existing .env.example with frontend vars")
        else:
            env_path.write_text(env_example, encoding="utf-8")
            logger.info("Generated .env.example")
        files_written.append(".env.example")

        return {
            "status": "success",
            "data": {
                "files": files_written,
                "system_name": system_slug,
                "domain": args.domain,
                "port": args.port,
            },
            "message": f"Deployment configs generated: {', '.join(files_written)}",
        }

    except Exception as e:
        logger.error("Deployment config generation failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
