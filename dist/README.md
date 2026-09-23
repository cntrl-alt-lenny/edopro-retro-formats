# dist/ — generated EDOPro assets

Everything in this directory is **generated** from the canonical data in `data/` and
`formats/` by `python -m retroformats build`. Do not edit by hand; CI rejects drift
(`build --check`).

## Prerequisite: this repo ships only a few cards of its own

**This repository is not self-contained.** All three generated whitelists reference
passcodes that exist only in **upstream** Project Ignis repositories, not in `dist/`
or anywhere else in this repo. The one exception is **three cards in the Edison list**
(`600000001`–`600000003`, below), which this repository itself generates into
`dist/databases/` and `dist/scripts/`. The counts here are upstream identities only
(codes ≥ `504700000` and < `600000000`):

| list | upstream codes ≥ `504700000` (pre-errata / GOAT-variant identities) |
|---|---|
| `2005-04-goat` | 209 |
| `2010-03-edison` | 67 |
| `2011-09-tengu` | 46 |
| **union across all three** | **226** |

These are historical-card identities from Project Ignis's `BabelCDB` repository —
191 from `goat-entries.cdb` and 35 from `cards-unofficial.cdb` (the "(Pre-Errata)"
rows) — at the revision pinned in `data/sources.json`'s `ignis-babelcdb` entry.
**Verified 2026-08-31:** all 226 codes were checked directly against the real
`goat-entries.cdb`/`cards-unofficial.cdb` SQLite files downloaded from that exact
pinned revision — every one resolves, with `ot=8` (`SCOPE_ILLEGAL`) as expected,
zero missing. This was an exhaustive check of every code these lists actually emit,
not a sample.

**What happens if a player's EDOPro doesn't have this data:** per
`docs/research/edopro-lflists.md` §6.1 (citing `generic_duel.cpp:375-377,423`), a
deck referencing a card code with no matching entry in any loaded `.cdb` is flagged
`DeckError::UNKNOWNCARD` **at deck-load time**, before the banlist/whitelist check
ever runs — the whole deck submission is rejected with a typed, visible error naming
the offending code, forcing the player not-ready (`docs/research/edopro-lflists.md`
§6.1, citing `generic_duel.cpp:384-390`). This is not a silent per-card drop; it is a
hard, explicit failure. (Separately, and not directly evidenced here: a player whose
own client never loaded the card at all could not have added it to a deck through
the normal deck editor in the first place, since the editor only lists cards the
client already knows about.)

**Does a default EDOPro install already have this data?** Partially, and this is
genuinely mixed evidence, not a clean yes:

- The stock `configs.json` always includes `ProjectIgnis/DeltaBagooska` as a shipped
  repo (`has_core: true`, cdbs at repo root — `docs/research/edopro-data-repos-ui.md`
  §2c), so a default install does fetch a card-data repo automatically.
- But DeltaBagooska's own git-hosted `goat-entries.delta.cdb` and
  `cards-unofficial.delta.cdb` are **incremental deltas**, not full copies. Checked
  live 2026-08-31 (DeltaBagooska `master` @ `bdb780815e9474ad63add0d49e0f9bd5480c9e93`,
  not a revision this project pins): `goat-entries.delta.cdb` currently carries only
  **5** of the 226 codes these whitelists need; `cards-unofficial.delta.cdb`
  contributes **0** of the remaining 221. The other 221 codes must already be baked
  into the base EDOPro client installer itself.
- Whether the base installer actually bundles the full 191/35-row set is an
  **unverified assumption** carried over from `docs/research/ignis-goat.md` §5
  ("could not verify installer contents offline") — this round did not attempt to
  download or inspect the EDOPro installer (out of scope; see below).

**Bottom line:** a normal, up-to-date EDOPro install is *likely* to already have
everything these lists need, because DeltaBagooska is a default repo and Project
Ignis builds it from the same BabelCDB source this project pins. But nothing here
independently confirms the base installer's bundled snapshot, and a user who has
removed DeltaBagooska (or whose client predates these cards being added upstream)
will hit a hard, visible `UNKNOWNCARD` failure the moment anyone tries to actually
play one of the 226 affected cards — not a warning, not a cosmetic gap.

