#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS_DIR = ROOT / "roms"
BUILD_DIR = ROOT / "build"
OUTPUT_PATH = BUILD_DIR / "rom_inventory.json"


def sha1_for_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def collect_inventory() -> dict:
    rom_files = sorted(
        path for path in ROMS_DIR.iterdir() if path.is_file() and not path.name.startswith(".")
    )

    files = []
    total_size = 0
    for path in rom_files:
        size = path.stat().st_size
        total_size += size
        files.append(
            {
                "name": path.name,
                "size": size,
                "sha1": sha1_for_file(path),
            }
        )

    return {
        "project": "rastan-genesis",
        "rom_directory": str(ROMS_DIR),
        "file_count": len(files),
        "total_size": total_size,
        "files": files,
    }


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    inventory = collect_inventory()
    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2) + "\n")

    print(f"ROM inventory written to {OUTPUT_PATH}")
    print(f"Files: {inventory['file_count']}")
    print(f"Total bytes: {inventory['total_size']}")
    for entry in inventory["files"]:
        print(f"{entry['name']:12} {entry['size']:8} {entry['sha1']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
