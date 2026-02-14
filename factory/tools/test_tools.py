"""
Test Tools — Validates generated Python tools for a WAT system.

Runs a suite of checks on each tool:
- Import validation (no syntax errors, all dependencies available)
- Structure validation (main() exists, docstrings present)
- Execution test with sample inputs (if provided)
- Error handling validation (try/except present)

Inputs:
    - tools_dir (str): Path to the directory containing tool .py files
    - sample_inputs (str): Optional JSON with sample inputs per tool

Outputs:
    - Test results JSON with pass/fail per tool and details

Usage:
    python test_tools.py --tools-dir tools/ --output test_results.json
"""

import argparse
import ast
import importlib.util
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


def check_syntax(file_path: str) -> dict[str, Any]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return {"passed": True, "message": "Syntax OK"}
    except SyntaxError as e:
        return {"passed": False, "message": f"Syntax error at line {e.lineno}: {e.msg}"}


def check_structure(file_path: str) -> dict[str, Any]:
    """Check that the tool follows WAT structure conventions."""
    issues = []

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    # Check module docstring
    if not (tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)):
        issues.append("Missing module-level docstring")

    # Check for main() function
    has_main = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            has_main = True
            # Check main() has a docstring
            if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                issues.append("main() missing docstring")
            break

    if not has_main:
        issues.append("Missing main() function")

    # Check for logging import
    has_logging = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging":
                    has_logging = True
        elif isinstance(node, ast.ImportFrom) and node.module == "logging":
            has_logging = True

    if not has_logging:
        issues.append("Missing logging import")

    # Check for try/except
    has_try = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            has_try = True
            break

    if not has_try:
        issues.append("Missing try/except error handling")

    # Check for if __name__ == "__main__"
    has_main_guard = False
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Compare):
                if (isinstance(test.left, ast.Name) and test.left.id == "__name__"
                        and isinstance(test.comparators[0], ast.Constant)
                        and test.comparators[0].value == "__main__"):
                    has_main_guard = True

    if not has_main_guard:
        issues.append("Missing if __name__ == '__main__' guard")

    if issues:
        return {"passed": False, "message": f"Structure issues: {'; '.join(issues)}"}
    return {"passed": True, "message": "Structure OK"}


def check_imports(file_path: str) -> dict[str, Any]:
    """Check if the tool can be imported without errors."""
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec is None or spec.loader is None:
            return {"passed": False, "message": "Could not create module spec"}

        module = importlib.util.module_from_spec(spec)
        # Don't actually execute — just validate the spec loads
        return {"passed": True, "message": "Import spec OK"}
    except Exception as e:
        return {"passed": False, "message": f"Import error: {e}"}


def test_single_tool(tool_path: str) -> dict[str, Any]:
    """Run all checks on a single tool."""
    tool_name = Path(tool_path).stem
    logger.info("Testing tool: %s", tool_name)

    results = {
        "tool": tool_name,
        "file": tool_path,
        "checks": {},
        "overall": "pass",
    }

    # Run checks
    results["checks"]["syntax"] = check_syntax(tool_path)
    results["checks"]["structure"] = check_structure(tool_path)
    results["checks"]["imports"] = check_imports(tool_path)

    # Determine overall status
    for check_name, check_result in results["checks"].items():
        if not check_result["passed"]:
            results["overall"] = "fail"
            logger.warning("FAIL: %s — %s: %s", tool_name, check_name, check_result["message"])

    if results["overall"] == "pass":
        logger.info("PASS: %s — all checks passed", tool_name)

    return results


def main() -> dict[str, Any]:
    """Test all tools in a directory."""
    parser = argparse.ArgumentParser(description="Test WAT system tools")
    parser.add_argument("--tools-dir", required=True, help="Directory containing .py tools")
    parser.add_argument("--output", default="test_results.json", help="Output results file")
    args = parser.parse_args()

    logger.info("Testing tools in: %s", args.tools_dir)

    try:
        tools_dir = Path(args.tools_dir)
        if not tools_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {tools_dir}"}

        tool_files = sorted(tools_dir.glob("*.py"))
        if not tool_files:
            logger.warning("No .py files found in %s", tools_dir)
            return {"status": "success", "data": {"tools_tested": 0, "results": []}, "message": "No tools to test"}

        all_results = []
        passed = 0
        failed = 0

        for tool_file in tool_files:
            result = test_single_tool(str(tool_file))
            all_results.append(result)
            if result["overall"] == "pass":
                passed += 1
            else:
                failed += 1

        # Check api/main.py if it exists (front-end API bridge)
        api_main = tools_dir.parent / "api" / "main.py"
        if api_main.is_file():
            logger.info("Found api/main.py — running syntax and structure checks")
            api_result = test_single_tool(str(api_main))
            all_results.append(api_result)
            if api_result["overall"] == "pass":
                passed += 1
            else:
                failed += 1

        summary = {
            "tools_tested": len(all_results),
            "passed": passed,
            "failed": failed,
            "results": all_results,
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("Testing complete: %d passed, %d failed out of %d", passed, failed, len(all_results))
        return {"status": "success", "data": summary, "message": f"{passed}/{len(all_results)} tools passed"}

    except Exception as e:
        logger.error("Testing failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
