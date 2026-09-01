# Project state — durable context

Fast rehydration for a fresh Brain session.

**This file deliberately stores no live repository state.** No current
SHA, no "what's queued", no branch or worktree layout, no per-machine
setup status, no test counts. Those go stale the moment anyone commits —
including when Brain commits its own housekeeping, which is exactly how
this file previously ended up contradicting itself within a single round.

Derive live state instead:

| question | source of truth |
|---|---|
| current commit, branch, sync with remote | `git status`, `git rev-parse` |
| is a Worker round in flight / queued? | [`docs/briefs/active.md`](briefs/active.md) — it states its own `Status:` |
| is a Worker branch unmerged? | `git branch -a`, `git worktree list` |
| is the local push hook configured? | `git config --get core.hooksPath` |
| what did CI say? | the run for that exact SHA |
| what did past rounds do? | [`agents/model-notes.md`](agents/model-notes.md), `docs/briefs/archive/`, `git log` |
| current implementation status per format | `python -m retroformats report` |

`/status` runs all of that. What follows is only what git *cannot* tell
you: rulings, blockers, owner preferences, and why things are parked.

## Architecture invariants

Pipeline: `sources → canonical data (data/, formats/) → validation
(retroformats/validate.py) → generated output (dist/)`. Concepts are kept
separate and shareable across formats: banlists, card pools, rule
profiles, errata, releases, and a `format.json` per format that is mostly
references. Detail: [`architecture.md`](architecture.md),
[`format-schema.md`](format-schema.md).

Rulings that are easy to get wrong and expensive to rediscover:

- **`legality_basis` is a policy claim, not an availability fact.**
  `historical-policy` requires actual period tournament-policy evidence.
  "No evidence a card was legal" is *not* "evidence policy prohibited
  it" — that conflation has already produced one wrong classification.
- **A format's `period.snapshot` is independent of its pool's
  `cutoff_date`.** Edison is the worked example: snapshot `2010-04-24`,
  pool cutoff `2010-05-10`. They are allowed to differ; don't "fix" one to
  match the other.
- **`implementationStatus` (`schemas/common.schema.json`) is the
  acceptance bar Brain reviews against.** `verified` specifically requires
  corroboration by strong primary/period evidence — not modern community
  consensus, however unanimous.
- **`implementation_status.overall` has no derivation rule** — not in
  `format.schema.json` (which only requires the key), not in the
  validator, not in `cli.py` or the atlas generator, all of which print
  the stored value verbatim. It is a per-format judgement, conventionally
  bottlenecked by the weakest axis. Established by round 5; don't
  re-investigate, and don't add a derivation rule without a brief.
- **Status drift is structurally limited to `banlist` and `card_pool`.**
  Only those two axes have an underlying file with its own
  `completeness` field to fall behind. `rule_profile` and `errata` have
  no mirrorable source at all (their schemas define no `completeness`),
  so they are pure adjudications. Audited exhaustively in round 5 — a
  third drifted axis is not possible without a schema change.
- **`schemas/*.json` are documentation, not enforcement.** Nothing in
  this repository runs a generic JSON-Schema validator over `data/`:
  there is no `jsonschema` import anywhere, `Repository.load()` is a
  hand-rolled loader, and `tests/schema_check.py` is wired only to
  `erratum.schema.json`. Adding a field to a schema's `required` array
  therefore changes nothing at runtime — the real gate is always
  `retroformats/validate.py`. Established in round 6; check this before
  believing any schema edit enforces something.
- **The errata v1→v2 migration is complete; the v1 positional model is
  retired.** Don't reintroduce it.
- **Python: standard library only.** No dependency manifest, by choice.
  Don't add one.

## Canonical formats

Three, and adding a fourth needs a Brain-reviewed brief first.

| format | snapshot | pool basis |
|---|---|---|
| `2005-04-goat` | 2005-04-01 | extensional (Ignis GOAT whitelist) |
| `2010-03-edison` | 2010-04-24 | release-cutoff |
| `2011-09-tengu` | 2011-09-17 | release-cutoff |

Live status per format: `python -m retroformats report`.

Two things about these that are not derivable and cost real time to
rediscover:

- **GOAT's generated lflist is entry-for-entry identical to Project
  Ignis's reference list, not byte-identical.** Historical anchor: EDOPro
  content hash `0x28e9fc02` (order- and name-independent). Ignis's own
  shipped file contains a duplicated line, so its byte-level and in-client
  hashes legitimately diverge. This is not a bug to fix.
