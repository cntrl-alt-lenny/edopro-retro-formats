"""Generation and validation of this project's own historical cards
(roadmap item 7, round 029): data/custom-cards/, dist/databases/, dist/scripts/.

Two halves. The first runs the real generator against the real canonical data
and pins what a client will find in dist/: rows, scripts, identity, and the
Edison list using them, with GOAT and Tengu untouched. The second builds tiny
synthetic repositories to prove each validator rule fires, and that the
stale-output guard fails when a generated script or row is missing or stale.
"""

from __future__ import annotations

import copy
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from retroformats.custom_cards import (
    CDB_NAME,
    build_cdb_bytes,
    build_custom_cards,
    cards_sorted,
    expected_outputs,
    read_cdb_rows,
    stale_generated_files,
)
from retroformats.lflist import build_lflist
from retroformats.model import RESERVED_PASSCODE_RANGE, STATUS_TO_COUNT
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import REPO_ROOT, TempRepoTest, card, change

EDISON = "2010-03-edison"
GOAT_HASH = 0x28E9FC02


def _validate(root):
    validator = Validator(Repository.load(root))
    validator.validate()
    return validator


def _error_codes(validator):
    return {f.code for f in validator.errors}


class LiveGeneratedOutputTest(unittest.TestCase):
    """The committed dist/ against the committed canonical data."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)
        cls.cards = cards_sorted(cls.repo)
        cls.dist = REPO_ROOT / "dist"

    def test_this_round_implements_exactly_two_cards(self):
        self.assertEqual(
            [
                (600000001, "erratum-metalzoa"),
                (600000002, "erratum-super-vehicroid-stealth-union"),
            ],
            [(c.passcode, c.erratum) for c in self.cards],
        )

    def test_dist_holds_exactly_the_generated_databases_and_scripts(self):
        self.assertEqual([], stale_generated_files(self.repo, self.dist))

    def test_every_generated_script_is_the_canonical_script_byte_for_byte(self):
        for c in self.cards:
            with self.subTest(passcode=c.passcode):
                generated = (self.dist / "scripts" / f"c{c.passcode}.lua").read_bytes()
                canonical = (REPO_ROOT / c.script).read_bytes()
                self.assertEqual(canonical.replace(b"\r\n", b"\n"), generated)
                self.assertTrue(generated.strip())

    def test_database_rows_alias_the_modern_card_and_are_never_official_scope(self):
        rows = read_cdb_rows(self.dist / "databases" / CDB_NAME)
        self.assertEqual({c.passcode for c in self.cards}, set(rows))
        for c in self.cards:
            with self.subTest(passcode=c.passcode):
                row = rows[c.passcode]
                modern = self.repo.errata[c.erratum].modern_card
                self.assertEqual(modern.passcode, row["alias"])
                self.assertEqual(8, row["ot"], "SCOPE_ILLEGAL: playable only through a whitelist")
                self.assertEqual(c.name, row["name"])
                self.assertEqual(c.desc, row["desc"])
                for key in ("type", "atk", "def", "level", "race", "attribute", "setcode", "category"):
                    self.assertEqual(c.cdb[key], row[key], key)
                self.assertIn(c.passcode, RESERVED_PASSCODE_RANGE)

    def test_database_file_bytes_do_not_depend_on_the_sqlite_that_wrote_them(self):
        # Header fields 24 (change counter), 92 (version-valid-for) and 96
        # (SQLITE_VERSION_NUMBER) are the only ones that vary with the library
        # version; the generator pins them so build --check is stable across
        # the Python/SQLite pairs CI and a developer's machine use.
        data = build_cdb_bytes(self.cards)
        self.assertEqual(data, build_cdb_bytes(self.cards), "deterministic for equal input")
        self.assertEqual(b"\x00\x00\x00\x01", data[24:28])
        self.assertEqual(b"\x00\x00\x00\x01", data[92:96])
        self.assertEqual(b"\x00\x00\x00\x00", data[96:100])
        self.assertEqual(data, (self.dist / "databases" / CDB_NAME).read_bytes())

    def test_database_opens_as_a_bare_babelcdb_layout(self):
        con = sqlite3.connect(f"file:{self.dist / 'databases' / CDB_NAME}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual({"datas", "texts"}, tables)
            datas = [r[1] for r in con.execute("PRAGMA table_info(datas)")]
            self.assertEqual(
                ["id", "ot", "alias", "setcode", "type", "atk", "def", "level", "race", "attribute", "category"],
                datas,
            )
            texts = [r[1] for r in con.execute("PRAGMA table_info(texts)")]
            self.assertEqual(["id", "name", "desc"] + [f"str{i}" for i in range(1, 17)], texts)
        finally:
            con.close()

    def test_edison_list_uses_each_historical_card_instead_of_the_modern_one(self):
        fmt = self.repo.formats[EDISON]
        built = build_lflist(fmt, self.repo)
        banlist = self.repo.banlists[fmt.banlist_id]
        status_by_code = {e.card.passcode: e.status for e in banlist.entries}
        for c in self.cards:
            with self.subTest(passcode=c.passcode):
                modern = self.repo.errata[c.erratum].modern_card.passcode
                self.assertIn(c.passcode, built.entries)
                self.assertNotIn(modern, built.entries, "the modern card would behave incorrectly")
                # Deck limits: the whitelist follows an alias only within +/-10,
                # so the historical code is listed itself, with the modern
                # card's own count. In a duel and when counting copies the row
                # is its modern card via `alias` (see the engine test).
                expected = STATUS_TO_COUNT.get(status_by_code.get(modern, ""), 3)
                self.assertEqual(expected, built.entries[c.passcode])

    def test_goat_and_tengu_do_not_use_any_generated_card(self):
        generated = {c.passcode for c in self.cards}
        for fmt_id in ("2005-04-goat", "2011-09-tengu"):
            with self.subTest(format=fmt_id):
                built = build_lflist(self.repo.formats[fmt_id], self.repo)
                self.assertEqual(set(), generated & set(built.entries))
        # The two cards' modern codes are exactly what those two lists used
        # before this round. Night Assailant is not generated (it is held
        # back, roadmap item 7), and GOAT keeps its Project Ignis variant.
        goat = build_lflist(self.repo.formats["2005-04-goat"], self.repo)
        self.assertEqual(GOAT_HASH, goat.hash)
        self.assertIn(16226796, goat.entries)

    def test_generated_codes_are_indexed_and_identifiable(self):
        for c in self.cards:
            with self.subTest(passcode=c.passcode):
                self.assertEqual(c.name, self.repo.card_index.name_of(c.passcode))
                self.assertEqual(c.alias, self.repo.card_index.alias_of(c.passcode))

    def test_every_record_declares_original_authorship_and_its_approximations(self):
        for c in self.cards:
            with self.subTest(passcode=c.passcode):
                self.assertEqual("original", c.raw["authorship"]["kind"])
                self.assertEqual("approximate", c.fidelity)
                self.assertTrue(c.not_reproduced)


class StaleOutputGuardTest(unittest.TestCase):
    """build --check must catch a generated script or row that is missing or
    stale, and a file nothing claims. Uses a scratch copy of dist/."""

    def setUp(self):
        self.repo = Repository.load(REPO_ROOT)
        self.tmp = Path(tempfile.mkdtemp(prefix="retroformats-dist-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        shutil.copytree(REPO_ROOT / "dist", self.tmp / "dist")
        self.dist = self.tmp / "dist"

    def test_a_faithful_copy_is_clean(self):
        self.assertEqual([], stale_generated_files(self.repo, self.dist))

    def test_a_missing_script_is_reported(self):
        (self.dist / "scripts" / "c600000001.lua").unlink()
        self.assertEqual(["missing: dist/scripts/c600000001.lua"], stale_generated_files(self.repo, self.dist))

    def test_a_stale_script_is_reported(self):
        path = self.dist / "scripts" / "c600000002.lua"
        path.write_bytes(path.read_bytes() + b"--hand edit\n")
        self.assertEqual(["stale: dist/scripts/c600000002.lua"], stale_generated_files(self.repo, self.dist))

    def test_a_missing_database_is_reported(self):
        (self.dist / "databases" / CDB_NAME).unlink()
        self.assertEqual([f"missing: dist/databases/{CDB_NAME}"], stale_generated_files(self.repo, self.dist))

    def test_a_stale_row_is_reported(self):
        db = self.dist / "databases" / CDB_NAME
        con = sqlite3.connect(str(db))
        try:
            con.execute("UPDATE datas SET atk = atk + 1 WHERE id = 600000002")
            con.commit()
        finally:
            con.close()
        self.assertEqual([f"stale: dist/databases/{CDB_NAME}"], stale_generated_files(self.repo, self.dist))

    def test_an_unclaimed_script_is_reported_and_removed_by_a_rebuild(self):
        stray = self.dist / "scripts" / "c600000099.lua"
        stray.write_text("--nobody's\n")
        self.assertEqual(["unexpected: dist/scripts/c600000099.lua"], stale_generated_files(self.repo, self.dist))
        build_custom_cards(self.repo, self.dist)
        self.assertFalse(stray.exists())
        self.assertEqual([], stale_generated_files(self.repo, self.dist))

    def test_gitkeep_placeholders_are_not_stale(self):
        self.assertTrue((self.dist / "scripts" / ".gitkeep").exists())
        self.assertEqual([], stale_generated_files(self.repo, self.dist))

    def test_a_rebuild_restores_a_hand_edited_script(self):
        path = self.dist / "scripts" / "c600000001.lua"
        original = path.read_bytes()
        path.write_bytes(b"--tampered\n")
        build_custom_cards(self.repo, self.dist)
        self.assertEqual(original, path.read_bytes())

    def test_no_custom_cards_means_no_generated_files(self):
        empty = Path(tempfile.mkdtemp(prefix="retroformats-empty-"))
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        repo = copy.copy(self.repo)
        repo.custom_cards = {}
        self.assertEqual({}, expected_outputs(repo))
        self.assertEqual([], build_custom_cards(repo, empty))


class CustomCardValidationTest(TempRepoTest):
    """Each rule of _validate_custom_cards, and the reserved-range gate."""

    CODE = 600000001
    TEXT = "Old Beta text."

    def _seed(self, **overrides):
        record = {
            "passcode": self.CODE,
            "alias": 200,
            "erratum": "erratum-beta",
            "events": [],
            "name": "Beta (Retro Formats)",
            "desc": self.TEXT,
            "cdb": {
                "ot": 8,
                "setcode": 0,
                "type": 33,
                "atk": 1000,
                "def": 1000,
                "level": 4,
                "race": 1,
                "attribute": 1,
                "category": 0,
            },
            "script": f"data/custom-cards/c{self.CODE}.lua",
            "authorship": {"kind": "original", "note": "written from the text"},
            "fidelity": "approximate",
            "not_reproduced": ["timing is not established"],
            "sources": ["test-source"],
        }
        record.update(overrides)
        self.add_card_index([card(200, "Beta"), card(self.CODE, "Beta (Retro Formats)", alias_of=200, ot=8)])
        self.add_banlist(entries=[{"card": card(200, "Beta"), "status": "limited"}])
        self.add_pool(cards=[card(200, "Beta")])
        self.add_rule_profile()
        self.add_format()
        self.add_erratum(
            changes=[change(date="2006-01-01", historical_text=self.TEXT)],
            impl={
                "strategy": "custom-script",
                "historical_passcode": self.CODE,
                "script": record["script"],
                "status": "partial",
            },
        )
        self.write(f"data/custom-cards/c{self.CODE}.json", record)
        (self.root / "data" / "custom-cards" / f"c{self.CODE}.lua").write_text("--script\n", encoding="utf-8")
        return record

    def test_a_well_formed_custom_card_validates_cleanly(self):
        self._seed()
        validator = _validate(self.root)
        self.assertEqual([], validator.errors, "\n".join(map(str, validator.errors)))

    def test_the_reserved_range_still_rejects_a_custom_script_with_no_record(self):
        self._seed()
        (self.root / "data" / "custom-cards" / f"c{self.CODE}.json").unlink()
        self.assertIn("card.reserved-passcode-collision", _error_codes(_validate(self.root)))

    def test_the_reserved_range_still_rejects_reuse_upstream_even_with_a_record(self):
        self._seed()
        self.add_erratum(
            changes=[change(date="2006-01-01", historical_text=self.TEXT)],
            impl={"strategy": "reuse-upstream", "historical_passcode": self.CODE, "status": "complete"},
        )
        self.assertIn("card.reserved-passcode-collision", _error_codes(_validate(self.root)))

    def test_the_reserved_range_still_rejects_a_pool_entry(self):
        self._seed()
        self.add_pool(cards=[card(200, "Beta"), card(self.CODE, "Beta (Retro Formats)")])
        self.assertIn("card.reserved-passcode-collision", _error_codes(_validate(self.root)))

    def test_passcode_outside_the_reserved_range_fails(self):
        self._seed(passcode=511000123, script="data/custom-cards/c511000123.lua")
        (self.root / "data" / "custom-cards" / f"c{self.CODE}.json").rename(
            self.root / "data" / "custom-cards" / "c511000123.json"
        )
        self.assertIn("custom-card.bad-passcode", _error_codes(_validate(self.root)))

    def test_record_file_must_be_named_for_its_passcode(self):
        self._seed()
        path = self.root / "data" / "custom-cards" / f"c{self.CODE}.json"
        path.rename(path.with_name("c600000777.json"))
        self.assertIn("custom-card.bad-filename", _error_codes(_validate(self.root)))

    def test_unknown_erratum_fails(self):
        self._seed(erratum="erratum-nope")
        self.assertIn("custom-card.unknown-erratum", _error_codes(_validate(self.root)))

    def test_alias_must_be_the_errata_modern_card(self):
        self._seed(alias=300)
        self.assertIn("custom-card.alias-mismatch", _error_codes(_validate(self.root)))

    def test_a_record_no_coverage_claims_is_an_orphan(self):
        self._seed()
        self.add_erratum(
            changes=[change(date="2006-01-01", historical_text=self.TEXT)],
            impl={"strategy": "none-needed", "status": "complete"},
        )
        self.assertIn("custom-card.orphan", _error_codes(_validate(self.root)))

    def test_text_must_be_a_text_the_erratum_record_carries(self):
        self._seed(desc="A text typed a second time.")
        self.assertIn("custom-card.text-not-in-record", _error_codes(_validate(self.root)))

    def test_the_cdb_row_must_never_be_official_scope(self):
        record = self._seed()
        record["cdb"]["ot"] = 3
        self.write(f"data/custom-cards/c{self.CODE}.json", record)
        self.assertIn("custom-card.bad-cdb", _error_codes(_validate(self.root)))

    def test_the_cdb_row_needs_integer_fields(self):
        record = self._seed()
        record["cdb"]["atk"] = "3000"
        self.write(f"data/custom-cards/c{self.CODE}.json", record)
        self.assertIn("custom-card.bad-cdb", _error_codes(_validate(self.root)))

    def test_the_script_must_exist_at_its_canonical_path(self):
        self._seed()
        (self.root / "data" / "custom-cards" / f"c{self.CODE}.lua").unlink()
        self.assertIn("custom-card.script-missing", _error_codes(_validate(self.root)))

    def test_the_script_path_is_fixed(self):
        self._seed(script="dist/scripts/c600000001.lua")
        self.assertIn("custom-card.bad-script-path", _error_codes(_validate(self.root)))

    def test_an_approximate_script_must_say_where(self):
        self._seed(not_reproduced=[])
        self.assertIn("custom-card.approximation-undisclosed", _error_codes(_validate(self.root)))

    def test_an_exact_script_must_not_claim_gaps(self):
        self._seed(fidelity="exact")
        self.assertIn("custom-card.approximation-undisclosed", _error_codes(_validate(self.root)))

    def test_fidelity_is_a_closed_set(self):
        self._seed(fidelity="close enough")
        self.assertIn("custom-card.bad-fidelity", _error_codes(_validate(self.root)))

    def test_a_derived_script_is_not_something_a_record_may_assert(self):
        self._seed(authorship={"kind": "derived", "note": "adapted from Project Ignis"})
        self.assertIn("custom-card.authorship-not-original", _error_codes(_validate(self.root)))

    def test_missing_authorship_fails(self):
        record = self._seed()
        del record["authorship"]
        self.write(f"data/custom-cards/c{self.CODE}.json", record)
        self.assertIn("custom-card.authorship-not-original", _error_codes(_validate(self.root)))

    def test_sources_must_resolve(self):
        self._seed(sources=["nope"])
        self.assertIn("sources.unresolved", _error_codes(_validate(self.root)))

    def test_the_card_index_row_must_agree_with_the_record(self):
        self._seed()
        self.add_card_index(
            [card(200, "Beta"), card(self.CODE, "Some other name", alias_of=200, ot=8)]
        )
        self.assertIn("custom-card.index-mismatch", _error_codes(_validate(self.root)))

    def test_duplicate_passcode_fails_to_load(self):
        self._seed()
        record = self._seed()
        self.write("data/custom-cards/c600000001-copy.json", record)
        codes = {f.code for f in _validate(self.root).errors}
        self.assertIn("load.failed", codes)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
