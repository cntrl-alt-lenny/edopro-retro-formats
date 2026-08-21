# Edison rule-flag research (roadmap item 5)

> **Correction record (2026-08-21):** the first pass of this research concluded row 1
> below (ignition-effect priority) should add `DUEL_TCG_FAST_EFFECT_IGNITION` to the
> profile. An adversarial review challenged that conclusion directly against the pinned
> core and against reopened period-source research, and found it wrong: `DUEL_TCG_FAST_
> EFFECT_IGNITION` grants ignition priority in situations period evidence says Edison did
> not have. Row 1 was rewritten from a behavioural matrix and an independently
> re-researched evidence base; the flag was removed from `data/rule-profiles/tcg-mr1-
> edison.json` and the mismatch is now tracked as an engine-level `known_gap` instead. Row
> 6 (0-ATK) also had its exact citation corrected (the change happened ~March 2011 via
> Rulebook Version 7.2, not "May 2011 / New Master Rules" as first written) - the
> underlying conclusion there (add `DUEL_0_ATK_DESTROYED`) was already correct and is
> unchanged. See the Decision and Adversarial review sections for the full account.

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
- **The document family that actually answers most (not all — see row 1's correction)
  of these questions**: Konami's numbered **Official Rulebook** series —
  `konami-rulebook-2008-v70` (Dec 2008), `konami-official-rulebook-v71-2010` (Mar 2010,
  **25 days before Edison**, the primary source for most rows below), and
  `konami-official-rulebook-v72-2011-dragunity` (Version 7.2, packaged with Structure
  Deck: Dragunity Legion, TCG street date ~2011-03-04/08 — corrected from an earlier,
  mislabeled "New Master Rules"/May-2011/13-months-after-Edison citation; direct PDF-text
  inspection confirmed the two are the same document) — read cover-to-relevant-section in
  all three editions to bracket every mechanic on both sides of the Edison date. For
  ignition-effect priority specifically (row 1), this Rulebook series' general prose
  turned out to be **insufficient on its own** — genuinely ambiguous about the exact
  Summon-vs-any-chain-end question — and the real answer came from a separate document
  family instead: dated period community rulings forums, all eight threads on the same
  "Yu-Gi-Oh! Ruling Queries" forum (`yugiohwiki-forum-priority-q-2010` 2010-01-01 - legacy
  Yu-Gi-Oh! Wiki/Fandom, answers the exact named Malicious/Summoned-Skull scenario directly
  and states it applies to the TCG; `yugiohwiki-forum-priority-q-excl-2010` 2010-03-31 -
  same legacy archive; `yugipedia-forum-chain-resolution-priority-2009` 2009-06;
  `yugipedia-forum-costs-and-priority-2010` 2010-03-07; `yugipedia-forum-priority-dots-2010`
  2010-03-12; `yugipedia-forum-ignition-effect-2010` 2010-03-24/25;
  `yugipedia-forum-about-priority-2010` 2010-07; `yugipedia-forum-sangan-priority-2010`
  2010-10 — independently-dated contemporaneous examples from the *same* community forum,
  not independent authorities, see row 1's provenance note), plus a Konami OCG FAQ ruling
  accessed via a modern citation (`yugipedia-card-rulings-malicious`) and a weaker,
  separate period snapshot of Yugipedia's own reference article
  (`yugipedia-priority-article-2010-01-revision`, 2010-01-28). An earlier pass of this
  research incorrectly reported the "Priority Q" thread as not found; that was a genuine
  research miss, corrected once the thread was directly located and independently
  verified — see the provenance-correction banner under row 1. Rulebook text proved to be
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
| 1 | **Ignition Effect Priority: the turn player's special immediate window to activate an Ignition Effect as Chain Link 1, ahead of the opponent** (rewritten after correction — see banner above; provenance corrected 2026-08-21, see second banner below) | **[period-evidence, eight independently-dated contemporaneous threads from the same community forum — not eight independent authorities; see the provenance note below]** Not a general "any empty-chain moment" rule as the general Rulebook Priority prose alone might suggest, and not first-checked in this pass — the general prose (`konami-official-rulebook-v71-2010`: Ignition Effects usable "just by declaring its activation during your Main Phase"; "Turn Player's Priority... in each phase or step of their turn") is genuinely **ambiguous** on the exact question and is **insufficient on its own** to resolve it (an earlier pass in this research read it as supporting the broad rule; a reopened, adversarial pass found that reading too permissive). The question is resolved instead by **contemporaneous ruling discussions** — the strongest TCG-specific evidence found, and the closest thing to a direct answer located in this entire research effort is `yugiohwiki-forum-priority-q-2010` (legacy Yu-Gi-Oh! Wiki/Fandom, question 2010-01-01 05:13 UTC, answer 06:05 UTC): asked whether Tribute-Summoning Summoned Skull using Destiny HERO - Malicious as tribute lets the turn player use priority to activate Malicious's Ignition Effect from the Graveyard, user Deus Ex Machina answers **yes** — "After Summoned Skull is Summoned, the last thing to happen is the Summon of a monster, so the Turn Player can has Priority to activate a monster's Ignition Effect... This applies to both \_CGs [OCG/TCG]" — then explicitly contrasts the negative case (Malicious sent to GY by Armageddon Knight/Foolish Burial, **not** a Summon): "the last thing to happen is something other than a monster being Summoned, so the Turn Player can't activate Ignition Effects at this time." This single thread directly supports **both** axes at once, using the exact card and exact scenario this research's brief named. `yugiohwiki-forum-priority-q-excl-2010` (2010-03-31, less than four weeks before Edison) independently corroborates the "doesn't have to be the Summoned monster" aspect with Catapult Turtle. Six more threads on the same forum converge on the same shape: `yugipedia-forum-chain-resolution-priority-2009` (2009-06-10/11) states plainly that Ignition Effect Priority applies "if the Chain ends with the Turn Player Special Summoning a monster" and *not otherwise*; `yugipedia-forum-costs-and-priority-2010` (2010-03-07), `yugipedia-forum-priority-dots-2010` (2010-03-12), and `yugipedia-forum-ignition-effect-2010` (2010-03-24/25) each frame a distinct worked example around a Summon; `yugipedia-forum-about-priority-2010` (2010-07-14/16) corroborates with two more Summon-framed examples; `yugipedia-forum-sangan-priority-2010` (2010-10-01) confirms the flip side — a Summon that itself triggers a Mandatory Trigger Effect does **not** grant the window. A period-adjacent Konami OCG FAQ ruling (the same #8231 citation `yugiohwiki-forum-priority-q-2010`'s own thread quotes), reached only via a modern secondary transcription (`yugipedia-card-rulings-malicious`), independently confirms the negative case. A weaker, separate contemporaneous source, a 2010-01-28 snapshot of Yugipedia's own "Priority" reference article (`yugipedia-priority-article-2010-01-revision`), confirms the basic Summon-triggered mechanic was already documented in the reference article at that date. **No period-primary Konami/UDE document stating the complete rule in its own words was found** — therefore confidence here is moderate-high, not absolute. None of these sources — nor edisonformat.com's own current, more detailed Priority page, which draws the identical distinction using the identical card (`edisonformat-priority-page`) — describe any Monster-Zone location restriction; Graveyard-resident Ignition Effects (Malicious, Plaguespreader Zombie) qualify equally. The TCG kept this exact rule until **2012-04-25**, two years after Edison (`average-duelist-2012-priority-change`). | See the behavioural matrix below — **no configuration tested** reproduces "gate = Summon-success only, location = unrestricted" exactly; each of the three real configurations evaluated couples the gate and location axes differently (`processor.cpp:796-836`, re-verified, and empirically confirmed by `tests/engine/test_historical_behaviour.py::IgnitionPriorityMatrixTest`). | Only the narrower `DUEL_OCG_OBSOLETE_IGNITION` (inherited from MR1) — **retained as a deliberate approximation, not an exact implementation; see "Approximation choice" below** | **D — cannot currently be reproduced exactly; recorded as a known_gap** (not **B**: adding `DUEL_TCG_FAST_EFFECT_IGNITION` was the earlier, now-reversed conclusion — it overreaches, see below) | **Moderate-high** for the historical rule itself (eight independently-dated contemporaneous threads from one community forum, including one — Forum:Priority Q — that answers the exact scenario named in this research's brief and states explicitly it applies to the TCG, plus a period-adjacent official-FAQ citation; no period source found describing a broader gate; but no period-primary Konami/UDE document found stating the full rule directly, so confidence is not raised to "high"); **high** for the engine-mismatch finding (direct source reading plus a 4-scenario, 3-configuration empirical test matrix). One agent in the reopened research flagged a legitimate tension worth recording: Konami's 2012 "Fast Effect Timing" replacement structurally treats "after a non-chain action" and "after a Chain resolves" as symmetric cases, which *could* be read to imply the pre-2012 rule also granted Ignition priority after any chain resolution — but no period-adjacent commentary ever describes the 2012 change that way, and every period source found is unanimous that only the Summon case granted it. |

> **Provenance correction (2026-08-21):** an earlier pass of this document stated that no
> document titled "Priority Q" could be located and cited a 2010-01-28 Yugipedia article
> revision as the closest real match. That was a genuine research miss, not a fabrication -
> the exact thread exists (`yugiohwiki-forum-priority-q-2010`, on the legacy Yu-Gi-Oh!
> Wiki/Fandom archive, dated 2010-01-01) and directly answers this research's central
> question using the exact card and scenario the task's original brief named. A companion
> thread, "Forum:Priority Q!" (`yugiohwiki-forum-priority-q-excl-2010`, 2010-03-31), was
> also located and registered. Every statement claiming "Priority Q" was not found has been
> removed from this document; the 2010-01-28 article revision remains cited as a separate,
> weaker, genuinely contemporaneous source, not as a substitute for the now-located thread.

**Provenance note:** the eight 2009–2010 threads above are all posts on the *same*
"Yu-Gi-Oh! Ruling Queries" community forum (a period-contemporaneous venue, not an
official Konami/UDE channel) — six survive on the current Yugipedia site
(`yugipedia.com`), and two (`yugiohwiki-forum-priority-q-2010`,
`yugiohwiki-forum-priority-q-excl-2010`) were located on the *legacy* Yu-Gi-Oh! Wiki
archive, now hosted at `yugioh.fandom.com` — the pre-fork wiki Yugipedia split from;
identical-content mirrors of both also exist at the corresponding `yugipedia.com` URLs,
carrying the same original timestamps, but this document cites the legacy
`yugioh.fandom.com` URLs where that is where the page was actually located and verified,
rather than silently relabelling them as native Yugipedia content. All eight are cited as
**independently-dated contemporaneous examples** — eight separate points in time, from
2009-06 through 2010-10, each independently confirming the same shape of the rule with a
different worked example — not as eight *independent authorities* corroborating each
other; a single incorrect community consensus on that forum could in principle have
produced all eight. This is why the table above still rates confidence "moderate-high,"
not "high": the convergence is real and meaningful (the same specific gate/location
distinction recurs across sixteen months of unrelated worked examples, volunteered by
several different users, including one thread — Forum:Priority Q — that answers the
exact named scenario directly and states it applies to the TCG), but it is convergence
within one community, not across independent communities or official documents.

**Behavioural matrix for row 1** (docs cross-reference: `tests/engine/test_historical_behaviour.py::IgnitionPriorityMatrixTest`, 12 tests, all passing — engine facts below are empirically measured against the pinned core, not merely reasoned from source. Each cell is checked by locating the SPECIFIC message-sequence anchor for that scenario — the last `MSG_SUMMONED`/`MSG_SPSUMMONED` for the Summon scenarios, the last `MSG_CHAIN_END` for the chain-end scenarios — and scanning only the `MSG_SELECT_CHAIN` messages between that anchor and the next `MSG_SELECT_IDLECMD`, with a self-check asserting the candidate never appears in any *earlier* `MSG_SELECT_CHAIN` window; a Normal Summon produces an unrelated, earlier `MSG_SELECT_CHAIN` pair — "does anyone want to respond to the Summon declaration itself" — before `MSG_SUMMONED`, which an unanchored scan of the whole message list could in principle have conflated with the actual ignition-priority window):

| Scenario | Historically expected (period evidence) | `DUEL_MODE_MR1` alone | `MR1 \| DUEL_TCG_FAST_EFFECT_IGNITION` | `MR1` with no ignition-priority flag at all |
|---|---|---|---|---|
| A. Successful Summon, candidate ignition effect in the Monster Zone | Offered | **Offered** (matches) | **Offered** (matches) | **Not offered** (wrong) |
| B. Successful Summon, candidate ignition effect in the Graveyard (the Malicious case) | Offered | **Not offered** (wrong — MR1's Monster-Zone-only filter excludes it) | **Offered** (matches) | **Not offered** (wrong) |
| C. A chain resolves *without* a Summon, candidate in the Monster Zone | **Not** offered | **Offered** (wrong — MR1's gate fires on any chain-end, not just Summons) | **Offered** (wrong, same reason) | **Not offered** (matches) |
| D. A chain resolves *without* a Summon, candidate in the Graveyard | **Not** offered | Not offered (matches, but only by accident — blocked by the location filter, not because the gate correctly excludes non-Summon chain-ends; row C proves the gate itself doesn't) | **Offered** (wrong — the broader flag removes the one thing that was accidentally saving MR1 in row D) | **Not offered** (matches) |

No configuration is fully correct. `DUEL_TCG_FAST_EFFECT_IGNITION` fixes MR1's genuine
error in scenario B but *introduces* a new error in scenario D that MR1 didn't have (MR1
got D right by coincidence), while neither configuration fixes scenario C — adding it does
not net improve accuracy, it just relocates the inaccuracy from one axis onto another. The
flagless option gets both C and D right but is wrong on **both** Summon scenarios (A and
B) — it never grants the special immediate window at all, deleting the defining
Summon-priority mechanic outright rather than approximating it imperfectly. See
"Approximation choice" below for why `DUEL_OCG_OBSOLETE_IGNITION` (plain MR1) is
nonetheless the profile's choice, and what a minimal, *unimplemented* ygopro-core change
would need to do to close this gap exactly: decouple `processor.cpp`'s single
`is_flag(DUEL_TCG_FAST_EFFECT_IGNITION)`
check (currently gating BOTH the event-gate bypass at `processor.cpp:809` AND the
location-filter bypass at `processor.cpp:826` together) into two independently settable
flags/conditions — one controlling only the location filter (bypass it unconditionally, as
an *addition* to `DUEL_OCG_OBSOLETE_IGNITION`'s existing Summon-or-chain-end gate), and a
separate, narrower gate condition that keeps only the Summon-success branch of
`check_events_ocg()` (`processor.cpp:800-808`) and drops the `check_event(EVENT_CHAIN_END)`
branch entirely. No such flag exists in the pinned core; this document does not propose
implementing one, per the task's scope.

### Approximation choice: why `DUEL_OCG_OBSOLETE_IGNITION` stays in the profile

Since row 1 cannot be reproduced exactly, the profile still has to ship *some* choice —
`preset: null` means this is a genuinely open decision, not an inherited default that has
to be defended just because MR1 happens to include the flag. Three real configurations
were evaluated, empirically, against all four scenarios (`IgnitionPriorityMatrixTest`):

| Configuration | A (Summon+MZONE) | B (Summon+GY) | C (chain-end+MZONE) | D (chain-end+GY) |
|---|---|---|---|---|
| No ignition-priority flag at all | Wrong | Wrong | Right | Right |
| `DUEL_OCG_OBSOLETE_IGNITION` (current) | Right | Wrong | Wrong | Right (by accident) |
| `DUEL_TCG_FAST_EFFECT_IGNITION` | Right | Right | Wrong | Wrong |

This is **not** a claim that period sources prove one configuration is objectively
"closest" — no measurement of how often each scenario actually arose in 2010 tournament
play exists, and none is claimed here. This project has not measured, and does not claim,
that scenario A is the single most common priority situation, that non-Summon chain-end
opportunities are quantitatively more frequent than Graveyard-ignition-after-Summon ones,
or that scenario B is quantitatively rare. What follows is an explicit **project policy /
modelling judgment**, stated as exactly that:

- **No flag at all** deletes the defining Summon-priority mechanic entirely — the special
  immediate "activate an Ignition Effect as Chain Link 1" window never exists under this
  configuration, for any scenario, including the case the period sources most directly
  illustrate: `yugipedia-forum-priority-dots-2010`'s own worked example is Special
  Summoning Red-Eyes Darkness Metal Dragon, then activating its effect to revive Blue-Eyes
  White Dragon *before* the opponent can Bottomless Trap Hole the newly-Summoned dragon -
  losing the flag means that activation no longer happens first, which can change which
  effect resolves, not merely reorder two effects that would have happened anyway.
- **`DUEL_OCG_OBSOLETE_IGNITION`** preserves the Summon-priority mechanic for the
  Monster-Zone case (scenario A) but has one false denial (scenario B: a Graveyard ignition
  effect like Destiny HERO - Malicious's is wrongly withheld after a Summon) and one false
  grant (scenario C: a Monster-Zone ignition effect is wrongly offered after an unrelated
  chain resolves with no Summon at all).
- **`DUEL_TCG_FAST_EFFECT_IGNITION`** preserves the mechanic for both Summon cases (A and
  B) but grants historically-unsupported priority in both non-Summon cases (C and D) -
  period sources describe no scenario in which a bare chain resolution (with no Summon)
  grants Ignition Effect Priority.

**Project policy choice**: the project retains `DUEL_OCG_OBSOLETE_IGNITION` as a
conservative compatibility compromise - it preserves the defining Summon-priority
mechanic (partially - correctly for the Monster-Zone case, incorrectly for the Graveyard
case) rather than deleting it outright (the flagless option), without expanding the
privilege to every location after arbitrary non-Summon chain ends (what
`DUEL_TCG_FAST_EFFECT_IGNITION` does). This is a modelling judgment about which kind of
wrongness is more acceptable to ship, not a claim derived from the historical sources
themselves, and it is not risk-free: denying a legal Ignition Effect Priority option
(scenario B, this configuration's own failure mode) is a real rules deviation that can
alter duel outcomes exactly as much as wrongly granting one can - the project does not
claim the retained configuration is safe or harmless, only that it is the compromise
chosen. This is an explicit compatibility choice, not an exact implementation, and both of
its known-wrong cases (B: Graveyard/other-location ignition effects miss their priority
window after a Summon; C: a Monster-Zone ignition effect wrongly gets a priority window
after an unrelated chain resolves) remain recorded, unchanged, in `known_gaps`.
| 2 | Continuous Trap's bare activation and its separately-usable trigger/quick effect forced into separate chains | **[period-adjacent, inconclusive]** No general rulebook statement found either way. A Konami TSHD rulings PDF (dated 2010-04-30, 6 days *after* Edison) shows one specifically-worded card (Roar of the Earthbound) whose activation and effect occur "on the same Chain," which is suggestive but does not confirm or refute the *general* mechanic, and postdates Edison anyway. | `DUEL_USE_TRAPS_IN_NEW_CHAIN` (`processor.cpp:3754`, re-verified): with the flag, the "combine into the same chain" prompt (message 94) is skipped and the combination is disallowed. | No | **E — unresolved** | Low. Leave the profile as-is (flag absent) rather than guess; the one card-specific data point available doesn't map cleanly onto the general mechanic. |
| 3 | Damage Step chain-window structure: finer (~7 distinct sub-step timings) vs. coarser ("6-step") | **[period-evidence + period-adjacent]** Rulebook v7.0/v7.1 (pre-Edison) describes Damage Step activation limits in prose without naming sub-steps. A dated Pojo.com forum post (**2009-04-16, a full year before Edison**), citing the same rulebook's page numbers, documents an explicit **7-substep** structure matching (sub-step for sub-step) what EdisonFormat.com's "Rule 8" presents today. | `DUEL_6_STEP_BATLLE_STEP` (`processor.cpp:2305-2315`, re-verified): suppresses/merges some Damage Step chain windows into a coarser structure. | No | **Confirmed correct as-is — do not add.** | Medium-high. The finer (non-"6-step") structure is attested a year before Edison via a source citing the operative rulebook by page number; the exact 2005→2009 transition date remains `[unknown]`. |
| 3b | The companion flag restricting damage-substep chains to one per window | Not independently researched by name; inferred from row 3 (same underlying Damage Step mechanism, always used together with it in the GOAT composite). | `DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP` (`processor.cpp:2315,2356,...`, re-verified mechanically but not period-researched). | No | **Inferred correct as-is — do not add**, lower confidence than row 3 | Low-medium (inference only, not directly researched). |
| 4 | Trigger effects on a card in a hidden zone (Deck / face-down Extra Deck / hand) still fire despite the opponent not knowing the condition was met | **[unknown]** — genuinely searched (general rulebook, three period rulings PDFs, KDE policy documents) and found nothing addressing this specific question in either direction. EdisonFormat.com's Rule 9 asserts it but cites only its own internal page, no period source. | `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` (`effect.cpp:236,256`, re-verified): removes the hidden-zone activation restriction. | No | **E — unresolved** | Low. Leave the profile as-is; do not add on an uncited community claim alone. |
| 5 | An Equip Spell whose target becomes invalid is sent to the GY (modern) rather than merely failing without disposal | **[period-evidence]** Official Rulebook v7.1 (25 days pre-Edison), verbatim identical 2008→2011: "the equipped card loses its target, and is destroyed and sent to the Graveyard." No period edition lacks this clause. | `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` (`operations.cpp:1688`, re-verified): suppresses GY-sending in one specific Monster-Zone re-check context. | No | **Confirmed correct as-is — do not add.** | High for the general case (stable, cited text spanning the whole window); the flag's narrower named edge case (equip card itself in the Monster Zone) is `[unknown]` on its own but doesn't change the conclusion for ordinary equip-card play. |
| 6 | Two 0-ATK monsters battling each other are BOTH destroyed | **[period-evidence, date corrected 2026-08-21]** Official Rulebook v7.1 (25 days pre-Edison): the ATK-tie rule ("both monsters are destroyed") carries **no ATK-value exception**. The exception ("neither monster is destroyed") first appears in Official Rulebook **Version 7.2**, page 43 — packaged with **Structure Deck: Dragunity Legion**, TCG street date **~2011-03-04/08** (`yugipedia-dragunity-legion-structure-deck`), ~10.5 months after Edison — not "May 2011 / 13 months" as an earlier pass of this research wrote, which mistook the Wayback capture date of an already-released PDF for its release date. Independently confirmed by a dated (**2011-03-08**) Pojo.com Forums post from Konami's own TCG "Judge Manager," quoting the exact new clause verbatim and stating plainly it was a genuine change, "at least for the TCG" (`pojo-atk0-rulebook-change-2011`) — this is also the exact source EdisonFormat.com itself cites. `konami-official-rulebook-v72-2011-dragunity` (renamed/corrected from a mislabeled "New Master Rules" source entry — direct PDF-text inspection confirms it IS Version 7.2, not a separate later edition). | `DUEL_0_ATK_DESTROYED` (`processor.cpp:2974`, re-verified): the tie-destroys-both branch requires `a != 0` unless this flag is set. | No | **B — add `DUEL_0_ATK_DESTROYED`** | **High.** Period-primary, dated on both sides of Edison, plus an engine test (`ZeroAtkBattleFlagTest`) empirically confirms the flag's effect on real battle resolution. The historical conclusion (add the flag) is unchanged by the date correction. |
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

`DUEL_MODE_MR1` alone is **not sufficient**, but only **one** of GOAT's eleven extra
flags is added — a second candidate (`DUEL_TCG_FAST_EFFECT_IGNITION`) was investigated in
depth, initially added, then **removed again** after an adversarial re-review found the
addition wrong. Both outcomes are backed by period evidence and, where the engine can
represent the conclusion at all, an engine test that fails under the wrong configuration
and passes under the right one:

- **Add `DUEL_0_ATK_DESTROYED`** (row 6). The rulebook's ATK-tie rule carried no 0-ATK
  exception until Official Rulebook Version 7.2, packaged with Structure Deck: Dragunity
  Legion (TCG street date ~2011-03-04/08, ~10.5 months after Edison — corrected from an
  earlier "May 2011 / 13 months" citation that had mistaken a document's Wayback capture
  date for its release date); at Edison, two 0-ATK monsters battling each other both died,
  matching ocgcore's flagged (non-default) behaviour rather than its modern default.
- **Do NOT add `DUEL_TCG_FAST_EFFECT_IGNITION`** (row 1) — reversing this research's own
  earlier conclusion. Reopened, adversarial research (six independently-dated 2009–2010
  threads from the same period community forum, a Konami OCG FAQ ruling for the exact
  card the task's brief named, and a direct re-derivation of the pinned core's exact
  mechanism) converged on a
  historical rule — Ignition Effect Priority gated to a **Summon that doesn't itself start
  a chain**, unrestricted by **location** — that is a genuine hybrid neither existing flag
  reproduces. A 4-scenario engine test matrix (`IgnitionPriorityMatrixTest`) proves this
  empirically: `DUEL_TCG_FAST_EFFECT_IGNITION` correctly fixes MR1's real error (excluding
  Graveyard-based ignition effects like Destiny HERO - Malicious after a Summon), but it
  also *introduces* a new error MR1 didn't have (wrongly granting ignition priority after
  a chain resolves with **no** Summon at all, in any location) — it does not net improve
  accuracy, and specifically risks representing behaviour Edison never had. This is
  recorded as an engine-level `known_gap` — see the matrix and the note on what a minimal,
  *unimplemented* core change would need to do, both under row 1 above.

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
flag set (`preset: null`, MR1's 6 flags + `DUEL_0_ATK_DESTROYED` = 7 flags) rather than a
pure `DUEL_MODE_MR1` alias. `formats/2010-03-edison/format.json`'s
`implementation_status.rule_profile` stays `"partial"` — the 0-ATK question is resolved
with high confidence, but the ignition-priority question is now understood precisely
enough to know it is an *engine limitation* rather than an open research question, and
five other flags remain genuinely open, most notably SEGOC. Per the task's explicit
instruction, accuracy takes priority over closing the roadmap item outright, and over
defending this document's own earlier conclusion. Note that MR1's own 6 flags include
`DUEL_OCG_OBSOLETE_IGNITION`, which this document's own row-1 evidence shows does NOT
reproduce Edison's ignition-priority rule exactly either — it is kept as a deliberately
evaluated approximation, not a default inherited without scrutiny; see "Approximation
choice" directly under the evidence table for the full three-configuration comparison and
the reasoning for keeping it over the two alternatives.

## Adversarial review

Working through the five self-challenge questions the task specified, against the final
proposed flag set (MR1's 6 + `DUEL_0_ATK_DESTROYED`):

**Are we accidentally importing a 2005 GOAT rule into 2010?** No evidence of this in
either direction taken. The one added flag, `DUEL_0_ATK_DESTROYED`, is independently
attested by rulebook editions dated *after* GOAT (2008, 2010) as well as before Edison,
not merely inherited from the GOAT composite's flag list — it was evaluated on its own
2010 merits, not carried over because GOAT has it. Conversely, GOAT flags that a naive
"GOAT ≈ old TCG" mental model might suggest carrying forward — `DUEL_TCG_FAST_EFFECT_IGNITION`
itself (this document's own first-pass conclusion), `DUEL_6_STEP_BATLLE_STEP`,
`DUEL_STORE_ATTACK_REPLAYS`, `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` — were checked and
found to be *2005-only or otherwise-overreaching* behaviour Edison did not share; the
ignition-priority case in particular shows this mistake can survive an initial pass of
research and only surface under a full behavioural matrix, which is why one was built.

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
against its exact source-level mechanism (not its name) for every row in the table —
**this question is exactly where the original ignition-priority conclusion failed**, and
is the reason this document was corrected. The first pass verified `DUEL_TCG_FAST_EFFECT_
IGNITION`'s mechanism (skip the location filter and the chain-end/own-summon gate) and
checked it against the Rulebook's general "just by declaring... during your Main Phase"
prose — but never built the 4-scenario matrix needed to notice that the flag's *gate* axis
is broader than the *historical* rule, not just broader than `DUEL_OCG_OBSOLETE_IGNITION`'s
gate. Re-deriving the matrix directly (row 1) shows the flag grants ignition priority
after **any** chain resolves, including ones with no Summon at all — behaviour six
independently-dated 2009–2010 threads from the same period community forum agree Edison
did not have. This is a
concrete instance of the exact failure mode this question warns about, caught by rebuilding
the check from a fuller behavioural matrix rather than a single worked example, and is why
the flag is now a `known_gap` instead of an addition. `DUEL_0_ATK_DESTROYED`'s actual
effect (drop the `a != 0` guard on the tie-destroys-both branch) matches the absence of any
ATK-value exception in the pre-2011 rulebook precisely, with no broader side effect
identified in `processor.cpp:2974` — this one addition remains narrowly scoped to exactly
the documented behaviour, not a superset of it. The retained `DUEL_OCG_OBSOLETE_IGNITION`
was checked against this same question directly, not assumed safe by default: its known-
wrong case (scenario B) is a *denial* of an option Edison duelists had (implementing LESS
behaviour than Edison actually had), never a grant of one they didn't (the Approximation
choice section's whole argument for keeping it over `DUEL_TCG_FAST_EFFECT_IGNITION` rests
on this asymmetry - a flag that does too little is judged safer for representing a
historical ruleset than one that does too much).
