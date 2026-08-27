# Erratum v2 unordered migration gate

Status: passed as a dry-run pre-migration gate. No canonical erratum was
migrated by this gate.

Source commit: `e7be46dbd92214140eb10d6d2a7d3e7a16bd9b62`

The dedicated tooling in `tests/unordered_migration_materializer.py` derives
its scope only from the live `migration_audit.audit_corpus()` facts:

```text
equivalent == false
research_status == "already-researched"
migration_complexity == "unordered-researched"
```

This produces 47 targets from the 49 remaining v1 records. The two excluded
records are exactly `erratum-insect-imitation` and `erratum-last-will`; they
remain v1 and were not researched or adjudicated by this gate.

The 47 target IDs are:

```text
erratum-a-deal-with-dark-ruler
erratum-apprentice-magician
erratum-armed-dragon-lv3
erratum-armed-dragon-lv5
erratum-axe-of-despair
erratum-birdface
erratum-bubonic-vermin
erratum-dark-mimic-lv1
erratum-dark-scorpion-meanae-the-thorn
erratum-dedication-through-light-and-darkness
erratum-elegant-egotist
erratum-emblem-of-dragon-destroyer
erratum-freed-the-matchless-general
erratum-fusion-sage
erratum-giant-rat
erratum-great-dezard
erratum-hand-of-nephthys
erratum-hero-signal
erratum-horus-the-black-flame-dragon-lv4
erratum-manju-of-the-ten-thousand-hands
erratum-masked-dragon
erratum-mother-grizzly
erratum-mystic-swordsman-lv2
erratum-mystic-swordsman-lv4
erratum-mystic-tomato
erratum-ninjitsu-art-of-transformation
erratum-paladin-of-white-dragon
erratum-pandemonium
erratum-peten-the-dark-clown
erratum-pyramid-turtle
erratum-sangan
erratum-skull-knight-2
erratum-sonic-bird
erratum-terraforming
erratum-thunder-dragon
erratum-toon-table-of-contents
erratum-tyrant-dragon
erratum-ufo-turtle
erratum-ultimate-insect-lv1
erratum-ultimate-insect-lv3
erratum-ultimate-insect-lv5
erratum-vampire-lord
erratum-witch-of-the-black-forest
erratum-xy-dragon-cannon
erratum-xyz-dragon-cannon
erratum-xz-tank-cannon
erratum-yz-tank-dragon
```

## Target shape and DAG proof

Every target is a full v2 payload: `target_count = 47`, `sugar_count = 0`,
`full_count = 47`. Each legacy change becomes one event and one transition;
no transitions are merged and no `cooccurrence_sources` are added. Event IDs
use the existing opaque `c0`, `c1`, ... convention. Declaration order is not
used as chronology.

| Property | Distribution |
|---|---:|
| Total events | 2: 41, 3: 5, 4: 1 |
| Relevant events | 2: 46, 3: 1 |
| Ordering shape | `{}`: 41, `edges:1`: 5, `edges:2`: 1 |
| Relevant ordering structure | `no-proven-ordering`: 47 |
| Authored state entries per record | 1: 44, 2: 3 |

The six records with date-proven edges are `Axe of Despair`, `Paladin of
White Dragon`, `Sangan`, `Tyrant Dragon`, `Vampire Lord`, and `XYZ-Dragon
Cannon`. Their edges are unrelated date-proven relations involving the
non-relevant `c1` event; the unordered relevant event pairs retain no edge.
The gate independently recomputes every edge from `ordering_proof()` and
rejects any edge not proven by chronology.

The authored coverage distribution is 49 `reuse-upstream` states and one
`known-gap` state. Across all 192 structurally reachable states, the runtime
resolves 47 terminal states mechanically to `modern`, 95 unauthored
non-terminal states to `unresolved`, and retains the 50 authored states (49
`reuse-upstream`, one `known-gap`). No state-space hole is guessed.

The 38 bundled/shared-package versus 9 mechanically-distinct order-unknown
split is the research classification in the frozen state-model design
document. It is not recomputed here and does not become a v2 schema field.

## Preservation and semantic delta

The gate parses every generated payload through the real `ErratumV2.load()`
and checks the v1 data independently of the constructor output. It preserves
top-level data, complete effective blocks, transition text/kind/axis/summary/
sources, coverage payloads and passcodes, known gaps, implementation metadata,
and exact-set reference identities.

```text
schema_failures = []
load_failures = []
preservation_failures = []
```

v1/v2 equality is intentionally not the criterion. Exhaustive comparisons at
the audit's finite chronology-boundary dates found 47 records with intentional
semantic deltas across 219 differing snapshots. The delta consists only of
event-set identities: common event sets retain their v1 coverage signatures.
At snapshot level, `v1_only` sizes were 1: 138 and 2: 3; `v2_only` sizes were
1: 216 and 3: 3. The delta is therefore removal of array-prefix artefacts and
addition of reachable unordered event sets, not changed text, sources,
chronology, coverage payload, metadata, or card identity.

All 46 self-contradictory targets have at least one exhaustive boundary
snapshot proving that v1's positional candidate conflicts with an event's own
OLD/NEW chronology, and v2 excludes that impossible candidate. YZ-Tank Dragon
is the sole non-contradictory incomplete target.

YZ-Tank Dragon has two unordered relevant events. Its v1 boundary candidates
name three states: `{}`, `{c0}`, and `{c0,c1}`. The v2 structural DAG names
all four reachable combinations: `{}`, `{c0}`, `{c1}`, and `{c0,c1}`. The
fourth state `{c1}` is present naturally through generic unordered-event
semantics and is mechanically `UNRESOLVED` because it is unauthored.

## Shadow consumers

The shadow repository replaces exactly the 47 audited v1 objects with parsed
targets. It contains `294 v2 + 2 v1`; the two v1 objects are the original
Insect Imitation and Last Will objects/bytes.

Both currently buildable formats were run through the real builder:

| Format | Baseline hash | Shadow hash | Text | Entries | Substitution map |
|---|---:|---:|---|---|---|
| GOAT | `0x28E9FC02` | `0x28E9FC02` | identical | identical | identical |
| Edison | `0x54508AB7` | `0x54508AB7` | identical | identical | identical |

The reporting path also runs against both repositories without v1-only
assumptions: it reports 247 v2/49 v1 for baseline and 294 v2/2 v1 for the
shadow. Human-facing v2 state labels may differ from legacy numeric labels;
the executable substitution choices are identical.

Validator results:

```text
baseline errors = 0
shadow errors = 0
new error codes = {}
baseline warnings = 360
shadow warnings = 360
warning-code delta = {}
```

No warning delta needed classification or authorization. In particular, no
validator, runtime, or schema files were changed for this gate.

## File-safety boundary

This commit changes only the dedicated gate tooling, its regression tests,
and this research record. It writes no canonical migration payloads. The
following remain unchanged: `data/errata/*.json`, `data/banlists/`,
`data/pools/`, `data/releases/`, `data/rule-profiles/`, `formats/`, and
`dist/`.
