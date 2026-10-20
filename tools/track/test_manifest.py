"""Unit tests of the evidence manifest's disposition lines (tools/track/manifest.py):
python3 -I -m unittest discover -s tools/track -p 'test_manifest.py'"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest  # noqa: E402


class DispositionLinesTest(unittest.TestCase):
    LINES = [
        "## Dispositions",
        "",
        "| kind | side | s (m) | what | source | disposition |",
        "|---|---|---|---|---|---|",
        "| mast | right | 111.2 | light mast | onboard:X@4.0 | not resolvable: no base on c20_s1870 |",
        "| stand | left | 3966.6 | main grandstand | onboard:X@134.0 | placed: Main grandstand (23 m along) |",
        "| station | left | 3511.2 | marshal at a door | onboard:X@116.0 | rejected: a person (onboard 1:56, t116) |",
        "| building | right | 3258.9 | tan buildings | onboard:X@110.0 | assigned: buildings round |",
        # not disposition lines: a generated outcome table (s first), a survey table, prose, a non-numeric station
        "| 111 | 0:04.0 | right | mast | light mast | onboard:X@4.0 | MISSING, placed: Light masts |",
        "| S/F, 5MY4x | concrete walls both sides | placed (rows: pit straight walls) | c20_s1595 |",
        "placed: not a table row",
        "| mast | right | near T1 | light mast | onboard | not resolvable: c20_s1870 |",
        "| mast | right | 120 | light mast | onboard | covered by structure 15 |",
    ]

    def test_parses_only_disposition_rows(self):
        d = manifest.parse_dispositions(self.LINES)
        self.assertEqual([(x["kind"], x["side"], x["s"], x["type"]) for x in d], [
            ("mast", "right", 111.2, "not resolvable"), ("stand", "left", 3966.6, "placed"),
            ("station", "left", 3511.2, "rejected"), ("building", "right", 3258.9, "assigned")])
        self.assertEqual(d[1]["text"], "Main grandstand (23 m along)")
        self.assertEqual(d[3]["text"], "buildings round")
        self.assertEqual(d[0]["what"], "light mast")

    def test_types_are_the_gate_types(self):
        self.assertEqual(manifest.DISPOSITION_TYPES, ("placed", "assigned", "rejected", "not resolvable"))

    def test_missing_manifest_is_empty(self):
        self.assertEqual(manifest.manifest_dispositions("no_such_track_for_tests"), [])

    def test_sonoma_manifest_disposes_30_rows(self):
        # 31 when the gate was written (4fce076); round 7f placed the T7a island-nose delineator, so its "not resolvable"
        # line went (the coverage gate passed with 0 missing rows in the 3fa66ae8a4 publish run). The count tracks the
        # manifest: a placed object loses its line, a new MISSING row gains one.
        if not os.path.exists(manifest.manifest_path("sonoma")):
            self.skipTest("no Sonoma manifest")
        d = manifest.manifest_dispositions("sonoma")
        self.assertEqual(len(d), 30)
        self.assertTrue(all(x["text"] for x in d))


if __name__ == "__main__":
    unittest.main()
