"""
Version an existing system before overwriting it with a new build.

Copies the current system files (excluding the versions/ directory) into
systems/{name}/versions/vN/ with a metadata.json recording the version,
date, job ID, and confidence score.

Usage:
    python factory/tools/version_system.py --system-name <name> [--job-id <id>] [--confidence <score>]

Exit codes:
    0 - Versioned successfully (or system didn't exist yet)
    1 - Error during versioning
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone


def get_next_version(versions_dir: str) -> int:
    """Determine the next version number from existing versions."""
    if not os.path.isdir(versions_dir):
        return 1
    existing = []
    for entry in os.listdir(versions_dir):
        if entry.startswith("v") and entry[1:].isdigit():
            existing.append(int(entry[1:]))
    return max(existing, default=0) + 1


def version_system(system_dir: str, job_id: str = "", confidence: int = 0) -> dict:
    """
    Archive the current system into its versions/ subdirectory.

    Args:
        system_dir: Path to systems/{name}/
        job_id: The job ID that triggered this build
        confidence: PRP confidence score

    Returns:
        dict with version info, or None if system didn't exist
    """
    if not os.path.isdir(system_dir):
        return None

    versions_dir = os.path.join(system_dir, "versions")
    version_num = get_next_version(versions_dir)
    version_dir = os.path.join(versions_dir, f"v{version_num}")

    os.makedirs(version_dir, exist_ok=True)

    # Copy all files/dirs except versions/
    for item in os.listdir(system_dir):
        if item == "versions":
            continue
        src = os.path.join(system_dir, item)
        dst = os.path.join(version_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Write metadata
    metadata = {
        "version": version_num,
        "date": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "confidence": confidence,
    }
    with open(os.path.join(version_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Version an existing system before rebuild")
    parser.add_argument("--system-name", required=True, help="Name of the system to version")
    parser.add_argument("--job-id", default="", help="Job ID triggering the build")
    parser.add_argument("--confidence", type=int, default=0, help="PRP confidence score")
    args = parser.parse_args()

    # Resolve system directory relative to repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    system_dir = os.path.join(repo_root, "systems", args.system_name)

    try:
        result = version_system(system_dir, args.job_id, args.confidence)
        if result is None:
            print(json.dumps({"status": "skipped", "reason": "system does not exist yet"}))
        else:
            print(json.dumps({"status": "versioned", **result}))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
