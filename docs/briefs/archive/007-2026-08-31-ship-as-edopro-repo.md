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

## MODE: IMPLEMENTATION

Part A additionally runs under **DATA/SCHEMA** discipline — it edits
canonical data (`data/sources.json`) and touches an evidence claim.

## Goal

Roadmap item 8 — **ship as an EDOPro repo**. Three canonical formats now
build clean, pool-enforcing whitelists and all three carry `verified`
banlists and pools. Nobody can actually use any of it.

Every check this project runs on itself is internal: the validator, the
suite, the reference-parity hash. Shipping is the first genuinely
external check, and this round is about making the packaging honest and
provable — starting with a dependency the repo has never stated.

Part A is a small correction carried over from round 6, bundled here
rather than given its own round.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Part A — an unsourced universal negative in `data/sources.json`

Round 6 (which was otherwise excellent, and whose conclusion is correct)
wrote this into `konami-september-2011-list`'s `reliability_notes`:

> one of its 52 forbidden entries, Sixth Sense (第六感), has **no TCG
> printing at all** and is left blank in the TCG column, proving the
> underlying list is the OCG's.

"No TCG printing at all" is a universal negative, and nothing cited
establishes it. The archived page shows the card's TCG-name cell blank
**in September 2011**; this repository's TCG release coverage
(`data/releases/coverage.json`) runs only to 2011-09-17, so the data here
cannot speak to any later date either. That is `AGENTS.md`'s "absence of
evidence → proof of absence" — now sitting in canonical data.

The **argument is sound on the weaker claim** and does not need
rescuing: a card with no TCG printing *in the period* and a blank
TCG-name cell is already enough to show the underlying list is the OCG's.

Fix the sentence so it claims only what is established. Either weaken it
to the period-scoped version, or — if you can find and cite genuine
evidence for the stronger claim — source it properly. **Do not simply
delete the Sixth Sense example**; it is the load-bearing illustration.

