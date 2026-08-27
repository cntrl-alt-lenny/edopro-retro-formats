"""Integration tests over the repository's REAL canonical data.

These are the guarantees the project makes about its shipped content:
- the canonical data validates with zero errors;
- the generated GOAT list is semantically identical (same code->count map,
  hence the same EDOPro banlist hash) to Project Ignis's reference
  GOAT.lflist.conf (vendored under tests/fixtures/ with provenance);
- dist/ is exactly what the canonical data regenerates (no hand edits).
"""

from __future__ import annotations

import datetime as _dt
import unittest
from pathlib import Path

from retroformats.build import build_all
from retroformats.lflist import build_lflist, historical_identity, lflist_hash, parse_lflist
from retroformats.model import ErratumV2
from retroformats.repo import Repository
from retroformats.validate import Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The EDOPro content hash of the deduplicated Ignis GOAT list entries.
# (Ignis's shipped file currently duplicates one line - 511000868 - which the
# client's line-folding XOR cancels out, so the file's *runtime* hash differs;
# see docs/edopro-research.md "banlist hash" notes.)
IGNIS_GOAT_MAP_HASH = 0x28E9FC02


class RealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)

    def test_canonical_data_validates_without_errors(self):
        validator = Validator(self.repo)
        validator.validate()
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_giant_rat_selection_shape(self):
        """The real-data ordering-constraint case backing
        docs/research/edison-behaviour-gaps.md (roadmap item 5c) and
        tests/test_errata.py's OrderingConstraintTest. Giant Rat has two
        relevant ruling changes: changes[0] is the Deck-verification/
        reveal-on-whiff axis, confirmed OLD at the Edison snapshot
        (old_attested_through 2011-02-02); changes[1] is the activation-
        semantics (no-valid-target-required) axis, completely undated.

        Under the v2 event-DAG representation, the two events remain separate
        and unordered. At this snapshot, the candidates are the baseline and
        the state in which only the activation-semantics event has happened;
        the latter is intentionally unresolved rather than guessed. The
        former v1 positional candidate that treated the verification event as
        the first axis is no longer represented. See docs/research/
        edison-behaviour-gaps.md's "A/B/C/D partition" section for the full
        per-record accounting, including the 8 sibling cluster-1 records
        whose changes[] lists the same two axes in the opposite order, for
        which candidate 1 *does* correctly represent the real intermediate
        state.
        """
        erratum = self.repo.errata["erratum-giant-rat"]
        sel = erratum.selection_at(_dt.date(2010, 4, 24))
        self.assertEqual("ambiguous", sel.chronology)
        self.assertEqual(
            (frozenset(), frozenset({"c1"})),
            tuple(candidate.events for candidate in sel.candidates),
        )
        self.assertEqual("unresolved", erratum.state_for(frozenset({"c1"})).coverage.kind.value)

    def test_goat_matches_ignis_reference(self):
        fixture = (FIXTURES / "ignis-GOAT.lflist.conf").read_text(encoding="utf-8")
        ((_, reference_map),) = parse_lflist(fixture).items()
        built = build_lflist(self.repo.formats["2005-04-goat"], self.repo)
        self.assertEqual(reference_map, built.entries)
        self.assertEqual(IGNIS_GOAT_MAP_HASH, built.hash)
        self.assertEqual(IGNIS_GOAT_MAP_HASH, lflist_hash(reference_map))

    def test_goat_declares_its_reference_id(self):
        """`formats/2005-04-goat/format.json` names the SPECIFIC reference
        implementation it reproduces ('project-ignis-goat'), distinct from
        provenance_source (the pinned ignis-lflists repository as a
        whole). Output-neutral across the canonical migration:
        `test_goat_matches_ignis_reference` above already proves the
        generated list is unaffected byte-for-byte whether the 247
        migrated records' `reference_identities[]` entries exist or not."""
        fmt = self.repo.formats["2005-04-goat"]
        self.assertEqual("project-ignis-goat", fmt.reference_parity.get("reference_id"))
        self.assertEqual("ignis-lflists", fmt.reference_parity.get("provenance_source"))

    def test_goat_forbids_modern_versions_of_overridden_cards(self):
        built = build_lflist(self.repo.formats["2005-04-goat"], self.repo)
        # Modern Chaos Emperor Dragon (82301904) must not appear; the
        # pre-errata implementation (511000819) must, at 0 copies.
        self.assertNotIn(82301904, built.entries)
        self.assertEqual(0, built.entries[511000819])
        # Modern Sangan must be replaced by Sangan (GOAT), limited to 1.
        self.assertNotIn(26202165, built.entries)
        self.assertEqual(1, built.entries[504700178])

    def test_edison_pool_cardinality(self):
        pool = self.repo.pools["pool-edison-2010"]
        self.assertEqual(
            3673,
            len(pool.cards),
            "Edison pool cardinality changed - re-run the comparison against "
            "YGOPRODeck's Edison tag and termitaklk before accepting",
        )

    def test_edison_pool_edge_cases(self):
        codes = self.repo.pools["pool-edison-2010"].passcodes()
        legal = {
            88643579: "Dark End Dragon (SJCS-EN007, the SJC prize promo cutoff)",
            33093439: "Cyber Eltanin (JUMP-EN038, the JUMP promo cutoff)",
            40854197: "Elemental HERO Absolute Zero (YG04-EN001, the manga promo cutoff)",
            58120309: "Starlight Road (Duelist Pack Collection Tin 2010)",
            30915572: "Gallis the Star Beast (GX Tag Force 3, Europe-only release)",
            31038159: "Genesis Dragon (JUMP-EN034, sourced include)",
            39980304: "Chain Material (PTDN-EN067; YGOPRODeck tag false negative)",
            52352005: "XX-Saber Gottoms (ANPR-EN044; YGOPRODeck tag false negative)",
        }
        illegal = {
            95453143: "Hundred Eyes Dragon (JUMP-EN039, after the JUMP promo cutoff)",
            88071625: "The Tyrant Neptune (May 2010 subscription bonus)",
            135598: "Key Mouse (The Shining Darkness - EU date inside window, set excluded)",
            5998840: "XX-Saber Boggart Knight (TSHD Sneak Peek participation card)",
            10026986: "Worm King (Duel Terminal 1 machine-only)",
            66661678: "Royal Knight of the Ice Barrier (Duel Terminal 1 machine-only)",
            68811206: "Tyler the Great Warrior (one-of-one charity card)",
        }
        for code, why in legal.items():
            self.assertIn(code, codes, f"must be Edison-legal: {why}")
        for code, why in illegal.items():
            self.assertNotIn(code, codes, f"must NOT be Edison-legal: {why}")

    def test_edison_whitelist_enforces_pool_and_banlist(self):
        """Every pool card contributes exactly one *card* to the list at its
        banlist count, but a card may emit several CODES: artwork variants,
        and (for a substituted card) the historical implementation's own
        artwork variants. Counting codes alone would drift whenever a
        substitution lands, so the invariant is asserted per card."""
        from retroformats.lflist import select_applicable_errata

        fmt = self.repo.formats["2010-03-edison"]
        built = build_lflist(fmt, self.repo)
        self.assertIn("$whitelist", built.text)
        pool = self.repo.pools["pool-edison-2010"]
        banlist = self.repo.banlists["tcg-2010-03"]
        status_by_code = {e.card.passcode: e.status for e in banlist.entries}
        overrides = select_applicable_errata(fmt, self.repo)

        expected_codes: dict[int, int] = {}
        counts = {"forbidden": 0, "limited": 1, "semilimited": 2}
        for card in pool.cards:
            count = counts.get(status_by_code.get(card.passcode, ""), 3)
            override = overrides.get(card.passcode)
            if override is not None:
                passcode, variants = historical_identity(override.implementation)
                codes = [passcode, *variants]
            else:
                codes = [card.passcode, *card.variants]
            for code in codes:
                expected_codes[code] = count
        self.assertEqual(expected_codes, built.entries)

        # Per-card banlist cardinality is unchanged by substitution.
        by_status: dict[str, int] = {}
        for card in pool.cards:
            status = status_by_code.get(card.passcode)
            if status:
                by_status[status] = by_status.get(status, 0) + 1
        self.assertEqual({"forbidden": 43, "limited": 70, "semilimited": 19}, by_status)

        # A card from the following set era must not appear at all (Key Mouse,
        # The Shining Darkness - the whitelist rejects unlisted cards).
        self.assertNotIn(135598, built.entries)

    def test_every_generated_code_is_identifiable(self):
        """Found by adversarial review: a code the build emits must exist in
        the card index, or the project is shipping a passcode whose identity
        and alias it cannot verify. The index collector originally walked only
        each record's BASELINE implementation, so the per-version
        implementations the multi-revision schema introduced went unindexed
        and 22 such codes reached the Edison whitelist."""
        index = self.repo.card_index
        for fmt_id in sorted(self.repo.formats):
            fmt = self.repo.formats[fmt_id]
            if fmt.banlist_id not in self.repo.banlists or fmt.pool_id not in self.repo.pools:
                continue
            built = build_lflist(fmt, self.repo)
            unknown = sorted(c for c in built.entries if index.name_of(c) is None)
            self.assertEqual([], unknown, f"{fmt_id}: emitted codes missing from the card index")

    def test_card_index_covers_every_referenced_passcode(self):
        """Every passcode the repository can legitimately reference — modern
        cards, banlist/pool entries and variants, v1 baseline/resulting
        implementations, and v2 authored-coverage/reference-identity
        substitutions alike — must already be indexed in
        data/cards/index.json. This is the broader, referenced-passcode
        invariant, distinct from `test_every_generated_code_is_identifiable`
        above (which only checks codes GOAT/Edison currently EMIT): a
        passcode can be legitimately referenced by canonical data without
        ever being emitted by either of the two currently-defined formats,
        and this test is what would catch that drifting silently.

        Previously a known gap (`collect_referenced_passcodes()` read only
        v1-shaped `erratum.implementation`/`erratum.changes`, raising
        AttributeError on any `ErratumV2` record) — the collector now reads
        each erratum through its own native v1/v2 API, and this test
        restores the real invariant rather than pinning the crash."""
        from retroformats.importers.card_index import collect_referenced_passcodes

        refs = collect_referenced_passcodes(self.repo)
        missing = sorted(p for p in refs if p not in self.repo.card_index.by_passcode)
        self.assertEqual([], missing, f"passcodes referenced by canonical data but absent from the card index: {missing}")

    def test_pool_cards_are_tcg_scoped_in_the_card_database(self):
        """A TCG format's pool must reference codes EDOPro treats as TCG cards
        (cdb `ot` including SCOPE_TCG 0x2). A code scoped OCG-only would be
        rejected in an official-cards room and would carry the OCG behaviour.

        One documented exception, found by the errata review: Project Ignis
        models Mind Master's TCG version as a SEPARATE entry (96782896,
        ot=2, aliased to 96782886) because the canonical row carries the
        OCG-only text, while our release-derived pool naturally references
        the canonical passcode its TDGS-EN016 printing maps to. Recorded as an
        open question in docs/roadmap.md rather than silently patched: it is a
        card-identity question, not an errata chronology one.
        """
        known_exceptions = {96782886: "Mind Master (TCG version is upstream 96782896)"}
        index = self.repo.card_index
        for pool_id in ("pool-goat-2005-ignis", "pool-edison-2010"):
            offenders = {}
            for card in self.repo.pools[pool_id].cards:
                row = index.by_passcode.get(card.passcode)
                ot = row.get("ot") if row else None
                if ot is not None and not (int(ot) & 0x2):
                    offenders[card.passcode] = card.name
            unexpected = {c: n for c, n in offenders.items() if c not in known_exceptions}
            self.assertEqual({}, unexpected, f"{pool_id}: non-TCG-scoped pool cards")

    def test_every_edison_substitution_rests_on_resolved_chronology(self):
        """Edison has no reference implementation to copy, so every historical
        version it uses must be justified by evidence that actually places the
        change relative to 2010-04-24 - an exact date or attested bounds.
        A substitution resting on unresolved chronology would be a guess."""
        import datetime as _dt

        from retroformats.lflist import select_applicable_errata

        fmt = self.repo.formats["2010-03-edison"]
        snapshot = _dt.date.fromisoformat(fmt.snapshot)
        unjustified = []
        for _, override in select_applicable_errata(fmt, self.repo).items():
            erratum = override.erratum
            if erratum.id in fmt.errata_include:
                continue  # explicit adjudication, documented separately
            if isinstance(erratum, ErratumV2):
                selection = erratum.selection_at(snapshot)
                all_relevant_ids = frozenset(e.id for e in erratum.relevant_events())
                if selection.chronology != "determinate":
                    continue
                if selection.candidates[0].events == all_relevant_ids:
                    continue  # terminal/modern: no substitution to justify
                justified = any(
                    e.effective.get("date")
                    or e.effective.get("old_attested_through")
                    or e.effective.get("new_attested_from")
                    for e in erratum.relevant_events()
                )
                if not justified:
                    unjustified.append(erratum.id)
                continue
            selection = erratum.selection_at(snapshot)
            relevant = erratum.relevant_changes()
            if selection.version_index is None or selection.version_index >= len(relevant):
                continue
            effective = relevant[selection.version_index].get("effective") or {}
            if not (
                effective.get("date")
                or effective.get("old_attested_through")
                or effective.get("new_attested_from")
            ):
                unjustified.append(erratum.id)
        self.assertEqual(
            [], sorted(unjustified),
            "these Edison substitutions rest on unresolved chronology",
        )

    def test_edison_never_lists_a_modern_and_historical_version_together(self):
        """The failure that would let a player run six copies: the modern card
        and its historical implementation both legal in one list."""
        from retroformats.lflist import select_applicable_errata

        fmt = self.repo.formats["2010-03-edison"]
        built = build_lflist(fmt, self.repo)
        for modern, override in select_applicable_errata(fmt, self.repo).items():
            passcode, _variants = historical_identity(override.implementation)
            self.assertNotIn(
                modern,
                built.entries,
                f"{override.erratum.modern_card.name}: modern code still legal alongside "
                f"its historical implementation {passcode}",
            )
            self.assertIn(passcode, built.entries)

    def test_edison_banlist_counts(self):
        banlist = self.repo.banlists["tcg-2010-03"]
        by_status = {}
        for entry in banlist.entries:
            by_status[entry.status] = by_status.get(entry.status, 0) + 1
        self.assertEqual(
            {"forbidden": 43, "limited": 70, "semilimited": 19},
            by_status,
            "March 2010 TCG list cardinality changed - re-verify against sources",
        )

    def test_dist_is_up_to_date(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            written = build_all(self.repo, dist=Path(tmp))
            self.assertTrue(written, "expected at least one buildable format")
            for fmt_id, path in written.items():
                committed = REPO_ROOT / "dist" / "lflists" / path.name
                self.assertTrue(committed.exists(), f"dist file missing for {fmt_id}")
                self.assertEqual(
                    committed.read_text(encoding="utf-8"),
                    path.read_text(encoding="utf-8"),
                    f"dist/lflists/{path.name} is stale: run python -m retroformats build",
                )

    def test_rule_profile_flags_match_preset_expansions(self):
        # Expansions verified against ocgapi_constants.h (see the rule profile
        # records and docs/edopro-research.md).
        mr1 = {
            "DUEL_OCG_OBSOLETE_IGNITION",
            "DUEL_1ST_TURN_DRAW",
            "DUEL_1_FACEUP_FIELD",
            "DUEL_SPSUMMON_ONCE_OLD_NEGATE",
            "DUEL_RETURN_TO_DECK_TRIGGERS",
            "DUEL_CANNOT_SUMMON_OATH_OLD",
        }
        goat_extra = {
            "DUEL_TCG_FAST_EFFECT_IGNITION",
            "DUEL_USE_TRAPS_IN_NEW_CHAIN",
            "DUEL_6_STEP_BATLLE_STEP",
            "DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE",
            "DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET",
            "DUEL_0_ATK_DESTROYED",
            "DUEL_STORE_ATTACK_REPLAYS",
            "DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP",
            "DUEL_CAN_REPOS_IF_NON_SUMPLAYER",
            "DUEL_TCG_SEGOC_NONPUBLIC",
            "DUEL_TCG_SEGOC_FIRSTTRIGGER",
        }
        # Edison is no longer a bare MR1 alias: docs/research/edison-rules.md's
        # evidence table adds DUEL_0_ATK_DESTROYED, researched and confirmed
        # against period (2008-2011) Konami rulebooks (0-ATK ties destroyed both
        # monsters until Rulebook Version 7.2, ~10.5 months after Edison).
        # DUEL_TCG_FAST_EFFECT_IGNITION was investigated and deliberately NOT
        # added - it overreaches relative to the researched 2010 TCG ignition-
        # priority rule (see the dossier's Decision and Adversarial review) -
        # and is tracked as an engine-level known_gap instead.
        edison_extra = {"DUEL_0_ATK_DESTROYED"}
        self.assertEqual(mr1 | edison_extra, set(self.repo.rule_profiles["rules-tcg-mr1-edison"].flags))
        self.assertEqual(mr1 | goat_extra, set(self.repo.rule_profiles["rules-tcg-goat"].flags))


if __name__ == "__main__":
    unittest.main()
