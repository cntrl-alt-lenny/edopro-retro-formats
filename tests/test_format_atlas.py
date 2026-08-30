import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "format-library-catalog.json"
PROGRESS = ROOT / "docs" / "format-atlas-progress.json"
SVG = ROOT / "docs" / "assets" / "format-atlas.svg"
BANNER = ROOT / "docs" / "assets" / "format-banner.svg"
GENERATOR = ROOT / "scripts" / "generate_format_atlas.py"
NS = {"svg": "http://www.w3.org/2000/svg"}


class FormatAtlasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
        cls.root = ET.parse(SVG).getroot()
        cls.banner_root = ET.parse(BANNER).getroot()
        cls.tiles = cls.root.findall(".//svg:g[@class='format']", NS)
        cls.tiles_by_id = {int(tile.attrib["data-format-id"]): tile for tile in cls.tiles}
        cls.banner_tiles = cls.banner_root.findall(".//svg:g[@class='format']", NS)
        cls.banner_tiles_by_id = {int(tile.attrib["data-format-id"]): tile for tile in cls.banner_tiles}

    def test_catalog_is_complete_unique_and_chronological(self):
        formats = self.catalog["formats"]
        self.assertEqual(self.catalog["count"], len(formats))
        self.assertEqual(len(formats), len({item["id"] for item in formats}))
        self.assertEqual({item["category"] for item in formats}, {"TCG", "OCG"})
        self.assertEqual(
            {item["era"] for item in formats},
            {"DM", "GX", "5D's", "ZEXAL", "ARC-V", "VRAINS", "SEVENS", "GO RUSH!!"},
        )
        dated = [item["date"] for item in formats if item["date"]]
        self.assertEqual(dated, sorted(dated))
        first_undated = next((index for index, item in enumerate(formats) if not item["date"]), len(formats))
        self.assertTrue(all(not item["date"] for item in formats[first_undated:]))

    def test_every_catalog_entry_is_rendered_exactly_once_in_the_atlas(self):
        expected = {item["id"] for item in self.catalog["formats"]}
        self.assertEqual(len(self.tiles), len(expected))
        self.assertEqual(set(self.tiles_by_id), expected)

    def test_banner_spotlights_only_formats_that_have_started(self):
        # The banner is a hero, not a second copy of the atlas: it must show
        # exactly the formats with real progress (canonical or research) and
        # nothing else, however large the catalog grows.
        canonical_ids = {8, 20, 24}
        research_ids = {int(item_id) for item_id in self.progress["formats"]}
        expected_active = canonical_ids | research_ids
        self.assertEqual(len(self.banner_tiles), len(expected_active))
        self.assertEqual(set(self.banner_tiles_by_id), expected_active)
        for item_id, tile in self.banner_tiles_by_id.items():
            with self.subTest(format_library_id=item_id):
                self.assertIn(tile.attrib["data-kind"], {"canonical", "research"})

    def test_banner_never_renders_a_placeholder_tile(self):
        # Regression guard for the wall-of-placeholders design the banner
        # deliberately moved away from: an untouched format must never get
        # its own box in the banner, only in the full atlas below the fold.
        for tile in self.banner_tiles:
            with self.subTest(format_library_id=tile.attrib["data-format-id"]):
                self.assertNotEqual(tile.attrib["data-kind"], "planned")

    def test_banner_era_coverage_counts_are_accurate(self):
        canonical_ids = {8, 20, 24}
        research_ids = {int(item_id) for item_id in self.progress["formats"]}
        active_ids = canonical_ids | research_ids
        by_era_name: dict[str, list] = {}
        for item in self.catalog["formats"]:
            by_era_name.setdefault(item["era"], []).append(item)

        eras = self.banner_root.findall(".//svg:g[@class='era']", NS)
        expected_eras = {"DM", "GX", "5D's", "ZEXAL", "ARC-V", "VRAINS", "SEVENS", "GO RUSH!!"}
        self.assertEqual({era_el.attrib["data-era"] for era_el in eras}, expected_eras)
        for era_el in eras:
            era = era_el.attrib["data-era"]
            with self.subTest(era=era):
                items = by_era_name.get(era, [])
                expected_active = sum(1 for item in items if item["id"] in active_ids)
                self.assertEqual(int(era_el.attrib["data-total"]), len(items))
                self.assertEqual(int(era_el.attrib["data-active"]), expected_active)

    def test_canonical_progress_is_read_from_format_records(self):
        expected = {
            8: "2005-04-goat",
            20: "2010-03-edison",
            24: "2011-09-tengu",
        }
        for format_library_id, format_id in expected.items():
            with self.subTest(format_id=format_id):
                record = json.loads((ROOT / "formats" / format_id / "format.json").read_text(encoding="utf-8"))
                for tiles_by_id in (self.tiles_by_id, self.banner_tiles_by_id):
                    tile = tiles_by_id[format_library_id]
                    self.assertEqual(tile.attrib["data-kind"], "canonical")
                    self.assertEqual(tile.attrib["data-banlist"], record["implementation_status"]["banlist"])
                    self.assertEqual(tile.attrib["data-card-pool"], record["implementation_status"]["card_pool"])
                    self.assertEqual(tile.attrib["data-rule-profile"], record["implementation_status"]["rule_profile"])
                    self.assertEqual(tile.attrib["data-errata"], record["implementation_status"]["errata"])

    def test_research_progress_is_explicit_and_does_not_claim_canonical_status(self):
        canonical_ids = {8, 20, 24}
        research_ids = {int(item_id) for item_id in self.progress["formats"]}
        self.assertTrue(canonical_ids.isdisjoint(research_ids))
        for item_id in research_ids:
            for tiles_by_id in (self.tiles_by_id, self.banner_tiles_by_id):
                tile = tiles_by_id[item_id]
                self.assertEqual(tile.attrib["data-kind"], "research")
        tokyo_dome = self.tiles_by_id[135]
        self.assertEqual(tokyo_dome.attrib["data-format-name"], "Tokyo Dome")
        self.assertEqual(
            {
                tokyo_dome.attrib["data-banlist"],
                tokyo_dome.attrib["data-card-pool"],
                tokyo_dome.attrib["data-rule-profile"],
                tokyo_dome.attrib["data-errata"],
            },
            {"research"},
        )

    def test_every_untracked_format_is_honestly_not_started(self):
        tracked = {8, 20, 24, *[int(item_id) for item_id in self.progress["formats"]]}
        for item_id, tile in self.tiles_by_id.items():
            if item_id in tracked:
                continue
            with self.subTest(format_library_id=item_id):
                self.assertEqual(tile.attrib["data-kind"], "planned")
                self.assertEqual(
                    {
                        tile.attrib["data-banlist"],
                        tile.attrib["data-card-pool"],
                        tile.attrib["data-rule-profile"],
                        tile.attrib["data-errata"],
                    },
                    {"missing"},
                )

    def test_checked_in_svg_is_fresh(self):
        completed = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_readme_uses_compact_banner_and_detailed_atlas(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            'href="https://github.com/cntrl-alt-lenny/edopro-retro-formats/raw/refs/heads/main/docs/assets/format-banner.svg"',
            readme,
        )
        self.assertIn('src="docs/assets/format-banner.svg" width="960"', readme)
        self.assertIn('src="docs/assets/format-atlas.svg" width="960"', readme)
        self.assertIn('Open the full-size detailed atlas', readme)


if __name__ == "__main__":
    unittest.main()
