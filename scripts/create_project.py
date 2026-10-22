#!/usr/bin/env python3
"""Generate a new project from World Seed's versioned, portable template."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
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
        # Installed releases are archived under their exact commit SHA and have no .git directory.
        revision = repository_root.name
    else:
        revision = result.stdout.strip()
    return revision if re.fullmatch(r"[0-9a-f]{40,64}", revision) else "unknown"


def validate_rendered_project(
    rendered: dict[str, str],
    project_name: str,
    mission: str,
) -> list[dict[str, str]]:
    """Validate the generated bundle before writing it and return auditable check results."""
    from urllib.parse import unquote, urlsplit

    checks: list[dict[str, str]] = []

    def record(check_id: str, passed: bool, detail: str) -> None:
        checks.append({
            "id": check_id,
            "status": "passed" if passed else "failed",
            "detail": detail,
        })

    inventory_ok = set(rendered) == set(PROJECT_FILES)
    record(
        "required_file_inventory",
        inventory_ok,
        "All and only the required project files are rendered."
        if inventory_ok else "Rendered file inventory does not match the required project bundle.",
    )

    mission_ok = (
        bool(mission)
        and mission in rendered.get("MISSION.md", "")
        and mission in rendered.get("README.md", "")
        and MISSION_MARKER not in rendered.get("MISSION.md", "")
    )
    record(
        "mission_substitution",
        mission_ok,
        "The supplied mission is present in the mission and README files."
        if mission_ok else "The mission is missing or the replacement marker remains.",
    )

    readme = rendered.get("README.md", "")
    readme_ok = "{{PROJECT_NAME}}" not in readme and "{{MISSION}}" not in readme
    record(
        "readme_placeholders_resolved",
        readme_ok,
        "Project name and mission placeholders are resolved."
        if readme_ok else "README contains unresolved project placeholders.",
    )

    unresolved = [
        name for name, content in rendered.items()
        if re.search(r"\\{\\{[^{}]+\\}\\}", content)
    ]
    record(
        "no_unresolved_template_markers",
        not unresolved,
        "No unresolved double-brace template markers remain."
        if not unresolved else "Unresolved template markers remain in: " + ", ".join(sorted(unresolved)),
    )

    rendered_names = set(rendered)
    broken_links: list[str] = []
    for source_name, content in rendered.items():
        if not source_name.endswith(".md"):
            continue
        for match in re.finditer(r"\\[[^\\]]*\\]\\(([^)]+)\\)", content):
            href = match.group(1).strip()
            parsed = urlsplit(href)
            if not parsed.path or parsed.scheme or href.startswith("//"):
                continue
            target = unquote(parsed.path)
            target_path = Path(target.lstrip("/")) if target.startswith("/") else Path(source_name).parent / target
            normalized = target_path.as_posix()
            if normalized not in rendered_names and not (
                not target_path.suffix and (normalized + ".md") in rendered_names
            ):
                broken_links.append(f"{source_name} -> {href}")
    record(
        "local_markdown_links_resolve",
        not broken_links,
        "All local Markdown links resolve to generated files."
        if not broken_links else "Broken local Markdown links: " + "; ".join(broken_links),
    )

    failed = [check["id"] for check in checks if check["status"] != "passed"]
    if failed:
        raise ProjectGenerationError("rendered project validation failed: " + ", ".join(failed))
    return checks


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
            rendered[name] = mission_template.replace(MISSION_MARKER, f"**{mission}**")
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

    validation_checks = validate_rendered_project(rendered, project_name, mission)
    file_hashes = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in sorted(rendered.items())
    }
    manifest: dict[str, object] = {
        "schema_version": 2,
        "project_name": project_name,
        "mission": mission,
        "template_version": template_version,
        "source_revision": revision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_files": sorted(PROJECT_FILES),
        "generated_file_sha256": file_hashes,
        "validation_results": {
            "status": "passed",
            "checks": validation_checks,
        },
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
    created_by_this_invocation = False
    try:
        destination.mkdir()
        created_by_this_invocation = True
        for name, content in rendered.items():
            (destination / name).write_text(content, encoding="utf-8", newline="\n")
        (destination / "world-seed-manifest.json").write_text(
            manifest_text, encoding="utf-8", newline="\n"
        )
    except Exception:
        # Never remove a destination if mkdir failed: another process may own it.
        if created_by_this_invocation:
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
