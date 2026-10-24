# First Factory Trial Evidence — 2026-10-23

**Status:** First disposable trial demonstrated; formal acceptance remains provisional.
**Scope:** Evidence Notebook generated from World Seed alone. This is a disposable acceptance fixture, not a publication candidate.

## Factory verification

- World Seed generator suite: **12/12 tests passed** against a temporary archive of GitHub `main`.
  - Evidence: [terminal journal report](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/world-seed-see-20261023T132509Z-4f06b705.txt)
- The generator tests cover complete bundle/provenance manifest, generated builder guidance, destination safety, invalid input, portable output, and local Markdown links.
- The generated project's manifest hashes for `MACHINE.md` and `README.md` matched the factory template at generation time. Those files were subsequently changed by the builder.

## Fresh builder result

The fresh builder produced a working local-first evidence notebook with:
- claims and source records in SQLite;
- evidence excerpts linked to claims and sources with `supports`, `challenges`, or `context` relationships;
- unresolved questions attached to claims;
- a `show` command that displays the claim, linked evidence/source locator, and open questions;
- standard-library-only setup and no network service.

The builder's documentation describes acceptance criteria, design decisions, assumptions, and limitations.

## Verification evidence

- Behavior tests: **2/2 passed**.
- Python compilation: passed.
- CLI help/startup: passed.
- Fresh temporary-directory documented workflow: successfully initialized a clean SQLite database, created a claim and source, attached supporting evidence, added an open question, and displayed the resulting record.
  - Evidence: [test and compile report](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/world-seed-see-20261023T134423Z-9615a4c5.txt)
  - Evidence: [fresh-directory workflow report](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/world-seed-see-20261023T134548Z-6d2f17a2.txt)

### Provenance check qualification

The last command returned exit code 1 because it compared the current, builder-edited `README.md` and `MACHINE.md` against hashes in the generation manifest. Those hashes intentionally describe the files as generated, not as immutable forever. The mismatch is expected after edits and is **not evidence of a factory defect**. The generator's own test checks each manifest hash against each generated file immediately after generation and passed.

## Privacy check

A targeted scan of the generated canon found the local checkout path only in `MACHINE.md`. No matches were found for the searched credential patterns. This was a limited heuristic scan, not a guarantee that all content is free of sensitive information. The project remains local and disposable; do not publish it as-is.

## Trial findings and limitations

1. **Useful first slice demonstrated.** The application works end to end for its stated initial use case.
2. **Builder compliance miss:** the generated `AGENTS.md` instructs the builder to replace every license placeholder, but the generated `LICENSE` still contains `<YEAR>` and `<COPYRIGHT HOLDER>`. This is a documented release-readiness defect in the disposable fixture, not proof of a generator failure. No ownership details were invented and no publication is authorized by this trial.
3. The application remains deliberately small: no editing/deletion commands, synchronization, source fetching, or automated truth assessment. These are recorded limitations, not demonstrated acceptance blockers for the chosen first slice.
4. The privacy scan was targeted and heuristic; it does not establish a universal no-secret guarantee.

## Provisional conclusion

This trial provides positive evidence that World Seed can generate a coherent project scaffold that a fresh builder can turn into a useful, tested, reproducible end-to-end slice. Do not claim the entire World Seed finish line is met solely from this result: the bounded terminal-visibility path's full privacy/exit-status acceptance and any remaining required mission checks must be confirmed against their own evidence. Fix only concrete acceptance blockers and repeat the trial if a factory-caused blocker is demonstrated.
