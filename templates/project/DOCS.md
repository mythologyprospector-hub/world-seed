# Project Documentation Standard

**Status:** Canonical baseline
**Governs:** Documentation shape and consistency within this repository.
**Last verified:** 2026-10-22

## Format and naming

- Use UTF-8 Markdown with Unix line endings and no trailing whitespace.
- Use one H1 per document and a logical heading hierarchy; do not skip heading levels.
- Use established uppercase names for canonical top-level documents and scoped lowercase directories for supporting material.
- Keep one canonical document per purpose. Update it rather than creating duplicate or misleadingly named `*_new_final.md` files.
- Use relative links for repository-local files and verify links when adding or moving documents.
- Use fenced code blocks with language labels for commands and examples.

## Status language

Distinguish **proposed**, **implemented**, **tested**, **verified**, **deprecated**, and **superseded** accurately. "Last verified" means checked against actual project state on that date, not merely edited.

## Quality

Lead with purpose, boundary, and what matters next. Prefer plain language, short paragraphs, meaningful lists, and tables only when comparison is clearer. Keep terminology, names, dates, and status labels consistent. Distinguish observed facts, assumptions, recommendations, decisions, and unknowns.

Documentation must describe actual behavior. Do not promise capabilities the project cannot demonstrate. Preserve required attribution, copyright notices, and license conditions.


## Public repository launch readiness

If this repository is public, prepare a social preview image before calling it launch-ready.

- Use PNG, JPG, or GIF under 1 MB; 1280 × 640 pixels is preferred.
- Keep the source image in the repository.
- Upload it through GitHub repository Settings → Social preview → Edit → Upload an image. Committing the image alone does not apply it.
- Do not claim it is applied until the owner confirms the setting was completed. Check GitHub's current requirements before preparing it.
