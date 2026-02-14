"""
Generate Tools — Creates Python tool files for a WAT system.

Reads the workflow steps and generates a Python tool for each action step,
following the tool_template.py pattern. Reuses patterns from tool_catalog.md
when available.

Inputs:
    - system_name (str): Name of the system being built
    - workflow_path (str): Path to the system's workflow.md
    - design (str): JSON with tool specifications
    - catalog_path (str): Path to library/tool_catalog.md for reuse

Outputs:
    - Python .py files in the specified tools directory
    - requirements.txt listing dependencies

Usage:
    python generate_tools.py --system-name "my-system" --design tools.json --output-dir tools/
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


def load_tool_template() -> str:
    """Load the tool template."""
    template_path = TEMPLATE_DIR / "tool_template.py"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_tool_code(tool_spec: dict, template: str) -> str:
    """
    Generate Python code for a single tool based on its specification.

    Args:
        tool_spec: Dictionary with tool name, description, inputs, outputs, logic
        template: The base tool template

    Returns:
        Python source code as a string
    """
    name = tool_spec.get("name", "unnamed_tool")
    description = tool_spec.get("description", "A WAT tool.")
    inputs = tool_spec.get("inputs", [])
    outputs = tool_spec.get("outputs", [])
    dependencies = tool_spec.get("dependencies", [])
    env_vars = tool_spec.get("env_vars", [])
    logic_steps = tool_spec.get("logic", [])

    # Build docstring
    input_docs = "\n".join(
        f"    - {inp['name']} ({inp.get('type', 'str')}): {inp.get('description', '')}"
        for inp in inputs
    )
    output_docs = "\n".join(
        f"    - {out['name']} ({out.get('type', 'str')}): {out.get('description', '')}"
        for out in outputs
    )
    env_docs = "\n".join(
        f"    - {ev['name']}: {ev.get('description', '')} ({ev.get('required', 'optional')})"
        for ev in env_vars
    )

    # Build imports — split into stdlib (module level) and third-party (inside main)
    # This keeps tools import-safe for the API bridge (FastAPI calls main() directly)
    stdlib_imports = [
        "import argparse",
        "import json",
        "import logging",
        "import os",
        "import sys",
        "from typing import Any",
    ]
    third_party_imports = []
    third_party_checks = []
    for dep in dependencies:
        import_stmt = dep.get("import", "")
        pip_name = dep.get("pip", "")
        if import_stmt:
            third_party_imports.append(import_stmt)
            # Extract the module name for the dependency check
            if import_stmt.startswith("from "):
                mod = import_stmt.split()[1].split(".")[0]
            elif import_stmt.startswith("import "):
                mod = import_stmt.split()[1].split(".")[0].split(",")[0]
            else:
                mod = import_stmt
            third_party_checks.append((mod, pip_name or mod))
    import_lines = stdlib_imports

    # Build argument parser
    arg_lines = []
    for inp in inputs:
        required = inp.get("required", True)
        default = inp.get("default", None)
        arg_name = inp["name"].replace("_", "-")
        if required and default is None:
            arg_lines.append(
                f'    parser.add_argument("--{arg_name}", required=True, help="{inp.get("description", "")}")'
            )
        else:
            default_str = f'"{default}"' if isinstance(default, str) else str(default)
            arg_lines.append(
                f'    parser.add_argument("--{arg_name}", default={default_str}, help="{inp.get("description", "")}")'
            )

    # Build logic comments
    logic_comments = []
    for i, step in enumerate(logic_steps, 1):
        logic_comments.append(f"        # Step {i}: {step}")

    # Build _check_dependencies() body
    if third_party_checks:
        dep_check_lines = ["    missing = []"]
        for mod, pip_pkg in third_party_checks:
            dep_check_lines.append(f"    try:")
            dep_check_lines.append(f'        import {mod}')
            dep_check_lines.append(f"    except ImportError:")
            dep_check_lines.append(f'        missing.append("{pip_pkg}")')
        dep_check_lines.append('    if missing:')
        dep_check_lines.append('        return f"Missing dependencies: {\', \'.join(missing)}. Run: pip install {\' \'.join(missing)}"')
        dep_check_lines.append("    return None")
        dep_check_body = chr(10).join(dep_check_lines)

        # Third-party imports go inside main() after the dep check
        third_party_block = chr(10).join(f"    {stmt}" for stmt in third_party_imports)
    else:
        dep_check_body = "    return None"
        third_party_block = ""

    # Build the dep check call + third-party imports for inside main()
    main_preamble = '    # Check dependencies before doing anything else\n    dep_error = _check_dependencies()\n    if dep_error:\n        logger.error(dep_error)\n        return {"status": "error", "data": None, "message": dep_error}\n'
    if third_party_block:
        main_preamble += f"\n    # Import third-party dependencies (verified available by _check_dependencies)\n{third_party_block}\n"

    # Assemble the tool
    code = f'''"""
{name} — {description}

