"""Migration restore and install-acceptance checks. No live WorkBuddy config."""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate_workbuddy_custom.ps1"
LAUNCHER_SOURCE = ROOT / "connector" / "launch" / "Program.cs"
EXE_SHA = "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d"


def nest(depth):
    node = {"level": depth}
    for value in range(depth - 1, 0, -1):
        node = {"level": value, "next": node}
    return node


class MigrationRestore(unittest.TestCase):
    def setUp(self):
        self.base = Path(os.environ["TEMP"]) / "jc-response-migrate-test"
        if self.base.exists():
            shutil.rmtree(self.base)
        local = self.base / "Local"
        official = local / "Programs" / "JC_response" / "bin" / "jctrans-mcp.exe"
        official.parent.mkdir(parents=True)
        official.write_bytes(b"official-identity")
        self.official = str(official)
        self.env = os.environ.copy()
        self.env["LOCALAPPDATA"] = str(local)
        self.env["USERPROFILE"] = str(self.base / "Profile")
        Path(self.env["USERPROFILE"]).mkdir()
        self.deep = nest(12)

    def write_config(self, name, payload):
        path = self.base / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def invoke(self, path, *args):
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(SCRIPT), "-ConfigPath", str(path), *args],
            env=self.env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        text = (completed.stdout + completed.stderr).decode("utf-8", "replace")
        return completed.returncode, text, json.loads(path.read_text(encoding="utf-8"))

    def official_entry(self):
        return {"type": "stdio", "command": self.official, "args": []}

    def base_config(self):
        return {
            "schema": "keep-me",
            "ui": {"panels": [{"id": "main", "flags": {"nested": self.deep}}]},
            "mcpServers": {
                "jc-response": self.official_entry(),
                "scys-mcp": {"type": "stdio", "command": "C:\\Other\\scys.exe", "args": ["keep"], "env": {"NEST": self.deep}},
            },
        }

    def test_restore_keeps_later_servers_and_nested_fields(self):
        path = self.write_config("mcp.json", self.base_config())
        code, text, removed = self.invoke(path, "-Confirm")
        self.assertEqual(code, 0, text)
        self.assertNotIn("jc-response", removed["mcpServers"])
        self.assertEqual(removed["ui"]["panels"][0]["flags"]["nested"], self.deep)
        self.assertEqual(removed["mcpServers"]["scys-mcp"]["env"]["NEST"], self.deep)
        removed["mcpServers"]["extra"] = {"type": "stdio", "command": "C:\\Other\\extra.exe", "env": {"NEST": self.deep}}
        removed["mcpServers"]["scys-mcp"]["args"] = ["keep", "changed-after-backup"]
        path.write_text(json.dumps(removed), encoding="utf-8")
        backup = next(path.parent.glob("mcp.json.bak-*"))
        code, text, restored = self.invoke(path, "-Confirm", "-Restore", str(backup))
        self.assertEqual(code, 0, text)
        self.assertEqual(restored["mcpServers"]["jc-response"]["command"], self.official)
        self.assertEqual(restored["mcpServers"]["jc-response"]["args"], [])
        self.assertEqual(restored["mcpServers"]["scys-mcp"]["args"], ["keep", "changed-after-backup"])
        self.assertEqual(restored["mcpServers"]["extra"]["env"]["NEST"], self.deep)
        self.assertEqual(restored["ui"]["panels"][0]["flags"]["nested"], self.deep)

    def test_conflict_unknown_source_and_live_config_do_not_write(self):
        path = self.write_config("mcp.json", self.base_config())
        self.invoke(path, "-Confirm")
        backup = next(path.parent.glob("mcp.json.bak-*"))
        current = json.loads(path.read_text(encoding="utf-8"))
        current["mcpServers"]["jc-response"] = {"type": "stdio", "command": self.official, "args": ["different"]}
        current["mcpServers"]["extra"] = {"type": "stdio", "command": "C:\\Other\\extra.exe"}
        path.write_text(json.dumps(current), encoding="utf-8")
        before = path.read_text(encoding="utf-8")
        code, text, after = self.invoke(path, "-Confirm", "-Restore", str(backup))
        self.assertEqual(code, 4, text)
        self.assertIn("conflict=target", text)
        self.assertEqual(after["mcpServers"]["jc-response"]["args"], ["different"])
        self.assertIn("extra", after["mcpServers"])
        self.assertEqual(path.read_text(encoding="utf-8"), before)

        unknown = self.write_config("unknown.json", {
            "mcpServers": {"jc-response": {"type": "stdio", "command": "C:\\NotOfficial\\jctrans-mcp.exe", "args": []},
                           "scys-mcp": {"args": ["stay"]}},
        })
        raw = unknown.read_text(encoding="utf-8")
        code, text, body = self.invoke(unknown, "-Confirm")
        self.assertEqual(code, 3, text)
        self.assertIn("unknown_source", text)
        self.assertEqual(unknown.read_text(encoding="utf-8"), raw)
        self.assertEqual(body["mcpServers"]["scys-mcp"]["args"], ["stay"])

        live = Path(self.env["USERPROFILE"]) / ".workbuddy" / "mcp.json"
        live.parent.mkdir()
        live.write_text(json.dumps(self.base_config()), encoding="utf-8")
        raw = live.read_text(encoding="utf-8")
        code, text, _body = self.invoke(live, "-Confirm")
        self.assertEqual(code, 2, text)
        self.assertEqual(live.read_text(encoding="utf-8"), raw)

    def test_concurrent_change_is_not_overwritten(self):
        path = self.base / "concurrent.json"
        path.write_text('{"schema":"original"}', encoding="utf-8")
        command = (
            f". '{SCRIPT}'\n"
            f"$original = [System.IO.File]::ReadAllText('{path}')\n"
            f"[System.IO.File]::WriteAllText('{path}', '{{\"schema\":\"newer\"}}')\n"
            f"$result = Write-MarketConfigIfUnchanged '{path}' $original '{{\"schema\":\"stale-write\"}}'\n"
            "Write-Output $result\n"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            env=self.env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        text = (completed.stdout + completed.stderr).decode("utf-8", "replace")
        self.assertIn("concurrent", text)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema"], "newer")


class InstallAcceptance(unittest.TestCase):
    def launcher(self):
        out = Path(os.environ["TEMP"]) / "jc-response-launch-test.exe"
        csc = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
        if not csc.is_file():
            self.skipTest("csc unavailable")
        compiled = subprocess.run(
            [str(csc), "/nologo", "/optimize+", "/target:exe", f"/out:{out}",
             "/r:System.IO.Compression.dll", "/r:System.IO.Compression.FileSystem.dll",
             "/r:System.Web.Extensions.dll", str(LAUNCHER_SOURCE)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
        self.assertEqual(compiled.returncode, 0, compiled.stderr.decode("utf-8", "replace"))
        return out

    def fixture(self, exe_bytes, version="1.2.0", schema="response_flow/1.1"):
        base = Path(os.environ["TEMP"]) / "jc-response-install-judge"
        if base.exists():
            shutil.rmtree(base)
        program = base / "Programs" / "JC_response"
        (program / "bin").mkdir(parents=True)
        (program / "bin" / "jctrans-mcp.exe").write_bytes(exe_bytes)
        (program / "VERSION").write_text(f"version={version}\nschema={schema}\n", encoding="utf-8")
        env = os.environ.copy()
        env["LOCALAPPDATA"] = str(base)
        return program, env

    def evaluate(self, exe, env, exit_code, status):
        pin = exe.parent / "runtime-pin.json"
        shutil.copyfile(ROOT / "connector" / "runtime-pin.json", pin)
        completed = subprocess.run(
            [str(exe), "--evaluate-install-result", str(exit_code), status],
            env=env, cwd=str(exe.parent), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        return completed.returncode, completed.stderr.decode("utf-8", "replace")

    def test_judgement_requires_exit_status_and_files(self):
        source = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "JC_response" / "bin" / "jctrans-mcp.exe"
        if not source.is_file():
            self.skipTest("installed runtime is not available for the hash fixture")
        exe = self.launcher()
        program, env = self.fixture(source.read_bytes())
        code, text = self.evaluate(exe, env, 3, "installed")
        self.assertEqual(code, 2, text)
        self.assertIn("install_rejected", text)
        self.assertNotIn("install_verified", text)
        code, text = self.evaluate(exe, env, 0, "target_in_use")
        self.assertEqual(code, 2, text)
        self.assertIn("install_rejected", text)
        code, text = self.evaluate(exe, env, 0, "unreadable")
        self.assertEqual(code, 2, text)
        self.assertIn("install_rejected", text)
        (program / "bin" / "jctrans-mcp.exe").write_bytes(b"mismatch")
        code, text = self.evaluate(exe, env, 0, "installed")
        self.assertEqual(code, 2, text)
        self.assertIn("install_rejected", text)
        (program / "bin" / "jctrans-mcp.exe").unlink()
        code, text = self.evaluate(exe, env, 0, "installed")
        self.assertEqual(code, 2, text)
        self.assertIn("install_rejected", text)
        program, env = self.fixture(source.read_bytes())
        code, text = self.evaluate(exe, env, 0, "installed")
        self.assertEqual(code, 0, text)
        self.assertIn("install_verified", text)
        self.assertEqual(EXE_SHA, __import__("hashlib").sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
