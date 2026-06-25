# 06 — Third-Party Package Policy

**[← Import Standards](05-import-standards.md)** | **[Next: Code Review Checklist →](07-code-review-checklist.md)**

---

## The Principle

Adding a dependency is a **decision**, not a reflex. Every package you add:

- Increases your attack surface (security vulnerabilities)
- Adds a maintenance burden (security updates, breaking changes)
- Creates a trust relationship with an external maintainer
- Increases install time for every developer and CI run

Before `pip install anything`, spend 60 seconds asking whether it's actually necessary.

---

## Step 0 — Check the Standard Library First

Python's standard library is large. Many common tasks that developers reach for packages to solve are already covered:

| Task | Standard library solution |
|---|---|
| HTTP requests (simple) | `urllib.request` |
| File paths | `pathlib` |
| CSV reading/writing | `csv` |
| JSON encoding/decoding | `json` |
| Date/time handling | `datetime` |
| Regex | `re` |
| Argument parsing | `argparse` |
| Hashing | `hashlib` |
| Compression | `gzip`, `zipfile` |
| Temporary files | `tempfile` |
| Data structures | `collections` |
| Functional tools | `functools`, `itertools` |
| Logging | `logging` |
| Running subprocesses | `subprocess` |
| Unit testing | `unittest` (though we use pytest) |

If the standard library covers your use case, use it. No new dependency needed.

---

## The 5-Question Review

If the standard library doesn't cover it, answer these five questions before adding the package:

### Question 1 — Is It Necessary?

Be honest. Is this package solving a real problem, or is it convenient? Could you implement the specific function you need in 20 lines of standard library code?

```python
# Before adding "humanize" for this:
from humanize import naturalsize
naturalsize(1024)   # '1.0 kB'

# Ask: is this worth a dependency?
# Alternative: one function, no dependency
def format_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
```

### Question 2 — Is It Maintained?

Check PyPI and GitHub:

```bash
pip show requests | grep -E "Home-page|Author"
```

Look for:
- **Last release date** — must be within 18 months
- **Open issues** — high count with no responses is a red flag
- **Download count** — millions/week signals broad adoption
- **Python versions supported** — must include your target version

### Question 3 — Is It Secure?

```bash
# Check for known vulnerabilities before and after adding
pip install pip-audit
pip-audit -r requirements.txt

# Check the package's GitHub security advisories
# Settings → Security → Advisories
```

For packages that handle:
- **Authentication** — require a second review
- **Cryptography** — require Platform team sign-off
- **User data / PII** — require Platform team sign-off

### Question 4 — What Is Its Dependency Tree?

A package's own dependencies become your dependencies. Check the tree:

```bash
pip install pipdeptree
pip install requests   # install first
pipdeptree -p requests
```

```
requests==2.32.3
├── certifi [required: >=2017.4.17, installed: 2024.2.2]
├── charset-normalizer [required: >=2,<4, installed: 3.3.2]
├── idna [required: >=2.5,<4, installed: 3.7]
└── urllib3 [required: >=1.21.1,<3, installed: 2.2.1]
```

Four transitive deps — reasonable. A package pulling in 30 deps needs more scrutiny.

### Question 5 — What Is the License?

| License | Status | Action |
|---|---|---|
| MIT | ✅ Pre-approved | Use freely |
| Apache 2.0 | ✅ Pre-approved | Use freely |
| BSD (2-clause, 3-clause) | ✅ Pre-approved | Use freely |
| ISC | ✅ Pre-approved | Use freely |
| LGPL | ⚠️ Check usage | Permitted if not modifying the library |
| GPL / AGPL | 🚫 Requires review | Legal review before use in commercial products |
| Unknown / Proprietary | 🚫 Stop | Legal review required |

Check the license:

```bash
pip show requests | grep License
# or check the package's PyPI page
```

---

## The Approval Workflow

```
1. Engineer identifies need for a new package
          │
          ▼
2. Standard library sufficient?
   YES ──────────────────────────────▶ Use it. No further steps.
          │
          NO
          ▼
3. Answer the 5 questions above
          │
          ▼
4. Open a PR that includes:
   • Package added to pyproject.toml [dependencies]
   • Updated requirements.txt (regenerated)
   • PR description template filled out (below)
          │
          ▼
5. Code reviewer approves
          │
          ├── Auth / crypto / PII package?
          │         YES ──▶ Platform team secondary approval
          │
          ▼
6. Merge + configure Dependabot to watch for updates
```

### PR Description Template

When adding a new package, include this in the PR description:

```markdown
## New Dependency: `package-name`

**Necessary?**
[Explain what problem it solves and why the standard library isn't sufficient]

**Maintained?**
- Last release: [date]
- Weekly downloads: [number]
- Open issues: [count]
- Python versions: [list]

**Secure?**
- pip-audit result: [PASS / FAIL — fix before merging]
- Security advisories: [none / list]

**Dependency tree:**
[paste pipdeptree output]

**License:** [MIT / Apache 2.0 / etc.]
```

---

## Pre-Approved Packages

These packages are pre-approved for use in any project without the full review process:

### Runtime

| Package | Purpose | Notes |
|---|---|---|
| `requests` | HTTP client | Prefer for synchronous HTTP |
| `httpx` | Async HTTP client | Use when you need async |
| `pandas` | Data analysis | Standard for tabular data |
| `numpy` | Numerical computing | Indirect dep of pandas |
| `pydantic` | Data validation, settings | Use for config and schemas |
| `click` | CLI framework | Clean alternative to argparse |
| `python-dotenv` | `.env` file loading | Load secrets from .env files |
| `boto3` | AWS SDK | Infrastructure and cloud storage |

### Development Only

| Package | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `pytest-mock` | Mocking helpers |
| `black` | Code formatter |
| `ruff` | Linter (replaces flake8, isort) |
| `mypy` | Type checker |
| `mkdocs` + `mkdocs-material` | Documentation |

Anything **not** on this list requires the full five-question review.

---

## PyPI as the Canonical Source

All packages must come from PyPI (`pip install`). Installing from other sources requires explicit approval:

```bash
# ✅ Always approved
pip install requests==2.32.3

# ❌ Requires Platform approval
pip install git+https://github.com/org/requests.git@main    # git URL
pip install /local/path/to/package                           # local path
pip install --index-url https://private.example.com requests # private index
```

### Why This Matters

- PyPI packages have provenance — you can verify the checksum
- Git URLs install unverified, unchecked code
- Private indexes bypass the public vulnerability database

---

## Removing a Dependency

Removing a dependency is just as important as adding one. When a dep is no longer needed:

```bash
# 1 — Remove from pyproject.toml
# 2 — Uninstall from your venv
pip uninstall package-name

# 3 — Regenerate requirements.txt
pip freeze | grep -v "my-package" > requirements.txt

# 4 — Confirm nothing broke
pytest -v

# 5 — Commit all three files together
git add pyproject.toml requirements.txt requirements-dev.txt
git commit -m "deps: remove unused package-name"
```

---

**[← Import Standards](05-import-standards.md)** | **[Next: Code Review Checklist →](07-code-review-checklist.md)**
