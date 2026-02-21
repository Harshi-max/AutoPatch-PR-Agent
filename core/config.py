import os
import tempfile

APP_NAME = "auto-patch-pr-agent"
MODEL_NAME = "gemini-2.0-flash"

# Use system temp directory for better compatibility with Streamlit Cloud
# Falls back to ./temp_repos if in local development
if os.path.exists("/tmp"):
    # Linux/macOS or Streamlit Cloud
    TEMP_REPOS_DIR = "/tmp/autopatch-repos"
elif os.path.exists(tempfile.gettempdir()):
    # Windows or any system
    TEMP_REPOS_DIR = os.path.join(tempfile.gettempdir(), "autopatch-repos")
else:
    # Fallback to local directory
    TEMP_REPOS_DIR = "./temp_repos"

def get_google_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    return key
