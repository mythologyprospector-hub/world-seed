#!/usr/bin/env python3
"""Plan or explicitly provision one private GitHub Intake Dock repository.

Default behavior is offline planning. Live calls are limited to the authenticated
personal account; organization repositories, uploads, and access changes are out
of scope. An existing public repository is never made private automatically.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from typing import Any, Protocol, Sequence

OWNER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\\Z")
REPO_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?\\Z")


class RepositoryNotFound(Exception):
    """GitHub explicitly reported that the exact repository does not exist."""


class GitHubClient(Protocol):
    def authenticated_login(self) -> str: ...
    def get_repository(self, full_name: str) -> dict[str, Any]: ...
    def create_private_repository(self, name: str) -> dict[str, Any]: ...


class GhCliClient:
    """Small gh adapter. Never prints tokens or changes existing visibility."""

    @staticmethod
    def _run(args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["gh", *args], check=False, capture_output=True, text=True, timeout=20
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"GitHub CLI request failed: {type(exc).__name__}") from exc
        if result.returncode != 0:
            raise RuntimeError("GitHub CLI request failed; inspect gh auth status and repository access")
        return result.stdout

    def authenticated_login(self) -> str:
        value = json.loads(self._run(["api", "user"]))
        login = value.get("login") if isinstance(value, dict) else None
        if not isinstance(login, str) or not login:
            raise RuntimeError("GitHub API did not return the authenticated account login")
        return login

    def get_repository(self, full_name: str) -> dict[str, Any]:
        try:
            output = self._run(["api", f"repos/{full_name}"])
        except RuntimeError as exc:
            # Only a clear HTTP 404 is interpreted as absent. Permission and
            # authentication errors fail closed rather than triggering creation.
            message = str(exc)
            if "HTTP 404" in message:
                raise RepositoryNotFound(full_name) from exc
            raise
        value = json.loads(output)
        if not isinstance(value, dict):
            raise RuntimeError("GitHub API returned an invalid repository response")
        return value

    def create_private_repository(self, name: str) -> dict[str, Any]:
        output = self._run([
            "api", "user/repos", "-f", f"name={name}",
            "-F", "private=true", "-f",
            "description=Private Intake Dock staging repository",
        ])
        value = json.loads(output)
        if not isinstance(value, dict):
            raise RuntimeError("GitHub API returned an invalid repository creation response")
        return value


def _validate_target(owner: str, name: str) -> str:
    if not OWNER_PATTERN.fullmatch(owner):
        raise ValueError("owner must be a valid GitHub personal-account login")
    if not REPO_PATTERN.fullmatch(name):
        raise ValueError("repository name must be a lowercase repository-style slug")
    return f"{owner}/{name}"


def _verify_private_target(repository: dict[str, Any], expected_full_name: str) -> None:
    actual = repository.get("full_name")
    if not isinstance(actual, str) or actual.casefold() != expected_full_name.casefold():
        raise ValueError("GitHub returned a repository other than the exact requested target")
    if repository.get("private") is not True:
        raise ValueError("target repository is not private; refusing to change visibility automatically")


def provision(
    client: GitHubClient,
    owner: str,
    name: str,
    *,
    apply: bool = False,
    confirmed_target: str | None = None,
) -> dict[str, str]:
    """Dry-run by default; provision only after exact-target confirmation."""
    target = _validate_target(owner, name)
    if not apply:
        return {
            "status": "planned",
            "target": target,
            "action": "verify existing private repository or create one if absent",
            "remote_calls_made": "false",
        }
    if confirmed_target != target:
        raise ValueError(f"live provisioning requires --confirm-target {target}")
    login = client.authenticated_login()
    if login.casefold() != owner.casefold():
        raise ValueError("owner must match the authenticated personal account; organization provisioning is out of scope")

    try:
        existing = client.get_repository(target)
    except RepositoryNotFound:
        created = client.create_private_repository(name)
        _verify_private_target(created, target)
        # Re-read from GitHub to verify the authoritative persisted state.
        verified = client.get_repository(target)
        _verify_private_target(verified, target)
        return {"status": "created-and-verified-private", "target": target, "remote_calls_made": "true"}

    _verify_private_target(existing, target)
    return {"status": "existing-private-verified", "target": target, "remote_calls_made": "true"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True, help="authenticated personal GitHub account login")
    parser.add_argument("--repo", required=True, help="lowercase repository name")
    parser.add_argument("--apply", action="store_true", help="perform GitHub API calls; otherwise plan only")
    parser.add_argument("--confirm-target", help="repeat exact OWNER/REPO to authorize this repository operation")
    args = parser.parse_args(argv)
    try:
        result = provision(
            GhCliClient(), args.owner, args.repo,
            apply=args.apply, confirmed_target=args.confirm_target,
        )
    except (ValueError, RuntimeError, RepositoryNotFound) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
