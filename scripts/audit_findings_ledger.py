#!/usr/bin/env python3
"""Maintain a private, queryable SQLite ledger of schema-validated audit findings."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from private_report import write_private_json
from validate_audit_schema import SCHEMA_PATH, validate_record

ROOT = Path(__file__).resolve().parents[1]


def _safe_path(path: Path, label: str) -> Path:
    """Resolve a path and refuse to place private audit data inside the public seed."""
    resolved = path.expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the public world-seed repository")
    return resolved


def open_ledger(path: Path) -> sqlite3.Connection:
    """Open/create the ledger, restricting the database file to owner access."""
    path = _safe_path(path, "ledger database")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        if not path.is_file():
            raise ValueError("ledger path is not a regular file")
        os.chmod(path, 0o600)
    else:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        os.close(fd)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS findings (
            finding_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            scope TEXT NOT NULL,
            last_reviewed TEXT NOT NULL,
            record_json TEXT NOT NULL
        )"""
    )
    connection.commit()
    return connection


def load_schema() -> dict:
    """Load and validate the canonical schema before using the ledger."""
    from jsonschema import Draft202012Validator
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def upsert_record(connection: sqlite3.Connection, record: object) -> None:
    """Insert or update one finding after full schema validation."""
    schema = load_schema()
    errors = validate_record(record, schema)
    if errors:
        raise ValueError("finding fails schema validation: " + "; ".join(errors))
    assert isinstance(record, dict)
    connection.execute(
        """INSERT INTO findings (finding_id, status, severity, scope, last_reviewed, record_json)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(finding_id) DO UPDATE SET
             status=excluded.status,
             severity=excluded.severity,
             scope=excluded.scope,
             last_reviewed=excluded.last_reviewed,
             record_json=excluded.record_json""",
        (
            record["finding_id"], record["status"], record["severity"],
            record["scope"], record["last_reviewed"],
            json.dumps(record, sort_keys=True),
        ),
    )
    connection.commit()


def query_records(
    connection: sqlite3.Connection,
    status: str | None = None,
    severity: str | None = None,
) -> list[dict]:
    """Return full finding records filtered by optional lifecycle/severity."""
    query = "SELECT record_json FROM findings"
    clauses = []
    values = []
    if status:
        clauses.append("status = ?")
        values.append(status)
    if severity:
        clauses.append("severity = ?")
        values.append(severity)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY severity, finding_id"
    rows = connection.execute(query, values).fetchall()
    return [json.loads(row["record_json"]) for row in rows]


def get_record(connection: sqlite3.Connection, finding_id: str) -> dict | None:
    """Return one finding by stable ID."""
    row = connection.execute(
        "SELECT record_json FROM findings WHERE finding_id = ?", (finding_id,)
    ).fetchone()
    return json.loads(row["record_json"]) if row else None


def main(argv: list[str] | None = None) -> int:
    """Initialize, query, update, or export the private findings ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="Private SQLite database path outside this public repository")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create the ledger if needed")
    upsert = sub.add_parser("upsert", help="Insert/update one schema-valid finding")
    upsert.add_argument("--record", required=True, type=Path)
    listing = sub.add_parser("list", help="List findings, optionally filtered")
    listing.add_argument("--status")
    listing.add_argument("--severity")
    show = sub.add_parser("show", help="Show one finding by ID")
    show.add_argument("finding_id")
    export = sub.add_parser("export", help="Export findings as a private JSON array")
    export.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        database = _safe_path(args.db, "ledger database")
        with open_ledger(database) as connection:
            if args.command == "init":
                print(f"Ledger initialized at {database}")
            elif args.command == "upsert":
                record = json.loads(args.record.expanduser().read_text(encoding="utf-8"))
                upsert_record(connection, record)
                print(f"Saved finding {record.get('finding_id') if isinstance(record, dict) else '(invalid record)'}")
            elif args.command == "list":
                print(json.dumps(query_records(connection, args.status, args.severity), indent=2))
            elif args.command == "show":
                record = get_record(connection, args.finding_id)
                if record is None:
                    print("NOT FOUND", file=sys.stderr)
                    return 1
                print(json.dumps(record, indent=2))
            elif args.command == "export":
                output = _safe_path(args.output, "export output")
                write_private_json(output, query_records(connection))
                print(f"Exported findings to private JSON at {output}")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, sqlite3.Error, ValueError) as exc:
        print(f"BLOCKED: ledger operation failed ({type(exc).__name__}); no successful change is implied.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
