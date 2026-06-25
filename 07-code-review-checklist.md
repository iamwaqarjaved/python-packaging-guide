# 07 — Code Review Checklist

**[← Third-Party Packages](06-third-party-packages.md)** | **[Next: Quick Reference →](08-quick-reference.md)**

---

## How to Use This Checklist

Run through this list on every PR that touches Python project structure, packaging, imports, or dependencies. Copy it into your PR review comments. Items marked **INSTANT REJECTION** do not require discussion — the PR is sent back without merge.

A PR is not "ready to merge" until all 10 questions have a passing answer.

---

## Q1 — Does the project use the `src/` layout?

```
src/my_package/   ← source code lives here
tests/            ← tests live here
pyproject.toml    ← [tool.setuptools.packages.find] where = ["src"]
```

**Check:**
- [ ] All importable source code is under `src/my_package/`
- [ ] No runnable `.py` files at the project root except `app.py`, `main.py`, or scripts in `scripts/`
- [ ] `pyproject.toml` contains `where = ["src"]` under `[tool.setuptools.packages.find]`
- [ ] `pip install -e .` works without error from a fresh clone

**INSTANT REJECTION:** Source code is at the project root (flat layout) with no `src/` directory.

---

## Q2 — Is `pyproject.toml` complete and correct?

**Check:**
- [ ] `[build-system]` section present with `setuptools>=68` and `wheel`
- [ ] `[project]` has `name`, `version`, `requires-python`, `description`, `dependencies`
- [ ] Runtime dependencies use version **ranges** (`>=`), not exact pins
- [ ] Tool config (`pytest`, `black`, `ruff`, `mypy`) is in `pyproject.toml`, not separate config files
- [ ] No `setup.py` or `setup.cfg` present alongside `pyproject.toml`

**Quick audit:**

```bash
# Should show your package name and version
python -c "import importlib.metadata; print(importlib.metadata.version('my-package'))"

# Should find no setup.py
ls setup.py 2>/dev/null && echo "FAIL: setup.py exists" || echo "OK"
```

**INSTANT REJECTION:** Both `setup.py` and `pyproject.toml` exist in the same project.

---

## Q3 — Are tests correctly located and structured?

**Check:**
- [ ] All tests are in `tests/` — never inside `src/`
- [ ] Test file naming: `test_<module>.py` — never just `test.py`
- [ ] Each source module has a corresponding test file
- [ ] `tests/conftest.py` exists (even if empty)
- [ ] Integration tests are in `tests/integration/` and marked `@pytest.mark.integration`
- [ ] `pytest -v` passes with no errors on a fresh install

**Verify structure:**

```bash
# Should show tests/ at root, not inside src/
find . -name "test_*.py" | grep -v ".venv"
```

**INSTANT REJECTION:** Test files are inside `src/` or co-located with source files.

---

## Q4 — Is the virtual environment correctly configured?

**Check:**
- [ ] `.venv/` is listed in `.gitignore`
- [ ] `README.md` includes the four-step setup sequence (clone → venv → install → test)
- [ ] `.python-version` is present and committed
- [ ] `pip install -e ".[dev]"` + `pytest -v` works from a fresh clone
- [ ] No `requirements.txt` contains the package itself

**Verify .gitignore:**

```bash
git check-ignore -v .venv/
# Should output: .gitignore:1:.venv/    .venv/
```

**INSTANT REJECTION:** `.venv/` is tracked by git (`git ls-files .venv` returns any output).

---

## Q5 — Are dependencies correctly managed?

**Check:**
- [ ] `requirements.txt` contains only exact pins (`==`), not ranges
- [ ] `requirements.txt` includes transitive dependencies (generated, not hand-written)
- [ ] `requirements-dev.txt` begins with `-r requirements.txt`
- [ ] `pyproject.toml [dependencies]` uses only ranges, not pins
- [ ] `pip-audit -r requirements.txt` passes with no high/critical vulnerabilities
- [ ] Any new packages added in this PR are documented in the PR description

**Verify with pip-audit:**

```bash
pip install pip-audit
pip-audit -r requirements.txt
# Should output: No known vulnerabilities found
```

**INSTANT REJECTION:** A new package was added to `requirements.txt` with no entry in `pyproject.toml` and no explanation in the PR description.

---

## Q6 — Are imports correctly ordered and grouped?

Imports must follow the three-group order:

```python
# Group 1 — stdlib
import json
from pathlib import Path

# Group 2 — third-party
import pandas as pd

# Group 3 — local
from my_package.cleaning import clean_email
```

**Check:**
- [ ] Three-group order: stdlib → third-party → local
- [ ] Groups separated by exactly one blank line
- [ ] No imports inside functions (unless avoiding circular imports, with a comment)
- [ ] `ruff --select I .` returns zero violations

**Run the linter:**

```bash
ruff --select I .
# Any output = fail
```

**INSTANT REJECTION:** `ruff check .` (full lint) returns errors.

