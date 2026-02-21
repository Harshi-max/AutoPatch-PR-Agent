import asyncio
import re
import contextlib
import io
import queue
import threading
import time
import warnings

# Suppress noisy Pydantic schema warning about the built-in `any` function
warnings.filterwarnings(
    "ignore",
    message=r".*<built-in function any> is not a Python type.*",
    category=UserWarning,
)

import streamlit as st

from agents.orchestrator import run_pipeline
from core.artifacts import get_artifact
from agents.publish_agent import create_pull_request


st.set_page_config(page_title="AutoPatch PR Agent", layout="centered")

st.title("AutoPatch PR Agent")
st.write("AI-powered multi-agent tool to auto-fix style issues and open a PR.")

repo_url = st.text_input("GitHub repository URL", help="e.g. https://github.com/owner/repo.git")
gh_token = st.text_input("GitHub token (PAT)", type="password")
base_branch = st.text_input("Base branch", value="main")

# Feature toggles
st.subheader("Options")
enable_security = st.checkbox("Enable security linting (e.g. safety, bandit)", value=False)
enable_pr_review = st.checkbox("Create automatic PR review comments", value=False)
enable_ci = st.checkbox("Add CI integration (generate GitHub Actions workflow)", value=False)
enable_confidence = st.checkbox("Compute patch confidence scores", value=False)
enable_semantic = st.checkbox("Enable deeper semantic refactoring", value=False)

run_now = st.button("Run AutoPatch")


def _run_pipeline_background(
    repo,
    token,
    base,
    log_queue,
    event_queue,
    security_flag=False,
    pr_review_flag=False,
    ci_flag=False,
    confidence_flag=False,
    semantic_flag=False,
):
    """Run the async pipeline in a thread and push logs/events to queues."""
    def progress_cb(stage, info=None):
        event_queue.put((stage, info))

    class QueueWriter:
        def __init__(self, q):
            self.q = q

        def write(self, data):
            if data:
                self.q.put(data)

        def flush(self):
            pass

    qw = QueueWriter(log_queue)
    try:
        # Redirect stdout to queue while running
        with contextlib.redirect_stdout(qw):
            res = asyncio.run(
                run_pipeline(
                    repo,
                    token,
                    base,
                    progress_callback=progress_cb,
                    security_lint=security_flag,
                    pr_review_comments=pr_review_flag,
                    ci_integration=ci_flag,
                    confidence_scoring=confidence_flag,
                    semantic_refactor=semantic_flag,
                    auto_create_pr=False,
                )
            )
            event_queue.put(("result", res))
    except Exception as e:
        log_queue.put(f"ERROR: {e}\n")
        event_queue.put(("error", str(e)))


