#!/usr/bin/env python3
"""Paste YouTube links one at a time, each one runs the script."""

import subprocess
import sys

print("Paste a YouTube URL and press Enter. Ctrl+C to quit.\n")

while True:
    try:
        url = input("> ").strip()
        if not url:
            continue
        subprocess.run([sys.executable, "remove_bg_music.py", url])
        print()
    except KeyboardInterrupt:
        print("\nBye.")
        break