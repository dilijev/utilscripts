#!/usr/bin/env python3

# Sniff the actual mime types of all image/video formats like:
# jpg/jpeg, png, video, mp4, gif, webm, webp
# - use magic bytes with offset encoded into a static const array mapping
# - map those types to acceptable (typical) file extensions in a static mapping
# - identify which extensions don't match the actual file type

# Options:
# - add an argparse flag to rename all the files that have incorrect extensions
# (and tell the user about the flag in the output when incorrect matches are noticed)
# and exit 1
# - by default list only incorrect files
# - add an argparse flag to list all
# - otherwise print that nothing was incorrect and exit 0

import argparse
import os
import sys
from pathlib import Path
from typing import Tuple, Optional

# Magic bytes for file type detection: (bytes_to_check, offset, type_name)
MAGIC_BYTES = [
    (b'\xff\xd8\xff', 0, 'jpeg'),                                 # ???
    (b'\x89PNG\r\n\x1a\n', 0, 'png'),                             # ?PNG???
    (b'GIF8', 0, 'gif'),                                          # GIF8
    (b'WEBP', 8, 'webp'),                                         # WEBP
    (b'\x1a\x45\xdf\xa3', 0, 'webm'),                             # ????
    (b'\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d', 0, 'mp4'),  # ???  ftypisom
    (b'\x00\x00\x00\x20\x66\x74\x79\x70\x6d\x70\x34\x32', 0, 'mp4'),  # ???  ftypmp42
    (b'\x00\x00\x00\x18\x66\x74\x79\x70\x6d\x70\x34\x32', 0, 'mp4'),  # ???? ftypmp42
]

# Map detected type to acceptable extensions
TYPE_TO_EXTENSIONS = {
    'jpeg': {'.jpg', '.jpeg'},
    'png': {'.png'},
    'gif': {'.gif'},
    'webp': {'.webp'},
    'webm': {'.webm'},
    'mp4': {'.mp4', '.mpeg', '.mpg'},
}


def detect_file_type(filepath: Path) -> Optional[str]:
    """Detect file type by reading magic bytes."""
    try:
        with open(filepath, 'rb') as f:
            for magic, offset, type_name in MAGIC_BYTES:
                f.seek(offset)
                header = f.read(len(magic))
                if header == magic:
                    return type_name
    except (IOError, OSError):
        pass
    return None


def is_extension_match(detected_type: str, file_extension: str) -> bool:
    """Check if file extension matches detected type."""
    if detected_type not in TYPE_TO_EXTENSIONS:
        return True
    return file_extension.lower() in TYPE_TO_EXTENSIONS[detected_type]


def main():
    parser = argparse.ArgumentParser(
        description='Sniff image/video file types and check for extension mismatches'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='List all files with detected types'
    )
    parser.add_argument(
        '--rename',
        action='store_true',
        help='Rename files with incorrect extensions and exit with code 1'
    )

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    incorrect_files = []
    all_files = []

    # Scan directory for image/video files
    image_extensions = {ext for exts in TYPE_TO_EXTENSIONS.values() for ext in exts}

    for filepath in sorted(directory.rglob('*')):
        if not filepath.is_file():
            continue

        if filepath.suffix.lower() not in image_extensions:
            continue

        detected_type = detect_file_type(filepath)
        if detected_type is None:
            continue

        is_match = is_extension_match(detected_type, filepath.suffix)
        all_files.append((filepath, detected_type, is_match))

        if not is_match:
            incorrect_files.append((filepath, detected_type))

    # Handle renaming
    if args.rename and incorrect_files:
        for filepath, detected_type in incorrect_files:
            correct_ext = next(iter(TYPE_TO_EXTENSIONS[detected_type]))
            new_name = filepath.stem + correct_ext
            new_path = filepath.parent / new_name

            filepath.rename(new_path)
            print(f"Renamed: {filepath.name} → {new_name}")

        sys.exit(1)

    # Display results
    if args.all and all_files:
        for filepath, detected_type, is_match in all_files:
            status = "✓" if is_match else "✗"
            print(f"{status} {filepath} [{detected_type}]")
    elif incorrect_files:
        for filepath, detected_type in incorrect_files:
            correct_ext = next(iter(TYPE_TO_EXTENSIONS[detected_type]))
            print(f"{filepath}: detected {detected_type}, expected {correct_ext}")
        print(f"\nFound {len(incorrect_files)} file(s) with incorrect extension(s)")
        print("Use --rename flag to fix these files")
        sys.exit(1)
    else:
        print("All files have correct extensions")
        sys.exit(0)


if __name__ == '__main__':
    main()