if run_now:
    if not repo_url:
        st.error("Please provide a GitHub repository URL.")
    elif not gh_token:
        st.error("Please provide a GitHub token (PAT).")
    else:
        log_q: "queue.Queue[str]" = queue.Queue()
        event_q: "queue.Queue[tuple]" = queue.Queue()

        # start thread later once we have the UI prepared

        # UI elements for stages
        stages = {
            "clone": st.empty(),
            "security": st.empty(),
            "scan": st.empty(),
            "lint": st.empty(),
            "analyze": st.empty(),
            "semantic": st.empty(),
            "confidence": st.empty(),
            "generate": st.empty(),
            "fix": st.empty(),
            "apply": st.empty(),
            "commit": st.empty(),
            "push": st.empty(),
            "publish": st.empty(),
            "pr": st.empty(),
            "prreview": st.empty(),
            "ci": st.empty(),
        }

        log_container = st.empty()
        log_text = ""

        stages["clone"].info("Clone: pending")
        stages["security"].info("Security: pending")
        stages["scan"].info("Scan: pending")
        stages["lint"].info("Lint: pending")
        stages["analyze"].info("Analyze: pending")
        stages["semantic"].info("Semantic refactor: pending")
        stages["confidence"].info("Patch confidence: pending")
        stages["generate"].info("Generate: pending")
        stages["fix"].info("Fix: pending")
        stages["apply"].info("Apply: pending")
        stages["prreview"].info("PR review comments: pending")
        stages["ci"].info("CI integration: pending")
        stages["commit"].info("Commit: pending")
        stages["push"].info("Push: pending")
        stages["publish"].info("Publish: pending")
        stages["pr"].info("PR: pending")

        # start the background runner with selected feature flags
        t = threading.Thread(
            target=_run_pipeline_background,
            args=(
                repo_url.strip(),
                gh_token.strip(),
                base_branch.strip() or None,
                log_q,
                event_q,
                enable_security,
                enable_pr_review,
                enable_ci,
                enable_confidence,
                enable_semantic,
            ),
            daemon=True,
        )
        t.start()

        with st.spinner("Running agents — streaming logs below..."):
            while t.is_alive() or not log_q.empty() or not event_q.empty():
                try:
                    while not event_q.empty():
                        stage, info = event_q.get_nowait()
                        if stage == "clone:done":
                            stages["clone"].success(f"Clone: done ({info})")
                        elif stage == "scan:start":
                            stages["scan"].info("Scan: running")
                        elif stage == "security:start":
                            stages["security"].info("Security lint: running")
                        elif stage == "security:done":
                            stages["security"].success("Security lint: done")
                            # show bandit artifact if present
                            if isinstance(info, str) and "Reference ID:" in info:
                                # parse report id
                                match = re.search(r"Reference ID: ([a-f0-9\-]{36})", info)
                                if match:
                                    rid = match.group(1)
                                    art = get_artifact(rid)
                                    if art:
                                        log_q.put(f"Bandit report ({rid}): {art.get('count')} issues\n")
                                        log_q.put(str(art.get('issues')) + "\n")
                        elif stage == "scan:done":
                            stages["scan"].success("Scan: done")
                        elif stage == "lint:start":
                            stages["lint"].info("Lint: running")
                        elif stage == "lint:done":
                            stages["lint"].success("Lint: done")
                            if info:
                                log_q.put(f"Lint/analysis output: {info}\n")
                        elif stage == "analyze:start":
                            stages["analyze"].info("Analyze: running")
                        elif stage == "analyze:done":
                            stages["analyze"].success("Analyze: done")
                        elif stage == "semantic:start":
                            stages["semantic"].info("Semantic refactor: running")
                        elif stage == "semantic:done":
                            stages["semantic"].success("Semantic refactor: done")
                        elif stage == "confidence:start":
                            stages["confidence"].info("Computing patch confidence...")
                        elif stage == "confidence:done":
                            stages["confidence"].success("Patch confidence: done")
                        elif stage == "generate:start":
                            stages["generate"].info("Generate: running")
                        elif stage == "generate:done":
                            stages["generate"].success("Generate: done")
                        elif stage == "fix:start":
                            stages["fix"].info("Fix: running")
                        elif stage == "fix:done":
                            stages["fix"].success("Fix: done")
                        elif stage == "apply:done":
                            stages["apply"].success("Apply: done")
                        elif stage == "commit:start":
                            stages["commit"].info("Commit: running")
                        elif stage == "commit:done":
                            stages["commit"].success(f"Commit: done ({info})")
                        elif stage == "push:done":
                            stages["push"].success(f"Push: done ({info})")
                        elif stage == "publish:start":
                            stages["publish"].info("Publish: running")
                        elif stage == "publish:done":
                            stages["publish"].success("Publish: done")
                        elif stage == "pr:created" or stage == "pr:created":
                            stages["pr"].success(f"PR created: {info}")
                            # show PR link in separate area
                            st.markdown(f"**PR:** {info}")
                        elif stage == "cloner:notify":
                            st.warning(f"Cloner notified: {info}")
                        elif stage == "result":
                            # pipeline result dict returned
                            try:
                                res = info
                                st.session_state['pipeline_result'] = res
                                if res and res.get('branch'):
                                    st.success(f"Branch prepared: {res.get('branch')}")
                                    if not res.get('pr_url'):
                                        st.session_state['pr_pending'] = True
                            except Exception:
                                pass
                        elif stage == "prreview:start":
                            stages["prreview"].info("PR review comments: running")
                        elif stage == "prreview:done":
                            stages["prreview"].success("PR review comments: done")
                        elif stage == "ci:start":
                            stages["ci"].info("CI integration: running")
                        elif stage == "ci:done":
                            stages["ci"].success("CI integration: done")
                        elif stage == "error":
                            st.error(f"Pipeline error: {info}")

                    # append logs
                    appended = False
                    while not log_q.empty():
                        chunk = log_q.get_nowait()
                        log_text += str(chunk)
                        appended = True

                    if appended:
                        log_container.code(log_text)

                except Exception:
                    pass
                time.sleep(0.2)

        st.success("Pipeline finished")
        log_container.code(log_text)

        # If a PR is pending, show create-PR button
        if st.session_state.get('pr_pending'):
            if st.button("Create Pull Request"):
                res = st.session_state.get('pipeline_result') or {}
                branch = res.get('branch')
                if branch:
                    try:
                        pr_url = create_pull_request(repo_url.strip(), branch, base_branch.strip() or 'main', gh_token.strip(),
                                                     title="chore: auto style fixes", body="This PR was created by Auto Patch PR Agent.")
                        st.success(f"PR created: {pr_url}")
                        st.session_state['pr_pending'] = False
                    except Exception as e:
                        st.error(f"Failed to create PR: {e}")


st.markdown("---")
st.markdown("**Notes:** The token must have repo access to push branches and open PRs.")
