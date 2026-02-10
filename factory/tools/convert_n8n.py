"""
Convert n8n — Converts an n8n workflow JSON into a WAT system.

Parses an n8n workflow export, maps every node type to its WAT equivalent
using the n8n_node_map.md reference, and produces a WAT design specification
that can be fed into the other factory tools.

Inputs:
    - n8n_json (str): Path to the n8n workflow JSON file or JSON string
    - node_map_path (str): Path to converters/n8n_node_map.md

Outputs:
    - WAT design JSON with workflow steps, tool specs, and trigger config
    - Preserved original n8n JSON as a reference file

Usage:
    python convert_n8n.py --n8n-json workflow.json --output wat_design.json
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

# Mapping of n8n node types to WAT equivalents
N8N_NODE_TYPE_MAP = {
    # Triggers → GitHub Actions triggers
    "n8n-nodes-base.webhook": {"wat_type": "trigger", "gh_trigger": "repository_dispatch"},
    "n8n-nodes-base.scheduleTrigger": {"wat_type": "trigger", "gh_trigger": "schedule"},
    "n8n-nodes-base.manualTrigger": {"wat_type": "trigger", "gh_trigger": "workflow_dispatch"},
    "n8n-nodes-base.cronTrigger": {"wat_type": "trigger", "gh_trigger": "schedule"},
    # HTTP/API → Python tool with requests
    "n8n-nodes-base.httpRequest": {"wat_type": "tool", "pattern": "api_request"},
    # Code/Function → Python tool
    "n8n-nodes-base.code": {"wat_type": "tool", "pattern": "custom_code"},
    "n8n-nodes-base.function": {"wat_type": "tool", "pattern": "custom_code"},
    "n8n-nodes-base.functionItem": {"wat_type": "tool", "pattern": "custom_code"},
    # Logic → Workflow decision points
    "n8n-nodes-base.if": {"wat_type": "decision", "pattern": "conditional"},
    "n8n-nodes-base.switch": {"wat_type": "decision", "pattern": "multi_branch"},
    "n8n-nodes-base.merge": {"wat_type": "merge", "pattern": "data_merge"},
    # Data → Python tool
    "n8n-nodes-base.set": {"wat_type": "tool", "pattern": "data_transform"},
    "n8n-nodes-base.spreadsheetFile": {"wat_type": "tool", "pattern": "file_io"},
    "n8n-nodes-base.readWriteFile": {"wat_type": "tool", "pattern": "file_io"},
    # Communication → Python tool
    "n8n-nodes-base.slack": {"wat_type": "tool", "pattern": "notification"},
    "n8n-nodes-base.telegram": {"wat_type": "tool", "pattern": "notification"},
    "n8n-nodes-base.emailSend": {"wat_type": "tool", "pattern": "notification"},
    "n8n-nodes-base.discord": {"wat_type": "tool", "pattern": "notification"},
    # Database → Python tool
    "n8n-nodes-base.postgres": {"wat_type": "tool", "pattern": "database"},
    "n8n-nodes-base.mysql": {"wat_type": "tool", "pattern": "database"},
    "n8n-nodes-base.mongoDb": {"wat_type": "tool", "pattern": "database"},
    # AI → Python tool
    "n8n-nodes-base.openAi": {"wat_type": "tool", "pattern": "ai_processing"},
    "@n8n/n8n-nodes-langchain.agent": {"wat_type": "tool", "pattern": "ai_processing"},
}


def parse_n8n_json(n8n_input: str) -> dict:
    """Parse n8n workflow JSON from file path or string."""
    if os.path.isfile(n8n_input):
        with open(n8n_input, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(n8n_input)


def extract_nodes(workflow: dict) -> list[dict]:
    """Extract nodes from n8n workflow structure."""
    # n8n exports can have nodes at top level or nested
    if "nodes" in workflow:
        return workflow["nodes"]
    if isinstance(workflow, list):
        # Some exports are arrays of workflows
        for item in workflow:
            if "nodes" in item:
                return item["nodes"]
    return []


def extract_connections(workflow: dict) -> dict:
    """Extract connections (edges) from n8n workflow."""
    if "connections" in workflow:
        return workflow["connections"]
    if isinstance(workflow, list):
        for item in workflow:
            if "connections" in item:
                return item["connections"]
    return {}


def map_node_to_wat(node: dict) -> dict:
    """Map a single n8n node to its WAT equivalent."""
    node_type = node.get("type", "unknown")
    node_name = node.get("name", "Unnamed")
    parameters = node.get("parameters", {})

    mapping = N8N_NODE_TYPE_MAP.get(node_type, {"wat_type": "tool", "pattern": "custom"})

    wat_step = {
        "n8n_node_type": node_type,
        "n8n_node_name": node_name,
        "n8n_parameters": parameters,
        "wat_type": mapping["wat_type"],
    }

    if mapping["wat_type"] == "trigger":
        wat_step["gh_trigger"] = mapping.get("gh_trigger", "workflow_dispatch")
        if mapping.get("gh_trigger") == "schedule" and "rule" in parameters:
            wat_step["cron"] = parameters.get("rule", {}).get("cronExpression", "")
    elif mapping["wat_type"] == "tool":
        wat_step["pattern"] = mapping.get("pattern", "custom")
        wat_step["tool_name"] = node_name.lower().replace(" ", "_")
    elif mapping["wat_type"] == "decision":
        wat_step["pattern"] = mapping.get("pattern", "conditional")
        wat_step["conditions"] = parameters.get("conditions", {})

    return wat_step


def build_execution_order(nodes: list[dict], connections: dict) -> list[str]:
    """Determine execution order from n8n connections (topological sort)."""
    # Build adjacency list
    adj: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for node in nodes:
        name = node.get("name", "")
        if name not in adj:
            adj[name] = []
        if name not in in_degree:
            in_degree[name] = 0

    for source_name, targets in connections.items():
        if isinstance(targets, dict):
            for output_key, connections_list in targets.items():
                if isinstance(connections_list, list):
                    for conn in connections_list:
                        if isinstance(conn, list):
                            for c in conn:
                                target = c.get("node", "")
                                if target:
                                    adj.setdefault(source_name, []).append(target)
                                    in_degree[target] = in_degree.get(target, 0) + 1

    # Topological sort (Kahn's algorithm)
    queue = [n for n in adj if in_degree.get(n, 0) == 0]
    order = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order


def generate_wat_design(workflow: dict) -> dict:
    """Convert a full n8n workflow into a WAT design specification."""
    nodes = extract_nodes(workflow)
    connections = extract_connections(workflow)
    execution_order = build_execution_order(nodes, connections)

    # Map all nodes
    node_map = {}
    for node in nodes:
        name = node.get("name", "")
        node_map[name] = map_node_to_wat(node)

    # Separate triggers from steps
    triggers = []
    steps = []
    tools = []

    for name in execution_order:
        if name not in node_map:
            continue
        wat = node_map[name]
        if wat["wat_type"] == "trigger":
            triggers.append(wat)
        else:
            step = {
                "name": name,
                "description": f"Converted from n8n node: {wat.get('n8n_node_type', 'unknown')}",
                "wat_type": wat["wat_type"],
            }
            if wat["wat_type"] == "tool":
                step["tool"] = f"{wat.get('tool_name', name.lower())}.py"
                tools.append({
                    "name": wat.get("tool_name", name.lower().replace(" ", "_")),
                    "description": f"Converted from n8n {wat['n8n_node_type']}: {name}",
                    "pattern": wat.get("pattern", "custom"),
                    "n8n_parameters": wat.get("n8n_parameters", {}),
                })
            elif wat["wat_type"] == "decision":
                step["decision"] = {
                    "condition": str(wat.get("conditions", "condition")),
                    "yes": "Continue to next step",
                    "no": "Skip or take alternate path",
                }
            steps.append(step)

    # Determine GitHub Actions triggers
    gh_triggers = ["workflow_dispatch"]  # Always include manual
    cron = None
    for t in triggers:
        trigger_type = t.get("gh_trigger", "")
        if trigger_type and trigger_type not in gh_triggers:
            gh_triggers.append(trigger_type)
        if t.get("cron"):
            cron = t["cron"]

    return {
        "title": workflow.get("name", "Converted n8n Workflow"),
        "description": f"Converted from n8n workflow. Original had {len(nodes)} nodes.",
        "inputs": [{"name": "task_input", "type": "str", "description": "Task input from trigger"}],
        "outputs": [{"name": "result", "type": "JSON", "description": "Workflow execution result"}],
        "steps": steps,
        "tools": tools,
        "github_actions": {
            "triggers": gh_triggers,
            "cron": cron,
            "secrets": [],
        },
        "n8n_metadata": {
            "original_node_count": len(nodes),
            "trigger_count": len(triggers),
            "step_count": len(steps),
            "tool_count": len(tools),
        },
    }


def main() -> dict[str, Any]:
    """Convert an n8n workflow JSON into a WAT design specification."""
    parser = argparse.ArgumentParser(description="Convert n8n workflow to WAT")
    parser.add_argument("--n8n-json", required=True, help="Path to n8n JSON or JSON string")
    parser.add_argument("--output", default="wat_design.json", help="Output design JSON path")
    parser.add_argument("--preserve-original", default=None, help="Path to save original n8n JSON")
    args = parser.parse_args()

    logger.info("Converting n8n workflow to WAT design")

    try:
        workflow = parse_n8n_json(args.n8n_json)
        design = generate_wat_design(workflow)

        # Write WAT design
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(design, f, indent=2)
        logger.info("WAT design written to %s", args.output)

        # Preserve original n8n JSON if requested
        if args.preserve_original:
            Path(args.preserve_original).parent.mkdir(parents=True, exist_ok=True)
            with open(args.preserve_original, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2)
            logger.info("Original n8n JSON preserved at %s", args.preserve_original)

        return {
            "status": "success",
            "design_path": args.output,
            "metadata": design.get("n8n_metadata", {}),
        }

    except json.JSONDecodeError as e:
        logger.error("Invalid n8n JSON: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except Exception as e:
        logger.error("Conversion failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
