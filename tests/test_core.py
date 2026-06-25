# tests/test_core.py
"""
Tests for my_package.core — demonstrates pytest best practices.

Test organisation:
  - One TestClass per public function
  - Descriptive test method names: test_<what>_<condition>_<expected>
  - Uses conftest.py fixtures (no explicit imports needed)
  - Uses pytest.raises for expected exceptions
  - No hardcoded paths — uses tmp_path fixture
"""

# ── Standard library ──────────────────────────────────────────────────────
import csv
from pathlib import Path

# ── Third-party ───────────────────────────────────────────────────────────
import pytest

# ── Local ─────────────────────────────────────────────────────────────────
from my_package.core import clean_csv, clean_email, clean_numeric, clean_phone


# ─────────────────────────────────────────────────────────────────────────
# clean_email
# ─────────────────────────────────────────────────────────────────────────

class TestCleanEmail:
    def test_normalizes_case_and_strips_whitespace(self):
        assert clean_email("  Alice@Example.COM  ") == "alice@example.com"

    def test_already_clean_email_unchanged(self):
        assert clean_email("user@domain.org") == "user@domain.org"

    def test_rejects_missing_at_sign(self):
        with pytest.raises(ValueError, match="Invalid e-mail"):
            clean_email("notanemail")

    def test_rejects_multiple_at_signs(self):
        with pytest.raises(ValueError):
            clean_email("a@@b.com")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            clean_email("")

    def test_converts_non_string_input(self):
        # Should convert to str before processing
        with pytest.raises(ValueError):
            clean_email(12345)  # not a valid email


# ─────────────────────────────────────────────────────────────────────────
# clean_phone
# ─────────────────────────────────────────────────────────────────────────

class TestCleanPhone:
    def test_strips_parentheses_spaces_dashes(self):
        assert clean_phone("(305) 555-1234") == "3055551234"

    def test_strips_dots(self):
        assert clean_phone("305.555.1234") == "3055551234"

    def test_strips_leading_country_code_1(self):
        assert clean_phone("+13055551234") == "3055551234"
        assert clean_phone("13055551234") == "3055551234"

    def test_returns_formatted_output_when_requested(self):
        assert clean_phone("3055551234", digits_only=False) == "(305) 555-1234"

    def test_rejects_too_few_digits(self):
        with pytest.raises(ValueError, match="Expected 10 digits"):
            clean_phone("305-123")

    def test_rejects_too_many_digits(self):
        with pytest.raises(ValueError):
            clean_phone("123456789012")  # 12 digits


# ─────────────────────────────────────────────────────────────────────────
# clean_numeric
# ─────────────────────────────────────────────────────────────────────────

class TestCleanNumeric:
    def test_strips_dollar_sign_and_comma(self):
        assert clean_numeric("$1,234.56") == 1234.56

    def test_plain_float_unchanged(self):
        assert clean_numeric(9.99) == 9.99

    def test_handles_string_float(self):
        assert clean_numeric("  42.0  ") == 42.0

    def test_allows_negative_by_default(self):
        assert clean_numeric("-50.0") == -50.0

    def test_rejects_negative_when_disallowed(self):
        with pytest.raises(ValueError, match="Negative value not allowed"):
            clean_numeric("-5.00", allow_negative=False)

    def test_rejects_non_numeric_string(self):
        with pytest.raises(ValueError, match="Cannot convert"):
            clean_numeric("abc")

    def test_zero_is_valid(self):
        assert clean_numeric("$0.00") == 0.0


# ─────────────────────────────────────────────────────────────────────────
# clean_csv (uses the sample_csv fixture from conftest.py)
# ─────────────────────────────────────────────────────────────────────────

class TestCleanCsv:
    def test_returns_correct_counts(self, sample_csv: Path, tmp_path: Path):
        output = tmp_path / "clean.csv"
        stats = clean_csv(
            sample_csv,
            output,
            required_fields=["name", "email"],
            email_fields=["email"],
            phone_fields=["phone"],
            skip_invalid=True,
        )
        assert stats["total"] == 5
        assert stats["errors"] >= 1   # at least some rows have errors

    def test_valid_rows_are_written(self, sample_csv: Path, tmp_path: Path):
        output = tmp_path / "clean.csv"
        stats = clean_csv(
            sample_csv,
            output,
            email_fields=["email"],
            phone_fields=["phone"],
            skip_invalid=True,
        )
        assert stats["written"] > 0
        assert output.exists()

    def test_creates_output_directory_if_missing(self, sample_csv: Path, tmp_path: Path):
        output = tmp_path / "nested" / "dir" / "clean.csv"
        clean_csv(sample_csv, output, skip_invalid=True)
        assert output.exists()

    def test_email_fields_are_normalized(self, sample_csv: Path, tmp_path: Path):
        output = tmp_path / "clean.csv"
        clean_csv(sample_csv, output, email_fields=["email"], skip_invalid=True)

        with output.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Alice's email should be normalized
        alice_rows = [r for r in rows if r["name"] == "Alice"]
        if alice_rows:
            assert alice_rows[0]["email"] == "alice@example.com"

    def test_skip_invalid_false_writes_error_column(self, sample_csv: Path, tmp_path: Path):
        output = tmp_path / "clean_with_errors.csv"
        stats = clean_csv(
            sample_csv,
            output,
            email_fields=["email"],
            skip_invalid=False,
        )
        assert stats["written"] == stats["total"]  # all rows written

        with output.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "_error" in (reader.fieldnames or [])
