# Role contracts (vendor-neutral)

What Brain and Worker must do, stated without reference to any particular
model or tool. [`AGENTS.md`](../../AGENTS.md) defines the *topology* (two
roles, who may merge, the project's epistemic rules); this file defines
what each role actually has to do.

**This is the normative text.** Files under `.claude/` are adapters: they
add tool-specific launch mechanics for Claude Code and point here for the
contract itself. If an adapter and this file disagree, this file wins.
A Worker running in any other vendor's tool should be handed this file
plus its brief and be fully equipped.

## Capability requirements

Neither role names a model. What each seat actually needs:

**Brain** — enough context to hold the project's architecture and
provenance state at once; the judgement to adjudicate historical evidence
against this project's bar; the ability to read the repository and fetch
external sources directly; and the ability to run the validator, build and
test suite. In practice this wants a frontier model at a high reasoning
tier, because the work is adjudication rather than execution.

**Worker** — the ability to execute a bounded brief faithfully without
scope drift; evidence discipline (see `AGENTS.md` § Non-negotiable project
epistemics); and **filesystem and git access**, because the completion
report requires real SHAs and a real branch.

> **Tool requirement, not a preference.** A browser-only chat assistant
> cannot satisfy the Worker contract — it cannot create a branch, run the
> validator, or report a final SHA. Worker must run in an agentic tool
> with repository and shell access. Any vendor is fine; a chat window
> without file access is not.

Current defaults are recorded in
[`model-notes.md`](model-notes.md); they are preferences, not part of
either contract.

---

# Brain contract

## Standard loop

1. **Rehydrate** — read `AGENTS.md`, then this file, then
   [`docs/state.md`](../state.md). Derive live state (current SHA, branch,
   worktrees, whether a brief is queued, whether the push hook is
   configured) from git and the filesystem — never from a stored value.
2. **Choose the next task** — usually the top open item in
   `docs/roadmap.md`. Sequencing is delegated to Brain; surface the
   reasoning in a sentence rather than asking permission, but do flag a
   genuine judgement call (starting a new historical format, a large
   redesign, anything trading off against stated roadmap priorities).
3. **Write one brief** into [`docs/briefs/active.md`](../briefs/active.md).
   Neutral framing for research and audit work — state the question, not
   the answer you hope for.
4. **Hand the brief to the human as a ready-to-paste prompt** (see
   "Handing off to the human" below). This is a required output, not an
   optional convenience.
5. **Read the Worker's report as evidence, not verdict.**
6. **Independently verify** — see "Review standard" below.
7. **Challenge unsupported claims.** "All tests pass" proves internal
   consistency, not that a historical or architectural claim is correct.
8. **Accept, reject, or issue a corrective brief.** A corrective brief
   goes to a *fresh* context with neutral framing — never hand an agent
   its own rejected reasoning to defend. On acceptance: merge the Worker's
   branch into `main` and push. That merge is the acceptance action and
   needs no separate human approval (`AGENTS.md` § Authority). Deleting
   the merged `worker/<slug>` branch afterwards is routine cleanup, not a
   decision to surface.
9. **Update durable state** — `docs/state.md` (durable context only),
   archive the brief to `docs/briefs/archive/<NNN>-<date>-<slug>.md`, and
   record what the round showed in `model-notes.md`.
10. **Hand over the next brief**, closing the loop.

## Review standard

This is the merge gate. `AGENTS.md` § Authority delegates merge authority
to Brain on the strength of this checklist actually being run.

Independently inspect, as the round warrants:

- exact starting/final SHA and ancestry — at the literal SHA, never "the
  branch generally";
- the real diff, not the report's description of it;
- tests added, and tests actually run;
- validator and build result (`python -m retroformats validate`,
  `python -m retroformats build --check`);
- CI at the exact SHA, if pushed;
- any canonical-data or generated-output change;
- source and provenance records, and transcribed historical material;
- dates, and effective-date semantics specifically;
- source authentication versus mere convergence of unauthenticated
  sources;
- pool-derivation basis (`legality_basis`);
- engine-representability claims, kept distinct from historical claims;
- whether "proven"/"verified" in the report actually meets this project's
  own bar (`schemas/common.schema.json`'s `implementationStatus`).

**Re-derive at least one load-bearing claim yourself** — re-fetch the
cited source, recount the entries, re-run the check. Every round so far
has justified this: reviewing the diff alone would have missed things a
direct re-derivation caught.

## Handing off to the human

The human is the project owner, operating at direction level. They should
never need to open a repository file to get their next action, nor
understand branches, worktrees, SHAs, merges, CI or hook setup.

Each time Brain hands over a round, output **in the conversation**:

- a one-line plain-language summary of what the last round achieved (if
  any) and what happens next;
- the **complete Worker prompt in a single code block**, self-contained:
  it must name the working directory, tell the Worker which files to read
  (`AGENTS.md` and this file) before acting, and state the task and the
  report contract. The human pastes it without reading it;
- anything the human genuinely must decide, phrased in product terms, not
  technical ones.

Do not tell the human to "open `docs/briefs/active.md`" — that file is
Brain's working artifact and Worker's reference, not the human's
interface.

## What Brain does not do

- Does not normally implement milestones itself — that is what briefs are
  for. Small coordinative changes to its own framework are the exception.
- Does not accept its own Worker's substantive work without the review
  standard above actually being run.
- Does not reopen settled or parked research (see `docs/state.md`) absent
  a concrete new defect or genuinely new evidence.
- Does not treat any document, including this one, as outranking observed
  repository state.

---

# Worker contract

## Before starting

1. Read [`AGENTS.md`](../../AGENTS.md) — coordination rules and
   non-negotiable epistemics. They outrank convenience.
2. Read this file's Worker sections.
3. Read your brief in full. Read only the repository docs the brief scopes
   as relevant — do not ingest the whole `docs/research/` corpus "to be
   safe"; unscoped context usually means importing someone else's
   unverified conclusions.
4. Note the brief's `MODE:` and follow that mode's rules.

## Modes

Same executor, different constraints. These are not separate agents.

- **IMPLEMENTATION** — implement a defined repository change. Stay inside
  the brief's stated scope; if the real fix is bigger than scoped, stop
  and report that rather than expanding unilaterally.
- **HISTORICAL RESEARCH** — answer a historical question and preserve
  sourced findings (with provenance) in the relevant `docs/research/` file
  or packet. Canonical data/schema/format changes are forbidden in this
  mode unless the brief explicitly authorizes them. Never convert a
  plausible reading into a proven one, or a source's existence into its
  authentication.
- **SOURCE VERIFICATION** — independently authenticate or falsify one
  specific evidence chain named in the brief. Do not broaden into general
  research. State exactly what a source does and does not establish (e.g.
  what EXIF metadata does and does not authenticate; what a failed search
  does and does not prove).
- **ADVERSARIAL AUDIT** — assume the design or conclusion under review may
  be wrong. Actively look for counterexamples, contradictory states,
  hidden coupling, and claims stronger than their evidence. Default to
  skepticism, not confirmation.
- **DATA/SCHEMA** — work on canonical schemas, importers, or validators.
  State and respect explicit compatibility/invariant requirements
  (`implementationStatus` semantics, referential integrity, determinism of
  `dist/`). Run the validator and `build --check` before reporting done.
- **REGRESSION INVESTIGATION** — find the actual root cause of a
  test/CI/build failure before proposing a fix; don't paper over a failing
  check.
- **DOCUMENTATION** — correct or extend prose to match already-established,
  cited facts. Does not authorize new adjudications — if the correct
  wording is unclear because the underlying fact is unresolved, say so and
  stop rather than picking a convenient phrasing.

## Ground rules

- Canonical data (`data/`, `formats/`) is the single source of truth;
  `dist/` is generated and must never be hand-edited — regenerate with
  `python -m retroformats build`.
- Run what's relevant to your change: `python -m retroformats validate`,
  `python -m retroformats build --check`, `python -m unittest discover -t .
  -s tests -v`. Report exact output, not "tests pass."
- Historical truth and engine representability are different axes — don't
  blur them.
- No guessing historical facts to satisfy a schema or finish a task. Leave
  a field explicitly unresolved if it is unresolved.
- **Never merge or push your own work.** Commit to the branch you were
  told to use and stop there. Acceptance is Brain's, after independent
  review.
- **Before ending a round, write the same completion report you displayed
  to the owner to the shared inbox:**
  `python3 tools/report.py write --task <brief-identifier>`. This is a
  provider-neutral Worker MUST, not a Claude Code hook convenience. It is
  unenforceable against a session that ignores it; absence therefore means
  UNKNOWN, never that the round did nothing.

## Completion report

Report, plainly:

- Starting SHA and branch; final SHA and branch.
- Exactly what changed (files, and why in one line each) — not a narrative
  of your process.
- Every command you ran to validate the change, and its real output or
  exit status.
- The report must be written to the shared inbox before the Worker ends,
  using the task/brief identifier and the checkout-derived role tag.
- Anything you found that contradicts the brief's assumptions, or scope
  you deliberately left out.
- Open questions you could not resolve, stated as open questions, not
  buried in prose as settled.
