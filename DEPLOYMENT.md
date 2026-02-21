# Deployment Guide: Patcher on Streamlit Cloud

This guide explains how to deploy **Patcher** (AutoPatch PR Agent) to Streamlit Cloud.

## Prerequisites

- GitHub repository with your code
- GitHub Personal Access Token (PAT) with scopes: `repo`, `issues:write`, `pull_requests:write`
- Streamlit Cloud account (free at https://share.streamlit.io)

## Step 1: Generate GitHub Token

1. Go to https://github.com/settings/tokens/new
2. Create a **Personal Access Token** with these scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `issues:write` (write access to issues and pull requests)
   - ✅ `pull_requests:write` (write access to pull requests)
3. Click "Generate token"
4. **Copy the token** (you won't see it again!)

## Step 2: Set Up Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Select your GitHub repository and branch (`main` recommended)
4. Set the main file path to: `app.py`

## Step 3: Configure Secrets

1. After app creation, click **"Settings"** (gear icon)
2. Navigate to **"Secrets"** tab
3. Paste the following and fill in your values:

```toml
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
GOOGLE_API_KEY = "AIzaSyxxxxxxxxxxxxxxxxxxxxx"  # Optional, for AI review generation
```

4. Click **"Save"**

## Step 4: Environment Variables

Streamlit Cloud automatically loads from `.streamlit/secrets.toml` in your repository.

**Important:** The `.streamlit/secrets.toml` file is **NOT committed to Git** (see `.gitignore`). Use the web interface secrets instead.

## Troubleshooting

### Error: `/mount/src/autopatch-pr-agent/temp_repos/...`

**Cause:** Streamlit Cloud has filesystem restrictions on the current directory.

**Solution:** ✅ Already fixed in the latest version!
- The app now uses `/tmp/` directory automatically on Streamlit Cloud
- If still experiencing issues, try:
  1. Restarting the app (see **App actions** → **Reboot**)
  2. Checking that `GITHUB_TOKEN` secret is set correctly

### Error: "Token does not have permission to push"

**Cause:** Your GitHub PAT doesn't have the required scopes.

**Solution:**
1. Delete the old token: https://github.com/settings/tokens
2. Create a new one with **all three required scopes** (see Step 1)
3. Update the secret in Streamlit Cloud settings

### Error: "Repository not found"

**Cause:** Token doesn't have access to the repo, or the repo URL is wrong.

**Solution:**
- Verify the repo URL format: `https://github.com/owner/repo.git`
- Ensure token has `repo` scope (full access, not just `public_repo`)
- If it's a private repo, token must have access

## Performance Tips

- **First run is slower** (clones repo, runs analysis) — subsequent runs are faster
- **For large repos**, linting can take 2-5 minutes
- **Memory limit**: Streamlit Cloud free tier has ~1GB; very large repos may hit limits

## Logs & Debugging

To see detailed logs:
1. Click **"Settings"** → **"View logs"**
2. Check the "Execution Logs" section in the app UI

## Advanced Configuration

Edit `.streamlit/config.toml` to customize:

```toml
[client]
showErrorDetails = true    # Show detailed error messages in UI

[server]
maxUploadSize = 200        # Max file upload size in MB
enableXsrfProtection = true # Security setting
```

## Security Best Practices

✅ **Do:**
- Store tokens in Streamlit Cloud secrets, **not** `.env` or `.gitignore`
- Rotate tokens periodically
- Use a dedicated GitHub user for the PAT (if possible)
- Restrict token scopes to minimum needed

❌ **Don't:**
- Commit tokens to Git (they're compromised if exposed!)
- Use your personal GitHub token (create a bot account token)
- Share Streamlit Cloud URLs with untrusted users (anyone can deploy your code!)

## Support

For issues, check:
- Streamlit docs: https://docs.streamlit.io
- GitHub API docs: https://docs.github.com/en/rest
- Patcher README: [README.md](README.md)
