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

# Magic bytes for file type detection: type_name -> [(bytes_to_check, offset), ...]
MAGIC_BYTES = {
    'jpeg': [
        (b'\xff\xd8\xff', 0),                                       # ???
    ],
    'png': [
        (b'\x89PNG\r\n\x1a\n', 0),                                  # ?PNG???
    ],
    'gif': [
        (b'GIF8', 0),                                               # GIF8
    ],
    'webp': [
        (b'WEBP', 8),                                               # WEBP
    ],
    'webm': [
        (b'\x1a\x45\xdf\xa3', 0),                                   # ????
    ],
    'mp4': [
        (b'\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d', 0),   # ??? ftypisom
        (b'\x00\x00\x00\x20\x66\x74\x79\x70\x6d\x70\x34\x32', 0),   # ??? ftypmp42
        (b'\x00\x00\x00\x18\x66\x74\x79\x70\x6d\x70\x34\x32', 0),   # ???? ftypmp42
        (b'\x00\x00\x00\x28\x66\x74\x79\x70\x6d\x70\x34\x31', 0),   # ???? ftypmp41
    ],
    'm4a': [
        (b'\x00\x00\x00\x20\x66\x74\x79\x70\x4d\x34\x41\x20', 0),   # ??? ftypM4A
        (b'\x00\x00\x00\x18\x66\x74\x79\x70\x4d\x34\x41\x20', 0),   # ???? ftypM4A
    ],
    'mov': [
        (b'\x00\x00\x00\x20\x66\x74\x79\x70\x71\x74\x20\x20', 0),   # ??? ftypqt
        (b'\x00\x00\x00\x18\x66\x74\x79\x70\x71\x74\x20\x20', 0),   # ???? ftypqt
    ],
}

# Map detected type to acceptable extensions
TYPE_TO_EXTENSIONS = {
    'jpeg': {'.jpg', '.jpeg', '.jfif'},
    'png': {'.png'},
    'gif': {'.gif'},
    'webp': {'.webp'},
    'webm': {'.webm'},
    'mp4': {'.mp4', '.mpeg', '.mpg', '.m4v'},
    'm4a': {'.m4a', '.m4b', '.m4p'},
    'mov': {'.mov'},
}


def bytes_to_ascii(data: bytes) -> str:
    """Convert bytes to ASCII representation, using ? for non-printable."""
    return ''.join(chr(b) if 32 <= b < 127 else '?' for b in data)


def bytes_to_xxd(data: bytes) -> str:
    """Convert bytes to xxd format (hex pairs with space separation)."""
    hex_str = ' '.join(f'{b:02x}' for b in data)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
    return f"{hex_str}  {ascii_str}"


def detect_file_type(filepath: Path) -> Tuple[str, str, str]:
    """Detect file type by reading magic bytes. Returns (type, magic_ascii, magic_xxd)."""
    try:
        with open(filepath, 'rb') as f:
            for file_type, patterns in MAGIC_BYTES.items():
                for magic, offset in patterns:
                    f.seek(offset)
                    header = f.read(len(magic))
                    if header == magic:
                        return (file_type, bytes_to_ascii(magic), bytes_to_xxd(magic))
    except (IOError, OSError):
        pass
    return ('unknown', '[unknown]', '')


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
    parser.add_argument(
        '-r', '--recurse',
        action='store_true',
        help='Recursively scan subdirectories'
    )
    parser.add_argument(
        '-b', '--bytes',
        action='store_true',
        help='Show magic bytes in xxd format'
    )
    parser.add_argument(
        '--deep',
        action='store_true',
        help='Scan all files (including those with unknown extensions) for magic bytes'
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
    glob_fn = directory.rglob if args.recurse else directory.glob

    for filepath in sorted(glob_fn('*')):
        if not filepath.is_file():
            continue

        if not args.deep and filepath.suffix.lower() not in image_extensions:
            continue

        detected_type, magic_ascii, magic_xxd = detect_file_type(filepath)
        is_match = is_extension_match(detected_type, filepath.suffix)
        all_files.append((filepath, detected_type, magic_ascii, magic_xxd, is_match))

        if not is_match and detected_type != 'unknown':
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
        if args.bytes:
            # Calculate column widths with magic bytes
            type_width = max(len(t) for _, t, _, _, _ in all_files) if all_files else 8
            ext_width = max(len(f.suffix) for f, _, _, _, _ in all_files) if all_files else 10

            # Calculate xxd column width by formatting each entry and finding max
            formatted_xxds = []
            max_hex_width = 0
            for _, _, _, xxd, _ in all_files:
                if '  ' in xxd:
                    hex_part, ascii_part = xxd.split('  ', 1)
                    max_hex_width = max(max_hex_width, len(hex_part))
                    formatted_xxds.append((hex_part, ascii_part))
                else:
                    formatted_xxds.append((xxd, ''))

            xxd_width = max_hex_width + 2 + max(len(a) for _, a in formatted_xxds) if formatted_xxds else 10
            type_width = max(type_width, len("Type"))
            ext_width = max(ext_width, len("Extension"))

            # Print header with proper alignment
            hex_part_header = "Hex".ljust(max_hex_width)
            ascii_part_header = "ASCII"
            xxd_header = f"{hex_part_header}  {ascii_part_header}".ljust(xxd_width)
            print(f"{'Type':<{type_width}}  {'Extension':<{ext_width}}  {xxd_header}  Filename")
            print("-" * (type_width + ext_width + xxd_width + 35))

            # Print rows
            for filepath, detected_type, magic_ascii, magic_xxd, is_match in all_files:
                status = "✓" if is_match else "✗"
                ext = filepath.suffix or "(no ext)"
                # Format xxd with proper padding
                if '  ' in magic_xxd:
                    hex_part, ascii_part = magic_xxd.split('  ', 1)
                    padded_xxd = f"{hex_part:<{max_hex_width}}  {ascii_part}".ljust(xxd_width)
                else:
                    padded_xxd = magic_xxd.ljust(xxd_width)
                print(f"{detected_type:<{type_width}}  {ext:<{ext_width}}  {padded_xxd}  {status} {filepath}")
        else:
            # Simple format without magic bytes
            type_width = max(len(t) for _, t, _, _, _ in all_files) if all_files else 8
            ext_width = max(len(f.suffix) for f, _, _, _, _ in all_files) if all_files else 10
            type_width = max(type_width, len("Type"))
            ext_width = max(ext_width, len("Extension"))

            print(f"{'Type':<{type_width}}  {'Extension':<{ext_width}}  Filename")
            print("-" * (type_width + ext_width + 40))

            for filepath, detected_type, _, _, is_match in all_files:
                status = "✓" if is_match else "✗"
                ext = filepath.suffix or "(no ext)"
                print(f"{detected_type:<{type_width}}  {ext:<{ext_width}}  {status} {filepath}")

        if not incorrect_files:
            print("\nAll files have correct extensions")
        else:
            print(f"\nFound {len(incorrect_files)} file(s) with incorrect extension(s)")
            print("Use --rename flag to fix these files")
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
