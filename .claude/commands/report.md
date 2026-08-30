---
description: Run python -m retroformats report to summarize implementation status across all canonical formats. Pass --verbose (or -v) for the per-card substitution/divergence detail.
argument-hint: [-v]
allowed-tools: Bash
---

Run `python -m retroformats report` (add `-v`/`--verbose` if the user
passed it in `$ARGUMENTS`) and summarize the result:

1. Headline: which formats are shown and their `overall`
   `implementation_status` (missing/stub/partial/complete/verified).
2. For any format below `verified`, name the specific area (banlist /
   card pool / rule profile / errata) holding it back, if the report
   surfaces that -- this is usually more useful to the human than the
   overall label alone.
3. Only with `-v`: don't paste the full per-card list into chat unless
   the user asks for it -- summarize the counts (e.g. "44 known-divergent
   substitutions, 41 chronologically-ordered, 0 gaps") and offer to show
   specific entries.

This is read-only and side-effect-free -- safe to run any time, doesn't
touch canonical data or `dist/`.
