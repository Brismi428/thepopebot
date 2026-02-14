"""
Analyze System — Reads an existing WAT system directory and produces a system_interface.json manifest.

Parses tools/*.py via AST to extract argparse arguments, env var references, and output formats.
Parses workflow.md for step ordering and data flow. Parses CLAUDE.md for system description.
Reads input/ examples for realistic sample data. Runs import-safety checks on each tool.

The resulting system_interface.json is the source of truth for front-end generation.
It is auto-generated but human-editable — downstream tools always read the JSON, never re-parse Python.

Inputs:
    - system_dir (str): Path to the existing system directory
    - output (str): Path for the output system_interface.json (default: system_interface.json in system_dir)

Outputs:
    - system_interface.json manifest describing every tool's inputs, outputs, argument schemas,
      env vars, and data flow

Usage:
    python analyze_system.py --system-dir systems/invoice-generator/
"""

import argparse
import ast
import importlib.util
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_argparse_args(source: str) -> list[dict[str, Any]]:
    """Extract argparse argument definitions from Python source via AST."""
    tree = ast.parse(source)
    args = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Match parser.add_argument(...) or similar
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"):
            continue

        arg_info: dict[str, Any] = {}

        # Get positional args (the argument name like "--input-path")
        for pos_arg in node.args:
            if isinstance(pos_arg, ast.Constant) and isinstance(pos_arg.value, str):
                name = pos_arg.value
                arg_info["name"] = name.lstrip("-").replace("-", "_")
                arg_info["cli_flag"] = name
                arg_info["positional"] = not name.startswith("-")

        # Get keyword args (required, default, help, type, choices, nargs, action)
        for kw in node.keywords:
            if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                arg_info["required"] = kw.value.value
            elif kw.arg == "default":
                if isinstance(kw.value, ast.Constant):
                    arg_info["default"] = kw.value.value
                elif isinstance(kw.value, ast.Name) and kw.value.id == "None":
                    arg_info["default"] = None
            elif kw.arg == "help" and isinstance(kw.value, ast.Constant):
                arg_info["help"] = kw.value.value
            elif kw.arg == "type" and isinstance(kw.value, ast.Name):
                arg_info["type"] = kw.value.id
            elif kw.arg == "choices":
                if isinstance(kw.value, ast.List):
                    choices = []
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant):
                            choices.append(elt.value)
                    arg_info["choices"] = choices
            elif kw.arg == "nargs" and isinstance(kw.value, ast.Constant):
                arg_info["nargs"] = kw.value.value
            elif kw.arg == "action" and isinstance(kw.value, ast.Constant):
                arg_info["action"] = kw.value.value

        # Infer required if not explicitly set
        if "required" not in arg_info:
            arg_info["required"] = arg_info.get("positional", False) and "default" not in arg_info

        # Infer type from default value if not explicitly set
        if "type" not in arg_info and "default" in arg_info and arg_info["default"] is not None:
            default = arg_info["default"]
            if isinstance(default, int):
                arg_info["type"] = "int"
            elif isinstance(default, float):
                arg_info["type"] = "float"
            elif isinstance(default, bool):
                arg_info["type"] = "bool"
            else:
                arg_info["type"] = "str"

        # Default type is str
        if "type" not in arg_info:
            if arg_info.get("action") in ("store_true", "store_false"):
                arg_info["type"] = "bool"
            else:
                arg_info["type"] = "str"

        if arg_info.get("name"):
            args.append(arg_info)

    return args


