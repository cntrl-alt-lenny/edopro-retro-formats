"""The rulings gate on errata records (round 037, part A; docs/errata.md).

Round 035 made every generated card record which period rulings were searched for
the one difference its script implements. Round 036 found that the same reading of
printed text as period behaviour sits in the records themselves: a `functional`
transition that no ruling was ever asked about decides which script a list ships.
So a functional transition that applies at Edison's or Tengu's snapshot carries a
`rulings_check` too, in the same shape and under the same rules
(`Validator._check_rulings_body`, codes under `erratum.`).

Two halves. The first builds tiny repositories to prove each rule fires. The second
reads the live data: the records the gate covers are re-derived here independently
of the validator, from the four conditions of the round brief, and each carries a
check.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import types
import unittest
from unittest import mock

from retroformats.model import ERRATUM_RULINGS_GATE_EXEMPT, change_state_at
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import REPO_ROOT, TempRepoTest, card, v2_event, v2_transition

EDISON = "2010-03-edison"
TENGU = "2011-09-tengu"
EDISON_SNAPSHOT = dt.date(2010, 4, 24)


def _validate(root):
    validator = Validator(Repository.load(root))
    validator.validate()
    return validator


def _codes(validator):
    return {f.code for f in validator.errors}, {f.code for f in validator.warnings}


def _finding(**changes):
    entry = {
        "source": "test-ude-ruling",
        "looked_for": "a ruling on Beta's use limit",
        "finding": "supports",
        "passage": "Beta can be used once.",
        "in_force": "shown",
        "in_force_basis": "The document was current at both snapshots.",
    }
    for key, value in changes.items():
        if value is None:
            entry.pop(key, None)
        else:
            entry[key] = value
    return entry


def _check(*findings, **changes):
    check = {
        "difference": "Beta is once per turn in the modern card and had no limit in the era.",
        "checked": "2026-09-29",
        "searched": list(findings) or [_finding()],
    }
    for key, value in changes.items():
        if value is None:
            check.pop(key, None)
        else:
            check[key] = value
    return check


class ErratumRulingsGateTest(TempRepoTest):
    """Each rule of `_check_erratum_rulings`, on synthetic records."""

    def _seed(self, events=None, ordering=None, states=None, classification="functional", format_ids=(EDISON,), **kw):
        self.add_card_index([card(200, "Beta")])
        self.add_banlist(entries=[{"card": card(200, "Beta"), "status": "limited"}])
        self.add_pool(cards=[card(200, "Beta")])
        self.add_rule_profile()
        snapshots = {EDISON: "2010-04-24", TENGU: "2011-09-17"}
        shutil.rmtree(self.root / "formats", ignore_errors=True)
        for format_id in format_ids:
            self.add_format(id=format_id, period={"start": "2010-03-01", "end": None, "snapshot": snapshots[format_id]})
        self.write(
            "data/sources.json",
            {
                "sources": [
                    {"id": "test-source", "kind": "other", "title": "Test source", "url": "https://example.invalid"},
                    {"id": "test-ude-ruling", "kind": "official", "title": "A UDE card FAQ", "ruling_class": "ude-era-ruling"},
                    {"id": "test-konami-list", "kind": "official", "title": "A Konami errata list", "ruling_class": "konami-document"},
                ]
            },
        )
        return self.add_erratum_v2(
            id="erratum-beta",
            classification=classification,
            events=events if events is not None else {"e1": self._event(kind="functional", date="2012-09-29")},
            states=states
            if states is not None
            else [{"events": [], "coverage": {"kind": "known-gap", "gap_reason": "none", "gap_sources": ["test-source"]}}],
            **kw,
        )

    @staticmethod
    def _event(kind="functional", date="2012-09-29", **transition):
        return v2_event(
            effective={"date": date, "precision": "day", "status": "reported", "basis": "a printing"},
            transitions=[v2_transition(kind=kind, summary="Beta lost its use limit.", **transition)],
        )

    def _codes(self):
        return _codes(_validate(self.root))

    def _decided(self, **changes):
        base = dict(
            in_force="by-decision",
            in_force_basis="Owner decision 2026-09-29 (docs/state.md): UDE-era rulings count at the snapshots.",
            later_konami_replacement="none-found",
            later_documents_checked=["test-konami-list"],
        )
        base.update(changes)
        return _finding(**base)

    # -- when a check is required ----------------------------------------------

    def test_a_functional_transition_after_the_snapshot_needs_a_check(self):
        self._seed()
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors | warnings)

    def test_the_finding_is_an_error_not_a_warning(self):
        # Round 037 introduced the rule as a warning and made it an error once every record in
        # scope carried a check. It stays an error: a record added without a check fails the build.
        self._seed()
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors)
        self.assertNotIn("erratum.rulings-check-missing", warnings)

    def test_an_undated_functional_transition_applies_and_needs_a_check(self):
        self._seed(events={"e1": self._event(date=None)})
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors | warnings)

    def test_a_transition_already_in_effect_at_every_gate_snapshot_needs_none(self):
        self._seed(events={"e1": self._event(date="2009-01-01")})
        errors, warnings = self._codes()
        self.assertNotIn("erratum.rulings-check-missing", errors | warnings)

    def test_a_transition_between_the_two_snapshots_applies_at_edison_only_and_still_needs_one(self):
        self._seed(events={"e1": self._event(date="2010-10-15")}, format_ids=(EDISON, TENGU))
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors | warnings)
        self._seed(events={"e1": self._event(date="2010-10-15")}, format_ids=(TENGU,))
        errors, warnings = self._codes()
        self.assertNotIn("erratum.rulings-check-missing", errors | warnings)

    def test_only_a_functional_transition_needs_one(self):
        for kind in ("cosmetic", "ruling", "engine"):
            with self.subTest(kind=kind):
                self._seed(
                    events={"e1": self._event(kind=kind)},
                    classification=kind,
                    states=[] if kind in ("cosmetic", "engine") else None,
                )
                errors, warnings = self._codes()
                self.assertNotIn("erratum.rulings-check-missing", errors | warnings)

    def test_a_format_that_is_not_a_gate_format_asks_for_nothing(self):
        self._seed(format_ids=())
        self.add_format(id="2005-04-test")
        errors, warnings = self._codes()
        self.assertNotIn("erratum.rulings-check-missing", errors | warnings)

    def test_citing_a_ruling_source_does_not_excuse_a_transition(self):
        # A ruling cited for another point does not say which rulings were searched for this one.
        self._seed(events={"e1": self._event(sources=["test-source", "test-ude-ruling"])})
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors | warnings)

    def test_only_the_three_transitions_rounds_035_and_036_checked_are_exempt(self):
        self.assertEqual(
            {
                ("erratum-dark-necrofear", "c2"),
                ("erratum-fushioh-richie", "event"),
                ("erratum-second-coin-toss", "event"),
            },
            set(ERRATUM_RULINGS_GATE_EXEMPT),
        )
        self._seed()
        with mock.patch("retroformats.validate.ERRATUM_RULINGS_GATE_EXEMPT", frozenset({("erratum-beta", "e1")})):
            errors, warnings = self._codes()
        self.assertNotIn("erratum.rulings-check-missing", errors | warnings)

    def test_a_transition_a_generated_card_implements_is_covered_by_the_cards_check(self):
        # The card's own `rulings_check` covers the transition it implements, so the record is not
        # asked twice. Read through the gate method with a card that names this record.
        self._seed()
        validator = Validator(Repository.load(self.root))
        erratum = validator.repo.errata["erratum-beta"]
        validator._check_erratum_rulings(erratum)
        self.assertIn("erratum.rulings-check-missing", {f.code for f in validator.findings})
        validator.findings.clear()
        validator.repo.custom_cards[600000001] = types.SimpleNamespace(erratum="erratum-beta")
        validator._check_erratum_rulings(erratum)
        self.assertEqual([], validator.findings)

    def test_a_check_on_the_flattened_single_event_shape_is_read_too(self):
        record = self._seed()
        event = record["events"]["e1"]
        sugar = {
            "id": "erratum-beta",
            "modern_card": {"passcode": 200, "name": "Beta"},
            "classification": "functional",
            "event": {"effective": event["effective"], **event["transitions"][0]},
            "coverage": record["states"][0]["coverage"],
            "review": {"status": "reviewed"},
            "sources": ["test-source"],
        }
        self.write("data/errata/beta.json", sugar)
        errors, warnings = self._codes()
        self.assertIn("erratum.rulings-check-missing", errors | warnings)
        sugar["event"]["rulings_check"] = _check()
        self.write("data/errata/beta.json", sugar)
        errors, warnings = self._codes()
        self.assertNotIn("erratum.rulings-check-missing", errors | warnings)
        sugar["event"]["rulings_check"] = _check(_finding(finding="maybe"))
        self.write("data/errata/beta.json", sugar)
        errors, _ = self._codes()
        self.assertIn("erratum.rulings-check-malformed", errors)

    # -- what a check must say (the shared body) -------------------------------

    def _with_check(self, check, **kw):
        event = self._event()
        event["transitions"][0]["rulings_check"] = check
        return self._seed(events={"e1": event}, **kw)

    def test_a_well_formed_check_clears_the_finding(self):
        self._with_check(_check())
        errors, warnings = self._codes()
        self.assertEqual(set(), errors)
        self.assertNotIn("erratum.rulings-check-missing", warnings)

    def test_a_malformed_check_is_refused(self):
        for name, check in (
            ("a string", "checked"),
            ("no difference", _check(difference=None)),
            ("no date", _check(checked=None)),
            ("an empty search", _check(searched=[])),
            ("no looked_for", _check(_finding(looked_for=None))),
            ("a finding outside the closed set", _check(_finding(finding="partly supports"))),
            ("supports with no passage", _check(_finding(passage=None))),
            ("shown with no basis", _check(_finding(in_force_basis=None))),
            ("in_force outside the closed set", _check(_finding(in_force="probably"))),
        ):
            with self.subTest(check=name):
                self._with_check(check)
                errors, _ = self._codes()
                self.assertIn("erratum.rulings-check-malformed", errors)

    def test_a_search_that_found_nothing_is_a_complete_record(self):
        self._with_check(_check(_finding(finding="does-not-address", passage=None, in_force=None, in_force_basis=None)))
        errors, warnings = self._codes()
        self.assertEqual(set(), errors)

    def test_a_searched_source_must_be_registered(self):
        self._with_check(_check(_finding(source="not-a-source")))
        errors, _ = self._codes()
        self.assertIn("sources.unresolved", errors)

    def test_a_contradicting_ruling_in_force_needs_an_owner_decision(self):
        contradicting = _finding(finding="contradicts")
        self._with_check(_check(contradicting))
        errors, _ = self._codes()
        self.assertIn("erratum.contradicting-ruling-unaccepted", errors)
        decision = {"date": "2026-10-01", "decision": "Keep it.", "recorded_in": "docs/state.md"}
        self._with_check(_check(contradicting, owner_decision=decision))
        errors, _ = self._codes()
        self.assertEqual(set(), errors)

    def test_a_contradicting_ruling_whose_range_is_not_shown_is_a_tracked_warning(self):
        self._with_check(_check(_finding(finding="contradicts", in_force="not-shown", in_force_basis=None)))
        errors, warnings = self._codes()
        self.assertEqual(set(), errors)
        self.assertIn("erratum.contradicting-ruling-range-unresolved", warnings)

    def test_the_owners_decision_on_which_rulings_count_is_accepted_with_its_conditions(self):
        self._with_check(_check(self._decided()))
        errors, _ = self._codes()
        self.assertEqual(set(), errors)
        for name, changes, code in (
            ("a source that is not a UDE-era ruling", dict(source="test-konami-list"), "erratum.decision-source-not-ude"),
            ("no replacement statement", dict(later_konami_replacement=None), "erratum.decision-later-documents-missing"),
            ("no documents checked", dict(later_documents_checked=None), "erratum.decision-later-documents-missing"),
            (
                "documents checked that are not Konami documents",
                dict(later_documents_checked=["test-ude-ruling"]),
                "erratum.decision-document-not-konami",
            ),
        ):
            with self.subTest(case=name):
                self._with_check(_check(self._decided(**changes)))
                errors, _ = self._codes()
                self.assertIn(code, errors)

    def test_a_contradicting_ruling_in_force_by_decision_still_needs_an_owner_decision(self):
        self._with_check(_check(self._decided(finding="contradicts")))
        errors, _ = self._codes()
        self.assertIn("erratum.contradicting-ruling-unaccepted", errors)

    def test_a_cosmetic_transition_may_carry_the_check_that_made_it_cosmetic(self):
        # Round 037 reclassifies a transition cosmetic because a ruling in force contradicts the difference it
        # claimed. Its check keeps that finding as the evidence; the transition claims nothing a ruling contradicts.
        contradicting = _check(_finding(finding="contradicts"))
        event = self._event(kind="cosmetic")
        event["transitions"][0]["rulings_check"] = contradicting
        self._seed(events={"e1": event}, classification="cosmetic", states=[])
        errors, warnings = self._codes()
        self.assertNotIn("erratum.contradicting-ruling-unaccepted", errors)
        self.assertNotIn("erratum.contradicting-ruling-range-unresolved", warnings)
        # The same finding on a transition that still claims a difference is refused.
        self._with_check(contradicting)
        errors, _ = self._codes()
        self.assertIn("erratum.contradicting-ruling-unaccepted", errors)
        # and the check is still validated on a cosmetic transition
        event["transitions"][0]["rulings_check"] = _check(_finding(finding="partly"))
        self._seed(events={"e1": event}, classification="cosmetic", states=[])
        errors, _ = self._codes()
        self.assertIn("erratum.rulings-check-malformed", errors)

    def test_the_two_records_share_one_body_and_only_the_code_prefix_differs(self):
        # `Validator._check_rulings_body` is the generated cards' check and the errata records'
        # check at once: the same finding values, in_force values and owner_decision rules.
        from retroformats.validate import Validator as V

        self.assertTrue(callable(V._check_rulings_body))
        self.assertIn("prefix", V._check_rulings_body.__code__.co_varnames)


class LiveErratumRulingsGateTest(unittest.TestCase):
    """The gate on the repository's own records."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)
        cls.validator = Validator(cls.repo)
        cls.validator.validate()
        cls.exempt = ERRATUM_RULINGS_GATE_EXEMPT

    def _independent_scope(self):
        """The transitions in scope, re-derived from the raw JSON with no use of the validator:
        (a) `functional`, (b) not one of the three that rounds 035 and 036 checked (they cite a ruling
        source), (c) not yet in effect at Edison's snapshot (or undated), (d) on a record no generated
        card implements."""
        linked = {
            json.loads(p.read_text(encoding="utf-8"))["erratum"]
            for p in (REPO_ROOT / "data" / "custom-cards").glob("*.json")
        }
        scope = {}
        for path in sorted((REPO_ROOT / "data" / "errata").glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw["id"] in linked:
                continue
            events = (
                [("event", raw["event"]["effective"], [raw["event"]])]
                if "event" in raw
                else [(k, e["effective"], e["transitions"]) for k, e in raw["events"].items()]
            )
            hits = [
                (event_id, transition)
                for event_id, effective, transitions in events
                for transition in transitions
                if transition["kind"] == "functional"
                and (raw["id"], event_id) not in self.exempt
                and change_state_at({"effective": effective}, EDISON_SNAPSHOT) != "new"
            ]
            if hits:
                scope[path.stem] = hits
        return scope

    def test_every_record_in_scope_carries_a_check_on_each_transition(self):
        missing = [f for f in self.validator.findings if f.code == "erratum.rulings-check-missing"]
        self.assertEqual([], missing, "\n".join(map(str, missing[:10])))
        for stem, hits in self._independent_scope().items():
            for event_id, transition in hits:
                with self.subTest(record=stem, event=event_id):
                    self.assertIsInstance(transition.get("rulings_check"), dict)

    def test_no_finding_of_the_gate_is_left_in_the_repository(self):
        codes = {f.code for f in self.validator.findings}
        self.assertEqual(set(), {c for c in codes if c.startswith("erratum.") and ("rulings" in c or "decision" in c)} - {"erratum.contradicting-ruling-range-unresolved"})

    def test_the_independent_scope_is_the_one_the_gate_uses(self):
        """The gate reads the transitions; this test reads the files. They must select the same
        transitions: remove every check in memory and compare."""
        scope = self._independent_scope()
        gated = {}
        for erratum in self.repo.errata.values():
            if not hasattr(erratum, "events"):
                continue
            for event_id, event in erratum.events.items():
                for transition in event.transitions:
                    if (
                        transition.kind == "functional"
                        and (erratum.id, event_id) not in self.exempt
                        and event.state_at(EDISON_SNAPSHOT) != "new"
                        and not any(c.erratum == erratum.id for c in self.repo.custom_cards.values())
                    ):
                        gated.setdefault(erratum.path.stem, []).append(event_id)
        self.assertEqual(
            {stem: sorted(event_id for event_id, _ in hits) for stem, hits in scope.items()},
            {stem: sorted(ids) for stem, ids in gated.items()},
        )


if __name__ == "__main__":
    unittest.main()
