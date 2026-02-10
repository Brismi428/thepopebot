"""
Git Operations — Git utilities for WAT system lifecycle.

Provides functions for common Git operations used during system building,
deployment, and self-improvement cycles.

Inputs:
    - action (str): The git operation to perform (init, commit, push, branch, pr)
    - Various action-specific parameters

Outputs:
    - Result of the git operation (success/failure, relevant details)

Usage:
    python git_operations.py --action commit --message "feat: add new tool" --files "tools/new_tool.py"
    python git_operations.py --action branch --name "system/my-system"
    python git_operations.py --action pr --title "New System" --body "Description" --base main --head feature
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_git(args: list[str], cwd: str | None = None) -> dict[str, Any]:
    """
    Run a git command and return the result.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command

    Returns:
        dict with stdout, stderr, and return code
    """
    cmd = ["git"] + args
    logger.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "returncode": 1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "git not found in PATH", "returncode": 1}


def init_repo(path: str) -> dict[str, Any]:
    """Initialize a new git repository."""
    result = run_git(["init"], cwd=path)
    if result["returncode"] == 0:
        logger.info("Repository initialized at %s", path)
    return result


def add_files(files: list[str], cwd: str | None = None) -> dict[str, Any]:
    """Stage files for commit."""
    result = run_git(["add"] + files, cwd=cwd)
    if result["returncode"] == 0:
        logger.info("Staged %d file(s)", len(files))
    return result


def commit(message: str, cwd: str | None = None) -> dict[str, Any]:
    """Create a commit with the given message."""
    result = run_git(["commit", "-m", message], cwd=cwd)
    if result["returncode"] == 0:
        logger.info("Committed: %s", message[:50])
    return result


def create_branch(name: str, cwd: str | None = None) -> dict[str, Any]:
    """Create and switch to a new branch."""
    result = run_git(["checkout", "-b", name], cwd=cwd)
    if result["returncode"] == 0:
        logger.info("Created branch: %s", name)
    return result


def push(remote: str = "origin", branch: str | None = None, cwd: str | None = None) -> dict[str, Any]:
    """Push to remote."""
    args = ["push", remote]
    if branch:
        args.extend(["-u", remote, branch])
    result = run_git(args, cwd=cwd)
    if result["returncode"] == 0:
        logger.info("Pushed to %s", remote)
    return result


def create_pr(title: str, body: str, base: str, head: str, cwd: str | None = None) -> dict[str, Any]:
    """Create a pull request using gh CLI."""
    cmd = [
        "gh", "pr", "create",
        "--title", title,
        "--body", body,
        "--base", base,
        "--head", head,
    ]
    logger.info("Creating PR: %s", title)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"stdout": "", "stderr": "gh CLI not found", "returncode": 1}


def get_status(cwd: str | None = None) -> dict[str, Any]:
    """Get current git status."""
    return run_git(["status", "--short"], cwd=cwd)


def get_current_branch(cwd: str | None = None) -> str:
    """Get the name of the current branch."""
    result = run_git(["branch", "--show-current"], cwd=cwd)
    return result["stdout"] if result["returncode"] == 0 else "unknown"


def main() -> dict[str, Any]:
    """Execute a git operation based on command-line arguments."""
    parser = argparse.ArgumentParser(description="Git operations for WAT systems")
    parser.add_argument("--action", required=True,
                        choices=["init", "add", "commit", "branch", "push", "pr", "status"],
                        help="Git operation to perform")
    parser.add_argument("--path", default=".", help="Working directory")
    parser.add_argument("--message", help="Commit message")
    parser.add_argument("--files", help="Comma-separated file paths to stage")
    parser.add_argument("--branch-name", help="Branch name for create_branch")
    parser.add_argument("--remote", default="origin", help="Remote name for push")
    parser.add_argument("--title", help="PR title")
    parser.add_argument("--body", help="PR body")
    parser.add_argument("--base", default="main", help="PR base branch")
    parser.add_argument("--head", help="PR head branch")
    args = parser.parse_args()

    logger.info("Git operation: %s", args.action)

    try:
        if args.action == "init":
            result = init_repo(args.path)
        elif args.action == "add":
            files = args.files.split(",") if args.files else ["."]
            result = add_files(files, cwd=args.path)
        elif args.action == "commit":
            if not args.message:
                return {"status": "error", "data": None, "message": "--message required for commit"}
            result = commit(args.message, cwd=args.path)
        elif args.action == "branch":
            if not args.branch_name:
                return {"status": "error", "data": None, "message": "--branch-name required"}
            result = create_branch(args.branch_name, cwd=args.path)
        elif args.action == "push":
            result = push(args.remote, args.branch_name, cwd=args.path)
        elif args.action == "pr":
            if not all([args.title, args.body, args.head]):
                return {"status": "error", "data": None, "message": "--title, --body, --head required for PR"}
            result = create_pr(args.title, args.body, args.base, args.head, cwd=args.path)
        elif args.action == "status":
            result = get_status(cwd=args.path)
        else:
            return {"status": "error", "data": None, "message": f"Unknown action: {args.action}"}

        status = "success" if result["returncode"] == 0 else "error"
        return {
            "status": status,
            "data": result,
            "message": result.get("stdout", "") or result.get("stderr", ""),
        }

    except Exception as e:
        logger.error("Git operation failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