## Cards this repository generates itself (Edison)

Project Ignis ships no historical version of some cards whose 2010 behaviour differs
from the modern card, so this repository writes them. `python -m retroformats build`
generates, from `data/custom-cards/` and the erratum records that claim them:

| file | contents |
|---|---|
| `dist/databases/retro-formats.cdb` | one `datas` + `texts` row per card, in the BabelCDB layout |
| `dist/scripts/c<passcode>.lua` | that card's script (found by filename, as EDOPro finds any script) |

Each row uses a passcode in this project's reserved range (`600000000`–`699999999`),
`alias` = the modern card and `ot = 8` (`SCOPE_ILLEGAL`, so it is legal only through a
whitelist). Generated so far, all used by `Retro 2010-03-edison` in place of the modern card:

| passcode | modern card (alias) | what differs from the modern card |
|---|---|---|
| `600000001` | Metalzoa (`50705071`) | can be Special Summoned only by its own procedure, so it can never be revived |
| `600000002` | Super Vehicroid - Stealth Union (`3897065`) | its equip effect selects only a monster you control |
| `600000003` | Night Assailant (`16226786`) | when discarded, the Night Assailant just discarded is itself a legal choice to return |

**In a duel** a generated card *is* its modern card for every name and code check (the
`alias`), while stats, text and script come from its own row. **In deck building**
copies are counted under the alias root, and a whitelist follows an alias only within
+/-10, so the lflist names each generated code itself, with the count the banlist
gives the modern card.

**These are original scripts, written from the erratum records' period text and the
engine's Lua API, not copies or adaptations of Project Ignis's CardScripts** (AGPL-3.0-or-later;
this repository is MIT). Every one is an *approximation*: each record in
`data/custom-cards/` lists, in `not_reproduced`, what its script does not establish.
Their engine tests are in `tests/engine/test_edison_historical_scripts.py`. Not
tested in a real client (see the last section).

## Using the lflists in EDOPro

Quick way: copy `dist/lflists/*.lflist.conf` into your EDOPro `lflists/` folder and
restart. The lists appear in the deck-builder and host banlist dropdowns as
`Retro <format id>`.

Repo way (auto-updating): add this repository to `config/user_configs.json` in your
EDOPro install:

```json
{
  "repos": [
    {
      "url": "<this repository's git URL>",
      "repo_name": "Retro Formats",
      "repo_path": "./repositories/retro-formats",
      "lflist_path": "dist/lflists",
      "data_path": "dist/databases",
      "script_path": "dist/scripts",
      "should_update": true
    }
  ],
  "urls": [],
  "servers": []
}
```

`data_path` and `script_path` point at the generated card database and scripts above,
so the three Edison cards resolve without any manual copying. EDOPro loads every
`*.cdb` directly in `data_path` and adds `script_path` and its subfolders to the script
search path (`docs/research/edopro-data-repos-ui.md` section 2a). The upstream card data
this repository does not ship (previous section) still has to come from Project Ignis.
Without these two keys a client falls back to its own defaults and the three Edison
cards are unknown to it (`UNKNOWNCARD` at deck-load time), exactly like a missing upstream
row.

## Host settings are NOT in the lflist

