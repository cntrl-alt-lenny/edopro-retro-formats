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

## Goal

Roadmap item 6 — **a deck-level validation tool**. Check a `.ydk` deck
file against a format and report what is and isn't legal, as a CLI
subcommand.

Round 7 made the shipped lists honest about what they need. This makes
them *checkable* without a game client: a player or tournament organiser
can verify a decklist, and this project gets what the roadmap calls "a
realistic fixture surface" for tests.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

## The single most important design constraint

**Do not reimplement legality logic.** `retroformats/lflist.py` already
resolves, for each format, exactly which passcodes are legal and at what
count — that is what `build` emits and what the shipped lists contain.

If this checker computes legality independently, it will eventually
disagree with the list this project actually ships, and a checker that
contradicts the artifact is worse than no checker. Derive the answer from
the same code path that produces `dist/lflists/`, and make that reuse
structural rather than a copied constant.

If reusing it cleanly needs a small refactor of `lflist.py`, that is in
scope — but keep the generated output **byte-identical** (see Protected
invariants) and say what you changed and why.

---

## Part A — the checker

Add a CLI subcommand alongside the existing `validate` / `build` /
`report` / `materialize` in `retroformats/cli.py`. Name it as you judge
best and say why; `check-deck` is the obvious candidate.

It takes a `.ydk` path and a format id, and reports legality.

### `.ydk` format

The EDOPro/YGOPro deck format is a plain text file with `#main`,
`#extra`, and `!side` section markers and one passcode per line;
`#created by ...` and similar comment lines appear in real files. Confirm
the exact shape against something authoritative rather than assuming —
`docs/research/edopro-data-repos-ui.md` and `edopro-lflists.md` are the
in-repo research corpus, and `deck_manager.cpp` behaviour is already
cited there for deck loading. Be tolerant of real-world files (blank
lines, CRLF, stray whitespace) and explicit about what you reject.

### What to check

1. **Pool / whitelist membership** — is each passcode legal in this
   format at all?
2. **Banlist counts** — does any card exceed its allowed count? Note
   that EDOPro counts main + extra + side **combined** for this purpose
   (`docs/research/edopro-lflists.md` documents the client's own rule —
   cite it rather than assuming).
3. **Deck sizes** — `main_deck`, `extra_deck`, `side_deck` ranges live
   in each rule profile's `client` section
   (`data/rule-profiles/*.json`). Use them; do not hard-code 40/60.

### What you probably cannot check, and must not fake

`client.forbidden_card_types` lists `TYPE_XYZ` / `TYPE_PENDULUM` /
`TYPE_LINK` (and Tengu deliberately permits Xyz where the other two
forbid it). **`data/cards/index.json` carries only `passcode`, `name`,
`alias_of` and `ot` — no card type.** So this check has no data behind it
today.

Do not invent a type field, do not read BabelCDB at runtime (the index
exists precisely so validation is self-contained), and do not silently
skip the check as though it passed.

Investigate and report which of these is true:

- the check is **largely redundant** for these three formats, because a
  whitelist already excludes any card not in the pool and none of the
  three pools can contain a forbidden type at their snapshot — in which
  case say so, with evidence, and have the tool state plainly that it
  does not check types and why; or
- it is **not** redundant (you find a real case), in which case report
  that as a finding and **stop** — extending the card index is a
  DATA/SCHEMA change that deserves its own decision, not a silent
  expansion of this round.

Either way the tool's output must be honest about what it did not check.

---

## Part B — the substitution problem

This is the genuinely interesting part, and the reason a naive checker
would mislead people.

For cards with a selected historical implementation, the generated
whitelist emits **only the historical passcode** — the modern one is
deliberately absent (see `docs/architecture.md`, "The whitelist build
algorithm", step 3). Round 7 measured the scale: 209 such codes in GOAT,
67 in Edison, 46 in Tengu, 226 unique.

So a deck containing the **modern** passcode of a substituted card is
genuinely illegal in that format — and a checker that just says
`12345678: not legal in this format` is technically right and completely
unhelpful, because the player has the right *card* and the wrong
*identity*.

Detect this case specifically and explain it: report that the card is
substituted in this format, name the historical passcode that **is**
legal, and say why (the modern implementation would behave incorrectly
for the era). The erratum records are the source for that mapping — use
them; don't build a parallel table.

Consider the reverse direction too, and report what you decide: a deck
containing a historical passcode for a format that does **not**
substitute that card.

---

## Part C — tests

The roadmap's stated reason for this tool is that it gives tests a
realistic fixture surface. Deliver that:

- at least one **legal** deck fixture and several deliberately illegal
  ones (over-count, unlisted card, wrong deck size, modern-code-instead-
  of-substituted), each asserting the specific diagnostic;
- a test that the checker agrees with the shipped list — i.e. a deck
  built from `dist/lflists/<id>.lflist.conf`'s own entries validates
  clean. This is the regression that keeps the checker and the artifact
  from drifting apart, and it is the most valuable test here.

Put fixtures where the suite already keeps them; follow the existing
convention rather than inventing a new one.

## Non-goals

- Do not attempt to run, install, or screenshot EDOPro. Same boundary as
  round 7.
- Do not change canonical data (`data/`, `formats/`) at all this round.
- Do not extend `data/cards/index.json` or its importer (see Part A).
- Do not generate `dist/databases/` or `dist/scripts/` content — that is
  roadmap item 7.
- Do not add a dependency; standard library only.
- Do not build deck *editing*, deck suggestions, or anything beyond
  checking a given file.

## Protected invariants

- All three generated lflists **byte-identical** after this round. If you
  refactor `lflist.py`, this is the check that proves you did it safely.
  Confirm via `build --check` and `git status` showing no change under
  `dist/lflists/`.
- GOAT's EDOPro content hash stays `0x28E9FC02`.
- `python -m retroformats validate` stays at **0 errors**, warnings at
  569 unless you deliberately and reportedly change them.
- Python remains standard-library only.

## Required investigation

1. Establish the real `.ydk` shape from cited evidence, not assumption.
2. Establish EDOPro's own main+extra+side combined counting rule from
   the research corpus, and cite it.
3. Determine whether `forbidden_card_types` is redundant for these three
   formats, with evidence either way.
4. Confirm your checker's verdicts agree with the shipped lflists.

## Acceptance criteria

- A working CLI subcommand that checks a `.ydk` against any of the three
  formats and reports specific, actionable diagnostics.
- Legality derived from the same code path that generates `dist/`, not
  reimplemented.
- Substituted-card decks get an explanation, not just a rejection.
- A definite, evidenced answer on `forbidden_card_types`, and honest
  output about what is not checked.
- Deck fixtures plus the checker-agrees-with-shipped-list regression.
- `dist/lflists/` byte-identical; full suite, validator, and
  `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

Also show the new subcommand's actual output on at least one legal and
one illegal deck — paste it, don't describe it.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/deck-validation-tool`). Do not merge to `main` yourself.
Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the subcommand's interface; how you reused `lflist.py` and any
  refactor you made; the `.ydk` shape you established and from what
  evidence; your evidenced answer on `forbidden_card_types`.
- Part B: how you detect and explain substituted cards, and what you
  decided about the reverse direction.
- Part C: the fixtures and tests added, especially the
  agrees-with-shipped-list regression.
- Real CLI output for a legal and an illegal deck.
- Exact output of the three validation commands, plus confirmation
  `dist/lflists/` is unchanged and the warning count.
- Anything left genuinely uncertain, stated as uncertain.
