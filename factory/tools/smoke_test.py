"""
Post-build smoke tests for generated WAT systems.

For each tool in a system, attempt to import it and run main() with sample
input extracted from a SMOKE_TEST comment. Provides a 4th validation level
after syntax, unit, and integration tests.

Usage:
    python factory/tools/smoke_test.py --system-dir systems/<name>

Convention:
    Each tool can define sample input via a comment:
        # SMOKE_TEST: {"key": "value"}

    Tools requiring external API keys are detected and skipped.

Exit codes:
    0 - All smoke tests passed (or skipped)
    1 - One or more smoke tests failed
"""

import argparse
import importlib.util
import json
import os
import re
import signal
import sys
import traceback
from pathlib import Path

TIMEOUT_SECONDS = 30

# Patterns that indicate a tool needs external API keys
API_KEY_PATTERNS = [
    r"os\.environ\[.*(API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)",
    r"os\.getenv\(.*(API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)",
    r"import\s+(openai|anthropic|stripe|twilio|sendgrid|boto3)",
    r"from\s+(openai|anthropic|stripe|twilio|sendgrid|boto3)\s+import",
]


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError(f"Smoke test timed out after {TIMEOUT_SECONDS}s")


def extract_smoke_input(filepath: str) -> dict | None:
    """Extract SMOKE_TEST JSON from a tool file's comments."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception:
        return None

    match = re.search(r"#\s*SMOKE_TEST:\s*({.+})", content)
    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def needs_api_keys(filepath: str) -> bool:
    """Check if a tool file references external API keys or services."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception:
        return True  # err on the side of skipping

    for pattern in API_KEY_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def run_smoke_test(filepath: str) -> dict:
    """
    Run a smoke test for a single tool file.

    Returns:
        dict with keys: tool, status (passed|failed|skipped), message
    """
    tool_name = os.path.basename(filepath)
    result = {"tool": tool_name, "status": "skipped", "message": ""}

    # Skip tools needing external API keys
    if needs_api_keys(filepath):
        result["message"] = "Requires external API keys — skipped"
        return result

    # Extract smoke test input
    smoke_input = extract_smoke_input(filepath)
    if smoke_input is None:
        result["message"] = "No SMOKE_TEST comment found — skipped"
        return result

    # Try to import the module
    try:
        spec = importlib.util.spec_from_file_location(
            tool_name.replace(".py", ""), filepath
        )
        if spec is None or spec.loader is None:
            result["status"] = "failed"
            result["message"] = "Could not create module spec"
            return result

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        result["status"] = "failed"
        result["message"] = f"Import failed: {e}"
        return result

    # Check for main()
    if not hasattr(module, "main") or not callable(module.main):
        result["status"] = "failed"
        result["message"] = "No callable main() function"
        return result

    # Run main() with timeout
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

    try:
        # Inject smoke input as sys.argv
        original_argv = sys.argv
        sys.argv = [filepath]
        for key, value in smoke_input.items():
            sys.argv.extend([f"--{key}", str(value)])

        module.main()

        result["status"] = "passed"
        result["message"] = "Smoke test completed successfully"
    except TimeoutError:
        result["status"] = "failed"
        result["message"] = f"Timed out after {TIMEOUT_SECONDS}s"
    except SystemExit as e:
        # main() called sys.exit — exit code 0 is fine
        if e.code == 0 or e.code is None:
            result["status"] = "passed"
            result["message"] = "Completed with sys.exit(0)"
        else:
            result["status"] = "failed"
            result["message"] = f"Exited with code {e.code}"
    except Exception as e:
        result["status"] = "failed"
        result["message"] = f"Runtime error: {e}"
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        sys.argv = original_argv

    return result


def main():
    parser = argparse.ArgumentParser(description="Run smoke tests on a WAT system")
    parser.add_argument("--system-dir", required=True, help="Path to the system directory")
    args = parser.parse_args()

    tools_dir = os.path.join(args.system_dir, "tools")
    if not os.path.isdir(tools_dir):
        print(json.dumps({"status": "skipped", "reason": "no tools/ directory", "results": []}))
        return

    tool_files = sorted(
        str(p) for p in Path(tools_dir).glob("*.py") if p.name != "__init__.py"
    )

    if not tool_files:
        print(json.dumps({"status": "skipped", "reason": "no tool files found", "results": []}))
        return

    results = []
    for filepath in tool_files:
        result = run_smoke_test(filepath)
        results.append(result)

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    summary = {
        "status": "failed" if failed > 0 else "passed",
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }

    print(json.dumps(summary, indent=2))

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
