# 08 — Quick Reference Card

**[← Code Review Checklist](07-code-review-checklist.md)** | **[← Home](../README.md)**

---

> Bookmark this page. It's everything you need in your daily workflow.

---

## Project Layout

```
my-project/
├── src/my_package/       ← ALL source code
│   ├── __init__.py       ← public API + __all__
│   ├── core.py
│   └── utils.py
├── tests/                ← ALL tests
│   ├── conftest.py       ← shared fixtures
│   ├── test_core.py
│   └── integration/
├── docs/                 ← MkDocs source
├── data/raw/             ← read-only inputs
├── data/processed/       ← outputs (.gitignored if large)
├── .venv/                ← NEVER commit
├── .gitignore
├── .python-version       ← commit this
├── pyproject.toml        ← single source of truth
├── requirements.txt      ← generated, pinned runtime
└── requirements-dev.txt  ← generated, pinned dev
```

---

## The Setup Sequence (Every Project, Every Time)

```bash
git clone https://github.com/org/my-project.git
cd my-project
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -v
```

---

## `pyproject.toml` Skeleton

```toml
[build-system]
requires      = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name            = "my-package"
version         = "0.1.0"
requires-python = ">=3.11"
dependencies    = ["requests>=2.31.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-cov>=5.0.0", "black>=24.0.0", "ruff>=0.4.0"]

[tool.setuptools.packages.find]
where = ["src"]           # ← critical

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts   = "-v --cov=my_package --cov-report=term-missing"
```

---

## Dependency Rules

```
pyproject.toml    → ranges   requests>=2.31.0     (what the package needs)
requirements.txt  → pins     requests==2.32.3     (what to actually install)

Generate requirements.txt:
  pip install -e . && pip freeze | grep -v "my-package" > requirements.txt

Audit for vulnerabilities:
  pip install pip-audit && pip-audit -r requirements.txt
```

---

## Import Order

```python
# ── 1. Standard library ────────────
import json
import logging
from pathlib import Path

# ── 2. Third-party ─────────────────
import pandas as pd
import requests

# ── 3. Local ───────────────────────
from my_package.cleaning import clean_email
```

---

## Import Rules

```
✅  Absolute imports always
✅  if __name__ == "__main__": on every runnable script
✅  logging instead of print()
✅  pathlib.Path instead of os.path strings

❌  from x import *    (banned, no exceptions)
❌  Relative imports   (avoid; justify with comment if used)
❌  Imports inside functions (except circular import avoidance)
❌  print() in library code
❌  Hardcoded paths (/Users/waqar/...)
❌  Secrets in source code
```

---

## Standard Library — Reach for These First

| Need | Module | Key tool |
|---|---|---|
| File paths | `pathlib` | `Path(__file__).parent / "data"` |
| Environment vars | `os` | `os.environ.get("KEY", "default")` |
| Dates and times | `datetime` | `datetime.now(tz=timezone.utc)` |
| JSON | `json` | `json.loads()` / `json.dumps(indent=2)` |
| CSV | `csv` | `csv.DictReader(f)` |
| Frequency count | `collections` | `Counter(items).most_common(10)` |
| Group-by | `collections` | `defaultdict(list)` |
| Lazy iteration | `itertools` | `chain()`, `islice()`, `batched()` |
| Caching | `functools` | `@lru_cache(maxsize=256)` |
| Pattern matching | `re` | Compile at module level |
| Structured output | `logging` | `logger = logging.getLogger(__name__)` |

---

## Logging Template

```python
# In library code — get, never configure
logger = logging.getLogger(__name__)

# In app entry point — configure once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-20s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# Log levels
logger.debug("Detailed diagnostic: %s", value)    # off in production
logger.info("Milestone: processed %d records", n) # normal operation
logger.warning("Unexpected but OK: %s", msg)      # recoverable
logger.error("Failed: %s", exc)                   # execution continues
logger.exception("Crash: %s", exc)                # includes traceback
```

---

## New Package Decision Tree

```
Need a package?
      │
      ▼
Standard library covers it? ──YES──▶ Use it.
      │
      NO
      ▼
Answer these 5 questions:
  1. Is it necessary?
  2. Is it maintained? (last release < 18 months)
  3. Is it secure? (pip-audit passes)
  4. Dep tree manageable? (pipdeptree)
  5. License OK? (MIT/Apache/BSD = approved)
      │
      ▼
Open PR with answers in description.
```

---

## Code Review — 10 Questions

| # | Check | Instant rejection condition |
|---|---|---|
| Q1 | `src/` layout | Flat layout (no `src/`) |
| Q2 | `pyproject.toml` complete | `setup.py` alongside `pyproject.toml` |
| Q3 | Tests in `tests/` | Tests inside `src/` |
| Q4 | `.venv` gitignored | `.venv/` committed to git |
| Q5 | Deps managed correctly | New dep, no explanation in PR |
| Q6 | Imports ordered | `ruff check .` fails |
| Q7 | No wildcards, absolute imports | `from x import *` anywhere |
| Q8 | `__main__` guard present | Side effects at import time |
| Q9 | Docstrings complete | Public function in `__all__` with no docstring |
| Q10 | Project reproducible | Hardcoded path or committed secret |

---

## Useful Commands

```bash
# Install + verify
pip install -e ".[dev]"
pytest -v

# Check imports
ruff --select I .

# Full lint
ruff check .

# Format
black .

# Type check
mypy src/

# Security audit
pip-audit -r requirements.txt

# Generate requirements.txt
pip freeze | grep -v "my-package" > requirements.txt

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Coverage report
pytest --cov=my_package --cov-report=html
open htmlcov/index.html
```

---

## `.gitignore` Minimum

```gitignore
.venv/
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
data/processed/
.DS_Store
```

---

*Full guide: [python-packaging-guide](../README.md)*
*Author: [Waqar Javed](https://github.com/iamwaqarjaved)*
