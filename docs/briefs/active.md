# Active brief

Status: **queued, not started**.

Identifier: **`025-2026-09-22-checklist-banner`** — use exactly this string
as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (024 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — invariants and the evidence table's
   "Format status, README banner" row.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. `scripts/generate_format_atlas.py`, `tests/test_format_atlas.py`, and the
   top of `README.md` where the banner is embedded.
5. `docs/state.md` § Owner preferences, the README banner entry.

---

## MODE: IMPLEMENTATION

## Goal

The README banner reads at a glance: a short, clean checklist of the formats
this project has started, showing for each one how far along its banlist, card
pool, rules and card text are. It stays generated from the project's data, as
it is today.

## Why this is next

The owner reviewed the current banner and rejected it: at README width its
per-area bars are unlabelled, the letter legend doesn't read, and eight era
tiles plus a 128-format count make it too dense for a banner. This is the
third rejection of a data-dense design, so the problem is the design language,
not its tuning.

## The design the owner approved in direction

A checklist table. Rows are the formats that have started (today: Goat, Edison,
Tengu, and Tokyo Dome as research), each with its short name and date. Four
columns with written headers: **Banlist, Card pool, Rules, Card text**. Each
cell is one symbol, and a small legend explains them:

| Area status | Symbol |
|---|---|
| verified | filled check (e.g. check inside a filled circle) |
| complete | plain check |
| partial | half-filled circle |
| research | magnifier or dot, visually distinct from partial |
| missing / stub | empty circle |

One short summary line at most (e.g. "3 shipped · 1 in research"). No era
tiles, no catalogue-wide count in the banner; the full atlas keeps that detail
and the README's link to it stays.

These are the owner's explicit constraints; treat them as requirements:

- **Readable as a banner.** Text large enough to read comfortably at the
  README's display width; nothing that needs zooming. Prefer fewer elements.
- **Symbols carry meaning without colour alone**, and colour is consistent:
  one colour family for done, one for partial, one for research, grey for not
  started.
- **Complete and verified must stay visibly different.** Showing complete as
  verified would claim more than the data says.

Beyond these, the visual details are yours. Aim for clean and slick, not
decorated.

## Required investigation

1. How GitHub renders an SVG embedded as `<img>`: no scripts, no external fonts,
   and whatever text or symbol technique you use must render in that context.
   State what you relied on and how you checked it.
2. How the banner looks on GitHub's light and dark README themes. It needs to
   read well on both, whether by carrying its own background or otherwise.

## Scope

- `scripts/generate_format_atlas.py` — the banner renderer only. The full atlas
  (`format-atlas.svg`) is out of scope and must not change.
- `docs/assets/format-banner.svg`, regenerated, never hand-edited.
- `tests/test_format_atlas.py` — the banner's tests. Tests that pin the old
  layout (era tiles, tile markup) are replaced because this brief's purpose is
  the redesign. Every guarantee they encoded that still applies must survive,
  in particular: only started formats appear, and the banner agrees with the
  canonical data.
- The README's banner `alt` text, so it describes the new banner accurately.

## Non-goals

- No change to canonical data, `dist/`, the full atlas, the progress badge, or
  any format's status.
- No new dependency; the generator stays standard-library only.
- No change to what CI runs.

## Acceptance criteria

- The regenerated banner is the checklist described above, and
  `python scripts/generate_format_atlas.py --check` is clean.
- A test fails if a cell's symbol disagrees with that area's status in the
  data. Show it: change one area's status in a scratch copy, the test goes red,
  restore it, green.
- A test fails if complete and verified would render the same.
- The full atlas SVG is byte-identical to the base.
- A rendered image of the new banner at README width (a PNG or a screenshot)
  is included with the report, in both light and dark README themes if you can
  produce them. Say how you produced it.

## Required evidence

`python scripts/generate_format_atlas.py --check`; the full suite
`python -m unittest discover -t . -s tests -v`; `python -m retroformats
validate` and `python -m retroformats build --check` unchanged at
0 errors / 569 warnings; the red/green demonstration; the rendered images;
and the URL of `docs/assets/format-banner.svg` on your pushed branch, so a
reviewer can view it as GitHub renders it.

## When to stop

If GitHub's rendering cannot show the symbols or text reliably in an `<img>`
SVG, stop and report what you found rather than falling back to a dense or
text-only design.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/checklist-banner` from `origin/main`. Focused
commits; push the branch; never push `main`; never merge; never bypass a local
check. After your final commit and push, write your report from inside
`.worktrees/builder/` with
`python3 tools/report.py write --task 025-2026-09-22-checklist-banner`
(`python` where `python3` does not resolve), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus: how the banner was checked in GitHub's
`<img>` context; the rendered images and how they were made; which old tests
were replaced and which guarantee each replacement keeps; the red/green
demonstration; and the pushed SVG's URL.
