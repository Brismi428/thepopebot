"""
Generate Subagents — Creates .claude/agents/ markdown files for a WAT system.

Produces custom Claude Code subagent definitions following the official format:
YAML frontmatter (name, description, tools, model, permissionMode) plus a
detailed system prompt in the markdown body.

Subagents are the DEFAULT delegation mechanism in WAT systems. Every system
gets specialist subagents for its core capabilities. Agent Teams is only used
when 3+ truly independent parallel tasks are identified.

Inputs:
    - system_name (str): Name of the system
    - design (str): JSON file path or JSON string with subagent definitions
    - output_dir (str): Output directory (typically systems/{system_name}/.claude/agents/)

Outputs:
    - One .md file per subagent in the output directory

Usage:
    python generate_subagents.py --system-name "lead-gen-machine" --design design.json --output-dir systems/lead-gen-machine/.claude/agents/
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Valid values for subagent configuration
VALID_MODELS = {"sonnet", "opus", "haiku", "inherit"}
VALID_PERMISSION_MODES = {
    "default", "acceptEdits", "delegate", "dontAsk", "bypassPermissions", "plan",
}
VALID_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task",
    "WebFetch", "WebSearch", "NotebookEdit",
}


def validate_subagent_config(config: dict) -> list[str]:
    """
    Validate a subagent configuration dict.

    Returns a list of validation issues (empty if valid).
    """
    issues = []

    if not config.get("name"):
        issues.append("Missing required field: name")
    elif not all(c.isalnum() or c == "-" for c in config["name"]):
        issues.append(f"Invalid name '{config['name']}': use lowercase letters, numbers, and hyphens only")

    if not config.get("description"):
        issues.append("Missing required field: description")

    if not config.get("system_prompt"):
        issues.append("Missing required field: system_prompt")

    model = config.get("model", "inherit")
    if model not in VALID_MODELS:
        issues.append(f"Invalid model '{model}': must be one of {VALID_MODELS}")

    perm = config.get("permissionMode", "default")
    if perm not in VALID_PERMISSION_MODES:
        issues.append(f"Invalid permissionMode '{perm}': must be one of {VALID_PERMISSION_MODES}")

    tools = config.get("tools", [])
    if tools:
        for tool in tools:
            # Handle Task(agent1, agent2) syntax
            base_tool = tool.split("(")[0]
            if base_tool not in VALID_TOOLS:
                issues.append(f"Unknown tool '{tool}': valid tools are {VALID_TOOLS}")

    return issues


def generate_subagent_markdown(config: dict) -> str:
    """
    Generate a subagent markdown file from a configuration dict.

    The file follows the official Claude Code subagent format:
    - YAML frontmatter with name, description, tools, model, permissionMode
    - Markdown body as the system prompt
    """
    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"name: {config['name']}",
        f"description: {config['description']}",
    ]

    # Tools (comma-separated string)
    tools = config.get("tools", [])
    if tools:
        frontmatter_lines.append(f"tools: {', '.join(tools)}")

    # Model
    model = config.get("model", "sonnet")
    frontmatter_lines.append(f"model: {model}")

    # Permission mode
    perm = config.get("permissionMode", "default")
    if perm != "default":
        frontmatter_lines.append(f"permissionMode: {perm}")

    # Max turns
    max_turns = config.get("maxTurns")
    if max_turns:
        frontmatter_lines.append(f"maxTurns: {max_turns}")

    frontmatter_lines.append("---")

    # Build full file
    frontmatter = "\n".join(frontmatter_lines)
    system_prompt = config.get("system_prompt", "")

    return f"{frontmatter}\n\n{system_prompt}\n"


def identify_core_subagents(steps: list[dict], system_name: str) -> list[dict]:
    """
    Identify what specialist subagents a system needs based on its workflow steps.

    Every system gets subagents for its core capabilities. Each step with a
    tool or distinct domain responsibility becomes a subagent candidate.
    """
    subagents = []

    for step in steps:
        tool = step.get("tool")
        name = step.get("name", "")
        description = step.get("description", "")

        if not name:
            continue

        # Convert step name to subagent name format
        agent_name = name.lower().replace(" ", "-").replace("_", "-")
        # Ensure it ends with -specialist if it doesn't already have a role suffix
        if not any(agent_name.endswith(suffix) for suffix in ["-specialist", "-agent", "-worker"]):
            agent_name = f"{agent_name}-specialist"

        # Determine appropriate tools based on the step's nature
        step_tools = _infer_tools_for_step(step)

        subagent = {
            "name": agent_name,
            "description": f"Specialist for {name.lower()}. Delegate to this subagent when the workflow reaches the {name} phase.",
            "tools": step_tools,
            "model": "sonnet",
            "permissionMode": "default",
            "system_prompt": _generate_system_prompt(step, system_name),
        }

        if tool:
            subagent["primary_tool"] = tool

        subagents.append(subagent)

    return subagents


def _infer_tools_for_step(step: dict) -> list[str]:
    """Infer which Claude Code tools a subagent needs based on the step description."""
    tools = ["Read"]  # Every subagent can read files
    description = (step.get("description", "") + " " + step.get("name", "")).lower()

    if any(kw in description for kw in ["search", "web", "api", "fetch", "http", "scrape"]):
        tools.append("Bash")
        tools.append("WebFetch")
        tools.append("WebSearch")

    if any(kw in description for kw in ["write", "generate", "create", "output", "csv", "report"]):
        tools.append("Write")

    if any(kw in description for kw in ["edit", "modify", "update", "transform"]):
        tools.append("Edit")

    if any(kw in description for kw in ["run", "execute", "install", "pip", "python", "script"]):
        tools.append("Bash")

    if any(kw in description for kw in ["find", "search file", "locate", "pattern"]):
        tools.append("Glob")
        tools.append("Grep")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for t in tools:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


def _generate_system_prompt(step: dict, system_name: str) -> str:
    """Generate a detailed system prompt for a subagent based on its step definition."""
    name = step.get("name", "task")
    description = step.get("description", "")
    tool = step.get("tool", "")
    inputs = step.get("requires", [])
    outputs = step.get("produces", [])
    failure_mode = step.get("failure_mode", "")

    lines = [
        f"You are a specialist subagent for the {system_name} system, responsible for: {name}.",
        "",
        f"{description}" if description else f"Execute the {name} phase of the workflow.",
        "",
    ]

    if tool:
        lines.extend([
            "## Primary Tool",
            "",
            f"Use `{tool}` to execute this task. Run it via Bash:",
            f"```",
            f"python {tool} [arguments]",
            f"```",
            "",
        ])

    if inputs:
        lines.extend([
            "## Inputs",
            "",
        ])
        for inp in inputs:
            lines.append(f"- {inp}")
        lines.append("")

    if outputs:
        lines.extend([
            "## Expected Outputs",
            "",
        ])
        for out in outputs:
            lines.append(f"- {out}")
        lines.append("")

    lines.extend([
        "## Instructions",
        "",
        "1. Read the input data from the previous step",
        "2. Execute your specialist task thoroughly",
        "3. Validate your output before returning",
        "4. Write results to the designated output location",
        "5. Report any errors clearly with context",
        "",
    ])

    if failure_mode:
        lines.extend([
            "## Failure Handling",
            "",
            failure_mode,
            "",
        ])

    lines.extend([
        "## Quality Standards",
        "",
        "- Validate all inputs before processing",
        "- Handle errors gracefully with meaningful messages",
        "- Log progress for observability",
        "- Return structured output (JSON preferred)",
    ])

    return "\n".join(lines)


def main() -> dict[str, Any]:
    """Generate subagent markdown files for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate subagent definitions")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--design", required=True, help="Design JSON file or string with subagent configs")
    parser.add_argument("--output-dir", required=True, help="Output directory for .claude/agents/")
    args = parser.parse_args()

    logger.info("Generating subagents for system: %s", args.system_name)

    try:
        # Load design
        if os.path.isfile(args.design):
            with open(args.design, "r", encoding="utf-8") as f:
                design = json.load(f)
        else:
            design = json.loads(args.design)

        # Get subagent configs — either explicit or auto-identified from steps
        subagent_configs = design.get("subagents", [])
        if not subagent_configs:
            steps = design.get("steps", [])
            subagent_configs = identify_core_subagents(steps, args.system_name)
            logger.info("Auto-identified %d subagents from workflow steps", len(subagent_configs))

        if not subagent_configs:
            logger.warning("No subagents to generate")
            return {
                "status": "success",
                "subagents_generated": 0,
                "message": "No subagent definitions found in design",
            }

        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)

        generated = []
        validation_issues = []

        for config in subagent_configs:
            # Validate
            issues = validate_subagent_config(config)
            if issues:
                logger.warning("Validation issues for '%s': %s", config.get("name", "?"), issues)
                validation_issues.extend(issues)
                continue

            # Generate markdown
            markdown = generate_subagent_markdown(config)

            # Write file
            filename = f"{config['name']}.md"
            filepath = os.path.join(args.output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)

            logger.info("Generated subagent: %s -> %s", config["name"], filepath)
            generated.append({
                "name": config["name"],
                "file": filepath,
                "tools": config.get("tools", []),
                "model": config.get("model", "sonnet"),
            })

        result = {
            "status": "success",
            "subagents_generated": len(generated),
            "subagents": generated,
            "validation_issues": validation_issues,
            "output_dir": args.output_dir,
            "message": f"Generated {len(generated)} subagent(s) in {args.output_dir}",
        }

        # Write manifest for other tools to reference
        manifest_path = os.path.join(args.output_dir, "_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Subagent manifest written to %s", manifest_path)
        return result

    except Exception as e:
        logger.error("Failed to generate subagents: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
