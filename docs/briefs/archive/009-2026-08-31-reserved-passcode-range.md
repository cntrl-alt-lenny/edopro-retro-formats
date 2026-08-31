# Active brief

Status: **queued, not started**.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number) and replace it with the next one, or leave a
one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — coordination rules and the
   non-negotiable epistemic rules. They outrank convenience.
2. [`docs/agents/role-contracts.md`](../agents/role-contracts.md) — the
   Worker contract: your mode's rules, the ground rules, and the
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: DATA/SCHEMA

## Goal

Choose, prove, and document **this project's own reserved passcode
range** — the prerequisite roadmap item 7 (`custom-script`/cdb
generation) has been blocked on since it was written.

Item 7 is the largest remaining structural piece: it is what lets this
project ship a historical card Project Ignis does not, and it is what
roadmap item 1c's 48 acknowledged implementation gaps feed into. It
cannot start until there is a code range that provably cannot collide
with anything upstream.

**This round picks and proves the range. It does not build generation.**

Part A is a small correction carried over from round 8.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Part A — one over-general sentence in the deck checker

`retroformats/deckcheck.py`'s `FORBIDDEN_TYPE_NOTE` is printed to the
user on every `check-deck` run. It says the check is redundant because:

> its **release-cutoff pool** cannot contain a card of any type it
> forbids, since every such type's real first TCG printing postdates
> this format's own cutoff

That reasoning is correct for Edison and Tengu. **It is not correct for
GOAT**, whose pool is `kind: extensional` (`data/pools/pool-goat-2005-ignis.json`)
— an imported Ignis whitelist, with no `cutoff` at all. The message
attributes to GOAT a pool structure it does not have.

The *conclusion* still holds for GOAT, by a different route: an
extensional pool is a fixed, vetted list, and nothing in it is of a
forbidden type. Round 8's underlying investigation was sound; only this
one sentence over-generalised.

Fix the message so it is true for all three formats — either by stating
both routes, or by a formulation that covers extensional and
release-cutoff pools without asserting a structure a given format lacks.
The same over-generalisation appears in the long `FORBIDDEN_TYPE_NOTE`
comment block directly above it; fix both, and keep the citations.

Verify your wording against all three pools rather than reasoning from
this brief.

---

## Part B — the reserved range (the substantive part)

`docs/roadmap.md` item 7 states the requirement: pick a range that
"cannot collide with 5047xxxxx/511YYYXXX/prerelease ranges and document
it." That instruction names the constraint but has never been discharged.

### What must be established, with evidence

1. **What is actually in use upstream.** Brain surveyed the two cdbs at
   the pinned `ignis-babelcdb` revision as a starting point — **re-derive
   this yourself, do not trust it**:
   - `goat-entries.cdb`: 191 rows, all in `504700000`–`504700190`.
   - `cards-unofficial.cdb`: 5,878 rows spanning a *wide* space —
     minimum `301`, maximum `810000114`, with rows in nearly every
     hundred-million bucket from 0 to 8.

   That second figure is the important one: the unofficial database is
   not confined to a tidy reserved block, so "pick a big round number"
   is not good enough. Establish the real occupied set, and check
   `cards.cdb` too — the official database is the largest constraint of
   all and Brain did not survey it.

2. **The documented upstream conventions**, not just observed data.
   `docs/research/ignis-goat.md` and
   `docs/research/edopro-data-repos-ui.md` already describe the
   `504700000+` and `511YYYXXX` conventions and the `ot`/`alias`
   mechanics. Cite what is *convention* versus what is merely *currently
   observed* — a range that is empty today but conventionally reserved
   upstream is not available to us.

3. **The prerelease range** the roadmap names. Establish what it
   actually is and where that is documented. If you cannot establish it
   from cited evidence, say so explicitly — do not assume a value.

4. **The engine's own limits.** `schemas/common.schema.json`'s
   `passcode` allows up to `4294967295`, and EDOPro codes are `uint32`.
   Confirm the ceiling from the engine research rather than the schema
   alone, and confirm nothing in the client special-cases high codes.

### What to deliver

- A **chosen range**, with a stated size and an argument for why that
  size is right for the plausible number of `custom-script` cards
  (roadmap 1c's 48 gaps is the current known demand — check that figure
  rather than repeating it).
- A **collision proof**: the range is disjoint from every code observed
  in the pinned upstream databases *and* from every convention you
  documented. Show the check, not just the conclusion.
- **Where the reservation is recorded** so it cannot be forgotten or
  quietly violated later. Prefer a mechanism over a note: a validator
  rule, a constant with a test, or a schema constraint. This project's
  own standing instruction is "prefer a mechanism over a list"
  (`AGENTS.md` § Working discipline) — apply it here.
- Documentation of the decision and its reasoning, sited where a future
  reader will look (the roadmap item, and/or `docs/architecture.md`'s
  card-identity section, which already describes the upstream ranges).

### What NOT to do

- **Do not generate any cdb rows, scripts, or `dist/databases/`
  content.** That is item 7's implementation and a separate round.
- Do not assign codes to specific cards.
- Do not change any existing passcode, erratum, pool, or banlist.
- Do not widen `schemas/common.schema.json`'s `passcode` bounds.

If, while proving non-collision, you conclude that **no safe range
exists** under the constraints as stated, that is a legitimate and
valuable finding — report it with the evidence and stop, rather than
picking the least-bad option silently.

## Non-goals

- Do not attempt to run, install, or screenshot EDOPro (standing
  boundary since round 7).
- Do not change canonical data other than what a reservation mechanism
  strictly requires.
- Do not add a dependency; standard library only.

## Protected invariants

- All three generated lflists **byte-identical** after this round.
  Confirm via `build --check` and `git status` showing no change under
  `dist/lflists/`.
- GOAT's EDOPro content hash stays `0x28E9FC02`.
- `python -m retroformats validate` stays at **0 errors**, warnings at
  569 unless you deliberately and reportedly change them.
- `python -m retroformats check-deck` keeps working on round 8's
  fixtures — Part A touches its output text, so re-run it.

## Required investigation

1. Re-derive the upstream occupied code set yourself, including
   `cards.cdb`, at the pinned revision.
2. Separate documented convention from merely-observed occupancy.
3. Establish or explicitly fail to establish the prerelease range.
4. Verify Part A's wording against all three pool records.

## Acceptance criteria

- `check-deck`'s disclosure is true for all three formats.
- A reserved range is chosen, sized with a stated rationale, and proven
  disjoint from documented conventions and observed upstream codes —
  or a reasoned finding that none is available.
- The reservation is enforced by a mechanism, not only described in
  prose, with a test that fails without it.
- The decision and its evidence are documented where item 7 will find
  them.
- `dist/lflists/` byte-identical; full suite, validator, and
  `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

Plus `check-deck` output on one round-8 fixture, showing the corrected
disclosure text.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/reserved-passcode-range`). Do not merge to `main`
yourself. Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the corrected wording, and how you verified it against all
  three pools.
- Part B: the occupied-code survey as you re-derived it (including
  `cards.cdb`); documented conventions versus observed occupancy; what
  you established or could not establish about the prerelease range;
  the chosen range with its size rationale; the collision proof; and the
  mechanism that enforces the reservation.
- Exact output of the three validation commands plus `check-deck`, and
  confirmation `dist/lflists/` is unchanged.
- Anything left genuinely uncertain, stated as uncertain.
