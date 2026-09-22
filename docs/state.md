# Project state — durable context

Fast rehydration for a fresh Brain session. **Stores no live repository
state** (no SHA outside `## Historical anchors`, no queue, no branch layout,
no test counts — stale the moment anyone commits). Derive live state:

| question | source of truth |
|---|---|
| commit, branch, remote sync | `git status`, `git rev-parse` |
| round queued / in flight / delivered? | `fw.py status`, `docs/rounds/`; `docs/briefs/active.md` is legacy until round 027 finishes |
| Builder branch unmerged? | `git branch -a`, `git worktree list` |
| push hook configured? | `git config --get core.hooksPath` |
| CI result | the run for that exact SHA |
| past rounds | `docs/rounds/`, `docs/briefs/archive/`, `git log` |
| per-format status | `python -m retroformats report` |

History: [`docs/archive/state-history.md`](archive/state-history.md).

## Architecture invariants

Pipeline: `sources → canonical data (data/, formats/) → validation
(retroformats/validate.py) → generated output (dist/)` — detail in
[`architecture.md`](architecture.md), [`format-schema.md`](format-schema.md).
Rulings easy to get wrong and expensive to rediscover:

- **`legality_basis` is a policy claim, not an availability fact.**
  `historical-policy` needs actual period tournament-policy evidence; "no
  evidence a card was legal" is *not* "evidence policy prohibited it".
- **A format's `period.snapshot` is independent of its pool's
  `cutoff_date`** (Edison: snapshot `2010-04-24`, pool cutoff `2010-05-10`).
  Allowed to differ; don't "fix" one to match the other.
- **`implementationStatus`** (`schemas/common.schema.json`) **is the
  acceptance bar**; `verified` needs strong primary/period evidence, not
  community consensus.
- **`implementation_status.overall` has no derivation rule** (a per-format
  judgement, weakest-axis convention, round 5); **status drift is limited to
  `banlist`/`card_pool`** (round 5, exhaustive). No derivation rule or third
  drifted axis without a brief.
- **`schemas/*.json` are documentation, not enforcement** — the real gate is
  `retroformats/validate.py` (round 6).
- **Errata v1→v2 migration is complete**; don't reintroduce v1. **Python:
  standard library only.**

## Canonical formats

Three; a fourth needs an owner-approved direction first (`AGENTS.md`). Live
status per format: `python -m retroformats report`.

| format | snapshot | pool basis |
|---|---|---|
| `2005-04-goat` | 2005-04-01 | extensional (Ignis GOAT whitelist) |
| `2010-03-edison` | 2010-04-24 | release-cutoff |
| `2011-09-tengu` | 2011-09-17 | release-cutoff |

- **GOAT parity is entry-for-entry, not byte-identical** (Ignis's file has a
  duplicated line, so hashes legitimately diverge — `## Historical anchors`).
- **Edison's rule profile is intentionally `partial`**: five flags remain
  unresolved ([`research/edison-rules.md`](research/edison-rules.md) §5a).
  Honest, not an oversight.

## Parked research — do not reopen without new evidence

**Tokyo Dome / `1999-08-tokyo-dome`** (target 1999-08-26). Detail:
[`research/yugi-kaiba-format-source-gate.md`](research/yugi-kaiba-format-source-gate.md)
+ packet + `format-atlas-progress.json` (id `135`); certified pool digest
under `## Historical anchors`. Restriction hypothesis (unresolved, blocking):
Raigeki, Dark Hole, Trap Hole each Limited-to-1; 0 Forbidden/Semi-Limited.
`legality_basis` is `community-retrospective`; `snapshot`/`pool_cutoff`
deliberately differ — don't re-collapse. Canonicalization is
`UNRESOLVED_BLOCKING`/`BLOCKED_BY_BOTH`: six axes must each reach `PROVEN`.
`battle_calculation` is resolved; `deck_out`/`trap_activation_frequency`
remain `NOT_REPRESENTABLE`. Restriction-list evidence is tier C,
unauthenticated. Don't restart or canonicalize on volume of research alone.

**Erratum v2** — [`research/erratum-state-model-v2.md`](research/erratum-state-model-v2.md),
frozen, sixteen properties, proven against the 296-record corpus. Don't
redesign without a concrete counterexample found while implementing.

## Owner decision — standing role chats (since 2026-09-16)

The owner keeps **one standing Builder chat and one separate Verifier chat**,
reused across rounds; fresh or cleared only after a rejection, or when very
long, stated explicitly with a reason. A Verifier prompt never goes into the
Builder's chat. Every prompt tells the agent to re-derive state from the
repository, not the conversation — overriding the framework's fresh-context
preference in those two cases only.

## Operating policy — the framework is done being built

Set by the owner on 2026-08-31: **stop polishing the framework, use it.**

- **No further workflow/framework changes without a concrete, observed
  problem** — not "this could be cleaner".
- **Larger, related briefs**, to amortise review.
- **Tier review depth proportionally** — deep for historical claims and
  canonical data; light for mechanical/bookkeeping.
- **Brain may fix genuinely trivial housekeeping directly, kept narrow** —
  canonical data or an evidence-level claim goes to the Builder regardless.
- **Topology: Brain, one Builder, one standing Verifier** (owner,
  2026-09-16; `AGENTS.md` § Topology says why). Still no parallel
  executors without an *observed* bottleneck.
- **The owner stays courier and model-chooser**, unless that becomes
  genuine friction.

**Evidence-gathering period: the next 5-10 genuine rounds**, then fix the
specific bottleneck actually observed, not speculatively.

## Open items and sequencing judgements

`docs/roadmap.md` is canonical for what is open. Sequencing reasoning it
doesn't record:

- **The ordered/unordered chronology redesign**
  ([`research/edison-behaviour-gaps.md`](research/edison-behaviour-gaps.md))
  **gates further chronology research** — the data model can't record the
  answer yet. Prefer Phase-1 hardening over breadth meanwhile: no new
  historical format while roadmap Phase-1 items remain open.
- **Format Library's "previous status" markers are unreliable as a class**
  (round 13) — membership only, never deltas. Landed: UDE Appendix A is the
  **August 1, 2005 revision** (attests April 1, not continuity through
  August).
- **An unreviewed second run of round 13 is parked, not adopted:** ref
  `preserve/round13-alt-run-1bec139` — a different primary source for the
  September 2010 changeover, to re-verify from source, never copy.
- **Materialisation repairs only pool-content drift**
  (`pool.materialization-drift`); every other `pool.*` error still refuses.

## Owner preferences

- **One project folder** — no siblings; per-role worktrees nest under
  `.worktrees/` (`AGENTS.md` § Topology).
- **The owner's interface is conversation** — never a repo file or diff.
- **Copy-paste blocks organised** — sections/paragraphs, no manual
  line-wrapping in a code block (lands as hard newlines elsewhere).
- **README banner:** data-dense designs rejected three times (last
  2026-09-22). Approved: a checklist, one row per started format, four
  columns (Banlist, Card pool, Rules, Card text), one symbol per cell, a
  small legend, one summary line at most; detail lives in the full atlas.

## Historical anchors

- GOAT generated lflist ≡ Ignis's reference list, entry-for-entry: EDOPro
  content hash `0x28E9FC02` (order- and name-independent).
- Tokyo Dome certified pool (2026-08-30, vs. an independent community cube,
  370/370 common, 0 divergent): 19 products, 370 cards, digest
  `f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`. A
  mismatch means the certification needs redoing, not that the number is
  stale.
- Erratum v2 frozen against the 296-record corpus.
- The duel engine builds on Linux and macOS only; Windows evidence comes
  from the CI `engine` job.
