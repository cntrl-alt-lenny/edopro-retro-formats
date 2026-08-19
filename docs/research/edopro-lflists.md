> Point-in-time research note (2026-08-19), verified against the pinned revisions in data/sources.json.

# EDOPro Forbidden/Limited list (lflist) handling — research note

Sources: `/home/user/edopro` (edo9300/edopro client, gframe/), `/workspace/projectignis/lflists`,
`/workspace/projectignis/distribution`. All line numbers refer to those working trees as of 2026-08-19.

Everything below is CONFIRMED from source unless explicitly marked ASSUMPTION/UNCERTAIN
(collected at the end).

---

## 1. Data model

`gframe/deck_manager.h:15-31`:

```cpp
using banlist_content_t = std::unordered_map<uint32_t, int>;   // code -> allowed count

struct LFList {
    uint32_t hash;
    std::wstring listName;
    banlist_content_t content;
    bool whitelist;
    auto GetLimitationIterator(const CardDataC* pcard) const {
        auto flit = content.find(pcard->code);
        if(flit == content.end() && pcard->alias) {
            if(!whitelist || pcard->IsInArtworkOffsetRange())
                flit = content.find(pcard->alias);
        }
        return flit;
    }
};
```

All loaded lists live in `DeckManager::_lfList` (`std::vector<LFList>`, deck_manager.h:49).
A list is identified everywhere (config, network, UI item data) by its **content hash**, not
by name or index.

---

## 2. Discovery: which files are scanned, and in what order

### 2.1 Startup scan — `DeckManager::LoadLFList()` (deck_manager.cpp:97-108)

Called once at startup from `DataHandler` constructor (data_handler.cpp:164), after databases
are loaded. Fixed order:

1. `./expansions/lflist.conf` — single file (deck_manager.cpp:98)
2. `./lflist.conf` — single file in the game root (deck_manager.cpp:99)
3. `./lflists/` — folder scan (deck_manager.cpp:100)
4. A built-in "N/A" list is appended: `listName = L"N/A"`, `hash = 0`, empty content,
   `whitelist = false` (deck_manager.cpp:101-107). Its index is remembered in
   `null_lflist_index`. Its display name is later re-localized via sysstring 1442
   (game.cpp:3550-3551; distribution/config/strings.conf:510 `!system 1442 N/A`).

### 2.2 Folder scan semantics — `LoadLFListFolder` (deck_manager.cpp:88-96)

- `Utils::FindFiles(path, { EPRO_TEXT("conf") })` — every file whose **extension is `conf`**
  (so `X.lflist.conf`, `X.conf`, anything `*.conf`), non-recursive (default
  `subdirectorylayers` = 0 in utils; see utils.cpp:560-577).
- Results are sorted **case-insensitively alphabetical** (`std::sort(..., CompareIgnoreCase)`,
  utils.cpp:575). That is why Project Ignis names its TCG list `0TCG.lflist.conf` — the `0`
  prefix sorts it first, making it `_lfList[0]`, the fallback/default list (see §6.3, §7).
- Quirk: `loaded = LoadLFListSingle(...)` inside the loop is overwritten every iteration, so
  the function's return value reflects only the **last** file in the folder
  (deck_manager.cpp:92-94).

### 2.3 Repos contribute lflists — per-repo, appended as repos finish cloning

Repo definitions come from `./config/configs.json` + `./config/user_configs.json`
(`gitManager->LoadRepositoriesFromJson`, data_handler.cpp:157-158; **user_configs is loaded
first**). `GitRepo` fields (repo_manager.h:30-38): `lflist_path` defaults to `"lflists"`;
`GitRepo::Sanitize()` resolves it to `<repo_path>/<lflist_path>/`, or `<repo_path>/lflists/`
when empty (repo_manager.cpp:51-54).

Every frame the main loop calls `ParseGithubRepositories(gRepoManager->GetReadyRepos())`
(game.cpp:2029). `GetReadyRepos()` returns repos **in configured order**, stopping at the
first not-yet-cloned one (repo_manager.cpp:117-140), so repo lists load in configs.json order,
but only as clones complete (i.e. across multiple frames on first install).
For each non-language repo, `Game::UpdateRepoInfo` (game.cpp:2770-2786) does:

