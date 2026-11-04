"""Refresh generated business rules; preserve presentation metadata and review history."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from pack_setup_skill import get_version

ROOT = Path(__file__).resolve().parents[1]


def body_of(text: str) -> str:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("Authority skill is missing frontmatter")
    return text.split("\n---\n", 1)[1].lstrip("\n")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sync(root: Path = ROOT) -> None:
    skill = root / "skills/jc-response-setup"
    source = root / "skills/jc-response-preview/SKILL.md"
    mapping_path = skill / "references/source-map.json"
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    raw = source.read_bytes().replace(b"\r\n", b"\n")
    body = body_of(raw.decode("utf-8"))
    ref = payload["business_rules_source_commit"]
    header = (
        "# 业务规则\n\n"
        "本文件由权威 Skill `skills/jc-response-preview/SKILL.md` 生成，供 JC回盘助手按需阅读。"
        "它不是第二份 Skill，没有自己的 frontmatter，也不改变 MCP 名称、工具名或契约。\n\n"
        f"来源标识：{ref}。权威是下方来源 SHA256，不是已发布程序版本。\n\n"
        "来源文件：skills/jc-response-preview/SKILL.md\n\n"
        f"来源 SHA256：{sha256(raw)}\n\n---\n\n"
    )
    rules = (header + body).encode("utf-8")
    pin = (skill / "references/runtime-pin.json").read_bytes().replace(b"\r\n", b"\n")
    payload.update({
        "skill_version": get_version(skill),
        "business_rules_source_sha256": sha256(raw),
        "business_rules_body_sha256": sha256(body.encode("utf-8")),
        "business_rules_file_sha256": sha256(rules),
        "runtime_pin_sha256": sha256(pin),
        "published_download": json.loads(pin)["published"],
    })
    for rel in payload.get("presentation_files_sha256", {}):
        payload["presentation_files_sha256"][rel] = sha256((skill / rel).read_bytes().replace(b"\r\n", b"\n"))
    icon = skill / "references/market-icon.png"
    if "presentation_update" in payload:
        # A missing icon is a real release blocker; never silently drop its fields.
        payload["presentation_update"]["icon_sha256"] = sha256(icon.read_bytes())
        payload["presentation_update"]["icon_size_bytes"] = icon.stat().st_size
    (skill / "references/business-rules.md").write_bytes(rules)
    mapping_path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    sync()
