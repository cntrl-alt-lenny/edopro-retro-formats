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

Part B additionally runs under **SOURCE VERIFICATION** rules (see
`role-contracts.md`): authenticate or falsify one named evidence chain,
do not broaden into general research, and state exactly what the source
does and does not establish.

## Goal

Tengu is the third canonical format and the only one never held to the
bar the other two have now cleared. This round closes that gap on two
fronts and fixes the validator hole that let one of them hide.

Round 5 fixed *status fields* that understated their own evidence. This
round is the next layer down: **canonical records whose own metadata
understates or under-specifies what is actually established.** Same
defect class, different surface.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Part A — `legality_basis` is missing on a shipped pool, and nothing catches it

`data/pools/tengu-2011.json` has **no `legality_basis` key at all**.
GOAT and Edison both carry `community-retrospective`.

What makes this more than a missing field: the Tengu pool asserts the
basis anyway, **in prose only** — its `notes` string opens with
`LEGALITY BASIS community-retrospective: ...`. So the claim exists, but
in a form nothing can read, query, or enforce.

`docs/state.md` records `legality_basis` as a policy claim that has
already produced one wrong classification when conflated with
availability. A shipped pool that makes this claim only in prose is
exactly the shape of that failure.

**Re-derive all of this yourself before acting** — check the three pool
files directly, don't trust this description.

### A1 — the data

Decide whether `community-retrospective` is the correct structured value
for `pool-tengu-2011`, on the evidence in the pool's own `notes` and
`sources` (it reproduces a modern community-defined format pool as of
YCS Toronto 2011-09-17). If it is, set the field. If the prose claim is
**not** supported at this project's bar, say so and leave the field
absent rather than encoding an unsupported policy claim — an absent
field is honest; a wrong one is not. Do not invent a basis to make the
schema tidier.

If you do set it, consider whether the now-redundant prose preamble in
`notes` should stay, go, or be reworded. Your call; justify it.

### A2 — the defect class

`retroformats/validate.py` (around line 164) reads:

```
basis = pool.raw.get("legality_basis")
if basis is not None and basis not in (...):
    self.error("pool.bad-legality-basis", ...)
```

An *invalid* basis errors. An **absent** one passes silently. That is
why this survived three formats and a `completeness: verified` label.

Close the class, not just the instance: make a pool that states no
`legality_basis` fail (or, if you can defend it, warn) rather than pass
unnoticed. Decide deliberately between validator-level enforcement and
making the field `required` in `schemas/pool.schema.json` — or both —
and say why. Add a test that fails without your change.

Note there is an irony worth reading before you design this:
`tests/test_yugi_kaiba_format_gate.py` already carries an elaborate
guard (`_assert_pool_legality_basis_not_laundered_from_absence_of_evidence`)
protecting the *Tokyo Dome research packet's* legality-basis
recommendation — built for a hypothetical future pool, while a real
shipped pool had no basis field at all. Don't duplicate that machinery;
this is a plain canonical-data invariant.

---

## Part B — is Tengu's banlist `verified`-eligible? (SOURCE VERIFICATION)

`data/banlists/tcg/2011-09.json` is `completeness: complete` — 134
entries (51 forbidden / 65 limited / 18 semi-limited), effective
2011-09-01. Rounds 2 and 3 took the other two banlists to `verified`
against archived primary sources.

**This part asks a question; it does not assume the answer.** Do not
treat "the other two got upgraded" as pressure to upgrade this one.

The named evidence chain to authenticate or falsify is the banlist's
own primary citation, `konami-september-2011-list` in
`data/sources.json`. Two specific things about that entry need
resolving, and both are reasons the answer may legitimately be *no*:

1. **It is a Japanese-domain Konami page.** The URL is
   `yugioh-card.com/japan/event/limitregulation/?list=201109`, and the
   entry's own `reliability_notes` say it "displays OCG and TCG columns;
   the packet uses the TCG column only." Establish whether that page's
   TCG column is genuinely a primary record of the **TCG** list, or an
   OCG-side publication's summary of it. These are not the same claim.
2. **It has no archive snapshot and no revision.** It was `retrieved`
   2026-08-27 — a present-day page listing historical regulations.
   Compare Edison's `konami-limited-2010-03`, which is a Wayback
   snapshot *of the period TCG page itself*. Establish whether a
   present-day retrospective listing by the publisher meets this
   project's `verified` bar, which requires corroboration by **strong
   primary/period evidence**, not merely by an official publisher's
   later summary.

