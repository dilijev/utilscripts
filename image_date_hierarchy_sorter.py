#!/usr/bin/env python3

# Given a flat directory of images, determine the date that should apply to them.
# if there's a yyyymmdd in the filename, use that timestamp.
# If there's no yyyymmdd in the filename, use the Date Modified
# Create a directory structure of YYYY/MM/ if it doesn't exist for the file's
# date, and move the file into that directory.

import argparse
import os
import re
import shutil
from pathlib import Path
from datetime import datetime


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
DATE_PATTERN = re.compile(r'(\d{8})')


def extract_date_from_filename(filename: str) -> str | None:
    """Extract YYYYMMDD date from filename. Returns None if not found."""
    match = DATE_PATTERN.search(filename)
    return match.group(1) if match else None


def get_date_string(file_path: Path) -> str:
    """Get YYYYMMDD string from filename or file modification date."""
    date_str = extract_date_from_filename(file_path.name)
    if date_str:
        return date_str

    mtime = file_path.stat().st_mtime
    date_obj = datetime.fromtimestamp(mtime)
    return date_obj.strftime('%Y%m%d')


def get_target_directory(base_path: Path, date_str: str) -> Path:
    """Create and return the YYYY/MM directory path."""
    year = date_str[:4]
    month = date_str[4:6]
    target_dir = base_path / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def rename_with_date(file_path: Path, date_str: str) -> str:
    """Generate a new filename with date prepended in YYYYMMDD format."""
    name = file_path.stem
    ext = file_path.suffix
    return f"{date_str}_{name}{ext}"


def process_directory(directory: str, rename_files: bool = False, dry_run: bool = False, recursive: bool = False) -> None:
    """Process images in directory, organizing by date hierarchy."""
    base_path = Path(directory).resolve()

    if not base_path.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return

    if recursive:
        image_files = [f for f in base_path.rglob('*')
                       if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        image_files = [f for f in base_path.iterdir()
                       if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

    if not image_files:
        print(f"No image files found in {directory}")
        return

    print(f"Found {len(image_files)} image(s) to process")

    for file_path in image_files:
        source_relative = file_path.relative_to(base_path)
        date_str = get_date_string(file_path)
        target_dir = get_target_directory(base_path, date_str)

        new_filename = rename_with_date(file_path, date_str) if rename_files else file_path.name
        target_path = target_dir / new_filename

        if dry_run:
            display_path = target_dir.relative_to(base_path) / new_filename
            print(f"[DRY RUN] {source_relative} -> {display_path}")
        else:
            shutil.move(str(file_path), str(target_path))
            display_path = target_dir.relative_to(base_path) / new_filename
            print(f"Moved {source_relative} to {display_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Organize images into YYYY/MM directory hierarchy by date'
    )
    parser.add_argument(
        'directory',
        help='Directory containing images to organize'
    )
    parser.add_argument(
        '-r', '--rename',
        action='store_true',
        help='Rename files to include date in format YYYYMMDD_originalname'
    )
    parser.add_argument(
        '-R', '--recursive',
        action='store_true',
        help='Recursively process all subdirectories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()
    process_directory(args.directory, rename_files=args.rename, dry_run=args.dry_run, recursive=args.recursive)


if __name__ == '__main__':
    main()
