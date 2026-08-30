# Project state

Fast rehydration for a fresh Brain session. Keep this short — point at the
detailed doc rather than duplicating it. Every fact here is a claim to
spot-check against live repo state, not a fact to relay forward unchecked.

**Last updated:** 2026-08-30, after Brain accepted and merged the first
Worker round (Tokyo Dome epistemic-wording fix, executed by a
non-Claude model) and queued the next brief.

## Repository

`cntrl-alt-lenny/edopro-retro-formats`, public, default branch `main`,
single-branch history (no long-lived branches, no PR history to date — the
established workflow is direct, reviewed-by-the-owner commits to `main`).
Pure-stdlib Python 3.10+ project; no dependency manifest exists or is
needed. CI (`.github/workflows/ci.yml`, push+PR, Python 3.10 & 3.13) runs:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

**Canonical `main` SHA as of this writing:** `1cc6e63e78a7b8681941fcb58bc53c9619cf91ee`
— verify with `git rev-parse origin/main`; do not trust this string once it's
old.

## Architecture (detail: `docs/architecture.md`, `docs/format-schema.md`)

`sources → canonical data (data/, formats/) → validation
(retroformats/validate.py) → generated output (dist/, build --check
enforced)`. Concepts are kept separate and shareable across formats:
banlists (`data/banlists/<region>/<yyyy-mm>.json`), card pools
(`data/pools/*.json`, `kind: extensional|release-cutoff`, and critically
`legality_basis: availability|historical-policy|community-retrospective` —
`historical-policy` requires actual period tournament-policy evidence, not
absence-of-contrary-evidence), rule profiles (`data/rule-profiles/*.json`),
errata (`data/errata/*.json`, now 100% migrated to the frozen "v2"
historical-event-DAG model — 296 v2 records, 0 v1 remaining), releases
(`data/releases/` + `coverage.json` + `gaps.json`), and a `format.json` per
format that is mostly references plus a `period.snapshot` (errata/chronology
reference date, independent of a release-cutoff pool's own `cutoff_date` —
Edison's snapshot `2010-04-24` vs. pool cutoff `2010-05-10` is the existing
example of these deliberately differing).

`implementationStatus` (`schemas/common.schema.json`) is the shared maturity
scale: `missing < stub < partial < complete < verified`, where `verified`
specifically requires "corroborated by strong primary/period evidence, not
merely modern community consensus" — this is the bar Brain checks Worker's
"verified"/"proven" claims against.

## Canonical formats shipped (exactly three; do not add a fourth without a Brain-reviewed brief)

| format | snapshot | pool basis | status |
|---|---|---|---|
| `2005-04-goat` | 2005-04-01 | extensional (Ignis GOAT whitelist) | shipped, `dist/lflists/2005-04-goat.lflist.conf` entry-for-entry identical to Ignis's reference list — same EDOPro content hash `0x28e9fc02` (order/name-independent), **not** byte-identical: Ignis's own shipped file has a duplicated line that makes its byte-level and in-client hashes diverge (see `docs/architecture.md`) |
| `2010-03-edison` | 2010-04-24 | release-cutoff, 3,673 cards | shipped; rule profile intentionally `partial` (5 evidentially-unresolved flags, SEGOC pair highest priority — see `docs/research/edison-rules.md` §5a) |
| `2011-09-tengu` | 2011-09-17 | release-cutoff, 4,562 cards | shipped (added 2026-08-27) |

## Current milestone

The erratum v1→v2 migration (design frozen in
`docs/research/erratum-state-model-v2.md`) and the Tengu format are the last
completed substantive format milestones (2026-08-25 and 2026-08-27). Since
then: Tokyo Dome ("yugi-kaiba" codename) research sessions (2026-08-28
through 2026-08-30, sessions 1-11), this framework install, and the first
Worker round below. No format work is in flight.

## Last accepted Worker round

**Accepted and merged (2026-08-30, commit `4624752`, executed by a
non-Claude model — Worker is model-agnostic, see `AGENTS.md`):** the Tokyo
Dome epistemic-wording fix. Both overclaim patterns flagged by external
review were corrected in `docs/research/yugi-kaiba-format-source-gate.md`
and `...-packet.json` — EXIF-authentication language ("authentic",
"genuine primary", "an actual ... Konami-issued document") reworded to
"purporting to be" / EXIF-consistent-with-capture framing; "found
anywhere" / "stronger form of the single-hosted finding" reworded to scope
explicitly to the channels actually searched. The JSON key
`content_hash_confirmation_of_single_hosting` (which itself asserted the
overclaim) was renamed to `wayback_content_hash_check_of_the_known_crop`
after confirming no code/test reads it by name. Worker also caught one
overclaim instance (`phase_g_content_completeness_result`) not listed in
the brief. No adjudication verdict, status, digest, date, or count
changed. Brain independently re-diffed every hunk, re-ran the grep checks
the commit message claimed, and ran the full suite (931 tests) before
merging — see the archived brief for the full spec:
[`docs/briefs/archive/2026-08-30-tokyo-dome-epistemic-wording-fix.md`](briefs/archive/2026-08-30-tokyo-dome-epistemic-wording-fix.md).

