#!/usr/bin/env python
"""Verify fixes for Streamlit Cloud deployment."""
import sys

print("[*] Testing imports after Streamlit Cloud fixes...")

try:
    from core.config import TEMP_REPOS_DIR
    print(f"✅ core.config: TEMP_REPOS_DIR = {TEMP_REPOS_DIR}")
except Exception as e:
    print(f"❌ core.config: {e}")
    sys.exit(1)

try:
    from core.git_utils import clone_repo
    print("✅ core.git_utils: clone_repo imported")
except Exception as e:
    print(f"❌ core.git_utils: {e}")
    sys.exit(1)

try:
    from agents.orchestrator import run_pipeline
    print("✅ agents.orchestrator: run_pipeline imported")
except Exception as e:
    print(f"❌ agents.orchestrator: {e}")
    sys.exit(1)

print("\n[✓] All imports successful!")
print(f"[✓] Temp repos will be stored in: {TEMP_REPOS_DIR}")
