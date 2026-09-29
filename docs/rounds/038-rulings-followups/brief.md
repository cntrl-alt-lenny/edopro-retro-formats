# 038-rulings-followups: Settle round 037's source conflicts under the owner's tie-break rules, and fix what its review found

Tier: 2
Mode: data and implementation
Supersedes: none

## Goal

Round 037 left a small set of records unresolved because two period
sources disagree. On 2026-09-29 the owner set how such conflicts are
decided (`docs/state.md`, "Owner decisions — card scripts", "Period
rulings"):

- **Rule 1 (standing since round 036).** A Konami document current at the
  snapshot outranks an earlier UDE-era ruling on the same point.
- **Rule 2 (new).** Between two versions of the same UDE FAQ, the latest
  version in force at the snapshot governs. In practice the 2008-12 pages
  outrank the 2005 UDE page at Edison (2010-04-24) and Tengu (2011-09-17).
- **Unchanged.** A conflict inside one entry of one document stays
  unresolved: neither rule decides it.

When this round is done:

- **A.** Every conflict these two rules decide is decided, in the record,
  with the evidence.
- **B.** Round 037's review findings are fixed.
- **C.** The rulings gate needs no by-name exemptions.

Do the parts in order, and put each part's evidence in the report.

## Context

- `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`,
  `docs/state.md`.
- `docs/research/text-only-errata-audit.md` (round 037). Section 5 has
  every record's verdicts and passages, and section 8 the thin-evidence and
  conflict list. Its sources are in `data/sources.json`.
- `docs/rounds/037-text-only-errata-audit/`: the brief, and both reports.
  The Verifier's findings are what part B fixes.
- The rulings checks: `rulings_check` in `schemas/erratum.schema.json` and
  `schemas/custom-card.schema.json`, `docs/errata.md`, and
  `retroformats/validate.py`.
- On the owner's Mac, `python3` is 3.9. Use `/opt/homebrew/bin/python3.13`
  for project commands. Yugipedia's MediaWiki API and `web.archive.org` both
  answered in rounds 035 to 037; Yugipedia is only a pointer.

## A. Apply the two rules

These are the records Brain found where round 037 recorded a conflict
between period sources, or an inference that one of the rules may settle:

- **Necrovalley** (`necrovalley.json`), at Edison. Konami's 2009 Raging
  Battle rulings (Lava Dragon's non-targeting effect does not resolve under
  Necrovalley), and the FAQ entries for Agido and Exchange of the Spirit,
  against the card's own FAQ sentence ("will NOT negate effects that do not
  target"). Rule 1 applies if the Raging Battle document is a Konami
  document current at 2010-04-24, on the same point.
- **YZ-Tank Dragon** (`yz-tank-dragon.json`). The FAQ wording on the four
  contact-Fusion monsters changed between the 2005 UDE page and the 2008-12
  pages. Rule 2 applies.
- **Xy Dragon Cannon, Xyz Dragon Cannon, Xz Tank Cannon.** The 2005 UDE
  page says "except" (a permanent lock). The 2008-12 and 2009 pages name
  only the Extra Deck and the Graveyard, and nothing names the banished
  zone. Rule 2 makes the 2008-12 pages govern. What they say, and do not
  say, about a return from banishment decides the verdict. If they are
  silent on it, the verdict stays `unresolved`, and you say so.
- **Blaze Accelerator** (`d3`). Two lines of one FAQ entry conflict.
  Neither rule applies. Leave it as it is, and confirm that in the report.

**Look for the rest.** Search section 5 of the research document, and
every record's `rulings_check`, for any other case where a Konami document
and an earlier UDE ruling, or two versions of the same UDE FAQ, disagree on
a claimed difference. Apply the rules to each, and list them all, even if
the answer is none.

**For each case:**

- Re-read both sources at the archived capture.
- Record which rule decides it, and set the verdict.
- Then act as round 037's part C did: reclassify, add evidence, or leave as
  it is. Keep every existing passage, and move any replaced summary into
  the review notes with the date and the rule applied.
- Record the governing ruling in the transition's rulings check, and the
  outranked one as the finding it was. Do not delete it.

**List changes are allowed** where a decided case changes a card's state at
a snapshot. Each changed line in Edison's or Tengu's list is explained by a
record here, and tested in the duel engine as round 037 tested Imperial
Custom and Senet Switch. The GOAT hash `0x28E9FC02` must not move. If it
would, stop on that record.

## B. Fix what round 037's review found

1. **The research document's wrong sentence.** Section 8 of
   `docs/research/text-only-errata-audit.md` says "No data was changed for
   anything in this list". But round 037 changed data for Imperial Custom,
   Senet Switch, Soul Rope, Toon Summoned Skull, and the eight narrowed
   records (Blaze Accelerator, Boss Rush, Red-Eyes Wyvern, Tri-Blaze
   Accelerator, Wild Fire, Anteatereatingant, Ancient Fairy Dragon, and
   Blackwing - Sirocco the Dawn's `c0`). Correct the sentence so it says
   exactly which entries changed data and how, and add a dated note saying
   the correction was made.
2. **Stale counts in the format notes.** The `notes` fields in
   `formats/2011-09-tengu/format.json` ("exactly 52 historical
   implementations … 161 … 9") and `formats/2010-03-edison/format.json`
   ("currently 72 historical implementations") no longer match the counts
   the tests pin. Make them true, in a way that cannot silently go stale
   again: either a test that fails when a number in a note drifts from the
   computed count, or no number in the note, just a pointer to the report
   command. Explain which you chose.
3. **Night Assailant's `owner_decision`** (`data/errata/night-assailant.json`).
   Round 037 filled it with the owner's 2026-09-23 decision, plus a
   sentence the owner did not write. On 2026-09-29, having seen round 037's
   evidence, the owner confirmed that Night Assailant stays held back. That
   evidence: both effects target; whether the effect was optional is
   unresolved. Rewrite the entry to record that confirmation, dated
   2026-09-29, in words the owner can own. Do not act on the ruling.
4. **Dark Necrofear `c2`** (`dark-necrofear.json`). Its summary says the
   effect does not target. The 2008-12-16 A–C FAQ page says "that effect
   selects 1 target" (the Chaos Command Magician entry). Narrow the summary
   to what is still claimed, keep the old text in the notes, and give the
   transition a full rulings check.

## C. Remove the by-name exemptions from the gate

`ERRATUM_RULINGS_GATE_EXEMPT` in `retroformats/model.py` exempts three
transitions by name: Dark Necrofear `c2`, Fushioh Richie, and Second Coin
Toss. Give each a rulings check from the evidence rounds 035 to 037 already
hold, re-reading anything you cite. Then delete the exemption list and its
code path. Show the gate failing first on one of the three with its check
removed.

## Scope and non-goals

What may change:

- the `data/errata/` records named above, and any others part A finds
- `data/sources.json`
- the `notes` of the two format files (part B2 only; nothing else in
  `formats/`)
- the model and validator, for C (and B2 if a check is chosen)
- tests
- regenerated `dist/`
- the hash and count pins, rebuilt so that every old value is still
  asserted where it can still be reached
- the CI engine floor, only by the net number of engine tests added
- the research document (correct and add; delete nothing else)
- `docs/roadmap.md`, `docs/errata.md`, `dist/README.md`,
  `docs/engine-testing.md` and `formats/2011-09-tengu/notes.md`

Non-goals:

- **No new generated card, and no edit to any Ignis script.** The points
  where a shipped Ignis variant script and a ruling disagree (section 9 of
  the research document) stay listed for a later round. Record them in
  `docs/roadmap.md` item 7 if they are not already there.
- No re-audit of `unresolved` verdicts that are not conflicts. No
  reclassification on anything but rule 1 or rule 2.
- No change to `docs/state.md`, to what CI's `check` job runs, or to the
  GOAT list. No new dependency.
- Night Assailant stays held back, and Second Coin Toss stays as it is.

## Invariants

- **Epistemics** (`AGENTS.md`). The two rules decide precedence between
  sources. They do not turn silence into a ruling, an OCG ruling into a TCG
  one, or a Yugipedia line into a source. No suite run is evidence for a
  historical claim.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`). The
  one exception is the sentence in B1, which is shown to be wrong; its
  correction is dated. Extend round 037's passages-kept check to every
  record changed here, and show it failing on a deleted passage.
- **No rule is loosened** (`AGENTS.md`). C removes an exemption; it adds
  none.
- **The validator ends with 0 errors.** Explain every warning added or
  removed, line by line against `main`, grouped by code.

## Acceptance criteria

- Every case in A, the named ones and any found, has the rule applied (or
  the reason neither applies), both passages quoted from the archived
  captures, and the resulting verdict and action.
- Every changed list line is explained, with a duel-engine test that the
  intended card is used. GOAT is byte-identical to `main`.
- B1 to B4 are done as described. B2's check, if chosen, fails when a note
  drifts.
- `ERRATUM_RULINGS_GATE_EXEMPT` no longer exists, and the gate fails first
  as described in C.
- CI is green at the final head, with the engine job's
  `executed=… skipped=0` line.

## Required evidence

- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`, grouped by code
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and the skips
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`
- `python scripts/generate_format_atlas.py --check`
- `python3 tools/fw.py check`
- `git diff main HEAD -- dist/lflists/`: every changed line
- the old and new Edison and Tengu hashes
- the CI run URL at the final head
- the failing-first runs for C, for B2 (if a check), and for the
  passages-kept check

Your report (`docs/rounds/038-rulings-followups/builder.md`) has the Worker
card's sections. Under Verified, it gives a table of every case in A with
its rule, verdict and action, and a line for each of B1 to B4 and C. Under
Open questions, it gives anything that needs the owner, in plain product
terms.
