# Git utils
# Local git operations
import os
from pathlib import Path
from typing import Optional

from git import Repo, GitCommandError  # pip install GitPython
from urllib.parse import urlparse, urlunparse, quote

def write_file(file_path: str, content: str) -> str:
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"Updated {file_path}"
    except Exception as e:
        return f"Error writing {file_path}: {e}"

def clone_repo(repo_url: str, dest_dir: str, branch: Optional[str] = None) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    local_path = os.path.join(dest_dir, repo_name)
    if not os.path.exists(local_path):
        repo = Repo.clone_from(repo_url, local_path)
    else:
        repo = Repo(local_path)
    if branch:
        repo.git.checkout(branch)
    return local_path

class MergeConflictError(RuntimeError):
    pass


def create_branch_and_push(repo_path: str, new_branch: str, github_token: Optional[str] = None, files_to_add: list | None = None, commit_message: str | None = None) -> str:
    repo = Repo(repo_path)
    git = repo.git

    print(f"[Git] Creating branch: {new_branch}")
    # Create or checkout branch
    stash_created = False
    try:
        if new_branch in repo.heads:
            print(f"[Git] Branch {new_branch} already exists locally, checking out")
            git.checkout(new_branch)
        else:
            git.checkout("-b", new_branch)
    except Exception as br_err:
        err_text = str(br_err)
        print(f"[Git] Branch checkout/creation failed: {err_text}")
        # If checkout failed due to untracked files that would be overwritten, try stashing untracked files and retry
        if "would be overwritten" in err_text or "untracked working tree files" in err_text:
            # Parse file paths from the git error message to stash only the conflicting files
            try:
                lines = err_text.splitlines()
                conflicting = []
                start = False
                for ln in lines:
                    if 'The following untracked working tree files would be overwritten by checkout:' in ln:
                        start = True
                        continue
                    if start:
                        if ln.strip().startswith('Please move') or ln.strip() == 'Aborting':
                            break
                        # lines typically start with a tab or spaces
                        path = ln.strip()
                        if path:
                            conflicting.append(path)
                if conflicting:
                    print(f"[Git] Stashing only conflicting untracked files: {conflicting}")
                    # Use pathspecs to stash only those files
                    stash_args = ['push', '-u', '-m', 'patcher-autostash', '--'] + conflicting
                    stash_msg = repo.git.stash(*stash_args)
                    stash_created = True
                else:
                    # Fallback to full untracked stash
                    print("[Git] No specific conflicting files parsed; stashing all untracked files to allow branch checkout...")
                    stash_msg = repo.git.stash('push', '-u', '-m', 'patcher-autostash')
                    stash_created = True

                # Retry checkout after stashing
                if new_branch in repo.heads:
                    git.checkout(new_branch)
                else:
                    git.checkout('-b', new_branch)
            except Exception as retry_err:
                print(f"[Git] Branch checkout retry failed after stash: {retry_err}")
                raise RuntimeError(f"Failed to create or checkout branch {new_branch}: {retry_err}")
        else:
            # attempt to create head and checkout as a last resort
            try:
                repo.create_head(new_branch)
                repo.heads[new_branch].checkout()
            except Exception as bh_err:
                raise RuntimeError(f"Failed to create or checkout branch {new_branch}: {bh_err}")
    
    # Stage files (prefer explicit list) and commit. If no changes, create empty commit.
    try:
        if files_to_add:
            for f in files_to_add:
                # Use repo-relative paths
                repo.git.add(f)
        else:
            repo.git.add(A=True)

        msg = commit_message or "chore: auto style fixes by agent"
        try:
            repo.index.commit(msg)
            print(f"[Git] Committed changes: {msg}")
        except GitCommandError as c_err:
            # Handle case: nothing to commit
            cerr = str(c_err)
            if "nothing to commit" in cerr.lower() or "no changes added to commit" in cerr.lower():
                try:
                    print(f"[Git] No code changes detected; creating an empty commit to ensure branch exists")
                    repo.git.commit('--allow-empty', '-m', msg)
                    print(f"[Git] Empty commit created")
                except Exception as ec_err:
                    print(f"[Git] Empty commit failed: {ec_err}")
            else:
                # Try setting local git user config and retry commit
                print(f"[Git] Commit failed: {c_err}. Attempting to set local git user and retry.")
                try:
                    cfg = repo.config_writer()
                    try:
                        cfg.set_value('user', 'name', 'Patcher AI')
                        cfg.set_value('user', 'email', 'patcher@local')
                        cfg.release()
                    except Exception:
                        pass
                    repo.index.commit(msg)
                    print(f"[Git] Committed changes on retry: {msg}")
                except Exception as c_err2:
                    print(f"[Git] Commit retry failed: {c_err2}")
                    raise RuntimeError(f"Commit failed: {c_err2}")
    except Exception as e:
        print(f"[Git] Error while staging/committing: {e}")
        raise

    origin = repo.remote(name="origin")
    pushed = False
    
    print(f"[Git] Attempting to push {new_branch} to origin... (origin url: {getattr(origin, 'url', None)})")
    try:
        origin.push(refspec=f"{new_branch}:{new_branch}", set_upstream=True)
        pushed = True
        print(f"[Git] ✅ Push successful!")
    except GitCommandError as e:
        print(f"[Git] ⚠️ Initial push failed: {e}")
        # Try authenticated push if token provided
        if github_token and getattr(origin, 'url', None) and origin.url.startswith("http"):
            print(f"[Git] Attempting authenticated push with token...")
            orig_url = origin.url
            try:
                token_enc = quote(github_token, safe='')
                parsed = urlparse(orig_url)
                host = parsed.hostname or ''
                port = f":{parsed.port}" if parsed.port else ''
                new_netloc = f"x-access-token:{token_enc}@{host}{port}"
                authed = parsed._replace(netloc=new_netloc)
                origin.set_url(urlunparse(authed))
                repo.git.push("--set-upstream", "origin", new_branch)
                pushed = True
                print(f"[Git] ✅ Authenticated push successful!")
            except Exception as auth_err:
                print(f"[Git] ❌ Authenticated push failed: {auth_err}")
                raise RuntimeError(f"Push with token failed: {auth_err}")
            finally:
                try:
                    origin.set_url(orig_url)
                except Exception:
                    pass
        else:
            # Attempt to pull and merge remote to detect conflicts
            print(f"[Git] No token provided or remote not an HTTP URL, attempting pull to resolve...")
            try:
                repo.git.pull()
                print(f"[Git] Merged remote changes, retrying push...")
                # After pulling, try pushing again
                origin.push(refspec=f"{new_branch}:{new_branch}", set_upstream=True)
                pushed = True
                print(f"[Git] ✅ Push successful after merge!")
            except GitCommandError as e2:
                msg = str(e2)
                print(f"[Git] ❌ Final push failed: {msg}")
                if "CONFLICT" in msg or "conflict" in msg:
                    raise MergeConflictError("Merge conflicts detected while pulling remote.")
                raise RuntimeError(f"Push failed: {msg}")
    
    if not pushed:
        raise RuntimeError("Failed to push branch - all push attempts failed.")
    # If we stashed earlier, try to pop the stash back
    try:
        if 'stash_created' in locals() and stash_created:
            try:
                print('[Git] Restoring stashed changes')
                repo.git.stash('pop')
            except Exception:
                # ignore stash pop failures
                pass
    except Exception:
        pass
    return new_branch


def get_commit_history(repo_path: str, max_count: int = 50):
    repo = Repo(repo_path)
    commits = []
    for c in repo.iter_commits(max_count=max_count):
        commits.append({
            "sha": c.hexsha,
            "message": c.message.strip(),
            "author": c.author.name,
            "date": c.committed_datetime.isoformat(),
        })
    return commits
