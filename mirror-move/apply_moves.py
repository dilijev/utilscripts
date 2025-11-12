#!/usr/bin/env python3
import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def setup_logging(log_file=None, verbose=False):
    """Setup logging configuration."""
    log_level = logging.INFO if verbose else logging.WARNING
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    if log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    return logging.getLogger(__name__)

def load_hash_map(json_file):
    """Load hash map from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading {json_file}: {e}", file=sys.stderr)
        return {}

def invert_hash_map(hash_map):
    """Invert hash map to path -> hash for easier lookup."""
    return {path: hash_val for hash_val, path in hash_map.items()}

def ensure_directory(filepath, dry_run=True, logger=None):
    """Ensure parent directory exists."""
    parent = Path(filepath).parent
    if not parent.exists():
        if dry_run:
            if logger:
                logger.info(f"[DRY RUN] Would create directory: {parent}")
            print(f"[DRY RUN] Would create directory: {parent}")
        else:
            parent.mkdir(parents=True, exist_ok=True)
            if logger:
                logger.info(f"Created directory: {parent}")
            print(f"Created directory: {parent}")

def apply_moves(base_dir, current_map, target_map, dry_run=True, logger=None):
    """Apply file moves based on hash mappings."""
    base_path = Path(base_dir).resolve()

    if not base_path.exists():
        error_msg = f"Error: Base directory {base_dir} does not exist"
        print(error_msg, file=sys.stderr)
        if logger:
            logger.error(error_msg)
        return

    # Invert maps for easier lookup
    current_path_to_hash = invert_hash_map(current_map)
    target_path_to_hash = invert_hash_map(target_map)

    # Find what needs to be moved
    moves_needed = []
    files_to_keep = set()

    for target_path, target_hash in target_path_to_hash.items():
        if target_hash in current_map:
            current_path = current_map[target_hash]
            if current_path != target_path:
                # File exists but in wrong location
                moves_needed.append((current_path, target_path, target_hash))
            files_to_keep.add(current_path)

    # Apply moves
    mode_str = "[DRY RUN] " if dry_run else ""
    action_verb = "Would move" if dry_run else "Moving"
    print(f"{mode_str}{action_verb} {len(moves_needed)} files...")

    if logger:
        logger.info(f"{mode_str}Processing {len(moves_needed)} file moves")

    successful_moves = 0
    failed_moves = 0

    for current_rel, target_rel, file_hash in moves_needed:
        current_full = base_path / current_rel
        target_full = base_path / target_rel

        if not current_full.exists():
            warning_msg = f"Warning: Source file not found: {current_rel}"
            print(warning_msg, file=sys.stderr)
            if logger:
                logger.warning(warning_msg)
            failed_moves += 1
            continue

        if target_full.exists():
            warning_msg = f"Warning: Target already exists, skipping: {target_rel}"
            print(warning_msg, file=sys.stderr)
            if logger:
                logger.warning(warning_msg)
            failed_moves += 1
            continue

        try:
            ensure_directory(target_full, dry_run, logger)

            if dry_run:
                move_msg = f"[DRY RUN] Would move: {current_rel} -> {target_rel}"
                print(move_msg)
                if logger:
                    logger.info(move_msg)
                successful_moves += 1
            else:
                shutil.move(str(current_full), str(target_full))
                move_msg = f"Moved: {current_rel} -> {target_rel}"
                print(move_msg)
                if logger:
                    logger.info(move_msg)
                successful_moves += 1

        except (OSError, IOError) as e:
            error_msg = f"Error moving {current_rel} to {target_rel}: {e}"
            print(error_msg, file=sys.stderr)
            if logger:
                logger.error(error_msg)
            failed_moves += 1

    # Report missing files (in target but not in current)
    missing_files = []
    for target_hash, target_path in target_map.items():
        if target_hash not in current_map:
            missing_files.append(target_path)

    if missing_files:
        print(f"\n=== MISSING FILES ({len(missing_files)}) ===")
        if logger:
            logger.info(f"Missing files: {len(missing_files)}")
        for missing in sorted(missing_files):
            print(f"Missing: {missing}")
            if logger:
                logger.info(f"Missing file: {missing}")

    # Report extra files (in current but not in target)
    extra_files = []
    for current_hash, current_path in current_map.items():
        if current_hash not in target_map:
            extra_files.append(current_path)

    if extra_files:
        print(f"\n=== EXTRA FILES ({len(extra_files)}) ===")
        if logger:
            logger.info(f"Extra files: {len(extra_files)}")
        for extra in sorted(extra_files):
            print(f"Extra: {extra}")
            if logger:
                logger.info(f"Extra file: {extra}")

    # Summary
    summary_lines = [
        f"\n=== SUMMARY ===",
        f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}",
        f"Successful moves: {successful_moves}",
        f"Failed moves: {failed_moves}",
        f"Missing files: {len(missing_files)}",
        f"Extra files: {len(extra_files)}"
    ]

    for line in summary_lines:
        print(line)
        if logger:
            logger.info(line.replace("=== ", "").replace(" ===", ""))

def main():
    parser = argparse.ArgumentParser(
        description="Apply file moves based on hash mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default behavior)
  python apply_moves.py /path/to/sync/folder current.json target.json

  # Explicit dry run with logging
  python apply_moves.py /path/to/sync/folder current.json target.json --dry-run --log-file moves.log

  # Execute moves with logging
  python apply_moves.py /path/to/sync/folder current.json target.json --execute --log-file moves.log --verbose
        """)

    parser.add_argument('base_directory',
                        help='Base directory containing files to move')
    parser.add_argument('current_hash_map',
                        help='JSON file with current file hash mappings')
    parser.add_argument('target_hash_map',
                        help='JSON file with target file hash mappings (source of truth)')

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--dry-run',
                           action='store_true',
                           default=True,
                           help='Show what would be moved without actually moving files (default)')
    mode_group.add_argument('--execute',
                           action='store_true',
                           help='Actually perform the file moves')

    # Logging options
    parser.add_argument('--log-file',
                        help='Log actions to specified file (also logs to stdout)')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_file, args.verbose)

    # Determine run mode
    dry_run = not args.execute

    if dry_run:
        print("=== DRY RUN MODE (use --execute to actually move files) ===")
        logger.info("Starting dry run mode")
    else:
        print("=== EXECUTE MODE (files will actually be moved) ===")
        logger.info("Starting execute mode")

    # Log start time and parameters
    start_time = datetime.now()
    logger.info(f"Run started at: {start_time}")
    logger.info(f"Base directory: {args.base_directory}")
    logger.info(f"Current hash map: {args.current_hash_map}")
    logger.info(f"Target hash map: {args.target_hash_map}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")

    print("Loading hash maps...")
    current_map = load_hash_map(args.current_hash_map)
    target_map = load_hash_map(args.target_hash_map)

    if not current_map or not target_map:
        error_msg = "Error: Could not load hash maps"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg)
        sys.exit(1)

    print(f"Current map: {len(current_map)} files")
    print(f"Target map: {len(target_map)} files")
    logger.info(f"Loaded current map: {len(current_map)} files")
    logger.info(f"Loaded target map: {len(target_map)} files")

    try:
        apply_moves(args.base_directory, current_map, target_map, dry_run, logger)
    except Exception as e:
        error_msg = f"Unexpected error during operation: {e}"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg)
        sys.exit(1)

    # Log completion
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Run completed at: {end_time}")
    logger.info(f"Total duration: {duration}")

if __name__ == "__main__":
    main()
