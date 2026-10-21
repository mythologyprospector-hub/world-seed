#!/usr/bin/env python3
"""Read-only preflight for all factory bootstrap destinations before any writes."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPT_DIR))

import materialize_intake_dock as dock
import materialize_profile_packages as profiles
import provision_intake_dock as remote_dock


def check_non_overlapping(paths: dict[str, Path]) -> None:
    resolved = {name: path.expanduser().resolve(strict=False) for name, path in paths.items()}
    names = list(resolved)
    for index, first_name in enumerate(names):
        first = resolved[first_name]
        for second_name in names[index + 1:]:
            second = resolved[second_name]
            if first == second or first in second.parents or second in first.parents:
                raise ValueError(
                    f"factory destinations must be separate and must not contain one another: "
                    f"{first_name} and {second_name}"
                )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, required=True)
    parser.add_argument("--factory-home", type=Path, required=True)
    parser.add_argument("--state-home", type=Path, required=True)
    parser.add_argument("--operator-destination", type=Path)
    parser.add_argument("--personal-data-destination", type=Path)
    parser.add_argument("--intake-dock-template-root", type=Path, required=True)
    parser.add_argument("--intake-dock-destination", type=Path)
    parser.add_argument("--intake-dock-lane")
    parser.add_argument("--remote-dock-owner")
    parser.add_argument("--remote-dock-repository")
    parser.add_argument("--remote-dock-confirm-target")
    args = parser.parse_args(argv)

    try:
        selected: dict[str, Path] = {
            "factory home": args.factory_home,
            "state home": args.state_home,
        }
        profile_set = args.operator_destination is not None or args.personal_data_destination is not None
        if profile_set:
            if args.operator_destination is None or args.personal_data_destination is None:
                raise ValueError("both operator-profile and personal-data destinations must be configured together")
            selected["operator-profile"] = args.operator_destination
            selected["personal-data"] = args.personal_data_destination

        dock_set = args.intake_dock_destination is not None or args.intake_dock_lane is not None
        if dock_set:
            if args.intake_dock_destination is None or not args.intake_dock_lane:
                raise ValueError("both Intake Dock destination and lane must be configured together")
            selected["Intake Dock"] = args.intake_dock_destination

        check_non_overlapping(selected)

        remote_values = (args.remote_dock_owner, args.remote_dock_repository, args.remote_dock_confirm_target)
        remote_set = any(value is not None and value != "" for value in remote_values)
        if remote_set:
            if not dock_set:
                raise ValueError("remote Intake Dock provisioning also requires a configured local Dock destination and lane")
            if not all(value is not None and value != "" for value in remote_values):
                raise ValueError("remote Intake Dock provisioning requires owner, repository, and exact confirmation together")
            target = remote_dock._validate_target(args.remote_dock_owner, args.remote_dock_repository)
            if args.remote_dock_confirm_target != target:
                raise ValueError("remote confirmation must exactly match " + target)
            if shutil.which("gh") is None:
                raise ValueError("remote Intake Dock provisioning is configured but GitHub CLI (gh) is unavailable")

        if profile_set:
            packages = profiles.load_templates(args.template_root)
            destinations = profiles.normalize_destinations(
                args.operator_destination, args.personal_data_destination
            )
            profiles.preflight(destinations, packages)

        if dock_set:
            dock.preflight(
                args.intake_dock_template_root,
                args.intake_dock_destination,
                args.intake_dock_lane,
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print("FACTORY_DESTINATIONS_PREFLIGHT=PASS")
    print("All configured package and Intake Dock destinations validated; no destination was changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
