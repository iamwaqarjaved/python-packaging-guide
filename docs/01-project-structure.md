# 01 — Project Structure Standard

**[← Home](../README.md)** | **[Next: Virtual Environments →](02-virtual-environments.md)**

---

## The Core Idea

Every Python project you write should answer one question the same way:

> _"Can someone clone this repo, run three commands, and have everything working?"_

The `src/` layout — combined with `pyproject.toml` and editable installs — makes that answer **yes**, every time, for every project, on every machine.

---

## The Canonical Layout

```
my-project/
│
├── src/                          ← all importable source code lives here
│   └── my_package/
│       ├── __init__.py           ← package entry point; version, __all__, docstring
│       ├── core.py               ← primary business logic
│       ├── utils.py              ← shared helpers
│       └── models.py             ← data models / schemas
│
├── tests/                        ← all tests; mirrors src/ structure
│   ├── conftest.py               ← shared pytest fixtures
│   ├── test_core.py
│   ├── test_utils.py
│   └── integration/
│       └── test_end_to_end.py
│
├── docs/                         ← documentation source (MkDocs)
│   ├── index.md
│   └── guides/
│       └── quickstart.md
│
├── data/
│   ├── raw/                      ← read-only input data
│   ├── processed/                ← outputs; .gitignore'd if large
│   └── fixtures/                 ← small test data; always committed
│
├── scripts/                      ← operational scripts; never imported
│   └── seed_database.py
│
├── .venv/                        ← virtual environment; NEVER commit
├── .gitignore
├── .python-version               ← pins interpreter version for pyenv
├── pyproject.toml                ← single source of truth
├── requirements.txt              ← pinned runtime deps (generated)
├── requirements-dev.txt          ← pinned dev/test deps (generated)
└── README.md
```

---

## Why `src/`? The Bug It Prevents

The `src/` layout exists to solve one specific, silent, expensive bug: **accidental local imports**.

### What happens without `src/`

```
# ❌ Flat layout
my-project/
├── my_package/        ← exists on the filesystem right here
│   └── __init__.py
└── tests/
```

When you run `pytest` from `my-project/`, Python adds the current directory to `sys.path`. So `import my_package` resolves to the **local folder** — not the installed package. This means:

- Your tests import code that was never installed
- A bug that only appears when properly installed will never be caught in development
- `pip install -e .` and `import my_package` can silently refer to different things

### What happens with `src/`

```
# ✅ src/ layout
my-project/
├── src/
│   └── my_package/    ← NOT on sys.path directly
│       └── __init__.py
└── tests/
```

`my_package/` is inside `src/`, which is **not** on `sys.path` by default. The only way `import my_package` works is if the package is installed. Running `pip install -e .` installs it — and from that point on, tests and production imports go through the exact same path.

**The invariant:** your test environment and your production environment import the same artifact.

---

## The Role of `pyproject.toml`

`pyproject.toml` is the **single source of truth** for a Python project. It replaces every one of these older files:

| Old file | Replaced by `pyproject.toml` section |
|---|---|
| `setup.py` | `[build-system]` + `[project]` |
| `setup.cfg` | `[project]` |
| `MANIFEST.in` | `[tool.setuptools]` |
| `pytest.ini` | `[tool.pytest.ini_options]` |
| `.flake8` | `[tool.ruff]` |
| `mypy.ini` | `[tool.mypy]` |

### The Complete Template

```toml
# ── 1. Build system ────────────────────────────────────────────────────────
[build-system]
requires      = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

# ── 2. Project metadata (PEP 621) ──────────────────────────────────────────
[project]
name            = "my-package"
version         = "0.1.0"
description     = "One sentence. What it does, not what it is."
readme          = "README.md"
license         = { text = "MIT" }
authors         = [{ name = "Your Name", email = "you@example.com" }]
requires-python = ">=3.11"

# Runtime dependencies — use ranges, not pins (see doc 03)
dependencies = [
    "requests>=2.31.0",
    "pandas>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "black>=24.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

# ── 3. Tool configuration ───────────────────────────────────────────────────
[tool.setuptools.packages.find]
where = ["src"]        # ← THE critical line for the src/ layout

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts   = "-v --cov=my_package --cov-report=term-missing"

[tool.black]
line-length    = 96
target-version = ["py311"]

[tool.ruff]
line-length = 96
select      = ["E", "F", "I", "UP"]

[tool.mypy]
python_version         = "3.11"
strict                 = true
ignore_missing_imports = true
```

