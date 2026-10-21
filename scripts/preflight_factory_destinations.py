#!/usr/bin/env python3
"""Read-only preflight for all factory bootstrap destinations before any writes."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import materialize_intake_dock as dock
import materialize_profile_packages as profiles


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
