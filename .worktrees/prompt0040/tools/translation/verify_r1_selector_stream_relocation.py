#!/usr/bin/env python3
"""Verify the retained R1 selector-stream initializer follows final ROM reflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CALLSITE_ARCADE_PC = 0x0503CE
SELECTOR_STREAM_ARCADE_PC = 0x050F6B
SELECTOR_STREAM_SIZE = 0x9D
MOVE_L_IMMEDIATE_D0 = bytes.fromhex("203c")


def parse_int(value: object) -> int:
    return int(str(value), 0)


def map_arcade(address_map: dict[str, object], arcade_address: int) -> int:
    matches: list[int] = []
    for raw_segment in address_map.get("segments", []):
        segment = dict(raw_segment)
        if "arcade_start" not in segment or "arcade_end_exclusive" not in segment:
            continue
        arcade_start = parse_int(segment["arcade_start"])
        arcade_end = parse_int(segment["arcade_end_exclusive"])
        if arcade_start <= arcade_address < arcade_end:
            genesis_start = parse_int(segment["genesis_start"])
            matches.append(genesis_start + arcade_address - arcade_start)
    if len(set(matches)) != 1:
        rendered = ", ".join(f"0x{value:06X}" for value in matches) or "none"
        raise RuntimeError(
            f"arcade 0x{arcade_address:06X} has non-unique address-map result: {rendered}"
        )
    return matches[0]


def require_relocation_policy(spec: dict[str, object]) -> None:
    shift_entries = [
        entry
        for entry in spec.get("shift_replacements", [])
        if parse_int(entry.get("arcade_pc", "-1")) == CALLSITE_ARCADE_PC
    ]
    opcode_entries = [
        entry
        for entry in spec.get("opcode_replace", [])
        if parse_int(entry.get("arcade_pc", "-1")) == CALLSITE_ARCADE_PC
    ]
    if opcode_entries:
        raise RuntimeError("0x0503CE remains a hard-coded opcode_replace policy entry")
    if len(shift_entries) != 1:
        raise RuntimeError(f"expected one relocation-backed 0x0503CE entry, got {len(shift_entries)}")
    entry = shift_entries[0]
    if not entry.get("relocate_after_shift"):
        raise RuntimeError("0x0503CE does not enable relocate_after_shift")
    if str(entry.get("replacement_template", "")).lower() != MOVE_L_IMMEDIATE_D0.hex():
        raise RuntimeError("0x0503CE no longer preserves MOVE.L #imm,D0")
    if parse_int(entry.get("operand_arcade_target", "-1")) != SELECTOR_STREAM_ARCADE_PC:
        raise RuntimeError("0x0503CE semantic operand target is not arcade 0x050F6B")
    if parse_int(entry.get("operand_width", 0)) != 4:
        raise RuntimeError("0x0503CE operand width is not 32 bits")


def verify_rom(
    rom_path: Path,
    maincpu_path: Path,
    address_map_path: Path,
    spec_path: Path,
) -> tuple[int, int]:
    rom = rom_path.read_bytes()
    maincpu = maincpu_path.read_bytes()
    address_map = json.loads(address_map_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    require_relocation_policy(spec)

    callsite = map_arcade(address_map, CALLSITE_ARCADE_PC)
    mapped_target = map_arcade(address_map, SELECTOR_STREAM_ARCADE_PC)
    instruction = rom[callsite:callsite + 6]
    if len(instruction) != 6 or instruction[:2] != MOVE_L_IMMEDIATE_D0:
        raise RuntimeError(
            f"mapped 0x0503CE is not MOVE.L #imm,D0: {instruction.hex()} at 0x{callsite:06X}"
        )
    operand = int.from_bytes(instruction[2:6], "big")
    if operand != mapped_target:
        raise RuntimeError(
            f"stale selector-stream operand: 0x{operand:06X} != map(0x050F6B)=0x{mapped_target:06X}"
        )

    expected = maincpu[
        SELECTOR_STREAM_ARCADE_PC:SELECTOR_STREAM_ARCADE_PC + SELECTOR_STREAM_SIZE
    ]
    if len(expected) != SELECTOR_STREAM_SIZE:
        raise RuntimeError("canonical maincpu selector stream is truncated")
    actual = bytearray()
    for offset in range(SELECTOR_STREAM_SIZE):
        mapped_byte = map_arcade(address_map, SELECTOR_STREAM_ARCADE_PC + offset)
        if mapped_byte != mapped_target + offset:
            raise RuntimeError(
                f"selector stream is not contiguous at +0x{offset:X}: "
                f"0x{mapped_byte:06X} != 0x{mapped_target + offset:06X}"
            )
        actual.extend(rom[mapped_byte:mapped_byte + 1])
    if bytes(actual) != expected:
        mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
        raise RuntimeError(
            f"selector stream differs from arcade at +0x{mismatch:X}: "
            f"ROM=0x{actual[mismatch]:02X} arcade=0x{expected[mismatch]:02X}"
        )
    return operand, mapped_target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--address-map", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    operand, mapped_target = verify_rom(args.rom, args.maincpu, args.address_map, args.spec)
    print("R1_SELECTOR_STREAM_RELOCATION_PASS")
    print(f"callsite_arcade=0x{CALLSITE_ARCADE_PC:06X}")
    print(f"operand=0x{operand:06X}")
    print(f"mapped_selector_stream=0x{mapped_target:06X}")
    print(f"selector_stream_bytes={SELECTOR_STREAM_SIZE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
