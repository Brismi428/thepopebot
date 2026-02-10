"""
Generate Agent Teams — Creates native Claude Code Agent Teams configurations.

Analyzes a workflow design to identify independent subtasks, then generates
Agent Teams configurations using the native team lead/teammate pattern with
shared task lists and inter-agent coordination.

This generates the NATIVE Agent Teams structure:
- Team Lead: coordinates the workflow, creates shared task list, spawns teammates
- Teammates: execute scoped independent tasks concurrently
- Shared Task List: TaskCreate/TaskUpdate/TaskList for coordination
- Sequential Fallback: identical results without Agent Teams enabled

Inputs:
    - system_name (str): Name of the system
    - design (str): JSON file path or JSON string with workflow steps and dependencies
    - output (str): Output file path for the agent teams configuration

Outputs:
    - Agent teams configuration JSON with team structure, task definitions, and fallback plan

Usage:
    python generate_agent_teams.py --system-name "my-system" --design design.json --output agent_teams.json
"""

import argparse
import json
import logging
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

AGENT_TEAMS_THRESHOLD = 3  # Minimum independent tasks to recommend Agent Teams


def build_dependency_graph(steps: list[dict]) -> dict[str, set[str]]:
    """
    Build a dependency graph from workflow steps.

    Returns a dict mapping step name to set of step names it depends on.
    """
    graph: dict[str, set[str]] = {}
    output_to_step: dict[str, str] = {}

    # Map outputs to the steps that produce them
    for step in steps:
        name = step.get("name", "")
        for output in step.get("produces", []):
            output_to_step[output] = name

    # Build dependency edges
    for step in steps:
        name = step.get("name", "")
        deps: set[str] = set()
        for req in step.get("requires", []):
            if req in output_to_step:
                deps.add(output_to_step[req])
        graph[name] = deps

    return graph


def find_independent_tasks(steps: list[dict]) -> list[dict]:
    """
    Identify tasks that have no dependencies on each other and can run concurrently.

    Two tasks are independent if neither depends on the other's output.
    """
    graph = build_dependency_graph(steps)
    step_map = {s.get("name", ""): s for s in steps}

    # Find groups of mutually independent tasks
    independent = []
    for step in steps:
        name = step.get("name", "")
        deps = graph.get(name, set())
        # A task is a candidate for parallelization if its dependencies
        # are all from steps OUTSIDE the current candidate set
        is_independent = True
        for other in independent:
            other_name = other.get("name", "")
            other_deps = graph.get(other_name, set())
            # If either depends on the other, they're not independent
            if name in other_deps or other_name in deps:
                is_independent = False
                break
        if is_independent:
            independent.append(step)

    return independent


def evaluate_agent_teams(steps: list[dict]) -> dict[str, Any]:
    """
    Apply the 3+ Independent Tasks Rule to decide whether Agent Teams is recommended.

    Returns evaluation with recommendation, reasoning, and identified parallel tasks.
    """
    independent = find_independent_tasks(steps)
    count = len(independent)
    recommended = count >= AGENT_TEAMS_THRESHOLD

    evaluation = {
        "recommended": recommended,
        "independent_task_count": count,
        "threshold": AGENT_TEAMS_THRESHOLD,
        "independent_tasks": [t.get("name", "") for t in independent],
        "reasoning": "",
    }

    if recommended:
        evaluation["reasoning"] = (
            f"Found {count} independent tasks (threshold: {AGENT_TEAMS_THRESHOLD}). "
            f"Agent Teams recommended for parallel execution."
        )
    elif count > 0:
        evaluation["reasoning"] = (
            f"Found {count} independent task(s), below threshold of {AGENT_TEAMS_THRESHOLD}. "
            f"Sequential execution preferred — parallelization overhead not justified."
        )
    else:
        evaluation["reasoning"] = (
            "All tasks have dependencies on each other. "
            "Sequential execution is the only option."
        )

    return evaluation