Inputs:
{input_docs if input_docs else "    None"}

Outputs:
{output_docs if output_docs else "    None"}

Usage:
    python {name}.py {" ".join(f"--{inp['name'].replace('_', '-')} <value>" for inp in inputs)}

Environment Variables:
{env_docs if env_docs else "    None required"}
"""

{chr(10).join(import_lines)}

# Third-party dependencies are imported inside main() to keep the module
# import-safe. No sys.exit() at module level, no side effects on import.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _check_dependencies() -> str | None:
    """Verify third-party dependencies are installed. Returns error message or None."""
{dep_check_body}


def main() -> dict[str, Any]:
    """
    Main entry point for {name}.

    Returns:
        dict: Result with status, data, and message.
    """
{main_preamble}
    parser = argparse.ArgumentParser(description="{description}")
{chr(10).join(arg_lines)}
    parser.add_argument("--output", default="output.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting {name}")

    try:
{chr(10).join(logic_comments) if logic_comments else "        # TODO: Implement tool logic"}

        result = {{
            "status": "success",
            "data": {{}},
            "message": "{name} completed successfully",
        }}

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Results written to %s", args.output)
        return result

    except Exception as e:
        logger.error("{name} failed: %s", e)
        return {{"status": "error", "data": None, "message": str(e)}}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
'''
    return code


def generate_requirements(all_dependencies: list[str]) -> str:
    """Generate requirements.txt content from collected dependencies."""
    # Deduplicate and sort
    unique_deps = sorted(set(all_dependencies))
    return "\n".join(unique_deps) + "\n" if unique_deps else ""


def main() -> dict[str, Any]:
    """Generate Python tools for a WAT system."""
    parser = argparse.ArgumentParser(description="Generate Python tools for a WAT system")
    parser.add_argument("--system-name", required=True, help="Name of the system")
    parser.add_argument("--design", required=True, help="Tool design JSON (file path or string)")
    parser.add_argument("--output-dir", default="tools", help="Output directory for tools")
    args = parser.parse_args()

    logger.info("Generating tools for system: %s", args.system_name)

    try:
        # Parse design
        if os.path.isfile(args.design):
            with open(args.design, "r", encoding="utf-8") as f:
                design = json.load(f)
        else:
            design = json.loads(args.design)

        template = load_tool_template()
        tools = design.get("tools", [])
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        all_deps = []
        generated = []

        for tool_spec in tools:
            tool_name = tool_spec.get("name", "unnamed_tool")
            logger.info("Generating tool: %s", tool_name)

            code = generate_tool_code(tool_spec, template)
            tool_path = output_dir / f"{tool_name}.py"
            with open(tool_path, "w", encoding="utf-8") as f:
                f.write(code)

            generated.append(str(tool_path))

            # Collect dependencies
            for dep in tool_spec.get("dependencies", []):
                if dep.get("pip"):
                    all_deps.append(dep["pip"])

        # Write requirements.txt
        req_content = generate_requirements(all_deps)
        req_path = output_dir.parent / "requirements.txt"
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(req_content)

        logger.info("Generated %d tools, requirements.txt written", len(generated))
        return {
            "status": "success",
            "tools_generated": generated,
            "requirements": str(req_path),
        }

    except Exception as e:
        logger.error("Failed to generate tools: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
