"""Checks for the JC回盘助手 setup skill. No live profile and no real JC calls."""

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
SKILL = ROOT / "skills" / "jc-response-setup"
SCRIPT = SKILL / "scripts" / "setup-windows.ps1"
SOURCE = ROOT / "skills" / "jc-response-preview" / "SKILL.md"
PIN = json.loads((SKILL / "references" / "runtime-pin.json").read_text(encoding="utf-8"))


def run_ps(command: str, env: dict | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    for key in ("JC_TOKEN", "JC_JCB_TOKEN", "JC_PASSWORD", "JC_USERNAME", "HTTPS_PROXY", "https_proxy"):
        merged.pop(key, None)
    if env:
        merged.update(env)
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=ROOT,
        env=merged,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def isolated(name: str) -> dict[str, str]:
    base = Path(os.environ["TEMP"]) / "jc-response-setup-test" / name
    if base.exists():
        shutil.rmtree(base)
    local = base / "Local"
    for path in (local, base / "Roaming", base / "Temp", base / "Home"):
        path.mkdir(parents=True)
    return {
        "USERPROFILE": str(base / "Home"),
        "HOME": str(base / "Home"),
        "LOCALAPPDATA": str(local),
        "APPDATA": str(base / "Roaming"),
        "TEMP": str(base / "Temp"),
        "TMP": str(base / "Temp"),
    }


def run_file(args: list[str], env: dict | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    for key in (
        "JC_TOKEN",
        "JC_JCB_TOKEN",
        "JC_PASSWORD",
        "JC_USERNAME",
        "JC_RESPONSE_HOME",
        "JC_RESPONSE_DATA_DIR",
        "HTTPS_PROXY",
        "https_proxy",
    ):
        merged.pop(key, None)
    if env:
        merged.update(env)
    return subprocess.run(
        ["powershell", "-NoProfile", "-File", str(SCRIPT), *args],
        cwd=ROOT,
        env=merged,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def dot(expression: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    command = f". '{SCRIPT}'; {expression}"
    return run_ps(command, env)


def test_names_and_generated_rules() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "display_name: JC回盘助手" in text
    assert "display_name_en: JC Response Assistant" in text
    assert "name: jc-response-setup" in text
    assert "version: 0.2.2" in text
    assert "尚未提交 WorkBuddy" in text
    assert "allowed-tools:" not in text
    for name in (
        "references/business-rules.md",
        "references/first-use.md",
        "references/prompt-examples.md",
        "references/upgrade-and-troubleshooting.md",
        "references/runtime-pin.json",
        "references/source-map.json",
    ):
        assert (SKILL / name).is_file()
    rules = (SKILL / "references" / "business-rules.md").read_text(encoding="utf-8")
    assert rules.count("---\n") == 1
    assert "name: jc-response-preview" not in rules
    body = SOURCE.read_text(encoding="utf-8")
    body = body.split("\n---\n", 1)[1].lstrip("\n")
    assert rules.endswith(body)
    source_map = json.loads((SKILL / "references" / "source-map.json").read_text(encoding="utf-8"))
    raw = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    assert source_map["business_rules_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert source_map["business_rules_source_commit"] == "feat/business-csv-rules"
    assert "JC_response_business/1.0" in rules
    assert "1.2.0-r1" in rules
    assert "本资料修订对应程序 1.3.0" in rules
    assert "程序版本仍为 1.2.0" not in rules
    assert PIN["program_version"] == "1.3.0"
    assert PIN["csv_schema"] == "JC_response_business/1.0"
    assert PIN["contract"] == "response_flow/1.1"
    assert PIN["download_url"] == "https://github.com/bobbanga/jc-response/releases/download/v1.3.0-r2/JC_response-windows-x64-1.3.0-r2.zip"
    assert PIN["published"] is True
    assert PIN["release_tag"] == "v1.3.0-r2"
    assert PIN["file_name"] == "JC_response-windows-x64-1.3.0-r2.zip"
    assert PIN["package_revision"] == "r2"
    assert PIN["sha256"] == "747a62e46af7177cb6364461f7edc776a0797652e3e423570109b3da7c47f9c9"
    assert PIN["file_size"] == 122402084
    predecessor = PIN["supported_upgrades"][0]
    assert predecessor["program_version"] == "1.2.0"
    assert predecessor["csv_schema"] == "JC_response/1.1"
    assert predecessor["exe_sha256"] == "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d"
    assert PIN["exe_sha256"] == "5a65927202043b605c48019ae552b110612c68600b745fb33af14764de4e9ff3"
    assert source_map["skill_version"] == "0.2.2"
    assert source_map["review_ready"] is False
    assert source_map["published_download"] is True
    script = SCRIPT.read_text(encoding="utf-8").casefold()
    assert "taskkill" not in script
    assert "stop-process" not in script
    assert "runas" not in script
    assert "inquiry-response assistant" not in (SKILL / "SKILL.md").read_text(encoding="utf-8")


def test_teach_and_boundaries() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    examples = (SKILL / "references" / "prompt-examples.md").read_text(encoding="utf-8")
    rules = (SKILL / "references" / "business-rules.md").read_text(encoding="utf-8")
    assert "不检查整台电脑，不下载" in skill
    assert "带我学习" in skill
    assert "不自动读取" in examples
    assert "inquiry-response assistant" in rules
    assert "不要默认 20" in rules
    assert "不补抓" in examples
    assert "continuation_id" in examples
    assert examples.count("## ") >= 6


def test_zip_and_classification(tmp: Path) -> None:
    bad = tmp / "bad.zip"
    with zipfile.ZipFile(bad, "w") as archive:
        archive.writestr("../outside.txt", "no")
    result = dot(f"if (Test-ZipSafe '{bad}') {{ 'safe' }} else {{ 'rejected' }}")
    assert result.returncode == 0, result.stderr
    assert "rejected" in result.stdout
    dup = tmp / "dup.zip"
    with zipfile.ZipFile(dup, "w") as archive:
        archive.writestr("bin/A.txt", "a")
        archive.writestr("bin/a.txt", "b")
    result = dot(f"if (Test-ZipSafe '{dup}') {{ 'safe' }} else {{ 'rejected' }}")
    assert "rejected" in result.stdout
    link = tmp / "link.zip"
    with zipfile.ZipFile(link, "w") as archive:
        info = zipfile.ZipInfo("bin/link")
        info.external_attr = 0xA1FF0000
        archive.writestr(info, "target")
    result = dot(f"if (Test-ZipSafe '{link}') {{ 'safe' }} else {{ 'rejected' }}")
    assert "rejected" in result.stdout
    program = tmp / "program"
    binary = program / "bin"
    binary.mkdir(parents=True)
    payload = b"official-bytes"
    digest = hashlib.sha256(payload).hexdigest()
    for name in PIN["exe_names"]:
        (binary / name).write_bytes(payload)
    version = program / "VERSION"
    version.write_text("version=1.2.0\nschema=response_flow/1.1\n", encoding="utf-8")
    sums = program / "SHA256SUMS.txt"
    lines = [f"{digest}  bin/{name}" for name in PIN["exe_names"]]
    lines.append(hashlib.sha256(version.read_bytes()).hexdigest() + "  VERSION")
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums_hash = hashlib.sha256(sums.read_bytes()).hexdigest()
    pin_literal = textwrap.dedent(f"""
        $pin = @{{
          program_version = '1.2.0'
          contract = 'response_flow/1.1'
          exe_sha256 = '{digest}'
          sums_sha256 = '{sums_hash}'
          exe_names = @('JC_response.exe','jctrans.exe','jctrans-mcp.exe')
        }}
    """)
    result = dot(pin_literal + f"Get-ProgramClass '{program}' $pin")
    assert result.stdout.strip().endswith("match"), result.stdout + result.stderr
    (binary / "jctrans-mcp.exe").write_bytes(b"other")
    result = dot(pin_literal + f"Get-ProgramClass '{program}' $pin")
    assert result.stdout.strip().endswith("different_binary"), result.stdout
    version.write_text("version=9.9.9\nschema=response_flow/1.1\n", encoding="utf-8")
    result = dot(pin_literal + f"Get-ProgramClass '{program}' $pin")
    assert result.stdout.strip().endswith("higher_version"), result.stdout


def test_isolated_actions() -> None:
    env = isolated("actions")
    home = Path(env["USERPROFILE"])
    skill = home / ".workbuddy" / "skills" / "jctrans-response-assistant"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("use inquiry-response assistant\n", encoding="utf-8")
    result = run_file(["-Action", "inspect"], env)
    assert result.returncode == 0, result.stderr
    assert "class=absent" in result.stdout
    assert "downloaded=0" in result.stdout
    assert "old_skill=dev_command" in result.stdout
    assert (skill / "SKILL.md").is_file()
    data = Path(env["LOCALAPPDATA"]) / "JC_response"
    data.mkdir()
    (data / "sentinel.txt").write_bytes(b"sentinel-v1")
    result = run_file(["-Action", "install"], env)
    assert result.returncode == 2, result.stdout + "\n" + result.stderr
    assert "consent=required" in result.stdout
    assert "downloaded=0" in result.stdout
    assert (data / "sentinel.txt").read_bytes() == b"sentinel-v1"
    program = Path(env["LOCALAPPDATA"]) / "Programs" / "JC_response"
    program.mkdir(parents=True)
    (program / "VERSION").write_text("version=9.9.9\nschema=other\n", encoding="utf-8")
    result = run_file(["-Action", "install", "-Confirm"], env)
    assert result.returncode == 4, result.stdout + result.stderr
    assert "class=higher_version" in result.stdout
    assert "downloaded=0" in result.stdout
    config = home / ".workbuddy" / "mcp.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps({
        "theme": "kept",
        "mcpServers": {
            "scys-mcp": {"type": "stdio", "command": "C:\\Other\\scys.exe", "env": {"nested": {"keep": True}}},
            "jc-response": {"type": "stdio", "command": "C:\\Unknown\\jctrans-mcp.exe", "args": []},
        },
    }, ensure_ascii=False)
    config.write_text(original, encoding="utf-8")
    result = run_file(["-Action", "configure", "-Confirm"], env)
    assert result.returncode == 5, result.stdout + result.stderr
    assert "config=conflict" in result.stdout
    assert config.read_text(encoding="utf-8") == original
    denied = env.copy()
    denied["OS"] = "Other"
    result = run_file(["-Action", "inspect"], denied)
    assert result.returncode == 3
    assert "platform=unsupported" in result.stdout


def test_docs_and_config_helpers(tmp: Path) -> None:
    root = tmp / "docs-case"
    extract = root / "extract"
    program = root / "program"
    for root in (extract, program):
        (root / "bin").mkdir(parents=True)
        (root / "bin" / "same.dll").write_bytes(b"same")
        (root / "docs").mkdir()
    (extract / "docs" / "安装说明.md").write_text("new", encoding="utf-8")
    (program / "docs" / "安装说明.md").write_text("old", encoding="utf-8")
    (program / "bin" / "sentinel.dll").write_bytes(b"keep")
    (extract / "bin" / "sentinel.dll").write_bytes(b"keep")
    pin = "@{ doc_files = @('docs/安装说明.md') }"
    result = dot(f"$pin = {pin}; Update-DocWhitelist '{extract}' '{program}' $pin")
    assert result.stdout.strip().endswith("docs_refreshed"), result.stdout + result.stderr
    assert (program / "docs" / "安装说明.md").read_text(encoding="utf-8") == "new"
    assert (program / "bin" / "sentinel.dll").read_bytes() == b"keep"
    assert (program / "bin" / "same.dll").read_bytes() == b"same"
    locked = program / "docs" / "安装说明.md"
    handle = open(locked, "rb")
    try:
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close()
        handle = None
    if handle is not None:
        try:
            (extract / "docs" / "安装说明.md").write_text("newer", encoding="utf-8")
            result = dot(f"$pin = {pin}; Update-DocWhitelist '{extract}' '{program}' $pin")
            assert "docs_locked" in result.stdout, result.stdout + result.stderr
        finally:
            handle.close()
        assert locked.read_text(encoding="utf-8") == "new"
    official = str(program / "bin" / "jctrans-mcp.exe")
    config = tmp / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"jc-response": {"type": "stdio", "command": official, "args": []}}}), encoding="utf-8")
    result = dot(f"Get-ConfigPlan '{config}' '{official}'")
    assert result.stdout.strip().endswith("reuse")
    config.write_text("{", encoding="utf-8")
    result = dot(f"Get-ConfigPlan '{config}' '{official}'")
    assert result.stdout.strip().endswith("invalid")


