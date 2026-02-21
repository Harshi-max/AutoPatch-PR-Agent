# mcp_server/repo_tool.py
from pathlib import Path

def list_files(root: str) -> list[str]:
    root_path = Path(root)
    files = []
    for p in root_path.rglob("*"):
        if p.is_file():
            files.append(str(p.relative_to(root_path)))
    return files

def read_file(root: str, relative_path: str) -> str:
    path = Path(root) / relative_path
    return path.read_text(encoding="utf-8")

def write_file(root: str, relative_path: str, content: str) -> str:
    path = Path(root) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Updated {relative_path}"
