# Historical card behaviour: the errata subsystem

A historical format is only playable if its cards *behave* the way they did.
This subsystem answers, per card and per format snapshot: **which
implementation reproduces the behaviour that was actually in force?** — and
refuses to answer when the evidence cannot support one.

The rule it replaces: *"Project Ignis has an old version of this card, so I
guess we need it."* The rule it installs: *"at this format's snapshot date,
this exact historical behaviour applies, here is the evidence, and here is
the implementation that reproduces it."*

## The data model

A card's history is a **chain of versions**: a baseline, then one new version
per entry in `changes[]` (ordered oldest → newest; the last one is the modern
card). See `schemas/erratum.schema.json`.

### Not all change is the same kind

`changes[].kind` distinguishes four genuinely different situations, and only
two of them can ever substitute a card implementation:

| kind | what happened | implementation consequence |
|---|---|---|
| `functional` | printed/official text changed **and** resolves differently | needs a historical implementation for the era before it |
| `ruling` | official interpretation/procedure changed, text unchanged | needs one too — the behaviour differed even though the card did not |
| `cosmetic` | wording/PSCT modernisation, same resolution | **never** substitutes; the modern script is period-correct |
| `engine` | the *game rules* changed, not the card | **never** substitutes; belongs to a rule profile |

The record-level `classification` is the dominant kind (severity
`functional` > `ruling` > `engine` > `cosmetic`) and the validator enforces
agreement, so anything filtering on classification sees the truth.

A record whose only changes are cosmetic or engine **cannot be selected
computationally** even if it carries an upstream passcode. It can still be
pinned by an explicit `errata_overrides.include` — the honest model for
reference-parity cases (see *Nobleman of Crossout* below).

### Chronology carries its own uncertainty

`changes[].effective` never forces a day-precise date to exist:

```jsonc
"effective": {
  "date": "2016-09-15",          // when the NEW behaviour took effect
  "precision": "day",            // day | month | year — widens into an interval
  "status": "reported",          // verified | reported
  "old_attested_through": null,  // latest date the OLD state is positively attested
  "new_attested_from": null,     // earliest date the NEW state is positively attested
  "basis": "TCG release of the first printing carrying the errata'd text (DPRP-EN038)"
}
```

Three shapes, all first-class:

- **exact** — a point date, at day/month/year precision;
- **bounded** — no point date, but the old state is attested through A and the
  new state from B (the honest shape when a change has no announcement);
- **unknown** — `{}`, when research established nothing.

Never invent a day to satisfy the schema. The validator rejects inverted
bounds, bounds contradicting a date, and definitely-inverted change order.

### Selection is fail-safe

`Erratum.selection_at(snapshot)` walks the implementation-relevant changes and
returns one of four states:

- **`modern`** — the modern implementation is correct (or a documented
  `none-needed` decision stands in for the version);
- **`historical`** — substitute this version's implementation;
- **`ambiguous`** — the snapshot falls inside an unresolved transition
  interval. **Selection refuses.** The validator errors
  (`format.erratum-ambiguous`) and `build_lflist` raises. Old-or-new is never
  guessed;
- **`gap`** — chronology is determinate, but the needed version has no usable
  implementation.

On the effective date itself the **new** behaviour applies (`snapshot >= date`
→ new), and a coarse-precision date makes every day inside its interval
ambiguous — exactly the semantics the release subsystem uses for release
events.

Only `review.status: "reviewed"` records participate in computed selection.
An `imported` record applies solely through an explicit
`errata_overrides.include`, so mechanically-imported guesses can never quietly
change a format.

### Multiple revisions

A card errata'd twice has two implementation-relevant changes and therefore
three versions. The version a change *creates* carries its own
implementation:

```jsonc
"implementation": { …version 0, the baseline… },
"changes": [
  { "kind": "ruling",     "resulting_implementation": { …version 1… } },
  { "kind": "functional" }        // creates the MODERN card: no implementation
]
```

Sangan is the worked example: version 0 is the 2005-era behaviour
(`goat-entries` 504700178: mandatory trigger, no name-lock, no once-per-turn,
failed searches verified by revealing the Deck), version 1 is the same card
after the verification procedure ended (`cards-unofficial` 511002631), and
the modern card is the 2016 erratum (name-lock + hard once per turn).

### Acknowledged divergences