---

## Q7 — Are all imports absolute? Are wildcards absent?

**Check:**
- [ ] All imports use the full dotted path (`from my_package.x import y`)
- [ ] Zero wildcard imports (`from x import *`) anywhere in the diff
- [ ] Any relative imports are justified with an inline comment
- [ ] `grep -r "import \*" src/ tests/` returns nothing

**Search for wildcards:**

```bash
grep -rn "from .* import \*" src/ tests/
# Any output = INSTANT REJECTION
```

**INSTANT REJECTION:** Any `from x import *` anywhere in the repository.

---

## Q8 — Do all runnable scripts use the `__main__` guard?

**Check:**
- [ ] Every file that can be run directly has `if __name__ == "__main__":`
- [ ] The `__main__` block contains only function calls, not logic
- [ ] The functions called from `__main__` are importable and testable independently
- [ ] No side effects execute at module import time (no HTTP calls, no file writes, no `print()`)

**Test the guard:**

```bash
# This should import cleanly with no side effects
python -c "import my_package.pipeline"
# If it prints anything or makes network calls, the guard is missing or broken
```

**INSTANT REJECTION:** A module executes side effects (network calls, file writes, print statements) at import time.

---

## Q9 — Are docstrings present and correctly formatted?

**Check:**
- [ ] Every public function and class has a docstring
- [ ] Docstrings follow NumPy format (Parameters / Returns / Raises / Examples)
- [ ] `__init__.py` has a package-level docstring
- [ ] `help(my_package)` produces useful output (verify in REPL)
- [ ] Private functions (`_name`) have at minimum a one-line docstring

**Spot-check in the REPL:**

```python
import my_package
help(my_package)             # should show meaningful description
help(my_package.clean_email) # should show Parameters, Returns, Examples
```

**INSTANT REJECTION:** A public function listed in `__all__` has no docstring.

---

## Q10 — Does the PR leave the project reproducible?

**Check:**
- [ ] A fresh clone + `pip install -e ".[dev]"` + `pytest -v` passes with zero errors
- [ ] No hardcoded absolute paths (search: `/Users/`, `/home/`, `C:\Users\`)
- [ ] All file paths use `pathlib.Path`, not string concatenation
- [ ] `logging` is used instead of `print()` in all non-interactive code
- [ ] All environment-specific values (secrets, URLs, API keys) come from environment variables

**Search for hardcoded paths:**

```bash
grep -rn "/Users/" src/ tests/
grep -rn "/home/" src/ tests/
grep -rn "C:\\\\Users\\\\" src/ tests/
# Any output = INSTANT REJECTION
```

**Search for committed secrets:**

```bash
grep -rn "API_KEY\s*=" src/ tests/ --include="*.py" | grep -v "os.environ"
grep -rn "PASSWORD\s*=" src/ tests/ --include="*.py" | grep -v "os.environ"
# Any output = INSTANT REJECTION
```

**INSTANT REJECTION:** A hardcoded path or secret is anywhere in the diff. No discussion needed.

---

## Summary — Instant Rejection Conditions

| Condition | Where to look |
|---|---|
| Flat layout (no `src/`) | Project root |
| `setup.py` alongside `pyproject.toml` | Project root |
| Tests inside `src/` | `find src/ -name "test_*.py"` |
| `.venv/` tracked by git | `git ls-files .venv` |
| `from x import *` anywhere | `grep -rn "import \*" src/ tests/` |
| Side effects at import time | `python -c "import my_package"` |
| Public function with no docstring | Check `__all__` in `__init__.py` |
| Hardcoded path | `grep -rn "/Users/" src/ tests/` |
| Committed secret | `grep -rn "API_KEY\s*=" src/ tests/` |
| `pip-audit` fails | `pip-audit -r requirements.txt` |

---

## Copy-Paste Review Comment

When a PR fails, paste this into the review comment:

```markdown
## Code Review — Structure & Packaging Check

- [ ] Q1: src/ layout ✅ / ❌ [reason]
- [ ] Q2: pyproject.toml complete ✅ / ❌ [reason]
- [ ] Q3: tests in tests/ ✅ / ❌ [reason]
- [ ] Q4: .venv .gitignore'd ✅ / ❌ [reason]
- [ ] Q5: deps correctly managed ✅ / ❌ [reason]
- [ ] Q6: imports ordered ✅ / ❌ [reason]
- [ ] Q7: no wildcards, absolute imports ✅ / ❌ [reason]
- [ ] Q8: __main__ guard present ✅ / ❌ [reason]
- [ ] Q9: docstrings complete ✅ / ❌ [reason]
- [ ] Q10: project reproducible ✅ / ❌ [reason]

See [Code Review Checklist](docs/07-code-review-checklist.md) for fix instructions.
```

---

**[← Third-Party Packages](06-third-party-packages.md)** | **[Next: Quick Reference →](08-quick-reference.md)**
