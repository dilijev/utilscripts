#!/usr/bin/env python3
import os
import sys
import json
import shutil
from pathlib import Path
from collections import defaultdict

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

def ensure_directory(filepath):
    """Ensure parent directory exists."""
    parent = Path(filepath).parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

def apply_moves(base_dir, current_map, target_map):
    """Apply file moves based on hash mappings."""
    base_path = Path(base_dir).resolve()
    
    if not base_path.exists():
        print(f"Error: Base directory {base_dir} does not exist", file=sys.stderr)
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
    print(f"Applying {len(moves_needed)} file moves...")
    
    for current_rel, target_rel, file_hash in moves_needed:
        current_full = base_path / current_rel
        target_full = base_path / target_rel
        
        if not current_full.exists():
            print(f"Warning: Source file not found: {current_rel}", file=sys.stderr)
            continue
            
        if target_full.exists():
            print(f"Warning: Target already exists, skipping: {target_rel}", file=sys.stderr)
            continue
        
        try:
            ensure_directory(target_full)
            shutil.move(str(current_full), str(target_full))
            print(f"Moved: {current_rel} -> {target_rel}")
        except (OSError, IOError) as e:
            print(f"Error moving {current_rel} to {target_rel}: {e}", file=sys.stderr)
    
    # Report missing files (in target but not in current)
    missing_files = []
    for target_hash, target_path in target_map.items():
        if target_hash not in current_map:
            missing_files.append(target_path)
    
    if missing_files:
        print(f"\n=== MISSING FILES ({len(missing_files)}) ===")
        for missing in sorted(missing_files):
            print(f"Missing: {missing}")
    
    # Report extra files (in current but not in target)
    extra_files = []
    for current_hash, current_path in current_map.items():
        if current_hash not in target_map:
            extra_files.append(current_path)
    
    if extra_files:
        print(f"\n=== EXTRA FILES ({len(extra_files)}) ===")
        for extra in sorted(extra_files):
            print(f"Extra: {extra}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Files moved: {len(moves_needed)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Extra files: {len(extra_files)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python apply_moves.py <base_directory> <current_hash_map.json> <target_hash_map.json>")
        print("  current_hash_map.json: Current state (Mac)")
        print("  target_hash_map.json: Desired state (Windows - source of truth)")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    current_json = sys.argv[2]
    target_json = sys.argv[3]
    
    print("Loading hash maps...")
    current_map = load_hash_map(current_json)
    target_map = load_hash_map(target_json)
    
    if not current_map or not target_map:
        print("Error: Could not load hash maps", file=sys.stderr)
        sys.exit(1)
    
    print(f"Current map: {len(current_map)} files")
    print(f"Target map: {len(target_map)} files")
    
    apply_moves(base_dir, current_map, target_map)
