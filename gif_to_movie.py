#!/usr/bin/env python3

"""
gif2media.py - convert all GIFs in the cwd to WebM or MP4 with ffmpeg.

Usage:
    python gif2media.py --format webm   # produces *.gif.webm
    python gif2media.py --format mp4    # produces *.gif.mp4

The script keeps the same target video bitrate (1100 k) you used in the
batch files and archives the source GIFs under an "old" sub‑directory.
"""

import argparse
import shutil
import subprocess
from pathlib import Path
import sys

# ---------------------------------------------------------------------------

def run_ffmpeg(input_path: Path, output_path: Path, fmt: str) -> None:
    """Build the ffmpeg command line for the chosen format and execute it."""
    # Common options
    cmd = [
        "ffmpeg",
        "-y",                     # overwrite output if it exists
        "-i", str(input_path),
    ]

    if fmt == "webm":
        cmd += [
            "-acodec", "libvorbis",
            "-ac", "1",
            "-ab", "96k",
            "-ar", "48000",
            "-c:v", "libvpx-vp9",
            "-b:v", "1100k",
            "-maxrate", "1100k",
            "-bufsize", "1835k",
            str(output_path),
        ]
    elif fmt == "mp4":
        cmd += [
            "-c:v", "libx264",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-b:v", "1100k",
            "-maxrate", "1100k",
            "-bufsize", "1835k",
            str(output_path),
        ]
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    # Run ffmpeg, forwarding stdout/stderr so the user sees progress / errors
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed for {input_path.name}: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch convert GIF → WebM/MP4")
    parser.add_argument(
        "--format",
        choices=["webm", "mp4"],
        required=True,
        help="Target container/codec (webm or mp4)",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    gif_files = list(cwd.glob("*.gif"))

    if not gif_files:
        print("No GIF files found in the current directory.")
        return

    # Ensure the archive folder exists
    old_dir = cwd / "old"
    old_dir.mkdir(exist_ok=True)

    for gif in gif_files:
        if args.format == "webm":
            out_path = gif.with_name(gif.name + ".webm")
        else:  # mp4
            out_path = gif.with_name(gif.stem + ".mp4")

        print(f"Converting {gif.name} → {out_path.name} ...")
        run_ffmpeg(gif, out_path, args.format)

        # Move the original GIF to the archive folder
        dest = old_dir / gif.name
        print(f"Archiving original GIF to {dest}")
        shutil.move(str(gif), str(dest))

    print("All done.")


if __name__ == "__main__":
    main()
