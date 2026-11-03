#!/usr/bin/env python3

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
BUILD_ROOT = ROOT / "build"
BUILD = ROOT / "build" / "regions"
ROM_INVENTORY = BUILD_ROOT / "rom_inventory.json"

MAINCPU_VARIANTS = {
    "world_rev1": [
        "b04-38.19",
        "b04-37.7",
        "b04-40.20",
        "b04-39.8",
        "b04-42.21",
        "b04-43-1.9",
    ],
    "world": [
        "b04-38.19",
        "b04-37.7",
        "b04-40.20",
        "b04-39.8",
        "b04-42.21",
        "b04-43.9",
    ],
    "us_rev1": [
        "b04-38.19",
        "b04-37.7",
        "b04-45.20",
        "b04-44.8",
        "b04-42.21",
        "b04-41-1.9",
    ],
    "us": [
        "b04-38.19",
        "b04-37.7",
        "b04-45.20",
        "b04-44.8",
        "b04-42.21",
        "b04-41.9",
    ],
    "japan_rev1": [
        "b04-14.19",
        "b04-13.7",
        "b04-16-1.20",
        "b04-15-1.8",
        "b04-18-1.21",
        "b04-17-1.9",
    ],
    "japan_earlier": [
        "b04-14.19",
        "b04-13.7",
        "b04-16.20",
        "b04-15.8",
        "b04-18-1.21",
        "b04-17-1.9",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build canonical Rastan ROM regions.")
    parser.add_argument(
        "--variant",
        default="world_rev1",
        choices=sorted(MAINCPU_VARIANTS),
        help="Main CPU program variant to assemble.",
    )
    return parser.parse_args()


def _merge_region(existing: str | None, incoming: str | None) -> str | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    if existing == incoming:
        return existing
    return None


def read_rom(filename: str, region: str | None, inventory: dict[str, dict[str, object]]) -> bytes:
    payload = (ROMS / filename).read_bytes()
    entry = inventory.get(filename)
    sha1 = hashlib.sha1(payload).hexdigest()

    if entry is None:
        inventory[filename] = {
            "path": f"roms/{filename}",
            "sha1": sha1,
            "size_bytes": len(payload),
            "region": region,
        }
    else:
        entry["region"] = _merge_region(entry.get("region"), region)
        entry["sha1"] = sha1
        entry["size_bytes"] = len(payload)

    return payload


def load16_byte_pairs(
    region_size: int,
    entries: list[tuple[str, int]],
    inventory: dict[str, dict[str, object]],
    region: str | None,
) -> bytes:
    data = bytearray(region_size)
    for filename, offset in entries:
        rom = read_rom(filename, region, inventory)
        data[offset : offset + len(rom) * 2 : 2] = rom
    return bytes(data)


def write_region(name: str, payload: bytes) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    path = BUILD / f"{name}.bin"
    path.write_bytes(payload)
    print(f"wrote {path} ({len(payload)} bytes)")


def write_variant_manifest(variant: str) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = {
        "maincpu_variant": variant,
        "maincpu_roms": MAINCPU_VARIANTS[variant],
    }
    (BUILD / "variant.json").write_text(json.dumps(manifest, indent=2) + "\n")


def warn_on_changed_sha1s(new_roms: dict[str, dict[str, object]]) -> None:
    if not ROM_INVENTORY.exists():
        return

    previous = json.loads(ROM_INVENTORY.read_text())
    previous_roms = previous.get("roms", {})

    for filename in sorted(new_roms):
        old_entry = previous_roms.get(filename)
        if old_entry is None:
            continue

        old_sha1 = old_entry.get("sha1")
        new_sha1 = new_roms[filename].get("sha1")

        if old_sha1 != new_sha1:
            print(f"WARNING: ROM {filename} SHA1 changed since last run.")
            print(f"Prior:  {old_sha1}")
            print(f"Now:    {new_sha1}")
            print("Delete build/rom_inventory.json to accept new ROMs.")


def write_rom_inventory(variant: str, roms: dict[str, dict[str, object]]) -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    warn_on_changed_sha1s(roms)
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "variant": variant,
        "roms": {name: roms[name] for name in sorted(roms)},
    }
    ROM_INVENTORY.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    args = parse_args()
    rom_inventory: dict[str, dict[str, object]] = {}

    write_region(
        "maincpu",
        load16_byte_pairs(
            0x60000,
            list(zip(MAINCPU_VARIANTS[args.variant], [0x00000, 0x00001, 0x20000, 0x20001, 0x40000, 0x40001])),
            rom_inventory,
            "maincpu",
        ),
    )
    write_region(
        "pc080sn",
        load16_byte_pairs(
            0x80000,
            [
                ("b04-01.40", 0x00000),
                ("b04-02.67", 0x00001),
                ("b04-03.39", 0x40000),
                ("b04-04.66", 0x40001),
            ],
            rom_inventory,
            "pc080sn",
        ),
    )
    write_region(
        "pc090oj",
        load16_byte_pairs(
            0x80000,
            [
                ("b04-05.15", 0x00000),
                ("b04-06.28", 0x00001),
                ("b04-07.14", 0x40000),
                ("b04-08.27", 0x40001),
            ],
            rom_inventory,
            "pc090oj",
        ),
    )
    write_region("audiocpu", read_rom("b04-19.49", "audiocpu", rom_inventory))
    write_region("adpcm", read_rom("b04-20.76", "adpcm", rom_inventory))
    write_rom_inventory(args.variant, rom_inventory)
    write_variant_manifest(args.variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
