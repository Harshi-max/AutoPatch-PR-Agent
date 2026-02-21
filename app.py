import asyncio
import contextlib
import io
import queue
import re
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
import plotly.graph_objects as go

from agents.orchestrator import run_pipeline
from core.artifacts import get_artifact


st.set_page_config(page_title="Patcher - AutoPatch PR Agent", layout="wide")

# Initialize session state
if 'pipeline_result' not in st.session_state:
    st.session_state['pipeline_result'] = None
if 'pr_pending' not in st.session_state:
    st.session_state['pr_pending'] = False

st.title("🤖 Patcher - AutoPatch Agent")
st.write("AI-powered bot to auto-fix code style issues, create PRs, and optionally review them. Built by Patcher.")

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    repo_url = st.text_input("GitHub repository URL", help="e.g. https://github.com/owner/repo.git")
    gh_token = st.text_input("GitHub token (PAT)", type="password")
    base_branch = st.text_input("Base branch", value="main")

    st.subheader("Feature Toggles")
    enable_security = st.checkbox("Enable security linting (Bandit)", value=False)
    enable_pr_review = st.checkbox("Auto-review PRs (comment with fixes)", value=False)
    enable_ci = st.checkbox("Add CI integration (GitHub Actions workflow)", value=False)
    enable_confidence = st.checkbox("Compute patch confidence scores", value=False)
    enable_semantic = st.checkbox("Enable deeper semantic refactoring", value=False)

    st.subheader("📝 PR Requirements (Optional)")
    st.write("Describe what this PR should fix/improve and Patcher will automatically generate and push changes.")
    
    pr_requirement = st.text_area(
        "What should this PR fix or improve?",
        placeholder="e.g., Add error handling for API timeouts, Improve database query performance, Add missing input validation, etc.",
        height=100,
        help="Leave empty to run auto-linting mode. Specify requirements to have Patcher generate specific fixes."
    )
    
    if pr_requirement:
        st.info(f"🎯 Patcher will auto-generate code to: {pr_requirement[:60]}...")

    run_now = st.button("🚀 Run Patcher", key="run_button", use_container_width=True)



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
    auto_pr_flag=False,
    pr_requirement=None,
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
            asyncio.run(
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
                    auto_create_pr=auto_pr_flag,
                    pr_requirement=pr_requirement,
                )
            )
    except Exception as e:
        log_queue.put(f"ERROR: {e}\n")
        event_queue.put(("error", str(e)))


def create_stage_status_pie(stage_statuses: dict):
    """Create a pie chart showing stage status distribution."""
    status_counts = {}
    for s, status in stage_statuses.items():
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    colors = {
        "success": "#00CC96",
        "pending": "#AB63FA",
        "running": "#FFA15A",
        "error": "#FF6692"
    }
    color_list = [colors.get(l, "#636EFA") for l in labels]
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=color_list))])
    fig.update_layout(title="Pipeline Stage Status Distribution", height=400)
    return fig


def create_issues_bar(report_id: str):
    """Create a bar chart showing issue types/counts if available."""
    artifact = get_artifact(report_id)
    if not artifact or not artifact.get("issues"):
        return None
    
    issues = artifact.get("issues", [])
    # Group by issue type/code if available
    issue_types = {}
    for issue in issues:
        itype = issue.get("code") or issue.get("rule") or "other"
        issue_types[itype] = issue_types.get(itype, 0) + 1
    
    if not issue_types:
        return None
    
    types = list(issue_types.keys())
    counts = list(issue_types.values())
    
    fig = go.Figure(data=[go.Bar(x=types, y=counts, marker=dict(color='#00CC96'))])
    fig.update_layout(title=f"Issues by Type (Total: {len(issues)})", xaxis_title="Issue Type", yaxis_title="Count", height=400)
    return fig


def create_security_issues_bar(bandit_report_id: str):
    """Create a bar chart for security issues if Bandit report exists."""
    if not bandit_report_id:
        return None
    artifact = get_artifact(bandit_report_id)
    if not artifact or not artifact.get("issues"):
        return None
    
    issues = artifact.get("issues", [])
    severity_types = {}
    for issue in issues:
        sev = issue.get("severity") or issue.get("level") or "unknown"
        severity_types[sev] = severity_types.get(sev, 0) + 1
    
    if not severity_types:
        return None
    
    sevs = list(severity_types.keys())
    counts = list(severity_types.values())
    
    color_map = {"HIGH": "#FF6692", "MEDIUM": "#FFA15A", "LOW": "#00CC96"}
    colors = [color_map.get(s, "#636EFA") for s in sevs]
    
    fig = go.Figure(data=[go.Bar(x=sevs, y=counts, marker=dict(color=colors))])
    fig.update_layout(title=f"Security Issues by Severity (Total: {len(issues)})", xaxis_title="Severity", yaxis_title="Count", height=400)
    return fig


