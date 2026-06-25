# 04 — Standard Library Guide: 10 Must-Know Modules

**[← Dependency Management](03-dependency-management.md)** | **[Next: Import Standards →](05-import-standards.md)**

---

## Before You `pip install` Anything

The Python standard library ships with Python. No installs, no version conflicts, no licensing questions. Before reaching for a third-party package, check whether the standard library already handles it.

This guide covers the 10 modules you will use most frequently. Learn them well.

---

## 1. `pathlib` — File System Paths

> **Use `pathlib.Path` for all file system operations. Retire `os.path` string concatenation.**

`pathlib` represents file paths as objects with methods, not raw strings. This makes path manipulation readable, composable, and cross-platform.

```python
from pathlib import Path

# Build project-relative paths
ROOT = Path(__file__).parent.parent   # navigate up from this file
DATA = ROOT / "data" / "raw"          # / operator joins paths
OUT  = ROOT / "data" / "processed"

# Inspect paths
p = Path("reports/q4.csv")
p.exists()                  # True or False
p.is_file()                 # True if it exists and is a file
p.suffix                    # '.csv'
p.stem                      # 'q4'
p.name                      # 'q4.csv'
p.parent                    # Path('reports')
p.with_suffix(".parquet")   # Path('reports/q4.parquet')

# Create directories without error if they exist
OUT.mkdir(parents=True, exist_ok=True)

# Read and write text
content = p.read_text(encoding="utf-8")
p.write_text("hello world", encoding="utf-8")

# Find files
csvs   = list(DATA.glob("*.csv"))         # one level
all_py = list(ROOT.rglob("*.py"))         # recursive

# Iterate a directory
for child in DATA.iterdir():
    if child.is_file():
        print(child.name)
```

```python
# ❌ Old way — don't do this
import os
path = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
full = os.path.join(path, "users.csv")

# ✅ New way
path = Path(__file__).parent.parent / "data" / "raw"
full = path / "users.csv"
```

---

## 2. `os` — Operating System Interface

> **Use `os` for environment variables and process info. Use `pathlib` for everything path-related.**

```python
import os

# Reading environment variables — the two canonical patterns
DB_URL  = os.environ.get("DATABASE_URL", "sqlite:///dev.db")  # with default
API_KEY = os.environ["OPENAI_API_KEY"]                        # fails fast if missing

# Process information
pid  = os.getpid()          # current process ID
cwd  = os.getcwd()          # current working directory
user = os.environ.get("USER", "unknown")

# Directory walking (prefer pathlib.rglob for simple cases)
for dirpath, dirnames, filenames in os.walk("data/"):
    for fname in filenames:
        full_path = Path(dirpath) / fname
        print(full_path)

# Environment variable best practice: fail loudly, fail early
def require_env(name: str) -> str:
    """Get an environment variable or raise a clear error."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"Add it to your .env file or shell profile."
        )
    return value

API_KEY = require_env("OPENAI_API_KEY")
```

---

## 3. `datetime` — Dates and Times

> **Always work in UTC internally. Convert to local time only at display.**

The single most common datetime bug: naive datetimes (no timezone). They look fine until you deploy in a different timezone.

```python
from datetime import datetime, date, timedelta, timezone

# ✅ Always-aware timestamps — the correct pattern
now_utc = datetime.now(tz=timezone.utc)

# Parse ISO 8601 strings (Python 3.11+)
dt = datetime.fromisoformat("2026-06-24T18:15:00+00:00")

# Format
dt.strftime("%Y-%m-%d")            # '2026-06-24'
dt.strftime("%Y-%m-%dT%H:%M:%S")  # '2026-06-24T18:15:00'
dt.isoformat()                     # '2026-06-24T18:15:00+00:00'

# Date arithmetic
yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
deadline  = date.today() + timedelta(weeks=2)
diff      = deadline - date.today()        # timedelta
diff.days                                  # integer

# Store timestamps as ISO strings in JSON/databases
record = {
    "created_at": datetime.now(tz=timezone.utc).isoformat(),
}

# ❌ Naive datetime — no timezone, dangerous
bad = datetime.now()           # What timezone? Nobody knows.

# ✅ Aware datetime — always safe
good = datetime.now(tz=timezone.utc)
```

---

## 4. `json` — JSON Encoding and Decoding

> **Use `json` for config files, API payloads, and inter-service data. Always `indent=2` for stored files.**

```python
import json
from pathlib import Path
from datetime import datetime

# Reading JSON
config = json.loads(Path("config.json").read_text(encoding="utf-8"))

# Writing JSON — always pretty-print files humans will read
Path("output.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
    encoding="utf-8",
)

# Custom encoder for types json can't handle natively
class AppEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

payload = json.dumps({"ts": datetime.now(tz=timezone.utc)}, cls=AppEncoder)

# Safe parsing — always handle errors
def parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc
```

