# mcp_server/git_tool.py
from typing import Optional
from core.git_utils import clone_repo, create_branch_and_push

def clone_repository(repo_url: str, dest_dir: str, branch: Optional[str] = None) -> str:
    """
    Clone the repository into dest_dir and optionally checkout branch.
    Returns the local path.
    """
    return clone_repo(repo_url, dest_dir, branch)

def create_and_push_branch(repo_path: str, new_branch: str, token: Optional[str] = None) -> str:
    """
    Create a new branch, commit existing staged changes, and push.
    Returns the created branch name.
    """
    return create_branch_and_push(repo_path, new_branch, token)