def test_reviewed_upgrade_keeps_sentinels() -> None:
    package = Path(r"D:\Code\work\jctrans-cli-export\dist") / PIN["file_name"]
    digest = hashlib.sha256()
    with package.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    assert digest.hexdigest() == PIN["sha256"]
    assert package.stat().st_size == PIN["file_size"]
    predecessor = PIN["supported_upgrades"][0]
    live = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "JC_response"
    live_hashes = {
        name: hashlib.sha256((live / "bin" / name).read_bytes()).hexdigest()
        for name in predecessor["exe_names"]
    }
    assert set(live_hashes.values()) == {predecessor["exe_sha256"]}
    assert not list(live.rglob("*.db"))
    env = isolated("upgrade")
    program = Path(env["LOCALAPPDATA"]) / "Programs" / "JC_response"
    shutil.copytree(live, program)
    data = Path(env["LOCALAPPDATA"]) / "JC_response"
    (data / "auth").mkdir(parents=True)
    (data / "state").mkdir()
    export = data / "accounts" / "synthetic" / "exports"
    export.mkdir(parents=True)
    (data / "auth" / "sentinel.bin").write_bytes(b"synthetic-auth")
    (data / "state" / "budget-sentinel.txt").write_text("synthetic-budget", encoding="utf-8")
    (export / "sentinel.csv").write_text("synthetic-not-a-real-response\n", encoding="utf-8")
    config = Path(env["USERPROFILE"]) / ".workbuddy" / "mcp.json"
    config.parent.mkdir(parents=True)
    original = {
        "theme": "kept",
        "mcpServers": {
            "scys-mcp": {"type": "stdio", "command": "C:\\Other\\scys.exe", "env": {"nested": {"keep": True}}},
            "jc-response": {"type": "stdio", "command": "C:\\Old\\jctrans-mcp.exe", "args": []},
        },
    }
    config.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

    def sentinels_held() -> None:
        assert (data / "auth" / "sentinel.bin").read_bytes() == b"synthetic-auth"
        assert (data / "state" / "budget-sentinel.txt").read_text(encoding="utf-8") == "synthetic-budget"
        assert (export / "sentinel.csv").read_text(encoding="utf-8") == "synthetic-not-a-real-response\n"
        current = json.loads(config.read_text(encoding="utf-8"))
        assert current["theme"] == "kept"
        assert current["mcpServers"]["scys-mcp"] == original["mcpServers"]["scys-mcp"]

    result = run_file(
        ["-Action", "install", "-Confirm", "-PackagePath", str(package)],
        env,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "class=supported_upgrade" in result.stdout
    assert "install_status=upgraded" in result.stdout
    assert "install_judged=verified" in result.stdout
    assert "downloaded=0" in result.stdout
    version = (program / "VERSION").read_text(encoding="utf-8")
    assert "version=1.3.0" in version
    assert "csv_schema=JC_response_business/1.0" in version
    upgraded = hashlib.sha256((program / "bin" / "JC_response.exe").read_bytes()).hexdigest()
    assert upgraded == PIN["exe_sha256"]
    sentinels_held()
    assert live_hashes["JC_response.exe"] == hashlib.sha256((live / "bin" / "JC_response.exe").read_bytes()).hexdigest()

    guide = program / "docs" / "使用说明.md"
    before_doc = guide.read_bytes()
    before_exe = (program / "bin" / "JC_response.exe").read_bytes()
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(package)], env, timeout=180)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "class=match" in result.stdout
    assert "install=reused" in result.stdout
    assert "downloaded=0" in result.stdout
    assert guide.read_bytes() == before_doc
    assert (program / "bin" / "JC_response.exe").read_bytes() == before_exe

    guide.write_bytes(before_doc + "\n<!-- synthetic marker -->\n".encode("utf-8"))
    result = run_file(
        ["-Action", "refresh-docs", "-Confirm", "-PackagePath", str(package)],
        env,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "docs=docs_refreshed" in result.stdout
    assert guide.read_bytes() == before_doc
    assert (program / "bin" / "JC_response.exe").read_bytes() == before_exe
    sentinels_held()

    absent = isolated("bad-package")
    rejected = Path(absent["TEMP"]) / "not-the-package.zip"
    rejected.write_bytes(b"not-the-reviewed-package")
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(rejected)], absent, timeout=180)
    assert result.returncode == 3, result.stdout + "\n" + result.stderr
    assert "download=local_rejected" in result.stdout
    assert not (Path(absent["LOCALAPPDATA"]) / "Programs" / "JC_response").exists()
    assert (program / "bin" / "JC_response.exe").read_bytes() == before_exe

    unknown = isolated("unknown-source")
    unknown_program = Path(unknown["LOCALAPPDATA"]) / "Programs" / "JC_response"
    (unknown_program / "bin").mkdir(parents=True)
    (unknown_program / "VERSION").write_text(
        "version=1.2.0\nschema=response_flow/1.1\ncsv_schema=JC_response/1.1\n",
        encoding="utf-8",
    )
    for name in predecessor["exe_names"]:
        (unknown_program / "bin" / name).write_bytes(b"unreviewed-bytes")
    result = run_file(["-Action", "install", "-Confirm", "-PackagePath", str(package)], unknown, timeout=180)
    assert result.returncode == 4, result.stdout + "\n" + result.stderr
    assert "class=unknown" in result.stdout
    assert "downloaded=0" in result.stdout
    assert (unknown_program / "bin" / "JC_response.exe").read_bytes() == b"unreviewed-bytes"
    sentinels_held()
    assert live_hashes["JC_response.exe"] == hashlib.sha256((live / "bin" / "JC_response.exe").read_bytes()).hexdigest()


class SetupSkill(unittest.TestCase):
    def test_candidate_package(self) -> None:
        main()


def main() -> None:
    tmp = Path(os.environ["TEMP"]) / "jc-response-setup-test" / "fixtures"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    test_names_and_generated_rules()
    test_teach_and_boundaries()
    test_zip_and_classification(tmp)
    test_isolated_actions()
    test_docs_and_config_helpers(tmp)
    test_reviewed_upgrade_keeps_sentinels()
    print("setup skill tests ok")


if __name__ == "__main__":
    main()
