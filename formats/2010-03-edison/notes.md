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
- **Pool `pool-edison-2010` — verified (3,673 cards).** Materialised from
  `data/releases/` (everything with a TCG release event in any territory on or
  before 2010-05-10), with five sourced product exclusions (The Shining Darkness's
  Europe-first street date, its Sneak Peek card, Duel Terminal 1, the May 2010
  JUMP subscription bonus, the Make-A-Wish one-of-one) and three sourced promo
  boundary resolutions (Genesis Dragon / Orichalcos Shunoros in, Hundred Eyes
  Dragon out). Europe-only Retro Pack and GX Tag Force 3 promos are legal with no
  special-casing — they fall out of all-TCG territory scoping (e.g. Gallis the
  Star Beast). Cross-checked against YGOPRODeck's Edison tag (every reference card
  present; our 15 extras are confirmed pre-cutoff printings their tag wrongly
  omits) and the termitaklk community whitelist. One documented deliberate
  deviation: Royal Knight of the Ice Barrier (Duel Terminal-only) is excluded
  where the references include it inconsistently. Regression tests lock the
  cardinality and sixteen edge cases.
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

`dist/lflists/2010-03-edison.lflist.conf` is now a full `$whitelist`: it enforces
the March 2010 F/L list AND rejects every non-period card. Pre-errata card
behaviour is still pending (the errata corpus is undated), so cards errata'd
after 2010 currently use modern implementations. Host with Duel Rule preset **Master Rule 1** and forbidden types
Xyz/Pendulum/Link (the preset sets this), 40–60/0–15/0–15 decks.