```cpp
if(gdeckManager->LoadLFListSingle(data_path + EPRO_TEXT("lflist.conf"))
   || gdeckManager->LoadLFListFolder(lflist_path)) {
    gdeckManager->RefreshLFList();   // rotate "N/A" back to the end (deck_manager.cpp:110-116)
    RefreshLFLists();                // rebuild the three combo boxes (game.cpp:2465-2484)
}
```

Note the short-circuit: if the repo has `<data_path>/lflist.conf`, its lflists **folder is not
scanned at all**.

Stock Project Ignis setup (distribution/config/configs.json): the
`https://github.com/ProjectIgnis/LFLists` repo is cloned to `./repositories/lflists` with
`"lflist_path": "."`, so every `*.conf` at that repo's root is loaded
(currently: `0TCG`, `GOAT`, `OCG`, `Rush-Prerelease`, `Rush`, `Speed`, `Traditional`, `World`
— /workspace/projectignis/lflists). The distribution ships an **empty** `./lflists/` folder
and no `./lflist.conf` / `./expansions/lflist.conf`, so on a stock install all real lists come
from the repo and are appended after the (initially lone) N/A entry, which `RefreshLFList()`
then rotates to the end.

**Resulting UI order** (top to bottom in every banlist combobox): `./expansions/lflist.conf`
lists, then `./lflist.conf` lists, then `./lflists/*.conf` (alphabetical), then each repo's
lists in repo-configuration order (each repo: `lflist.conf` first or folder alphabetical),
with **"N/A" always forced last**. On stock Ignis: `0TCG, GOAT, OCG, Rush-Prerelease, Rush,
Speed, Traditional, World, N/A`.

There is no file watching; lists load once (startup + once per repo clone/update completion).

---

## 3. Parser semantics — `LoadLFListSingle` (deck_manager.cpp:35-87)

Line-by-line, after stripping a trailing `\r` (deck_manager.cpp:45-49):

| Line | Behavior |
|---|---|
| empty or starts with `#` | skipped entirely — comments (deck_manager.cpp:50-51). The conventional first line `#[2026.05 TCG]` is *only* a comment. |
| starts with `!` | Starts a **new list** whose name is the entire rest of the line (UTF-8 decoded). If a list was already in progress (hash != 0), it is pushed first — one file can hold several lists. Resets: `content.clear()`, `hash = 0x7dfcee6a` (seed), `whitelist = false` (deck_manager.cpp:52-61). |
| starts with `$whitelist` (prefix match) | sets `whitelist = true` for the **current** section (deck_manager.cpp:36, 62-65). Must appear after the section's `!` header, since `!` resets the flag. This is the only `$` token; there is no `$blacklist` handling. |
| anything before the first `!` header | ignored (`if(!lflist.hash) continue;`, deck_manager.cpp:66-67) |
| card line | `code<SPACE>count[junk]` — see below (deck_manager.cpp:68-82) |

Card-line parsing details:

- Split at the **first space**: `p = str.find(' ')`. No space → line ignored.
- `code = stoul(str.substr(0, p))`; `code == 0` → ignored; parse failure → whole line silently
  ignored (`catch(...)`).
- Count field: characters from `p` up to the first char not in `-0123456789` (so an optional
  minus sign and digits), parsed with `stol`. Trailing junk (`--Card Name` etc.) is ignored,
  which is what makes the conventional `12345678 0 --Name` format work.
- `lflist.content[code] = count;` — **duplicate codes: last occurrence wins** in the map, but
  *every* occurrence is folded into the hash (see §4), so a file with duplicated lines hashes
  differently from one without.
