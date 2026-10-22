#!/usr/bin/env python3
"""Create a separate candidate recovery-state file with only freshness updated."""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys

from audit_recovery_state import compare, inspect_git, load_state, safe_slug, write_new_private


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="exact project slug from state.project.name")
    parser.add_argument("--state", required=True, type=Path, help="existing reviewed recovery-state JSON")
    parser.add_argument("--repo", required=True, type=Path, help="local Git checkout to inspect")
    parser.add_argument("--output", required=True, type=Path, help="new candidate JSON path; must not exist")
    args = parser.parse_args()

    try:
        project = safe_slug(args.project)
        state_path = args.state.expanduser().resolve()
        output_path = args.output.expanduser().resolve()
        if state_path == output_path:
            raise ValueError("candidate output must not be the source state path")

        state = load_state(state_path, project)
        observed = inspect_git(args.repo.expanduser())
        comparison = compare(state, observed)

        candidate = copy.deepcopy(state)
        old_freshness = state["record"]["freshness"]
        proposed_freshness = comparison["proposed_freshness"]
        candidate["record"]["freshness"] = proposed_freshness

        write_new_private(output_path, candidate)
        print(f"Recovery-state candidate written: {output_path}")
        print(f"Freshness proposal: {old_freshness} -> {proposed_freshness}")
        print(f"Describes commit preserved: {state['record']['describes_commit']}")
        print("Only record.freshness was changed in the candidate; the source state was not edited.")
        print("Review the candidate before replacing any authoritative state record.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"[recovery-state-refresh] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
