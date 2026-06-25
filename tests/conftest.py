import csv
from pathlib import Path
import pytest

@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    f = tmp_path / "sample.csv"
    rows = [
        {"name": "Alice", "email": "  Alice@Example.COM  ", "phone": "(305) 555-0001", "price": "$9.99"},
        {"name": "Bob",   "email": "not-an-email",          "phone": "(305) 555-0002", "price": "$19.99"},
        {"name": "Carol", "email": "carol@example.com",     "phone": "bad-phone",      "price": "$29.99"},
        {"name": "Dana",  "email": "dana@example.com",      "phone": "(305) 555-0004", "price": "$39.99"},
        {"name": "",      "email": "eve@example.com",       "phone": "(305) 555-0005", "price": "$0.00"},
    ]
    with f.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["name", "email", "phone", "price"])
        writer.writeheader()
        writer.writerows(rows)
    return f
