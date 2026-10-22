# World Seed See

**First live-terminal milestone:** run a command normally while sharing a bounded snapshot of its output with the existing private `miracle-depot` repository.

From the World Seed checkout:

```bash
python3 scripts/world_seed_see.py -- python -m unittest discover -s tests -v
```

Or any other explicit command:

```bash
python3 scripts/world_seed_see.py -- git status --short --branch
```

The wrapper:
- streams combined stdout/stderr to your terminal as the command runs;
- verifies that `gh` can access `mythologyprospector-hub/miracle-depot` and that GitHub reports it private;
- prints a stable report link, creates that report before starting the command, and refreshes it about every 10 seconds while output is produced;
- retains at most 24 KiB by default (adjust with `--limit-bytes`, up to 1 MiB), applies basic heuristic redaction, and records process status;
- returns the wrapped command's exit code.

## Important limits

This is **near-real-time snapshots, not a live terminal session**. The report updates roughly every 10 seconds, and an assistant can reread that URL when asked; the upload does not itself push a notification into the chat. GitHub creates a commit for each report update, so the snapshots are retained in repository history.

Redaction is not a guarantee. **Do not wrap commands that print passwords, access tokens, private keys, recovery codes, sensitive personal information, or other material you would not want stored in the private repository and its history.** Private means visible to people/apps authorized for that repository, not only to this conversation. Only commands deliberately placed after `--` are run and shared; ordinary shell commands are not captured.

If the private-repository check or initial upload fails, the command is not started. A later upload failure is reported, but the command continues and its output remains visible locally.