- **Any integer count parses.** There is no validation of 0..3:
  - `0` → forbidden; `1` → limited; `2` → semi-limited; `3` → unlimited-but-listed.
  - Negative counts (e.g. `-1`) are accepted by the parser and behave as forbidden at
    validation time (any deck count `dc >= 1 > it->second`), and draw the "forbidden" icon
    (drawing.cpp:1205-1208 treats `-1` and `0` identically).
  - Counts > 3 are pointless: the global 3-copy cap fires first (deck_manager.cpp:194-196).
- Return value: `true` iff at least one `!` header was seen. A trailing in-progress list is
  pushed at EOF (deck_manager.cpp:84-85).

**"N" handling**: there is no `N` token in this parser. The only "N" is the internally
generated "N/A" no-limit pseudo-list (hash 0, §2.1); nothing in a `.conf` file produces it.

Whitelist file convention (per actual Ignis files, e.g.
/workspace/projectignis/lflists/GOAT.lflist.conf:1-25): `$whitelist` on line 3, then *every
legal card* is listed with its count (0 entries additionally pin forbidden cards, including
alt-art/pre-errata codes explicitly).

---

## 4. The hash

Computed incrementally per card line (deck_manager.cpp:57, 80):

```cpp
lflist.hash = 0x7dfcee6a;                       // seed, set at the '!' header
...
lflist.hash = lflist.hash
    ^ ((code << 18) | (code >> 14))
    ^ ((code << (27 + count)) | (code >> (5 - count)));
```

Properties (all follow from the code):
- Pure XOR fold → **order-independent**: shuffling lines does not change the hash.
- The list **name and the `$whitelist` flag are NOT hashed** — only (code, count) pairs.
  Two lists with identical entries but different names/whitelist flags collide.
- A duplicated identical line XORs itself out of the hash.
- The empty "N/A" list has hash **0** (assigned literally, deck_manager.cpp:103), not the seed.
- This is the same algorithm used by classic ygopro forks, so hashes are interoperable across
  clients that share the same file content. (ASSUMPTION for other forks; the algorithm itself
  is confirmed here.)
- Shift amounts stay in range for counts −27..4; standard counts 0-3 give shifts
  27..30 / 5..2.

Lookup by hash: `DeckManager::GetLFList(uint32_t)` does a linear find, **first match wins**
(deck_manager.cpp:130-133); `GetLFListName` falls back to `unknown_string` ("???") when the
hash is unknown (deck_manager.cpp:134-139).

---

## 5. Selection and use in the UI

Three combo boxes are (re)filled by `Game::RefreshLFLists()` (game.cpp:2465-2484), in
`_lfList` vector order, with the **hash stored as per-item data**:

- `cbDBLFList` — deck-builder banlist (label "Forbidden List:", sysstring 1226);
- `cbHostLFList` — host-a-game dialog (game.cpp:1179);
- `cbFilterBanlist` — room-list filter (game.cpp:932; prepended `[...]` "any" entry).

The last-used list is remembered as `gGameConfig->lastlflist` (a **hash**, default 0 = N/A;
game_config.inl:20) and re-selected on refresh (game.cpp:2477-2480); it is saved when leaving
the deck builder (deck_con.cpp:126) and when hosting (duelclient.cpp:234).

Deck builder consumption (`DeckBuilder::filterList`, selected by combobox index into
`_lfList` — deck_con.cpp:73, 512):

- Thumbnail limit icons: `Game::DrawThumb` (drawing.cpp:1182-1221) resolves the card through
  `GetLimitationIterator`; count −1 (i.e. whitelist-and-absent) or 0 → forbidden icon,
  1 → limited, 2 → semi-limited, otherwise a Legend icon if `SCOPE_LEGEND`.
- Search results: with a whitelist active, cards **not on the list are filtered out of search
  results** unless the limit filter is set to "(All)" (deck_con.cpp:1235-1302, esp. 1238-1240
  and 1301-1302); also, non-official cards (anime etc.) become searchable under a whitelist
  without the "Anime" checkbox (deck_con.cpp:1173). The limit dropdown gets a reduced item set
  for whitelists ("Allowed" instead of "(All)", no scope filters — game.cpp:3439-3460).