def extract_env_vars(source: str) -> list[dict[str, Any]]:
    """Extract environment variable references from Python source."""
    env_vars = []
    seen = set()

    # Pattern: os.environ["VAR_NAME"] or os.environ['VAR_NAME']
    for match in re.finditer(r'os\.environ\[(["\'])(\w+)\1\]', source):
        name = match.group(2)
        if name not in seen:
            seen.add(name)
            env_vars.append({"name": name, "required": True})

    # Pattern: os.environ.get("VAR_NAME", "default") or os.getenv("VAR_NAME", "default")
    for match in re.finditer(r'os\.(?:environ\.get|getenv)\(\s*(["\'])(\w+)\1(?:\s*,\s*([^)]+))?\)', source):
        name = match.group(2)
        default = match.group(3)
        if name not in seen:
            seen.add(name)
            env_vars.append({
                "name": name,
                "required": default is None or default.strip() == "None",
                "default": default.strip().strip("\"'") if default and default.strip() != "None" else None,
            })

    return env_vars


def extract_output_format(source: str) -> dict[str, Any]:
    """Infer the output format from the tool source."""
    output_info: dict[str, Any] = {"formats": []}

    # Check for JSON output
    if "json.dump" in source or "json.dumps" in source:
        output_info["formats"].append("json")

    # Check for file response patterns (PDF, CSV, etc.)
    if "reportlab" in source or "FPDF" in source or ".pdf" in source.lower():
        output_info["formats"].append("pdf")
    if "csv.writer" in source or "csv.DictWriter" in source or ".csv" in source:
        output_info["formats"].append("csv")
    if ".xlsx" in source or "openpyxl" in source:
        output_info["formats"].append("xlsx")
    if ".html" in source and ("write" in source or "render" in source):
        output_info["formats"].append("html")

    # Check for stdout output
    if "print(" in source or "sys.stdout" in source:
        output_info["formats"].append("stdout")

    # Check for file write patterns
    file_write_pattern = re.findall(r'open\([^,]+,\s*["\']w', source)
    if file_write_pattern:
        output_info["writes_files"] = True

    if not output_info["formats"]:
        output_info["formats"].append("json")  # default assumption

    return output_info


def extract_docstring(source: str) -> str:
    """Extract the module-level docstring."""
    try:
        tree = ast.parse(source)
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
            return tree.body[0].value.value.strip()
    except SyntaxError:
        pass
    return ""


def extract_imports(source: str) -> list[str]:
    """Extract top-level import names."""
    imports = []
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
    except SyntaxError:
        pass
    return sorted(set(imports))


def check_import_safety(tool_path: str) -> dict[str, Any]:
    """
    Check if a tool module can be safely imported.

    Flags tools that:
    - Call sys.exit() at module level
    - Pollute global state
    - Fail to import cleanly
    """
    safety = {"safe": True, "issues": []}

    try:
        with open(tool_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        safety["safe"] = False
        safety["issues"].append(f"Cannot read file: {e}")
        return safety

    # AST check: look for sys.exit() calls at module level (not inside functions)
    try:
        tree = ast.parse(source)
        for node in tree.body:
            # Skip function/class definitions and if __name__ guards
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, ast.If):
                # Check if this is the __name__ == "__main__" guard
                test = node.test
                if isinstance(test, ast.Compare):
                    if (isinstance(test.left, ast.Name) and test.left.id == "__name__"
                            and test.comparators
                            and isinstance(test.comparators[0], ast.Constant)
                            and test.comparators[0].value == "__main__"):
                        continue

            # Walk this top-level node for sys.exit() calls
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        if (isinstance(child.func.value, ast.Name)
                                and child.func.value.id == "sys"
                                and child.func.attr == "exit"):
                            safety["issues"].append(
                                f"sys.exit() called at module level (line {child.lineno})"
                            )
                    elif isinstance(child.func, ast.Name) and child.func.id == "exit":
                        safety["issues"].append(
                            f"exit() called at module level (line {child.lineno})"
                        )
    except SyntaxError as e:
        safety["safe"] = False
        safety["issues"].append(f"Syntax error: {e}")
        return safety

    # Try actual import (without executing __main__ block)
    try:
        spec = importlib.util.spec_from_file_location("_safety_check", tool_path)
        if spec is None or spec.loader is None:
            safety["issues"].append("Could not create module spec")
        else:
            module = importlib.util.module_from_spec(spec)
            # Attempt execution — this catches runtime import errors
            try:
                spec.loader.exec_module(module)
            except SystemExit as e:
                safety["safe"] = False
                safety["issues"].append(f"Module calls sys.exit({e.code}) during import")
            except Exception as e:
                safety["issues"].append(f"Import execution warning: {type(e).__name__}: {e}")
    except Exception as e:
        safety["issues"].append(f"Import check failed: {e}")

    if safety["issues"]:
        # Distinguish warnings from blockers
        blockers = [i for i in safety["issues"] if "sys.exit" in i.lower() or "syntax error" in i.lower()]
        if blockers:
            safety["safe"] = False

    return safety


