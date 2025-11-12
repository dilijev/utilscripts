#!/usr/bin/env python3
import os
import argparse
import shutil
from pathlib import Path

SOURCE_DIR="machine1"
DEST_DIR="machine2"


def create_destination_from_source(source_dir, dest_dir):
    """Create destination directory by copying source and reorganizing files."""
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)

    print(f"Creating destination directory from source...")

    # Clean up existing destination
    if dest_path.exists():
        shutil.rmtree(dest_path)

    # Copy entire source directory to destination
    print("  Copying source directory...")
    shutil.copytree(source_path, dest_path)

    print("Reorganizing files in destination...")

    # Create new directory structure
    new_dirs = [
        dest_path / "organized" / "texts",
        dest_path / "organized" / "data",
        dest_path / "archive" / "images",
        dest_path / "projects" / "media",
        dest_path / "backup"
    ]

    for dir_path in new_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Move and rename files to simulate reorganization
    moves = [
        (dest_path / "documents" / "personal" / "quarterly_report.txt",
         dest_path / "organized" / "texts" / "report.txt"),

        (dest_path / "documents" / "work" / "app_config.json",
         dest_path / "organized" / "data" / "config.json"),

        (dest_path / "media" / "photos" / "photo_meta.xml",
         dest_path / "archive" / "images" / "metadata.xml"),

        (dest_path / "media" / "videos" / "processing_script.py",
         dest_path / "projects" / "media" / "process.py"),

        (dest_path / "temp" / "downloads" / "employee_data.csv",
         dest_path / "backup" / "dataset.csv")
    ]

    for source_file, dest_file in moves:
        if source_file.exists():
            print(f"  Moving {source_file.relative_to(dest_path)} -> {dest_file.relative_to(dest_path)}")
            shutil.move(str(source_file), str(dest_file))
        else:
            print(f"  Warning: {source_file.relative_to(dest_path)} not found")

    # Remove now-empty directories (simulate directories left vacant by moves)
    print("Removing empty directories...")
    empty_dirs_to_try = [
        dest_path / "documents" / "work",
        dest_path / "media" / "videos",
        dest_path / "temp" / "downloads",
        dest_path / "temp"
    ]

    for dir_path in empty_dirs_to_try:
        try:
            if dir_path.exists() and not any(dir_path.iterdir()):
                dir_path.rmdir()
                print(f"  Removed empty directory: {dir_path.relative_to(dest_path)}")
        except OSError as e:
            print(f"  Could not remove {dir_path.relative_to(dest_path)}: directory not empty")

    # Create additional files that only exist in destination (missing from source)
    print("Creating files that only exist in destination...")

    new_files = [
        (dest_path / "organized" / "texts" / "new_document.txt",
         "This document only exists in destination."),
        (dest_path / "backup" / "backup_config.ini",
         "[backup]\nfrequency=daily\nretention=30")
    ]

    for file_path, content in new_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created: {file_path.relative_to(dest_path)}")

def print_directory_structure(base_path, dir_name):
    """Print a visual representation of directory structure."""
    print(f"\n{dir_name}/")

    def print_tree(path, prefix="", is_last=True):
        if not path.is_dir():
            return

        items = list(path.iterdir())
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))

        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            print(f"{prefix}{current_prefix}{item.name}")

            if item.is_dir():
                next_prefix = prefix + ("    " if is_last_item else "│   ")
                print_tree(item, next_prefix, is_last_item)

    print_tree(base_path)

