import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repacker", ROOT / "scripts/repack_reviewed.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReleaseAssets(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(m.safe_name(r"docs\安装说明.md"), "docs/安装说明.md")
        for bad in ("../x", "/tmp/x", r"C:\x", "a//b", "a/../b", "x:stream", "CON.txt", "a./b"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                m.safe_name(bad)

    def test_duplicate_windows_names(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("Docs/a", "1")
                z.writestr(r"docs\A", "2")
            with zipfile.ZipFile(p) as z, self.assertRaises(ValueError):
                m.index_zip(z)

    def test_checksum_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("a.txt", b"ok")
                z.writestr("SHA256SUMS.txt", hashlib.sha256(b"ok").hexdigest()+"  a.txt\n")
            self.assertIn("a.txt", m.verify_zip(p))
            with zipfile.ZipFile(p, "a") as z:
                z.writestr("extra", b"x")
            with self.assertRaises(ValueError):
                m.verify_zip(p)

    def test_overlays(self):
        for n, p in m.OVERLAYS.items():
            self.assertFalse(n.startswith(("bin/", "src/", "tests/")))
            self.assertTrue((ROOT / p).is_file())

    def test_metadata(self):
        v = json.loads((ROOT / "release-files/RELEASE-METADATA.json").read_text())
        self.assertEqual(v["program_version"], "1.2.0")
        self.assertEqual(v["contract_version"], "response_flow/1.1")
        self.assertEqual(v["windows_upgrade_validation"], "NOT_RUN")
        self.assertFalse(v["binary_recompiled"])
        self.assertEqual(v["download_url"], "")

    def test_install_prompt(self):
        t = (ROOT / "docs/接入提示词.md").read_text(encoding="utf-8")
        self.assertIn("--install-user --json", t)
        self.assertIn("--configure-workbuddy --json", t)
        self.assertNotIn("response authorize --confirm-scope", t)
        self.assertIn("metadata_refresh_required", t)
        self.assertIn("conflict", t)

    def test_csv(self):
        t = (ROOT / "docs/使用说明.md").read_text(encoding="utf-8")
        h = next(x for x in t.splitlines() if x.startswith("response_id,freight_id,"))
        self.assertEqual(len(h.split(",")), 30)
        self.assertEqual(len(set(h.split(","))), 30)

    def test_skill(self):
        t = (ROOT / "skills/jc-response-preview/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(t.startswith("---\n"))
        self.assertIn("response_flow/1.1", t)
        self.assertIn("version: 1.2.0", t)
        self.assertNotIn("latest 5", t)
        self.assertNotIn("读取最近 5 条", t)

    def test_wrong_input(self):
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d)/"wrong.zip", Path(d)/"out.zip"
            p.write_bytes(b"wrong")
            with self.assertRaises(ValueError):
                m.repack(p, q, ROOT)
            self.assertFalse(q.exists())


if __name__ == "__main__":
    unittest.main()
