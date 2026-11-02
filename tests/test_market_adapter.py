"""Static checks for the WorkBuddy connector source. No network and no live config."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ZIP_SHA = "91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713"
EXE_SHA = "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d"
DOWNLOAD = "https://github.com/bobbanga/jc-response/releases/download/v1.2.0-r1/JC_response-windows-x64-1.2.0-r1.zip"


class MarketAdapter(unittest.TestCase):
    def test_connector_metadata(self):
        meta = json.loads((ROOT / "connector/connector-meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["source"], "jc-response")
        self.assertEqual(meta["type"], "mcp")
        self.assertEqual(meta["name_en"], "JC Response Assistant")
        self.assertEqual(meta["version"], "1.0.0")
        self.assertNotEqual(meta["version"], "1.2.0")
        self.assertEqual(meta["minWorkbuddyVersion"], "4.24.0")
        self.assertNotIn("preAuth", meta)
        self.assertNotIn("auth_mode", meta)
        self.assertIn("Windows", meta["description_en"])
        self.assertIn("未签名", meta["description_zh"])

    def test_mcp_uses_proven_stdio_fields_only(self):
        mcp = json.loads((ROOT / "connector/mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(set(mcp), {"$schema", "mcpServers"})
        self.assertEqual(set(mcp["mcpServers"]), {"jc-response"})
        server = mcp["mcpServers"]["jc-response"]
        self.assertEqual(set(server), {"type", "command", "args"})
        self.assertEqual(server["type"], "stdio")
        self.assertEqual(server["command"], "./jc-response-launch.exe")
        self.assertEqual(server["args"], [])

    def test_plugin_manifest_name_is_safe(self):
        plugin = json.loads((ROOT / "connector/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "jc-response")
        self.assertNotIn("--", plugin["name"])
        self.assertTrue(plugin["$schema"].endswith("plugin.schema.json"))

    def test_runtime_pin_matches_release(self):
        pin = json.loads((ROOT / "connector/runtime-pin.json").read_text(encoding="utf-8"))
        self.assertEqual(pin["download_url"], DOWNLOAD)
        self.assertEqual(pin["file_size"], 122270089)
        self.assertEqual(pin["sha256"], ZIP_SHA)
        self.assertEqual(pin["exe_sha256"], EXE_SHA)
        self.assertEqual(pin["contract"], "response_flow/1.1")

    def test_launcher_does_not_configure_or_invent_a_url(self):
        text = (ROOT / "connector/launch/Program.cs").read_text(encoding="utf-8")
        self.assertIn(DOWNLOAD, text)
        self.assertIn(ZIP_SHA, text)
        self.assertNotIn("--configure-workbuddy", text)
        self.assertNotIn("preAuth", text)
        self.assertNotIn("-executionpolicy bypass", text.casefold())

    def test_icon_is_local_svg(self):
        text = (ROOT / "connector/icon.svg").read_text(encoding="utf-8").casefold()
        self.assertIn("<svg", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("https://", text)
        self.assertEqual(text.count("http://"), 1)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', text)

    def test_skill_keeps_the_product_contract(self):
        text = (ROOT / "skills/jc-response-preview/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("response_flow/1.1", text)
        self.assertIn("不要再执行 `--configure-workbuddy`", text)
        self.assertIn("不要调用全局 `jctrans`", text)
        self.assertNotIn("c:\\users\\hiabo", text.casefold())


if __name__ == "__main__":
    unittest.main()