> **Key insight:** `where = ["src"]` in `[tool.setuptools.packages.find]` is what makes the `src/` layout work. Without it, setuptools won't find your package.

---

## Where Tests Live

Tests live in `tests/` at the project root — **never** inside `src/`.

### Mirroring the Source Structure

Each source module gets a corresponding test file:

```
src/my_package/core.py    →    tests/test_core.py
src/my_package/utils.py   →    tests/test_utils.py
src/my_package/models.py  →    tests/test_models.py
```

### `conftest.py` — Shared Fixtures

`tests/conftest.py` is loaded automatically by pytest. Put fixtures that multiple test files share here:

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_csv(tmp_path):
    """A small CSV file for testing cleaners."""
    f = tmp_path / "sample.csv"
    f.write_text("name,email\nAlice,alice@example.com\nBob,bob@example.com\n")
    return f

@pytest.fixture
def sample_df():
    """A minimal inventory DataFrame for testing."""
    import pandas as pd
    return pd.DataFrame([
        {"sku": "A1", "quantity": 10, "unit_price": 9.99},
        {"sku": "B2", "quantity":  0, "unit_price": 4.99},
    ])
```

### Integration Tests

Tests that hit the network, a database, or require external services go in `tests/integration/`:

```python
# tests/integration/test_weather_api.py
import pytest

@pytest.mark.integration
def test_live_weather_fetch():
    from my_package.weather import get_current_weather
    result = get_current_weather(latitude=25.96, longitude=-80.35)
    assert "temperature" in result
```

Exclude them from the default run, require explicit opt-in:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-v -m 'not integration'"
```

```bash
pytest          # unit tests only (fast)
pytest -m integration   # integration tests (slow, requires network)
```

---

## Where Docs Live

```
docs/
├── index.md           ← home page
├── api.md             ← auto-generated from docstrings
└── guides/
    ├── quickstart.md  ← "get something running in 5 minutes"
    └── configuration.md
```

Use **MkDocs** with the Material theme. Install and serve locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve    # live-reloading at http://localhost:8000
mkdocs build    # builds static site to site/
```

### Docstring Format — NumPy Style

Every public function needs a docstring. Use NumPy format:

```python
def clean_email(email: str) -> str:
    """Lowercase and validate an e-mail address.

    Parameters
    ----------
    email : str
        Raw e-mail string; leading/trailing whitespace is stripped.

    Returns
    -------
    str
        Normalized e-mail address in lowercase.

    Raises
    ------
    ValueError
        If the cleaned value does not contain exactly one ``@``.

    Examples
    --------
    >>> clean_email("  Alice@Example.COM  ")
    'alice@example.com'
    """
    cleaned = email.strip().lower()
    if cleaned.count("@") != 1:
        raise ValueError(f"Invalid email: {email!r}")
    return cleaned
```

---

## Where Data Lives

```
data/
├── raw/           ← original files; READ ONLY; commit if < 10 MB
├── processed/     ← pipeline outputs; .gitignore if large
├── fixtures/      ← small, stable test data; always committed
└── schemas/       ← JSON Schema or Pydantic model definitions
```

**The rules:**
- Never modify `data/raw/`. Pipelines write to `data/processed/`.
- Files > 10 MB → use DVC or S3, never git.
- Fixtures are always small and synthetic — never real customer data.

---

## Checklist for This Section

Before moving on, verify:

- [ ] Your project has a `src/my_package/` directory
- [ ] `pyproject.toml` has `[tool.setuptools.packages.find] where = ["src"]`
- [ ] Tests are in `tests/`, not in `src/`
- [ ] `tests/conftest.py` exists
- [ ] `pip install -e .` works without error

---

**[← Home](../README.md)** | **[Next: Virtual Environments →](02-virtual-environments.md)**
