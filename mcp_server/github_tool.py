# mcp_server/github_tool.py
from core.git_utils import create_branch_and_push
from agents.publish_agent import create_pull_request

def open_pr(
    repo_url: str,
    repo_path: str,
    new_branch: str,
    base_branch: str,
    gh_token: str,
    title: str,
    body: str,
) -> str:
    """
    Create a branch (if not already), push it and open a PR.
    Returns the PR URL.
    """
    created_branch = create_branch_and_push(repo_path, new_branch, gh_token)
    pr_url = create_pull_request(
        repo_url=repo_url,
        new_branch=created_branch,
        base_branch=base_branch,
        gh_token=gh_token,
        title=title,
        body=body,
    )
    return pr_url
