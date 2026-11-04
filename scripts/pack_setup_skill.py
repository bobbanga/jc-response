"""Pack a reviewed Skill from its manifest; do not rebuild the Windows runtime."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/jc-response-setup"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frontmatter(text: str) -> str:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("Missing frontmatter")
    return text.split("\n---\n", 1)[0][4:]


def get_version(skill: Path = SKILL) -> str:
    match = re.search(r"^version:\s*(\d+\.\d+\.\d+)\s*$", frontmatter((skill / "SKILL.md").read_text(encoding="utf-8")), re.M)
    if not match:
        raise ValueError("Expected numeric Skill version")
    return match.group(1)


def check_examples(text: str) -> None:
    header = frontmatter(text)
    for name in ("examples_zh", "examples_en"):
        block = re.search(r"^" + name + r":\s*\n((?:[ \t]*- [^\n]*\n?)+)", header, re.M)
        count = len(re.findall(r"^[ \t]*- ", block.group(1), re.M)) if block else 0
        if not 1 <= count <= 3:
            raise ValueError(f"{name}: expected 1-3 entries, got {count}")


def load_manifest(root: Path = ROOT, skill: Path = SKILL) -> dict:
    return json.loads((root / "releases" / ("skill-" + get_version(skill)) / "manifest.json").read_text(encoding="utf-8"))


def archive_bytes(skill: Path, item: dict) -> bytes:
    rel = PurePosixPath(item["path"])
    if rel.is_absolute() or ".." in rel.parts or "\\" in str(rel):
        raise ValueError("Unsafe relative path")
    path = skill.joinpath(*rel.parts)
    current = path
    while current != skill.parent:
        if current.is_symlink():
            raise ValueError("Symlink source")
        current = current.parent
    raw = path.read_bytes()
    if item["line_endings"] != "binary":
        raw = raw.replace(b"\r\n", b"\n")
    if sha256(raw) != item["source_sha256"]:
        raise ValueError("Source changed: " + str(rel))
    if item["line_endings"] == "crlf":
        raw = raw.replace(b"\n", b"\r\n")
    if len(raw) != item["bytes"] or sha256(raw) != item["sha256"]:
        raise ValueError("Archive bytes changed: " + str(rel))
    return raw


def validate(skill: Path, manifest: dict) -> None:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    check_examples(text)
    if get_version(skill) != manifest["skill_version"]:
        raise ValueError("Manifest version differs")
    for key in ("name", "display_name", "display_name_en", "description", "description_zh", "description_en", "author"):
        if not re.search(r"^" + key + r":\s*\S", frontmatter(text), re.M):
            raise ValueError("Missing metadata: " + key)
    for ref in re.findall(r"@(references/[A-Za-z0-9_.\-/]+)", text):
        if not (skill / ref).is_file():
            raise ValueError("Missing reference: " + ref)
    expected = {x["path"] for x in manifest["files"]}
    actual = {p.relative_to(skill).as_posix() for p in skill.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError(f"File set differs; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    for item in manifest["files"]:
        archive_bytes(skill, item)
    icon = (skill / "references/market-icon.png").read_bytes()
    if icon[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", icon[16:24]) != (512, 512) or len(icon) > 500000:
        raise ValueError("Icon must be 512x512 PNG below 500 KB")
    mapping = json.loads((skill / "references/source-map.json").read_text(encoding="utf-8"))
    for rel, key in (("references/business-rules.md", "business_rules_file_sha256"), ("references/runtime-pin.json", "runtime_pin_sha256")):
        if sha256((skill / rel).read_bytes().replace(b"\r\n", b"\n")) != mapping[key]:
            raise ValueError("Generated hash differs: " + rel)
    if mapping["skill_version"] != get_version(skill):
        raise ValueError("source-map version differs")


def pack(output: Path, skill: Path = SKILL, manifest: dict | None = None) -> Path:
    manifest = manifest or load_manifest(skill=skill)
    validate(skill, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create: never replace an existing published/reviewed package.
    with output.open("xb") as handle:
        try:
            recipe = manifest["zip_recipe"]
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=recipe["level"]) as archive:
                for item in manifest["files"]:
                    info = zipfile.ZipInfo(manifest["skill_id"] + "/" + item["path"], tuple(recipe["date_time"]))
                    info.create_system = recipe["create_system"]
                    info.external_attr = recipe["external_attr"]
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, archive_bytes(skill, item), compresslevel=recipe["level"])
        except Exception:
            handle.close()
            output.unlink(missing_ok=True)
            raise
    data = output.read_bytes()
    if len(data) != manifest["package"]["bytes"] or sha256(data) != manifest["package"]["sha256"]:
        output.unlink()
        raise ValueError("Rebuild differs from approved ZIP; check compression environment. Do not change the published hash.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = load_manifest()
    path = pack(args.output or ROOT / "dist" / manifest["package"]["name"], manifest=manifest)
    print(f"path={path}\nbytes={path.stat().st_size}\nsha256={sha256(path.read_bytes())}")
