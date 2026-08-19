# EDOPro research summary

What we verified about EDOPro, ocgcore, and the Project Ignis data ecosystem before
designing this project. Everything here was confirmed against source code at the
pinned revisions recorded in `data/sources.json` (EDOPro client
`9d6fb3e`, ocgcore `46779fb`, LFLists `98ecbfd`, BabelCDB `da54f28`, CardScripts
`383bfbd`, Distribution `54a6e23`). The full research notes, with file:line citations
for every claim, live in [docs/research/](research/):

- [edopro-lflists.md](research/edopro-lflists.md) — banlist discovery, parsing, hashing, enforcement
- [edopro-data-repos-ui.md](research/edopro-data-repos-ui.md) — cdb/script loading, repo config schema, duel-rule UI
- [ocgcore-flags.md](research/ocgcore-flags.md) — every `DUEL_*` flag, composite modes, behavioural effects
- [ignis-goat.md](research/ignis-goat.md) — the GOAT reference implementation end-to-end

## Banlists (lflists)

- Discovery order: `./expansions/lflist.conf` → `./lflist.conf` → `./lflists/*.conf`
  (case-insensitive alphabetical — hence upstream's `0TCG...` name sorting first as
  the default) → each configured repo (`<data_path>/lflist.conf`, else the repo's
  `lflist_path` folder) → a built-in "N/A" list forced last.
- Format: `#` comments; `!Name` starts a (new) list — several lists per file are
  legal; a `$whitelist` line makes the current list a whitelist; entries are
  `code count` with trailing text ignored (`--Name` comments by convention). Counts:
  0/negative = forbidden, 1, 2, 3; unlisted = 3 on a blacklist, illegal on a whitelist.
- Identity is a 32-bit order-independent XOR hash over `(code, count)` pairs — the
  name and whitelist flag are **not** hashed. Only the hash travels over the network;
  both players need identical entries for the list to resolve remotely.
  - Quirk found: duplicated identical lines cancel out of the client's line-folded
    hash. Ignis's GOAT file duplicates `511000868`, so its runtime hash (`0x6d9ed1c5`)
    differs from its deduplicated entry-set hash (`0x28e9fc02`).
- Enforcement is server-side only (the hosting client's embedded server), in
  `DeckManager::CheckDeckContent`: copies are counted under the **alias root** (so
  alt arts and pre-errata variants share the 3-copy pool); the limit lookup tries the
  card's own code, then its alias — but on a whitelist the alias fallback applies only
  within the ±10 artwork window, so functional variants (pre-errata codes) must be
  listed explicitly.
- Selecting a banlist implies nothing else: no duel flags, no deck sizes, no scopes.

## Card databases, scripts, repositories

- cdb load order is "last wins": `./cards.cdb` → `./expansions/**.cdb` → expansion
  zips → each repo's `data_path/*.cdb` (depth 0) in config order. Same-id rows
  overwrite silently.
- Scripts: ocgcore requests `c<code>.lua`; a card whose alias is within ±10 loads the
  alias's script instead. The client searches repo `script_path`s (latest-configured
  first, subdirs 2 deep), then `./expansions/script`, zips, `./script`. Subdirectories
  (like upstream's `script/goat/`) are organisational only. Each repo's
  `script_path/init.lua` runs at every duel creation — a sanctioned hook for
  era-global ruling patches.
- Repo entries (`config/configs.json` + `config/user_configs.json`, user file parsed
  first, **later entries win** for both cdbs and scripts) support: `url`, `repo_name`,
  `repo_path`, `data_path` (cdbs/strings/mappings/lflist.conf), `lflist_path`,
  `script_path`, `pics_path`, `should_read`, `should_update`, `not_git_repo`,
  `is_language`+`language`, `has_core`+`core_path`. No in-game UI — users edit
  `user_configs.json`.
- What an external repo **cannot** contribute: duel-rule presets, deck-size defaults,
  server lists, UI skins/sounds, field-spell art, `system.conf` defaults.

## Rules engine (ocgcore)

- 37 individual `DUEL_*` flags (64-bit space, bits 0–36) plus composite presets:
  `DUEL_MODE_MR1..MR5`, `SPEED`, `RUSH`, `GOAT`. `OCG_DuelOptions.flags` is `uint64_t`.
- `DUEL_MODE_GOAT = DUEL_MODE_MR1 | 11 TCG-era flags` (fast-effect ignition, TCG SEGOC
  ×2, 6-step battle step, private-knowledge triggers, single chain per damage substep,
  0-ATK mutual destruction, stored attack replays, equip-missing-target, traps-in-new-
  chain, repos-after-control-change). Each flag's mechanical effect is documented with
  engine citations in the research note.
- `DUEL_MODE_MR*_FORB` are client-side deck-type masks (Xyz/Pendulum/Link bans), never
  passed to the core. Starting LP/hand/draw are per-player `OCG_Player` fields, not flags.
- The 8 duel-rule presets and their flag mappings are **compiled into the client**
  (`Game::ReloadCBDuelRule`, `menu_handler.cpp`); the GOAT preset also sets MR1
  forbidden types, 40–60/0–999/0–15 deck sizes, and TCG SEGOC. Every rule flag is
  individually togglable in the Custom Rules dialog, so any historical combination is
  *hostable*, just not shippable as a named preset.
- Gaps (no flag exists): missing-the-timing conventions, spell speed/chain legality
  variations, match/side procedure, first-player determination, deck construction.
  Historical accuracy beyond the flag axes needs card-script-level work or upstream
  engine changes.

## The GOAT reference implementation (Project Ignis)

Three cooperating pieces, all delivered through the standard repo mechanism:

1. `LFLists/GOAT.lflist.conf` — a whitelist of 1704 codes (19×0, 43×1, 15×2, 1627×3).
2. `BabelCDB/goat-entries.cdb` — 191 "(GOAT)" card versions, codes 504700000–190,
   `ot=8` (SCOPE_ILLEGAL), `alias` → modern passcode; plus 21 "(Pre-Errata)" cards
   from `cards-unofficial.cdb` (511-range or modern+10 codes). The whitelist lists
   variant codes and **never** the modern codes of overridden cards.
3. `CardScripts/goat/` — one standalone script per variant, edited copies of the
   modern scripts; `Duel.GoatConfirm` in `utility.lua` encodes the 2005
   failed-search-verification ruling (used by 73 scripts).

Because variant cards carry `ot=8`, GOAT rooms must be hosted with allowed cards
"Any"; the whitelist does the actual pool enforcement. In-duel, `card::get_code()`
returns the alias, so a "(GOAT)" card *is* the modern card for name/code purposes
while using its own text, stats, and script.

## Consequences for this project

1. Ship banlists as generated `*.lflist.conf` (whitelists for closed pools); entry
   parity with a reference list gives hash-level network compatibility.
2. Reference upstream's historical card implementations by code (errata records);
   generate whitelist entries with the historical codes substituted for modern ones.
3. Model rules as flag-set profiles; document per format which preset (or custom flag
   set) the host must select — this cannot be automated from a data repo today.
   (Possible future upstream contribution: let an lflist or repo suggest duel flags.)
4. A single git repo with `lflists/` (and later cdb + `script/`) directories is
   directly consumable by EDOPro via one `user_configs.json` entry.
