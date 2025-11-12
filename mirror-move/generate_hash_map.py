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

def generate_hash_map(base_dir):
    """Generate mapping of file hash -> relative path."""
    base_path = Path(base_dir).resolve()
    hash_map = {}

    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist", file=sys.stderr)
        return {}

    print(f"Scanning directory: {base_path}")

    file_count = 0
    for root, dirs, files in os.walk(base_path):
        for file in files:
            filepath = Path(root) / file
            try:
                # Get relative path from base directory
                rel_path = filepath.relative_to(base_path)
                # Convert to forward slashes for consistency
                rel_path_str = str(rel_path).replace('\\', '/')

                file_hash = calculate_file_hash(filepath)
                if file_hash:
                    hash_map[file_hash] = rel_path_str
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"Processed {file_count} files...", file=sys.stderr)

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

    hash_map = generate_hash_map(base_dir)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hash_map, f, indent=2, ensure_ascii=False)
        print(f"Hash map saved to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
        sys.exit(1)
