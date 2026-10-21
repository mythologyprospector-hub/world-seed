#!/usr/bin/env python3
"""Dependency-free structural checks for the world-seed repository."""
from pathlib import Path
import sys

REQUIRED_FILES = (
    ".github/workflows/world-seed-checks.yml",
    "MISSION.md",
    "MISSION-RESET-AND-ACCEPTANCE.md",
    "PROFILE_PACKAGES.md",
    "templates/MISSION.md",
    "templates/project/PROJECT_TEMPLATE_VERSION",
    "templates/project/AGENTS.md",
    "templates/project/CONSTITUTION.md",
    "templates/project/DOCS.md",
    "templates/project/HUMAN.md",
    "templates/project/MACHINE.md",
    "templates/project/ORGANS.md",
    "templates/project/README.md",
    "scripts/create_project.py",
    "tests/test_create_project.py",
    "tests/test_mission_template.py",
    "tests/test_portable_profile_boundary.py",
    "README.md",
    "LICENSE",
    "AGENTS.md",
    "CONSTITUTION.md",
    "HUMAN.md",
    "BOOTSTRAP.md",
    "REPOSITORY_MODEL.md",
    "PROJECT_SEED_ABSORPTION.md",
    "AUTOMATION.md",
    "AUDIT_SYSTEM.md",
    "CONSISTENCY_STANDARD.md",
    "MACHINE_PROFILE.md",
    "FACTORY_INSTALLER.md",
    "scripts/install_local_factory.sh",
    "scripts/collect_machine_profile.py",
    "BASH_PROMPT.md",
    "RECOVERY.md",
    "ONBOARDING_PROMPT.md",
    "profiles/ACCOUNT_PROFILE.template.md",
    "requirements-dev.txt",
    "schemas/audit-finding.schema.json",
    "templates/audit-finding.template.json",
    "templates/expected-inventory.template.json",
    "templates/expected-contracts.template.json",
    "scripts/validate_seed.py",
    "scripts/validate_audit_findings.py",
    "scripts/validate_audit_schema.py",
    "scripts/audit_account_inventory.py",
    "scripts/audit_backup_coverage.py",
    "scripts/audit_branch_safeguards.py",
    "scripts/audit_findings_ledger.py",
    "scripts/audit_report_findings.py",
    "scripts/compare_audit_baselines.py",
    "scripts/export_governance_settings.py",
    "scripts/export_github_operating_records.py",
    "scripts/inspect_cross_repository_contracts.py",
    "scripts/inspect_repository_documents.py",
    "scripts/inspect_repository_layout.py",
    "scripts/private_report.py",
    "scripts/reconcile_expected_inventory.py",
    "scripts/run_account_audit.py",
    "scripts/prepare_local_handoff_backup.sh",
    "scripts/verify_source_artifacts.py",
    "tests/test_audit_account_inventory.py",
    "tests/test_audit_backup_coverage.py",
    "tests/test_audit_branch_safeguards.py",
    "tests/test_audit_contract.py",
    "tests/test_audit_findings_ledger.py",
    "tests/test_audit_report_findings.py",
    "tests/test_compare_audit_baselines.py",
    "tests/test_export_governance_settings.py",
    "tests/test_export_github_operating_records.py",
    "tests/test_inspect_cross_repository_contracts.py",
    "tests/test_inspect_repository_documents.py",
    "tests/test_inspect_repository_layout.py",
    "tests/test_private_report.py",
    "tests/test_reconcile_expected_inventory.py",
    "tests/test_run_account_audit.py",
    "tests/test_validate_audit_findings.py",
    "tests/test_validate_audit_schema.py",
    "tests/test_collect_machine_profile.py",
    "tests/test_install_local_factory.py",
    "tests/test_verify_source_artifacts.py",
    "tests/test_validate_seed.py",
)

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
