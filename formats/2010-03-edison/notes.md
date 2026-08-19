# Edison Format (2010-03-edison)

The TCG format named for the 75th Shonen Jump Championship in Edison, New Jersey
(April 24–25, 2010): the era of the March 1, 2010 Forbidden/Limited list, ending
May 10, 2010 — the day before The Shining Darkness's North American release
(per EdisonFormat.com; URLs in `data/sources.json` and `format.json`).

Edison is the project's second fixture because it exercises everything GOAT does not:
a banlist built from published sources rather than an existing implementation, a
rule-based card pool (release cutoff), Master Rule 1-era behaviour with Synchros, and
a large functional-errata surface (many 2010 staples were errata'd later).

## Data status

- **Banlist `tcg-2010-03` — complete.** Transcribed from Yugipedia's
  "March 2010 Lists (TCG)" wikitext (which cites Konami's original list via the
  Internet Archive) by `retroformats/importers/yugipedia_banlist.py`; 43 forbidden /
  70 limited / 19 semi-limited; independently cross-checked against Format Library's
  `/api/banlists/march-2010?category=TCG` — memberships matched exactly.
  (Format Library's "previous status" markers disagreed on 3 cards; adjudicated
  against Yugipedia's September 2009 page — recorded in docs/data-sources.md.)
- **Pool `pool-edison-2010` — stub.** Defined as "everything TCG-released through
  2010-05-10" with sourced special cases (Europe-only RP01/GX06 promos legal, promo
  cutoffs Dark End Dragon / Cyber Eltanin / Elemental Hero Absolute Zero, DPCT's
  Starlight Road legal despite its omission from EdisonFormat.com's set table).
  Cannot be materialised until `data/releases/` covers 2002–2010, so the generated
  lflist is currently a **blacklist only** — it does not yet reject post-Edison cards.
- **Rules `rules-tcg-mr1-edison` — partial.** EdisonFormat.com states the era rules
  are the "TCG 2008 Rules Change (the equivalent of Master Rules)" and catalogues 13
  differences vs modern play. The profile currently uses the plain `DUEL_MODE_MR1`
  composite; whether TCG-variant flags (fast-effect ignition, TCG SEGOC, 6-step
  damage step — all used by the GOAT composite) should be added is an open research
  question tracked in the profile's `known_gaps`.
- **Errata — missing.** No overrides apply yet because the errata corpus is undated;
  cards like Sangan played pre-errata in 2010 but the generated blacklist currently
  points at modern implementations. Dating the corpus (roadmap item 1) fixes this
  automatically via computed applicability.
- **Chronology.** Format Library names the neighbours "Lightsworn" (previous) and
  "Frog" (next); left null until those formats exist here.

## Playing it (current honesty level)

`dist/lflists/2010-03-edison.lflist.conf` enforces the March 2010 F/L list only.
Players must restrict themselves to period cards manually until the pool
materialises. Host with Duel Rule preset **Master Rule 1** and forbidden types
Xyz/Pendulum/Link (the preset sets this), 40–60/0–15/0–15 decks.