def parse_workflow(workflow_path: str) -> dict[str, Any]:
    """Parse workflow.md to extract step ordering, data flow, and tool references."""
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {"steps": [], "error": "workflow.md not found"}

    steps = []
    current_step = None

    for line in content.split("\n"):
        # Match step headers: ## Step N: Title or ## Step N. Title
        step_match = re.match(r"^##\s+Step\s+(\d+\w*)[.:]\s*(.+)", line)
        if step_match:
            if current_step:
                steps.append(current_step)
            current_step = {
                "step_id": step_match.group(1),
                "title": step_match.group(2).strip(),
                "tools_referenced": [],
                "inputs": [],
                "outputs": [],
                "description_lines": [],
            }
            continue

        if current_step:
            current_step["description_lines"].append(line)

            # Extract tool references: tools/name.py or `tools/name.py`
            tool_refs = re.findall(r'`?tools/(\w+\.py)`?', line)
            for ref in tool_refs:
                tool_name = ref.replace(".py", "")
                if tool_name not in current_step["tools_referenced"]:
                    current_step["tools_referenced"].append(tool_name)

    if current_step:
        steps.append(current_step)

    # Clean up description lines
    for step in steps:
        step["description"] = "\n".join(step["description_lines"]).strip()
        del step["description_lines"]

    return {"steps": steps}