- Add-card gate: `DeckBuilder::check_limit` (deck_con.cpp:1646-1671) — baseline
  `limit = whitelist ? 0 : 3`, overridden by the list entry; counts existing copies matching
  the **alias root** (`pcard->code == limitcode || pcard->alias == limitcode`) and takes the
  minimum limit across entries found by each copy's code-then-alias.

When joining a host, the client sets `deckBuilder.filterList` from the host's hash so the
in-lobby deck editor shows the right icons; unknown hash → falls back to `_lfList[0]`
(duelclient.cpp:874-879).

---

## 6. Enforcement at deck-validation time

### 6.1 Where validation happens

Deck legality is checked **server-side only** — in `GenericDuel::PlayerReady`
(generic_duel.cpp:366-391), i.e. inside the embedded `NetServer` that the *hosting client*
runs for LAN games (the same code a headless EDOPro server would run). Order:

1. `DeckManager::CheckDeckSize(dueler.pdeck, host_info.sizes)` (generic_duel.cpp:373;
   impl deck_manager.cpp:238-258) — pure min/max on main(-skills)/extra/side.
2. If sizes pass and `!host_info.no_check_deck_content`:
   - unknown cards recorded at deck-load time → `DeckError::UNKNOWNCARD`
     (generic_duel.cpp:375-377; error code from `LoadDeckFromBuffer`, generic_duel.cpp:423);
   - otherwise `DeckManager::CheckDeckContent(pdeck, gdeckManager->GetLFList(host_info.lflist),
     (DuelAllowedCards)host_info.rule, host_info.forbiddentypes, rituals_in_extra)`
     (generic_duel.cpp:378-381).
3. Failure → player is forced not-ready and receives `STOC_ERROR_MSG` with a typed
   `DeckError` (`LFLIST`, `CARDCOUNT`, `OCGONLY`, `FORBTYPE`, ... network.h:108-135)
   carrying the offending card code (generic_duel.cpp:384-390).

There is **no client-side pre-check**; the client only draws icons (§5).

### 6.2 `CheckDeckContent` / `CheckCards` semantics (deck_manager.cpp:157-237)

Per deck section (main, then extra, then side — one shared `ccount` map across all three):

```cpp
uint32_t code = cit->alias ? cit->alias : cit->code;   // count under the ALIAS ROOT
ccount[code]++;
int dc = ccount[code];
if (dc > 3) return CARDCOUNT;                          // global 3-copy cap, alias-merged
auto it = curlist->GetLimitationIterator(cit);         // lookup: own code, then alias
auto is_end = it == curlist->content.end();
if ((!is_end && dc > it->second) || (curlist->whitelist && is_end))
    return LFLIST;
```

(deck_manager.cpp:192-200)

Alias interaction, precisely:

- **Counting** always merges all variants under `alias ? alias : code` — 2× alt-art +
  2× base = 4 copies → `CARDCOUNT`.
- **Limit lookup** (`GetLimitationIterator`, deck_manager.h:23-30) tries the card's *own*
  code first, then its alias — so a list entry for either the printed code or the root code
  works on a blacklist. If both exist, the card's own-code entry wins for that copy (the
  Ignis TCG list actually lists both Apollousa artworks separately —
  /workspace/projectignis/lflists/0TCG.lflist.conf:6-7).
- **Whitelist restriction**: on a whitelist the alias fallback only happens when
  `IsInArtworkOffsetRange()` — |code − alias| < 10 (`CARD_ARTWORK_VERSIONS_OFFSET`,
  data_manager.h:74-85). So alt-artworks inherit the base card's whitelist entry, but
  *functional* aliases (pre-errata `511xxxxxx` cards, retrains aliased to a faraway code) do
  **not** — they must be whitelisted (or 0-listed) under their own code. This is why
  GOAT.lflist.conf explicitly lists e.g. `511000819 0` (pre-errata CED) and both Harpie's
  Feather Duster codes.
- On a plain (black)list the alias fallback is unconditional, so pre-errata versions inherit
  the erratad card's limit status, and vice versa, in addition to sharing the count pool.

