import os

APP_NAME = "auto-patch-pr-agent"
MODEL_NAME = "gemini-2.0-flash"
TEMP_REPOS_DIR = "./temp_repos"

def get_google_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    return key