- **Edison's rule profile is intentionally `partial`.** Five flags are
  evidentially unresolved (SEGOC pair highest priority) —
  [`research/edison-rules.md`](research/edison-rules.md) §5a. Leaving it
  partial is the honest state, not an oversight.

## Review protocol

Brain's merge authority rests on this actually being run, every round:
independently re-diff the commit, re-run whatever the report claims to
have checked, and **re-derive at least one load-bearing claim directly**
(re-fetch the cited source, recount the entries, re-run the check). Full
checklist: [`agents/role-contracts.md`](agents/role-contracts.md).

Every round so far has justified it — reviewing the diff alone would have
missed something a direct re-derivation caught.

## Parked research — do not reopen without new evidence

### Tokyo Dome / `1999-08-tokyo-dome` (codename `yugi-kaiba`)

Target event 1999-08-26. Full detail:
[`research/yugi-kaiba-format-source-gate.md`](research/yugi-kaiba-format-source-gate.md)
(narrative) + `...-packet.json` (machine-readable packet) +
`format-atlas-progress.json` (id `135`).

- **Certified candidate pool — historical anchor, not a live value:** 19
  products, 370 canonical cards, digest
  `f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`, as
  certified 2026-08-30 against an independent community cube (370/370
  common, 0 divergent after canonicalization). If a regenerated pool no
  longer matches this digest, that means **the certification must be
  redone** — not that this number is stale.
- **Restriction hypothesis (unresolved, blocking):** Raigeki, Dark Hole,
  Trap Hole each Limited-to-1; 0 Forbidden, 0 Semi-Limited.
- **Pool `legality_basis` is `community-retrospective`** — corrected from
  a wrongly-claimed `historical-policy`. See the ruling above for why.
- **`snapshot = 1999-08-26` and `pool_cutoff = 1999-08-25` are
  deliberately different fields.** Corrected once already; don't
  re-collapse them.
- **Canonicalization is `UNRESOLVED_BLOCKING` / `BLOCKED_BY_BOTH`** —
  historical evidence *and* engine representability each independently
  block. Six load-bearing axes must each reach `PROVEN`;
  `scope_class_status` is itself unresolved and gates which
  representability path even applies. Per-axis values live in the packet.
- **Engine representability:** `battle_calculation` is **resolved, not a
  blocker** — pinned ocgcore's default already matches the historical
  rule. Don't reopen without a new engine-behaviour finding. `deck_out`
  and `trap_activation_frequency` remain confirmed `NOT_REPRESENTABLE` and
  are active blockers.
- **Source authentication:** the V Jump interior crop — the actual
  restriction-list evidence — remains tier C: single point of hosting,
  chain unauthenticated. The daiti0526 collector photographs are a
  different, stronger-in-kind *candidate* source, but only for event
  date/venue/identity of a **parallel Game Boy tournament**. They are
  never restriction-list evidence, and are correctly described as
  "purporting to be" a period document rather than authenticated as one.

**Do not:** restart Tokyo research from scratch, redesign the six-axis
canonicalization gate absent a concrete discovered defect, or canonicalize
this format because substantial research already exists.

### Erratum v2 architecture

[`research/erratum-state-model-v2.md`](research/erratum-state-model-v2.md)
— frozen, sixteen named properties, proven against the 296-record corpus
as of the migration (historical anchor: that corpus is what the freeze was
proven against). Don't redesign without a concrete counterexample found
during implementation.

## Operating policy — the framework is done being built

Set by the owner on 2026-08-31, after a setup phase in which roughly
two-thirds of Brain's commits were framework rather than project content.
**That phase is over.** The architecture is to be *used*, not polished.

- **No further workflow/framework changes unless real project development
  exposes a concrete problem.** Not "this could be cleaner" — an actual
  observed failure.
- **Larger briefs where work is naturally related.** Amortise briefing and
  review overhead instead of artificially splitting closely-related
  verification or data tasks into separate rounds.
- **Tier review depth proportionally.** Deep independent re-derivation for
  historical claims, canonical data, and any proposed general rule. Lighter
  proportional review for mechanical, docs and bookkeeping changes.
- **Brain may fix genuinely trivial housekeeping directly, and must keep
  that narrow.** The risk is "this looks easy" gradually turning Brain into
  the implementation Worker and hollowing out independent review. Anything
  touching canonical data, or asserting an evidence level, goes to a
  Worker even when the change itself is small.