---

## 5. `csv` — CSV Reading and Writing

> **Use `csv.DictReader` / `csv.DictWriter` always. Never split on commas manually.**

```python
import csv
from pathlib import Path

# Reading — DictReader gives you column names as dict keys
with Path("data/raw/users.csv").open(encoding="utf-8-sig") as f:
    # utf-8-sig strips the BOM that Excel adds
    reader = csv.DictReader(f)
    print(reader.fieldnames)     # ['name', 'email', 'phone']
    rows = list(reader)          # list of OrderedDicts

# Writing
fieldnames = ["id", "name", "email"]
with Path("data/processed/clean.csv").open("w", newline="", encoding="utf-8") as f:
    # newline="" is required on all platforms to avoid double newlines
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

# Non-standard dialects (TSV, pipe-delimited, etc.)
with open("data.tsv", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        process(row)

# ❌ Never do this — breaks on quoted fields containing commas
for line in open("data.csv"):
    id, name, email = line.strip().split(",")   # "Smith, John" → broken
```

---

## 6. `collections` — Specialized Container Types

> **Learn Counter, defaultdict, namedtuple, and deque. They replace verbose patterns with clear ones.**

```python
from collections import Counter, defaultdict, namedtuple, deque

# Counter — frequency analysis, bag-of-words, top-N
words  = ["apple", "banana", "apple", "cherry", "banana", "apple"]
counts = Counter(words)
counts.most_common(2)    # [('apple', 3), ('banana', 2)]
counts["apple"]          # 3
counts["mango"]          # 0 — no KeyError, just 0

# Combine counters
a = Counter(["x", "x", "y"])
b = Counter(["y", "y", "z"])
a + b                    # Counter({'y': 3, 'x': 2, 'z': 1})

# defaultdict — group-by without key-existence checks
groups: dict[str, list] = defaultdict(list)
for item in records:
    groups[item["category"]].append(item)
# no need for: if key not in groups: groups[key] = []

# namedtuple — lightweight, immutable, readable structs
Point   = namedtuple("Point", ["x", "y"])
Record  = namedtuple("Record", ["sku", "quantity", "price"])

p = Point(3, 4)
p.x                      # 3 — readable
p._asdict()              # {'x': 3, 'y': 4}
x, y = p                 # unpacking still works

# deque — efficient queue and sliding-window buffer
window = deque(maxlen=5)          # auto-discards oldest when full
for reading in sensor_stream:
    window.append(reading)
    avg = sum(window) / len(window)   # rolling average

# deque as a queue (fast O(1) popleft; list.pop(0) is O(n))
queue = deque()
queue.append("first")
queue.append("second")
queue.popleft()          # 'first'
```

---

## 7. `itertools` — Iterator Building Blocks

> **Use itertools to process data lazily — without loading everything into memory.**

```python
import itertools

# chain — flatten multiple iterables without creating a big list
all_records = itertools.chain(jan_data, feb_data, mar_data)
for record in all_records:           # consumes one at a time
    process(record)

# islice — take the first N items from any iterator
first_100 = list(itertools.islice(huge_generator(), 100))

# groupby — group consecutive items with the same key
# IMPORTANT: data must be sorted by the key first
data = sorted(records, key=lambda r: r["department"])
for dept, members in itertools.groupby(data, key=lambda r: r["department"]):
    dept_list = list(members)
    print(f"{dept}: {len(dept_list)} members")

# product — cartesian product; replaces nested for-loops
for size, color, material in itertools.product(
    ["S", "M", "L"],
    ["red", "blue", "green"],
    ["cotton", "polyester"],
):
    create_variant(size, color, material)

# batched (Python 3.12+) — process in chunks
for batch in itertools.batched(large_list, n=100):
    db.bulk_insert(batch)

# takewhile / dropwhile — conditional iteration
import itertools
positive = list(itertools.takewhile(lambda x: x > 0, [3, 1, -2, 4, 5]))
# [3, 1]  — stops at the first non-positive value
```

---

## 8. `functools` — Higher-Order Functions

> **lru_cache for memoization, wraps for decorators, partial for pre-filling arguments.**

