# mcp_server/lint_tool.py
import json
import subprocess
from typing import List, Dict, Any

def run_ruff(root: str) -> List[Dict[str, Any]]:
    """
    Run ruff on the repo and return issues as a list of dicts.
    """
    try:
        result = subprocess.run(
            ["ruff", "check", root, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            return []
        return json.loads(result.stdout)
    except Exception as e:
        print("ruff error:", e)
        return []
