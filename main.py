import asyncio
import os
import sys
import warnings

# Suppress noisy Pydantic schema warning about the built-in `any` function
# which can appear when third-party packages or generated code accidentally
# use the built-in `any` as a type. This is harmless for runtime but noisy.
warnings.filterwarnings(
    "ignore",
    message=r".*<built-in function any> is not a Python type.*",
    category=UserWarning,
)

# Ensure project package dir is first on sys.path so local stubs (e.g. google.genai)
# are importable even if an installed `google` namespace package exists.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import run_pipeline

def main():
    repo_url = input("GitHub Repo URL: ").strip()
    gh_token = input("GitHub Token: ").strip()
    base_branch = input("Base branch (default: main): ").strip() or "main"

    asyncio.run(run_pipeline(repo_url, gh_token, base_branch))

if __name__ == "__main__":
    main()