Then either (a) find genuinely period/archived TCG-side evidence — an
archived `yugioh-card.com/en/limited/` page for the September 2011 list
is the obvious candidate — and reconcile all 134 entries card-by-card
against it, exactly as rounds 2 and 3 did; or (b) report that the
evidence available does not clear the bar, leave `completeness` at
`complete`, and record precisely what is missing.

**(b) is a fully acceptable outcome.** An honest "not yet" is worth more
than an upgraded label. Whatever you conclude, update the source
registry entry's `reliability_notes` to state what that page actually
establishes.

If and only if you reach (a): update the banlist file's `completeness`
**and** `formats/2011-09-tengu/format.json`'s
`implementation_status.banlist` together — round 5 established that
those two drift apart when only one is touched. That change regenerates
the atlas (see below).

---

## Part C — stale `reliability_notes` in the source registry

`data/sources.json`'s `konami-limited-2010-03` entry still says:

> "Direct entry-by-entry verification against this archive snapshot is
> still TODO (see roadmap)."

Round 2 performed exactly that verification (see
`data/banlists/tcg/2010-03.json`'s own `notes`, and
`docs/briefs/archive/002-*`). The note is stale in the same direction as
everything else this round touches: it understates work that was done.

Fix it, and **sweep the rest of `data/sources.json`** for other
`reliability_notes`/`used_for` values that describe work as pending,
TODO, or research-only when the repository shows it has since been done.
Report what you found — including "nothing else" if that is the answer.

Apply round 5's Part C discipline here: correct a note to match what was
actually done, and never write a note that asserts a verification nobody
performed. If a note is ambiguous rather than clearly stale, leave it
and say so.

---

## Scope consequence: the generated atlas

`implementation_status` feeds `scripts/generate_format_atlas.py`. **If**
Part B reaches (a), regenerate `docs/assets/format-atlas.svg` and
`format-banner.svg` (`python scripts/generate_format_atlas.py`, no
flags — offline and deterministic) and commit the result;
`tests/test_format_atlas.py::test_checked_in_svg_is_fresh` fails
otherwise. Confirm the diff contains *only* the status colour/label for
the field you changed.

If Part B reaches (b), the SVGs must **not** change. Confirm that too.

Do **not** run `--refresh`, which re-pulls the live Format Library
catalog and is out of scope. Do not redesign the atlas or banner.

## Non-goals

- Do not touch banlist `entries`, pool `cards`, or any historical
  adjudication. Part B may only change `completeness` and status/notes
  fields — if reconciliation reveals an actual entry discrepancy, **stop
  and report it** rather than editing the list.
- Do not re-materialise the Tengu pool or change its `cutoff`.
- Do not add a `legality_basis` to anything other than a pool, and do
  not extend the enum.
- Do not revisit GOAT's or Edison's banlists; they are settled.

## Protected invariants

- All three generated lflists **byte-identical** after this round.
  Confirm via `build --check` and `git status` showing no `dist/` change.
- GOAT's EDOPro content hash stays `0x28E9FC02`.
- `python -m retroformats validate` stays at **0 errors** — including
  after your Part A change, which means Tengu's pool must satisfy the
  new rule before you land it.
- The 569 existing warnings should not grow except by your deliberate,
  reported design.

## Required investigation

1. Re-derive the three pools' `legality_basis` state yourself.
2. Confirm the validator's absence hole by observation — construct the
   failing case and watch it pass before you fix it.
3. Establish what `konami-september-2011-list` actually is (region,
   period vs present-day) before judging `verified` eligibility.
4. Sweep `data/sources.json` rather than fixing only the one entry named.

## Acceptance criteria

- `pool-tengu-2011` either carries a defensible structured
  `legality_basis` or a clear argument for leaving it absent.
- A pool with no `legality_basis` can no longer pass validation
  unnoticed, pinned by a test that fails without the change.
- A definite, evidence-stated answer on Tengu banlist `verified`
  eligibility — "not yet, because X" fully acceptable.
- `data/sources.json` contains no note describing already-completed work
  as pending.
- `dist/` byte-identical; atlas fresh (regenerated only if Part B
  changed a status).
- Full suite, validator, and `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/tengu-legality-basis-and-banlist-evidence`). Do not merge
to `main` yourself. Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the three pools' state as you re-derived it; what you set for
  Tengu and why; how you closed the validator hole and why you chose
  that layer; the test you added.
- Part B: what `konami-september-2011-list` actually establishes; which
  outcome you reached, (a) or (b); if (a), the reconciliation result
  entry-by-entry; if (b), precisely what evidence is missing.
- Part C: every note you changed, and what the sweep found.
- Whether the atlas changed, and whether it should have.
- Exact output of the three validation commands, plus confirmation
  `dist/` is unchanged and the warning count.
- Anything left genuinely uncertain, stated as uncertain.
