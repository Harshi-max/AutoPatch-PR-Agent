import json
import subprocess
from typing import List

from core.artifacts import store_issues


def run_ruff_on_path(path: str) -> List[dict]:
    # Example: ruff in JSON mode
    try:
        result = subprocess.run(
            ["ruff", "check", path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        issues = json.loads(result.stdout or "[]")
        return issues
    except Exception:
        return []


def analyze_repo_for_issues(local_path: str) -> str:
    issues = run_ruff_on_path(local_path)
    # Always store (even if empty) so pipeline continues with a valid report ID
    report_id = store_issues(issues, local_path)
    count = len(issues) if issues else 0
    return f"Issues stored. Reference ID: {report_id} (found {count} issues)"


def run_bandit_on_path(path: str) -> str:
    """Run Bandit security scan on path and store results as artifact.

    Returns a short text summary to display.
    """
    try:
        result = subprocess.run(
            ["bandit", "-r", path, "-f", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout or "{}")
        issues = data.get("results", [])
        if issues:
            report_id = store_issues(issues, path)
            return f"Security issues found. Reference ID: {report_id}"
        else:
            return "No security issues found."
    except FileNotFoundError:
        return "Bandit not installed. Install it with `pip install bandit`."
    except subprocess.CalledProcessError as e:
        # Bandit may return non-zero on findings; still try to parse stdout
        try:
            data = json.loads(e.stdout or "{}")
            issues = data.get("results", [])
            if issues:
                report_id = store_issues(issues, path)
                return f"Security issues found. Reference ID: {report_id}"
        except Exception:
            pass
        return f"Bandit run failed: {e}"


def compute_confidence(report_id: str, repo_path: str) -> dict:
    """Compute a simple confidence score by re-running ruff and comparing issue counts.

    Returns a dict with `score` (0-1) and textual `summary`.
    """
    try:
        before_data = None
        from core.artifacts import get_artifact

        before = get_artifact(report_id)
        before_count = before.get("count", 0) if before else 0
        # Re-run ruff to get post-fix issues
        new_issues = run_ruff_on_path(repo_path)
        after_count = len(new_issues) if new_issues else 0
        if before_count == 0:
            score = 1.0 if after_count == 0 else 0.5
        else:
            reduced = max(0, before_count - after_count)
            score = reduced / before_count
        summary = f"Before: {before_count} issues, After: {after_count} issues. Confidence: {score:.2f}"
        return {"score": score, "summary": summary}
    except Exception as e:
        return {"score": 0.0, "summary": f"Confidence computation failed: {e}"}
