#!/usr/bin/env python3
import os
import argparse
import shutil
from pathlib import Path

def create_test_files(base_dir):
    """Create test directories with different file organizations."""
    base_path = Path(base_dir)
    
    # Clean up existing directories if they exist
    source_dir = base_path / "source"
    dest_dir = base_path / "destination"
    
    if source_dir.exists():
        shutil.rmtree(source_dir)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    # Create directory structures
    source_dirs = [
        source_dir / "documents" / "personal",
        source_dir / "documents" / "work", 
        source_dir / "media" / "photos",
        source_dir / "media" / "videos",
        source_dir / "temp" / "downloads"
    ]
    
    dest_dirs = [
        dest_dir / "organized" / "texts",
        dest_dir / "organized" / "data",
        dest_dir / "archive" / "images",
        dest_dir / "projects" / "media",
        dest_dir / "backup"
    ]
    
    # Create all directories
    for dir_path in source_dirs + dest_dirs:
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
    
    # Create files in destination directory structure (same content, different paths/names)
    dest_files = [
        (dest_dirs[0] / "report.txt", "report.txt"),              # organized/texts/
        (dest_dirs[1] / "config.json", "config.json"),           # organized/data/
        (dest_dirs[2] / "metadata.xml", "image_metadata.xml"),   # archive/images/
        (dest_dirs[3] / "process.py", "script.py"),              # projects/media/
        (dest_dirs[4] / "dataset.csv", "large_dataset.csv")      # backup/
    ]
    
    # Write source files
    print("Creating source directory structure...")
    for file_path, content_key in source_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_files[content_key])
        print(f"  Created: {file_path.relative_to(source_dir)}")
    
    # Write destination files  
    print("\nCreating destination directory structure...")
    for file_path, content_key in dest_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_files[content_key])
        print(f"  Created: {file_path.relative_to(dest_dir)}")
    
    # Create some additional files that will be "extra" in source
    extra_source_files = [
        (source_dirs[0] / "old_notes.txt", "These are old notes that don't exist in destination."),
        (source_dirs[2] / "temp_file.tmp", "Temporary file content.")
    ]
    
    print("\nCreating extra files in source (will be reported as 'extra')...")
    for file_path, content in extra_source_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created: {file_path.relative_to(source_dir)}")
    
    # Create some additional files that will be "missing" from source
    missing_files = [
        (dest_dirs[0] / "new_document.txt", "This document only exists in destination."),
        (dest_dirs[4] / "backup_config.ini", "[backup]\nfrequency=daily\nretention=30")
    ]
    
    print("\nCreating files only in destination (will be reported as 'missing')...")
    for file_path, content in missing_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created: {file_path.relative_to(dest_dir)}")
    
    print(f"\n=== Test Environment Created ===")
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    print(f"\nDirectory structure after moves will leave these empty:")
    print(f"  - source/media/photos (temp_file.tmp moves, only extra files remain)")
    print(f"  - source/media/videos (processing_script.py moves)")
    print(f"  - source/temp/downloads (employee_data.csv moves)")
    print(f"\nNext steps:")
    print(f"1. Generate hash maps:")
    print(f"   python generate_hash_map.py {source_dir} source_hashes.json")
    print(f"   python generate_hash_map.py {dest_dir} dest_hashes.json")
    print(f"2. Test move script:")
    print(f"   python apply_moves.py {source_dir} source_hashes.json dest_hashes.json --dry-run")
    print(f"3. Execute moves:")
    print(f"   python apply_moves.py {source_dir} source_hashes.json dest_hashes.json --execute")

def main():
    parser = argparse.ArgumentParser(
        description="Create test directories for file sync testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script creates two directory structures:
- 'source': Files organized in one way
- 'destination': Same file content organized differently

The same 5 files exist in both, but with different paths and sometimes different filenames.
Some directories will be left empty after moves are applied.
        """)
    
    parser.add_argument('base_directory',
                        nargs='?',
                        default='.',
                        help='Base directory to create test folders in (default: current directory)')
    
    args = parser.parse_args()
    
    try:
        create_test_files(args.base_directory)
    except Exception as e:
        print(f"Error creating test files: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
