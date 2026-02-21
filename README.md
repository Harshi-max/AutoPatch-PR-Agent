# AutoPatch PR Agent

![1764223059010](https://github.com/user-attachments/assets/c6ac1fb1-bc9f-4aa7-a40f-03de8c13df1f)

AutoPatch PR Agent is an AI-powered multi-agent system that automatically scans a repository, detects code style issues, fixes them, and creates a pull request with the corrected code. It helps developers and open-source contributors save time by automating repetitive cleanup tasks like formatting, unused imports, naming issues, and minor code smells.

The project is built for the Kaggle 5-Day AI Agents Intensive Capstone and demonstrates the use of multi-agent workflows, MCP tools, GitHub API integration, and LLM-powered code transformations.

---

## 🚀 Features

- Automatic repo scanning  
- Linting with Ruff / ESLint / Prettier  
- AI-generated code patches  
- Automatic file rewriting  
- Branch creation + commit  
- Pull Request creation using GitHub token  
- Multi-agent workflow  
- MCP tool integration  
- Basic memory for project style preferences  
- Clean logs for observability  

---


1. **User inputs** a GitHub repo URL, base branch, and a personal access token (PAT).  


## 🏗 Architecture

```
User Input → Agent Orchestrator
                |
        ┌───────┼────────────────────────┐
        ▼       ▼                        ▼
Repo Scanner   Style Analysis        Fix Generator
   Agent          Agent                 Agent
        \          |                    /
         \         |                   /
          ▼        ▼                  ▼
              MCP Tools Layer
                     |
                     ▼
               GitHub API (PR creation)
```

---

## 🔁 Workflow

1. Enter repo URL + token  
2. Clone repo  
3. Scan files  
4. Run linters  
5. Generate patches  
6. Apply fixes  
7. Create branch  
8. Commit + push  
9. Open PR  
10. Output PR link  
---

## 📦 Project Structure

```
auto-patch-agent/
│
├── agents/
│   ├── orchestrator.py
│   ├── repo_scanner.py
│   ├── style_analysis.py
│   ├── fix_generator.py
│   └── pr_creator.py
├── mcp_server/
│   ├── server.py
│   ├── repo_tool.py
│   ├── lint_tool.py
│   ├── git_tool.py
│   └── github_tool.py
│
├── interface/
│   ├── cli.py
│   └── ui.py (optional)
│
├── core/
│   ├── memory.py
│   ├── config.py
│   └── utils.py
│
├── data/
│   └── memory.json
│
├── README.md
├── requirements.txt
└── main.py
```

---

## 🛠 Tech Stack

- Python  
- MCP server  
- LLM (Gemini or OpenAI)  
- GitHub REST API  
- Ruff, ESLint, Prettier  
- Git CLI  
- SQLite/JSON for memory  


## ⚙️ Setup

1. Clone the repo and install dependencies:

```bash
git clone https://github.com/<your-username>/autopatch-pr-agent
cd AutoPatch-PR-Agent
pip install -r requirements.txt
```

2. Create a `.env` file by copying `.env.example` and set secrets there (do not commit):

```
cp .env.example .env
# then edit .env and add values for GITHUB_TOKEN and GOOGLE_API_KEY if needed
```

3. Run the CLI (optional):

```bash
python main.py
```

4. Run the Streamlit UI (recommended):

```bash
streamlit run app.py
```

### What to keep in `.env`

- `GITHUB_TOKEN` — GitHub personal access token (scopes: repo) for pushing and PR creation.
- `GOOGLE_API_KEY` — API key for Google GenAI (if using `google-genai`).
- `DEFAULT_BASE_BRANCH` — optional default branch (e.g., `main`).
- `TEMP_REPOS_DIR` — where repos are cloned (default `./temp_repos`).
- `MODEL_NAME` / `APP_NAME` — optional model/app configuration.

Keep `.env` out of source control.

---

![image 1764329210004](https://github.com/user-attachments/assets/a261e100-2cbb-477f-89a7-4827eff0389d)


## 🔧 Usage

- Enter repo URL  
- Enter GitHub token  
- Choose base branch  
- Copy your pull request link  

---

- AI fixes are safe but should be reviewed manually  
---

- Full CI integration  
- Deeper semantic refactoring  

This tool aims to simplify open-source contributions by reducing the effort needed to prepare clean, patch-ready pull requests.
<img width="1024" height="1024" alt="Generated_Image_November_27_2025_-_11_43AM" src="https://github.com/user-attachments/assets/2417585d-8b32-483c-a470-7874d5a3ffcf" />