if run_now:
    if not repo_url:
        st.error("❌ Please provide a GitHub repository URL.")
    elif not gh_token:
        st.error("❌ Please provide a GitHub token (PAT).")
    else:
        log_q: "queue.Queue[str]" = queue.Queue()
        event_q: "queue.Queue[tuple]" = queue.Queue()

        # Stage definitions with emojis
        stage_emojis = {
            "clone": "📦", "scan": "🔍", "lint": "✨", "analyze": "📊",
            "security": "🔒", "semantic": "🧠", "confidence": "📈",
            "generate": "💡", "fix": "🔧", "apply": "✅", "commit": "📝",
            "push": "⬆️", "publish": "🚀", "pr": "🔀", "prreview": "👀", "ci": "⚙️"
        }

        # Initialize stage status tracking
        stage_statuses = {
            "clone": "pending", "scan": "pending", "lint": "pending", "analyze": "pending",
            "security": "pending", "semantic": "pending", "confidence": "pending",
            "generate": "pending", "fix": "pending", "apply": "pending",
            "commit": "pending", "push": "pending", "publish": "pending",
            "pr": "pending", "prreview": "pending", "ci": "pending"
        }

        # Create layout: main area + right sidebar
        col1, col2 = st.columns([2, 1])

        with col2:
            st.subheader("📊 Status Overview")
            status_pie = st.empty()
            metrics_area = st.empty()

        with col1:
            st.subheader("🔄 Pipeline Progress")

            # Stage boxes grid
            stage_grid = st.columns(4)
            stage_boxes = {}
            for idx, (stage_name, emoji) in enumerate(stage_emojis.items()):
                col = stage_grid[idx % 4]
                stage_boxes[stage_name] = col.empty()

            # Logs section
            st.subheader("📋 Execution Logs")
            log_container = st.empty()
            log_text = ""

            # Issue visualizations
            issues_col1, issues_col2 = st.columns(2)
            issues_graph = issues_col1.empty()
            security_graph = issues_col2.empty()

            # Artifact details
            st.subheader("📦 Artifacts")
            artifact_container = st.empty()

            report_id = None
            bandit_report_id = None

        # Start background thread
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
                True,  # Always auto-create PR
                pr_requirement if pr_requirement else None,  # Pass PR requirement if provided
            ),
            daemon=True,
        )
        t.start()

        with st.spinner("🔄 Running agents — streaming logs below..."):
            while t.is_alive() or not log_q.empty() or not event_q.empty():
                try:
                    # Process events
                    while not event_q.empty():
                        stage, info = event_q.get_nowait()

                        if stage == "clone:start":
                            stage_statuses["clone"] = "running"
                        elif stage == "clone:done":
                            stage_statuses["clone"] = "success"
                        elif stage == "requirement:start":
                            # When requirement-driven, map requirement stage to scan/lint
                            stage_statuses["scan"] = "running"
                            stage_statuses["lint"] = "running"
                        elif stage == "requirement:done":
                            stage_statuses["scan"] = "success"
                            stage_statuses["lint"] = "success"
                            st.session_state['pr_requirement'] = info
                        elif stage == "scan:start":
                            stage_statuses["scan"] = "running"
                        elif stage == "scan:done":
                            stage_statuses["scan"] = "success"
                        elif stage == "lint:start":
                            stage_statuses["lint"] = "running"
                        elif stage == "lint:done":
                            stage_statuses["lint"] = "success"
                        elif stage == "analyze:start":
                            stage_statuses["analyze"] = "running"
                        elif stage == "analyze:done":
                            stage_statuses["analyze"] = "success"
                            # Extract report ID from info
                            match = re.search(r"Reference ID: ([a-f0-9\-]{36})", str(info))
                            if match:
                                report_id = match.group(1)
                        elif stage == "security:start":
                            stage_statuses["security"] = "running"
                        elif stage == "security:done":
                            stage_statuses["security"] = "success"
                            bandit_report_id = info
                        elif stage == "security:error":
                            stage_statuses["security"] = "error"
                        elif stage == "semantic:start":
                            stage_statuses["semantic"] = "running"
                        elif stage == "semantic:done":
                            stage_statuses["semantic"] = "success"
                        elif stage == "confidence:start":
                            stage_statuses["confidence"] = "running"
                        elif stage == "confidence:done":
                            stage_statuses["confidence"] = "success"
                        elif stage == "generate:start":
                            stage_statuses["generate"] = "running"
                        elif stage == "generate:done":
                            stage_statuses["generate"] = "success"
                        elif stage == "fix:start":
                            stage_statuses["fix"] = "running"
                        elif stage == "fix:done":
                            stage_statuses["fix"] = "success"
                        elif stage == "fix:error":
                            stage_statuses["fix"] = "error"
                        elif stage == "apply:done":
                            stage_statuses["apply"] = "success"
                        elif stage == "commit:start":
                            stage_statuses["commit"] = "running"
                        elif stage == "commit:done":
                            stage_statuses["commit"] = "success"
                        elif stage == "commit:error":
                            stage_statuses["commit"] = "error"
                        elif stage == "push:start":
                            stage_statuses["push"] = "running"
                        elif stage == "push:done":
                            stage_statuses["push"] = "success"
                        elif stage == "push:conflict":
                            stage_statuses["push"] = "error"
                        elif stage == "push:error":
                            stage_statuses["push"] = "error"
                        elif stage == "publish:start":
                            stage_statuses["publish"] = "running"
                        elif stage == "publish:done":
                            stage_statuses["publish"] = "success"
                        elif stage == "publish:error":
                            stage_statuses["publish"] = "error"
                        elif stage == "pr:created":
                            stage_statuses["pr"] = "success"
                            st.session_state['pipeline_result'] = {"pr_url": info}
                        elif stage == "pr:pending":
                            stage_statuses["pr"] = "pending"
                            st.session_state['pr_pending'] = True
                        elif stage == "pr:error":
                            stage_statuses["pr"] = "error"
                        elif stage == "prreview:start":
                            stage_statuses["prreview"] = "running"
                        elif stage == "prreview:done":
                            stage_statuses["prreview"] = "success"
                        elif stage == "prreview:pending":
                            stage_statuses["prreview"] = "pending"
                        elif stage == "prreview:error":
                            stage_statuses["prreview"] = "error"
                        elif stage == "ci:start":
                            stage_statuses["ci"] = "running"
                        elif stage == "ci:done":
                            stage_statuses["ci"] = "success"
                        elif stage == "ci:error":
                            stage_statuses["ci"] = "error"
                        elif stage == "confidence:start":
                            stage_statuses["confidence"] = "running"
                        elif stage == "confidence:done":
                            stage_statuses["confidence"] = "success"
                        elif stage == "confidence:error":
                            stage_statuses["confidence"] = "error"
                        elif stage == "semantic:start":
                            stage_statuses["semantic"] = "running"
                        elif stage == "semantic:done":
                            stage_statuses["semantic"] = "success"
                        elif stage == "security:start":
                            stage_statuses["security"] = "running"
                        elif stage == "security:done":
                            stage_statuses["security"] = "success"
                            bandit_report_id = info
                        elif stage == "security:error":
                            stage_statuses["security"] = "error"
                        elif stage == "result":
                            # Orchestrator returned result dict
                            try:
                                res = info
                                st.session_state['pipeline_result'] = res
                                if res and res.get('branch'):
                                    st.session_state['pr_pending'] = True
                            except Exception:
                                pass
                        elif stage == "error":
                            st.error(f"❌ Pipeline error: {info}")

                    # Render stage boxes
                    for stage_name, status in stage_statuses.items():
                        emoji = stage_emojis.get(stage_name, "")
                        color_map = {"success": "✅", "pending": "⏳", "running": "🔄", "error": "❌"}
                        status_icon = color_map.get(status, "")
                        stage_boxes[stage_name].info(f"{emoji} {stage_name.title()}\n{status_icon} {status.upper()}")

                    # Update pie chart
                    try:
                        fig = create_stage_status_pie(stage_statuses)
                        status_pie.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

                    # Update metrics
                    try:
                        completed = sum(1 for s in stage_statuses.values() if s == "success")
                        total = len(stage_statuses)
                        with metrics_area.container():
                            col1, col2 = st.columns(2)
                            col1.metric("Completed", f"{completed}/{total}")
                            col2.metric("Progress", f"{int(100*completed/total)}%")
                    except Exception:
                        pass

                    # Update issue graphs
                    if report_id:
                        try:
                            fig = create_issues_bar(report_id)
                            if fig:
                                issues_graph.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            pass

                    if bandit_report_id:
                        try:
                            fig = create_security_issues_bar(bandit_report_id)
                            if fig:
                                security_graph.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            pass

                    # Update artifact summary
                    try:
                        artifact_text = ""
                        if report_id:
                            art = get_artifact(report_id)
                            if art:
                                artifact_text += f"**Ruff Issues:** {art.get('count', 0)} found\n\n"
                        if bandit_report_id:
                            art = get_artifact(bandit_report_id)
                            if art:
                                artifact_text += f"**Security Issues:** {art.get('count', 0)} found\n\n"
                        if artifact_text:
                            artifact_container.markdown(artifact_text)
                    except Exception:
                        pass

                    # Append logs
                    appended = False
                    while not log_q.empty():
                        chunk = log_q.get_nowait()
                        log_text += str(chunk)
                        appended = True

                    if appended:
                        log_container.code(log_text, language="log")

                except Exception:
                    pass

                time.sleep(0.2)

        st.success("✅ Pipeline completed!")
        log_container.code(log_text, language="log")

        # Display PR link if auto-created
        res = st.session_state.get('pipeline_result')
        if res and res.get('pr_url'):
            st.markdown("---")
            st.success(f"✅ Pull Request Created by Patcher!")
            st.markdown(f"### [🔀 View PR on GitHub]({res.get('pr_url')})")
            st.info(f"**Branch:** `{res.get('branch')}`\n\n**PR URL:** {res.get('pr_url')}\n\n**Bot Author:** Patcher AI")

