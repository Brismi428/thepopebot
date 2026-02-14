#!/usr/bin/env python3
"""
Git Commit and Push Tool

Stages specific files, commits with a message, and optionally pushes to remote.

CRITICAL: This tool uses ONLY specific file paths. NEVER uses `git add -A` or `git add .`.

Usage:
    python git_commit.py \
        --files output/published/*.json output/failed/*.json logs/*.md \
        --message "Published 5 posts, 2 failures [2026-02-14 12:00:00]" \
        --push

Returns:
    JSON: {"committed": bool, "commit_sha": "...", "pushed": bool}
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_git_command(
    args: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a git command.
    
    Args:
        args: Git command arguments
        cwd: Working directory (default: current directory)
        check: Raise exception on non-zero exit
        
    Returns:
        CompletedProcess result
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: git {' '.join(args)}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise


def expand_glob_patterns(patterns: list[str], cwd: Path | None = None) -> list[str]:
    """
    Expand glob patterns to actual file paths.
    
    Args:
        patterns: List of file paths or glob patterns
        cwd: Working directory
        
    Returns:
        List of resolved file paths
    """
    base_path = cwd or Path.cwd()
    resolved_files = []
    
    for pattern in patterns:
        pattern_path = Path(pattern)
        
        # If pattern contains glob characters
        if "*" in pattern or "?" in pattern:
            # Resolve glob from base path
            matches = list(base_path.glob(pattern))
            resolved_files.extend([str(m.relative_to(base_path)) for m in matches])
        else:
            # Check if file exists
            full_path = base_path / pattern_path
            if full_path.exists():
                resolved_files.append(pattern)
            else:
                logger.warning(f"File does not exist: {pattern}")
    
    return resolved_files


def git_commit(
    files: list[str],
    message: str,
    push: bool = False,
    retry: bool = True,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """
    Stage files, commit, and optionally push.
    
    Args:
        files: List of file paths to stage (supports glob patterns)
        message: Commit message
        push: Whether to push to remote
        retry: Retry commit once with rebase if push fails
        cwd: Working directory
        
    Returns:
        Result dictionary
    """
    base_path = cwd or Path.cwd()
    
    try:
        # Expand glob patterns
        logger.info("Resolving file paths...")
        resolved_files = expand_glob_patterns(files, base_path)
        
        if not resolved_files:
            logger.warning("No files to commit")
            return {
                "committed": False,
                "commit_sha": "",
                "pushed": False,
                "message": "No files to commit",
            }
        
        logger.info(f"Staging {len(resolved_files)} file(s)...")
        for file_path in resolved_files:
            logger.debug(f"  - {file_path}")
        
        # Stage files individually (NEVER use git add -A or git add .)
        for file_path in resolved_files:
            run_git_command(["add", file_path], cwd=base_path)
        
        # Check if there are staged changes
        status_result = run_git_command(["status", "--porcelain"], cwd=base_path, check=False)
        
        if not status_result.stdout.strip():
            logger.info("No changes to commit")
            return {
                "committed": False,
                "commit_sha": "",
                "pushed": False,
                "message": "No changes to commit",
            }
        
        # Commit
        logger.info(f"Committing: {message}")
        run_git_command(["commit", "-m", message], cwd=base_path)
        
        # Get commit SHA
        sha_result = run_git_command(["rev-parse", "HEAD"], cwd=base_path)
        commit_sha = sha_result.stdout.strip()
        
        logger.info(f"✓ Committed: {commit_sha[:8]}")
        
        # Push if requested
        pushed = False
        if push:
            try:
                logger.info("Pushing to origin...")
                run_git_command(["push", "origin", "HEAD"], cwd=base_path)
                pushed = True
                logger.info("✓ Pushed successfully")
            except subprocess.CalledProcessError as e:
                if retry:
                    logger.warning("Push failed, retrying with rebase...")
                    try:
                        # Pull with rebase
                        run_git_command(["pull", "--rebase", "origin", "HEAD"], cwd=base_path)
                        # Retry push
                        run_git_command(["push", "origin", "HEAD"], cwd=base_path)
                        pushed = True
                        logger.info("✓ Pushed successfully after rebase")
                    except subprocess.CalledProcessError:
                        logger.error("Push failed after retry. Results are committed locally.")
                        # Don't raise - commit is done, push failure is not fatal
                else:
                    logger.error("Push failed. Results are committed locally.")
        
        return {
            "committed": True,
            "commit_sha": commit_sha,
            "pushed": pushed,
            "files_count": len(resolved_files),
        }
        
    except subprocess.CalledProcessError as e:
        logger.exception(f"Git operation failed: {e}")
        return {
            "committed": False,
            "commit_sha": "",
            "pushed": False,
            "error": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {
            "committed": False,
            "commit_sha": "",
            "pushed": False,
            "error": str(e),
        }


def main(
    files: list[str],
    message: str | None = None,
    push: bool = False,
    auto_message: bool = False,
) -> dict[str, Any]:
    """
    Main entry point.
    
    Args:
        files: List of file paths to commit
        message: Commit message (auto-generated if None and auto_message=True)
        push: Push to remote
        auto_message: Generate commit message automatically
        
    Returns:
        Result dictionary
    """
    try:
        # Auto-generate message if requested
        if auto_message and not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Instagram publish update [{timestamp}]"
        
        if not message:
            raise ValueError("Commit message required (use --message or --auto-message)")
        
        return git_commit(
            files=files,
            message=message,
            push=push,
        )
        
    except Exception as e:
        logger.exception(f"Commit failed: {e}")
        return {
            "committed": False,
            "commit_sha": "",
            "pushed": False,
            "error": str(e),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Git commit and push tool")
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="File paths to stage (supports globs like output/*.json)",
    )
    parser.add_argument(
        "--message",
        type=str,
        help="Commit message",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to remote",
    )
    parser.add_argument(
        "--auto-message",
        action="store_true",
        help="Auto-generate commit message",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    args = parser.parse_args()
    
    result = main(
        files=args.files,
        message=args.message,
        push=args.push,
        auto_message=args.auto_message,
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["committed"]:
            print(f"✓ Committed: {result['commit_sha'][:8]} ({result.get('files_count', 0)} files)")
            if result["pushed"]:
                print("✓ Pushed to remote")
        else:
            print(f"✗ Commit failed: {result.get('error', 'unknown error')}", file=sys.stderr)
            sys.exit(1)
