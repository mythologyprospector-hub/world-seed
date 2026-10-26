#!/usr/bin/env bash
# Read-only acceptance diagnostic for the installed world-seed-see launcher.
# Run from a World Seed checkout through the launcher being inspected:
# world-seed-see -- bash scripts/inspect_world_seed_see_launcher.sh
set -u

launcher="$(command -v world-seed-see || true)"
if [[ -z "$launcher" ]]; then
  printf 'ERROR: world-seed-see is not resolvable through PATH in this shell.\n'
  exit 2
fi

resolved="$(readlink -f -- "$launcher" 2>/dev/null || printf '%s' "$launcher")"
printf 'launcher_path=%s\n' "$launcher"
printf 'resolved_launcher_path=%s\n' "$resolved"
printf 'current_checkout=%s\n' "$(git rev-parse --show-toplevel 2>/dev/null || printf '(not in a Git checkout)')"
printf '\n===== WORLD SEED WORKTREES =====\n'
git worktree list --porcelain 2>&1 || true
printf '\n===== LAUNCHER TARGET SUMMARY =====\n'
if [[ -f "$resolved" ]]; then
  if head -n 1 -- "$resolved" 2>/dev/null | grep -q '^#!'; then
    sed -n '1,80p' "$resolved"
  else
    printf 'Launcher target is not a shebang script; source excerpt omitted.\n'
  fi
else
  printf 'Resolved launcher target is not a regular file.\n'
fi
printf '\n===== CURRENT CHECKOUT STATUS =====\n'
git status --short --branch 2>&1 || true
printf '\nDiagnostic complete. This reports evidence; it does not change files.\n'
