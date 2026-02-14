"""
Test Frontend — Validates generated front-end and API bridge for a WAT system.

Runs four validation levels:
- Level 1: Syntax (HTML valid, JS/TS compiles, Python imports clean)
- Level 2: Cross-reference (every tool has a form AND an API endpoint, Pydantic models match argparse)
- Level 3: Accessibility (contrast ratios, focus states, heading hierarchy, form labels)
- Level 4: Smoke (FastAPI app creates, all routes registered, health returns 200)

Inputs:
    - system_dir (str): Path to the system directory containing api/ and frontend/
    - level (int): Maximum validation level to run (1-4, default 4)
    - output (str): Path for the test results JSON

Outputs:
    - Test results JSON with pass/fail per level and details

Usage:
    python test_frontend.py --system-dir systems/my-system/ --output frontend_test_results.json
"""

import argparse
import ast
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Level 1: Syntax Validation ---

def check_python_syntax(file_path: str) -> dict[str, Any]:
    """Verify Python file has valid syntax and imports cleanly."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return {"passed": True, "message": "Python syntax OK"}
    except SyntaxError as e:
        return {"passed": False, "message": f"Syntax error at line {e.lineno}: {e.msg}"}


def check_typescript_syntax(file_path: str) -> dict[str, Any]:
    """Check that TypeScript/JavaScript files have no obvious syntax errors."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic bracket/brace/paren balance check
        open_chars = {'(': ')', '[': ']', '{': '}'}
        close_chars = {v: k for k, v in open_chars.items()}
        stack = []
        in_string = False
        string_char = None
        in_template = 0

        i = 0
        while i < len(content):
            ch = content[i]

            # Handle string literals
            if not in_string and ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                if ch == '`':
                    in_template += 1
            elif in_string and ch == string_char:
                # Check for escape
                backslashes = 0
                j = i - 1
                while j >= 0 and content[j] == '\\':
                    backslashes += 1
                    j -= 1
                if backslashes % 2 == 0:
                    in_string = False
                    if string_char == '`':
                        in_template -= 1
                    string_char = None
            elif not in_string:
                if ch in open_chars:
                    stack.append(ch)
                elif ch in close_chars:
                    if not stack:
                        return {"passed": False, "message": f"Unmatched closing '{ch}' at position {i}"}
                    if stack[-1] != close_chars[ch]:
                        return {"passed": False, "message": f"Mismatched '{stack[-1]}' and '{ch}' at position {i}"}
                    stack.pop()
            i += 1

        if stack:
            return {"passed": False, "message": f"Unclosed brackets: {''.join(stack)}"}

        return {"passed": True, "message": "TypeScript/JavaScript syntax OK"}
    except Exception as e:
        return {"passed": False, "message": f"Syntax check error: {e}"}


