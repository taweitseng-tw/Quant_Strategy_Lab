# Task 055C - Git Repository Setup Readiness

## Current Workspace State
An audit of the `D:\Quant_Strategy_Lab` workspace confirms that **Git is currently not initialized**. There is no `.git` directory present. The workspace contains a mix of source code (`app`, `core`, `strategy_engine`, `reports`, etc.), virtual environment files (`.venv`), IDE configurations (`.idea`), and large user/data files (`TXF.txt`, local project outputs like `data/`, `logs/`, `strategies/`, and `project_reports/`).

## Why Git Matters for the Semi-Automated Agent Workflow
The Quant Strategy Lab is being developed iteratively by multiple agents (Codex, Anti-Gravity, DeepSeek) through a shared task queue (`docs/agent_queue/current_task.md`) and task board. Currently, tracking changes relies heavily on manual changelog updates and `agent_status.ps1` reading file modification times. 
Initializing a Git repository will provide:
- **Safety Nets**: The ability to quickly revert a workspace if an agent makes a destructive error.
- **Diffing and Code Review**: Clear `git diff` outputs for Codex to review Anti-Gravity/DeepSeek implementations before acceptance.
- **Workflow Automation**: `agent_status.ps1` will be able to query the active branch and uncommitted changes rather than falling back to timestamps.
- **Traceability**: Linking changelog items to specific Git commits for long-term project health.

## Files and Directories Needing Ignore Rules
Before running `git init`, it is critical to construct a robust `.gitignore` file. If Git is initialized in the current dirty state without ignore rules, it will attempt to track massive data files and ephemeral outputs, risking repository bloat and severe performance degradation.

The following items should be ignored:
1. **Python Environment**: `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `uv.lock`
2. **IDE Configurations**: `.idea/`, `.vscode/`
3. **Large Raw Data**: `TXF.txt` (250MB+) and any `.csv`, `.parquet` files.
4. **Local Project Outputs**: 
   - `data/` (raw, normalized, resampled)
   - `strategies/` (archived, generated, passed)
   - `exports/`
   - `logs/`
   - `project_reports/` (this is where generated HTML/Markdown reports go, distinct from the root `reports/` source package)
   - `project.sqlite`
   - `config/` (user-specific app settings)
   - Ephemeral testing/scratch files like `pytest_out.txt`, `pytest_full.txt`, `test.pdf`, `scratch_clean.py`, and test project folders (`1/`, `2/`, `app/test1/`, `virtual/`).
5. **Binaries**: `codewhale-tui-windows-x64.exe`

### Do Not Ignore Source Packages
It is critical that you do **not** add ignore rules for the root packages that contain the Quant Strategy Lab application logic. These must be tracked by Git:
- `app/`
- `core/`
- `data_engine/`
- `strategy_engine/`
- `backtest_engine/`
- `validation_engine/`
- `repository/`
- `reports/` (Note: This is the Python source code for generating reports, not the generated outputs themselves.)
- `tests/`

## Proposed `.gitignore` Draft

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
.pytest_cache/
uv.lock

# IDEs
.idea/
.vscode/

# Build & Dependencies
build/
dist/
*.egg-info/

# Data & Large Files
*.csv
*.parquet
*.txt
!requirements.txt
# Explicitly ignore the massive local tick file.
TXF.txt

# Local QSL Project Storage
project.sqlite
data/
strategies/
exports/
logs/
project_reports/
config/

# Ephemeral & Scratch
scratch*.py
pytest*.txt
test.pdf
1/
2/
virtual/
app/test1/

# Binaries
*.exe
```

## Risks of Initializing Git in a Dirty Workspace
1. **Accidental Tracking of Bloat**: Running `git add .` before `.gitignore` is created and verified will stage the 250MB `TXF.txt` and the entire `.venv` directory, bloating the `.git` database immediately.
2. **Secrets Leakage**: If API keys or broker credentials exist in `config/app_settings.json`, they could be permanently recorded in the commit history.
3. **Performance**: A massive untracked workspace can slow down standard `git status` commands, which `agent_status.ps1` will start relying on.

## Manual Commands for the User
The user should run these commands manually in PowerShell at the root of `D:\Quant_Strategy_Lab` when ready to proceed:

```powershell
# 1. Create the .gitignore file first (copy the draft above into it)
notepad .gitignore

# 2. Initialize the repository
git init

# 3. Verify that the output of git status is clean and does NOT list TXF.txt or .venv/
git status

# 4. Stage the project files
git add .

# 5. Create the initial commit
git commit -m "Initial commit: Pre-v0.2 Baseline"
```
