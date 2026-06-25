# 05 — Import Style Standards

**[← Standard Library](04-standard-library.md)** | **[Next: Third-Party Packages →](06-third-party-packages.md)**

---

## Why Import Style Matters

Imports are the first thing a reviewer reads. A consistent, predictable import block signals that the author understands the codebase structure and cares about maintainability. An inconsistent block — mixed order, wildcard imports, hidden dependencies — signals the opposite.

These standards are enforced by `ruff` in CI. But understanding *why* the rules exist makes you a better developer than any linter can.

---

## Import Order — Three Groups

Imports are divided into exactly three groups, in this order, separated by blank lines:

```python
# ── Group 1: Standard library ──────────────────────────────────────────────
import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Group 2: Third-party packages ─────────────────────────────────────────
import pandas as pd
import requests
from pydantic import BaseModel, Field

# ── Group 3: Local / internal ─────────────────────────────────────────────
from my_package.cleaning import clean_email, clean_phone
from my_package.models import Record, User
from my_package.utils import format_currency
```

### The Rules Within Each Group

1. `import x` lines before `from x import y` lines
2. Alphabetical order within each style
3. No blank lines within a group
4. One blank line between groups

`ruff` enforces this automatically. Run `ruff --select I .` to check import order.

---

## Absolute vs. Relative Imports

### Absolute Imports — Always Use These

An **absolute import** uses the full dotted path from the package root:

```python
from my_package.cleaning import clean_email
from my_package.models import User
from my_package.utils import format_date
```

Absolute imports are unambiguous. They work from any directory, in any context — tests, scripts, REPLs, and production code alike.

### Relative Imports — Avoid

A **relative import** uses `.` to express position relative to the current file:

```python
from .cleaning import clean_email   # one level up
from ..utils import format_date     # two levels up
```

Relative imports are problematic because:

- They break when you move a file to a different directory
- They don't work in scripts run directly (`python my_package/core.py`)
- They're harder to grep for across a large codebase
- They confuse new contributors who don't know the directory structure

**When relative imports are permitted:** inside a tight package where the relative relationship is stable and documented. A comment must explain why.

```python
# ✅ Acceptable relative import — within a sub-package
# Using relative import here because these modules are always co-located
from .validators import validate_email
```

### The Test

If you can't tell which module a name came from by reading the import block, the import is wrong. Absolute imports pass this test. Wildcard imports fail it completely.

---

## The Wildcard Import Ban

`from module import *` is **banned**. No exceptions. No "just this once."

```python
# ❌ Banned — always, everywhere
from os.path import *
from numpy import *
from my_package.constants import *
```

### Why It's Banned

**1. Namespace pollution.** Every name in the imported module lands in your namespace. You have no idea what's there.

```python
from os.path import *   # imports: join, exists, dirname, basename,
                        # abspath, split, splitext, expanduser,
                        # isfile, isdir, isabs, normpath, ...
                        # How many of these did you want?
```

**2. Hidden coupling.** Your code depends on names you didn't explicitly import. If the upstream module removes a name, your code breaks with no indication of which import caused it.

**3. Tool blindness.** `ruff`, `mypy`, and IDEs cannot resolve names imported by `*`. Autocomplete, go-to-definition, and rename refactoring all break.

**4. Review opacity.** A reviewer sees `clean_email(raw)` and cannot tell where `clean_email` came from. This slows code review and hides bugs.

### The Fix — Always Explicit

```python
# ✅ Import what you need, explicitly
from my_package.constants import MAX_RETRIES, DEFAULT_TIMEOUT, BASE_URL

# ✅ Or import the module and use the dot
import my_package.constants as const
result = const.MAX_RETRIES
```

---

## The `if __name__ == '__main__'` Guard

Every Python file that can be run directly **must** have this guard. Without it, importing the module executes the script.

### What Happens Without the Guard

```python
# ❌ No guard — dangerous
import requests

data = requests.get("https://api.example.com/data").json()  # executes on import!
print(data)
```

