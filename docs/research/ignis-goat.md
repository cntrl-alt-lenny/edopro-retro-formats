> Point-in-time research note (2026-08-19), verified against the pinned revisions in data/sources.json.

# Project Ignis GOAT Format Implementation — Reverse-Engineering Notes

Research date: 2026-08-19. All paths are local read-only checkouts:

- `/home/user/edopro` — EDOPro client (edo9300/edopro fork)
- `/workspace/edo9300/ygopro-core` — ocgcore
- `/workspace/projectignis/lflists` — ProjectIgnis/LFLists
- `/workspace/projectignis/babelcdb` — ProjectIgnis/BabelCDB
- `/workspace/projectignis/cardscripts` — ProjectIgnis/CardScripts
- `/workspace/projectignis/distribution` — ProjectIgnis/Distribution
- `/workspace/projectignis/deltabagooska` — ProjectIgnis/DeltaBagooska (shallow-cloned during this session to verify delivery)

Everything below is CONFIRMED against source unless explicitly marked **ASSUMPTION/UNCERTAIN**.

---

## 1. The GOAT lflist (`/workspace/projectignis/lflists/GOAT.lflist.conf`)

### Syntax

```
#[2005.4 GOAT]          <- line 1: comment (ignored by parser; convention: bracketed display hint)
!2005.4 GOAT            <- line 2: '!' starts a new list; the rest of the line is the list name
$whitelist              <- line 3: marks this list as a whitelist
#forbidden Goat         <- section comments, purely cosmetic
511000819 0 --Chaos Emperor Dragon - Envoy of the End
...
```

Entry format: `<passcode> <limit> --<comment>`. The client parser (`/home/user/edopro/gframe/deck_manager.cpp:34-86`, `LoadLFListSingle`):

- skips empty lines and lines starting with `#` (deck_manager.cpp:50-51)
- `!` line: pushes any previous list and starts a new one, name = rest of line, seeds hash `0x7dfcee6a` (deck_manager.cpp:52-61)
- a line beginning with the literal `$whitelist` sets `lflist.whitelist = true` (deck_manager.cpp:36, 62-65)
- data lines: code parsed up to first space, count parsed from chars in `-0123456789`; everything after (the `--Name` comment) is ignored (deck_manager.cpp:67-80)
- multiple lists per file are possible (each `!` starts one); every `.conf` file in `./lflists/` is loaded (deck_manager.cpp:87-96 `LoadLFListFolder`, extension filter `conf`)

Section headers like `#forbidden Goat` / `#limited Goat` / `#semi limited Goat` / `#unlimited` are comments only — the number after each passcode is the sole source of the limit.

### Contents / stats (computed from the file)

