"""Repack one reviewed ZIP with public documentation only; never execute programs."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

INPUT_SHA256 = "a042880a60bc3cadbbb3ffaf667c222cba6560a760b874271b9710c3e6254035"
INPUT_BYTES = 122266807
EXE_SHA256 = "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d"
OVERLAYS = {"docs/" + n + ".md": "docs/" + n + ".md" for n in ("安装说明", "使用说明", "安全说明", "接入提示词", "升级说明")}
OVERLAYS.update({"skills/jc-response-preview/SKILL.md": "skills/jc-response-preview/SKILL.md", "VERSION": "release-files/VERSION", "RELEASE-METADATA.json": "release-files/RELEASE-METADATA.json"})


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_name(raw: str) -> str:
    name = raw.replace("\\", "/")
    parts = name.rstrip("/").split("/")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if name.startswith("/") or any(ord(c) < 32 for c in name):
        raise ValueError("unsafe archive path")
    if any(p in ("", ".", "..") or ":" in p or p.endswith((".", " ")) or p.split(".", 1)[0].lower() in reserved for p in parts):
        raise ValueError("unsafe Windows path")
    return "/".join(parts)


def index_zip(z: zipfile.ZipFile) -> dict:
    entries, result, seen = z.infolist(), {}, set()
    if len(entries) > 10000 or sum(x.file_size for x in entries) > 2 * 1024**3:
        raise ValueError("archive exceeds review limits")
    for x in entries:
        n = safe_name(x.filename)
        if n.casefold() in seen or x.flag_bits & 1 or stat.S_ISLNK(x.external_attr >> 16):
            raise ValueError("duplicate, encrypted or linked entry")
        seen.add(n.casefold())
        if not x.is_dir() and not x.filename.endswith("\\"):
            result[n] = x
    folded = {n.casefold() for n in result}
    for n in result:
        parts = n.split("/")
        if any("/".join(parts[:i]).casefold() in folded for i in range(1, len(parts))):
            raise ValueError("file/directory collision")
    return result


def verify_zip(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        items = index_zip(z)
        hashes = {n: hashlib.sha256(z.read(x)).hexdigest() for n, x in items.items()}
        declared, seen = {}, set()
        for line in z.read(items["SHA256SUMS.txt"]).decode("utf-8-sig").splitlines():
            if not line.strip():
                continue
            m = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
            if not m:
                raise ValueError("invalid checksum record")
            n = safe_name(m[2])
            if n.casefold() in seen:
                raise ValueError("duplicate checksum target")
            declared[n], seen = m[1].lower(), seen | {n.casefold()}
        if declared != {n: h for n, h in hashes.items() if n != "SHA256SUMS.txt"}:
            raise ValueError("checksum content or coverage mismatch")
        return hashes


def repack(source: Path, output: Path, root: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    if source == output or output.exists():
        raise ValueError("output must be a new file")
    if source.stat().st_size != INPUT_BYTES or sha_file(source) != INPUT_SHA256:
        raise ValueError("input does not match the reviewed archive")
    original = verify_zip(source)
    for n in ("JC_response.exe", "jctrans.exe", "jctrans-mcp.exe"):
        if original.get("bin/" + n) != EXE_SHA256:
            raise ValueError("product binary identity mismatch")
    overlays = {n: (root / p).read_bytes() for n, p in OVERLAYS.items()}
    meta = json.loads(overlays["RELEASE-METADATA.json"])
    if meta["input_zip_sha256"] != INPUT_SHA256 or meta["binary_recompiled"] is not False or meta["product_exe_sha256"] != EXE_SHA256:
        raise ValueError("metadata identity mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    written = {}
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as new:
        indexed = index_zip(old)
        def write(name: str, data: bytes) -> None:
            info = zipfile.ZipInfo(name, (2026, 11, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            new.writestr(info, data, compresslevel=6)
        for n in sorted((set(indexed) | set(overlays)) - {"SHA256SUMS.txt"}):
            data = overlays[n] if n in overlays else old.read(indexed[n])
            write(n, data)
            written[n] = hashlib.sha256(data).hexdigest()
        write("SHA256SUMS.txt", "".join(f"{written[n]}  {n}\n" for n in sorted(written)).encode())
    checked = verify_zip(output)
    runtime = {n: h for n, h in original.items() if n.startswith("bin/")}
    if runtime != {n: h for n, h in checked.items() if n.startswith("bin/")}:
        raise ValueError("runtime changed; retain output for investigation")
    changed = sorted(n for n in original if checked.get(n) != original[n])
    added = sorted(set(checked) - set(original))
    if (set(changed) | set(added)) - (set(OVERLAYS) | {"SHA256SUMS.txt"}):
        raise ValueError("unexpected changes")
    return dict(file_name=output.name, file_size=output.stat().st_size, sha256=sha_file(output), runtime_files_unchanged=len(runtime), changed_files=changed, added_files=added, checksum_entries_verified=len(checked)-1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(repack(args.source, args.output, Path(__file__).resolve().parents[1]), ensure_ascii=False, indent=2))
