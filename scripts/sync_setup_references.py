"""Generate the setup skill's business-rules reference from the authority skill."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "jc-response-preview" / "SKILL.md"
TARGET = ROOT / "skills" / "jc-response-setup" / "references" / "business-rules.md"
PIN = ROOT / "skills" / "jc-response-setup" / "references" / "runtime-pin.json"
SOURCE_MAP = ROOT / "skills" / "jc-response-setup" / "references" / "source-map.json"
COMMIT = "2b69ad300ee2435e4432292ca2af9e26a1e83b3a"


def body_of(text: str) -> str:
    if not text.startswith("---\n"):
        raise SystemExit("authority skill is missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise SystemExit("authority skill frontmatter does not close")
    body = text[end + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    if "---\n" in body.split("\n", 1)[0]:
        raise SystemExit("generated reference would keep a second frontmatter")
    return body


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    raw = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    text = raw.decode("utf-8")
    body = body_of(text)
    if "name: jc-response-preview" in body or text.count("---\n") < 2:
        raise SystemExit("authority split failed")
    header = (
        "# 业务规则\n\n"
        "本文件由权威 Skill `skills/jc-response-preview/SKILL.md` 生成，供 JC回盘助手按需阅读。"
        "它不是第二份 Skill，没有自己的 frontmatter，也不改变 MCP 名称、工具名或契约。\n\n"
        f"来源提交：{COMMIT}\n\n"
        "来源文件：skills/jc-response-preview/SKILL.md\n\n"
        f"来源 SHA256：{sha256(raw)}\n\n"
        "---\n\n"
    )
    TARGET.write_bytes((header + body).encode("utf-8"))
    rules_hash = sha256((header + body).encode("utf-8"))
    payload = {
        "skill_id": "jc-response-setup",
        "skill_version": "0.1.0",
        "skill_maturity": "candidate",
        "display_name": "JC回盘助手",
        "display_name_en": "JC Response Assistant",
        "subtitle": "安装接入 · 上手教学 · 回盘整理",
        "business_rules_source_commit": COMMIT,
        "business_rules_source_path": "skills/jc-response-preview/SKILL.md",
        "business_rules_source_sha256": sha256(raw),
        "business_rules_body_sha256": sha256(body.encode("utf-8")),
        "business_rules_file_sha256": rules_hash,
        "runtime_pin_sha256": sha256(PIN.read_bytes().replace(b"\r\n", b"\n")),
        "market_adapter_not_included": True,
        "market_adapter_source_seen": "8352547331fb4838715a50095dfeeaeb959ecc52",
        "docs_checked_on": "2026-11-03",
        "docs_checked": [
            "https://open.workbuddy.cn/docs/skill",
            "https://open.workbuddy.cn/docs/developer-agreement",
            "https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market",
            "https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide",
        ],
    }
    SOURCE_MAP.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