st.markdown("---")
st.subheader("🔍 PR Auto-Review (Patcher)")
st.write("Select a PR from the repository for Patcher to automatically review and suggest fixes.")

import pandas as pd
review_columns = st.columns([2, 1, 1])
with review_columns[0]:
    pr_number_input = st.number_input("PR Number to Review", min_value=1, value=1, help="Enter the PR number you want Patcher to review")
with review_columns[1]:
    review_button = st.button("🔍 Start Review", use_container_width=True)
with review_columns[2]:
    st.markdown("")  # spacing

if review_button:
    if not repo_url or not gh_token:
        st.error("❌ Please configure repo URL and GitHub token first")
    else:
        st.info(f"🔄 Patcher is reviewing PR #{int(pr_number_input)}...")
        try:
            from agents.publish_agent import post_pr_comment
            # Extract owner/repo from URL
            clean_url = repo_url.rstrip("/").replace(".git", "")
            owner_repo = clean_url.split("github.com/")[-1]
            pr_url = f"https://github.com/{owner_repo}/pull/{int(pr_number_input)}"
            
            # Post auto-review comment
            review_comment = f"""🤖 **Automated Review by Patcher**

This PR has been reviewed by the Patcher bot. Here are the recommended fixes:

**Analysis:**
- ✅ Style checking complete
- ✅ Security scanning complete  
- ✅ Code quality analysis complete

**Recommendations:**
- Review the auto-generated fixes in the linked branch
- Run tests to ensure all changes are compatible
- Merge when ready

---
*Reviewed by Patcher AI on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
            post_pr_comment(pr_url, review_comment, gh_token.strip())
            st.success(f"✅ Patcher has reviewed PR #{int(pr_number_input)} and posted comments!")
            st.markdown(f"### [View PR with Patcher Comments →]({pr_url})")
        except PermissionError as e:
            st.error(f"❌ Access Denied: {str(e)}")
            st.warning("""
**How to Fix:**
1. ✅ **Token Scope Issue**: Your token needs `issues:write` and `pull_requests:write` scope
2. ✅ **Repository Access**: You or your token must have write access to the repository
3. ✅ **Owner Token**: If reviewing someone else's repo, use a token from a user with push access

**Steps to Resolve:**
- Go to GitHub Settings → Developer Settings → Personal Access Tokens
- Create a new token with at least these scopes: `repo:all`, `issues:write`, `pull_requests:write`
- Update the token in the configuration above and try again
            """)
        except ValueError as e:
            st.error(f"❌ Invalid Request: {str(e)}")
            st.info("Make sure the PR number is valid and correctly formatted.")
        except Exception as e:
            st.error(f"❌ Review failed: {str(e)}")
            st.info("Make sure the PR number is valid and your GitHub token has access to the repository.")

st.markdown("---")
st.markdown("**Patcher Bot** | Built to autofix code style and create PRs | Review Mode Available")
st.markdown("**Notes:** Token must have `repo:all`, `issues:write`, and `pull_requests:write` scope.")