## In-flight / next Worker task

**Queued in [`docs/briefs/active.md`](briefs/active.md):** a
`SOURCE VERIFICATION` task on `data/banlists/tcg/2010-03.json` (roadmap
item 3). It already cites a Wayback-archived Konami primary source
(`konami-limited-2010-03`, retrieved 2026-08-19) alongside Yugipedia, but
`completeness` is still `"complete"`, not `"verified"` — meaning either
the entries were never actually reconciled card-by-card against that
primary source, or they were and the status just never got bumped. The
brief asks Worker to actually do that reconciliation and report the real
outcome (upgrade if it holds; document precisely what's missing if it
doesn't), not assume a match either way.

## Parked research — do not reopen without new evidence

**Tokyo Dome / `1999-08-tokyo-dome` (research codename `yugi-kaiba`)** —
target event 1999-08-26. Full detail:
`docs/research/yugi-kaiba-format-source-gate.md` (narrative log) +
`...-packet.json` (machine-readable evidence packet) +
`docs/format-atlas-progress.json` (id `135`, all axes `research`).

- Certified candidate pool: 19 products, 370 canonical cards, digest
  `f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`
  (cross-checked against an independent community cube: 370/370 common, 0
  divergent after canonicalization).
- Restriction hypothesis (unresolved, blocking): Raigeki, Dark Hole, Trap
  Hole each Limited-to-1; 0 Forbidden, 0 Semi-Limited.
- Recommended pool `legality_basis`: `community-retrospective` (corrected
  in session 8 from a wrongly-claimed `historical-policy` — "no evidence a
  card was legal" is not "evidence policy prohibited it").
- `target_recommendation.snapshot = 1999-08-26`; `pool_cutoff = 1999-08-25`
  — deliberately different fields (corrected in session 7).
- `canonicalization_status = UNRESOLVED_BLOCKING`, `BLOCKED_BY_BOTH`
  (historical evidence *and* engine representability each independently
  block). Six load-bearing axes must each reach `PROVEN`; `scope_class_status`
  (tournament-specific vs. general-regional) is itself unresolved and gates
  which representability path even applies.
- Engine representability: `battle_calculation` **resolved, not a blocker**
  (session 3, 2026-08-29 — pinned ocgcore's default already matches the
  historical rule; don't reopen without a new engine-behavior finding).
  `deck_out` and `trap_activation_frequency` remain confirmed
  `NOT_REPRESENTABLE` — active blockers.
- V Jump interior crop (the actual restriction-list evidence) remains
  source-authentication tier C — single point of hosting, chain
  unauthenticated. The daiti0526 collector photographs are a *different,
  stronger-in-kind candidate* source but only for event date/venue/identity
  of a *parallel* Game Boy tournament — never restriction-list evidence,
  and (as of the 2026-08-30 wording fix above) correctly described as
  "purporting to be" a period document rather than authenticated as one.

**Do not**: restart Tokyo research from scratch, redesign the six-axis
canonicalization gate absent a concrete discovered defect, or canonicalize
this format because substantial research already exists.

**Erratum v2 architecture** (`docs/research/erratum-state-model-v2.md`) —
frozen, sixteen named properties, proven against the full 296-record
corpus. Don't redesign without a concrete counterexample found during
implementation.

## Other known open items (not blocking any shipped format)

- Edison/GOAT-adjacent: 44+41-record (85 total) ordered/unordered
  chronology representation redesign recommended but **not started**
  (`docs/research/edison-behaviour-gaps.md`) — premature to do more
  chronology research on those records until this lands.
- Roadmap 1a/1b/1c/1e, 2, 3, 4b — see `docs/roadmap.md` Phase 1 follow-ups.
- Edison rule profile: 5 evidentially-unresolved flags, SEGOC pair highest
  priority (`docs/research/edison-rules.md` §5a).

## Recommended next action

Run the queued brief in `docs/briefs/active.md` (`SOURCE VERIFICATION`,
March 2010 banlist reconciliation). After that: roadmap item 2 (April 2005
GOAT banlist — currently `completeness: "partial"`, no Yugipedia source
cited at all yet, needs an actual transcription pass, not just a
reconciliation — bigger lift than item 3) is the natural next step. Do
**not** start a new historical format next; the roadmap's own Phase-1
hardening items (banlist verification, chronology) are more informative
uses of the next few slots than breadth.