Whitelist + absent card → `LFLIST` error (the `(curlist->whitelist && is_end)` branch):
**whitelists forbid everything not explicitly listed**; listed entries carry their own counts
(0 entries are then redundant for legality but pin the forbidden icon/search filter and change
the hash).

`CheckDeckContent` also enforces, independent of the lflist: `forbiddentypes` bitmask
(FORBTYPE), max 1 Legend monster (main+extra) / 1 Legend spell / 1 Legend trap
(`SCOPE_LEGEND` in `ot` — deck_manager.cpp:148-156, 208-213), max 1 Skill, and
main/extra-deck type placement (deck_manager.cpp:219-236).

`lflist == nullptr` (hash not found on the checking side) skips *all* per-card checks
including the 3-copy cap (deck_manager.cpp:216-218). The N/A list (hash 0) is **not** null —
it is an empty non-whitelist list, so with N/A the per-card loop still runs and enforces the
3-copy cap and card-scope (`DuelAllowedCards`) checks, just no banlist limits.

### 6.3 Hash-miss fallback when hosting

When the embedded server receives `CTOS_CreateGame`, it verifies the requested hash exists in
its own `_lfList`; an unknown hash is silently replaced with `_lfList[0].hash` — the first
loaded list, on stock installs `0TCG` (netserver.cpp:367-375). N/A's hash 0 is a legal value
and passes this check.

---

## 7. Networking: how the banlist travels

- The banlist is communicated **only as the 32-bit hash** inside `HostInfo`
  (`uint32_t lflist` — network.h:40-61), which rides in `CTOS_CreateGame`
  (duelclient.cpp:223-267, field set at :234 from the host combobox item data) and comes back
  to every joiner in the `STOC_JoinGame` packet (read at duelclient.cpp:733 for the
  room-rules text, and :874-879 for the deck-builder filter). List *contents are never
  transmitted*; both sides must own a list file with identical entries for the hash to
  resolve. A joiner without the file just sees "???" in the rules summary and gets
  `_lfList[0]` icons, but the host's server still enforces its own copy.
- LAN room broadcast (`HostPacket.host.lflist`) is shown in the LAN server list via
  `GetLFListName` (duelclient.cpp:4603-4610).
- Online lobby (separate server software, e.g. Multirole — not in this repo): the room-list
  JSON carries `banlist_hash`, parsed into `room.info.lflist` (server_lobby.cpp:241), shown by
  matching against local `_lfList` (server_lobby.cpp:95-102) and filterable
  (server_lobby.cpp:86-90). Hosting on such servers sends the exact same `CTOS_CreateGame`
  packet over the connection (duelclient.cpp:214-267 — same code path as LAN).
- Enforcement is wherever the server runs: the hosting client's embedded NetServer for LAN,
  the remote server for online play (ASSUMPTION for Multirole's internals; the client-side
  protocol is confirmed).

## 8. Single player / hand test / puzzles

`SingleMode` (puzzles, hand-test — deck_con.cpp:176-208) never touches lflists: no
`CheckDeckContent` call exists outside generic_duel.cpp (grep over gframe). Banlists are
irrelevant offline; the deck builder merely displays the selected list.

## 9. Banlist selection does NOT imply duel rule flags — verified

- `HostInfo.lflist` and `duel_flag_low/high` are populated independently
  (duelclient.cpp:234-237): flags come solely from `mainGame->duel_param`, which is set by the
  Duel Rule combobox / custom-rule checkboxes (`Game::UpdateDuelParam` game.cpp:3097+;
  menu_handler.cpp:915-935, 981-1010 — e.g. selecting the "GOAT" *duel rule* sets
  `DUEL_MODE_GOAT` and MR1 forbidden types, and deck sizes/start-hand defaults).
- There is **no event handler at all** for `COMBOBOX_HOST_LFLIST` (grep: the ID appears only
  in menu_handler.h:39 and game.cpp:1179) — changing the banlist changes nothing else.
- The room list derives its "GOAT"/"Rush"/"Speed" column from `duel_flag`, not from the
  banlist (server_lobby.cpp:115-125).
