"""Offline safeguards for presentation and byte-identical Skill packaging."""
from __future__ import annotations
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pack_setup_skill import SKILL, archive_bytes, check_examples, get_version, load_manifest, pack, sha256, validate
from sync_setup_references import sync
from import_reviewed_icon import import_icon


class SkillPresentation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "skills", self.root / "skills")
        self.skill = self.root / "skills/jc-response-setup"
        self.manifest = load_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def test_version_and_three_examples(self):
        self.assertEqual(get_version(), "0.2.3")
        check_examples((SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def test_four_examples_fail(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "examples_zh"):
            check_examples(text.replace("examples_en:", "- fourth forbidden\nexamples_en:", 1))

    def test_text_sources_match_reviewed_manifest(self):
        for item in self.manifest["files"]:
            if item["line_endings"] != "binary":
                archive_bytes(self.skill, item)

    def test_runtime_unchanged(self):
        data = (SKILL / "references/runtime-pin.json").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(sha256(data), "6d4c5ca55cd0385de4a90efae8317e1cd9f8bd19f2a2d3bdbdbaf39592eb37cc")

    def test_missing_icon_fails_pack(self):
        (self.skill / "references/market-icon.png").unlink(missing_ok=True)
        with self.assertRaises(ValueError):
            pack(self.root / "bad.zip", self.skill, self.manifest)
        self.assertFalse((self.root / "bad.zip").exists())

    def test_missing_reference_fails(self):
        (self.skill / "references/product-notes.md").unlink()
        with self.assertRaises(ValueError):
            validate(self.skill, self.manifest)

    def test_modified_installer_fails(self):
        item = next(x for x in self.manifest["files"] if x["path"] == "scripts/setup-windows.ps1")
        path = self.skill / item["path"]
        path.write_bytes(path.read_bytes() + b"\n# changed\n")
        with self.assertRaises(ValueError):
            archive_bytes(self.skill, item)

    @unittest.skipUnless((SKILL / "references/market-icon.png").is_file(), "Original PNG upload pending; complete-package validation not passed")
    def test_sync_idempotent_and_version_derived(self):
        source_map = self.skill / "references/source-map.json"
        before = source_map.read_bytes()
        sync(self.root)
        self.assertEqual(before, source_map.read_bytes())
        p = self.skill / "SKILL.md"
        p.write_text(p.read_text(encoding="utf-8").replace("version: 0.2.3", "version: 0.2.4", 1), encoding="utf-8")
        sync(self.root)
        data = json.loads(source_map.read_text(encoding="utf-8"))
        self.assertEqual(data["skill_version"], "0.2.4")
        self.assertFalse(data["presentation_update"]["market_submitted"])

    @unittest.skipUnless((SKILL / "references/market-icon.png").is_file(), "Original PNG upload pending; complete-package validation not passed")
    def test_exact_zip_and_icon_import(self):
        target = pack(self.root / "approved.zip", self.skill, self.manifest)
        self.assertEqual(target.stat().st_size, 234614)
        self.assertEqual(sha256(target.read_bytes()), "a86a58a26831e60a05247797cde92c78ea1543faf2c8e0145b4786d73ae70e42")
        with self.assertRaises(FileExistsError):
            pack(target, self.skill, self.manifest)
        (self.skill / "references/market-icon.png").unlink()
        self.assertEqual(import_icon(target, self.skill, self.manifest), "imported")
        self.assertEqual(import_icon(target, self.skill, self.manifest), "already_present")

    def test_unknown_zip_refused(self):
        path = self.root / "wrong.zip"
        path.write_bytes(b"unknown")
        with self.assertRaises(ValueError):
            import_icon(path, self.skill, self.manifest)


if __name__ == "__main__":
    unittest.main()
