# Active brief

Status: **queued, not started**. One brief lives here at a time; when
Worker completes it (accepted or rejected by Brain), move this file to
`docs/briefs/archive/<date>-<slug>.md` and replace it with the next one, or
leave a one-line "no brief queued" placeholder.

---

## MODE: DOCUMENTATION

## Goal

Correct two overclaiming wording patterns in the Tokyo Dome ("yugi-kaiba")
research packet, identified by external review, without changing any
adjudication, verdict, canonicalization status, or data value they
accompany.

## Starting SHA

`1cc6e63e78a7b8681941fcb58bc53c9619cf91ee` (verify this is still `main`'s
tip before starting; if not, note the actual starting SHA in your report).

## Why this is next

This is a small, precisely-scoped correction flagged by review before the
Brain/Worker framework existed. It was deliberately left unfixed while the
framework was installed, per instruction not to mix corrective research
edits into a coordination-setup commit. It's also a good first brief to
validate the new Worker workflow end-to-end on something low-risk before
anything larger.

## Relevant context

Read only:

- `docs/research/yugi-kaiba-format-source-gate.md` (narrative research log
  — you do not need to read the whole multi-thousand-line file; the
  relevant passages are the ones matching the patterns below, plus enough
  surrounding context in each to edit safely)
- `docs/research/yugi-kaiba-format-source-packet.json` (machine-readable
  evidence packet — same scoping)
