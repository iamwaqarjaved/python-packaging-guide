# 03 — Dependency Management

**[← Virtual Environments](02-virtual-environments.md)** | **[Next: Standard Library →](04-standard-library.md)**

---

## The Problem Dependency Management Solves

You write code that works. Six months later, a teammate clones the repo, runs it, and gets errors — because `pandas` released version 3.0 and removed the API you were using. Or because a transitive dependency updated and changed its behavior.

Dependency management is how you prevent this. The goal: **anyone who installs your project gets the exact same environment you tested with**.

---

## The Two-File System

We maintain three separate dependency declarations, each with a distinct job:

```
pyproject.toml            → what your package NEEDS (ranges)
requirements.txt          → what to install in production (exact pins)
requirements-dev.txt      → what developers need (exact pins + dev tools)
```

Think of it this way:

```
pyproject.toml says:   "I need requests, at least version 2.31"
requirements.txt says: "Install requests 2.32.3 exactly"
```

These serve different audiences. `pyproject.toml` talks to other packages and pip's resolver. `requirements.txt` talks to CI/CD and Docker — it says "reproduce this exact state".

---

## `pyproject.toml` — Ranges (Flexible)

In `pyproject.toml`, declare what your package **needs to work**, using ranges:

```toml
[project]
dependencies = [
    "requests>=2.31.0",     # minimum bound — any 2.31+ works
    "pandas>=2.1.0",        # minimum bound
    "click>=8.0.0",
]
```

### Version Specifiers

| Style | Example | Meaning | Use when |
|---|---|---|---|
| Minimum bound | `requests>=2.31.0` | 2.31 or higher | `pyproject.toml` — your package |
| Exact pin | `requests==2.32.3` | exactly 2.32.3 | `requirements.txt` — deployments |
| Compatible release | `requests~=2.31` | >=2.31, <3.0 | Libraries with stable APIs |
| Upper bound | `requests>=2.31,<3.0` | range with ceiling | When you know v3 breaks things |
| No constraint | `requests` | anything | **Never. Always add a minimum.** |

### Why Not Pin in `pyproject.toml`?

If you publish a library and pin `requests==2.32.3`, every project that depends on yours **must** use exactly that requests version. If they need `requests==2.31.0` for another reason, the install fails.

Ranges let pip negotiate. Your package gets a compatible version; so does everything else.

---

## `requirements.txt` — Exact Pins (Reproducible)

`requirements.txt` is **generated**, not hand-edited. It contains every runtime dependency — direct and transitive — pinned to exact versions:

```bash
# Generate: install, then freeze
pip install -e .
pip freeze | grep -v "my-package" > requirements.txt
```

The result:

```
# requirements.txt — GENERATED — do not edit manually
# Generated: 2026-06-24
requests==2.32.3
pandas==2.2.2
numpy==1.26.4
urllib3==2.2.1
certifi==2024.2.2
charset-normalizer==3.3.2
idna==3.7
python-dateutil==2.9.0
pytz==2024.1
six==1.16.0
```

> **Rule:** If you see a handwritten `requirements.txt` with only the top-level packages and no transitive deps, it's incomplete. Regenerate it properly.

---

## `requirements-dev.txt` — Development Dependencies

```
# requirements-dev.txt
# Install with: pip install -r requirements-dev.txt

-r requirements.txt     ← inherit all runtime deps first

# Testing
pytest==8.2.2
pytest-cov==5.0.0
pytest-mock==3.14.0
coverage==7.5.3

# Code quality
black==24.4.2
ruff==0.4.9
mypy==1.10.0
types-requests==2.32.0.20240523

# Documentation
mkdocs==1.6.0
mkdocs-material==9.5.18
```

The `-r requirements.txt` line means a developer runs **one command** and gets everything:

```bash
pip install -r requirements-dev.txt
# → installs runtime deps + dev tools
```

---

## The Pinned vs Floating Decision

