import re
try:
    from google.genai.agents import Runner
except Exception:
    import importlib.util, os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agents_path = os.path.join(base, "google", "genai", "agents.py")
    spec = importlib.util.spec_from_file_location("google.genai.agents", agents_path)
    agents_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agents_mod)
    Runner = agents_mod.Runner

from core.agent_runtime import build_session_service, run_agent, ensure_dir
from core.config import TEMP_REPOS_DIR
from core.git_utils import clone_repo, create_branch_and_push, MergeConflictError, write_file
from git import Repo
from urllib.parse import urlparse
from agents.analysis_agent import analyze_repo_for_issues, run_bandit_on_path, compute_confidence
from agents.fix_agent import fix_issues_with_llm, generate_code_from_requirement
from agents.publish_agent import create_pull_request, create_issue, post_pr_comment
from agents.semantic_agent import run_semantic_refactor
from core.artifacts import store_issues

async def run_pipeline(
    repo_url: str,
    gh_token: str,
    base_branch: str,
    progress_callback=None,
    *,
    security_lint: bool = False,
    pr_review_comments: bool = False,
    ci_integration: bool = False,
    confidence_scoring: bool = False,
    semantic_refactor: bool = False,
    auto_create_pr: bool = False,
    pr_requirement: str = None,
):
    """Run the full auto-patch pipeline.

    progress_callback: optional callable(stage: str, info: str|None) used to emit
    stage updates (e.g. "analyze:start", "analyze:done", "fix:start", etc.).
    
    pr_requirement: optional string describing what the PR should fix/improve.
                   If provided, Patcher will generate code based on this requirement
                   instead of running auto-linting.
    """
    def emit(stage: str, info: str | None = None):
        try:
            if progress_callback:
                progress_callback(stage, info)
        except Exception:
            pass

    ensure_dir(TEMP_REPOS_DIR)
    emit("clone:start")
    local_path = clone_repo(repo_url, TEMP_REPOS_DIR, base_branch or None)
    emit("clone:done", local_path)

    # Initialize runners (needed for both requirement-driven and analysis-driven modes)
    session_service = build_session_service()
    session_id = "session_main"
    runner_analyze = Runner(model="models/gemini-2.0-flash", app= "auto-patch-pr-agent", session_service=session_service)
    runner_fix = Runner(model="models/gemini-2.0-flash", app= "auto-patch-pr-agent", session_service=session_service)

    # Requirement analysis (if provided)
    if pr_requirement:
        emit("requirement:start", f"Processing requirement: {pr_requirement[:60]}...")
        print(f"\n[Requirements] User requirement: {pr_requirement}")
        # Create an artifact entry (empty issues) so downstream stages have a valid report id
        report_id = store_issues([], local_path)
        analysis_output = f"Requirement: {pr_requirement}\nReference ID: {report_id}"
        emit("requirement:done", pr_requirement)
    else:
        # Normal scan / lint
        emit("scan:start")
        emit("lint:start")

        # Analyze
        emit("analyze:start")
        print("\n[Analyzer]: Analyzing...")
        analysis_output = analyze_repo_for_issues(local_path)
        print("Analysis:", analysis_output)
        emit("analyze:done", analysis_output)
        emit("lint:done", analysis_output)
        emit("scan:done", local_path)
        report_id = None

    # Optional security linting
    # Security linting (Bandit)
    bandit_report_id = None
    if security_lint:
        emit("security:start", "Running Bandit security scan")
        try:
            bandit_report_id = run_bandit_on_path(local_path)
            emit("security:done", bandit_report_id)
        except Exception as e:
            emit("security:error", str(e))

    # Optional deeper semantic refactoring
    if semantic_refactor:
        emit("semantic:start")
        sem_out = run_semantic_refactor(local_path)
        emit("semantic:done", sem_out)

    # Optional patch confidence scoring (computed after fixes)
    # We'll compute later after fixes run

    match = re.search(r"([a-f0-9\-]{36})", analysis_output)
    if not match:
        print("No Reference ID returned.")
        return {"status": "failed", "reason": "no_analysis_report"}
    report_id = match.group(1)
    print(f"Artifact ID: {report_id}")

    # Fix / Generate code
    emit("generate:start", report_id)
    emit("fix:start", report_id)
    print("\n[Fixer]: Processing...")
    try:
        generated_files = None
        if pr_requirement:
            # Requirement-based code generation
            generated_files = await generate_code_from_requirement(runner_fix, session_id, local_path, pr_requirement)
        else:
            # Normal linting-based fixes
            await fix_issues_with_llm(runner_fix, session_id, report_id)
        emit("fix:done", report_id)
    except Exception as e:
        print(f"[Fixer] Error: {e}")
        emit("fix:error", str(e))
    emit("generate:done", report_id)
    emit("apply:done", report_id)

    # After fixes, optional confidence scoring
    confidence_result = None
    if confidence_scoring:
        emit("confidence:start")
        try:
            confidence_result = compute_confidence(report_id, local_path)
            emit("confidence:done", confidence_result)
        except Exception as e:
            emit("confidence:error", str(e))

    # Optional CI integration: generate simple GitHub Actions workflow
    if ci_integration:
        emit("ci:start")
        try:
            workflow = """name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install ruff
        run: pip install ruff
      - name: Run ruff
        run: ruff check .
"""
            wf_path = f"{local_path}/.github/workflows/auto-patch.yml"
            write_file(wf_path, workflow)
            emit("ci:done", wf_path)
        except Exception as e:
            emit("ci:error", str(e))


    # Publish
    emit("publish:start")
    print("\n[Publisher]: Publishing...")
    import time
    timestamp = int(time.time())
    new_branch = f"auto-style-fixes-{timestamp}"
    emit("commit:start", new_branch)
    try:
        # Safety: ensure the repo we're about to push to matches the repo URL provided
        try:
            repo_obj = Repo(local_path)
            origin_url = (repo_obj.remotes.origin.url or "").rstrip("/").replace(".git", "")
            provided = (repo_url or "").rstrip("/").replace(".git", "")
        except Exception:
            origin_url = None
            provided = (repo_url or "").rstrip("/").replace(".git", "")

        if origin_url and provided and origin_url != provided:
            err = f"Refusing to push: cloned repo origin ({origin_url}) does not match provided repo URL ({provided})"
            print(f"[Safety] {err}")
            emit("push:error", err)
            return {"status": "failed", "reason": "repo_mismatch", "detail": err}

        created_branch = create_branch_and_push(local_path, new_branch, gh_token, files_to_add=generated_files or None, commit_message=(pr_requirement if pr_requirement else None))
        emit("commit:done", created_branch)
        emit("push:done", created_branch)
    except MergeConflictError as e:
        emit("push:conflict", str(e))
        # create an issue to notify the 'cloner' about the conflict
        try:
            issue_url = create_issue(repo_url, "Merge conflicts detected by AutoPatch",
                                     f"Merge conflicts detected when pushing branch {new_branch}: {e}", gh_token)
            emit("cloner:notify", issue_url)
        except Exception:
            pass
        # Emit remaining stages as failed
        emit("publish:error", str(e))
        emit("pr:error", "Cannot create PR due to merge conflict")
        emit("prreview:error", "Cannot review PR due to merge conflict")
        # Still return result so UI can show what happened
        return {"status": "failed", "reason": "merge_conflict", "detail": str(e)}
    except Exception as e:
        emit("push:error", str(e))
        emit("publish:error", str(e))
        emit("pr:error", str(e))
        emit("prreview:error", str(e))
        return {"status": "failed", "reason": "push_error", "detail": str(e)}

    # Branch created successfully
    emit("publish:start")
    pr_url = None
    
    # Auto-create PR (always enabled - Patcher always creates PRs)
    pr_url = None
    try:
        print("[Publisher] Creating pull request...")
        
        # Determine PR title and body based on requirement or auto-fixes
        if pr_requirement:
            # Requirement-driven PR
            pr_title = f"feat: {pr_requirement[:60]}" if len(pr_requirement) > 0 else "feat: AI-generated improvements"
            files_section = ""
            if 'generated_files' in locals() and generated_files:
                files_section = "\n**Files Generated:**\n" + "\n".join([f"- `{p}`" for p in generated_files]) + "\n"
            pr_body = f"""Patcher - AI-Powered Auto-Generated Fixes

Requirement:
{pr_requirement}
{files_section}
Changes Made:
- Code automatically generated to address the requirement

---
Created by Patcher AI
"""
        else:
            # Auto-linting PR
            pr_title = "chore: auto style fixes"
            pr_body = "🤖 **Patcher** - Automated code style fixes\n\nThis PR was created by the Patcher bot to fix code style issues detected in your repository."
        pr_url = create_pull_request(
            repo_url=repo_url,
            new_branch=created_branch,
            base_branch=base_branch or "main",
            gh_token=gh_token,
            title=pr_title,
            body=pr_body,
        )
        print(f"[Publisher] PR created successfully: {pr_url}")
        emit("pr:created", pr_url)
    except Exception as e:
        error_msg = f"Failed to create PR: {str(e)}"
        print(f"[Publisher] PR creation failed: {error_msg}")
        emit("pr:error", error_msg)
        pr_url = None
    
    emit("publish:done", pr_url or created_branch)


    # Auto-review (if requested)
    if pr_review_comments:
        try:
            if not pr_url:
                print("[Publisher] ❌ Cannot post PR review - no PR created")
                emit("prreview:error", "Cannot review PR - PR creation failed")
            else:
                print("[Patcher] Posting automated review comment...")
                # Dynamic review comment with requirement and generated files summary
                comment_body = f"Automated Review by Patcher\n\n"
                if pr_requirement:
                    comment_body += f"**Requirement:** {pr_requirement}\n\n"
                if 'generated_files' in locals() and generated_files:
                    comment_body += "**Generated Files:**\n"
                    for p in generated_files:
                        comment_body += f"- {p}\n"
                    comment_body += "\n"
                comment_body += "**Summary:**\n- Code changes were auto-generated by Patcher to address the requirement.\n"
                if bandit_report_id:
                    comment_body += f"- Security scan complete (Bandit report: {bandit_report_id})\n"
                comment_body += "\n**Next Steps:**\n1. Review the changes in this PR\n2. Run your test suite to verify compatibility\n3. Merge when ready\n\n---\nCreated by Patcher AI\n"
                post_pr_comment(pr_url, comment_body, gh_token)
                print(f"[Patcher] Review comment posted")
                emit("prreview:done", pr_url)
        except Exception as e:
            error_msg = f"Failed to post review comment: {str(e)}"
            print(f"[Patcher] PR review failed: {error_msg}")
            emit("prreview:error", error_msg)
    else:
        emit("prreview:done", "Review not requested")
    # Return structured result for UI
    res = {"status": "ok", "branch": created_branch, "pr_url": pr_url, "bandit": bandit_report_id}
    emit("result", res)
    return res