- **No parallel Workers yet.** Brain plus one fresh Worker is simple and
  working. Propose parallel lanes only if Worker throughput becomes an
  *observed* bottleneck — with evidence, not pre-optimisation.
- **The owner stays courier and model-chooser.** Copying prompts and
  reports is not currently the bottleneck, and per-task model choice
  across vendors is valued. Revisit only if it becomes genuine friction.

**Evidence-gathering period: the next 5-10 genuine project rounds.** If
progress is still slower than it should be after that, identify the
*specific* bottleneck from what actually happened — Worker speed, review
cost, brief sizing, research difficulty — and fix that one thing. Do not
optimise speculatively before then.

## Open items and sequencing judgements

`docs/roadmap.md` is canonical for what is open. What it doesn't record —
the *sequencing* reasoning:

- **The ordered/unordered chronology representation redesign
  ([`research/edison-behaviour-gaps.md`](research/edison-behaviour-gaps.md))
  gates further chronology research.** Doing more chronology work on those
  records before the representation lands is premature — the data model
  cannot correctly record the answer yet.
- **Prefer Phase-1 hardening over breadth.** Do not start a new historical
  format while roadmap Phase-1 items remain open; they are more
  informative per unit of effort than another format.
- **A parallel April-2005 round produced three findings `191630e` does not
  have.** A Worker round briefed against a checkout that predated this
  framework duplicated roadmap item 2 and landed nowhere; its transcription
  and `verified` status are superseded by `191630e`. Three things in it are
  additive, recorded here so they do not depend on a local ref surviving
  (they also sit on the branch/tag `preserve/april-2005-40cc995`):
  1. A **primary source for `superseded_by_date`** — the gap `191630e`'s own
     notes name as unclosed: an official UDE page dated "EFFECTIVE OCTOBER
     1ST 2005", Wayback capture `20051026142552` of
     `upperdeckentertainment.com/yugioh/uk/forbidden_advanced_new.htm`.
  2. **Format Library's "previous status" markers are unreliable as a
     class** — 5 wrong in April 2005 (newly-printed cards defaulted to
     `previous: unlimited` where Yugipedia has "not yet released"), matching
     the 3 already recorded for March 2010. Current-list membership matched
     exactly both times. Use it for membership, never for deltas.
  3. UDE Appendix A is the **August 1, 2005 revision**: it proves the April
     list was still in force in August, not that it went unamended from
     April. With a pre-effective-date Pojo capture it brackets the period;
     alone it does not.
  **Sequencing: fold these into the roadmap item 3 round** (March 2010 ->
  `verified`), which re-touches the same sources and the same supersession
  question. Not worth a standalone round.

- **The Claude adapter has two demonstrated defect classes, and the fix
  pattern for one already exists here.** (a) The `Stop` hook launches the
  inbox script through a single hard-coded interpreter name, so on a host
  lacking that name it exits 127 and silently writes no Worker report —
  and this project genuinely has hosts of both kinds, so neither name is
  safe hard-coded. `.githooks/pre-push` already solves this by probing
  both in a `/bin/sh` shim, with `tests/test_push_readiness.py` as the
  testing precedent. (b) A Worker can run in Brain's primary checkout;
  this has now happened twice, so the standing instruction to re-check
  `git branch`/`git status` is not prevention and needs a mechanism that
  fails closed. Both are queued as one framework round.

- **Roadmap 1a is large and open-ended** (undated era rulings, needing
  period rulings documents that may not exist). Prefer better-bounded
  items unless the owner asks for it directly.

## Owner preferences

- **One project folder.** No sibling directories next to the repo; the
  Worker worktree is nested inside it
  ([`agents/worktree-mechanism.md`](agents/worktree-mechanism.md)).
- **The owner's interface is conversation.** They should never need to
  open a repo file, run a git command, or judge a diff to keep the loop
  moving — see `AGENTS.md` § Authority.
- **Copy-paste blocks must be organised** — sections or paragraphs, not
  one dense wall of text, and no manual line-wrapping inside a code block
  (it lands as hard newlines when pasted elsewhere).
- **README banner:** the current data-dense design (rows of shipped
  formats with per-axis status badges) was rejected as still not the right
  shape — the ask is a *different visual language*, more visual and less
  text-dense, not a tighter version of the same concept. Don't iterate on
  density again.
