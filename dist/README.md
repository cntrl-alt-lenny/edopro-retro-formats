# dist/ — generated EDOPro assets

Everything in this directory is **generated** from the canonical data in `data/` and
`formats/` by `python -m retroformats build`. Do not edit by hand; CI rejects drift
(`build --check`).

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

(`dist/databases` and `dist/scripts` are empty today — historical card versions are
currently reused from Project Ignis's own repositories, which ship with EDOPro.)

## Host settings are NOT in the lflist

EDOPro cannot read duel rules from a banlist file, so the host must select them (see
each format's `formats/<id>/notes.md`):

| format | banlist | Duel Rule preset | allowed cards |
|---|---|---|---|
| `Retro 2005-04-goat` | whitelist (pool-enforcing) | GOAT | Anything goes (pre-errata cards are `ot=8`) |
| `Retro 2010-03-edison` | whitelist (pool-enforcing) | Master Rule 1 | Anything goes (historical cards are `ot=8`) |
