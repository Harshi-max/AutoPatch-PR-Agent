import uuid
import json
from typing import Dict, Any, List

ARTIFACT_STORE: Dict[str, Dict[str, Any]] = {}
MEMORY_BANK: Dict[str, Any] = {}

def store_issues(issues: List[dict], repo_path: str) -> str:
    """Store issues in artifact store. Always returns a valid report_id, even for empty lists."""
    report_id = str(uuid.uuid4())
    ARTIFACT_STORE[report_id] = {
        "issues": issues if issues else [],
        "count": len(issues) if issues else 0,
        "repo_path": repo_path,
    }
    MEMORY_BANK["last_issues"] = issues if issues else []
    return report_id

def fetch_issue_batch(report_id: str, batch_size: int = 3) -> str:
    data = ARTIFACT_STORE.get(report_id)
    if not data:
        return "Error: Report ID not found."
    batch = data.get("issues", [])[:batch_size]
    return json.dumps(batch) if batch else "No more issues to fix."

def get_artifact(report_id: str) -> dict | None:
    return ARTIFACT_STORE.get(report_id)
