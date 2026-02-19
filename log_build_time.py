#!/usr/bin/env python3
"""
log_build_completion.py

For each input file (relative to Chromium src/), this script:

1) Finds the Chromium src/ git root, derives src/brave as the normalized directory
2) Adds an entry under the normalized directory path in a JSON file (default 
Logs the current date/time in ISO-8601 format, the exit code of the last command
 adds an entry under the normalized directory path
3) 
4) Applies the patch with:       git apply -p0 <patch>

Usage:
  ./log_build_completion.py --log-file <path>
"""

import argparse
import os
import shlex
import subprocess
import sys
from typing import List, Optional


def run(cmd: List[str], *, cwd: Optional[str] = None, check: bool = True, dry_run: bool = False) -> subprocess.CompletedProcess:
    pretty = " ".join(shlex.quote(c) for c in cmd)
    if cwd:
        pretty = f"(cd {shlex.quote(cwd)} && {pretty})"
    print(pretty)
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, cwd=cwd, check=check)


def find_git_root(path: str) -> Optional[str]:
    path = os.path.abspath(path)
    while path != "/":
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return None


def ensure_src_root(git_root: str) -> str:
    # If the closest .git is src/brave, walk up to src.
    if os.path.basename(git_root) == "src":
        return git_root
    parent = os.path.dirname(git_root)
    if os.path.basename(parent) == "src":
        return parent
    if os.path.basename(os.path.dirname(parent)) == "src":
        return os.path.dirname(parent)
    return git_root


def patch_name(rel_path_from_src: str, src_root: str) -> str:
    # Replace / and \ with -, add .patch suffix, add brave/patches prefix.
    name = rel_path_from_src.replace("/", "-").replace("\\", "-")
    return os.path.join(src_root, "brave", "patches", name + ".patch")


def reset_and_apply_patch(file_path: str, src_root: str, dry_run: bool) -> None:
    # Normalize input file -> rel path from src_root
    if os.path.isabs(file_path):
        abs_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(abs_path, src_root)
    else:
        rel_path = os.path.normpath(file_path)

    patch_file = patch_name(rel_path, src_root)
    target_file = os.path.join(src_root, rel_path)

    print(f"target: {rel_path}")
    if not os.path.exists(target_file):
        print(f"  ⚠️\tWarning: target file not found for {rel_path}: {target_file}", file=sys.stderr)
    else:
        print(f"  ✅\tTarget file exists: {target_file}")

    print(f"patch:  {patch_file}")
    if not os.path.exists(patch_file):
        print(f"  ⚠️\tWarning: patch file not found for {rel_path}: {patch_file}", file=sys.stderr)
    else:
        print(f"  ✅\tPatch file exists: {patch_file}")

    print()  # blank line for readability

    # 1) Reset the target file if it exists, else warn.
    if os.path.exists(target_file):
        print(f"Resetting {rel_path} to HEAD version...")
        run(["git", "-C", src_root, "checkout", "--", rel_path], dry_run=dry_run)
    else:
        print(f"  ⚠️\tWarning: Skipping patch application for {rel_path} since target file is missing.", file=sys.stderr)
        return

    if not os.path.exists(patch_file):
        return

    print(f"Applying patch for {rel_path}...")
    # 2) Apply the patch.
    # -p1 matches patches generated with a/ and b/ prefixes by stripping the leading a/ or b/.
    run(["git", "-C", src_root, "apply", "-p1", "--whitespace=nowarn", patch_file], dry_run=dry_run)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="Target file path(s) relative to Chromium src/ (or absolute under src/).")
    ap.add_argument("--dry-run", action="store_true", help="Print what would run, but do not execute.")
    args = ap.parse_args()

    cwd = os.getcwd()
    git_root = find_git_root(cwd)
    if not git_root:
        print("Error: Could not find git repository root (no .git found while walking up).", file=sys.stderr)
        return 1

    src_root = ensure_src_root(git_root)
    brave_dir = os.path.join(src_root, "brave")
    if not os.path.isdir(brave_dir):
        print(f"Error: expected brave checkout at {brave_dir}", file=sys.stderr)
        return 1

    print(f"src root: {src_root}")

    for file_path in args.files:
        reset_and_apply_patch(file_path, src_root, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
