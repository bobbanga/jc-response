"""Pack the JC回盘助手 skill. The runtime ZIP is not included."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "jc-response-setup"
OUT = ROOT / "dist" / "jc-response-setup-0.2.2.zip"
NAMES = [
    "SKILL.md",
    "scripts/setup-windows.ps1",
    "references/runtime-pin.json",
    "references/business-rules.md",
    "references/first-use.md",
    "references/prompt-examples.md",
    "references/upgrade-and-troubleshooting.md",
    "references/source-map.json",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in NAMES:
            source = SKILL / name
            data = source.read_bytes()
            text = data.decode("utf-8").casefold()
            if "c:\\users\\hiabo" in text or "d:\\code\\work" in text:
                raise SystemExit("personal path in " + name)
            archive.writestr("jc-response-setup/" + name, data)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"path={OUT}")
    print(f"bytes={OUT.stat().st_size}")
    print(f"sha256={digest}")
    print("files=" + ",".join(NAMES))


if __name__ == "__main__":
    main()
