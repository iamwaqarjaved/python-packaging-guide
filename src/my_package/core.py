"""
my_package.core — Data normalization functions.

This module demonstrates the coding standards from the python-packaging-guide:
- Module-level docstring
- NumPy-style function docstrings
- Type hints on all public functions
- logging instead of print()
- pathlib.Path for file operations
- csv.DictReader/DictWriter (never split on commas)
- Explicit ValueError for bad input
"""

# ── Standard library ──────────────────────────────────────────────────────
import csv
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Module-level logger — get it, never configure it here
logger = logging.getLogger(__name__)

# Compile regex patterns at module level — never inside a function or loop
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PHONE_DIGITS_RE = re.compile(r"\D")
_CURRENCY_RE = re.compile(r"[^\d.\-]")


# ── Public functions ──────────────────────────────────────────────────────

def clean_email(email: Any) -> str:
    """Lowercase and validate an e-mail address.

    Parameters
    ----------
    email : Any
        Raw e-mail string; converted to str and stripped of whitespace.

    Returns
    -------
    str
        Normalized e-mail address in lowercase.

    Raises
    ------
    ValueError
        If the cleaned value does not contain exactly one ``@`` or
        does not match a basic e-mail pattern.

    Examples
    --------
    >>> clean_email("  Alice@Example.COM  ")
    'alice@example.com'
    >>> clean_email("user@domain.org")
    'user@domain.org'
    """
    cleaned = str(email).strip().lower()
    if not _EMAIL_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid e-mail address: {email!r}")
    logger.debug("clean_email: %r → %r", email, cleaned)
    return cleaned


def clean_phone(phone: Any, *, digits_only: bool = True) -> str:
    """Normalize a US phone number.

    Strips all non-digit characters, removes a leading country code of 1,
    and validates that exactly 10 digits remain.

    Parameters
    ----------
    phone : Any
        Raw phone string; e.g. ``"(305) 555-1234"`` or ``"13055551234"``.
    digits_only : bool, optional
        If ``True`` (default), return the 10-digit string.
        If ``False``, return in ``(NXX) NXX-XXXX`` format.

    Returns
    -------
    str
        Normalized phone number.

    Raises
    ------
    ValueError
        If the cleaned value does not resolve to exactly 10 digits.

    Examples
    --------
    >>> clean_phone("(305) 555-1234")
    '3055551234'
    >>> clean_phone("305.555.1234", digits_only=False)
    '(305) 555-1234'
    """
    digits = _PHONE_DIGITS_RE.sub("", str(phone))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(
            f"Expected 10 digits after stripping, got {len(digits)}: {phone!r}"
        )
    if digits_only:
        return digits
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def clean_numeric(value: Any, *, allow_negative: bool = True) -> float:
    """Strip currency symbols and commas; return a float.

    Parameters
    ----------
    value : Any
        Raw value, e.g. ``"$1,234.56"``, ``1234.56``, or ``"-99.9"``.
    allow_negative : bool, optional
        If ``False``, raise ``ValueError`` for negative results.

    Returns
    -------
    float
        Numeric value.

    Raises
    ------
    ValueError
        If the value cannot be converted to float, or if it is negative
        and ``allow_negative`` is ``False``.

    Examples
    --------
    >>> clean_numeric("$1,234.56")
    1234.56
    >>> clean_numeric("  -50.0 ", allow_negative=False)
    Traceback (most recent call last):
        ...
    ValueError: Negative value not allowed: -50.0
    """
    cleaned = _CURRENCY_RE.sub("", str(value)).strip()
    try:
        result = float(cleaned)
    except ValueError:
        raise ValueError(f"Cannot convert to numeric: {value!r}")
    if not allow_negative and result < 0:
        raise ValueError(f"Negative value not allowed: {result}")
    return result


def clean_csv(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    email_fields: Optional[List[str]] = None,
    phone_fields: Optional[List[str]] = None,
    numeric_fields: Optional[List[str]] = None,
    required_fields: Optional[List[str]] = None,
    skip_invalid: bool = True,
) -> Dict[str, int]:
    """Read a CSV, clean specified columns, and write a cleaned CSV.

    Parameters
    ----------
    input_path : str or Path
        Path to the source CSV file.
    output_path : str or Path
        Path where the cleaned CSV will be written. Created if needed.
    email_fields : List[str], optional
        Column names to run through :func:`clean_email`.
    phone_fields : List[str], optional
        Column names to run through :func:`clean_phone`.
    numeric_fields : List[str], optional
        Column names to run through :func:`clean_numeric`.
    required_fields : List[str], optional
        Fields that must be non-empty; rows failing this are flagged.
    skip_invalid : bool, optional
        If ``True`` (default), invalid rows are skipped.
        If ``False``, they are written with an ``_error`` column.

    Returns
    -------
    Dict[str, int]
        Summary: ``{"total": N, "written": N, "skipped": N, "errors": N}``.

    Examples
    --------
    >>> stats = clean_csv("raw.csv", "clean.csv", email_fields=["email"])
    >>> stats["written"]
    97
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    email_fields = email_fields or []
    phone_fields = phone_fields or []
    numeric_fields = numeric_fields or []
    required_fields = required_fields or []

    counters: Dict[str, int] = {"total": 0, "written": 0, "skipped": 0, "errors": 0}

    logger.info("Cleaning CSV: %s → %s", input_path, output_path)

    with (
        input_path.open(newline="", encoding="utf-8-sig") as infile,
        output_path.open("w", newline="", encoding="utf-8") as outfile,
    ):
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        if not skip_invalid:
            fieldnames = [*fieldnames, "_error"]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            counters["total"] += 1
            errors: List[str] = []

            # Validate required fields
            for field in required_fields:
                if not str(row.get(field, "")).strip():
                    errors.append(f"missing required field: {field!r}")

            # Clean columns
            for field in email_fields:
                if row.get(field):
                    try:
                        row[field] = clean_email(row[field])
                    except ValueError as exc:
                        errors.append(str(exc))

            for field in phone_fields:
                if row.get(field):
                    try:
                        row[field] = clean_phone(row[field])
                    except ValueError as exc:
                        errors.append(str(exc))

            for field in numeric_fields:
                if row.get(field):
                    try:
                        row[field] = clean_numeric(row[field])
                    except ValueError as exc:
                        errors.append(str(exc))

            if errors:
                counters["errors"] += 1
                logger.debug("Row %d errors: %s", counters["total"], errors)
                if skip_invalid:
                    counters["skipped"] += 1
                    continue
                row["_error"] = "; ".join(errors)

            writer.writerow(row)
            counters["written"] += 1

    logger.info("Done: %s", counters)
    return counters
