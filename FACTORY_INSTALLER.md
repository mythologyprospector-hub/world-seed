# Local Factory Installer

**Status:** First safe bootstrap layer; not a complete factory.

Run from a clean, trusted `world-seed` Git checkout:

```bash
bash scripts/install_local_factory.sh
```

The installer archives the exact committed seed tree into a versioned local release under `~/.local/share/world-seed-factory`, creates a project-local Python environment, installs the seed's declared development dependencies (preferring `uv`, with a standard Python/pip fallback), and writes private state under `~/.local/state/world-seed-factory`. It installs the complete committed script/tool set, not just the machine collector. It refuses a dirty source checkout and will not overwrite an existing release or report. Re-running it at the same commit reuses the versioned release and creates a new timestamped report.

The machine profile is allowlisted and does not read credential files, inspect environment-variable values, or upload data. The private report can include platform and tool versions. Repository names and paths are not collected unless the collector is separately run with its explicit repository-scan option.

## Optional private package initialization

The installer can initialize the generic operator-profile and personal-data package structures in two explicitly chosen local destinations. Set **both** environment variables, or neither:

```bash
export WORLD_SEED_OPERATOR_PROFILE_DESTINATION="$HOME/path-you-have-chosen/operator-profile"
export WORLD_SEED_PERSONAL_DATA_DESTINATION="$HOME/path-you-have-chosen/personal-data"
bash scripts/install_local_factory.sh
```

Replace the example paths with destinations you have deliberately selected. Do not paste private records or credentials into these commands. If neither variable is set, package initialization is skipped. Setting only one is an error.

For new destinations, the materializer creates owner-only directories and files on POSIX systems. Existing destinations must already be private. Byte-identical template files are accepted on reruns; unrelated files are preserved; conflicting files cause a safe refusal rather than an overwrite. The install manifest records only whether package initialization was configured, not the private destination paths.

This step initializes **local package structure only**. It does not create GitHub repositories, push data, collect personal records, or prove that existing private packages are backed up. Keep source exports separate and use the explicit recovery tooling for any capture/restore operation.

## Explicit non-goals

This first installer does **not** install or reconfigure Organs, start services, create API credentials, alter shell startup files, push private data to GitHub, or configure remote delivery. It only records whether `/srv/organs` exists. Those actions require a discovered service contract, explicit destination and authorization, and separate verification. Never treat a successful bootstrap as proof that APIs, BUS, or project recovery are working.

## Current recovery boundary

- Reinstallable: this installer and the allowlisted collector, from a trusted seed checkout.
- Preserved locally: timestamped machine profile and install manifest, with owner-only permissions.
- Not yet configured: collection of actual project/user data, secure remote delivery, API/BUS wiring, credential provisioning, and end-to-end restore acceptance. Optional local package initialization creates only generic directory structure; it is not a data backup.

The next factory increment is to connect an owner-approved private destination and explicit data manifest to verified capture/restore. Do not upload raw machine profiles or private inventory to a public repository.


## Intake Dock local scaffold (separate capability)

`scripts/materialize_intake_dock.py --destination "$HOME/private-intake-dock" --lane episteme` initializes local private staging folders and generic handoff instructions for the explicitly selected project lane (replace `episteme` with the intended lane slug). It is not yet called by `install_local_factory.sh`. The companion helpers now exist as separate building blocks: `scripts/provision_intake_dock.py` plans by default and can create/verify one private repository only with explicit exact-target confirmation; `scripts/package_intake_dock_handoff.py` creates a hash-verified local package from explicit files; `scripts/transfer_intake_dock_handoff.py` validates locally by default and requires explicit exact-target confirmation for a live transfer. The local synthetic package-to-Git round-trip is covered by `tests/test_intake_dock_synthetic_handoff.py`. None of these helpers is automatically invoked by the installer, and live GitHub transfer, remote Codex discovery, and post-wipe recovery acceptance remain unproven.