EDOPro cannot read duel rules from a banlist file, so the host must select them (see
each format's `formats/<id>/notes.md`). The Duel Rule dropdown alone is not always
enough — two of the three formats need one additional Custom Rule checkbox beyond
the closest compiled preset, because their rule profile's exact flag set isn't
identical to any single compiled preset:

| format | banlist | Duel Rule preset | additional Custom Rule | allowed cards |
|---|---|---|---|---|
| `Retro 2005-04-goat` | whitelist (pool-enforcing) | `GOAT` | none — GOAT is an exact compiled preset | Anything goes (pre-errata cards are `ot=8`) |
| `Retro 2010-03-edison` | whitelist (pool-enforcing) | `Master Rule 1` | enable the 0‑ATK‑vs‑0‑ATK destruction rule (`DUEL_0_ATK_DESTROYED`, not part of the MR1 preset — see `formats/2010-03-edison/notes.md`) | Anything goes (historical cards are `ot=8`) |
| `Retro 2011-09-tengu` | whitelist (pool-enforcing) | `Master Rule 2` | enable **"OCG Ignition Priority"** (`DUEL_OCG_OBSOLETE_IGNITION`, added on top of the MR2 baseline as a documented 2011-TCG approximation — see `formats/2011-09-tengu/notes.md`) | Anything goes (historical cards are `ot=8`) |

Preset/flag composition confirmed 2026-08-31 against `docs/research/ocgcore-flags.md`
(exact per-flag bit values) and each format's `data/rule-profiles/*.json`: Edison's
and Tengu's `engine.flags` are each the named preset's compiled flag set plus exactly
one extra bit, matching the field-by-field description above. The "OCG Ignition
Priority" checkbox label and its mapping to `DUEL_OCG_OBSOLETE_IGNITION` (the first
Custom Rule checkbox, `0x100`) is cited from
`docs/research/edopro-data-repos-ui.md` §4c.

## Versioned releases

`dist/` is fully reproducible: `python -m retroformats build` regenerates it
byte-for-byte from `data/`/`formats/` at any given commit, and every generated
lflist stamps its own generator version in a header comment
(`GENERATED by edopro-retro-formats/<version>`, from `retroformats.__version__`).
A consumer who wants to pin a specific `dist/` snapshot should:

1. Confirm `retroformats/__init__.py`'s `__version__` reflects the intended release
   (bump it if this is a new release point).
2. Run `python -m retroformats build --check` to confirm `dist/` matches canonical
   data exactly.
3. Commit, then tag that commit `vX.Y.Z` matching `__version__`
   (`git tag v0.1.0 && git push --tags`).
4. A consumer pins a release by checking out that tag (`git checkout v0.1.0`) or
   cloning at it — `dist/lflists/*.lflist.conf` at that tag is exactly what that
   version number identifies, and the version stamped in each file's own header
   comment cross-checks the tag.

No release-automation script is added: cutting a release is the three commands
above, and a wrapper would only add a second thing to keep in sync with what
`build` actually does, for a project that isn't otherwise dependency-managed or
published anywhere. Git tags plus this documented convention are proportionate; CI
publishing or an external release service are not warranted at this project's
current size and are explicitly out of scope.

## What's proven vs. untested in a real client

Statically proven this round (see the round's commit and `docs/briefs/archive/`):
the exact per-list and union counts of upstream-dependent codes; that every one of
those 226 codes resolves in the real, pinned-revision upstream `.cdb` files; the
cited client-side loading, deck-validation, and `UNKNOWNCARD` mechanisms (file:line
citations in `docs/research/edopro-data-repos-ui.md` and
`docs/research/edopro-lflists.md`); the exact bitwise composition of each format's
Duel Rule flags against the compiled presets; that `dist/`'s generated list names
match this document's table.

**Explicitly untested: nobody has installed EDOPro, loaded these lists, hosted a
room, or played a single card from any of the three formats in a real client.**
Every claim above is a static analysis of source code, generated output, and
upstream data — not an observation of the running game. In particular, unverified:
whether a stock EDOPro install's base installer actually bundles the full upstream
card set (see above); whether the described Custom Rule checkboxes produce the
intended in-duel behaviour end-to-end; whether the repo-way `user_configs.json`
snippet above actually registers and loads correctly in a real client session, including
whether a real client loads `dist/databases/retro-formats.cdb` and `dist/scripts/` through
its `data_path`/`script_path` (the generated cards are exercised only in the headless
engine harness, `docs/engine-testing.md`). This
is deliberate — a live client test is out of scope for this round (roadmap item 8's
"test in a real client" is not yet done) and remains open work.