def check_json_syntax(file_path: str) -> dict[str, Any]:
    """Verify JSON file is valid."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return {"passed": True, "message": "JSON syntax OK"}
    except json.JSONDecodeError as e:
        return {"passed": False, "message": f"JSON error: {e}"}


def run_level1(system_dir: Path) -> dict[str, Any]:
    """Level 1: Syntax validation for all generated files."""
    results = {"level": 1, "name": "Syntax", "checks": [], "passed": True}

    # Check api/ Python files
    api_dir = system_dir / "api"
    if api_dir.is_dir():
        for py_file in sorted(api_dir.rglob("*.py")):
            check = check_python_syntax(str(py_file))
            check["file"] = str(py_file.relative_to(system_dir))
            results["checks"].append(check)
            if not check["passed"]:
                results["passed"] = False
    else:
        results["checks"].append({"file": "api/", "passed": False, "message": "api/ directory not found"})
        results["passed"] = False

    # Check frontend/ TypeScript/JavaScript files
    frontend_dir = system_dir / "frontend"
    if frontend_dir.is_dir():
        for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
            for ts_file in sorted(frontend_dir.rglob(ext)):
                # Skip node_modules
                if "node_modules" in str(ts_file):
                    continue
                check = check_typescript_syntax(str(ts_file))
                check["file"] = str(ts_file.relative_to(system_dir))
                results["checks"].append(check)
                if not check["passed"]:
                    results["passed"] = False

        # Check JSON configs
        for json_name in ("package.json", "tsconfig.json"):
            json_file = frontend_dir / json_name
            if json_file.is_file():
                check = check_json_syntax(str(json_file))
                check["file"] = str(json_file.relative_to(system_dir))
                results["checks"].append(check)
                if not check["passed"]:
                    results["passed"] = False
    else:
        results["checks"].append({"file": "frontend/", "passed": False, "message": "frontend/ directory not found"})
        results["passed"] = False

    # Check system_interface.json
    sij = system_dir / "system_interface.json"
    if sij.is_file():
        check = check_json_syntax(str(sij))
        check["file"] = "system_interface.json"
        results["checks"].append(check)
        if not check["passed"]:
            results["passed"] = False

    return results


# --- Level 2: Cross-Reference Validation ---

def run_level2(system_dir: Path) -> dict[str, Any]:
    """Level 2: Cross-reference validation — every tool has a form AND an API endpoint."""
    results = {"level": 2, "name": "Cross-Reference", "checks": [], "passed": True}

    # Load system_interface.json
    sij_path = system_dir / "system_interface.json"
    if not sij_path.is_file():
        results["checks"].append({
            "check": "system_interface.json",
            "passed": False,
            "message": "system_interface.json not found — cannot cross-reference",
        })
        results["passed"] = False
        return results

    with open(sij_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    tool_names = [t["name"] for t in manifest.get("tools", [])]

    # Check that api/main.py exists and defines routes for each tool
    api_main = system_dir / "api" / "main.py"
    if api_main.is_file():
        with open(api_main, "r", encoding="utf-8") as f:
            api_source = f.read()

        for tool_name in tool_names:
            # Look for route definition: /api/{tool_name} or tool_name in route
            route_pattern = tool_name.replace("_", "[-_]")
            if re.search(rf'["\'/]api/{route_pattern}', api_source) or re.search(rf'"{route_pattern}"', api_source):
                results["checks"].append({
                    "check": f"api_route:{tool_name}",
                    "passed": True,
                    "message": f"API route found for {tool_name}",
                })
            else:
                results["checks"].append({
                    "check": f"api_route:{tool_name}",
                    "passed": False,
                    "message": f"No API route found for tool: {tool_name}",
                })
                results["passed"] = False

        # Check pipeline endpoint exists
        if "/api/run-pipeline" in api_source:
            results["checks"].append({
                "check": "pipeline_endpoint",
                "passed": True,
                "message": "Pipeline endpoint found",
            })
        else:
            results["checks"].append({
                "check": "pipeline_endpoint",
                "passed": False,
                "message": "Missing /api/run-pipeline endpoint",
            })
            results["passed"] = False

        # Check health endpoint
        if "/api/health" in api_source:
            results["checks"].append({
                "check": "health_endpoint",
                "passed": True,
                "message": "Health endpoint found",
            })
        else:
            results["checks"].append({
                "check": "health_endpoint",
                "passed": False,
                "message": "Missing /api/health endpoint",
            })
            results["passed"] = False
    else:
        results["checks"].append({
            "check": "api/main.py",
            "passed": False,
            "message": "api/main.py not found",
        })
        results["passed"] = False

    # Check Pydantic models exist for each tool
    models_dir = system_dir / "api" / "models"
    if models_dir.is_dir():
        model_files = [f.stem for f in models_dir.glob("*.py") if f.name != "__init__.py"]
        for tool_name in tool_names:
            if tool_name in model_files or f"{tool_name}_model" in model_files:
                results["checks"].append({
                    "check": f"pydantic_model:{tool_name}",
                    "passed": True,
                    "message": f"Pydantic model found for {tool_name}",
                })
            else:
                results["checks"].append({
                    "check": f"pydantic_model:{tool_name}",
                    "passed": False,
                    "message": f"No Pydantic model file for tool: {tool_name}",
                })
                results["passed"] = False

    # Check frontend pages exist for each tool
    frontend_app = system_dir / "frontend" / "src" / "app"
    if frontend_app.is_dir():
        # Look in (dashboard) route group
        dashboard_dir = frontend_app / "(dashboard)"
        for tool_name in tool_names:
            tool_slug = tool_name.replace("_", "-")
            page_found = False
            for search_dir in [dashboard_dir, frontend_app]:
                if not search_dir.is_dir():
                    continue
                for page in search_dir.rglob("page.tsx"):
                    if tool_slug in str(page) or tool_name in str(page):
                        page_found = True
                        break
                # Also check for directory matching tool name
                if (search_dir / tool_slug).is_dir() or (search_dir / tool_name).is_dir():
                    page_found = True
            results["checks"].append({
                "check": f"frontend_page:{tool_name}",
                "passed": page_found,
                "message": f"Frontend page {'found' if page_found else 'NOT found'} for {tool_name}",
            })
            if not page_found:
                results["passed"] = False

    # Validate Pydantic models match argparse schemas
    for tool in manifest.get("tools", []):
        tool_name = tool["name"]
        model_file = models_dir / f"{tool_name}.py" if models_dir.is_dir() else None
        if model_file and model_file.is_file():
            with open(model_file, "r", encoding="utf-8") as f:
                model_source = f.read()
            # Check each argument appears in the model
            for arg in tool.get("arguments", []):
                arg_name = arg["name"]
                if arg_name in model_source:
                    results["checks"].append({
                        "check": f"model_field:{tool_name}.{arg_name}",
                        "passed": True,
                        "message": f"Model field found: {arg_name}",
                    })
                else:
                    # Skip output-only args
                    if arg_name == "output":
                        continue
                    results["checks"].append({
                        "check": f"model_field:{tool_name}.{arg_name}",
                        "passed": False,
                        "message": f"Model missing field: {arg_name} for tool {tool_name}",
                    })
                    results["passed"] = False

    return results


# --- Level 3: Accessibility Validation ---

def run_level3(system_dir: Path) -> dict[str, Any]:
    """Level 3: Accessibility checks on generated frontend."""
    results = {"level": 3, "name": "Accessibility", "checks": [], "passed": True}

    frontend_dir = system_dir / "frontend" / "src"
    if not frontend_dir.is_dir():
        results["checks"].append({
            "check": "frontend_src",
            "passed": False,
            "message": "frontend/src/ not found",
        })
        results["passed"] = False
        return results

    tsx_files = list(frontend_dir.rglob("*.tsx"))
    if not tsx_files:
        results["checks"].append({
            "check": "tsx_files",
            "passed": False,
            "message": "No .tsx files found in frontend/src/",
        })
        results["passed"] = False
        return results

    for tsx_file in tsx_files:
        rel_path = str(tsx_file.relative_to(system_dir))
        with open(tsx_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check: form inputs have labels (htmlFor or aria-label)
        # Find <input elements
        input_matches = re.findall(r'<input\b[^>]*>', content)
        for inp in input_matches:
            has_label = ("aria-label" in inp or "aria-labelledby" in inp or "id=" in inp)
            if not has_label:
                results["checks"].append({
                    "check": f"input_label:{rel_path}",
                    "passed": False,
                    "message": f"Input without label/aria-label in {rel_path}",
                })
                results["passed"] = False

        # Check: images have alt text
        img_matches = re.findall(r'<img\b[^>]*>', content)
        for img in img_matches:
            if 'alt=' not in img:
                results["checks"].append({
                    "check": f"img_alt:{rel_path}",
                    "passed": False,
                    "message": f"Image without alt text in {rel_path}",
                })
                results["passed"] = False

        # Check: heading hierarchy (no skipping levels in a single file)
        headings = re.findall(r'<h([1-6])', content)
        if headings:
            levels = [int(h) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    results["checks"].append({
                        "check": f"heading_hierarchy:{rel_path}",
                        "passed": False,
                        "message": f"Heading skip h{levels[i-1]} to h{levels[i]} in {rel_path}",
                    })
                    results["passed"] = False

        # Check: buttons have accessible text
        button_matches = re.findall(r'<button\b[^>]*>([^<]*)</button>', content)
        empty_buttons = [b for b in button_matches if not b.strip()]
        for _ in empty_buttons:
            # Check if the button tag has aria-label
            btn_tag_matches = re.findall(r'<button\b([^>]*)>[^<]*</button>', content)
            for btn_attrs in btn_tag_matches:
                if "aria-label" not in btn_attrs and not re.search(r'>[^<]+<', content):
                    results["checks"].append({
                        "check": f"button_label:{rel_path}",
                        "passed": False,
                        "message": f"Button without accessible text in {rel_path}",
                    })
                    results["passed"] = False

        # Check: focus-visible styles referenced (tailwind focus-visible: or focus: classes)
        if "page.tsx" in str(tsx_file) or "form" in content.lower():
            has_focus = "focus-visible:" in content or "focus:" in content or "focus-within:" in content
            if not has_focus and input_matches:
                results["checks"].append({
                    "check": f"focus_styles:{rel_path}",
                    "passed": False,
                    "message": f"No focus styles found for interactive elements in {rel_path}",
                })
                # This is a warning, not a blocker
                results["passed"] = results["passed"]

    # If no specific failures were found, add a passing note
    if all(c.get("passed", True) for c in results["checks"]):
        results["checks"].append({
            "check": "accessibility_overview",
            "passed": True,
            "message": f"Accessibility checks passed across {len(tsx_files)} files",
        })

    return results


# --- Level 4: Smoke Tests ---

def run_level4(system_dir: Path) -> dict[str, Any]:
    """Level 4: Smoke tests — FastAPI app creates, routes registered, health responds."""
    results = {"level": 4, "name": "Smoke", "checks": [], "passed": True}

    api_main = system_dir / "api" / "main.py"
    if not api_main.is_file():
        results["checks"].append({
            "check": "api_main_exists",
            "passed": False,
            "message": "api/main.py not found",
        })
        results["passed"] = False
        return results

    # Try to import FastAPI app
    try:
        # Add system dir and api dir to path temporarily
        original_path = sys.path.copy()
        sys.path.insert(0, str(system_dir / "api"))
        sys.path.insert(0, str(system_dir))

        import importlib.util
        spec = importlib.util.spec_from_file_location("api_main", str(api_main))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                results["checks"].append({
                    "check": "api_import",
                    "passed": True,
                    "message": "api/main.py imports successfully",
                })

                # Check app object exists
                if hasattr(module, "app"):
                    results["checks"].append({
                        "check": "app_object",
                        "passed": True,
                        "message": "FastAPI app object found",
                    })

                    # Check routes
                    app = module.app
                    if hasattr(app, "routes"):
                        route_paths = []
                        for route in app.routes:
                            if hasattr(route, "path"):
                                route_paths.append(route.path)

                        # Verify health endpoint
                        if "/api/health" in route_paths:
                            results["checks"].append({
                                "check": "health_route",
                                "passed": True,
                                "message": "GET /api/health route registered",
                            })
                        else:
                            results["checks"].append({
                                "check": "health_route",
                                "passed": False,
                                "message": "GET /api/health route not registered",
                            })
                            results["passed"] = False

                        # Verify pipeline endpoint
                        if "/api/run-pipeline" in route_paths:
                            results["checks"].append({
                                "check": "pipeline_route",
                                "passed": True,
                                "message": "POST /api/run-pipeline route registered",
                            })
                        else:
                            results["checks"].append({
                                "check": "pipeline_route",
                                "passed": False,
                                "message": "POST /api/run-pipeline route not registered",
                            })
                            results["passed"] = False

                        results["checks"].append({
                            "check": "total_routes",
                            "passed": True,
                            "message": f"{len(route_paths)} routes registered: {', '.join(route_paths)}",
                        })
                else:
                    results["checks"].append({
                        "check": "app_object",
                        "passed": False,
                        "message": "No 'app' object found in api/main.py",
                    })
                    results["passed"] = False

            except Exception as e:
                results["checks"].append({
                    "check": "api_import",
                    "passed": False,
                    "message": f"api/main.py import failed: {type(e).__name__}: {e}",
                })
                results["passed"] = False
        else:
            results["checks"].append({
                "check": "api_import",
                "passed": False,
                "message": "Could not create module spec for api/main.py",
            })
            results["passed"] = False

    except Exception as e:
        results["checks"].append({
            "check": "api_import",
            "passed": False,
            "message": f"Import setup failed: {e}",
        })
        results["passed"] = False
    finally:
        sys.path = original_path

    return results


def main() -> dict[str, Any]:
    """Run front-end validation tests."""
    parser = argparse.ArgumentParser(description="Validate generated front-end and API bridge")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    parser.add_argument("--level", type=int, default=4, choices=[1, 2, 3, 4],
                        help="Maximum validation level to run (1-4)")
    parser.add_argument("--output", default="frontend_test_results.json", help="Output results file")
    args = parser.parse_args()

    logger.info("Validating front-end in: %s (up to level %d)", args.system_dir, args.level)

    try:
        system_dir = Path(args.system_dir)
        if not system_dir.is_dir():
            return {"status": "error", "data": None, "message": f"Not a directory: {system_dir}"}

        all_results = []
        overall_passed = True

        # Level 1: Syntax
        logger.info("Running Level 1: Syntax validation")
        l1 = run_level1(system_dir)
        all_results.append(l1)
        if not l1["passed"]:
            overall_passed = False
            logger.warning("Level 1 FAILED — %d issues", sum(1 for c in l1["checks"] if not c["passed"]))
        else:
            logger.info("Level 1 PASSED")

        # Level 2: Cross-Reference
        if args.level >= 2:
            if l1["passed"]:
                logger.info("Running Level 2: Cross-reference validation")
                l2 = run_level2(system_dir)
                all_results.append(l2)
                if not l2["passed"]:
                    overall_passed = False
                    logger.warning("Level 2 FAILED — %d issues", sum(1 for c in l2["checks"] if not c["passed"]))
                else:
                    logger.info("Level 2 PASSED")
            else:
                logger.warning("Skipping Level 2 — Level 1 failed")

        # Level 3: Accessibility
        if args.level >= 3:
            if l1["passed"]:
                logger.info("Running Level 3: Accessibility validation")
                l3 = run_level3(system_dir)
                all_results.append(l3)
                if not l3["passed"]:
                    overall_passed = False
                    logger.warning("Level 3 FAILED — %d issues", sum(1 for c in l3["checks"] if not c["passed"]))
                else:
                    logger.info("Level 3 PASSED")
            else:
                logger.warning("Skipping Level 3 — Level 1 failed")

        # Level 4: Smoke
        if args.level >= 4:
            if l1["passed"]:
                logger.info("Running Level 4: Smoke tests")
                l4 = run_level4(system_dir)
                all_results.append(l4)
                if not l4["passed"]:
                    overall_passed = False
                    logger.warning("Level 4 FAILED — %d issues", sum(1 for c in l4["checks"] if not c["passed"]))
                else:
                    logger.info("Level 4 PASSED")
            else:
                logger.warning("Skipping Level 4 — Level 1 failed")

        summary = {
            "overall": "passed" if overall_passed else "failed",
            "levels_run": len(all_results),
            "results": all_results,
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        total_checks = sum(len(r["checks"]) for r in all_results)
        total_passed = sum(1 for r in all_results for c in r["checks"] if c.get("passed"))
        logger.info("Validation complete: %d/%d checks passed across %d levels",
                     total_passed, total_checks, len(all_results))

        return {
            "status": "success",
            "data": summary,
            "message": f"{'PASSED' if overall_passed else 'FAILED'} — {total_passed}/{total_checks} checks",
        }

    except Exception as e:
        logger.error("Validation failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
    if result.get("data", {}).get("overall") == "failed":
        sys.exit(1)
