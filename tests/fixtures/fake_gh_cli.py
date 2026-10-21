#!/usr/bin/env python3
"""Deterministic fake gh CLI used only by installer tests; it never contacts GitHub."""
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
state = Path(os.environ["FAKE_GH_STATE"])

if args == ["api", "user"]:
    print(json.dumps({"login": "mythologyprospector-hub"}))
elif len(args) == 2 and args[0] == "api" and args[1].startswith("repos/"):
    if not state.exists():
        print("HTTP 404 Not Found", file=sys.stderr)
        raise SystemExit(1)
    print(state.read_text(encoding="utf-8"))
elif len(args) >= 3 and args[:2] == ["api", "user/repos"]:
    name = next((item.split("=", 1)[1] for item in args if item.startswith("name=")), None)
    if not name:
        print("missing repo name", file=sys.stderr)
        raise SystemExit(2)
    value = {"full_name": "mythologyprospector-hub/" + name, "private": True}
    state.write_text(json.dumps(value), encoding="utf-8")
    print(json.dumps(value))
else:
    print("unexpected gh command", file=sys.stderr)
    raise SystemExit(2)
