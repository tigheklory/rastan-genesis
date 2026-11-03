#!/usr/bin/env python3
"""Verify the final-life phase-9 bridge against the final address map."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


SOURCE_ARCADE_PC = 0x03A1C0
TARGET_ARCADE_PC = 0x03B11A


def map_arcade(address_map: dict[str, object], arcade_pc: int) -> int:
    for raw in address_map.get("segments", []):
        segment = dict(raw)
        if "arcade_start" not in segment:
            continue
        start = int(str(segment["arcade_start"]), 0)
        end = int(str(segment["arcade_end_exclusive"]), 0)
        if start <= arcade_pc < end:
            return int(str(segment["genesis_start"]), 0) + arcade_pc - start
    raise RuntimeError(f"arcade PC 0x{arcade_pc:06X} is absent from address map")


def verify(rom_path: Path, address_map_path: Path, spec_path: Path) -> tuple[int, int, int]:
    rom = rom_path.read_bytes()
    address_map = json.loads(address_map_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    matches = [
        entry for entry in spec.get("declared_relative_branches", [])
        if int(entry["arcade_pc"], 0) == SOURCE_ARCADE_PC
    ]
    if len(matches) != 1 or int(matches[0]["target_arcade_pc"], 0) != TARGET_ARCADE_PC:
        raise RuntimeError("final-life branch lacks one semantic source/target declaration")
    source = map_arcade(address_map, SOURCE_ARCADE_PC)
    expected = map_arcade(address_map, TARGET_ARCADE_PC)
    if rom[source:source + 2] != b"\x60\x00":
        raise RuntimeError(f"final-life bridge opcode mismatch at 0x{source:06X}")
    displacement = struct.unpack_from(">h", rom, source + 2)[0]
    actual = source + 2 + displacement
    if actual != expected:
        raise RuntimeError(
            f"final-life bridge target mismatch: source=0x{source:06X} "
            f"actual=0x{actual:06X} expected=0x{expected:06X}"
        )
    return source, actual, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--address-map", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    source, actual, expected = verify(args.rom, args.address_map, args.spec)
    print(
        "FINAL_LIFE_TRANSITION_VERIFY_PASS "
        f"source=0x{source:06X} generated_target=0x{actual:06X} mapped_target=0x{expected:06X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
