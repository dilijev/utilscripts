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