- `tests/test_yugi_kaiba_format_gate.py` (the test that reads the packet —
  read this fully; it's the thing you must not break)

You do **not** need to read the rest of `docs/research/`, the roadmap, or
any other Tokyo Dome material. Do not re-derive or re-adjudicate anything
about Tokyo Dome's canonicalization status, restriction hypothesis, or
engine representability — those are out of scope and currently correct as
stated.

### The two patterns

**Pattern 1 — object-authentication overclaim.** Session 11 found collector
photographs (blog `daiti0526`, 2018-03-08) of what's described as a
physical 1999 Konami Tokyo Dome invitation and Game Boy tournament
rulebook. Confirmed instances (Brain verified each of these directly —
this list is a floor, not a ceiling; re-grep before considering the pass
complete):

- `...-packet.json:1704` (a source `label` field) — "EXIF-verified personal
  photographs of an authentic 1999 Konami invitation and..."
- `...-packet.json:1707` (the `evidence_tier` **data field**, not prose —
  see "Protected invariants") — `"1-genuine-primary-for-event-identity-only
  (an actual 1999 Konami-issued document, personally inspected; ...)"`
- `...-packet.json:1712` (a `note` field) — "...of a genuine 1999 Konami
  invitation envelope, invitation card..., and a 4-page tournament
  rulebook..." and "...via a genuinely independent, **official period
  document**..." (the "genuinely independent" half, contrasting this
  provenance group with others in the packet, is fine — only "official
  period document" overclaims)
- `...-packet.json:3704` — "...publishing original, EXIF-verified
  photographs of an authentic 1999 Konami Tokyo Dome invitation..." and
  "...genuine new primary confirmation of the event's date/venue/official
  identity, via a source-type (an actual period Konami-issued document)
  stronger than anything previously in this packet..."
- `...-packet.json:3714` — "a new, independently-authenticated, official
  1999 Konami document confirming the event's date/venue/identity"
- `...-packet.json:4067` — "an authentic, EXIF-verified 1999 Konami
  invitation and tournament rulebook for this exact event was located"
- `...-gate.md:3081` — "publishing EXIF-verified photographs of an
  authentic 1999 Konami Tokyo Dome invitation, guardian notification
  letter, and a full tournament rulebook."
- `...-gate.md:3083` — "This is genuine new primary confirmation of the
  event's date..., venue..., and"
- `...-gate.md:3085` — "official identity, via a source-type - an actual
  period Konami-issued document - stronger than anything previously..."

Note: the literal phrase **"genuine primary" (two words) does not actually
appear** anywhere in either file — it only occurs as the hyphenated
compound `genuine-primary` inside the `evidence_tier` slug (1707) and as
"genuine **new** primary confirmation" (3704, gate.md:3083). Grep for
`genuine` broadly, not the exact two-word phrase.

This overclaims: EXIF metadata authenticates a *photograph's capture*
(e.g., that the photo was actually taken in 2018 with the claimed
camera/settings — that specific claim, where made, is fine), not the
*physical historical object* the photograph depicts. The object's own
provenance was never independently authenticated in this research.

Corrected framing (adapt to context, don't just find-and-replace):
collector-held physical document photographed in 2018; photograph whose
EXIF metadata is consistent with an original 2018 capture; a document
*purporting to be* a 1999 Konami invitation/rulebook; a strong candidate
physical primary object. Where the surrounding prose is already careful
about scope (e.g., correctly walling this source off from OCG
restriction-list use — every instance above already does this, and that
scoping logic must be preserved verbatim), the defect is specifically the
authentication-strength language, not the scoping logic around it.

**Do not overcorrect to "this is probably fake."** The issue is that
*object* provenance wasn't independently established by EXIF, not that
there's a reason to doubt the object. Visually/historically-consistent
language is fine where the research actually supports it.

**Pattern 2 — search-completeness overclaim.** Session 5 and session 11
found no independent second hosting of the V Jump interior restriction-card
crop via a Wayback/CDX digest search. Confirmed instances needing a fix
(again, a floor not a ceiling):

- `...-gate.md:3062-3066` ("### What was found" section) — "No independent
  copy of the interior restriction-card crop or of page 20 was found
  **anywhere** - not via marketplace listing, not via collector blog, not
  via Wayback/CDX content-hash search, not via English-language sources..."
  — this sentence already *names* the channels searched, which is good;
  the overclaim is narrowly the word "anywhere" implying totality. Fix:
  something like "...was located via any of the following channels
  searched..." rather than "found anywhere."
- `...-gate.md:3073` — "This is a stronger form of the 'single-hosted'
  finding than session 5's search-based conclusion: a direct content-hash
  check, not merely the absence of a search hit." Treats "single-hosted"
  as a finding that further search "strengthens." A content-hash check
  against the Wayback CDX index only narrows what wasn't found *there* —
  it doesn't make a global-uniqueness claim more true.
- `...-packet.json:3707` — the JSON key itself,
  `"content_hash_confirmation_of_single_hosting"`, plus its value's closing
  clause: "This is a STRONGER form of the 'no independent hosting found'
  conclusion than session 5's own search-based finding: it is a direct,
  mechanical, content-hash-level check, not merely the absence of a search
  hit." Same defect as gate.md:3073. If you rename the key, first confirm
  nothing reads it by key name (see "Required investigation" — `grep -r
  content_hash_confirmation_of_single_hosting` across the repo); if
  anything does, leave the key name and fix only the prose value.
- `...-packet.json:3710` — "No independent copy of the interior
  restriction-card crop or of page 20 specifically was found **anywhere**
  - not via marketplace listing, not via collector blog, not via
  Wayback/CDX content-hash search, not via English-language sources, and
  not via verbatim propagation of any of the crop's seven most distinctive
  sentences..." — same "anywhere" defect as gate.md:3062-3066, same fix
  pattern (it already names channels; drop the totality claim).
- `...-packet.json:3714` — "a materially stronger form of the
  'single-hosted' negative finding, via direct content-hash verification
  rather than search-absence alone" — same "strengthens a global claim"
  defect as the two instances above.

Lower-priority / likely-already-adequate instances exist too (e.g.
`...-gate.md:2199,3040`; `...-packet.json:273,3454,3727,3797,3829` all use
"single-hosted" but mostly as a plain descriptive label already paired
with hedges like "authentication chain unverified," "despite a dedicated
... search," or "SUPPORTED_BUT_INCOMPLETE, not PROVEN"). Use this test for
every instance you find: **does this sentence claim or imply (a) that no
independent copy exists in reality/globally, or (b) that more/repeated
searching progressively "confirms" or "strengthens" a single-hosted
status — rather than simply narrowing what wasn't found in the channels
actually checked?** If yes to either, fix it. If a sentence already scopes
cleanly to "not located via [named searches]," it likely needs no change —
use judgment rather than mechanically touching every occurrence of the
word "single-hosted."

Corrected framing where a fix is needed: no independent copy was
**located** despite the specific searches actually performed (name them —
Wayback/CDX content-hash search, English- and Japanese-language
reverse-image/text search, marketplace listings, etc., as the surrounding
sentence already does in most cases), and no exact-byte duplicate was
found in the queried Wayback index. This is evidence about the searched
corpus, not proof of global absence.

## Scope

- Edit prose and, where the overclaim is baked into a **data field value**
  (not just narrative text — see "Protected invariants" below), edit that
  field's string value too, in both files.
- Find every instance of both patterns, not just the ones listed above —
  the ones above are known instances from a grep pass, not necessarily
  exhaustive. Do a full pass of both files for these two patterns before
  considering this done.
- You may reword adjacent sentences as needed for the correction to read
  naturally, but do not add new claims, new evidence, or new sources.

## Non-goals

- Do not change `canonicalization_status`, `scope_class_status`,
  `source_authentication_status`, the restriction hypothesis, the
  certified candidate pool, any digest/hash value, or any other
  adjudication verdict.
- Do not re-run or re-derive any research (no new web fetches, no new
  source hunting).
- Do not touch any file outside the three listed above unless you discover
  a genuine third file carrying the same overclaim text — if so, note it in
  your report; don't silently expand scope without flagging it.
- Do not canonicalize Tokyo Dome or otherwise change its status from
  research-only.

## Protected invariants

- Brain already verified (grep across `tests/` and `retroformats/`) that
  **no test or code currently asserts on any of these overclaiming
  substrings.** `tests/test_yugi_kaiba_format_gate.py` does reference an
  `evidence_tier` field once (line ~1983), but that's a *different,
  unrelated* field (`event_disruption_reassessment.evidence_tier`), not
  the source's `evidence_tier` at packet.json:1707. Re-run this grep
  yourself before editing (`grep -rn "evidence_tier\|single-hosted\|EXIF\|Konami-issued" tests/ retroformats/`)
  as a final check — if it still comes back empty outside the one known
  unrelated hit, you do not need to touch any test assertion logic, only
  `tests/test_yugi_kaiba_format_gate.py` needs to keep *passing* (no
  reason it shouldn't, since it doesn't assert on this text).
- The `evidence_tier` field at packet.json:1707 and the `tier` field at
  packet.json:3727 are data-shaped strings with a leading `N-slug` prefix
  (`"1-genuine-primary-for-event-identity-only"`,
  `"2-candidate"`). Preserve the leading tier number and the overall
  `N-slug (parenthetical detail)` shape — only reword the slug/parenthetical
  text, don't renumber or restructure, since nothing you've found reads
  this by number today but a future consumer might.
- No canonical `data/`, `formats/`, or `dist/` files should be touched by
  this brief at all.

## Required investigation

1. Re-grep both files for the terms listed under each pattern above (and
   any close variants you notice while reading) to confirm you have every
   instance — Brain's list above is verified but explicitly not claimed
   exhaustive.
2. For each instance, read enough surrounding context to write a correction
   that's accurate and doesn't orphan a sentence that referred to the old
   wording.
3. Re-run `grep -rn "evidence_tier\|single-hosted\|EXIF\|Konami-issued\|content_hash_confirmation_of_single_hosting" tests/ retroformats/`
   yourself to confirm the "Protected invariants" finding above still
   holds before you start editing.

## Acceptance criteria

- Every instance of both overclaim patterns in the two named files is
  corrected to accurately scope what was and wasn't established.
- No adjudication verdict, status enum, digest, hash, date, or count
  changed.
- `tests/test_yugi_kaiba_format_gate.py` passes.
- `python -m retroformats validate` and `python -m retroformats build
  --check` are unaffected (these files aren't canonical data, but run them
  anyway to confirm — should be a no-op).
- The full suite (`python -m unittest discover -t . -s tests -v`) passes.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Commit on a new branch (e.g. `worker/tokyo-dome-epistemic-wording-fix`).
Do not merge to `main` yourself. Do not push unless asked. One commit is
fine; split into two only if the test-string update is logically distinct
enough to warrant it.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Full list of instances corrected (file:line before → after, or a diff).
- Whether `tests/test_yugi_kaiba_format_gate.py` needed a matching string
  update, and what changed if so.
- Exact output of the three validation commands above.
- Any third location you found carrying either overclaim pattern that
  wasn't in the known-instances list above.
- Anything you were unsure how to word without either re-overclaiming or
  overcorrecting into unwarranted doubt — flag it rather than guessing.
