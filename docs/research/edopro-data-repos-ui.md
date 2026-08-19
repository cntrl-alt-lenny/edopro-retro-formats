> Point-in-time research note (2026-08-19), verified against the pinned revisions in data/sources.json.

# EDOPro: card database loading, script resolution, repo configuration, and duel-rule presets

Research note for the historical-format recreation project.
Sources: `/home/user/edopro` (client, edo9300/edopro fork), `/workspace/edo9300/ygopro-core` (ocgcore),
`/workspace/projectignis/distribution`, `/workspace/projectignis/lflists`, `/workspace/projectignis/babelcdb`.
All line numbers refer to those working copies as of 2026-08-19.

---

## 1. `.cdb` loading: paths, order, conflict behavior

### 1a. Startup scan (synchronous, before the window opens)

`DataHandler::LoadDatabases()` — `gframe/data_handler.cpp:28-39`:

1. `./cards.cdb` (if present) — `data_handler.cpp:29-32`
2. every `*.cdb` under `./expansions/` recursively up to **2 subdirectory levels** — `data_handler.cpp:33-37` (`Utils::FindFiles(..., {"cdb"}, 2)`)
3. every `*.cdb` inside any `./expansions/*.zip` archive (up to 3 path levels inside the zip) — `LoadArchivesDB()`, `data_handler.cpp:40-52`; the zips were mounted earlier by `LoadZipArchives()` (`data_handler.cpp:96-104`)

`Utils::FindFiles` sorts results case-insensitively (`gframe/utils.cpp:560-577`, sort at :575), so within one directory the load order is alphabetical.

Every DB that loads successfully is also registered as a WindBot AI database (`WindBot::AddDatabase`, `data_handler.cpp:31,36`; `gframe/windbot.cpp:140-147`).

Strings are loaded at the same stage: `./config/strings.conf` then `./expansions/strings.conf` (`data_handler.cpp:130-133`), and id mappings from `./config/mappings.json` (`data_handler.cpp:165`, parser at `gframe/data_manager.cpp:303-327`).

### 1b. Repo databases (asynchronous, as each git repo becomes ready)

Repos are cloned/fetched on 3 worker threads (`gframe/repo_manager.cpp:97-98`). Each frame of the main loop calls `ParseGithubRepositories(gRepoManager->GetReadyRepos())` (`gframe/game.cpp:2029`). For each ready non-language repo (`game.cpp:2670-2688`):

- every `*.cdb` **directly in** the repo's `data_path` (depth 0, no subdirectories: `FindFiles(data_path, {"cdb"}, 0)`, `game.cpp:2678`) is loaded via `gDataManager->LoadDB` and added to WindBot (`game.cpp:2680-2686`)
- `data_path/strings.conf` is loaded (`game.cpp:2687`) — this can add/override `!system`, `!counter`, `!setname`, `!victory` strings
- `data_path/mappings.json` is loaded (`game.cpp:2688`)

`GetReadyRepos()` returns ready repos in the order they were added (`repo_manager.cpp:117-140` — it walks `available_repos` in insertion order and stops at the first not-yet-ready repo, so parse order == config order even with parallel clones). Repos are added in the order: all of `user_configs.json` first, then all of `configs.json` (`data_handler.cpp:157-158`), each file's `repos` array in listed order (`repo_manager.cpp:153-186`).

### 1c. Conflict behavior — LAST LOADED WINS

`DataManager::ParseDB` (`gframe/data_manager.cpp:96-177`) runs
`SELECT ... FROM datas,texts WHERE texts.id = datas.id` (`data_manager.cpp:23-25`) and stores each row with
`auto ptr = &cards[code];` (`data_manager.cpp:109`) — `cards` is a `std::unordered_map<uint32_t, CardDataM>` (`data_manager.h:179`). `operator[]` reuses the existing entry and every field is then reassigned (`data_manager.cpp:118-167`). There is **no duplicate detection and no skip**: a later-loaded cdb silently overwrites an earlier entry with the same `datas.id`.