```python
import functools

# lru_cache — cache expensive pure function results
@functools.lru_cache(maxsize=256)
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Hits the API once per unique pair, then returns cached result."""
    return fetch_rate(from_currency, to_currency)

get_exchange_rate("USD", "EUR")   # API call
get_exchange_rate("USD", "EUR")   # cache hit — no API call

# cache (Python 3.9+) — unbounded, simpler spelling
@functools.cache
def fibonacci(n: int) -> int:
    return n if n < 2 else fibonacci(n - 1) + fibonacci(n - 2)

# partial — pre-fill function arguments to create specialised versions
import csv
tsv_reader  = functools.partial(csv.reader, delimiter="\t")
pipe_reader = functools.partial(csv.reader, delimiter="|")

with open("data.tsv") as f:
    for row in tsv_reader(f):       # behaves like csv.reader(f, delimiter="\t")
        print(row)

# wraps — ALWAYS use this when writing decorators
def retry(max_attempts: int = 3):
    def decorator(func):
        @functools.wraps(func)    # preserves __name__, __doc__, __annotations__
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator

@retry(max_attempts=3)
def fetch_data(url: str) -> dict:
    """Fetch JSON from a URL with automatic retry."""
    return requests.get(url).json()

fetch_data.__name__   # 'fetch_data' — not 'wrapper', thanks to @wraps
fetch_data.__doc__    # 'Fetch JSON from a URL...' — preserved
```

---

## 9. `re` — Regular Expressions

> **Compile patterns once at module level. Use named groups. Prefer string methods for simple cases.**

```python
import re

# Compile once at module level — not inside functions or loops
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")
SLUG_RE  = re.compile(r"[^a-z0-9\-]")

def is_valid_email(s: str) -> bool:
    return bool(EMAIL_RE.fullmatch(s.strip()))

def slugify(text: str) -> str:
    return SLUG_RE.sub("-", text.lower().strip()).strip("-")

# Named groups — readable, maintainable
LOG_LINE = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"\s+(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)"
    r"\s+(?P<message>.+)"
)

for line in log_file:
    m = LOG_LINE.match(line)
    if m:
        ts      = m.group("timestamp")   # readable
        level   = m.group("level")
        message = m.group("message")

# findall vs finditer — prefer finditer for large inputs (lazy)
for m in re.finditer(r"\d+", large_text):
    print(m.group(), m.start(), m.end())

# Substitution
clean = re.sub(r"\s+", " ", raw_text).strip()      # collapse whitespace
redacted = re.sub(EMAIL_RE, "[REDACTED]", text)     # remove emails

# ❌ Compiling inside a loop — recompiles on every iteration
for line in lines:
    if re.match(r"\d{4}-\d{2}-\d{2}", line):        # slow!
        process(line)

# ✅ Compile at module level
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
for line in lines:
    if DATE_RE.match(line):
        process(line)
```

---

## 10. `logging` — Application Logging

> **Never use `print()` in production code. Configure logging once, at the application entry point. Never in library code.**

```python
import logging
from pathlib import Path

# ── In library code — get a logger, never configure it ──────────────────
logger = logging.getLogger(__name__)
# __name__ = "my_package.core" — gives hierarchical logger names

def process_file(path: Path) -> int:
    logger.debug("Processing file: %s", path)        # lazy formatting — always %s
    try:
        count = _parse(path)
        logger.info("Processed %s → %d records", path.name, count)
        return count
    except FileNotFoundError:
        logger.warning("File not found, skipping: %s", path)
        return 0
    except Exception:
        logger.exception("Unexpected error in %s", path)  # includes full traceback
        raise

# ── In application entry point (app.py, main.py) — configure here ────────
def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(name)-20s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=handlers,
    )

if __name__ == "__main__":
    setup_logging(level="INFO")
    process_file(Path("data/raw/users.csv"))
```

### Log Level Guide

```
DEBUG    — high-volume diagnostic info; off in production
           "Processing row 4523 of 10000"

INFO     — normal operation milestones
           "Job started", "Processed 10,000 records in 3.2s"

WARNING  — unexpected but recoverable
           "Missing optional field 'phone', using default"

ERROR    — something failed; execution can continue
           "Failed to fetch URL, will retry in 5s"

CRITICAL — system cannot continue; immediate attention
           "Database connection lost; shutting down"
```

---

## Standard Library Decision Tree

Before installing a package, ask:

```
Need to work with files/paths?        → pathlib
Need environment variables?           → os
Need dates and times?                 → datetime
Need to read/write JSON?              → json
Need to read/write CSV?               → csv
Need frequency counting?              → collections.Counter
Need to group items?                  → collections.defaultdict / itertools.groupby
Need to process large sequences?      → itertools
Need to cache function results?       → functools.lru_cache
Need to match/extract text patterns?  → re
Need structured output/debugging?     → logging
```

If the standard library handles it, **use it**. If not, follow the [Third-Party Package Policy](06-third-party-packages.md).

---

**[← Dependency Management](03-dependency-management.md)** | **[Next: Import Standards →](05-import-standards.md)**
