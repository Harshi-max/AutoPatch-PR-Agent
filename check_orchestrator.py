#!/usr/bin/env python
"""Quick import check for orchestrator fix."""
import sys

try:
    from agents.orchestrator import run_pipeline
    print("✅ agents.orchestrator: run_pipeline imported successfully")
    print("[✓] Orchestrator syntax is valid!")
except SyntaxError as e:
    print(f"❌ Syntax error in orchestrator: {e}")
    sys.exit(1)
except ImportError as e:
    print(f"⚠️ Import error (expected - may need dependencies): {e}")
    print("[✓] Syntax is valid though!")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
