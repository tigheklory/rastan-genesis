#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
BUILD = ROOT / "build" / "regions"

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


def load16_byte_pairs(region_size: int, entries: list[tuple[str, int]]) -> bytes:
    data = bytearray(region_size)
    for filename, offset in entries:
        rom = (ROMS / filename).read_bytes()
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


def main() -> int:
    args = parse_args()

    write_region(
        "maincpu",
        load16_byte_pairs(
            0x60000,
            list(zip(MAINCPU_VARIANTS[args.variant], [0x00000, 0x00001, 0x20000, 0x20001, 0x40000, 0x40001])),
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
        ),
    )
    write_region("audiocpu", (ROMS / "b04-19.49").read_bytes())
    write_region("adpcm", (ROMS / "b04-20.76").read_bytes())
    write_variant_manifest(args.variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