Then check whether the same overreach appears anywhere else this round's
predecessors wrote: grep `data/sources.json` and
`data/banlists/tcg/2011-09.json` for other absolute negatives ("no ...
at all", "never", "does not exist") added recently, and report what you
find, including "nothing else."

---

## Part B — the shipping dependency nobody has written down

**This is the substantive part.** Brain established the following
statically; **re-derive it yourself rather than trusting it.**

Every generated whitelist references passcodes that **do not exist in
this repository**:

| list | codes ≥ `504700000` |
|---|---|
| `2005-04-goat` | 209 |
| `2010-03-edison` | 67 |
| `2011-09-tengu` | 46 |

Those are Project Ignis's `goat-entries.cdb` / pre-errata rows, which
ship in **upstream** repositories (BabelCDB → DeltaBagooska), not here.
`dist/` contains only `lflists/` and a README.

So this repo is **not self-contained**, and nothing in it says so. On a
whitelist an unresolvable code is not a cosmetically missing card — that
card simply cannot be played, silently.

Establish and document, with citations:

1. **Which upstream repository actually supplies those rows** at the
   revision `data/sources.json` pins, and whether every one of the codes
   the three lists emit is present there. Report the count checked and
   any that are missing. If checking exhaustively needs a clone you
   cannot make, say so and state exactly what you did check — a partial
   check honestly labelled beats a confident guess.
2. **What EDOPro does when a whitelist names a code no loaded cdb
   provides.** `docs/research/edopro-data-repos-ui.md` already carries
   file:line citations for the repo/cdb/lflist loading path — use it,
   and cite it. If the source does not settle the behaviour, say the
   behaviour is undetermined rather than predicting it.
3. **Whether the default EDOPro install already satisfies the
   dependency** (i.e. whether DeltaBagooska is a shipped default repo),
   and what a user who has somehow removed it would experience.

Then write it down where a user will actually hit it — `dist/README.md`
— as a plain prerequisite, not a footnote.

### Explicit scope limit: do NOT attempt a live client test

Roadmap item 8 says "test in a real client." **That part is out of scope
for this round and you should not attempt it.** Installing and driving a
GUI game client is not something to fake, and a fabricated or inferred
"tested it, works" is the worst possible outcome here.

Instead: state plainly, in the round report and in `dist/README.md`,
which claims are statically proven and which remain **untested in a real
client**. Leaving that explicitly untested is the honest state and is a
fully acceptable outcome for this round.

---

## Part C — make the packaging match reality

`dist/README.md` already carries a `user_configs.json` snippet. Two
things in it are wrong or unproven; re-derive both before changing them:

1. It sets `"data_path": "dist/databases"` and `"script_path":
   "dist/scripts"`. **Neither directory exists.** The README's own
   parenthetical admits they are empty, which is not the same as absent.
   Determine from the cited EDOPro source research what the client does
   with a configured path that does not exist, and fix the snippet so it
   is correct for what this repo actually ships today — whether that
   means omitting the keys, pointing them elsewhere, or creating the
   directories with a `.gitkeep`. Justify the choice.
2. Confirm the documented list names (`Retro 2005-04-goat` etc.) and the
   per-format host-settings table still match what `build` actually
   emits. Brain checked the list names and they matched at the starting
   SHA; check the table's Duel Rule presets against each format's
   `rule_profile`, which is the part more likely to have drifted.

Then add the **versioned release layout** roadmap item 8 asks for: a
documented, repeatable way to cut a versioned release of `dist/` so a
consumer can pin one. Keep it proportionate — this project is stdlib-only
with no dependency manifest and that must not change. A documented
convention plus, if warranted, a small script is enough; **do not** add
CI publishing, external services, or a release-automation framework. If
you conclude the honest answer is "git tags plus this documented
convention, no tooling needed," that is a legitimate outcome — say why.

## Non-goals

- Do not attempt to run, install, or screenshot EDOPro (see Part B).
- Do not generate `dist/databases/` or `dist/scripts/` **content** —
  that is roadmap item 7 (custom-script/cdb generation) and needs a
  reserved passcode range chosen first. Creating an empty placeholder
  directory is in scope; generating card rows is not.
- Do not change canonical data other than Part A's wording fix.
- Do not touch banlists, pools, errata, or any `implementation_status`.
- Do not add a dependency manifest or any third-party package.
- Do not redesign the atlas or banner.

## Protected invariants

- All three generated lflists **byte-identical** after this round —
  nothing here should change card resolution. Confirm via `build --check`
  and `git status` showing no change under `dist/lflists/`.
- GOAT's EDOPro content hash stays `0x28E9FC02`.
- `python -m retroformats validate` stays at **0 errors**, warnings at
  569 unless you deliberately and reportedly change them.
- Python remains standard-library only.

## Required investigation

1. Re-derive the three per-list counts of codes ≥ `504700000` yourself.
2. Establish where those rows actually live upstream, at the pinned
   revision.
3. Read `docs/research/edopro-data-repos-ui.md` for the loading path
   before asserting any client behaviour, and cite it.
4. Verify the `dist/README.md` snippet's paths and the host-settings
   table against what the repo actually produces.

## Acceptance criteria

- `data/sources.json` no longer asserts an unsourced universal negative,
  and the Sixth Sense argument still stands on what is established.
- `dist/README.md` states the upstream card-data prerequisite plainly,
  with the client behaviour on a missing code either cited or explicitly
  marked undetermined.
- The `user_configs.json` snippet is correct for what this repo ships
  today.
- A documented, proportionate versioned-release convention exists.
- What remains untested in a real client is stated explicitly, in both
  the report and `dist/README.md`.
- `dist/lflists/` byte-identical; full suite, validator, and
  `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

If you add a check worth keeping (e.g. that the README's documented list
names match generated output), add it as a real test.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/ship-as-edopro-repo`). Do not merge to `main` yourself.
Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the corrected wording and why it now matches the evidence;
  what the sweep for other absolute negatives found.
- Part B: the per-list code counts as you re-derived them; where those
  rows live upstream and how much of that you could actually verify;
  what EDOPro does with an unresolvable whitelist code, cited — or
  explicitly marked undetermined; what you wrote into `dist/README.md`.
- Part C: what was wrong in the snippet and what you changed it to; the
  release convention you chose and why it is proportionate.
- Exactly which claims remain untested in a real client.
- Exact output of the three validation commands, plus confirmation
  `dist/lflists/` is unchanged and the warning count.
- Anything left genuinely uncertain, stated as uncertain.
