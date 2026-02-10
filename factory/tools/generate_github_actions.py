"""
Generate GitHub Actions — Creates .github/workflows/ YAML files for a WAT system.

Reads the system design and generates GitHub Actions workflow files for:
- Main system execution (dispatch, cron, webhook triggers)
- Agent HQ integration (issue/PR-driven execution)

Inputs:
    - system_name (str): Name of the system
    - design (str): JSON with trigger config, secrets, and execution details
    - agent_teams (bool): Whether to enable Agent Teams env var

Outputs:
    - .github/workflows/*.yml files in the output directory

Usage:
    python generate_github_actions.py --system-name "my-system" --design actions.json --output-dir .github/workflows/
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

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def load_template(name: str) -> str:
    """Load a YAML template from the templates directory."""
    path = TEMPLATE_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_main_workflow(system_name: str, config: dict) -> str:
    """Generate the main GitHub Actions workflow YAML."""
    triggers = config.get("triggers", ["workflow_dispatch"])
    secrets = config.get("secrets", [])
    cron = config.get("cron", None)
    timeout = config.get("timeout_minutes", 15)
    agent_teams = config.get("agent_teams", False)
    input_description = config.get("input_description", "Task input (JSON or text)")

    # Build trigger section
    trigger_lines = ["on:"]
    if "workflow_dispatch" in triggers:
        trigger_lines.extend([
            "  workflow_dispatch:",
            "    inputs:",
            "      task_input:",
            f'        description: "{input_description}"',
            "        required: true",
            "        type: string",
        ])
    if "schedule" in triggers and cron:
        trigger_lines.extend([
            "  schedule:",
            f'    - cron: "{cron}"',
        ])
    if "repository_dispatch" in triggers:
        trigger_lines.extend([
            "  repository_dispatch:",
            f'    types: [{system_name}-run]',
        ])

    # Build secrets env section
    secret_env_lines = [
        "          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}",
        "          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
    ]
    for secret in secrets:
        name = secret.get("name", "")
        if name and name not in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN"):
            secret_env_lines.append(f"          {name}: ${{{{ secrets.{name} }}}}")

    # Build agent teams env
    agent_teams_env = ""
    if agent_teams:
        agent_teams_env = "          CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: '1'"

    yaml = f"""name: "{system_name} — WAT System"

{chr(10).join(trigger_lines)}

permissions:
  contents: write
  issues: write

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: {timeout}

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Determine input
        id: input
        run: |
          if [ "${{{{ github.event_name }}}}" = "workflow_dispatch" ]; then
            echo "task_input=${{{{ github.event.inputs.task_input }}}}" >> $GITHUB_OUTPUT
          elif [ "${{{{ github.event_name }}}}" = "repository_dispatch" ]; then
            echo "task_input=${{{{ github.event.client_payload.task_input }}}}" >> $GITHUB_OUTPUT
          else
            echo "task_input={{}}" >> $GITHUB_OUTPUT
          fi

      - name: Execute via Claude Code
        env:
{chr(10).join(secret_env_lines)}
{agent_teams_env}
          TASK_INPUT: ${{{{ steps.input.outputs.task_input }}}}
        run: |
          npx @anthropic-ai/claude-code --print \\
            "Read CLAUDE.md for context, then execute workflow.md with input: $TASK_INPUT"

      - name: Commit results
        run: |
          git config user.name "WAT System: {system_name}"
          git config user.email "wat-system@users.noreply.github.com"
          git add output/ || true
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "run: {system_name} results $(date +%Y-%m-%d_%H%M)"
            git push
          fi

      - name: Notify on failure
        if: failure()
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          gh issue create \\
            --title "Run Failed: {system_name} ($(date +%Y-%m-%d))" \\
            --body "System \\`{system_name}\\` failed. Check [logs](${{{{ github.server_url }}}}/${{{{ github.repository }}}}/actions/runs/${{{{ github.run_id }}}})." \\
            --label "bug,system-failure"
"""
    return yaml


def generate_agent_hq_workflow(system_name: str) -> str:
    """Generate the Agent HQ workflow YAML for issue/PR-driven execution."""
    try:
        template = load_template("agent_hq_template.yml")
        return template.replace("{system_name}", system_name)
    except FileNotFoundError:
        logger.warning("agent_hq_template.yml not found, generating from scratch")
        return f"""name: "{system_name} — Agent HQ"

on:
  issues:
    types: [opened, assigned]
  issue_comment:
    types: [created]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  agent-hq:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    if: >
      (github.event_name == 'issues' && contains(github.event.issue.assignees.*.login, 'claude')) ||
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude'))
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt || true
      - name: Execute
        env:
          ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          npx @anthropic-ai/claude-code --print "Read CLAUDE.md and execute workflow.md"
"""


def main() -> dict[str, Any]:
    """Generate GitHub Actions workflow files for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate GitHub Actions for a WAT system")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--design", required=True, help="Actions design JSON (file path or string)")
    parser.add_argument("--output-dir", default=".github/workflows", help="Output directory")
    parser.add_argument("--agent-teams", action="store_true", help="Enable Agent Teams env var")
    args = parser.parse_args()

    logger.info("Generating GitHub Actions for: %s", args.system_name)

    try:
        if os.path.isfile(args.design):
            with open(args.design, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = json.loads(args.design)

        if args.agent_teams:
            config["agent_teams"] = True

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate main workflow
        main_yaml = generate_main_workflow(args.system_name, config)
        main_path = output_dir / f"{args.system_name}.yml"
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_yaml)
        logger.info("Main workflow written to %s", main_path)

        # Generate Agent HQ workflow
        hq_yaml = generate_agent_hq_workflow(args.system_name)
        hq_path = output_dir / "agent_hq.yml"
        with open(hq_path, "w", encoding="utf-8") as f:
            f.write(hq_yaml)
        logger.info("Agent HQ workflow written to %s", hq_path)

        return {
            "status": "success",
            "files": [str(main_path), str(hq_path)],
        }

    except Exception as e:
        logger.error("Failed to generate GitHub Actions: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