- Consequence for historical formats: choosing e.g. the GOAT *banlist* does not give GOAT
  *rules*; a format needs banlist + duel-rule flags + allowed-cards scope
  (`HostInfo.rule` → `DuelAllowedCards`, deck_manager.h:32-38 / deck_manager.cpp:163-187)
  + deck sizes configured separately. The lflist file cannot express any of the latter.

## 10. Practical implications for recreating historical formats

1. Drop a `MyFormat.lflist.conf` into `./lflists/` (or ship a git repo with
   `"lflist_path"` pointing at a folder of `.conf` files, registered in
   `config/user_configs.json`); it appears in all three combo boxes after restart.
   File name is irrelevant except for sort order; the display name is the `!` line.
2. For eras where card pools must be closed (pre-errata texts, no later cards), use
   `$whitelist` and enumerate every legal code — remembering that only ±10 alt-arts inherit
   entries via alias; pre-errata (`511…`) codes and cross-numbered reprints must be listed
   explicitly, exactly as GOAT.lflist.conf does.
3. Both players need the identical file for the hash to resolve on the non-hosting side
   (cosmetic) and on whatever machine runs the server (enforcement).
4. Count semantics available per card: 0 (or negative) = forbidden, 1, 2, 3; anything not
   listed = 3 on a blacklist, forbidden on a whitelist.
5. Banlist choice never sets rules: pair the list with the right Duel Rule
   (MR1-5/Speed/Rush/GOAT presets or custom flag set) and allowed-scope (OCG/TCG/either/
   prerelease/any) when hosting.

---

## CONFIRMED vs ASSUMPTIONS

CONFIRMED (all statements above with file:line citations), notably:
- Scan order `./expansions/lflist.conf` → `./lflist.conf` → `./lflists/*.conf` (alphabetical,
  case-insensitive) → per-repo (`<data>/lflist.conf` else `<repo>/lflists/` or configured
  `lflist_path`) → N/A forced last. deck_manager.cpp:97-108, utils.cpp:575, game.cpp:2782,
  repo_manager.cpp:51-54.
- Parser: `#` comment, `!` header/new-list, `$whitelist` prefix token, `code count` lines,
  any integer count accepted, duplicates overwrite content but double-hash;
  hash = seed 0x7dfcee6a XOR-folded per entry; name/whitelist flag not hashed.
  deck_manager.cpp:35-87.
- Enforcement server-side in `GenericDuel::PlayerReady` via `CheckDeckContent`; counting keyed
  on alias root; lookup own-code-then-alias; whitelist alias fallback restricted to |Δ|<10;
  whitelist bans unlisted cards; `no_check_deck_content` host flag skips it entirely.
  deck_manager.cpp:157-237, deck_manager.h:23-30, generic_duel.cpp:366-391.
- Network: hash-only in `HostInfo.lflist`; unknown hash at the server → `_lfList[0]`;
  unknown hash at a joiner → "???" + `_lfList[0]` icons. network.h:41, netserver.cpp:367-375,
  duelclient.cpp:733, 874-879.
- No duel-rule coupling to banlist selection. duelclient.cpp:234-237, menu_handler.h:39 (no
  handler), menu_handler.cpp:964-1010.
- No banlist checks in single/puzzle/hand-test mode (no other `CheckDeckContent` callers).

ASSUMPTIONS / UNCERTAIN:
- The hash algorithm matching other ygopro forks (interop) — consistent with the shared
  lineage of the code, but other forks were not read here.
- Remote (Multirole) servers enforcing the list the same way — their code is outside this
  repo; only the client-side protocol and the identical embedded-server behavior are
  confirmed.
- Repo lflist load *timing* (order among repos when clones finish out of order): GetReadyRepos
  preserves configured order and blocks on the first unfinished repo, so configured order is
  preserved within one run; first-install UI order can still shift between frames as repos
  complete (behavioral inference from repo_manager.cpp:117-140 + game.cpp:2029, not observed
  at runtime).
