#!/usr/bin/env bash
# Install a versioned local factory from the exact committed seed tree.
set -Eeuo pipefail
umask 077

SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
for command in git python3 install tar; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'ERROR: required command not found: %s\n' "$command" >&2
    exit 2
  fi
done
if ! git -C "$SOURCE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'ERROR: run this installer from a Git checkout.\n' >&2
  exit 2
fi
if [[ -n "$(git -C "$SOURCE_ROOT" status --porcelain --untracked-files=normal)" ]]; then
  printf 'ERROR: source checkout has uncommitted changes; commit or clean it before installation.\n' >&2
  exit 2
fi
REV="$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
FACTORY_HOME="${WORLD_SEED_FACTORY_HOME:-$HOME/.local/share/world-seed-factory}"
STATE_HOME="${WORLD_SEED_STATE_HOME:-$HOME/.local/state/world-seed-factory}"
OPERATOR_PROFILE_DESTINATION="${WORLD_SEED_OPERATOR_PROFILE_DESTINATION:-}"
PERSONAL_DATA_DESTINATION="${WORLD_SEED_PERSONAL_DATA_DESTINATION:-}"
INTAKE_DOCK_DESTINATION="${WORLD_SEED_INTAKE_DOCK_DESTINATION:-}"
INTAKE_DOCK_LANE="${WORLD_SEED_INTAKE_DOCK_LANE:-}"
INTAKE_DOCK_REMOTE_OWNER="${WORLD_SEED_INTAKE_DOCK_REMOTE_OWNER:-}"
INTAKE_DOCK_REMOTE_REPOSITORY="${WORLD_SEED_INTAKE_DOCK_REMOTE_REPOSITORY:-}"
INTAKE_DOCK_REMOTE_CONFIRM_TARGET="${WORLD_SEED_INTAKE_DOCK_REMOTE_CONFIRM_TARGET:-}"
if [[ -n "$OPERATOR_PROFILE_DESTINATION" && -z "$PERSONAL_DATA_DESTINATION" ]] || [[ -z "$OPERATOR_PROFILE_DESTINATION" && -n "$PERSONAL_DATA_DESTINATION" ]]; then
  printf 'ERROR: set both WORLD_SEED_OPERATOR_PROFILE_DESTINATION and WORLD_SEED_PERSONAL_DATA_DESTINATION, or neither.\n' >&2
  exit 2
fi
if [[ -n "$INTAKE_DOCK_DESTINATION" && -z "$INTAKE_DOCK_LANE" ]] || [[ -z "$INTAKE_DOCK_DESTINATION" && -n "$INTAKE_DOCK_LANE" ]]; then
  printf 'ERROR: set both WORLD_SEED_INTAKE_DOCK_DESTINATION and WORLD_SEED_INTAKE_DOCK_LANE, or neither.\n' >&2
  exit 2
fi
if [[ -n "$INTAKE_DOCK_REMOTE_OWNER$INTAKE_DOCK_REMOTE_REPOSITORY$INTAKE_DOCK_REMOTE_CONFIRM_TARGET" ]]; then
  if [[ -z "$INTAKE_DOCK_REMOTE_OWNER" || -z "$INTAKE_DOCK_REMOTE_REPOSITORY" || -z "$INTAKE_DOCK_REMOTE_CONFIRM_TARGET" ]]; then
    printf 'ERROR: remote Intake Dock provisioning requires owner, repository, and exact confirmation together.\n' >&2
    exit 2
  fi
  if [[ -z "$INTAKE_DOCK_DESTINATION" || -z "$INTAKE_DOCK_LANE" ]]; then
    printf 'ERROR: remote Intake Dock provisioning also requires the local Dock destination and lane.\n' >&2
    exit 2
  fi
fi
PROFILE_PACKAGES_STATUS="not_configured"
INTAKE_DOCK_STATUS="not_configured"
INTAKE_DOCK_REMOTE_STATUS="not_configured"
RELEASE="$FACTORY_HOME/releases/$REV"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="$STATE_HOME/machine-profile-$STAMP.json"
MANIFEST="$STATE_HOME/install-$STAMP.tsv"

# Refuse timestamp collisions before changing the release pointer or materializing destinations.
if [[ -e "$REPORT" || -L "$REPORT" || -e "$MANIFEST" || -L "$MANIFEST" ]]; then
  printf 'ERROR: generated output path already exists; refusing to overwrite.\n' >&2
  exit 2
fi

# Validate every configured destination together before creating the release pointer or writing any package.
PREFLIGHT_ARGS=(
  --template-root "$SOURCE_ROOT/templates"
  --factory-home "$FACTORY_HOME"
  --state-home "$STATE_HOME"
  --intake-dock-template-root "$SOURCE_ROOT/templates/intake-dock"
)
if [[ -n "$OPERATOR_PROFILE_DESTINATION" && -n "$PERSONAL_DATA_DESTINATION" ]]; then
  PREFLIGHT_ARGS+=(--operator-destination "$OPERATOR_PROFILE_DESTINATION")
  PREFLIGHT_ARGS+=(--personal-data-destination "$PERSONAL_DATA_DESTINATION")
fi
if [[ -n "$INTAKE_DOCK_DESTINATION" && -n "$INTAKE_DOCK_LANE" ]]; then
  PREFLIGHT_ARGS+=(--intake-dock-destination "$INTAKE_DOCK_DESTINATION")
  PREFLIGHT_ARGS+=(--intake-dock-lane "$INTAKE_DOCK_LANE")