Some period behaviour is known to differ and cannot be reproduced today.
Blocking every format forever is not honest; silently using the modern card
is not either. So the record acknowledges it:

```jsonc
"implementation": {
  "strategy": "unresolved",
  "gap": { "reason": "…", "upstream_checked": true,
           "behavioural_impact": "…", "sources": ["…"] }
}
```

An acknowledged gap lets the format keep the modern card, raises
`format.erratum-known-divergence`, and is counted by `report`. An
**un**acknowledged one stays a hard error: a gap must be *examined*, not
merely unfinished. This mirrors the release gap ledger — known holes are
recorded with evidence and stay visible.

## The pipeline

Raw network fetching and offline normalisation are separate stages, and the
canonical records are only ever written by a guarded applier.

```
Yugipedia Card Errata namespace ─┐
Yugipedia set release dates ─────┤ fetch_errata_sources.py   (network, cached,
Project Ignis BabelCDB (pinned) ─┤                            never committed)
Project Ignis CardScripts (pinned)┘
                 ↓
        errata_research.py        (offline) → one research packet per card:
                                   text lineage + each version's introducing
                                   printing and its earliest TCG date, cdb
                                   texts matched to lineage versions, script
                                   diffs, upstream annotations
                 ↓
          per-card review          → decisions (classification, change kinds,
                                     chronology with evidence, version→impl)
                 ↓
        errata_apply.py           (offline, guarded) → data/errata/*.json
                 ↓
        validate → build          → whitelists substituting the right version
```

### Evidence is machine-checked, not trusted

`errata_apply.py` rejects a decision rather than record an unverifiable claim:

- a chronology claim must carry `date_evidence`;
- **`set-release`** evidence names a lineage version; the applier **recomputes**
  the date and precision from the research packet and rejects any mismatch —
  a reviewer cannot type a date;
- **`shared-chronology`** evidence names an entry in the sourced chronology
  table and the bounds are **copied from it**, never from the decision;
- **`external`** evidence needs a URL and a quote, and a bound claimed from a
  web.archive.org capture must equal that capture's own date;
- card texts are copied from the packet by version index (or must match a
  packet-carried database text exactly) — never hand-transcribed;
- a `reuse-upstream` passcode must exist among the packet's upstream
  implementations;
- the classification is recomputed as the dominant change kind.

Output is deterministic: stable key order, LF newlines, unchanged files are
not rewritten, and `--dry-run` reports without writing.

## Running it

```bash
# 1. network stage (polite, cached under ~/.cache/retroformats)
python -m retroformats.importers.fetch_errata_sources --cache ~/.cache/retroformats \
    --list-namespace --pages-for-names names.json --set-dates sets.json

# 2. offline normalisation into research packets
python -m retroformats.importers.errata_research --cache ~/.cache/retroformats

# 3. apply reviewed decisions (guarded, deterministic)
python -m retroformats.importers.errata_apply --decisions decisions/ \
    --packets ~/.cache/retroformats/errata/research \
    --chronologies chronologies.json --dry-run

# 4. certify and build
python -m retroformats validate
python -m retroformats build
python -m retroformats report -v      # substitutions + divergences per format
```

Caches are never committed (`.gitignore`); pinned upstream revisions live in
`data/sources.json`.

## What the research established

