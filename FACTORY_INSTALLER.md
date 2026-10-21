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


## Intake Dock bootstrap (opt-in, local only)

Before changing the `current` pointer or materializing either profile package or the Dock, the installer runs `scripts/preflight_factory_destinations.py`. It validates all configured destinations together, rejects overlapping destinations, and checks existing template files/permissions for conflicts. A conflict in one destination must not leave another configured package partially initialized. This is a read-only preflight; it does not prove recovery or configure a remote repository.

The installer can regenerate the local Dock scaffold when both destination and lane are explicitly configured:

```bash
export WORLD_SEED_INTAKE_DOCK_DESTINATION="$HOME/private-intake-dock"
export WORLD_SEED_INTAKE_DOCK_LANE="episteme"
bash scripts/install_local_factory.sh
```

Replace the example destination and lane with the exact choices for this machine. Setting only one variable is an error. The install manifest records `intake_dock\tmaterialized_local_only` or `intake_dock\tnot_configured`; it does not record the private destination path. This step initializes folders and generic instructions only—it does not transfer content or create a remote repository.

### Optional guarded private GitHub repository provisioning

The installer can also create-or-verify the configured private Intake Dock repository, but only when all three remote settings are supplied together: `WORLD_SEED_INTAKE_DOCK_REMOTE_OWNER`, `WORLD_SEED_INTAKE_DOCK_REMOTE_REPOSITORY`, and `WORLD_SEED_INTAKE_DOCK_REMOTE_CONFIRM_TARGET`. The confirmation value must exactly equal `OWNER/REPOSITORY`; the owner must match the already authenticated personal account in `gh`; and the local Dock destination/lane must also be configured. Before any remote call, the installer validates the target, confirmation, local destinations, and `gh` availability. Provisioning happens only after local preflight and release preparation. An existing public repository is refused, never made private automatically. If authentication/access is unavailable, the installer fails honestly; it does not upload files or alter repository access.

Do not invent a target or use this as a blanket approval. Select the intended existing private repository or an explicitly approved new name, then put that exact owner/name/confirmation into the operator's private configuration. The public seed contains no private target defaults. The manifest records only `intake_dock_remote\tverified_private` or `intake_dock_remote\tnot_configured`, never the repository name. This verifies the remote container only; it does not transfer userdata or prove Codex discovery/recovery.

Separate helpers now exist: `scripts/provision_intake_dock.py` plans by default and can create/verify one private repository only with explicit exact-target confirmation; `scripts/package_intake_dock_handoff.py` creates a hash-verified local package from explicit files; `scripts/transfer_intake_dock_handoff.py` validates locally by default and requires explicit exact-target confirmation for a live transfer. The local synthetic package-to-Git round-trip is covered by `tests/test_intake_dock_synthetic_handoff.py`. Remote provisioning and transfer are not automatically invoked by the installer, and live GitHub transfer, remote Codex discovery, and post-wipe recovery acceptance remain unproven.

## Shared runtime services

The factory's runtime-plumbing direction is documented in [RUNTIME_PLUMBING.md](RUNTIME_PLUMBING.md). Organs is an implementation source to audit, not a required dependency of World Seed or every generated project. The current installer intentionally does not install, configure, start, or recover Organs. Any future adoption must be capability-scoped, security-reviewed, versioned, testable, and recoverable; the legacy Organs installer is not copied blindly.
