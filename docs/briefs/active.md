# Active brief

Status: **queued, not started**. One brief lives here at a time; when
Worker completes it (accepted or rejected by Brain), move this file to
`docs/briefs/archive/<NNN>-<date>-<slug>.md` (zero-padded, check the
archive for the last-used number) and replace it with the next one, or
leave a one-line "no brief queued" placeholder.

---

## MODE: DATA/SCHEMA

## Goal

Transcribe the published April 2005 TCG Forbidden/Limited/Semi-Limited
list from Yugipedia using the existing importer
(`retroformats/importers/yugipedia_banlist.py`), reconcile it against
`data/banlists/tcg/2005-04.json` (currently derived only from Project
Ignis's GOAT whitelist counts), and upgrade `completeness` from
`"partial"` honestly if -- and only to the extent -- the reconciliation
actually supports it.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report.

## Why this is next

Roadmap item 2 (`docs/roadmap.md`, Phase 1): "Cross-check the April 2005
banlist. The GOAT banlist is currently derived from Ignis's whitelist
counts. Transcribe the published April 2005 TCG list (Yugipedia `April
2005 Lists (TCG)`) with the existing importer, reconcile, upgrade
`completeness` to `complete`/`verified`, and document any deliberate GOAT
community deviations if found." Round 3 in this project's Worker-round
sequence, following the same pattern as round 2's March 2010 banlist
verification (`docs/briefs/archive/002-2026-08-30-march-2010-banlist-verification.md`)
but bigger: that banlist already had a Yugipedia source cited and just
needed reconciling against a Konami primary; this one has no Yugipedia
source at all yet and needs the actual import run for the first time.

## Relevant context

Read:

- `data/banlists/tcg/2005-04.json` -- the record in question. Its own
  `notes` field already states the exact gap: "TODO: cross-check against
  the April 2005 TCG list as published (Yugipedia) and upgrade
  completeness; the effective/superseded dates ... also need a primary
  citation."
- `retroformats/importers/yugipedia_banlist.py` -- read its module
  docstring and `parse_limitation_list` function. It was used for the
  March 2010 banlist; that's your worked example for exact usage
  (`data/sources.json`'s `yugipedia-march-2010` /
  `konami-limited-2010-03` entries show what the resulting `sources`
  array should look like in shape, not content).
- `docs/edopro-research.md` -- pins the BabelCDB revision this project
  uses (`BabelCDB da54f28` as of this writing; confirm it's still what's
  pinned, don't assume this brief's copy is current).
- `docs/releases.md` around the `--babelcdb <BabelCDB clone>` examples --
  shows how other importers in this codebase expect a local BabelCDB
  clone to be passed.

You do not need to read anything about Tokyo Dome, Edison rules, or the
erratum v2 model -- unrelated to this task.

## Scope

1. Fetch the Yugipedia page's wikitext via the MediaWiki parse API
   (`https://yugipedia.com/api.php?action=parse&page=April%202005%20Lists%20(TCG)&format=json&prop=wikitext`
   -- confirm the exact page title/URL yourself; don't assume it matches
   this exact string without checking, Yugipedia's naming isn't always
   predictable from the March 2010 precedent).
2. Clone BabelCDB at the pinned revision (or confirm a usable local
   checkout already exists) so `yugipedia_banlist.py` can resolve card
   names to passcodes.
3. Run the importer to produce a candidate record for `tcg-2005-04`.
4. Reconcile the importer's output against the current
   `data/banlists/tcg/2005-04.json` entries, the same way round 2
   reconciled the March 2010 banlist -- entry by entry, not sampled.
5. If they match exactly: update `completeness` (to `"complete"` or
   `"verified"` -- pick based on the actual bar each meets per
   `schemas/common.schema.json`'s `implementationStatus` definition;
   don't default to the higher one just because a source now exists),
   add the new source(s) to `data/sources.json` and to this banlist's
   `sources` array, and record in `notes` exactly what was checked and
   against what.
6. If they don't match: this is the interesting case the roadmap itself
   anticipates ("document any deliberate GOAT-community deviations if
   found"). Do not silently overwrite `entries` to match the Yugipedia
   transcription -- GOAT's own defining characteristic (see
   `formats/2005-04-goat/format.json`'s `errata_overrides` and its
   `notes.md`) is `reference_parity` with the Project Ignis whitelist,
   which may deliberately differ from a literal reading of the original
   April 2005 announcement. Report every discrepancy by name, and
   propose (don't unilaterally decide) whether each one looks like a
   transcription error to fix, a genuine parity deviation to document, or
   something else -- see "Non-goals" below on where your authority to act
   on this stops.
7. Also confirm (or fix, if you can source it) the `effective_date`
   (2005-04-01) / `superseded_by_date` (2005-10-01) citation gap the
   `notes` field flags -- these are currently "community-documented"
   without a primary cite.

## Non-goals

- Do not change GOAT's `entries` array to resolve a discrepancy against
  Yugipedia without flagging it first -- see step 6. This brief verifies
  and reconciles; it does not re-adjudicate GOAT's parity policy.
- Do not touch `2010-03.json`, Edison, or Tengu data.
- Do not touch `formats/2005-04-goat/format.json`'s
  `implementation_status.banlist` unless you've confirmed (the same way
  round 2 did for Edison) whether it's meant to mirror the banlist file's
  own `completeness` -- check `retroformats/validate.py` yourself rather
  than assume round 2's Edison finding carries over unchanged.
- Do not touch `dist/` directly -- if anything changes that affects the
  built lflist, regenerate via `python -m retroformats build`, don't
  hand-edit.

## Protected invariants

- `docs/architecture.md` and `formats/2005-04-goat/notes.md` describe
  GOAT's output as required to stay entry-for-entry identical to Project
  Ignis's reference list (EDOPro content hash `0x28e9fc02`,
  order/name-independent -- see `docs/state.md` for the exact
  "entry-for-entry, not byte-identical" distinction, already corrected
  once this session for being overstated). `tests/test_repo_data.py`
  pins this. If your reconciliation surfaces a genuine discrepancy
  between Yugipedia's transcription and the current entries, resolving
  it must not silently break that parity test -- if fixing a real error
  would change GOAT's output, that's a bigger, separate decision to flag,
  not something to push through in this brief.
- Card names must resolve to real BabelCDB passcodes -- the importer
  already refuses to guess on an unresolved/ambiguous name; don't work
  around that by hand-resolving a name it rejected without saying so
  explicitly in your report.

## Required investigation

1. Confirm BabelCDB's pinned revision from `docs/edopro-research.md`
   before cloning -- don't use `main`/`HEAD` of BabelCDB, which would be
   inconsistent with everything else this repo cites it against.
2. Do the full entry-by-entry reconciliation, not a sample.
3. Check whether `formats/2005-04-goat/format.json`'s
   `implementation_status.banlist` field is code-derived from anything
   (grep `retroformats/validate.py` and `retroformats/model.py` for
   `implementation_status` yourself -- round 2 already did this for a
   different format and found no code linkage, but verify it still holds
   here rather than citing round 2's finding as if it's a project-wide
   guarantee).

## Acceptance criteria

- A real, evidenced answer on whether GOAT's current banlist entries
  match the primary/community-published April 2005 list, not a guess.
- Every discrepancy (if any) named explicitly, with a proposed
  classification (transcription error / deliberate parity deviation /
  unclear), not silently resolved.
- If upgraded: correct `completeness` value for what was actually
  checked, new sources cited in both `data/sources.json` and the
  banlist's own `sources` array, `notes` states what was verified and how.
- `tests/test_repo_data.py`'s GOAT parity/hash tests still pass.
- Full test suite, validator, and `build --check` all still pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Work in the sibling worktree if running locally alongside a Brain session
on the same machine (`docs/agents/worktree-mechanism.md`) -- fetch
`origin/main` first and branch from there
(e.g. `worker/verify-2005-04-banlist`). Do not merge to `main` yourself.
Do not push unless asked.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- The exact Yugipedia page/URL used, and the BabelCDB revision cloned.
- The full reconciliation result: exact match, or every discrepancy found
  (name each card, both sides' status) with your proposed classification
  for each.
- What you changed, file by file, and why.
- Exact output of the three validation commands.
- Anything left genuinely uncertain -- state it as uncertain.