- 1712 lines total; 1705 entry lines; **1704 unique passcodes** (one duplicated line: `511000868 1 --Twin-Headed Behemoth` appears at lines 46 and 729 — harmless, second overwrites first in the `content` map)
- Limits: 19 at `0` (forbidden), 43 at `1`, 15 at `2`, 1627 at `3`
- Even though it is a whitelist, banned cards are still listed with limit `0` (documentation value; functionally identical to not listing them)
- **All 191 goat-entries IDs (504700000–504700190) appear in the list**; **none of their modern-alias passcodes appear** (verified by cross-join with goat-entries.cdb) — i.e. only the GOAT variants are legal, never the errata'd modern versions
- 18 passcodes from the `511xxxxxx` unofficial/pre-errata range appear (e.g. 511000818 Sinister Serpent (Pre-Errata) at 1, 511000819 CED (Pre-Errata) at 0, 511001039 DMoC (Pre-Errata) at 1, 511002996 Imperial Order (Pre-Errata) at 0)
- One pre-errata card uses the "+10" ID convention instead: `16226796 2 --Night Assailant (Pre-Errata)` (modern ID 16226786 + 10)
- Alternate artworks are individually listed (e.g. Jinzo 77585513 and 77585514, Harpie's Feather Duster 18144506/18144507, Monster Reborn 83764718/83764719, Ring of Destruction pre-errata 511000824/511000825)
- Cards that were never errata'd (or whose modern text is acceptable) are whitelisted under their ordinary `cards.cdb` passcode (e.g. `33184167 1 --Tribe-Infecting Virus`, `14087893 3 --Book of Moon`)

### `$whitelist` semantics in the client

`LFList::GetLimitationIterator` (`/home/user/edopro/gframe/deck_manager.h:23-30`):

```cpp
auto flit = content.find(pcard->code);
if(flit == content.end() && pcard->alias) {
    if(!whitelist || pcard->IsInArtworkOffsetRange())
        flit = content.find(pcard->alias);
}
```

- Non-whitelist: a card not listed under its own code falls back to its alias entry.
- Whitelist: the alias fallback is allowed **only for alt artworks** (alias within ±10 of code, `data_manager.h:74-85`, `CARD_ARTWORK_VERSIONS_OFFSET = 10`, strict `<`). A GOAT variant (alias offset in the millions) must therefore be listed under its own passcode — which GOAT.lflist.conf does for all 191.
- Deck check (`deck_manager.cpp:186-201`, `CheckCards`): copies are counted under `alias ? alias : code` (deck_manager.cpp:192-194), so a GOAT variant and its modern version would share the 3-copy bucket; then `if ((!is_end && dc > it->second) || (curlist->whitelist && is_end)) return DeckError::LFLIST` (deck_manager.cpp:199) — **in a whitelist, any card without an entry is illegal**. This is what shuts out the entire post-GOAT cardpool and the errata'd modern versions.

### Naming convention: why `0TCG.lflist.conf`?

Files present: `0TCG.lflist.conf, GOAT.lflist.conf, OCG.lflist.conf, Rush-Prerelease.lflist.conf, Rush.lflist.conf, Speed.lflist.conf, Traditional.lflist.conf, World.lflist.conf` (ls of `/workspace/projectignis/lflists`).

- `LoadLFListFolder` loads files in the order returned by `Utils::FindFiles`, which sorts case-insensitively (`/home/user/edopro/gframe/utils.cpp:575`).
- `Game::RefreshLFLists` (`/home/user/edopro/gframe/game.cpp:2465-2484`) populates the host/deck-editor banlist combo boxes in `_lfList` order and defaults to index 0 unless a previously used list hash (`lastlflist`) matches.
- Therefore the `0` prefix makes the current TCG list sort before everything else → it is the first and default list. **ASSUMPTION (intent)**: the prefix exists precisely for this; the mechanism is confirmed, the author's intent is inferred.
- Headers of the others: `0TCG` = `!2026.05 TCG` with `#Forbidden` sections; `Traditional.lflist.conf` = `!2026.05 Traditional` (TCG list with all forbidden cards moved to Limited — starts directly with `#Limited`); `World.lflist.conf` = `!2026.05 Worlds`. None of these carry `$whitelist`; only `GOAT`, `Rush`, `Rush-Prerelease`, `Speed` do (grep `$whitelist` across the folder).
- Rush whitelists are machine-generated from cdb `ot` flags by `/workspace/projectignis/babelcdb/ci/rush-whitelist.sh` (SQL `WHERE ot == 0x200`, emits `id 3 --name` lines, prepends the 3-line header, then appends a hand-kept template banlist `ci/rush-template.lflist.conf`). GOAT's list shows no generator in-repo — **ASSUMPTION**: hand-maintained.

---

## 2. `goat-entries.cdb` (`/workspace/projectignis/babelcdb/goat-entries.cdb`)

### Schema (standard ygopro cdb)

```sql
CREATE TABLE "datas" ("id","ot","alias","setcode","type","atk","def","level","race","attribute","category", PRIMARY KEY("id"))
CREATE TABLE "texts" ("id","name","desc","str1".."str16", PRIMARY KEY("id"))
```

### Contents

- **191 rows** in both tables; IDs are a dense block **504700000–504700190**
- **Every row has `ot = 8`** (`SELECT DISTINCT ot` returns only 8) → `SCOPE_ILLEGAL` in the client (see §6)
- **Every row has a non-zero `alias` pointing at the modern card's passcode** (e.g. `504700178 → 26202165` Sangan, `504700188 → 34124316` Cyber Jar, `504700123 → 73915051` Scapegoat, `504700102 → 63519819` Thousand-Eyes Restrict)
- Every `name` is suffixed `" (GOAT)"`: `Sangan (GOAT)`, `Cyber Jar (GOAT)`, `Reinforcement of the Army (GOAT)`, …
- Alias offsets are far outside the ±10 alt-artwork window, so these are distinct cards to the client's deck-editor/banlist logic, but the alias still links them to the modern card (name identity in-duel, copy counting, sorting).

Full row dump (id, alias, ot, name) captured during research; representative sample:

```
(504700000, 126218,   8, 'Skull Dice (GOAT)')
(504700055, 32807846, 8, 'Reinforcement of the Army (GOAT)')
(504700102, 63519819, 8, 'Thousand-Eyes Restrict (GOAT)')
(504700118, 72989439, 8, 'Black Luster Soldier - Envoy of the Beginning (GOAT)')
(504700178, 26202165, 8, 'Sangan (GOAT)')
(504700188, 34124316, 8, 'Cyber Jar (GOAT)')
(504700190, 94773007, 8, 'Jirai Gumo (GOAT)')
```

### Comparisons with `cards.cdb`

**Sangan** — goat 504700178 (ot=8, alias=26202165, category=512) vs modern 26202165 (ot=3, alias=0, category=544):

- GOAT desc: "When this card is sent from the field to the Graveyard, select 1 monster with an ATK of 1500 or less from your Deck, show it to your opponent, and add it to your hand. Then shuffle your Deck." (pre-errata, mandatory trigger, no name-lock)
- Modern desc: "...but you cannot activate cards, or the effects of cards, with that name... once per turn." (errata text)

**Cyber Jar** — goat 504700188 vs modern 34124316: identical stats; GOAT text is the original "pick up 5 cards" wording, modern text is the "reveal" errata with the fewer-than-5 clause.

**Reinforcement of the Army** — goat 504700055 vs modern 32807846: GOAT text "…Then shuffle your Deck." (original), modern text is the short errata.

### Related range: `511xxxxxx` pre-errata cards live in `cards-unofficial.cdb`, not goat-entries

`/workspace/projectignis/babelcdb/cards-unofficial.cdb` (5878 rows) holds the "(Pre-Errata)" variants, also with `ot = 8` and `alias` → modern ID:

```
(511000818, 8131171,  8, 'Sinister Serpent (Pre-Errata)')
(511000819, 82301904, 8, 'Chaos Emperor Dragon - Envoy of the End (Pre-Errata)')
(511001039, 40737112, 8, 'Dark Magician of Chaos (Pre-Errata)')
(511002996, 61740673, 8, 'Imperial Order (Pre-Errata)')
(16226796,  16226786, 8, 'Night Assailant (Pre-Errata)')   <- modern+10 convention
(21593987,  21593977, 8, 'Makyura the Destructor (Pre-Errata)')  <- modern+10
```

Two pre-errata ID conventions coexist:
1. `511YYYXXX` — the BabelCDB "unofficial" range (README: "Unofficial cards fall under numerous ranges … slowly being reworked and reorganized to the 511YYYXXX range", `/workspace/projectignis/babelcdb/README.md`).
2. `modern_id + 10` — deliberately the first value **outside** the alt-artwork alias window (`IsInArtworkOffsetRange` is strict `< 10`, so +10 is a distinct card, `data_manager.h:80-85`). Examples above plus Firewall Dragon (5043020), Ancient Fairy Dragon (25862691), etc.

**Distinction between the two cdbs**: goat-entries.cdb = cards whose GOAT-2005 behavior/ruling/text differs from today but that had no *printed errata* requiring a general pre-errata card ("(GOAT)" suffix, 5047xxxxx range, only whitelisted in GOAT); cards-unofficial.cdb "(Pre-Errata)" = genuinely errata'd cards usable by any format (e.g. Traditional-style play). **ASSUMPTION**: this editorial split is inferred from naming and content; no doc states it explicitly.

Sinister Serpent pre-errata text (511000818): "During your Standby Phase, if there is a 'Sinister Serpent' in your Graveyard: you can add this card from your Graveyard to your hand." vs modern 8131171's banish-errata text — confirmed in both dbs.

---

## 3. BabelCDB conventions (`README.md`, `ci/`, `util/`)

From `/workspace/projectignis/babelcdb/README.md`:

- Databases are auto-synced to servers; changes are auto-imported to "the repository the users get updates from", linked as DeltaPuppetOfStrings (README is stale here; the client's configs.json now points at DeltaBagooska — see §5).
- Delta pipeline: GitHub Actions computes **delta databases** ("a database containing only new or changed rows compared to the previous version"); new cdbs since the last tag are committed whole.
- Passcode policy: prerelease OCG/TCG cards get 9-digit prerelease passcodes (`10ZZYYXXX` etc.), Speed Duel `30ZYYYXXX`, Rush `160ZYYXXX`, unofficial → `511YYYXXX`. **The `5047xxxxx` goat range is NOT documented in the README** — it only exists in practice (goat-entries.cdb + GOAT.lflist.conf + script/goat). Note `0x8` ot is also not documented there; the README documents pre-release ot 0x100.
- "Cards with passcodes aliased to a passcode within 10 are treated as alternate artworks." — the alias/alt-art rule, matching the client's `CARD_ARTWORK_VERSIONS_OFFSET = 10`.
- `ci/`: `sqlite3-git.sh` + `sqlite3-delta.sh` (dump INSERTs, `comm -13` old vs new, build `*.delta.cdb`), `cross-delta.sql`, `rush-whitelist.sh` + `rush-template.lflist.conf` (whitelist generation from `ot` bits).
- `util/merge-cdb.py`: merges all cdbs in a directory "following the same semantics that a client or server would do" (schema copied from Multirole's `CardDatabase.cpp`) — later rows replace earlier by primary key.

---

## 4. Card scripts (`/workspace/projectignis/cardscripts`)

- Top-level directories: `goat/` (**191 scripts**, `c504700000.lua`–`c504700190.lua`, exactly one per goat-entries row), `pre-errata/` (**68 scripts**: 51 in the 511-range + 17 using modern+10 IDs), `official/`, `pre-release/`, `unofficial/`… Filename convention `c<passcode>.lua` throughout.
- `README.md:5`: "the most accurate rulings and mechanics, including pre-errata variants" — the only in-repo mention of the concept.
- Scripts are full standalone implementations (copies of the modern script, edited), not patches/includes of the modern script. They begin with the JP name comment and usually a one-line comment stating the GOAT-era difference:
  - `goat/c504700188.lua` (Cyber Jar): comment "--Unlike OCG, first both players reveal, then both summon"; diff vs `official/c34124316.lua` shows no `CATEGORY_SET` and reordered `Duel.ConfirmDecktop` (both reveals before summoning).
  - `goat/c504700116.lua` (Nobleman of Crossout): comment "--view your own deck for verification".
  - `goat/c504700102.lua` (Thousand-Eyes Restrict): comment "--Gains stats of trap monsters as well"; diff shows the modern script excludes non-monster (trap-monster) originals from the atk/def copy, GOAT one doesn't.
  - `goat/c504700178.lua` (Sangan) vs `official/c26202165.lua`: GOAT drops `SetCountLimit(1,id)` and the whole name-lock effect, and adds the failed-search deck reveal.
- **Period-ruling helper**: `Duel.GoatConfirm(tp,loc)` defined in `/workspace/projectignis/cardscripts/utility.lua:2747` (reveal deck/hand to prove a whiffed search, then shuffle). Used in 73 of the 191 goat scripts (grep count) — encodes the 2005 "failed search must be verified" ruling.
- Pre-errata scripts reference modern codes for name checks, e.g. `pre-errata/c511000818.lua` sets `s.listed_names={8131171}` and its condition checks `Card.IsCode(...,8131171)` — this works because in-duel the card's code resolves to its alias (see §6, ocgcore `get_code`).
- Script discovery: repos contribute `script_path` and its subfolders (2 levels) to the client's `script_dirs` (`/home/user/edopro/gframe/game.cpp:2771-2776`, plus `./script/` and its subfolders at game.cpp:3991-3993); `Game::FindScript` (game.cpp:3868-3887) tries `dir + "cXXXXXXX.lua"` for each dir. So `script/goat/c504700188.lua` is found by plain filename — the subdirectory is organizational only; **no format switching is involved, the GOAT variant is simply a different passcode.**

---

## 5. Distribution / delivery (`/workspace/projectignis/distribution` + DeltaBagooska)

`/workspace/projectignis/distribution/config/configs.json` "repos" array:

1. `https://github.com/ProjectIgnis/DeltaBagooska` — "Project Ignis updates", `repo_path ./repositories/delta-bagooska`, `has_core: true`, `core_path "bin"`, `data_path ""` (repo root), `script_path "script"`.
2. `https://github.com/ProjectIgnis/LFLists` — "Forbidden & Limited Card Lists", `repo_path ./repositories/lflists`, `lflist_path "."`. **This is how GOAT.lflist.conf reaches users.**
3. `https://github.com/ProjectIgnis/Puzzles`.

The distribution repo's own `lflists/`, `expansions/`, `script/` directories are empty (only `.gitkeep`) — everything card-related arrives via the repos above at runtime (the README's configs.json section documents `data_path`/`script_path`/`lflist_path` semantics).

Verified contents of DeltaBagooska (shallow clone, HEAD da54f282c7…):

- root: `cards.delta.cdb`, `cards-unofficial.delta.cdb`, **`goat-entries.delta.cdb`**, `cards-rush.delta.cdb`, `cards-skills.delta.cdb`, full `prerelease-*.cdb` files, `strings.conf`, `mappings.json`, `VERSION`
- `script/` mirrors CardScripts including **`script/goat/` and `script/pre-errata/`**
- `bin/` with ocgcore builds (`ocgcore.dll`, `libocgcore.so`, …)
- README: "EDOPro 41 'Bagooska' … automatically generated from CardScripts and BabelCDB"
- `goat-entries.delta.cdb` currently holds only **5 changed rows** (504700085–504700190) — it is a *delta* against the snapshot bundled with the EDOPro 41 base install. **ASSUMPTION**: the full 191-row goat-entries.cdb ships inside the base game installer (built from BabelCDB at release time); could not verify installer contents offline. The BabelCDB README's "new CDBs are directly committed / deltas for existing ones" rule is consistent with this.
- Naming drift: BabelCDB README says deltas go to *DeltaPuppetOfStrings*, CardScripts README says *DeltaHopeHarbinger*; configs.json ships *DeltaBagooska*. **ASSUMPTION**: one combined delta repo per client release nickname; the per-source READMEs are stale.

Client-side loading: `Game::ParseGithubRepositories` (`/home/user/edopro/gframe/game.cpp:2670-2688`) loads **every `*.cdb`** in each repo's `data_path` via `gDataManager->LoadDB`, plus `strings.conf` and `mappings.json`. `DataManager::ParseDB` (`/home/user/edopro/gframe/data_manager.cpp:96-178`) upserts by passcode into `cards[code]`, so later-loaded delta rows override the base install's rows. goat-entries rows coexist with cards.cdb rows because the passcodes never collide.

### Whitelist ↔ cdb cross-check (the key linkage)

- GOAT.lflist.conf whitelists the **pre-errata/goat IDs, not the modern IDs**, whenever a variant exists: all 191 `5047xxxxx` IDs are present; 18 `511xxxxxx` IDs and `16226796` are present; none of the 191 modern aliases appear anywhere in the list.
- e.g. `504700178 1` (Sangan (GOAT)) is in the list, `26202165` (modern Sangan) is not; `511000818 1` in, `8131171` not; `504700188 1` in, `34124316` not; `504700123 3` in, `73915051` not.
- Cards without a goat/pre-errata variant are whitelisted under their modern cards.cdb passcode.

---

## 6. Why goat cards don't leak into normal play

Three independent gates, all keyed off `ot = 8`:

1. **Scope flags** (`/home/user/edopro/gframe/data_manager.h:21-34`):
   ```
   SCOPE_OCG 0x1, SCOPE_TCG 0x2, SCOPE_ANIME 0x4, SCOPE_ILLEGAL 0x8,
   SCOPE_VIDEO_GAME 0x10, SCOPE_CUSTOM 0x20, SCOPE_SPEED 0x40,
   SCOPE_PRERELEASE 0x100, SCOPE_RUSH 0x200, SCOPE_LEGEND 0x400, SCOPE_HIDDEN 0x1000
   SCOPE_OFFICIAL = OCG|TCG|PRERELEASE
   ```
   goat-entries and 511-range pre-erratas all carry `ot = 8` = `SCOPE_ILLEGAL` (a scope value, not a "banned" marker).

2. **Deck editor visibility** (`/home/user/edopro/gframe/deck_con.cpp:1173`, `CheckCardProperties`): a card is hidden when `(ot & SCOPE_OFFICIAL) != ot` unless the "Anime" checkbox is on **or the currently selected banlist is a whitelist**. So with the TCG list selected the GOAT cards are invisible; selecting the GOAT whitelist reveals them. Additionally, in whitelist mode any card not on the list is filtered out of search results (deck_con.cpp:1235-1301: unlisted ⇒ `count = -1` ⇒ rejected), so the editor shows exactly the GOAT pool. There is also a dedicated "Illegal" limitation filter (`LIMITATION_FILTER_ILLEGAL`, deck_con.cpp:1286-1288, `ot == SCOPE_ILLEGAL`).

3. **Deck legality check** (`/home/user/edopro/gframe/deck_manager.cpp:157-204`, `CheckCards`):
   - For host settings OCG/TCG/OCG&TCG: `#define CHECK_UNOFFICIAL(cit) if (cit->ot > 0x3) return DeckError::UNOFFICIALCARD` (deck_manager.cpp:165) — `ot 8` decks are rejected outright in official-cards rooms. GOAT rooms must therefore host with allowed cards = Any (`ALLOWED_CARDS_ANY` skips the check; enum in deck_manager.h:32-38).
   - Plus the whitelist rule from §1: with the GOAT list selected, unlisted cards ⇒ `DeckError::LFLIST` (deck_manager.cpp:199), and with any *other* list selected the goat card (code 5047…, far alias) finds no entry → legal by count only in non-whitelists, but it already failed the `ot > 0x3` gate in official rooms.

**In-duel identity via alias (ocgcore)**: `card::get_code()` (`/workspace/edo9300/ygopro-core/card.cpp:242-273`, alias substitution at 265-266) returns `data.alias` when set (absent code-change effects). So "Sangan (GOAT)" *is* card 26202165 during the duel for every name/code check ("Sangan" searchability, `IsCode`, etc.), while its stats/text/script come from its own row 504700178. Copy-counting in deck check also merges via alias (deck_manager.cpp:192). The client only treats alias-within-10 as "same artwork variant" (`IsInArtworkOffsetRange`, data_manager.h:74-85); farther aliases are distinct deck-editor entries that still share in-duel identity.

---

## Blueprint distilled for our own historical-format implementation

1. **One cdb per format** for behavior-variant cards: unique ID block (Ignis uses 504700000+ for GOAT), `ot = 8`, `alias` = modern passcode, name suffixed with the format tag.
2. **One standalone Lua script per variant ID** in a per-format script subfolder (any subfolder of a repo `script_path` works — lookup is by filename only).
3. **A whitelist lflist**: 3-line header (`#[display]`, `!Name`, `$whitelist`), then `code limit --name` lines; list variant IDs (whitelists don't follow far aliases), list every alt-art ID, list unchanged cards by modern ID; limit 0 entries optional documentation.
4. **Ship** the lflist via a `lflist_path` repo entry and the cdb+scripts via a `data_path`/`script_path` repo entry in `config/configs.json` (or drop them in `./expansions/` — README documents that path too).
5. Host with allowed cards "Any" so `ot=8` passes; the whitelist enforces the pool.
