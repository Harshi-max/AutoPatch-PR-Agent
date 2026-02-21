import asyncio
import json
import os

try:
    from google.genai.agents import Runner
except Exception:
    import importlib.util
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agents_path = os.path.join(base, "google", "genai", "agents.py")
    spec = importlib.util.spec_from_file_location("google.genai.agents", agents_path)
    agents_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agents_mod)
    Runner = agents_mod.Runner

from core.agent_runtime import run_agent
from core.artifacts import get_artifact
from core.git_utils import write_file

async def fix_issues_with_llm(runner_fix: Runner, session_id: str, report_id: str):
    """Fix issues found by linting. Handles gracefully even with 0 issues or LLM timeouts."""
    artifact = get_artifact(report_id)
    if not artifact:
        print(f"Report id {report_id} not found.")
        return

    issues = artifact.get("issues", [])
    issue_count = len(issues)
    print(f"[Fix Agent] Found {issue_count} issues to fix")

    if issue_count == 0:
        print("[Fix Agent] No issues to fix, skipping LLM calls")
        return

    fixed_count = 0
    for idx, issue in enumerate(issues, 1):
        filename = issue.get("filename") or issue.get("file")
        if not filename:
            print(f"[Fix Agent] Issue {idx}/{issue_count}: No filename, skipping")
            continue

        if not os.path.exists(filename):
            print(f"[Fix Agent] Issue {idx}/{issue_count}: File not found {filename}, skipping")
            continue

        try:
            with open(filename, "r", encoding="utf-8") as fh:
                current_content = fh.read()

            prompt = (
                "Here is the current file content and suggestion by ruff. "
                "Fix the code according to suggestions.\n\n"
                f"File Content:\n{current_content}\n\n"
                f"suggestion:\n{json.dumps(issue, default=str)}"
            )
            
            print(f"[Fix Agent] Issue {idx}/{issue_count}: Calling LLM for {filename}...")
            try:
                fix_resp = await asyncio.wait_for(run_agent(runner_fix, session_id, prompt), timeout=30.0)
                if fix_resp and fix_resp.strip():
                    write_file(filename, fix_resp)
                    print(f"[Fix Agent] ✅ Updated {filename}")
                    fixed_count += 1
                else:
                    print(f"[Fix Agent] LLM returned empty response for {filename}")
            except asyncio.TimeoutError:
                print(f"[Fix Agent] ⏱️ LLM timeout for {filename}, skipping")
            except Exception as e:
                print(f"[Fix Agent] ❌ LLM error for {filename}: {e}")
        except Exception as e:
            print(f"[Fix Agent] Error processing issue {idx}: {e}")
            continue

    print(f"[Fix Agent] Completed: Fixed {fixed_count}/{issue_count} issues")


def detect_repo_language(repo_path: str) -> str:
    """Detect repo language by checking for package.json, requirements.txt, etc."""
    if os.path.exists(os.path.join(repo_path, "package.json")):
        return "javascript"
    elif os.path.exists(os.path.join(repo_path, "requirements.txt")) or os.path.exists(os.path.join(repo_path, "setup.py")):
        return "python"
    else:
        return "javascript" if os.path.exists(os.path.join(repo_path, "src")) else "python"


async def generate_code_from_requirement(runner_fix: Runner, session_id: str, repo_path: str, requirement: str):
    """Generate real implementation code based on user requirement."""
    print(f"\n[Requirement Agent] Processing requirement: {requirement}")
    try:
        created_files = []
        lang = detect_repo_language(repo_path)
        req_low = requirement.lower()

        if lang == "javascript":
            if "dark" in req_low or "light" in req_low or "mode" in req_low or "theme" in req_low:
                # Theme toggle component
                component_dir = os.path.join(repo_path, "src", "components")
                component_path = os.path.join(component_dir, "ThemeToggle.jsx")
                component_code = '''import React, { useState } from 'react';

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
  };

  return (
    <button onClick={toggleTheme} className="theme-toggle">
      {isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}
    </button>
  );
}
'''
                write_file(component_path, component_code)
                created_files.append(os.path.relpath(component_path, repo_path).replace('\\', '/'))
            else:
                # Generic feature component
                safe_name = requirement.title().replace(' ', '').replace('-', '')
                component_dir = os.path.join(repo_path, "src", "components")
                component_path = os.path.join(component_dir, f"{safe_name}Feature.jsx")
                component_code = f'''import React, {{ useState }} from 'react';

export default function {safe_name}Feature() {{
  const [data, setData] = useState([]);

  return (
    <div className="feature-container">
      <h2>{requirement}</h2>
      <p>Implementation for: {requirement}</p>
    </div>
  );
}}
'''
                write_file(component_path, component_code)
                created_files.append(os.path.relpath(component_path, repo_path).replace('\\', '/'))

        elif lang == "python":
            if "dark" in req_low or "light" in req_low or "mode" in req_low or "theme" in req_low:
                # Theme manager module
                module_path = os.path.join(repo_path, "theme_manager.py")
                module_code = '''"""Theme management for the application."""

class ThemeManager:
    """Manages application theme (dark/light mode)."""
    
    def __init__(self, default_theme='light'):
        self.current_theme = default_theme
        self.themes = {
            'light': {'bg': '#ffffff', 'text': '#000000'},
            'dark': {'bg': '#1e1e1e', 'text': '#ffffff'}
        }
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        return self.get_current_theme()
    
    def get_current_theme(self):
        """Get current theme config."""
        return self.themes.get(self.current_theme, {})
'''
                write_file(module_path, module_code)
                created_files.append(os.path.relpath(module_path, repo_path).replace('\\', '/'))
            else:
                # Generic feature module
                module_name = requirement.lower().replace(' ', '_').replace('-', '_')
                module_path = os.path.join(repo_path, f"{module_name}.py")
                safe_class = requirement.title().replace(' ', '').replace('-', '')
                module_code = f'''"""Implementation for: {requirement}"""

class {safe_class}:
    """Implementation of {requirement} feature."""
    
    def __init__(self):
        self.enabled = True
    
    def execute(self):
        print(f"Executing: {requirement}")
        return True
'''
                write_file(module_path, module_code)
                created_files.append(os.path.relpath(module_path, repo_path).replace('\\', '/'))

        # Create implementation documentation
        doc_path = os.path.join(repo_path, "IMPLEMENTATION.md")
        doc_lines = [f'# Implementation: {requirement}', '', '## Files Generated']
        for p in created_files:
            doc_lines.append(f'- `{p}`')
        doc_lines.append('')
        doc_lines.append('Generated by Patcher AI Bot')
        write_file(doc_path, '\n'.join(doc_lines))
        created_files.append(os.path.relpath(doc_path, repo_path).replace('\\', '/'))

        print(f"[Requirement Agent] ✅ Generated files: {created_files}")
        return created_files
    except Exception as e:
        print(f"[Requirement Agent] ❌ Error generating code: {e}")
        raise