def create_test_files(base_dir, create_dest=True):
    """Create test source directory and optionally the destination."""
    base_path = Path(base_dir)

    # Clean up existing directories if they exist
    source_dir = base_path / SOURCE_DIR
    dest_dir = base_path / DEST_DIR

    if source_dir.exists():
        shutil.rmtree(source_dir)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    # Create source directory structure
    source_dirs = [
        source_dir / "documents" / "personal",
        source_dir / "documents" / "work",
        source_dir / "media" / "photos",
        source_dir / "media" / "videos",
        source_dir / "temp" / "downloads"
    ]

    # Create all source directories
    for dir_path in source_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Test file contents (different content for each file)
    test_files = {
        "report.txt": "This is a detailed quarterly report with important financial data.\nRevenue increased by 15% this quarter.\nExpenses were kept under control.",

        "config.json": """{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "production_db"
    },
    "cache": {
        "redis_url": "redis://localhost:6379",
        "ttl": 3600
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/app.log"
    }
}""",

        "image_metadata.xml": """<?xml version="1.0" encoding="UTF-8"?>
<metadata>
    <camera>
        <make>Canon</make>
        <model>EOS R5</model>
        <lens>RF 24-70mm f/2.8L IS USM</lens>
    </camera>
    <settings>
        <iso>800</iso>
        <aperture>f/5.6</aperture>
        <shutter>1/60</shutter>
        <focal_length>35mm</focal_length>
    </settings>
    <location>
        <latitude>37.7749</latitude>
        <longitude>-122.4194</longitude>
        <city>San Francisco</city>
    </location>
</metadata>""",

        "script.py": """#!/usr/bin/env python3
import sys
import os
from pathlib import Path

def process_data(input_file, output_file):
    \"\"\"Process input data and write results.\"\"\"
    try:
        with open(input_file, 'r') as f:
            data = f.read().strip().split('\\n')

        processed = [line.upper().replace(' ', '_') for line in data if line]

        with open(output_file, 'w') as f:
            f.write('\\n'.join(processed))

        print(f"Processed {len(processed)} lines")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py input.txt output.txt")
        sys.exit(1)

    process_data(sys.argv[1], sys.argv[2])
""",

        "large_dataset.csv": """id,name,email,department,salary,hire_date
1001,John Smith,john.smith@company.com,Engineering,95000,2020-03-15
1002,Sarah Johnson,sarah.j@company.com,Marketing,72000,2019-08-22
1003,Mike Chen,m.chen@company.com,Engineering,88000,2021-01-10
1004,Lisa Rodriguez,lisa.r@company.com,Sales,67000,2018-11-05
1005,David Park,d.park@company.com,Engineering,92000,2020-07-18
1006,Anna Kowalski,a.kowalski@company.com,HR,58000,2017-09-12
1007,James Wilson,j.wilson@company.com,Finance,71000,2019-04-03
1008,Maria Garcia,maria.g@company.com,Marketing,69000,2021-06-25
1009,Robert Taylor,r.taylor@company.com,Sales,73000,2018-02-14
1010,Jennifer Liu,j.liu@company.com,Engineering,97000,2020-12-08"""
    }

    # Create files in source directory structure
    source_files = [
        (source_dirs[0] / "quarterly_report.txt", "report.txt"),  # documents/personal/
        (source_dirs[1] / "app_config.json", "config.json"),     # documents/work/
        (source_dirs[2] / "photo_meta.xml", "image_metadata.xml"), # media/photos/
        (source_dirs[3] / "processing_script.py", "script.py"),  # media/videos/
        (source_dirs[4] / "employee_data.csv", "large_dataset.csv") # temp/downloads/
    ]

    # Write source files
    print("Creating source directory structure...")
    for file_path, content_key in source_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_files[content_key])
        print(f"  Created: {file_path.relative_to(source_dir)}")

    # Create some additional files that will remain in source (extras)
    extra_source_files = [
        (source_dirs[0] / "old_notes.txt", "These are old notes that don't exist in destination."),
        (source_dirs[2] / "temp_file.tmp", "Temporary file content.")
    ]

    print("\nCreating extra files in source (will be reported as 'extra')...")
    for file_path, content in extra_source_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created: {file_path.relative_to(source_dir)}")

    # Create destination directory if requested
    if create_dest:
        print(f"\n{'='*50}")
        create_destination_from_source(source_dir, dest_dir)

        print(f"\n{'='*50}")
        print("=== Test Environment Created ===")
        print_directory_structure(dest_dir, DEST_DIR)

        print(f"\nEmpty directories that would be left after moves:")
        print(f"- documents/work/ (empty after moving app_config.json)")
        print(f"- media/videos/ (empty after moving processing_script.py)")
        print(f"- temp/downloads/ (empty after moving employee_data.csv)")
        print(f"- temp/ (empty after removing downloads/)")
    else:
        print(f"\n=== Source Directory Created ===")
        print_directory_structure(source_dir, SOURCE_DIR)
        print(f"\nTo create destination, run:")
        print(f"python create_test_dirs.py --create-destination {base_dir}")

    print(f"\nNext steps:")
    if create_dest:
        print(f"1. Generate hash maps:")
        print(f"   python generate_hash_map.py test/{SOURCE_DIR} machine1_hashes.json")
        print(f"   python generate_hash_map.py test/{DEST_DIR} machine2_hashes.json")
        print(f"2. Test move script (move files on machine2 to the relative locations per machine1:")
        print(f"   python apply_moves.py test/machine2 machine2_hashes.json machine1_hashes.json --dry-run --verbose --log-file dry_run.log")
        print(f"3. Execute moves:")
        print(f"   python apply_moves.py test/machine2 machine2_hashes.json machine1_hashes.json --execute --verbose --log-file test_moves.log")
    else:
        print(f"1. Create destination directory")
        print(f"2. Generate hash maps and test sync")

def main():
    parser = argparse.ArgumentParser(
        description="Create test directories for file sync testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script creates test directories to simulate manual file reorganization:
- 'source': Files organized in original structure
- 'destination': Same files reorganized into different structure

Use --source-only to create just the source directory first.
        """)

    parser.add_argument('base_directory',
                        nargs='?',
                        default='.',
                        help='Base directory to create test folders in (default: current directory)')

    parser.add_argument('--source-only',
                        action='store_true',
                        help='Create only the source directory (no destination)')

    parser.add_argument('--create-destination',
                        action='store_true',
                        help='Create destination from existing source directory')

    args = parser.parse_args()

    base_path = Path(args.base_directory)

    if args.create_destination:
        # Only create destination from existing source
        source_dir = base_path / SOURCE_DIR
        dest_dir = base_path / DEST_DIR

        if not source_dir.exists():
            print(f"Error: Source directory {source_dir} does not exist", file=sys.stderr)
            return 1

        create_destination_from_source(source_dir, dest_dir)
        print("\n=== Destination Created ===")
        print_directory_structure(dest_dir, DEST_DIR)

    else:
        # Create source and optionally destination
        try:
            create_test_files(args.base_directory, not args.source_only)
        except Exception as e:
            print(f"Error creating test files: {e}", file=sys.stderr)
            return 1

    return 0

if __name__ == "__main__":
    exit(main())
