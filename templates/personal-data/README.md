# Personal Data Package Template

This is a generic structure for owner-controlled personal records. It contains no real personal data.

## Rules

- Keep personal records separate from operator preferences and project source code.
- Use a private destination with stricter access controls than public project documentation.
- Maintain a manifest listing each deliberately included record, its source, date, purpose, sensitivity, and disclosure restriction.
- Preserve original exports as received; work on separate copies.
- Never ingest or publish everything by default. Select records for a specific purpose and authorized task.
- Do not place credentials, tokens, private keys, or recovery codes in this package.
- Never expose private record names, contents, or the private destination identifier in public factory reports.
- Setup and restore must not overwrite existing records. Missing or inaccessible records must be reported as such, not silently treated as recovered.

A directory created from this template is not itself a backup. Actual records require a separate, verified preservation and restore process.
