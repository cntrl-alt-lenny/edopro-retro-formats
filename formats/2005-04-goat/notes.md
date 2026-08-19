# Goat Format (2005-04-goat)

The community-defined retrospective format played under the April 2005 TCG
Forbidden/Limited list — the canonical first target for this project because Project
Ignis already ships a battle-tested implementation, giving us a reference to
regression-test against.

## How this format's data was built

Everything was imported from the Project Ignis reference by
`retroformats/importers/ignis_goat.py` (revisions pinned in `data/sources.json`):

- `GOAT.lflist.conf` (1704 whitelist codes) was decomposed into:
  - **pool** `pool-goat-2005-ignis`: 1700 canonical cards (modern passcodes; 3 alt-art
    codes recorded as `variant_passcodes`, 1 as a historical-implementation variant);
  - **banlist** `tcg-2005-04`: 73 canonical entries derived from the whitelist's
    0/1/2 counts (19 forbidden / 43 limited / 15 semi-limited at the code level);
  - **211 errata records** — one per card the whitelist represents by a historical
    implementation: 191 "(GOAT)" cards from `goat-entries.cdb` (codes
    504700000–504700190) + 20 "(Pre-Errata)" cards from `cards-unofficial.cdb`
    (511-range / modern+10 codes; pre-errata Ring of Destruction has two artwork
    codes folded into one record). All are `strategy: reuse-upstream` — the cdb rows
    and `script/goat/` / `script/pre-errata/` Lua scripts ship with EDOPro already.

The build then regenerates the whitelist from those canonical records, and
`tests/test_repo_data.py::test_goat_matches_ignis_reference` asserts the result stays
**entry-for-entry identical** to the vendored upstream reference, including the EDOPro
content hash `0x28e9fc02`.

## Known caveats / TODO

- The banlist is *derived* from the Ignis whitelist, not yet cross-checked against the
  published April 2005 TCG list — hence `completeness: partial` (roadmap item 2).
- The 211 errata records have no `date_effective` yet, so this format pins them via
  `errata_overrides.include` (mirroring `data/imported/ignis-goat-report.json`). As
  dates are researched the include list should shrink to nothing.
- `period.end` is null pending a sourced answer to when the goat era is considered to
  end (list change vs Cybernetic Revolution release); `snapshot` = the list's
  effective date as a documented modeling choice.
- Upstream quirk: Ignis's file duplicates line `511000868 1` (Twin-Headed Behemoth),
  which cancels out of EDOPro's line-folded runtime hash — their file hashes as
  `0x6d9ed1c5` in-client while the entry set hashes `0x28e9fc02`. Our generated file
  has no duplicate, so it hashes canonically.

## Playing it

Host with the generated list (`dist/lflists/2005-04-goat.lflist.conf`), Duel Rule
preset **GOAT** (sets `DUEL_MODE_GOAT` + MR1 forbidden types + 40–60/0–999/0–15
decks), and allowed cards **"Anything goes"** (the historical card versions carry
`ot=8` and would otherwise be rejected as unofficial; the whitelist enforces the real
pool). This matches how the format is played on Project Ignis's own list.
