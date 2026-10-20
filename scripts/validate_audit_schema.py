#!/usr/bin/env python3
"""Validate audit finding records against the full JSON Schema contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "audit-finding.schema.json"


def validate_record(record: object, schema: dict) -> list[str]:
    """Return all full-schema validation errors in stable, readable order."""
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(validator.iter_errors(record), key=lambda item: (list(map(str, item.absolute_path)), item.message)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{location}: {error.message}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Validate one or more audit finding JSON records against the canonical schema."""
    paths = [Path(item) for item in (argv if argv is not None else sys.argv[1:])]
    if not paths:
        print("Usage: python scripts/validate_audit_schema.py FINDING.json [...]", file=sys.stderr)
        return 2
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, Exception) as exc:
        print(f"BLOCKED: canonical JSON Schema is invalid or unreadable ({type(exc).__name__}).", file=sys.stderr)
        return 2
    failures = 0
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path}: could not read valid JSON ({type(exc).__name__})")
            failures += 1
            continue
        errors = validate_record(record, schema)
        if errors:
            failures += 1
            for error in errors:
                print(f"ERROR: {path}: {error}")
        else:
            print(f"PASS: {path} conforms to the full audit finding schema.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