def parse_claude_md(claude_md_path: str) -> dict[str, Any]:
    """Extract system description and metadata from CLAUDE.md."""
    try:
        with open(claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {"description": "", "error": "CLAUDE.md not found"}

    info: dict[str, Any] = {}

    # Extract system name from first heading
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if title_match:
        info["system_name"] = title_match.group(1).strip()

    # Extract description (first paragraph after the title)
    desc_match = re.search(r"^#\s+.+\n\n(.+?)(?:\n\n|\n##)", content, re.MULTILINE | re.DOTALL)
    if desc_match:
        info["description"] = desc_match.group(1).strip()

    # Extract inputs section
    inputs_match = re.search(r"##\s+Inputs\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL)
    if inputs_match:
        info["inputs_section"] = inputs_match.group(1).strip()

    # Extract outputs section
    outputs_match = re.search(r"##\s+Outputs\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL)
    if outputs_match:
        info["outputs_section"] = outputs_match.group(1).strip()

    return info


def read_sample_inputs(input_dir: str) -> list[dict[str, Any]]:
    """Read sample input files from the input/ directory."""
    samples = []
    input_path = Path(input_dir)
    if not input_path.is_dir():
        return samples

    for file in sorted(input_path.iterdir()):
        if file.is_file():
            sample: dict[str, Any] = {
                "filename": file.name,
                "format": file.suffix.lstrip("."),
            }
            try:
                content = file.read_text(encoding="utf-8")
                if file.suffix == ".json":
                    sample["data"] = json.loads(content)
                else:
                    # Truncate large text files
                    sample["data"] = content[:2000] if len(content) > 2000 else content
                samples.append(sample)
            except Exception as e:
                sample["error"] = str(e)
                samples.append(sample)

    return samples


def analyze_tool(tool_path: str) -> dict[str, Any]:
    """Analyze a single Python tool file."""
    tool_name = Path(tool_path).stem
    logger.info("Analyzing tool: %s", tool_name)

    try:
        with open(tool_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return {"name": tool_name, "error": str(e)}

    tool_info = {
        "name": tool_name,
        "file": Path(tool_path).name,
        "docstring": extract_docstring(source),
        "arguments": extract_argparse_args(source),
        "env_vars": extract_env_vars(source),
        "output": extract_output_format(source),
        "imports": extract_imports(source),
        "import_safety": check_import_safety(tool_path),
    }

    return tool_info


def main() -> dict[str, Any]:
    """Analyze a WAT system and produce system_interface.json."""
    parser = argparse.ArgumentParser(description="Analyze a WAT system for front-end generation")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    parser.add_argument("--output", default=None, help="Output path for system_interface.json")
    args = parser.parse_args()

    logger.info("Analyzing system at: %s", args.system_dir)

    try:
        system_dir = Path(args.system_dir)
        if not system_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {system_dir}"}

        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "system_dir": str(system_dir.resolve()),
            "system": {},
            "tools": [],
            "workflow": {},
            "sample_inputs": [],
        }

        # Parse CLAUDE.md for system info
        claude_md = system_dir / "CLAUDE.md"
        if claude_md.is_file():
            manifest["system"] = parse_claude_md(str(claude_md))
            logger.info("Parsed CLAUDE.md")
        else:
            logger.warning("No CLAUDE.md found")

        # Parse workflow.md for step ordering
        workflow_md = system_dir / "workflow.md"
        if workflow_md.is_file():
            manifest["workflow"] = parse_workflow(str(workflow_md))
            logger.info("Parsed workflow.md — %d steps found", len(manifest["workflow"].get("steps", [])))
        else:
            logger.warning("No workflow.md found")

        # Analyze each tool
        tools_dir = system_dir / "tools"
        if tools_dir.is_dir():
            tool_files = sorted(tools_dir.glob("*.py"))
            tool_files = [f for f in tool_files if f.name != "__init__.py"]
            for tool_file in tool_files:
                tool_info = analyze_tool(str(tool_file))
                manifest["tools"].append(tool_info)
            logger.info("Analyzed %d tools", len(manifest["tools"]))
        else:
            logger.warning("No tools/ directory found")

        # Read sample inputs
        input_dir = system_dir / "input"
        manifest["sample_inputs"] = read_sample_inputs(str(input_dir))
        if manifest["sample_inputs"]:
            logger.info("Read %d sample input files", len(manifest["sample_inputs"]))

        # Derive workflow ordering for tools
        if manifest["workflow"].get("steps"):
            tool_order = []
            for step in manifest["workflow"]["steps"]:
                for tool_ref in step.get("tools_referenced", []):
                    if tool_ref not in tool_order:
                        tool_order.append(tool_ref)
            manifest["pipeline_order"] = tool_order

        # Summary of import safety
        unsafe_tools = [
            t["name"] for t in manifest["tools"]
            if not t.get("import_safety", {}).get("safe", True)
        ]
        if unsafe_tools:
            manifest["import_safety_warnings"] = unsafe_tools
            logger.warning("Import-unsafe tools: %s", ", ".join(unsafe_tools))

        # Write output
        output_path = args.output or str(system_dir / "system_interface.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info("Manifest written to %s", output_path)
        return {
            "status": "success",
            "data": {
                "tools_analyzed": len(manifest["tools"]),
                "workflow_steps": len(manifest["workflow"].get("steps", [])),
                "sample_inputs": len(manifest["sample_inputs"]),
                "import_warnings": len(unsafe_tools) if unsafe_tools else 0,
            },
            "message": f"system_interface.json written to {output_path}",
        }

    except Exception as e:
        logger.error("Analysis failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
