#!/usr/bin/env bash
# Read-only with respect to GitHub: clone and export every repository visible
# under the selected owner. Does not archive, delete, rename, or change repos.
set -Eeuo pipefail
umask 077

OWNER="${1:-mythologyprospector-hub}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${2:-$HOME/archive/github-handoff-$STAMP}"

for command in gh git; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'ERROR: required command not found: %s\n' "$command" >&2
    exit 2
  fi
done

if ! gh auth status >/dev/null 2>&1; then
  printf 'ERROR: GitHub CLI is not authenticated. Run: gh auth login\n' >&2
  exit 2
fi

if [[ -e "$DEST" ]]; then
  printf 'ERROR: destination already exists; refusing to overwrite: %s\n' "$DEST" >&2
  exit 2
fi

mkdir -p "$DEST/checkouts" "$DEST/bundles" "$DEST/zips"
chmod 700 "$DEST" "$DEST/checkouts" "$DEST/bundles" "$DEST/zips"
printf 'owner\tvisibility\tarchived\tresult\n' > "$DEST/manifest.tsv"
chmod 600 "$DEST/manifest.tsv"

inventory="$DEST/.inventory.tsv"
if ! gh repo list "$OWNER" --limit 1000 --json nameWithOwner,visibility,isArchived \
    --jq '.[] | [.nameWithOwner, .visibility, (.isArchived|tostring)] | @tsv' > "$inventory"; then
  printf 'ERROR: could not list repositories for %s; no repositories processed.\n' "$OWNER" >&2
  exit 1
fi
chmod 600 "$inventory"

count=0
failed=0
while IFS=$'\t' read -r repo visibility archived; do
  [[ -n "${repo:-}" ]] || continue
  count=$((count + 1))
  name="${repo#*/}"
  checkout="$DEST/checkouts/$name"
  bundle="$DEST/bundles/$name.bundle"
  zipfile="$DEST/zips/$name.zip"
  printf '[%s] Backing up %s (%s, archived=%s)\n' "$count" "$repo" "$visibility" "$archived"

  if gh repo clone "$repo" "$checkout" && \
     git -C "$checkout" fetch --all --tags --prune && \
     git -C "$checkout" bundle create "$bundle" --all && \
     git -C "$checkout" archive --format=zip --output="$zipfile" HEAD; then
    chmod 700 "$checkout"
    chmod 600 "$bundle" "$zipfile"
    printf '%s\t%s\t%s\tOK\n' "$repo" "$visibility" "$archived" >> "$DEST/manifest.tsv"
  else
    failed=$((failed + 1))
    printf '%s\t%s\t%s\tFAILED\n' "$repo" "$visibility" "$archived" >> "$DEST/manifest.tsv"
    printf 'WARNING: backup failed for %s; continuing. See output above.\n' "$repo" >&2
  fi
done < "$inventory"

rm -f "$inventory"
printf '\nBackup directory: %s\nRepositories found: %s\nFailures: %s\n' "$DEST" "$count" "$failed"
printf 'This does not back up GitHub issues, pull-request discussions, Actions artifacts, releases, or settings.\n'
printf 'Do not delete or archive any GitHub repository until the backups have been checked.\n'
if (( failed > 0 )); then exit 1; fi
