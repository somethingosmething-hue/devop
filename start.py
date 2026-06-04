#!/usr/bin/env python3
"""Bootstrap script: clones the repo if missing, then runs main.py."""
import subprocess
import sys
import os

REPO_URL = "https://github.com/somethingosmething-hue/devop"

if not os.path.isdir(".git"):
    print("[START] .git not found — cloning repository...")
    result = subprocess.run(
        ["git", "clone", REPO_URL, "."],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[START] Clone failed:\n{result.stderr}")
        sys.exit(1)
    print("[START] Clone complete.")

print("[START] Starting main.py...")
os.execv(sys.executable, [sys.executable, "main.py"])
