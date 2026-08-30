---
description: Check or refresh the generated format atlas/banner (scripts/generate_format_atlas.py). No args checks freshness; --refresh re-pulls the pinned Format Library catalog first.
argument-hint: [--refresh]
allowed-tools: Bash
---

Run `scripts/generate_format_atlas.py` against the argument the user gave
(`$ARGUMENTS`):

- **No args** -- freshness check only: `python scripts/generate_format_atlas.py --check`.
- **`--refresh`** -- re-pull the pinned Format Library catalog first,
  then regenerate: `python scripts/generate_format_atlas.py --refresh`
  (this both refreshes `docs/format-library-catalog.json` and rewrites
  both SVGs in one pass -- there's no separate refresh-only mode).

Then:

1. Report the one-line result (`ok: ...` or `stale: ...` file list, or
   the refreshed catalog's new format count) -- don't dump SVG content.
2. If `--check` reports stale files, that means canonical data changed
   (a format's `implementation_status`, or `docs/format-atlas-progress.json`)
   without regenerating -- run `python scripts/generate_format_atlas.py`
   (no flags) to regenerate offline from current data, then re-run
   `--check` to confirm it's clean, and mention both SVG files now need
   committing.
3. If `--refresh` changed the catalog (new/removed/re-dated formats),
   say so and note that `tests/test_format_atlas.py` should be run
   before committing -- it pins catalog invariants (uniqueness,
   chronological ordering, category/era coverage) that a live refresh
   could violate if Format Library's data shifted structurally.
