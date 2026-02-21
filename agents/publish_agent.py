import requests
from core.git_utils import create_branch_and_push
from typing import Optional
try:
    from core.agent_runtime import run_agent
except Exception:
    run_agent = None


async def generate_pr_review_comment(
    runner,
    session_id: str,
    pr_url: str,
    repo_url: Optional[str],
    gh_token: str,
    max_files: int = 8,
) -> str:
    """Generate an AI-based PR review comment using the provided `runner`.

    Falls back to a heuristic summary if no runner is available.
    """
    # Simple helper to fetch PR files
    try:
        parts = pr_url.rstrip("/").split("/")
        pr_number = parts[-1]
        owner_repo = "/".join(parts[-4:-2])
    except Exception:
        return "Automated review: could not parse PR URL to generate review."

    api_url = f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}/files"
    headers = {"Accept": "application/vnd.github+json"}
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return f"Automated review: failed to fetch PR files (status {resp.status_code})."
        files = resp.json()
    except Exception:
        return "Automated review: failed to fetch PR files."

    # Build a concise summary of changed files and small diffs
    summary_lines = []
    for f in files[:max_files]:
        filename = f.get("filename")
        changes = f.get("changes")
        additions = f.get("additions")
        deletions = f.get("deletions")
        patch = f.get("patch") or ""
        snippet = "".join(patch.splitlines()[:6])
        summary_lines.append(f"- {filename}: +{additions} / -{deletions} (changes: {changes})\n{snippet}\n")

    prompt = (
        "You are an expert code reviewer. Given the list of changed files and small diffs, "
        "produce a clear, concise review comment that: (1) summarizes the main changes, "
        "(2) points out potential bugs or risky changes, (3) gives improvement suggestions, "
        "and (4) provides a short acceptance checklist. Be professional and constructive.\n\n"
        "Changed files and diffs:\n" + "\n".join(summary_lines)
    )

    # Use runner if available
    if runner is not None and run_agent is not None:
        try:
            res = await run_agent(runner, session_id, prompt)
            if res and res.strip():
                return res
        except Exception:
            pass

    # Fallback heuristic comment
    comment = "Automated review by Patcher:\n\n"
    comment += "Summary of changed files:\n"
    comment += "\n".join([l.splitlines()[0] for l in summary_lines])
    comment += "\n\nNotes: Please review the diffs above; consider unit tests and edge cases."
    return comment

def create_pull_request(repo_url: str, new_branch: str, base_branch: str, gh_token: str, title: str, body: str) -> str:
    # repo_url: https://github.com/owner/repo.git
    clean = repo_url.rstrip("/").replace(".git", "")
    owner_repo = clean.split("github.com/")[-1]
    api_url = f"https://api.github.com/repos/{owner_repo}/pulls"

    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": title,
        "head": new_branch,
        "base": base_branch,
        "body": body,
    }
    # First, check if a PR already exists for this head branch to avoid duplicates
    try:
        list_resp = requests.get(api_url, headers=headers, params={"head": f"{owner_repo.split('/')[0]}:{new_branch}", "state": "all"})
        if list_resp.status_code == 200:
            prs = list_resp.json()
            if prs:
                # Return the first matching PR URL
                pr = prs[0]
                print(f"[Publisher] Found existing PR: {pr.get('html_url')}")
                return pr.get("html_url", "")
    except Exception:
        # ignore list errors and proceed to create
        pass

    resp = requests.post(api_url, headers=headers, json=payload)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # If GitHub returns 422 Unprocessable Entity, try to find an existing PR and return it
        if resp.status_code == 422:
            try:
                list_resp = requests.get(api_url, headers=headers, params={"head": f"{owner_repo.split('/')[0]}:{new_branch}", "state": "all"})
                if list_resp.status_code == 200:
                    prs = list_resp.json()
                    if prs:
                        pr = prs[0]
                        print(f"[Publisher] Existing PR found after 422: {pr.get('html_url')}")
                        return pr.get("html_url", "")
            except Exception:
                pass
        raise

    pr = resp.json()
    return pr.get("html_url", "")


def create_issue(repo_url: str, title: str, body: str, gh_token: str) -> str:
    clean = repo_url.rstrip("/").replace(".git", "")
    owner_repo = clean.split("github.com/")[-1]
    api_url = f"https://api.github.com/repos/{owner_repo}/issues"

    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "body": body}
    resp = requests.post(api_url, headers=headers, json=payload)
    resp.raise_for_status()
    issue = resp.json()
    return issue.get("html_url", "")


def post_pr_comment(pr_url: str, comment: str, gh_token: str) -> str:
    # pr_url: https://github.com/owner/repo/pull/123
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid PR URL")
    pr_number = parts[-1]
    owner_repo = "/".join(parts[-4:-2])
    api_url = f"https://api.github.com/repos/{owner_repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"}
    payload = {"body": comment}
    
    print(f"[Patcher Review] Posting comment to {owner_repo}#{pr_number}...")
    
    try:
        resp = requests.post(api_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        print(f"[Patcher Review] ✅ Comment posted successfully")
        return data.get("html_url", "")
    except requests.exceptions.HTTPError as e:
        error_status = e.response.status_code
        if error_status == 403:
            raise PermissionError(
                f"403 Forbidden: Your token doesn't have write access to this repository. "
                f"You need a token with 'issues:write' and 'pull_requests:write' scope from the repo owner or a user with push access."
            )
        elif error_status == 404:
            raise ValueError(f"404 Not Found: PR #{pr_number} not found in {owner_repo}")
        elif error_status == 401:
            raise PermissionError("401 Unauthorized: Invalid or expired GitHub token")
        else:
            raise Exception(f"GitHub API error {error_status}: {e.response.text}")