fi
if [[ -n "$INTAKE_DOCK_REMOTE_OWNER" ]]; then
  PREFLIGHT_ARGS+=(--remote-dock-owner "$INTAKE_DOCK_REMOTE_OWNER")
  PREFLIGHT_ARGS+=(--remote-dock-repository "$INTAKE_DOCK_REMOTE_REPOSITORY")
  PREFLIGHT_ARGS+=(--remote-dock-confirm-target "$INTAKE_DOCK_REMOTE_CONFIRM_TARGET")
fi
python3 "$SOURCE_ROOT/scripts/preflight_factory_destinations.py" "${PREFLIGHT_ARGS[@]}"

mkdir -p "$FACTORY_HOME/releases" "$STATE_HOME"
chmod 700 "$STATE_HOME"

if [[ -e "$RELEASE" ]]; then
  if [[ ! -f "$RELEASE/scripts/collect_machine_profile.py" || ! -x "$RELEASE/.venv/bin/python" || ! -f "$RELEASE/FACTORY_INSTALLER.md" ]]; then
    printf 'ERROR: existing release is incomplete; refusing to overwrite: %s\n' "$RELEASE" >&2
    exit 2
  fi
else
  staging="$FACTORY_HOME/releases/.staging-$REV-$$"
  if [[ -e "$staging" ]]; then
    printf 'ERROR: staging path already exists; refusing to overwrite: %s\n' "$staging" >&2
    exit 2
  fi
  mkdir -m 700 "$staging"
  cleanup() { [[ ! -d "$staging" ]] || rm -rf -- "$staging"; }
  trap cleanup EXIT

  # Archive only tracked files at the selected commit; ignored local files are excluded.
  git -C "$SOURCE_ROOT" archive "$REV" | tar -x -C "$staging"
  if command -v uv >/dev/null 2>&1; then
    uv venv --python python3 "$staging/.venv"
    uv pip install --python "$staging/.venv/bin/python" -r "$staging/requirements-dev.txt"
  else
    python3 -m venv "$staging/.venv"
    "$staging/.venv/bin/python" -m pip install --disable-pip-version-check -r "$staging/requirements-dev.txt"
  fi
  mv -- "$staging" "$RELEASE"
  trap - EXIT
fi

# Provision the exact owner-approved private remote only after local preflight and release preparation.
if [[ -n "$INTAKE_DOCK_REMOTE_OWNER" ]]; then
  "$RELEASE/.venv/bin/python" "$RELEASE/scripts/provision_intake_dock.py" \\
    --owner "$INTAKE_DOCK_REMOTE_OWNER" \\
    --repo "$INTAKE_DOCK_REMOTE_REPOSITORY" \\
    --apply \\
    --confirm-target "$INTAKE_DOCK_REMOTE_CONFIRM_TARGET"
  INTAKE_DOCK_REMOTE_STATUS="verified_private"
fi

# "current" is a convenience pointer inside this installer's own directory.
ln -sfn "releases/$REV" "$FACTORY_HOME/current"
if [[ -n "$OPERATOR_PROFILE_DESTINATION" && -n "$PERSONAL_DATA_DESTINATION" ]]; then
  "$RELEASE/.venv/bin/python" "$RELEASE/scripts/materialize_profile_packages.py" \
    --template-root "$RELEASE/templates" \
    --operator-destination "$OPERATOR_PROFILE_DESTINATION" \
    --personal-data-destination "$PERSONAL_DATA_DESTINATION"
  PROFILE_PACKAGES_STATUS="materialized"
fi
if [[ -n "$INTAKE_DOCK_DESTINATION" && -n "$INTAKE_DOCK_LANE" ]]; then
  "$RELEASE/.venv/bin/python" "$RELEASE/scripts/materialize_intake_dock.py" \
    --template-root "$RELEASE/templates/intake-dock" \
    --destination "$INTAKE_DOCK_DESTINATION" \
    --lane "$INTAKE_DOCK_LANE"
  INTAKE_DOCK_STATUS="materialized_local_only"
fi
"$RELEASE/.venv/bin/python" "$RELEASE/scripts/collect_machine_profile.py" --output "$REPORT"
{
  printf 'schema_version\t1\n'
  printf 'installed_at_utc\t%s\n' "$STAMP"
  printf 'source_commit\t%s\n' "$REV"
  printf 'release_path\t%s\n' "$RELEASE"
  printf 'machine_profile_report\t%s\n' "$REPORT"
  if [[ -d /srv/organs ]]; then printf 'organs_detected\tyes\n'; else printf 'organs_detected\tno\n'; fi
  printf 'remote_delivery\tnot_configured\n'
  printf 'profile_packages\t%s\n' "$PROFILE_PACKAGES_STATUS"
  printf 'intake_dock\t%s\n' "$INTAKE_DOCK_STATUS"
  printf 'intake_dock_remote\t%s\n' "$INTAKE_DOCK_REMOTE_STATUS"
  printf 'api_bus_changes\tnot_attempted\n'
} > "$MANIFEST"
chmod 600 "$REPORT" "$MANIFEST"

printf '\nFactory bootstrap installed.\nRelease: %s\nPrivate state: %s\nManifest: %s\n' "$RELEASE" "$STATE_HOME" "$MANIFEST"
printf 'No credentials were read, no data was uploaded, and no API/BUS services were changed.\n'
