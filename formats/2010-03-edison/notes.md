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
- **Errata — partial, and computed.** Edison substitutes historical implementations
  for cards its snapshot date requires, derived entirely from each record's evidence:
  **no hand-written Edison errata list exists.** Sangan, Rescue Cat, Sinister Serpent,
  Chaos Emperor Dragon, Dark Magician of Chaos, Imperial Order, Ring of Destruction,
  Makyura the Destructor and Witch of the Black Forest are among the cards that fall
  out automatically. Run `python -m retroformats report -v` for the current list.

  Two evidence routes reach 2010-04-24:

  1. **Dated functional errata after 2010** — the modern text's first printing
     post-dates the snapshot, so the pre-errata version applies.
  2. **The period search-verification ruling** — a Deck search that failed to find
     was verified by the opponent, and Konami's own *Machina Mayhem* rulings document
     (compiled 2010-04-06, eighteen days before the snapshot) still says so. The old
     state is attested through 2011-02-02 and the modern policy only from 2019-04-03,
     so the interval stays open as bounded chronology — but 2010-04-24 sits
     determinately inside the old era. Cards whose only implementation-relevant
     difference is that procedure therefore use their period implementation here as
     well as in GOAT.

  Where chronology cannot place a change relative to the snapshot, this format's
  documented `errata_overrides.unresolved_policy` keeps the **modern** implementation
  rather than assert unproven period behaviour, and the validator names every card it
  was applied to (`format.erratum-unresolved-defaulted`). Where a period behaviour is
  known to differ but no implementation exists, the record acknowledges the gap and
  the divergence is counted by `report`. Both sets shrink as research continues.
- **Chronology.** Format Library names the neighbours "Lightsworn" (previous) and
  "Frog" (next); left null until those formats exist here.

## The event versus the format

Two related but distinct things bear the name "Edison":

1. **The historical event** - the 75th Shonen Jump Championship, Edison NJ,
   April 24-25, 2010. Konami's own pre-event FAQ (archived 2010-04-11, source
   `sjc-edison-2010-faq`) defines what was legal *there*: boosters through
   Absolute Powerforce and Duelist Pack: Kaiba ("Legal for play starting
   4/20/2010"), Machina Mayhem, Shonen Jump promos **up until Hundred Eyes
   Dragon**, GX manga promos through Angel O7, video-game promos through the
   Reverse of Arcadia trio, and an explicit list of Duel Terminal exclusives
   that were NOT legal.
2. **The retrospective community format** - what EdisonFormat.com and the
   community pools define and play today. It matches the event's pool on
   everything except one deliberate divergence: the community's promo cutoff is
   Cyber Eltanin (JUMP-EN038), excluding Hundred Eyes Dragon (JUMP-EN039)
   even though the event's FAQ permitted it.

Our pool declares `legality_basis: community-retrospective` and preserves the
community convention; the divergence is documented (with the period evidence)
on the Hundred Eyes Dragon exclusion entry. A future historical-event pool
could reuse every shared record and differ only there.

Period policy findings that ground the pool's other decisions (see
docs/releases.md "Availability versus legality policy"): Duel Terminal
machine exclusives were illegal in sanctioned play per Konami's own 2009-2010
policy (not just community convention); Europe-only releases counted as legal
in North America (UDE's worldwide-simultaneity clause; the 2009 US Nationals
FAQ explicitly legalising the GX Tag Force 3 promos); and the TSHD Sneak Peek
actually ran May 1-2 (NA) / April 30-May 2 (EU) per archived official pages -
not the May 8-9 weekend earlier assumed.

## Playing it (current honesty level)

`dist/lflists/2010-03-edison.lflist.conf` is now a full `$whitelist`: it enforces
the March 2010 F/L list, rejects every non-period card, AND substitutes the
historical implementation of every card whose evidence places its change after the
snapshot. Host with Duel Rule preset **Master Rule 1** and forbidden types
Xyz/Pendulum/Link (the preset sets this), 40–60/0–15/0–15 decks, and allowed cards
**"Anything goes"** — the historical card versions carry `ot=8` and would otherwise
be rejected as unofficial, exactly as GOAT is hosted.

Honest bounds on accuracy: the rule profile is still plain `DUEL_MODE_MR1` (the
TCG-variant flag question is open, roadmap item 5), records whose chronology is
unresolved fall back to modern implementations, and the acknowledged divergences
are behaviours nothing available reproduces. All three are enumerable rather than
assumed — `python -m retroformats report -v` lists them.
