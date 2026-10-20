#!/usr/bin/env python3
"""Dependency-free structural checks for the world-seed repository."""
from pathlib import Path
import sys

REQUIRED_FILES = ("README.md", "MISSION.md", "LICENSE", "AGENTS.md", "CONSTITUTION.md", "HUMAN.md", "BOOTSTRAP.md", "REPOSITORY_MODEL.md", "AUTOMATION.md", "AUDIT_SYSTEM.md", "CONSISTENCY_STANDARD.md", "MACHINE_PROFILE.md", "PROFILE_PACKAGES.md", "RECOVERY.md", "ONBOARDING_PROMPT.md", "profiles/ACCOUNT_PROFILE.template.md", "schemas/audit-finding.schema.json", "templates/audit-finding.template.json", "scripts/validate_audit_findings.py", "scripts/audit_account_inventory.py", "scripts/inspect_repository_layout.py", "scripts/inspect_repository_documents.py", "scripts/run_account_audit.py", "scripts/export_governance_settings.py", "scripts/audit_backup_coverage.py", "tests/test_export_governance_settings.py", "tests/test_audit_backup_coverage.py", "tests/test_validate_seed.py", "tests/test_audit_contract.py", "tests/test_validate_audit_findings.py", "tests/test_audit_account_inventory.py", "tests/test_inspect_repository_layout.py", "tests/test_inspect_repository_documents.py", "tests/test_run_account_audit.py")

def validate(root: Path) -> list[str]:
    """Return missing required files and broken relative Markdown links."""
    root = root.resolve()
    errors = [f"required file missing: {name}" for name in REQUIRED_FILES if not (root / name).is_file()]
    for path in sorted(root.rglob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {path.relative_to(root)}: {exc}")
            continue
        visible_lines = []
        fenced = False
        fence_marker = ""
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[:3]
                if not fenced:
                    fenced, fence_marker = True, marker
                elif marker == fence_marker:
                    fenced = False
                visible_lines.append("")
                continue
            visible_lines.append("" if fenced else line)

        for line_number, line in enumerate(visible_lines, 1):
            if "](" not in line:
                continue
            remainder = line.split("](", 1)[1]
            raw_target = remainder.split(")", 1)[0].strip()
            if not raw_target:
                continue
            target = raw_target.split()[0].strip("<>")
            if not target or "://" in target or target.startswith(("mailto:", "#", "//")):
                continue
            relative = target.split("#", 1)[0].split("?", 1)[0]
            if relative and not (path.parent / relative).resolve().exists():
                errors.append(f"{path.relative_to(root)}:{line_number}: broken local link: {target}")
    return errors

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        print(f"FAILED: {len(errors)} issue(s) found.")
        return 1
    print(f"PASS: {len(REQUIRED_FILES)} required files and local Markdown links checked.")
    print("LIMIT: semantic quality, account coverage, and recovery are not proven.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
