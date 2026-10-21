# Local Factory Installer

**Status:** First safe bootstrap layer; not a complete factory.

Run from a clean, trusted `world-seed` Git checkout:

```bash
bash scripts/install_local_factory.sh
```

The installer archives the exact committed seed tree into a versioned local release under `~/.local/share/world-seed-factory`, creates a project-local Python environment, installs the seed's declared development dependencies (preferring `uv`, with a standard Python/pip fallback), and writes private state under `~/.local/state/world-seed-factory`. It installs the complete committed script/tool set, not just the machine collector. It refuses a dirty source checkout and will not overwrite an existing release or report. Re-running it at the same commit reuses the versioned release and creates a new timestamped report.

The machine profile is allowlisted and does not read credential files, inspect environment-variable values, or upload data. The private report can include platform and tool versions. Repository names and paths are not collected unless the collector is separately run with its explicit repository-scan option.

## Explicit non-goals

This first installer does **not** install or reconfigure Organs, start services, create API credentials, alter shell startup files, push private data to GitHub, or configure remote delivery. It only records whether `/srv/organs` exists. Those actions require a discovered service contract, explicit destination and authorization, and separate verification. Never treat a successful bootstrap as proof that APIs, BUS, or project recovery are working.

## Current recovery boundary

- Reinstallable: this installer and the allowlisted collector, from a trusted seed checkout.
- Preserved locally: timestamped machine profile and install manifest, with owner-only permissions.
- Not yet configured: project/user-data collection beyond the machine profile, secure delivery destination, API/BUS wiring, credential provisioning, and restore acceptance tests.

The next factory increment is to define a private, explicit data manifest and delivery adapter that can validate destination permissions before any transfer. Do not upload raw machine profiles or private inventory to a public repository.