Effective priority (lowest → highest):
`./cards.cdb` → `./expansions/**.cdb` (alphabetical) → cdbs in `./expansions/*.zip` → repo cdbs in ready/parse order (user_configs repos, then configs.json repos; the **last listed repo wins**).

So a repo cdb overrides the base game DB for the same card code — this is exactly how ProjectIgnis ships updates (the "DeltaBagooska" repo's cdbs override any stale local data).

The cdb schema (from `/workspace/projectignis/babelcdb/goat-entries.cdb`, identical across BabelCDB):
`datas(id,ot,alias,setcode,type,atk,def,level,race,attribute,category)`, `texts(id,name,desc,str1..str16)`.
`ot` is the scope bitmask (`SCOPE_OCG 0x1, SCOPE_TCG 0x2, SCOPE_ANIME 0x4, SCOPE_ILLEGAL 0x8, ... SCOPE_PRERELEASE 0x100, SCOPE_RUSH 0x200, SCOPE_LEGEND 0x400, SCOPE_HIDDEN 0x1000` — `gframe/data_manager.h:21-31`). `level` packs pendulum scales in the upper bytes (`data_manager.cpp:144-151`); for Link monsters `def` is the link marker (`data_manager.cpp:138-142`).

### 1d. The card reader callback into ocgcore

`Game::SetupDuel` wires `opts.cardReader = DataManager::CardReader; opts.payload1 = gDataManager;` (`gframe/game.cpp:3922-3931`). `CardReader` is a memcpy of the client's in-memory record (`data_manager.cpp:553-557`). ocgcore stores it via `read_card_callback` (`/workspace/edo9300/ygopro-core/duel.cpp:17-20`). So whatever won the cdb override race is what the core simulates with.

---

## 2. Repo entry schema in `configs.json`

### 2a. Recognized keys (from the parser, `RepoManager::LoadRepositoriesFromJson`, `gframe/repo_manager.cpp:147-186`)

Top-level object: `{"repos": [ ... ]}` (only the `"repos"` array is read by RepoManager; other top-level keys are `"urls"` (pic download sources, `data_handler.cpp:54-95`), `"servers"` (`game.cpp:2788-2818`), `"posixPathExtension"`).

Every recognized per-repo key, with json type and default (defaults from `GitRepo` declaration, `gframe/repo_manager.h:30-44`):

| key | type | default | meaning |
|---|---|---|---|
| `should_read` | bool | `true` | if explicitly `false`, entry is skipped entirely (`repo_manager.cpp:157-161`) |
| `not_git_repo` | bool | `false` | treat `repo_path` as a plain local folder; no clone/fetch (`repo_manager.cpp:163`, used at `repo_manager.cpp:218-227`) |
| `url` | string | `""` | git remote URL; **required unless** `not_git_repo` is true (`repo_manager.cpp:164-166`, `Sanitize` :31-32) |
| `should_update` | bool | `true` | if false, an existing clone is opened but never fetched/reset (`repo_manager.cpp:167`, used at :295) |
| `repo_path` | string | derived | local checkout dir, prefixed with `./` by `Sanitize` (`repo_manager.cpp:34-35`); if empty, becomes `./repositories/<repo_name>` (:43,:47) |
| `repo_name` | string | derived | display name; if empty, derived from `url` or `repo_path` filename (:40,:45) |
| `data_path` | string | `""` | dir (relative to `repo_path`) scanned for `*.cdb` + `strings.conf` + `mappings.json` + `lflist.conf`; `""` = repo root (`Sanitize` :49) |
| `lflist_path` | string | `"lflists"` | dir (relative to repo) scanned for `*.conf` banlists (:51-54) |
| `script_path` | string | `"script"` | dir (relative to repo) added to script search path, plus its subdirs 2 deep (:56-59; `game.cpp:2771-2776`) |
| `pics_path` | string | `"pics"` | dir added to card-art search path (:61-64; `game.cpp:2777`) |
| `is_language` | bool | `false` | marks a locale repo; its cdbs/strings load as *locale* text overlays instead of card data (`repo_manager.cpp:174`; `game.cpp:2689-2707`) |
| `language` | string | `""` | only read when `is_language` is true (`repo_manager.cpp:175-176`) |
| `has_core` | bool | `false` | repo ships an ocgcore shared library; **only parsed in `YGOPRO_BUILD_DLL` builds** (`repo_manager.cpp:177-181`) |
| `core_path` | string | `""` | dir (relative to repo) containing the core dll; only read if `has_core` (:179-180; setting `core_path` alone also implies `has_core`, `Sanitize` :66-69) |

Unrecognized keys are ignored; wrong-typed values are ignored (the `JSON_SET_IF_VALID` macro checks the json type, `repo_manager.cpp:147-151`). Entries failing `Sanitize()` (no url and not local; no name derivable) are dropped (:182-183). Duplicate `repo_path`s are deduped, first one wins (`AddRepo`, `repo_manager.cpp:208-213`).

All path fields are joined as `repo_path + "/" + field + "/"` and normalized — they must be *relative* subpaths of the checkout.

### 2b. How a user adds a third-party repo

`GameConfig` loads `./config/configs.json` into `configs` and `./config/user_configs.json` into `user_configs` (`gframe/game_config.cpp:19-44`). Both are fed to RepoManager, **user file first** (`data_handler.cpp:157-158`). The shipped `user_configs.json` is an empty skeleton `{"repos": [], "urls": [], "servers": []}` (`/workspace/projectignis/distribution/config/user_configs.json`). A user (or a format package installer) adds a repo by appending an object to `user_configs.json`'s `repos` array, e.g.:

```json
{ "url": "https://github.com/you/goat-format-pack",
  "repo_name": "Goat Format Pack",
  "repo_path": "./repositories/goat-pack",
  "data_path": "",
  "script_path": "script",
  "lflist_path": "lflists",
  "should_update": true }
```

There is no in-game UI for adding repos — it's manual JSON editing (the Repositories tab only shows clone/update progress and changelogs, `game.cpp:2600-2669`).

Note on priority: because user_configs repos are *parsed first*, a shipped-configs repo listed later can override a user repo's card data (later `LoadDB` wins) and its scripts sit *earlier* in the search path (front-insertion per parsed repo, `game.cpp:2771`). I.e. **later entry = higher priority for both cdbs and scripts**.

### 2c. Shipped Distribution `configs.json` (`/workspace/projectignis/distribution/config/configs.json`)

Three repos:
1. `https://github.com/ProjectIgnis/DeltaBagooska` → `./repositories/delta-bagooska`, `has_core: true`, `core_path: "bin"`, `data_path: ""` (cdbs at repo root), `script_path: "script"` — the main updates repo (cdbs aggregated from BabelCDB, all card scripts, prebuilt ocgcore).
2. `https://github.com/ProjectIgnis/LFLists` → `./repositories/lflists`, `lflist_path: "."` — banlists at repo root. The lflists repo currently ships: `0TCG.lflist.conf, GOAT.lflist.conf, OCG.lflist.conf, Rush-Prerelease.lflist.conf, Rush.lflist.conf, Speed.lflist.conf, Traditional.lflist.conf, World.lflist.conf` (`/workspace/projectignis/lflists/`).
3. `https://github.com/ProjectIgnis/Puzzles` → `repo_path: "./puzzles/Canon collection"` — cloned straight into the puzzle browser's working dir (`lstSinglePlayList->setWorkingPath(L"./puzzles")`, `game.cpp:788-791`).

Plus `urls` (three `"default"` pic/field/cover download sources) and 5 `servers` entries.
The distribution repo's `expansions/`, `lflists/`, `script/` folders are empty placeholders — all content arrives via the repos at runtime.

---

## 3. Card script resolution

### 3a. What ocgcore asks for

ocgcore requests scripts by name through the `OCG_ScriptReader` callback (`read_script`, `/workspace/edo9300/ygopro-core/duel.h:109-111,116,120`). For a card it requests **`c<code>.lua`** (decimal code, no padding): `interpreter.cpp:287` `pduel->read_script(format_to(code_buf, "c%u.lua", code))` inside `interpreter::load_card_script` (`interpreter.cpp:235-299`). If the card's `alias` is within ±10 of its code (alt-artwork range), the **alias's** script is loaded instead (`interpreter.cpp:145-148`). Scripts can also request other files via `Duel.LoadScript` from Lua (`libduel.cpp:4087-4098`).

### 3b. Client-side resolution

`Game::ScriptReader` → `Game::LoadScript` → `FindAndReadScript` → `FindScript` (`gframe/game.cpp:3941-3943, 3918-3921, 3890-3894, 3868-3887`).

`FindScript` walks `script_dirs` in order; each entry is either a real directory (checks `dir + name`) or the literal token `"archives"`, which searches `script/<name>` inside every mounted `./expansions/*.zip` (`game.cpp:3870-3877`, `Utils::FindFileInArchives`, `utils.cpp:613-624`). Final fallback: the raw name as a path relative to the CWD (`game.cpp:3884-3885`, used for puzzle files like `./puzzles/foo.lua`, cf. `single_mode.cpp:156-165`).

`script_dirs` construction:
- Base order (at startup, `Game::PopulateResourcesDirectories`, `game.cpp:3984-3993`):
  1. `./expansions/script/`
  2. every subfolder of `./expansions/script/` (1 level)
  3. `"archives"` (zips)
  4. `./script/`
  5. every subfolder of `./script/` (1 level)
- Each ready repo *prepends* (higher priority): its `script_path`, then its subfolders 2 levels deep (`Game::UpdateRepoInfo`, `game.cpp:2770-2776`). So after startup the order is: [last-parsed repo's script subdirs, last repo's script_path, …, first repo's…, ./expansions/script/, …, ./script/…].

First match wins. Therefore a repo script `c12345.lua` overrides `./script/c12345.lua`, and among repos the one listed later in configs.json wins.

`ReadScript` strips a UTF-8 BOM if present (`game.cpp:3895-3916`).

### 3c. Init scripts

- `./init.lua` in the game root is collected at startup (`game.cpp:3985-3986`).
- Each non-language repo's `script_path/init.lua` is collected when the repo becomes ready (`game.cpp:2772-2774`).
- On every duel creation, `Game::SetupDuel` loads `constant.lua`, then `utility.lua` (both resolved through the same `script_dirs` search), then all collected `init.lua` files (`game.cpp:3932-3938`). This is a sanctioned hook for a format package to patch core utility behavior per duel.

---

## 4. Duel-rule presets and the custom-rules dialog

### 4a. Flag definitions (compiled in)

Client copy: `gframe/ocgapi_constants.h:379-428`; identical macros exist core-side. Individual `DUEL_*` bit flags occupy a 64-bit space (`DUEL_TCG_SEGOC_NONPUBLIC 0x100000000` and above are in the high 32 bits, `ocgapi_constants.h:411-415`).

Preset combinations (`ocgapi_constants.h:416-428`):
- `DUEL_MODE_SPEED` = 3-columns | no MP2 | trap-monsters-no-zone | trigger-only-in-location
- `DUEL_MODE_RUSH` = 3-columns | no MP2 | no SP | 1st-turn-draw | inverted quick priority | draw-until-5 | no hand limit | unlimited summons | trap-monsters-no-zone | trigger-only-in-location | extra-deck-ritual
- `DUEL_MODE_MR1` = OCG obsolete ignition | 1st-turn-draw | 1 faceup field | spsummon-once-old-negate | return-to-deck-triggers | cannot-summon-oath-old
- `DUEL_MODE_GOAT` = MR1 | TCG fast-effect ignition | use-traps-in-new-chain | 6-step battle step | trigger-when-private-knowledge | equip-not-sent-if-missing-target | 0-ATK-destroyed | store-attack-replays | single-chain-in-damage-substep | can-repos-if-non-sumplayer | TCG SEGOC nonpublic | SEGOC first-trigger
- `DUEL_MODE_MR2/3/4/5` per macro; forbidden-type companions `DUEL_MODE_MR1_FORB = XYZ|PENDULUM|LINK`, `MR2_FORB = PENDULUM|LINK`, `MR3_FORB = LINK`, `MR4/5_FORB = 0`.

### 4b. The preset combobox

`Game::ReloadCBDuelRule` (`gframe/game.cpp:3496-3507`) hard-codes exactly 8 items, by system-string id:
index 0-4 = strings 1260-1264 (**"Master Rule 1"…"Master Rule 4", "Master Rules (2020)"**), index 5 = 1258 (**"Speed Duel"**), index 6 = 1259 (**"Rush Duel"**), index 7 = 1248 (**"GOAT"**) — string values from `/workspace/projectignis/distribution/config/strings.conf`. A 9th item "Custom Rule" (string 1630) is appended dynamically when the current flag set matches no preset (`Game::UpdateDuelParam`, `game.cpp:3161-3165`).

Selection → flags mapping (host dialog): `gframe/menu_handler.cpp:964-1015` (`COMBOBOX_DUEL_RULE` handler; index 0-4 → `DUEL_MODE_MR1..5` + `_FORB` + OCG deck sizes 40-60/0-15/0-15 + 5-card hand; index 5 → SPEED + 20-30/0-6/0-6 + 4-card hand; index 6 → RUSH + 40-60/0-15/0-15 + 4-card hand; index 7 → GOAT + `MR1_FORB` + 40-60/**0-999**/0-15 + auto-checks "TCG rulings" + 5-card hand). Same mapping in the tab-change handler (`menu_handler.cpp:905-961`) and for hand-test in the deck editor (`gframe/deck_con.cpp:184-205`, combobox built at `game.cpp:618`). Reverse mapping (flags → selected preset) in `Game::UpdateDuelParam` (`game.cpp:3097-3170`).

### 4c. Custom rules UI

The host dialog's "Custom Rule" tab (built at `game.cpp:1319-1364`) has:
- `chkCustomRules[32]` (declared `[7+12+8+5]`, `game.h:226`), labels = system strings **1631-1662** ("OCG Ignition Priority" … "Normal Summon in face-up Defense position"). Index→flag mapping (`game.cpp:1337-1351`, mirrored at `game.cpp:3100-3113`): i==19 → `DUEL_USE_TRAPS_IN_NEW_CHAIN` (0x4), i==20 → `DUEL_6_STEP_BATLLE_STEP` (0x8), i==21 → `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` (0x20), otherwise `0x100 << i` for i<19 and `0x100 << (i-3)` for i>21 — i.e. every flag from `DUEL_OCG_OBSOLETE_IGNITION` (0x100) through `DUEL_NORMAL_SUMMON_FACEUP_DEF` (0x1000000000) is individually togglable. Not exposed as checkboxes: `DUEL_TEST_MODE`, `DUEL_ATTACK_FIRST_TURN`, `DUEL_PSEUDO_SHUFFLE`, `DUEL_SIMPLE_AI`, `DUEL_RELAY` (relay and no-shuffle are separate UI controls, see 4d).
- `chkTypeLimit[5]` forbidden card types (Fusion/Synchro/Xyz/Pendulum/Link → `forbiddentypes`, `game.cpp:1353-1361`, `game.cpp:3114-3120`).
- Separate "Extra Rules" window `chkRules[13]` (strings 1132-1144: Sealed Duel, Booster Draft, Destiny Draw, Concentration Duel, Boss Duel, Battle City, Duelist Kingdom, Dimension Duel, Turbo Duel, Rule of the day, Command Duel, Virtual World, Action Duel; built `game.cpp:1255-1268`). These do NOT set duel flags — they inject hidden "rule cards" into the duel (`gframe/generic_duel.cpp:616-647`, e.g. `SEALED_DUEL → card 511005092`).
- "TCG rulings" checkbox = `DUEL_TCG_SEGOC_NONPUBLIC` (`game.cpp:1212`, `menu_handler.cpp:845-849`).

Last-used values persist in `system.conf` via `lastDuelParam` (default `0x2E800` = MR5) and `lastDuelForbidden` (`gframe/game_config.inl:22-24`, saved `game.cpp:2556-2558`).

### 4d. How the host's flags reach ocgcore

1. Host clicks Host → `DuelClient::ClientEvent` builds `CTOS_CreateGame`: `cscg.info.duel_flag_low = mainGame->duel_param & 0xffffffff; cscg.info.duel_flag_high = (mainGame->duel_param >> 32)` (`gframe/duelclient.cpp:236-237`); `DUEL_RELAY` and `DUEL_PSEUDO_SHUFFLE` are OR'd into the low word from their own UI toggles (:258-261); `forbiddentypes`, `extra_rules`, deck `sizes`, lflist hash, allowed-cards `rule` also ride in `HostInfo` (:228-263). `HostInfo` layout: `gframe/network.h:40-61` (`duel_flag_high` at :51, `duel_flag_low` at :57 — split for wire-format compat; legacy `duel_rule` byte is sent as 0, :235).
2. The hosting client's embedded server recombines: `uint64_t opt = (uint64_t)host_info.duel_flag_low | ((uint64_t)host_info.duel_flag_high << 32)` (`gframe/generic_duel.cpp:598`) and creates the duel: `mainGame->SetupDuel({ {seed...}, opt, team, team })` (:602).
3. `Game::SetupDuel` fills `OCG_DuelOptions` (`flags` is the `uint64_t` second member, `gframe/ocgapi_types.h:62-76`) and calls `OCG_CreateDuel` (`game.cpp:3922-3931`).
4. Core-side: `OCG_CreateDuel` → `duel` ctor → `field` ctor stores `core.duel_options = options.flags` (`/workspace/edo9300/ygopro-core/ocgapi.cpp:23-55`, `field.cpp:68`), queried everywhere via `field::is_flag` (`field.cpp:1249`). Card scripts can also read it (`Duel.GetFlag` etc.) and the client mirrors it in `dInfo.duel_params` for field layout (`Game::GetMasterRule`, `game.cpp:3211-3233`).

Single/puzzle mode bypasses the network: `SingleMode::SinglePlayThread` passes `duelOptions.duelFlags` straight to `SetupDuel` (`gframe/single_mode.cpp:61-93`).

### 4e. Can a data file / repo add a new preset?

**No.** The preset list is compiled in: `ReloadCBDuelRule` hard-codes 8 `addItem` calls (`game.cpp:3496-3507`) and the index→flags mapping is a compiled switch (`menu_handler.cpp:981-1015`). No code path reads presets from JSON/conf. What external data *can* do:
- **Rename** presets: repo `data_path/strings.conf` reloads system strings 1248/1258/1259/1260-1264 (`game.cpp:2687`; `LocaleStringHelper::SetMain` overwrites, `data_manager.cpp:246-259`; UI re-labeled via `ReloadElementsStrings` after repos finish, `game.cpp:2716-2719`) — cosmetic only.
- Every *flag combination* is reachable through the Custom Rule tab, and the last-used combination persists (`lastDuelParam`). A "GOAT-like but tweaked" historical format therefore needs manual checkbox setup (or a distributed `system.conf`), not a preset.
- Servers/room-list can host arbitrary flag combos: joining clients just receive `duel_flag_low/high` in `STOC_JoinGame` and display the matching preset name or the custom-rule breakdown (`duelclient.cpp:713-760`, `server_lobby.cpp:116-123`).

---

## 5. What an external repo can and cannot contribute (historical-format package)

### CAN (all confirmed in code)

| asset | mechanism |
|---|---|
| **card databases (.cdb)** | files directly in `data_path` (no subdirs, `game.cpp:2678`); override base DBs by same-id (last wins). Alt-format cards can use new codes with `alias` to the real card + custom `ot` (cf. `goat-entries.cdb` in BabelCDB: 191 "(GOAT)" entries, `ot=8`, alias→real code) |
| **banlists / lflists (.conf)** | `lflist_path` folder of `*.conf` (`game.cpp:2781-2785`, `deck_manager.cpp:88-96`) or a single `data_path/lflist.conf`. NOTE: `LoadLFListSingle(data_path + "lflist.conf") || LoadLFListFolder(lflist_path)` short-circuits — if `data_path/lflist.conf` exists, the lflist folder is **skipped** (`game.cpp:2782`). Format: `!ListName`, `#comment`, `code count`, optional `$whitelist` (whitelist mode — everything not listed is banned; parser `deck_manager.cpp:35-87`). Lists appear in host/deck-builder combos identified by content hash (`game.cpp:2465-2476`, sent as `HostInfo.lflist`, `duelclient.cpp:234`) |
| **card scripts (cN.lua + any .lua)** | `script_path` + subdirs 2 deep, prepended = highest priority (`game.cpp:2770-2776`); overrides official scripts by filename |
| **init.lua** | `script_path/init.lua` auto-runs at every duel creation after constant/utility (`game.cpp:2772-2774, 3934-3938`) — can monkey-patch utility.lua behavior for era-accurate rulings |
| **strings.conf** | `data_path/strings.conf`: `!system`/`!counter`/`!setname`/`!victory` additions and overrides (`game.cpp:2687`) — needed for new setcodes/counters used by the pack's cdb |
| **mappings.json** | `data_path/mappings.json` id remaps (`game.cpp:2688`, `data_manager.cpp:303-327`) |
| **card art / pics** | `pics_path` prepended to `pic_dirs` (`game.cpp:2777`). Only card art + cover lookup use `pic_dirs`/`cover_dirs` (`image_manager.cpp:624`); repo pics dirs feed `pic_dirs` only — field-spell backgrounds (`field_dirs`) and covers are *not* extended by repos (`game.cpp:3994-4002`) |
| **ocgcore binary** | `has_core` + `core_path`, hot-loaded when repos finish (`Game::LoadCoreFromRepos`, `game.cpp:1124-1145`) — a format pack *could* ship a legacy-behavior core, but it must match the client's core API (DLL builds only, `repo_manager.cpp:177-181`) |
| **puzzles** | set `repo_path` under `./puzzles/...` (as the shipped Puzzles repo does); the single-player browser lists `*.lua` under `./puzzles` (`game.cpp:788-791`) |
| **locale text** | separate repo with `is_language: true` + `language` (`game.cpp:2689-2707`) |

A repo can also be a plain local folder (`not_git_repo: true` + `repo_path`) — useful for development or offline packages (`repo_manager.cpp:218-227`).

### CANNOT

- **Duel-rule presets** — compiled in (see 4e). A pack can ship an lflist + cdb + scripts, but the host must pick GOAT/MR-N or hand-build the flag set in Custom Rule.
- **Deck-size / starting-hand defaults per format** — presets' deck sizes are compiled (`menu_handler.cpp:975-978`); hosts can edit them manually per game (Deck settings tab, `game.cpp:1283-1316`).
- **servers / urls lists** — read only from local `./config/configs.json` + `user_configs.json` (`game.cpp:2788-2818`, `data_handler.cpp:54-95`), never from a cloned repo's own configs.json.
- **UI textures, skins, sounds, fonts** — those load from `./textures`, `./skin`, `./sound` etc.; no repo path feeds them.
- **Field-spell backgrounds & sleeves/covers** — `field_dirs`/`cover_dirs` only contain `./expansions/pics/...`, `archives`, `./pics/...` (`game.cpp:3997-4002`). Workaround: ship a zip in `./expansions/` (archives are searched) — but repos can't place files into `./expansions/` either; that would be a manual install step.
- **system.conf settings** (e.g. defaulting `lastDuelParam` to a historical flag set) — user-local file.
- **Extra deck-check logic** — deck legality (`DuelAllowedCards` OCG/TCG/Prerelease/Anything, `deck_manager.h:32-38`, checks at `deck_manager.cpp:157-203`) is compiled; a pack's unofficial-`ot` cards require the host to pick "Anything goes" (`rule` index 4) unless the cards carry official ot bits.

### Practical packaging recipe (for the historical-format project)

One git repo, default layout, added to `user_configs.json`:
```
<repo>/
  *.cdb            <- data_path "" (repo root): era-frozen card text/stats via alt codes, or overrides
  lflists/*.conf   <- one banlist per season (use $whitelist for a hard-legal-pool cut)
  script/          <- overridden cN.lua for era rulings; init.lua for global patches
  pics/            <- optional alt art
```
Caveats: cdbs must sit *directly* in `data_path` (depth 0); avoid `data_path/lflist.conf` if you also use `lflists/`; card-code collisions with the official repo will be won by whichever repo is listed later in the merged config order (user_configs repos parse first ⇒ official DeltaBagooska overrides yours on collision — prefer distinct codes+alias, as ProjectIgnis's own `goat-entries.cdb` does).

---

## CONFIRMED vs ASSUMPTIONS

### CONFIRMED (verified in source, citations above)
- cdb scan paths, depth limits, alphabetical order, and last-loaded-wins override semantics (`data_handler.cpp:28-52`, `data_manager.cpp:96-177`).
- Full repo-entry key set and defaults (`repo_manager.cpp:147-186`, `repo_manager.h:30-44`), `should_read`/`should_update`/`not_git_repo` semantics, path sanitization.
- Shipped configs.json contents (3 repos + urls + servers).
- Script request name `c%u.lua` from core (`interpreter.cpp:287`), alias-within-10 rule (`interpreter.cpp:145-148`), client search order (`game.cpp:3868-3887, 3984-3993, 2770-2776`), archive (`script/` in expansion zips) support, init.lua hooks.
- The 8 compiled presets + dynamic 9th "Custom Rule" item, exact flag macros, 32 custom-rule checkbox mapping, 5 forbidden-type checkboxes, 13 extra-rule cards.
- Flag transport: `duel_param` (uint64) → `HostInfo.duel_flag_low/high` → recombined in `generic_duel.cpp:598` → `OCG_DuelOptions.flags` → `field::core.duel_options`.
- lflist file format incl. `$whitelist`, hash-based identification, repo lflist loading incl. the `||` short-circuit.
- Repo-supplied strings.conf/mappings.json/pics/core loading; language repos; puzzles-via-repo_path.

### ASSUMPTIONS / UNCERTAIN
- **Repo ready order under slow networks**: parse order is config order because `GetReadyRepos` stops at the first unready repo (`repo_manager.cpp:117-140`); I did not run the client to observe this, but the code path is unambiguous. Confidence: high.
- **DeltaBagooska repo layout** (cdbs at root, scripts in `script/`, cores in `bin/`): inferred from its configs.json entry + BabelCDB naming; the repo itself was not cloned here. Confidence: likely.
- **Intended use of `goat-entries.cdb`** (alt codes 504700000+, `ot=8` = SCOPE_ILLEGAL, alias→real card): consistent with "GOAT-behavior variant cards selectable in deck builder under Anything-goes / via GOAT whitelist", but I did not verify how the GOAT.lflist.conf references them or how ChampionshipSeries servers use them. Worth checking `GOAT.lflist.conf` contents and matching scripts in `cardscripts` before designing our own alt-code scheme.
- The exact behavior of `WindBot` with repo databases beyond registration (`windbot.cpp:140-147`) was not traced further.
- `overwrites/` directory in the client repo (build-system overrides) not examined; assumed irrelevant to data loading.