```
┌─────────────────────────────────────────────────────────────┐
│                    WHICH FILE?                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Adding a runtime dep?                                      │
│  → pyproject.toml [dependencies]  with ranges (>=x.y)      │
│  → run pip freeze to update requirements.txt                │
│                                                             │
│  Adding a dev/test dep?                                     │
│  → pyproject.toml [project.optional-dependencies.dev]       │
│  → run pip freeze to update requirements-dev.txt            │
│                                                             │
│  Deploying to production?                                   │
│  → pip install -r requirements.txt  (exact pins)            │
│                                                             │
│  Setting up a dev environment?                              │
│  → pip install -e ".[dev]"  (lets pip resolve ranges)       │
│  → or pip install -r requirements-dev.txt  (exact pins)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Security Trade-Off

Pinned versions give you reproducibility. The cost: you won't automatically receive security patches. Manage this with three practices:

### 1. Dependabot (Automated PRs)

Add `.github/dependabot.yml` to your repo:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

Dependabot opens PRs when security patches are available. Review and merge them.

### 2. `pip-audit` in CI

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

Add to your CI pipeline. It scans against the OSV vulnerability database and fails the build if high/critical vulnerabilities are found.

```yaml
# .github/workflows/security.yml
- name: Security audit
  run: |
    pip install pip-audit
    pip-audit -r requirements.txt --severity high
```

### 3. Response Time Policy

| Severity | Required response |
|---|---|
| Critical | Update within 24 hours |
| High | Update within 72 hours |
| Medium | Update in next scheduled maintenance |
| Low | Track; address when convenient |

---

## When to Use `uv` or `poetry`

`pip` + `pyproject.toml` is the default. Consider alternatives only when there is a specific, documented need:

### `uv` — Ultra-fast Package Installer

```bash
pip install uv
uv pip install -e ".[dev]"   # same interface as pip, 10-100x faster
```

Use `uv` when:
- CI is slow because of pip install times
- You're working in a large monorepo with many packages
- You want faster local installs during development

Don't use it when the team is unfamiliar — the speed gain isn't worth confusion.

### `poetry` — All-in-One for Library Publishing

```bash
pip install poetry
poetry new my-package
poetry add requests
poetry publish
```

Use `poetry` when:
- You're publishing a library to PyPI
- You want automatic version management and changelog generation
- The whole team agrees to adopt it

Avoid it for simple applications — it adds significant complexity for marginal gain.

### `pip-tools` — Automated `requirements.txt` Generation

```bash
pip install pip-tools
pip-compile pyproject.toml               # → requirements.txt
pip-compile --extra dev pyproject.toml   # → requirements-dev.txt
```

Use `pip-tools` when you want the `requirements.txt` generation automated and committed to git with a clear audit trail. Good middle ground between raw pip and poetry.

---

## Regenerating Requirements Files

Whenever you add, remove, or update a dependency:

```bash
# 1 — Update pyproject.toml with the new/changed dep
# 2 — Reinstall
pip install -e ".[dev]"

# 3 — Regenerate pinned files
pip freeze | grep -v "$(python -c 'import my_package; print(my_package.__name__)')" > requirements.txt

# 4 — Commit both pyproject.toml and requirements.txt together
git add pyproject.toml requirements.txt requirements-dev.txt
git commit -m "deps: add requests>=2.31.0 for HTTP client"
```

---

## Checklist for This Section

- [ ] `pyproject.toml` uses version ranges (`>=`), not pins
- [ ] `requirements.txt` is generated, not hand-edited
- [ ] `requirements-dev.txt` starts with `-r requirements.txt`
- [ ] `pip-audit` passes on `requirements.txt`
- [ ] Dependabot is configured (or equivalent)
- [ ] Any new packages added are explained in the commit message

---

**[← Virtual Environments](02-virtual-environments.md)** | **[Next: Standard Library →](04-standard-library.md)**
