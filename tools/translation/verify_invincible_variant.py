#!/usr/bin/env python3
"""Verify the permanent build-time _invincible ROM differs only as declared."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard", type=Path, required=True)
    parser.add_argument("--invincible", type=Path, required=True)
    parser.add_argument("--standard-manifest", type=Path, required=True)
    parser.add_argument("--invincible-manifest", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    standard = args.standard.read_bytes()
    invincible = args.invincible.read_bytes()
    standard_manifest = read_json(args.standard_manifest)
    invincible_manifest = read_json(args.invincible_manifest)

    if len(standard) != len(invincible):
        raise SystemExit("FAIL: standard and _invincible ROM sizes differ")
    if standard_manifest.get("invincible_variant") is not False:
        raise SystemExit("FAIL: standard manifest is not explicitly non-invincible")
    if invincible_manifest.get("invincible_variant") is not True:
        raise SystemExit("FAIL: _invincible manifest is not marked invincible")

    standard_variant_writes = [
        item for item in standard_manifest.get("address_rewrites", [])
        if item.get("kind") == "build_variant_patch"
    ]
    invincible_variant_writes = [
        item for item in invincible_manifest.get("address_rewrites", [])
        if item.get("kind") == "build_variant_patch"
    ]
    if standard_variant_writes:
        raise SystemExit("FAIL: standard ROM contains a build-variant patch")
    if len(invincible_variant_writes) != 1:
        raise SystemExit(
            f"FAIL: expected one _invincible variant patch, found {len(invincible_variant_writes)}"
        )

    patch = invincible_variant_writes[0]
    expected = {
        "variant": "invincible",
        "arcade_pc": "0x05FF9F",
        "original_bytes": "ff",
        "replacement_bytes": "bf",
    }
    for key, value in expected.items():
        if patch.get(key) != value:
            raise SystemExit(
                f"FAIL: _invincible manifest {key}={patch.get(key)!r}, expected {value!r}"
            )

    rom_pc = int(patch["rom_pc"], 0)
    if standard[rom_pc] != 0xFF or invincible[rom_pc] != 0xBF:
        raise SystemExit(
            f"FAIL: gate source byte at ROM 0x{rom_pc:06X} is "
            f"standard=0x{standard[rom_pc]:02X}, invincible=0x{invincible[rom_pc]:02X}"
        )

    differences = {
        offset for offset, (normal_byte, invincible_byte) in
        enumerate(zip(standard, invincible)) if normal_byte != invincible_byte
    }
    allowed = {0x18E, 0x18F, rom_pc}  # Genesis checksum plus declared source bit.
    unexpected = differences - allowed
    if unexpected:
        preview = ", ".join(f"0x{offset:06X}" for offset in sorted(unexpected)[:16])
        raise SystemExit(f"FAIL: unrelated standard/_invincible ROM differences: {preview}")
    if rom_pc not in differences:
        raise SystemExit("FAIL: declared invincibility source byte does not differ")

    print("INVINCIBLE_VARIANT_PASS")
    print(f"gate_source_rom_pc=0x{rom_pc:06X}")
    print("standard_source=0xFF -> A5+0x0040=0x0000")
    print("invincible_source=0xBF -> A5+0x0040=0x0040")
    print("A5+0x0044 source bit 7 unchanged")
    print("unrelated_rom_differences=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
