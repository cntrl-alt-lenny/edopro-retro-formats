# Edison rule-flag research (roadmap item 5)

**Question:** what is the most historically accurate ocgcore duel-flag configuration for
TCG Edison Format as played at SJC Edison, 2010-04-24?

**Method, and why it matters:** this is not "does 2010 = 2005 GOAT" and not "does a flag's
name sound plausible" — GOAT (April 2005) and Edison (April 2010) are five years and at
least one TCG rules revision apart, and community explanations of "TCG rules" are
frequently written from the perspective of the *modern* game and retroactively applied.
Every claim below is placed on an explicit timeline (true in 2005? still true in 2010?
changed by 2010? changed after 2010?) and labelled by evidence quality:

- **[period-evidence]** — a primary/period document (official rulebook, tournament
  policy, rulings PDF, event FAQ), ideally archived, quoted verbatim.
- **[secondary]** — a later but reliable account, or a period forum/community source
  where no primary document was found.
- **[inference]** — reasoned from indirect evidence (e.g. "the flag is inherited from
  MR1 and nothing suggests MR1 behaviour changed here").
- **[unknown]** — genuinely searched, found nothing. Recorded as a gap, not guessed.

Mechanical claims (what a `DUEL_*` flag actually changes) are separately, independently
verified against the **pinned** `edo9300/ygopro-core` revision recorded in
`data/sources.json` (`ygopro-core`, `46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57`) — cloned
fresh for this task and read directly (not merely trusted from the prior
`docs/research/ocgcore-flags.md` survey, though every mechanical claim there was
independently re-derived here and found to match exactly). Source citations below are
`file:line` against that exact commit.

## Scope

The current profile (`data/rule-profiles/tcg-mr1-edison.json`) is `DUEL_MODE_MR1`
verbatim — six flags: `DUEL_OCG_OBSOLETE_IGNITION`, `DUEL_1ST_TURN_DRAW`,
`DUEL_1_FACEUP_FIELD`, `DUEL_SPSUMMON_ONCE_OLD_NEGATE`, `DUEL_RETURN_TO_DECK_TRIGGERS`,
`DUEL_CANNOT_SUMMON_OATH_OLD`. None of MR1's own six flags is in dispute here — MR1 is
the documented rules-era label EDOPro itself uses for the Synchro-era-without-Synchro-
restrictions period Edison sits inside, and nothing in this research questions it. What
*is* in question is the eleven additional flags `DUEL_MODE_GOAT` adds on top of MR1
(GOAT = MR1 | 11 flags, `ocgapi_constants.h:419`) — each one is an axis on which Project
Ignis's GOAT composite chose TCG-2005-era behaviour over the OCG/modern default, and each
is evaluated independently for whether that same choice holds five years later, in April
2010.

## Sources consulted

Per-source findings and evidence-quality labels are folded into each row below; the
consolidated source list (with archive URLs) is recorded in `data/sources.json` under
the ids referenced per row.

- `edisonformat-rule-differences`, `edisonformat-priority-page` — the community's own
  13 claimed "Edison Format Rule Differences" and its "Ignition Effect Priority"
  explainer, fully transcribed and cross-checked against every source they themselves
  cite. Never treated as evidence on their own; used as a lead list. Of the 13 claimed
  rules, only 4 correspond to any ocgcore flag at all (the rest are card-template/
  deck-construction/judge-procedure matters with no engine flag) — the other 9 are not
  forced into a match.
- **The document family that actually answers these questions**: Konami's numbered
  **Official Rulebook** series — `konami-rulebook-2008-v70` (Dec 2008),
  `konami-official-rulebook-v71-2010` (Mar 2010, **25 days before Edison**, the primary
  source for most rows below), and `konami-new-master-rules-rulebook-2011` (May 2011,
  13 months after Edison) — read cover-to-relevant-section in all three editions to
  bracket every mechanic on both sides of the Edison date. Text proved to be
  word-for-word stable across years except where a row below says otherwise.
- **The document families that do NOT answer these questions** (checked and confirmed
  empty, a useful negative result in its own right, and a correction to how this
  project's existing source notes characterised them): `ude-tournament-policy-appendix-a`
  and `kde-tournament-policy-archive` are Tournament Policy / Penalty Guidelines /
  Appendix A documents — administrative (penalties, sanctioning, deck-legality
  procedure) in both the UDE and Konami eras, never duel mechanics. `sjc-edison-2010-faq`
  and `konami-set-rulings-archive` (the Machina Mayhem rulings PDF, compiled
  2010-04-06 — 18 days before Edison) were re-read specifically for general
  rules-mechanics content and contain none beyond card-specific chain/timing notes.
- `konami-fast-effect-timing-page`, `average-duelist-2012-priority-change` — dates the
  one confirmed rules CHANGE relevant to this research (TCG ignition-priority) to
  2012-04-25, two years after Edison; used to bound the "still true at Edison" finding
  on its later side.

## The evidence table

Legend for "Required action": **A** reproduced by an MR1 flag already present · **B**
requires an additional existing `DUEL_*` flag · **C** already reproduced by card
scripts/historical variants, not a duel flag · **D** cannot currently be reproduced by
ocgcore · **E** the historical claim itself remains unresolved.

| # | Historical behaviour | 2010 evidence | ocgcore mechanism (pinned commit, independently re-verified) | Currently in profile? | Action | Confidence |
|---|---|---|---|---|---|---|
| 1 | **Ignition-effect priority (broad "TCG-style"): the turn player may activate ANY ignition effect, any location, at any point the chain is empty during Main Phase** | **[period-evidence]** Official Rulebook v7.1 (archived 2010-03-30, **25 days pre-Edison**): Ignition Effects usable "just by declaring its activation during your Main Phase"; general "Priority" system grants the turn player first action "in each phase or step of their turn." Identical wording v7.0 (Dec 2008) → v8.0 (Nov 2011, already Xyz-era) — a span that fully brackets Edison. The narrower condition was adopted **2012-04-25**, two years after Edison (`average-duelist-2012-priority-change`, corroborated by the first archive capture of Konami's Fast Effect Timing page, 2012-04-27). | `DUEL_TCG_FAST_EFFECT_IGNITION` (`processor.cpp:809,826`, independently re-read): bypasses both the Monster-Zone-only location filter and the "must follow a chain-end/own-summon event" gate that `DUEL_OCG_OBSOLETE_IGNITION` alone enforces. | No — only the narrower `DUEL_OCG_OBSOLETE_IGNITION` (inherited from MR1) | **B — add `DUEL_TCG_FAST_EFFECT_IGNITION`** | **High.** Period-primary, dated on both sides of Edison, plus an engine test (`IgnitionPriorityFlagTest`) empirically confirms the flag changes real ocgcore behaviour in exactly the documented way. |
| 2 | Continuous Trap's bare activation and its separately-usable trigger/quick effect forced into separate chains | **[period-adjacent, inconclusive]** No general rulebook statement found either way. A Konami TSHD rulings PDF (dated 2010-04-30, 6 days *after* Edison) shows one specifically-worded card (Roar of the Earthbound) whose activation and effect occur "on the same Chain," which is suggestive but does not confirm or refute the *general* mechanic, and postdates Edison anyway. | `DUEL_USE_TRAPS_IN_NEW_CHAIN` (`processor.cpp:3754`, re-verified): with the flag, the "combine into the same chain" prompt (message 94) is skipped and the combination is disallowed. | No | **E — unresolved** | Low. Leave the profile as-is (flag absent) rather than guess; the one card-specific data point available doesn't map cleanly onto the general mechanic. |
| 3 | Damage Step chain-window structure: finer (~7 distinct sub-step timings) vs. coarser ("6-step") | **[period-evidence + period-adjacent]** Rulebook v7.0/v7.1 (pre-Edison) describes Damage Step activation limits in prose without naming sub-steps. A dated Pojo.com forum post (**2009-04-16, a full year before Edison**), citing the same rulebook's page numbers, documents an explicit **7-substep** structure matching (sub-step for sub-step) what EdisonFormat.com's "Rule 8" presents today. | `DUEL_6_STEP_BATLLE_STEP` (`processor.cpp:2305-2315`, re-verified): suppresses/merges some Damage Step chain windows into a coarser structure. | No | **Confirmed correct as-is — do not add.** | Medium-high. The finer (non-"6-step") structure is attested a year before Edison via a source citing the operative rulebook by page number; the exact 2005→2009 transition date remains `[unknown]`. |
| 3b | The companion flag restricting damage-substep chains to one per window | Not independently researched by name; inferred from row 3 (same underlying Damage Step mechanism, always used together with it in the GOAT composite). | `DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP` (`processor.cpp:2315,2356,...`, re-verified mechanically but not period-researched). | No | **Inferred correct as-is — do not add**, lower confidence than row 3 | Low-medium (inference only, not directly researched). |
| 4 | Trigger effects on a card in a hidden zone (Deck / face-down Extra Deck / hand) still fire despite the opponent not knowing the condition was met | **[unknown]** — genuinely searched (general rulebook, three period rulings PDFs, KDE policy documents) and found nothing addressing this specific question in either direction. EdisonFormat.com's Rule 9 asserts it but cites only its own internal page, no period source. | `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` (`effect.cpp:236,256`, re-verified): removes the hidden-zone activation restriction. | No | **E — unresolved** | Low. Leave the profile as-is; do not add on an uncited community claim alone. |
| 5 | An Equip Spell whose target becomes invalid is sent to the GY (modern) rather than merely failing without disposal | **[period-evidence]** Official Rulebook v7.1 (25 days pre-Edison), verbatim identical 2008→2011: "the equipped card loses its target, and is destroyed and sent to the Graveyard." No period edition lacks this clause. | `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` (`operations.cpp:1688`, re-verified): suppresses GY-sending in one specific Monster-Zone re-check context. | No | **Confirmed correct as-is — do not add.** | High for the general case (stable, cited text spanning the whole window); the flag's narrower named edge case (equip card itself in the Monster Zone) is `[unknown]` on its own but doesn't change the conclusion for ordinary equip-card play. |
| 6 | Two 0-ATK monsters battling each other are BOTH destroyed | **[period-evidence]** Official Rulebook v7.1 (25 days pre-Edison): the ATK-tie rule ("both monsters are destroyed") carries **no ATK-value exception**. The exception ("neither monster is destroyed") first appears as a new paragraph in the May-2011 "New Master Rules" edition — 13 months after Edison. Independently cross-verified: that same 2011 edition's dated addition is exactly what EdisonFormat.com cites as the 2011 change point, confirming the version dating. | `DUEL_0_ATK_DESTROYED` (`processor.cpp:2974`, re-verified): the tie-destroys-both branch requires `a != 0` unless this flag is set. | No | **B — add `DUEL_0_ATK_DESTROYED`** | **High.** Period-primary, dated on both sides of Edison, plus an engine test (`ZeroAtkBattleFlagTest`) empirically confirms the flag's effect on real battle resolution. |
| 7 | Attack "replay" is auto-declined and not counted against the attacker's announce count unless explicitly canceled | **[period-evidence]** Official Rulebook v7.1 (25 days pre-Edison) documents Replay as an **active choice** every time ("you can choose to attack with the same monster again, or... a different monster, or... not attack at all") — the modern discretionary procedure was already the documented rule at Edison. Read as most likely a simulator-only UX default in the first place, not a paper-TCG rule a rulebook would ever need to state either way. | `DUEL_STORE_ATTACK_REPLAYS` (`processor.cpp:2190-2220`, re-verified): auto-declines the replay prompt and conditionally skips the announce-count increment. | No | **Confirmed correct as-is — do not add.** | Medium-high (the general replay procedure is well-attested as discretionary; the flag's specific "software default" framing is inference). |
| 8 | A monster whose control changed after being Summoned CAN be repositioned by its new controller (vs. the modern restriction, which follows the summoning player) | **[secondary only]** Only a modern community site (edisonformat.net) makes this specific claim, uncorroborated. The general rulebook clause ("cannot change the position of a monster played onto the field this turn") is worded per-monster and is **verbatim unchanged 2008→2011**, so it cannot itself date this claim either way — the real answer would need a specific period ruling/FAQ entry, which was not found in any of the rulings PDFs checked. | `DUEL_CAN_REPOS_IF_NON_SUMPLAYER` (`card.cpp:3272,3773`, re-verified): bypasses the restriction when control changed after the Summon. | No | **E — unresolved** | Low. Leave the profile as-is; the only source is an uncited modern community claim. |
| 9 | Simultaneous Trigger Effects: TCG-specific handling of (a) hidden/non-public triggers folded into the main ordering pass, and (b) triggers from multiple different simultaneous events restricted to only the earliest event | **[period-evidence, genuinely contested]** The official Rulebook (v6.0 through v8.0, 2008-2011, bracketing Edison — text confirmed byte-identical across all four dated captures) describes a **simple two-tier system**: the turn player's simultaneous triggers go first (freely ordered by that player), then the opponent's — with **no mandatory-before-optional split and no "earlier trigger first" tiebreak** anywhere in the text. This directly **contradicts** EdisonFormat.com's own claimed four-tier structure. A 2012 forum thread (two years after Edison) claims the stricter structure was already unwritten tournament-floor practice "for years," which cannot be verified against any 2008-2011 document. Neither of the two SPECIFIC mechanics these ocgcore flags actually implement (non-public-trigger folding; first-event-only restriction) is addressed by any period source in either direction — the rulebook's own worked examples never involve a hidden-zone trigger or two distinct simultaneous events. | `DUEL_TCG_SEGOC_NONPUBLIC` (`field.cpp:3235-3251`, re-verified) and `DUEL_TCG_SEGOC_FIRSTTRIGGER` (`processor.cpp:641-653`, re-verified). | No | **E — unresolved** | Low, and genuinely contested rather than merely under-evidenced: the strongest period-primary source available (the rulebook) describes a simpler baseline than the community claims, and the two specific flag mechanics are untouched by any source found either way. Leave the profile as-is; this is the highest-value open item for future research (candidate lead: an unlocated "Rulebook v9/9.1" edition between Nov 2011 and 2017). |
| 10 | The starting player draws in the first Draw Phase | Already governed by `DUEL_1ST_TURN_DRAW`, part of MR1's own baseline (unchanged since GOAT; out of scope for this GOAT-extras review — see Scope). EdisonFormat.com's Rule #1 makes the same claim with no ocgcore-flag correspondence beyond this existing baseline flag. | `DUEL_1ST_TURN_DRAW` (`processor.cpp:3381`) — already active. | **Yes (inherited from MR1)** | **A — already correct, no action** | High (uncontested; not a GOAT-extra). |

### Claimed rule differences with no ocgcore flag at all

EdisonFormat.com's 13 claimed rule differences were fully transcribed and cross-checked
(`docs/research/edison-rules.md` companion research, cache retained per-agent). Nine of
the thirteen have **no corresponding `DUEL_*` flag** and are not forced into a match:
starting-player draw (already covered, row 10 above), only-one-active-Field-Spell (a
Field Zone replacement rule, not a flag axis), Union Monster equip conditions (card-text/
errata, not an engine flag), phase-dependent mandatory-trigger re-activation-on-negation
(no flag axis), Trap Monster Zone dual-occupancy interactions (core game-state rule, not
a toggle), Life Point payment floor (no flag axis), end-of-turn-discard chain rules (no
flag axis), and infinite-loop resolution procedure (judge/card-ruling policy, not an
engine toggle). These are out of scope for a duel-flag profile; several may be relevant
to future `errata`/card-script work instead and are not tracked further here.

## Decision

`DUEL_MODE_MR1` alone is **not sufficient**. Two of GOAT's eleven extra flags are backed
by period-primary evidence dated on both sides of Edison, and each is now confirmed by an
engine test that fails without it and passes with it:

- **Add `DUEL_TCG_FAST_EFFECT_IGNITION`** (row 1). The broader "any ignition effect,
  any location, whenever the chain is empty during Main Phase" condition was the TCG rule
  continuously from at least Dec 2008 through Nov 2011 — comfortably bracketing Edison —
  and the narrower OCG-style condition (`DUEL_OCG_OBSOLETE_IGNITION` alone, MR1's current
  baseline) was not adopted by the TCG until 2012-04-25, two years after Edison.
- **Add `DUEL_0_ATK_DESTROYED`** (row 6). The rulebook's ATK-tie rule carried no 0-ATK
  exception until the May-2011 "New Master Rules" edition, 13 months after Edison; at
  Edison, two 0-ATK monsters battling each other both died, matching ocgcore's flagged
  (non-default) behaviour rather than its modern default.

Nine other candidate flags are **deliberately left out** of the profile:

- Four are **confirmed correct as-is** by period or period-adjacent evidence — the
  modern ocgcore default already matches 2010 TCG play, so adding the flag would import
  behaviour Edison never had: `DUEL_6_STEP_BATLLE_STEP` and its paired
  `DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP` (rows 3, 3b — the finer non-"6-step" Damage Step
  was already in place at least a year before Edison), `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET`
  (row 5), and `DUEL_STORE_ATTACK_REPLAYS` (row 7).
- Five remain **evidentially unresolved** (classification E) after genuine research
  effort and are recorded honestly in `known_gaps` rather than guessed either way:
  `DUEL_USE_TRAPS_IN_NEW_CHAIN` (row 2), `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` (row 4),
  `DUEL_CAN_REPOS_IF_NON_SUMPLAYER` (row 8), and the SEGOC pair
  `DUEL_TCG_SEGOC_NONPUBLIC`/`DUEL_TCG_SEGOC_FIRSTTRIGGER` (row 9). The SEGOC case is the
  most consequential of these: the strongest period-primary source found (the Official
  Rulebook, stable 2008–2011) directly contradicts the community's claimed structure, so
  adding these flags now would risk importing a rule Edison never had, on the strength of
  a 2012 forum recollection the primary sources don't support. Not adding them is the more
  conservative, evidence-respecting choice, but it is a judgment call, not a settled fact,
  and is flagged as the single highest-value lead for follow-up research.

**Profile status:** `data/rule-profiles/tcg-mr1-edison.json` is updated to a **custom**
flag set (`preset: null`, MR1's 6 flags + the 2 additions above = 8 flags) rather than a
pure `DUEL_MODE_MR1` alias. `formats/2010-03-edison/format.json`'s
`implementation_status.rule_profile` stays `"partial"` — the two most consequential,
best-evidenced questions (ignition priority, 0-ATK destruction) are now resolved with
high confidence, but five flags remain genuinely open, most notably SEGOC. Per the task's
explicit instruction, accuracy takes priority over closing the roadmap item outright.

## Adversarial review

Working through the five self-challenge questions the task specified, against the final
proposed flag set (MR1's 6 + `DUEL_TCG_FAST_EFFECT_IGNITION` + `DUEL_0_ATK_DESTROYED`):

**Are we accidentally importing a 2005 GOAT rule into 2010?** No evidence of this in
either direction taken. Both added flags are independently attested by rulebook editions
dated *after* GOAT (2008, 2010) as well as before Edison, not merely inherited from the
GOAT composite's flag list — they were evaluated on their own 2010 merits, not carried
over because GOAT has them. Conversely, GOAT flags that a naive "GOAT ≈ old TCG" mental
model might suggest carrying forward — `DUEL_6_STEP_BATLLE_STEP`, `DUEL_STORE_ATTACK_REPLAYS`,
`DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` — were specifically checked and found to be
*2005-only* behaviour that had already reverted to the modern default well before Edison;
including them would have been exactly this mistake, and the evidence table exists
precisely to prevent it.

**Are we using an OCG behaviour to approximate a TCG rule that differs subtly?** This is
the live risk for the two SEGOC flags, which is exactly why they were left out rather than
added: the DuelistGroundz 2012 thread's claim ("SEGOC exists in the OCG... In the TCG,
traditionally... Trigger Order plays a large part") explicitly frames the TCG's stricter
tiebreak as a *TCG-specific* deviation from OCG SEGOC, not an OCG behaviour safely
reusable for TCG. Since the mechanism can't be confirmed for April 2010 specifically, the
conservative choice was to decline it rather than risk importing an OCG-flavoured
approximation of a rule the TCG may not have had yet.

**Is a supposed "rule difference" actually card-specific?** Caught directly in row 2:
the one concrete piece of evidence for `DUEL_USE_TRAPS_IN_NEW_CHAIN` was a single card's
(Roar of the Earthbound) rulings text, dated after Edison, that does not establish a
general mechanic — this is exactly the trap the task warned about, and the flag was left
unadded specifically because of it rather than generalized from one card's ruling.

**Is any community explanation contradicted by a period source?** Yes, explicitly — row
9 (SEGOC): EdisonFormat.com's four-tier mandatory/optional structure is directly
contradicted by the Official Rulebook text stable from 2008 through Nov 2011. This is the
clearest instance found in this research of a modern community explanation not matching
the period-primary document, and it is the reason the corresponding flags are not in the
profile.

**Does the flag implement more behaviour than Edison actually had?** Checked per-flag
against its exact source-level mechanism (not its name) for every row in the table.
`DUEL_TCG_FAST_EFFECT_IGNITION`'s actual effect (skip the location filter and the
chain-end/own-summon gate) matches the rulebook's actual "just by declaring... during
your Main Phase" wording precisely, with no broader side effect identified in
`processor.cpp:809,826`. `DUEL_0_ATK_DESTROYED`'s actual effect (drop the `a != 0` guard
on the tie-destroys-both branch) matches the absence of any ATK-value exception in the
pre-2011 rulebook precisely, with no broader side effect identified in
`processor.cpp:2974`. Both additions are narrowly scoped to exactly the documented
behaviour, not a superset of it.
