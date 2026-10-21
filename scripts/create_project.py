#!/usr/bin/env python3
"""Generate a new project from World Seed's versioned, portable template."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MISSION_MARKER = "**REPLACE THIS SENTENCE WITH THE SINGLE-SENTENCE MISSION FOR THIS PROJECT.**"
PROJECT_FILES = (
    "AGENTS.md",
    "LICENSE",
    "CONSTITUTION.md",
    "DOCS.md",
    "HUMAN.md",
    "MACHINE.md",
    "ORGANS.md",
    "README.md",
    "MISSION.md",
)


class ProjectGenerationError(ValueError):
    """Raised when project generation would be incomplete or unsafe."""


def source_revision(repository_root: Path) -> str:
    """Return the checked-out World Seed commit, or 'unknown' outside Git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    revision = result.stdout.strip()
    return revision if re.fullmatch(r"[0-9a-f]{40,64}", revision) else "unknown"


def render_project(
    repository_root: Path,
    project_name: str,
    mission: str,
    revision: str,
) -> tuple[dict[str, str], dict[str, object]]:
    """Render every project file and its provenance manifest in memory."""
    if not PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise ProjectGenerationError(
            "project name must be a lowercase slug using letters, numbers, and single hyphens"
        )
    if "\n" in mission or "\r" in mission:
        raise ProjectGenerationError("mission must be a single line")
    mission = " ".join(mission.split())
    if not mission:
        raise ProjectGenerationError("mission must not be blank")
    if revision != "unknown" and not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise ProjectGenerationError("source revision must be a Git SHA or the literal unknown")

    template_root = repository_root / "templates" / "project"
    mission_template_path = repository_root / "templates" / "MISSION.md"
    required_templates = [template_root / name for name in PROJECT_FILES if name != "MISSION.md"]
    missing = [str(path.relative_to(repository_root)) for path in required_templates if not path.is_file()]
    if not mission_template_path.is_file():
        missing.append(str(mission_template_path.relative_to(repository_root)))
    version_path = template_root / "PROJECT_TEMPLATE_VERSION"
    if not version_path.is_file():
        missing.append(str(version_path.relative_to(repository_root)))
    if missing:
        raise ProjectGenerationError("required template files missing: " + ", ".join(missing))

    mission_template = mission_template_path.read_text(encoding="utf-8")
    if mission_template.count(MISSION_MARKER) != 1:
        raise ProjectGenerationError("mission template must contain exactly one mission replacement marker")

    rendered: dict[str, str] = {}
    for name in PROJECT_FILES:
        if name == "MISSION.md":
            rendered[name] = mission_template.replace(MISSION_MARKER, mission)
        elif name == "README.md":
            readme = (template_root / name).read_text(encoding="utf-8")
            if "{{PROJECT_NAME}}" not in readme or "{{MISSION}}" not in readme:
                raise ProjectGenerationError("README template is missing required placeholders")
            rendered[name] = readme.replace("{{PROJECT_NAME}}", project_name).replace("{{MISSION}}", mission)
        else:
            rendered[name] = (template_root / name).read_text(encoding="utf-8")

    template_version = version_path.read_text(encoding="utf-8").strip()
    if not template_version:
        raise ProjectGenerationError("project template version must not be blank")

    manifest: dict[str, object] = {
        "schema_version": 1,
        "project_name": project_name,
        "mission": mission,
        "template_version": template_version,
        "source_revision": revision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_files": sorted(PROJECT_FILES),
        "manifest_excludes_itself": True,
    }
    return rendered, manifest


def create_project(
    repository_root: Path,
    project_name: str,
    mission: str,
    destination: Path,
    revision: str | None = None,
) -> Path:
    """Create a new project without overwriting an existing path or source tree."""
    repository_root = repository_root.resolve()
    destination = destination.expanduser()
    if destination.is_symlink():
        raise ProjectGenerationError("destination must not be a symbolic link")
    destination = destination.resolve()
    try:
        destination.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ProjectGenerationError("destination must be outside the World Seed source checkout")

    rendered, manifest = render_project(
        repository_root,
        project_name,
        mission,
        revision if revision is not None else source_revision(repository_root),
    )
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"

    if destination.exists() or destination.is_symlink():
        raise ProjectGenerationError(f"destination already exists; refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.mkdir()
        for name, text in rendered.items():
            (destination / name).write_text(text, encoding="utf-8", newline="\n")
        (destination / "world-seed-manifest.json").write_text(
            manifest_text, encoding="utf-8", newline="\n"
        )
    except Exception:
        # This directory was created exclusively by this invocation.
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a new project from World Seed's portable template."
    )
    parser.add_argument("--name", required=True, help="lowercase project slug, such as example-project")
    parser.add_argument("--mission", required=True, help="single-line mission sentence for the project")
    parser.add_argument("--destination", required=True, type=Path, help="new output directory; must not exist")
    parser.add_argument(
        "--source-revision",
        help="optional source revision override for reproducible builds; normally detected from Git",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        created = create_project(root, args.name, args.mission, args.destination, args.source_revision)
    except (OSError, ProjectGenerationError) as exc:
        parser.error(str(exc))
    print(f"Created project: {created}")
    print(f"Template manifest: {created / 'world-seed-manifest.json'}")
    print("No GitHub repository, remote, credential, or external service was created or modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
