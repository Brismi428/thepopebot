"""
Generate Workflow — Creates a workflow.md for a new WAT system.

Inputs:
    - system_name (str): Name of the system being built
    - design (str): JSON string containing the workflow design (steps, decisions, inputs, outputs)
    - template_path (str): Path to workflow_template.md
    - agent_teams (bool): Whether to include Agent Teams parallel sections
    - agent_teams_template (str): Path to agent_teams_template.md (optional)

Outputs:
    - workflow.md file written to the specified output path

Usage:
    python generate_workflow.py --system-name "my-system" --design design.json --output workflow.md
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


def load_template(template_name: str) -> str:
    """Load a template file from the templates directory."""
    template_path = TEMPLATE_DIR / template_name
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_design(design_input: str) -> dict[str, Any]:
    """Parse the design input — either a JSON file path or a JSON string."""
    if os.path.isfile(design_input):
        with open(design_input, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(design_input)


def generate_inputs_section(inputs: list[dict]) -> str:
    """Generate the Inputs section of the workflow."""
    lines = ["## Inputs\n"]
    for inp in inputs:
        name = inp.get("name", "unnamed")
        type_ = inp.get("type", "str")
        desc = inp.get("description", "No description")
        lines.append(f"- **{name}** ({type_}): {desc}")
    return "\n".join(lines)


def generate_outputs_section(outputs: list[dict]) -> str:
    """Generate the Outputs section of the workflow."""
    lines = ["## Outputs\n"]
    for out in outputs:
        name = out.get("name", "unnamed")
        type_ = out.get("type", "str")
        desc = out.get("description", "No description")
        lines.append(f"- **{name}** ({type_}): {desc}")
    return "\n".join(lines)


def generate_step(step_num: int, step: dict) -> str:
    """Generate a single workflow step."""
    name = step.get("name", f"Step {step_num}")
    description = step.get("description", "")
    substeps = step.get("substeps", [])
    tool = step.get("tool", None)
    decision = step.get("decision", None)
    failure_mode = step.get("failure_mode", "Log the error and continue to the next step.")

    lines = [f"## Step {step_num}: {name}\n"]
    if description:
        lines.append(f"{description}\n")

    for i, substep in enumerate(substeps, 1):
        lines.append(f"{i}. {substep}")

    if tool:
        lines.append(f"\n**Tool**: `tools/{tool}` — {step.get('tool_description', 'Executes this step')}")

    if decision:
        condition = decision.get("condition", "condition is met")
        yes_action = decision.get("yes", "Continue")
        no_action = decision.get("no", "Skip")
        lines.append(f"\n**Decision point**: **If {condition}**:")
        lines.append(f"- **Yes**: {yes_action}")
        lines.append(f"- **No**: {no_action}")

    lines.append(f"\n**Failure mode**: {failure_mode}")
    return "\n".join(lines)


def generate_agent_teams_section(parallel_tasks: list[dict]) -> str:
    """Generate the Agent Teams parallel execution section."""
    try:
        template = load_template("agent_teams_template.md")
    except FileNotFoundError:
        template = ""

    lines = ["\n---\n", "## Parallel Execution — Agent Teams\n"]
    lines.append("**Environment requirement**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`\n")
    lines.append("### Parallel Tasks\n")
    lines.append("| Task ID | Description | Expected Output |")
    lines.append("|---------|-------------|-----------------|")
    for task in parallel_tasks:
        tid = task.get("id", "task")
        desc = task.get("description", "")
        output = task.get("expected_output", "")
        lines.append(f"| {tid} | {desc} | {output} |")

    lines.append("\n### Sequential Fallback\n")
    lines.append("If Agent Teams is unavailable, execute the above tasks sequentially in order.")

    return "\n".join(lines)


def main() -> dict[str, Any]:
    """Generate a workflow.md file from a design specification."""
    parser = argparse.ArgumentParser(description="Generate workflow.md for a WAT system")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--design", required=True, help="Design JSON (file path or string)")
    parser.add_argument("--output", default="workflow.md", help="Output file path")
    parser.add_argument("--agent-teams", action="store_true", help="Include Agent Teams sections")
    args = parser.parse_args()

    logger.info("Generating workflow for system: %s", args.system_name)

    try:
        design = parse_design(args.design)

        # Build the workflow document
        sections = []

        # Header
        title = design.get("title", args.system_name)
        description = design.get("description", "A WAT system.")
        sections.append(f"# {title} — Workflow\n\n{description}")

        # Inputs
        inputs = design.get("inputs", [])
        if inputs:
            sections.append(generate_inputs_section(inputs))

        # Outputs
        outputs = design.get("outputs", [])
        if outputs:
            sections.append(generate_outputs_section(outputs))

        sections.append("---")

        # Steps
        steps = design.get("steps", [])
        for i, step in enumerate(steps, 1):
            sections.append(generate_step(i, step))
            sections.append("---")

        # Agent Teams
        if args.agent_teams:
            parallel_tasks = design.get("parallel_tasks", [])
            if parallel_tasks:
                sections.append(generate_agent_teams_section(parallel_tasks))

        # Notes
        notes = design.get("notes", [])
        if notes:
            sections.append("## Notes\n")
            for note in notes:
                sections.append(f"- {note}")

        # Write output
        workflow_content = "\n\n".join(sections) + "\n"
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(workflow_content)

        logger.info("Workflow written to %s", args.output)
        return {"status": "success", "output": str(output_path), "steps": len(steps)}

    except json.JSONDecodeError as e:
        logger.error("Failed to parse design JSON: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except Exception as e:
        logger.error("Failed to generate workflow: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
