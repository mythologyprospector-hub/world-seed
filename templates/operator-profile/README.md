# Operator Profile Package Template

This directory is a **generic template**, not a real operator profile. Copy it into an owner-controlled private destination and fill only fields the owner chooses to provide.

## Purpose

Keep working preferences, collaboration conventions, approval boundaries, and environment orientation available independently of any chat or project.

## Files

- manifest.json: package metadata and disclosure boundary; never put secrets in it.
- PREFERENCES.md: operator-approved preferences and collaboration rules.

## Rules

- Keep this package private and separate from the portable World Seed.
- Never add passwords, access tokens, private keys, recovery codes, or credential values.
- Do not infer missing preferences. Mark unknown fields as unknown.
- Record provenance and review dates for mutable facts. Re-verify machine/account details before relying on them.
- Share only the specific sections needed for the current authorized task.
- Do not publish the actual private destination name or its contents in public factory records.
- Preserve existing package files during setup. Template generation must refuse to overwrite existing files unless a separately authorized migration explicitly handles them.

This template defines a starting structure; it does not prove that a package exists, that it is complete, or that access is authorized.
