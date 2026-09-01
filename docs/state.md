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
- **Format Library's "previous status" markers are unreliable as a class.**
  Landed on the source records in round 13; kept here because it is a
  standing rule about a source, not a one-off incident. Newly-printed cards
  are defaulted to `previous: unlimited` where Yugipedia has "not yet
  released" — six such in the April 2005 response, three already recorded
  for March 2010. Current-list *membership* matched canonical exactly both
  times. Use it for membership, never for deltas. (The count moved 5 -> 6
  between observations of a live API, which is itself the reason the marker
  field is not evidence.)
- **The April-2005 findings from the stranded parallel round are landed.**
  Round 13 put all three on the canonical records: the UDE October 2005
  successor page as a primary source for `superseded_by_date`, the Format
  Library marker class above, and the distinction that UDE Appendix A is the
  **August 1, 2005 revision** — it attests the April list as of April 1, not
  that the list went unamended through August; a pre-effective-date Pojo
  capture is what brackets the period. Nothing here depends on the ref
  `preserve/april-2005-40cc995` any more, which is as well: that ref is
  absent from this clone, from reachable objects and from `origin`, and was
  independently confirmed missing by both Brain and Worker.

- **The Claude adapter has four demonstrated defect classes, now covered by
  framework mechanisms and regression tests.** The Stop hook probes
  `python3` then `python` through a shell shim and remains safe when neither
  is available; the Worker adapter's blocking `UserPromptSubmit` hook derives
  the Git common directory and refuses Brain's primary checkout or a
  non-`worker/*` branch; the pre-push hook is tracked executable while its
  `core.hooksPath` activation remains explicitly per-clone; and the nested
  Worker worktree is documented as per-clone state that must be derived with
  `git worktree list`, not assumed to exist. These are durable mechanism
  classes, not claims about any clone's current setup.

- **A test that asserts checkout behaviour must build the git state it
  asserts against.** The adapter's guard tests pointed at
  `<primary>/.claude/worktrees/worker` — per-clone developer state, absent on
  a fresh checkout — so CI was red for four consecutive pushes with a
  `FileNotFoundError`, and the accept-case additionally depended on whichever
  branch that worktree happened to be on. Fixed by constructing a real
  temporary repository and a real linked worktree per test. The rule
  generalises: ambient layout is not a fixture.
- **`git rev-parse --git-common-dir` returns `C:/...` on Git for Windows.**
  Classifying absolute-vs-relative by a leading `/` therefore misreads it as
  relative; the Worker guard did exactly that, prefixed the repo root, and
  fail-closed against the *correct* worktree — the guard was unusable on
  Windows and nobody had noticed, because the broken test could not express
  the case. Let `cd` resolve the value instead of classifying it. Verified
  against the real worktree: exit 2 before, exit 0 after.
- **Open, non-blocking: `report.py`'s atomic write loses to a concurrent
  reader on Windows.** `os.replace` raises `PermissionError [WinError 32]`
  when another handle has the destination open, so a reader polling
  `<role>-latest.md` while a round writes it can make the write fail. Two
  tests error on Windows for this reason; CI is POSIX and unaffected. The
  canonical self-report path works normally in single-reader use (verified on
  Windows: `write`, `status` fresh/stale/absent all correct). The fix is a
  bounded retry around the replace, not a Windows-specific protocol.

- **A round's completion report reaches Brain by a provider-neutral
  self-report first, transcript recovery only as fallback.** The order is:
  (1) the role writes its own report into the shared `agent-inbox/` under
  the git common dir, using only filesystem, git and a shell — capabilities
  every Worker contract already requires, so it works on any tool including
  ones with no adapter and no readable transcript store; (2) provider
  transcript recovery, only when that artifact is missing or stale;
  (3) manual owner relay, only when both fail. A tool-specific hook fixes
  one member of the problem class, not the class. The canonical mechanism
  is designed in the sibling `agentic-project-framework` repository and is
  adopted here rather than reimplemented — including its rule that a role's
  tag is derived from which checkout it is in, never asserted.
  Two conclusions worth not relearning: transcript recovery being
  unavailable for a provider does NOT mean that provider needs manual
  relay, since its Worker can still write the canonical report; and a
  session that merely ran `git log` mentions every earlier round's SHA, so
  recovery must reconcile a session to the round it *produced*, not the
  most recent conversation that mentions it. Absence stays UNKNOWN, and a
  report — recovered or self-written — stays evidence of what the agent
  said, never a substitute for reviewing the diff.

- **The transcript-recovery fallback over-rejects real producing sessions;
  fold the fix into the next framework touch rather than a round of its
  own.** Its primary-checkout exclusion requires that *no* recorded working
  directory in a candidate session is the primary checkout. Sessions
  routinely start there and move into the worktree, and one provider
  records only a start-of-session working directory — the exact field the
  design says identity must not rest on — so a genuine producing session is
  rejected. Verified by probe: the round-12 round's own session is local,
  in-window and correct, and recovery returns UNKNOWN for it. It fails
  closed, so it yields no answer rather than a wrong one, and the canonical
  self-report is unaffected — which is why this is a follow-up, not a
  blocker. The fix is to exclude *the reading session itself* rather than
  any session that ever touched the primary checkout. Its tests pass
  because their fixtures never touch the primary checkout, so they encode
  the intended shape rather than the observed one.

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
