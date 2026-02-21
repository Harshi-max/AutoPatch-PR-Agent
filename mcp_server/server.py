# mcp_server/server.py
from typing import Dict, Any

from . import repo_tool, lint_tool, git_tool, github_tool

def list_tools() -> Dict[str, Any]:
    """
    Simple registry you can adapt to real MCP config.
    """
    return {
        "repo.list_files": repo_tool.list_files,
        "repo.read_file": repo_tool.read_file,
        "repo.write_file": repo_tool.write_file,
        "lint.run_ruff": lint_tool.run_ruff,
        "git.clone": git_tool.clone_repository,
        "git.create_and_push_branch": git_tool.create_and_push_branch,
        "github.open_pr": github_tool.open_pr,
    }