When a test imports this module — or when another module imports it — it fires an HTTP request. This is a silent, hard-to-debug bug.

### The Correct Pattern

```python
# src/my_package/pipeline.py

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    """Main pipeline logic — importable, testable, and pure.

    Parameters
    ----------
    input_dir : Path
        Directory containing raw input files.
    output_dir : Path
        Directory where processed output will be written.

    Returns
    -------
    dict
        Summary statistics: records processed, errors, duration.
    """
    logger.info("Starting pipeline: %s → %s", input_dir, output_dir)
    # ... actual logic here ...
    return {"processed": 1000, "errors": 2}


if __name__ == "__main__":
    # This block runs ONLY when the script is called directly:
    #   python -m my_package.pipeline /input /output
    #   python src/my_package/pipeline.py /input /output
    #
    # It does NOT run when imported by tests or other modules.

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 3:
        print("Usage: pipeline.py <input_dir> <output_dir>", file=sys.stderr)
        sys.exit(1)

    stats = run_pipeline(
        input_dir=Path(sys.argv[1]),
        output_dir=Path(sys.argv[2]),
    )
    print(f"Done: {stats}")
```

### The Three-Part Rule

1. **All logic in functions** — importable, testable, reusable
2. **`__main__` block only wires CLI to functions** — no logic in the block itself
3. **Functions work without the `__main__` block** — tests can call them directly

---

## `__init__.py` — Designing the Public API

`__init__.py` defines what the outside world sees when they `import my_package`. Use it deliberately.

### What to Export

Export only the names that form a stable public interface. Everything else is internal — subject to change without notice.

```python
# src/my_package/__init__.py
"""
my_package — brief one-line description.

This package provides tools for normalizing and analysing data.
Import from here for the stable public interface.

Quick Start
-----------
>>> from my_package import clean_email, summarize_inventory
>>> clean_email("  Alice@Example.COM  ")
'alice@example.com'
"""

from importlib.metadata import PackageNotFoundError, version

# Import from submodules to expose at the top level
from my_package.cleaning import clean_csv, clean_email, clean_phone
from my_package.inventory import flag_low_stock, summarize_inventory
from my_package.models import Record, User

try:
    __version__ = version("my-package")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

__author__ = "Your Name"

# __all__ is the contract: these names are stable and public
# Names not in __all__ are considered internal even if importable
__all__ = [
    "clean_csv",
    "clean_email",
    "clean_phone",
    "flag_low_stock",
    "summarize_inventory",
    "Record",
    "User",
]
```

### The Public / Private Naming Convention

```python
# Public — in __all__, stable, documented
def clean_email(email: str) -> str: ...
class User: ...

# Private — NOT in __all__, may change, one-liner docstring minimum
def _normalize_whitespace(s: str) -> str: ...
def _validate_schema(data: dict) -> bool: ...
```

---

## Type Hints — Write Them

Type hints are not optional. They serve as machine-readable documentation, enable `mypy` static analysis, and make IDEs useful.

```python
# ✅ With type hints
def clean_email(email: str) -> str: ...
def process_records(records: list[dict[str, str]], limit: int = 100) -> pd.DataFrame: ...
def load_config(path: Path | None = None) -> dict[str, Any]: ...

# ❌ Without type hints — no mypy, no autocomplete, no documentation
def clean_email(email): ...
def process_records(records, limit=100): ...
```

For Python 3.10+, use `X | Y` for unions. For older versions, use `Optional[X]` from `typing`.

---

## Import Checklist

Before committing:

- [ ] Imports are in three groups: stdlib → third-party → local
- [ ] Groups are separated by blank lines
- [ ] No wildcard imports (`from x import *`) anywhere
- [ ] All imports are absolute (or relative imports are justified with a comment)
- [ ] Every runnable script has `if __name__ == "__main__":`
- [ ] `__init__.py` has `__all__` listing the public API
- [ ] `ruff --select I .` shows no violations

---

**[← Standard Library](04-standard-library.md)** | **[Next: Third-Party Packages →](06-third-party-packages.md)**
