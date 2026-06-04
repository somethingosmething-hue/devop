#!/usr/bin/env python3
"""Bootstrap script: clones the repo if missing, then runs main.py."""
import subprocess
import sys
import os
import shutil

REPO_URL = "https://github.com/somethingosmething-hue/devop"
BRANCH = "main"
PROTECTED = ["config.toml"]

if not os.path.isdir(".git"):
    print("[START] Initializing git...")
    r = subprocess.run(["git", "init"], capture_output=True, text=True)
    if r.returncode != 0: print(f"[START] git init failed:\n{r.stderr}"); sys.exit(1)
    r = subprocess.run(["git", "remote", "add", "origin", REPO_URL], capture_output=True, text=True)
    if r.returncode != 0: print(f"[START] git remote add failed:\n{r.stderr}"); sys.exit(1)

backup = {}
for name in PROTECTED:
    if os.path.exists(name):
        bak = f"/tmp/{name}.bak"
        shutil.copy2(name, bak)
        backup[name] = bak

print("[START] Fetching repository...")
r = subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True)
if r.returncode != 0: print(f"[START] git fetch failed:\n{r.stderr}"); sys.exit(1)

print("[START] Checking out...")
r = subprocess.run(["git", "checkout", "-f", "-B", BRANCH, f"origin/{BRANCH}"], capture_output=True, text=True)
if r.returncode != 0: print(f"[START] git checkout failed:\n{r.stderr}"); sys.exit(1)

for name, bak in backup.items():
    shutil.copy2(bak, name)
    os.remove(bak)

print("[START] Repository ready.")
print("[START] Starting main.py...")
os.execv(sys.executable, [sys.executable, "main.py"])
