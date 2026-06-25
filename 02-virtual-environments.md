# 02 — Virtual Environments

**[← Project Structure](01-project-structure.md)** | **[Next: Dependency Management →](03-dependency-management.md)**

---

## Why Virtual Environments Exist

Python has one global `site-packages` directory per interpreter. Without virtual environments, every project on your machine shares that same directory. This means:

- Project A needs `requests==2.28` → installs it globally
- Project B needs `requests==2.32` → overwrites it
- Project A breaks

Virtual environments solve this by giving each project its own isolated copy of `site-packages`. The project's environment knows nothing about any other project's environment.

```
Without venv:                    With venv:
                                
System Python                   System Python
└── site-packages/              ├── project-a/.venv/
    ├── requests 2.28  ← ??    │   └── site-packages/
    └── requests 2.32  ← ??    │       └── requests 2.28  ✅
                                └── project-b/.venv/
                                    └── site-packages/
                                        └── requests 2.32  ✅
```

---

## The Policy

**Every Python project has exactly one virtual environment. No exceptions.**

| Rule | Rationale |
|---|---|
| One `.venv/` per project | Isolates dependencies; prevents version conflicts |
| Always named `.venv/` | Consistent; IDEs find it automatically |
| Always `.gitignore`'d | Contains compiled binaries; platform-specific; regeneratable |
| README must document setup | Reproducibility; anyone can run it from scratch |

---

## Creating and Activating

### Step 1 — Create

```bash
# Always from the project root
python -m venv .venv
```

This creates `.venv/` with its own Python interpreter and `pip`.

### Step 2 — Activate

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate

# Windows CMD
.venv\Scripts\activate.bat
```

After activation, your prompt shows `(.venv)`:

```
(.venv) waqarjaved@MacBookPro my-project %
```

### Step 3 — Confirm You're in the Right Environment

```bash
which python       # macOS/Linux → should show .venv/bin/python
where python       # Windows → should show .venv\Scripts\python.exe
python --version   # should match requires-python in pyproject.toml
pip --version      # should show pip from .venv
```

### Step 4 — Install the Project

```bash
# Install your package + all dev tools in one command
pip install -e ".[dev]"
```

The `-e` flag means **editable mode** — changes to your source code take effect immediately without reinstalling. This is the standard workflow for development.

### Step 5 — Deactivate When Done

```bash
deactivate
```

---

## The Standard README Setup Block

Every project's `README.md` must include this section verbatim (adapted for the project name):

````markdown
## Setup

```bash
# 1 — Clone
git clone https://github.com/your-org/my-project.git
cd my-project

# 2 — Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3 — Install package in editable mode with dev tools
pip install -e ".[dev]"

# 4 — Verify everything works
python -c "import my_package; print(my_package.__version__)"
pytest -v
```
````

Anyone who clones your repo should be able to run these four steps and have a working development environment. If they can't, the README is incomplete.

---

## The Required `.gitignore`

Every project must have a `.gitignore` that includes at minimum:

```gitignore
# ── Virtual environment ────────────────────────────────────────────────────
.venv/
venv/
env/
ENV/
.env

# ── Python bytecode ────────────────────────────────────────────────────────
__pycache__/
*.py[cod]
*$py.class
*.pyo

# ── Package build artifacts ────────────────────────────────────────────────
*.egg-info/
*.egg
dist/
build/

# ── Test & coverage ────────────────────────────────────────────────────────
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml

# ── Type checkers & linters ────────────────────────────────────────────────
.mypy_cache/
.ruff_cache/
.dmypy.json

# ── Data (large files) ────────────────────────────────────────────────────
data/processed/
*.parquet
*.csv.gz

# ── OS files ──────────────────────────────────────────────────────────────
.DS_Store
Thumbs.db

# ── IDE ───────────────────────────────────────────────────────────────────
.idea/
.vscode/
*.swp
```

---

## Python Version Management with `pyenv`

Different projects need different Python versions. Use `pyenv` to manage this cleanly.

### Install pyenv

```bash
# macOS (via Homebrew)
brew install pyenv

# Linux
curl https://pyenv.run | bash

# Windows — use pyenv-win
pip install pyenv-win --target $HOME\.pyenv
```

### Install a Python Version

```bash
pyenv install 3.11.9
pyenv install 3.12.3
```

### Pin the Version Per Project

Create `.python-version` in the project root:

```
3.11.9
```

Commit this file. When a teammate with `pyenv` installed enters the directory, their shell automatically uses the correct Python version:

```bash
cd my-project
python --version   # → Python 3.11.9  (from .python-version)
```

### The Complete Flow

```bash
# One-time: install the right Python
pyenv install 3.11.9

# Per project
cd my-project
pyenv local 3.11.9          # creates .python-version
python -m venv .venv        # uses the pyenv Python
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Common Problems and Fixes

### `pip install` installs to the wrong place

**Symptom:** Installing a package, but it's not importable.

**Fix:** You forgot to activate the venv.

```bash
source .venv/bin/activate   # then retry pip install
```

### `python` resolves to the system Python, not `.venv`

**Symptom:** `which python` shows `/usr/bin/python` instead of `.venv/bin/python`

**Fix:** The venv isn't activated.

```bash
source .venv/bin/activate
```

### `ModuleNotFoundError` after cloning a repo

**Symptom:** `from my_package import clean_email` → `ModuleNotFoundError`

**Fix:** You haven't installed the package. Run:

```bash
pip install -e ".[dev]"
```

### `.venv/` accidentally committed to git

**Fix:**

```bash
echo ".venv/" >> .gitignore
git rm -r --cached .venv/
git commit -m "chore: remove .venv from git tracking"
```

---

## Checklist for This Section

- [ ] `.venv/` created at project root
- [ ] `.venv/` listed in `.gitignore`
- [ ] `pip install -e ".[dev]"` runs without error
- [ ] `pytest -v` passes
- [ ] README documents the setup sequence
- [ ] `.python-version` committed with the correct interpreter version

---

**[← Project Structure](01-project-structure.md)** | **[Next: Dependency Management →](03-dependency-management.md)**