def generate_team_lead_config(system_name: str, teammates: list[dict]) -> dict:
    """Generate the team lead configuration for the native Agent Teams pattern."""
    task_names = [t.get("name", "task") for t in teammates]
    return {
        "role": "team_lead",
        "system_name": system_name,
        "responsibilities": [
            "Create shared task list with TaskCreate for each parallel task",
            "Spawn teammate agents to work on independent tasks concurrently",
            "Monitor progress via TaskList and TaskGet",
            "Collect results from all teammates after completion",
            "Merge results and perform quality control",
            "Handle failures — retry or fall back to sequential for failed tasks",
        ],
        "task_list_setup": [
            {
                "action": "TaskCreate",
                "subject": step.get("name", "task"),
                "description": step.get("description", ""),
                "activeForm": f"Working on {step.get('name', 'task')}",
            }
            for step in teammates
        ],
        "coordination_flow": [
            f"1. Create {len(teammates)} tasks via TaskCreate",
            f"2. Spawn {len(teammates)} teammate agents, each assigned one task",
            "3. Each teammate updates task status: pending → in_progress → completed",
            "4. Team lead monitors via TaskList until all tasks show completed",
            "5. Team lead reads results from each teammate's output",
            "6. Team lead merges results and validates cross-references",
            "7. If any teammate failed, team lead retries that task sequentially",
        ],
        "display_mode": "default",
        "display_mode_options": {
            "default": "Shows teammate status in a compact summary line",
            "verbose": "Shows full output from each teammate as they work",
        },
    }


def generate_teammate_config(step: dict, system_name: str, index: int) -> dict:
    """Generate a teammate configuration from a workflow step."""
    return {
        "role": "teammate",
        "teammate_id": f"{system_name}_teammate_{index + 1}",
        "task_name": step.get("name", f"task_{index + 1}"),
        "description": step.get("description", step.get("name", "Teammate task")),
        "scoped_instructions": (
            f"You are a teammate agent working on the '{system_name}' system. "
            f"Your task: {step.get('description', step.get('name', ''))}. "
            f"Work independently. Update your task status via TaskUpdate when done. "
            f"Write output to the designated location. Do not coordinate with other teammates."
        ),
        "inputs": step.get("requires", []),
        "expected_outputs": step.get("produces", []),
        "output_format": step.get("output_format", "Files written to the system output directory"),
        "tool": step.get("tool", None),
        "timeout_seconds": step.get("timeout", 300),
        "on_failure": "Report failure via TaskUpdate. Team lead will retry or fall back to sequential.",
    }


def generate_sequential_fallback(steps: list[dict]) -> dict:
    """Generate the sequential fallback plan for when Agent Teams is disabled."""
    return {
        "description": (
            "When CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is not set or set to 0, "
            "execute all tasks sequentially in the order listed. "
            "Results are identical — only execution time differs."
        ),
        "execution_order": [
            {
                "step": i + 1,
                "task": step.get("name", f"task_{i + 1}"),
                "description": step.get("description", ""),
            }
            for i, step in enumerate(steps)
        ],
        "env_check": (
            'import os; '
            'agent_teams = os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0") == "1"'
        ),
    }


def main() -> dict[str, Any]:
    """Generate native Agent Teams configuration for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate Agent Teams configuration")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--design", required=True, help="Workflow design JSON file or string")
    parser.add_argument("--output", default="agent_teams.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Analyzing workflow for Agent Teams: %s", args.system_name)

    try:
        import os

        if os.path.isfile(args.design):
            with open(args.design, "r", encoding="utf-8") as f:
                design = json.load(f)
        else:
            design = json.loads(args.design)

        steps = design.get("steps", [])

        # Step 1: Evaluate whether Agent Teams is recommended
        evaluation = evaluate_agent_teams(steps)
        logger.info(
            "Agent Teams evaluation: recommended=%s, independent_tasks=%d",
            evaluation["recommended"],
            evaluation["independent_task_count"],
        )

        if not evaluation["recommended"]:
            config = {
                "agent_teams_enabled": False,
                "evaluation": evaluation,
                "sequential_fallback": generate_sequential_fallback(steps),
            }
        else:
            # Step 2: Build team configuration
            independent = find_independent_tasks(steps)

            teammates = [
                generate_teammate_config(step, args.system_name, i)
                for i, step in enumerate(independent)
            ]

            team_lead = generate_team_lead_config(args.system_name, independent)

            config = {
                "agent_teams_enabled": True,
                "env_var": "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1",
                "evaluation": evaluation,
                "team_lead": team_lead,
                "teammates": teammates,
                "teammate_count": len(teammates),
                "sequential_fallback": generate_sequential_fallback(steps),
                "token_cost_note": (
                    f"Agent Teams will spawn {len(teammates)} teammate agents. "
                    f"Token usage for parallel sections scales ~{len(teammates)}x. "
                    "Sequential fallback produces identical results with lower token cost. "
                    "Use Agent Teams when speed matters more than token efficiency."
                ),
            }

        # Write configuration
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info("Agent Teams config written to %s", args.output)
        return {"status": "success", "config": config}

    except Exception as e:
        logger.error("Failed to generate Agent Teams config: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
