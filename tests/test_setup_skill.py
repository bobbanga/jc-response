"""Setup skill tests. Windows integration needs explicitly supplied offline fixtures."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import textwrap
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/jc-response-setup"
SCRIPT = SKILL / "scripts/setup-windows.ps1"
SOURCE = ROOT / "skills/jc-response-preview/SKILL.md"
PIN = json.loads((SKILL / "references/runtime-pin.json").read_text(encoding="utf-8"))


def run_ps(command: str, env: dict | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    for key in ("JC_TOKEN", "JC_JCB_TOKEN", "JC_PASSWORD", "JC_USERNAME", "HTTPS_PROXY", "https_proxy"):
        merged.pop(key, None)
    if env:
        merged.update(env)
    return subprocess.run(["powershell", "-NoProfile", "-Command", command], cwd=ROOT, env=merged,
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def isolated(name: str) -> dict[str, str]:
    base = Path(os.environ["TEMP"]) / "jc-response-setup-test" / name
    if base.exists():
        shutil.rmtree(base)
    local = base / "Local"
    for path in (local, base / "Roaming", base / "Temp", base / "Home"):
        path.mkdir(parents=True)
    return {"USERPROFILE": str(base / "Home"), "HOME": str(base / "Home"), "LOCALAPPDATA": str(local),
            "APPDATA": str(base / "Roaming"), "TEMP": str(base / "Temp"), "TMP": str(base / "Temp")}


def run_file(args: list[str], env: dict | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    for key in ("JC_TOKEN", "JC_JCB_TOKEN", "JC_PASSWORD", "JC_USERNAME", "JC_RESPONSE_HOME", "JC_RESPONSE_DATA_DIR", "HTTPS_PROXY", "https_proxy"):
        merged.pop(key, None)
    if env:
        merged.update(env)
    return subprocess.run(["powershell", "-NoProfile", "-File", str(SCRIPT), *args], cwd=ROOT, env=merged,
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def dot(expression: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return run_ps(f". '{SCRIPT}'; {expression}", env)


def test_names_and_generated_rules() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "display_name: JC回盘助手" in text and "display_name_en: JC Response Assistant" in text
    assert "name: jc-response-setup" in text and "version: 0.2.3" in text
    assert "平台审核状态分别记录" in text and "allowed-tools:" not in text
    for name in ("business-rules.md", "first-use.md", "prompt-examples.md", "upgrade-and-troubleshooting.md", "runtime-pin.json", "source-map.json", "product-notes.md"):
        assert (SKILL / "references" / name).is_file()
    rules = (SKILL / "references/business-rules.md").read_text(encoding="utf-8")
    assert rules.count("---\n") == 1 and "name: jc-response-preview" not in rules
    body = SOURCE.read_text(encoding="utf-8").split("\n---\n", 1)[1].lstrip("\n")
    assert rules.endswith(body)
    mapping = json.loads((SKILL / "references/source-map.json").read_text(encoding="utf-8"))
    assert mapping["business_rules_source_sha256"] == hashlib.sha256(SOURCE.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert mapping["business_rules_source_commit"] == "feat/business-csv-rules"
    assert "JC_response_business/1.0" in rules and "1.2.0-r1" in rules
    assert "本资料修订对应程序 1.3.0" in rules and "程序版本仍为 1.2.0" not in rules
    assert PIN["program_version"] == "1.3.0" and PIN["csv_schema"] == "JC_response_business/1.0"
    assert PIN["contract"] == "response_flow/1.1" and PIN["published"] is True
    assert PIN["release_tag"] == "v1.3.0-r2" and PIN["package_revision"] == "r2"
    assert PIN["file_name"] == "JC_response-windows-x64-1.3.0-r2.zip"
    assert PIN["download_url"] == "https://github.com/bobbanga/jc-response/releases/download/v1.3.0-r2/JC_response-windows-x64-1.3.0-r2.zip"
    assert PIN["sha256"] == "747a62e46af7177cb6364461f7edc776a0797652e3e423570109b3da7c47f9c9"
    assert PIN["file_size"] == 122402084
    predecessor = PIN["supported_upgrades"][0]
    assert predecessor["program_version"] == "1.2.0" and predecessor["csv_schema"] == "JC_response/1.1"
    assert predecessor["exe_sha256"] == "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d"
    assert PIN["exe_sha256"] == "5a65927202043b605c48019ae552b110612c68600b745fb33af14764de4e9ff3"
    assert mapping["skill_version"] == "0.2.3" and mapping["review_ready"] is False and mapping["published_download"] is True
    script = SCRIPT.read_text(encoding="utf-8").casefold()
    assert "taskkill" not in script and "stop-process" not in script and "runas" not in script
    assert "inquiry-response assistant" not in text


def test_teach_and_boundaries() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    examples = (SKILL / "references/prompt-examples.md").read_text(encoding="utf-8")
    rules = (SKILL / "references/business-rules.md").read_text(encoding="utf-8")
    assert "不检查整台电脑，不下载" in text and "带我学习" in text
    assert "不自动读取" in examples and "inquiry-response assistant" in rules
    assert "不要默认 20" in rules and "不补抓" in examples
    assert "continuation_id" in examples and examples.count("## ") >= 6


def test_zip_and_classification(tmp: Path) -> None:
    bad = tmp / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("../outside.txt", "no")
    result = dot(f"if (Test-ZipSafe '{bad}') {{ 'safe' }} else {{ 'rejected' }}")
    assert result.returncode == 0 and "rejected" in result.stdout, result.stdout + result.stderr
    dup = tmp / "dup.zip"
    with zipfile.ZipFile(dup, "w") as z:
        z.writestr("bin/A.txt", "a"); z.writestr("bin/a.txt", "b")
    assert "rejected" in dot(f"if (Test-ZipSafe '{dup}') {{ 'safe' }} else {{ 'rejected' }}").stdout
    link = tmp / "link.zip"
    with zipfile.ZipFile(link, "w") as z:
        info = zipfile.ZipInfo("bin/link"); info.external_attr = 0xA1FF0000; z.writestr(info, "target")
    assert "rejected" in dot(f"if (Test-ZipSafe '{link}') {{ 'safe' }} else {{ 'rejected' }}").stdout
    program = tmp / "program"; binary = program / "bin"; binary.mkdir(parents=True)
    data = b"official-bytes"; sha = hashlib.sha256(data).hexdigest()
    for name in PIN["exe_names"]:
        (binary / name).write_bytes(data)
    version = program / "VERSION"; version.write_text("version=1.2.0\nschema=response_flow/1.1\n", encoding="utf-8")
    sums = program / "SHA256SUMS.txt"
    sums.write_text("\n".join([f"{sha}  bin/{n}" for n in PIN["exe_names"]] + [hashlib.sha256(version.read_bytes()).hexdigest() + "  VERSION"]) + "\n", encoding="utf-8")
    pin = f"$pin = @{{ program_version='1.2.0'; contract='response_flow/1.1'; exe_sha256='{sha}'; sums_sha256='{hashlib.sha256(sums.read_bytes()).hexdigest()}'; exe_names=@('JC_response.exe','jctrans.exe','jctrans-mcp.exe') }}; "
    assert dot(pin + f"Get-ProgramClass '{program}' $pin").stdout.strip().endswith("match")
    (binary / "jctrans-mcp.exe").write_bytes(b"other")
    assert dot(pin + f"Get-ProgramClass '{program}' $pin").stdout.strip().endswith("different_binary")
    version.write_text("version=9.9.9\nschema=response_flow/1.1\n", encoding="utf-8")
    assert dot(pin + f"Get-ProgramClass '{program}' $pin").stdout.strip().endswith("higher_version")


def test_isolated_actions() -> None:
    env = isolated("actions"); home = Path(env["USERPROFILE"])
    old = home / ".workbuddy/skills/jctrans-response-assistant"; old.mkdir(parents=True)
    (old / "SKILL.md").write_text("use inquiry-response assistant\n", encoding="utf-8")
    result = run_file(["-Action", "inspect"], env)
    assert result.returncode == 0 and "class=absent" in result.stdout and "downloaded=0" in result.stdout
    assert "old_skill=dev_command" in result.stdout and (old / "SKILL.md").is_file()
    data = Path(env["LOCALAPPDATA"]) / "JC_response"; data.mkdir(); (data / "sentinel.txt").write_bytes(b"sentinel-v1")
    result = run_file(["-Action", "install"], env)
    assert result.returncode == 2 and "consent=required" in result.stdout and "downloaded=0" in result.stdout
    assert (data / "sentinel.txt").read_bytes() == b"sentinel-v1"
    program = Path(env["LOCALAPPDATA"]) / "Programs/JC_response"; program.mkdir(parents=True)
    (program / "VERSION").write_text("version=9.9.9\nschema=other\n", encoding="utf-8")
    result = run_file(["-Action", "install", "-Confirm"], env)
    assert result.returncode == 4 and "class=higher_version" in result.stdout and "downloaded=0" in result.stdout
    config = home / ".workbuddy/mcp.json"; config.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps({"theme": "kept", "mcpServers": {"scys-mcp": {"type": "stdio", "command": "C:\\Other\\scys.exe", "env": {"nested": {"keep": True}}}, "jc-response": {"type": "stdio", "command": "C:\\Unknown\\jctrans-mcp.exe", "args": []}}}, ensure_ascii=False)
    config.write_text(original, encoding="utf-8")
    result = run_file(["-Action", "configure", "-Confirm"], env)
    assert result.returncode == 5 and "config=conflict" in result.stdout and config.read_text(encoding="utf-8") == original
    denied = env.copy(); denied["OS"] = "Other"
    result = run_file(["-Action", "inspect"], denied)
    assert result.returncode == 3 and "platform=unsupported" in result.stdout


def test_docs_and_config_helpers(tmp: Path) -> None:
    extract = tmp / "docs-case/extract"; program = tmp / "docs-case/program"
    for root in (extract, program):
        (root / "bin").mkdir(parents=True); (root / "docs").mkdir()
        (root / "bin/same.dll").write_bytes(b"same"); (root / "bin/sentinel.dll").write_bytes(b"keep")
    (extract / "docs/安装说明.md").write_text("new", encoding="utf-8")
    target = program / "docs/安装说明.md"; target.write_text("old", encoding="utf-8")
    pin = "$pin = @{ doc_files = @('docs/安装说明.md') }; "
    result = dot(pin + f"Update-DocWhitelist '{extract}' '{program}' $pin")
    assert result.stdout.strip().endswith("docs_refreshed"), result.stdout + result.stderr
    assert target.read_text(encoding="utf-8") == "new"
    assert (program / "bin/same.dll").read_bytes() == b"same" and (program / "bin/sentinel.dll").read_bytes() == b"keep"
    handle = open(target, "rb")
    try:
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close(); handle = None
    if handle is not None:
        try:
            (extract / "docs/安装说明.md").write_text("newer", encoding="utf-8")
            assert "docs_locked" in dot(pin + f"Update-DocWhitelist '{extract}' '{program}' $pin").stdout
        finally:
            handle.close()
        assert target.read_text(encoding="utf-8") == "new"
    official = str(program / "bin/jctrans-mcp.exe"); config = tmp / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"jc-response": {"type": "stdio", "command": official, "args": []}}}), encoding="utf-8")
    assert dot(f"Get-ConfigPlan '{config}' '{official}'").stdout.strip().endswith("reuse")
    config.write_text("{", encoding="utf-8")
    assert dot(f"Get-ConfigPlan '{config}' '{official}'").stdout.strip().endswith("invalid")


def test_reviewed_upgrade_keeps_sentinels() -> None:
    # Explicit fixtures replace a developer-specific ZIP path and live installation copy.
    package = Path(os.environ["JC_RESPONSE_REVIEWED_RUNTIME_ZIP"])
    predecessor_dir = Path(os.environ["JC_RESPONSE_REVIEWED_PREDECESSOR_DIR"])
    assert hashlib.sha256(package.read_bytes()).hexdigest() == PIN["sha256"] and package.stat().st_size == PIN["file_size"]
    predecessor = PIN["supported_upgrades"][0]
    hashes = {n: hashlib.sha256((predecessor_dir / "bin" / n).read_bytes()).hexdigest() for n in predecessor["exe_names"]}
    assert set(hashes.values()) == {predecessor["exe_sha256"]} and not list(predecessor_dir.rglob("*.db"))
    env = isolated("upgrade"); program = Path(env["LOCALAPPDATA"]) / "Programs/JC_response"
    shutil.copytree(predecessor_dir, program)
    data = Path(env["LOCALAPPDATA"]) / "JC_response"; (data / "auth").mkdir(parents=True); (data / "state").mkdir()
    export = data / "accounts/synthetic/exports"; export.mkdir(parents=True)
    (data / "auth/sentinel.bin").write_bytes(b"synthetic-auth")
    (data / "state/budget-sentinel.txt").write_text("synthetic-budget", encoding="utf-8")
    (export / "sentinel.csv").write_text("synthetic-not-a-real-response\n", encoding="utf-8")
    config = Path(env["USERPROFILE"]) / ".workbuddy/mcp.json"; config.parent.mkdir(parents=True)
    original = {"theme": "kept", "mcpServers": {"scys-mcp": {"type": "stdio", "command": "C:\\Other\\scys.exe", "env": {"nested": {"keep": True}}}, "jc-response": {"type": "stdio", "command": "C:\\Old\\jctrans-mcp.exe", "args": []}}}
    config.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
    def held() -> None:
        assert (data / "auth/sentinel.bin").read_bytes() == b"synthetic-auth"
        assert (data / "state/budget-sentinel.txt").read_text(encoding="utf-8") == "synthetic-budget"
        assert (export / "sentinel.csv").read_text(encoding="utf-8") == "synthetic-not-a-real-response\n"
        current = json.loads(config.read_text(encoding="utf-8"))
        assert current["theme"] == "kept" and current["mcpServers"]["scys-mcp"] == original["mcpServers"]["scys-mcp"]
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(package)], env, timeout=900)
    assert result.returncode == 0, result.stdout + result.stderr
    for message in ("class=supported_upgrade", "install_status=upgraded", "install_judged=verified", "downloaded=0"):
        assert message in result.stdout
    version = (program / "VERSION").read_text(encoding="utf-8")
    assert "version=1.3.0" in version and "csv_schema=JC_response_business/1.0" in version
    assert hashlib.sha256((program / "bin/JC_response.exe").read_bytes()).hexdigest() == PIN["exe_sha256"]
    held()
    guide = program / "docs/使用说明.md"; before_doc = guide.read_bytes(); before_exe = (program / "bin/JC_response.exe").read_bytes()
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(package)], env, timeout=180)
    assert result.returncode == 0 and "class=match" in result.stdout and "install=reused" in result.stdout and "downloaded=0" in result.stdout
    assert guide.read_bytes() == before_doc and (program / "bin/JC_response.exe").read_bytes() == before_exe
    guide.write_bytes(before_doc + "\n<!-- synthetic marker -->\n".encode("utf-8"))
    result = run_file(["-Action", "refresh-docs", "-Confirm", "-PackagePath", str(package)], env, timeout=900)
    assert result.returncode == 0 and "docs=docs_refreshed" in result.stdout and guide.read_bytes() == before_doc
    assert (program / "bin/JC_response.exe").read_bytes() == before_exe
    held()
    absent = isolated("bad-package"); rejected = Path(absent["TEMP"]) / "not-the-package.zip"; rejected.write_bytes(b"not-the-reviewed-package")
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(rejected)], absent, timeout=180)
    assert result.returncode == 3 and "download=local_rejected" in result.stdout
    assert not (Path(absent["LOCALAPPDATA"]) / "Programs/JC_response").exists()
    unknown = isolated("unknown-source"); unknown_program = Path(unknown["LOCALAPPDATA"]) / "Programs/JC_response"
    (unknown_program / "bin").mkdir(parents=True)
    (unknown_program / "VERSION").write_text("version=1.2.0\nschema=response_flow/1.1\ncsv_schema=JC_response/1.1\n", encoding="utf-8")
    for name in predecessor["exe_names"]:
        (unknown_program / "bin" / name).write_bytes(b"unreviewed-bytes")
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(package)], unknown, timeout=180)
    assert result.returncode == 4 and "class=unknown" in result.stdout and "downloaded=0" in result.stdout
    assert (unknown_program / "bin/JC_response.exe").read_bytes() == b"unreviewed-bytes"
    held()
    assert hashes["JC_response.exe"] == hashlib.sha256((predecessor_dir / "bin/JC_response.exe").read_bytes()).hexdigest()


class SetupSkill(unittest.TestCase):
    def test_text_contract(self) -> None:
        test_names_and_generated_rules(); test_teach_and_boundaries()

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell"), "Windows PowerShell required; NOT_RUN outside Windows")
    def test_candidate_package(self) -> None:
        tmp = Path(os.environ["TEMP"]) / "jc-response-setup-test/fixtures"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        test_zip_and_classification(tmp); test_isolated_actions(); test_docs_and_config_helpers(tmp)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell") and os.environ.get("JC_RESPONSE_REVIEWED_RUNTIME_ZIP") and os.environ.get("JC_RESPONSE_REVIEWED_PREDECESSOR_DIR"), "Explicit offline upgrade fixtures required; never read the live install")
    def test_reviewed_upgrade(self) -> None:
        test_reviewed_upgrade_keeps_sentinels()


if __name__ == "__main__":
    unittest.main()