- **Failed-search deck verification** — the period procedure Project Ignis
  encodes as `Duel.GoatConfirm` — was official TCG ruling-layer policy
  through at least **2011-02-02** (Konami's Storm of Ragnarok rulings), and
  demonstrably **eighteen days before the Edison snapshot** (the Machina
  Mayhem rulings document, compiled 2010-04-06). The modern
  no-verification policy is first attested **2019-04-03**. No announcement of
  the change was found, so the interval stays open and is recorded as bounded
  chronology. **Both GOAT and Edison are determinately inside the old era.**
- Separately, whether a card could be **activated at all** with no valid
  target changed **per card**: Reinforcement of the Army had already lost its
  fail-to-find allowance by the 2008-12-15 official Card FAQ capture while
  Sangan and Witch of the Black Forest kept theirs. The two behaviours are
  modelled as different changes, and the per-card one is left unresolved
  where it could not be dated.
- **Format Library is not a usable structured errata source.** Its `erratas`
  table exists but nothing reads or writes it; period texts live per printing
  in `Print.description` and are deliberately excluded from the card API; the
  site-wide card text is the *current* text synced nightly from YGOPRODeck;
  format-specific behaviour is carried by human-written per-format rulings.
  Details and quotes in `data/sources.json` (`formatlibrary-source`).

## Adversarial self-review (2026-08-20)

The subsystem was attacked after it was built, on the real data. What broke,
and what held:

**Two genuine defects, both fixed with regression tests:**

1. **Unidentifiable generated codes.** The card index — the project's ground
   truth for passcode identity and alias relationships — is generated from
   "every passcode the repository references", but its collector walked only
   each record's *baseline* implementation. The per-version implementations
   the multi-revision schema introduced were never indexed, so **22 historical
   codes reached the Edison whitelist with no verifiable identity**. Fixed by
   walking every version; two tests now assert that every emitted code is
   identifiable and that the committed index covers every reference.
2. **Known-wrong modern fallbacks reported as neutral defaults.** When one
   change in a chain is dated and another is not, the evidence can be unable
   to say *which* historical version applies while still proving the modern
   card is not one of them. Edison's `unresolved_policy: modern` then selects
   a card we know is wrong — for **44 cards** — and reported it as an ordinary
   default. Selection now exposes the candidate version set, and this case is
   reported and counted separately (`format.erratum-modern-known-wrong`). The
   behaviour is unchanged (there is no better determinate answer, and erroring
   would block the format), but the accuracy claim is now honest.

**What held under attack:**

- *Boundary and precision*: 20 probes over the exact-date boundary, month
  precision in December, year precision across a leap day, 30/31-day months,
  touching and adjacent attestation bounds, date-plus-bounds together, and
  malformed input. All correct; ambiguity is returned wherever the evidence
  does not decide.
- *Multi-revision selection*: three-revision chains at four era points,
  ambiguous middle changes bracketed by definite ones, cosmetic/engine
  changes interleaved with functional ones (version indices count the
  implementation-relevant subsequence only, and `implementation_for_version`
  indexes the same one), empty relevant-change sets, and an implementation
  wrongly attached to the final change.
- *Validator guards*: definite chronological inversion, inverted attestation
  bounds, artwork variants outside the ±10 window, and a historical passcode
  aliasing the wrong modern card all fire. Overlapping-but-uncertain intervals
  are correctly *not* errors and resolve to ambiguity only inside the overlap.
- *GOAT parity*: entry-for-entry identical to the reference with hash
  `0x28e9fc02`. The provenance discriminator was checked for equivalence in
  both directions — no record marked in-reference has its modern code in the
  reference list, and no record marked out-of-reference has its historical
  code there. Deliberate breaks (excluding a record, mislabelling one as
  in-reference) were both caught by the parity test.
- *Whitelist and identity*: no modern code is ever legal alongside its
  historical implementation, no historical code is emitted for two cards, no
  pool card is itself a historical code, and banlist counts transfer to every
  emitted code including artwork variants (Ring of Destruction's
  511000824/511000825 and Crush Card Virus's 511000822/511000823 each carry
  their card's count).
- *Edison version choice*: every GOAT-era variant Edison selects was diffed
  against its modern script; the differences are the verification package, the
  activation-condition relaxation that belongs to it, upstream metadata
  refactors, or MR1 zone handling shared by both eras. None is 2005-only.
- *Evidence integrity*: all 296 records were re-verified independently of the
  applier — every recorded date matches a real printing date in its research
  packet, every card text is verbatim from the packet, every `reuse-upstream`
  code exists, and every unresolved version documents its gap.
- *Classification consistency*: all 73 records whose upstream variant uses
  `Duel.GoatConfirm` carry a `ruling` change — exactly the 73 scripts upstream
  ships with it, with no drift.

An earlier pass had already normalised three records that classified the
damage-step activation window as `engine` while the rest called the identical
phenomenon `ruling`; in ocgcore that window is a per-effect script flag no
`DUEL_*` rule-profile flag can set, so only a card-level implementation
reproduces it. `erratum.engine-with-card-implementation` now makes the
incoherent combination visible.

## Behavioural verification

`implementation.tested: true` means an executable test demonstrated the
behaviour against the real engine — never that a Lua file exists. See
[docs/engine-testing.md](engine-testing.md).
