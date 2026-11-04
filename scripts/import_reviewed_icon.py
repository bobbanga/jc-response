"""Import the exact original PNG from the approved Skill ZIP. No network or Git writes."""
from __future__ import annotations
import argparse
import zipfile
from pathlib import Path
from pack_setup_skill import SKILL, load_manifest, sha256, archive_bytes


def import_icon(package: Path, skill: Path = SKILL, manifest: dict | None = None) -> str:
    manifest = manifest or load_manifest(skill=skill)
    raw = package.read_bytes()
    if len(raw) != manifest["package"]["bytes"] or sha256(raw) != manifest["package"]["sha256"]:
        raise ValueError("Not the approved Skill ZIP")
    item = next(x for x in manifest["files"] if x["path"] == "references/market-icon.png")
    for other in manifest["files"]:
        if other["path"] != item["path"]:
            archive_bytes(skill, other)
    with zipfile.ZipFile(package) as archive:
        expected = [manifest["skill_id"] + "/" + x["path"] for x in manifest["files"]]
        if archive.namelist() != expected or archive.testzip() is not None:
            raise ValueError("Unexpected ZIP contents")
        data = archive.read(manifest["skill_id"] + "/" + item["path"])
    if sha256(data) != item["sha256"] or len(data) != item["bytes"]:
        raise ValueError("PNG identity mismatch")
    target = skill / item["path"]
    current = target
    while current != skill.parent:
        if current.is_symlink():
            raise ValueError("Symlink destination refused")
        current = current.parent
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError("Different icon exists; not overwritten")
        return "already_present"
    with target.open("xb") as handle:
        handle.write(data)
    return "imported"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    print(import_icon(parser.parse_args().zip))
