#!/usr/bin/env python3
import os
import sys
import json
import hashlib
from pathlib import Path

def calculate_file_hash(filepath, chunk_size=8192):
    """Calculate SHA256 hash of file contents."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (OSError, IOError) as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

def generate_hash_map(base_dir, output_file):
    """Generate mapping of file hash -> {relative path, updated time}. Only scan files whose mtime has changed."""
    base_path = Path(base_dir).resolve()
    hash_map = {}
    prev_map = {}

    # Load previous hash map if output file exists
    if Path(output_file).exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                prev_map = json.load(f)
                hash_map = prev_map.copy()
        except Exception as e:
            print(f"Warning: Could not load previous hash map: {e}", file=sys.stderr)

    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist", file=sys.stderr)
        return {}

    print(f"Scanning directory: {base_path}")

    file_count = 0
    for root, dirs, files in os.walk(base_path):
        for file in files:
            filepath = Path(root) / file
            try:
                rel_path = filepath.relative_to(base_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                mtime = int(filepath.stat().st_mtime)

                # Check if file was previously scanned and mtime is unchanged
                key_value = next(((k, v) for (k, v) in prev_map.items() if v['path'] == rel_path_str), None)
                k, v = key_value if key_value else (None, None)
                if k and v['updated'] == mtime:
                    # hash_map already has this entry from prev_map copy
                    print(f"Skipping (unchanged): {rel_path_str}", file=sys.stderr)
                    print(f"  file_hash: {k}", file=sys.stderr)
                    continue

                print(f"Scanning: {rel_path_str}...", file=sys.stderr, end='')
                file_hash = calculate_file_hash(filepath)
                print(f"Done!\n  file_hash: {file_hash}", file=sys.stderr)
                if file_hash:
                    hash_map[file_hash] = {'path': rel_path_str, 'updated': mtime, 'hash': file_hash}
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"Processed {file_count} files...", file=sys.stderr)
                    # Write output file after each file
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(hash_map, f, indent=2, ensure_ascii=False)
                    except IOError as e:
                        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
            except (OSError, ValueError) as e:
                print(f"Error processing {filepath}: {e}", file=sys.stderr)

    print(f"Completed: {file_count} files processed", file=sys.stderr)
    return hash_map

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_hash_map.py <base_directory> <output_json>")
        sys.exit(1)

    base_dir = sys.argv[1]
    output_file = sys.argv[2]

    generate_hash_map(base_dir, output_file)
