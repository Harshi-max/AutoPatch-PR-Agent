#!/usr/bin/env python
"""Quick syntax and import check for modified modules."""
import sys
print("[*] Testing imports...")

try:
    from agents.publish_agent import generate_pr_review_comment, post_pr_comment
    print("✅ agents.publish_agent: generate_pr_review_comment, post_pr_comment imported")
except Exception as e:
    print(f"❌ agents.publish_agent: {e}")
    sys.exit(1)

try:
    from agents.orchestrator import run_pipeline
    print("✅ agents.orchestrator: run_pipeline imported")
except Exception as e:
    print(f"❌ agents.orchestrator: {e}")
    sys.exit(1)

try:
    from core.git_utils import clone_repo, create_branch_and_push
    print("✅ core.git_utils: clone_repo, create_branch_and_push imported")
except Exception as e:
    print(f"❌ core.git_utils: {e}")
    sys.exit(1)

print("\n[✓] All imports successful!")
