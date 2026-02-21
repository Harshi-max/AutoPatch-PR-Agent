import os
import json
try:
    from google.genai import types
    from google.genai.agents import Runner, InMemorySessionService
except Exception:
    import importlib.util
    # Load local stub from project `google/genai` to allow running without external SDK
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    types_path = os.path.join(base, "google", "genai", "types.py")
    agents_path = os.path.join(base, "google", "genai", "agents.py")

    spec = importlib.util.spec_from_file_location("google.genai.types", types_path)
    types = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(types)

    spec2 = importlib.util.spec_from_file_location("google.genai.agents", agents_path)
    agents_mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(agents_mod)
    Runner = agents_mod.Runner
    InMemorySessionService = agents_mod.InMemorySessionService

from .config import MODEL_NAME, APP_NAME

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

async def run_agent(runner: Runner, session_id: str, prompt: str) -> str:
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_text = ""
    async for event in runner.stream_input_content(session_id=session_id, content=content):
        if event.type == "response.delta":
            for part in event.delta.parts:
                if part.text:
                    final_text += part.text
    return final_text

def build_session_service() -> InMemorySessionService:
    return InMemorySessionService()
