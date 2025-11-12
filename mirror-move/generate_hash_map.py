#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
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

    # Pre-scan to count files to be scanned
    files_to_scan = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            filepath = Path(root) / file
            try:
                rel_path = filepath.relative_to(base_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                mtime = int(filepath.stat().st_mtime)
                key_value = next(((k, v) for (k, v) in prev_map.items() if v['path'] == rel_path_str), None)
                k, v = key_value if key_value else (None, None)
                if not (k and v['updated'] == mtime):
                    files_to_scan.append((filepath, rel_path_str, mtime))
            except Exception:
                continue
    total_files = len(files_to_scan)
    print(f"Total files to scan: {total_files}")

    file_count = 0
    start_time = time.time()
    scan_times = []
    for idx, (filepath, rel_path_str, mtime) in enumerate(files_to_scan, 1):
        try:
            print(f"Scanning: {rel_path_str}...", file=sys.stderr, end=' ')
            t0 = time.time()
            file_hash = calculate_file_hash(filepath)
            t1 = time.time()
            scan_times.append(t1 - t0)

            print("Done!", file=sys.stderr)

            if file_hash:
                hash_map[file_hash] = {'path': rel_path_str, 'updated': mtime, 'hash': file_hash}
                file_count += 1

                print(f"  Hash: {file_hash}", file=sys.stderr)

                # Write output file after each file
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(hash_map, f, indent=2, ensure_ascii=False)
                except IOError as e:
                    print(f"Error writing to {output_file}: {e}", file=sys.stderr)
            # Status indicator
            elapsed = time.time() - start_time
            avg_time = sum(scan_times) / len(scan_times) if scan_times else 0
            remaining = total_files - idx
            est_remaining = avg_time * remaining
            est_total = elapsed + est_remaining
            est_finish = time.strftime('%H:%M:%S', time.localtime(time.time() + est_remaining))
            print(f"Status: {file_count}/{total_files} files processed | Elapsed: {elapsed:.1f}s | Avg: {avg_time:.2f}s/file | Time Remaining: {est_remaining} | Est Total: {est_total} | ETA: {est_finish}", file=sys.stderr)
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
