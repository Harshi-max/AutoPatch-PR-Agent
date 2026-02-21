import requests
from core.git_utils import create_branch_and_push

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
