#!/usr/bin/env python3
"""Verify the final-ROM runtime contract of the permanent _invincible variant."""

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
    parser.add_argument("--address-map", type=Path, required=True)
    parser.add_argument("--maincpu", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    standard = args.standard.read_bytes()
    invincible = args.invincible.read_bytes()
    standard_manifest = read_json(args.standard_manifest)
    invincible_manifest = read_json(args.invincible_manifest)
    address_map = read_json(args.address_map)
    maincpu = args.maincpu.read_bytes()

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

    patch_rom_pc = int(patch["rom_pc"], 0)
    if standard[patch_rom_pc] != 0xFF or invincible[patch_rom_pc] != 0xBF:
        raise SystemExit(
            f"FAIL: gate source byte at ROM 0x{patch_rom_pc:06X} is "
            f"standard=0x{standard[patch_rom_pc]:02X}, "
            f"invincible=0x{invincible[patch_rom_pc]:02X}"
        )

    def relocation(manifest: dict, arcade_pc: int) -> dict:
        matches = [
            item for item in manifest.get("address_rewrites", [])
            if item.get("kind") == "relocate_after_shift_operand"
            and int(item.get("arcade_pc", "-1"), 0) == arcade_pc
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"FAIL: expected one runtime operand relocation for arcade 0x{arcade_pc:06X}, "
                f"found {len(matches)}"
            )
        return matches[0]

    startup_standard = relocation(standard_manifest, 0x03AFEE)
    startup_invincible = relocation(invincible_manifest, 0x03AFEE)
    bit7_standard = relocation(standard_manifest, 0x03AFFE)
    bit7_invincible = relocation(invincible_manifest, 0x03AFFE)

    startup_pc = int(startup_standard["genesis_callsite"], 0)
    startup_target = int(startup_standard["final_operand"], 0)
    if (
        int(startup_invincible["genesis_callsite"], 0) != startup_pc
        or int(startup_invincible["final_operand"], 0) != startup_target
    ):
        raise SystemExit("FAIL: standard/_invincible startup relocation differs")
    expected_startup = b"\x30\x39" + startup_target.to_bytes(4, "big")
    if standard[startup_pc:startup_pc + 6] != expected_startup:
        raise SystemExit("FAIL: standard final startup instruction does not read relocated config")
    if invincible[startup_pc:startup_pc + 6] != expected_startup:
        raise SystemExit("FAIL: _invincible final startup instruction does not read relocated config")
    if patch_rom_pc != startup_target + 1:
        raise SystemExit(
            f"FAIL: variant patch 0x{patch_rom_pc:06X} is not low byte of runtime-read word "
            f"0x{startup_target:06X}"
        )

    bit7_pc = int(bit7_standard["genesis_callsite"], 0)
    bit7_target = int(bit7_standard["final_operand"], 0)
    if (
        int(bit7_invincible["genesis_callsite"], 0) != bit7_pc
        or int(bit7_invincible["final_operand"], 0) != bit7_target
        or bit7_target != startup_target
    ):
        raise SystemExit("FAIL: A5+0x0044 does not read the same relocated config word")
    expected_bit7 = b"\x30\x39" + bit7_target.to_bytes(4, "big")
    if standard[bit7_pc:bit7_pc + 6] != expected_bit7:
        raise SystemExit("FAIL: standard final A5+0x0044 initializer reads wrong config")
    if invincible[bit7_pc:bit7_pc + 6] != expected_bit7:
        raise SystemExit("FAIL: _invincible final A5+0x0044 initializer reads wrong config")

    standard_word = int.from_bytes(standard[startup_target:startup_target + 2], "big")
    invincible_word = int.from_bytes(invincible[startup_target:startup_target + 2], "big")
    standard_not = (~standard_word) & 0xFFFF
    invincible_not = (~invincible_word) & 0xFFFF
    standard_gate = standard_not & 0x0040
    invincible_gate = invincible_not & 0x0040
    if standard_gate != 0x0000 or invincible_gate != 0x0040:
        raise SystemExit(
            f"FAIL: runtime gate results standard=0x{standard_gate:04X}, "
            f"invincible=0x{invincible_gate:04X}"
        )
    if (standard_not & 0x0080) != (invincible_not & 0x0080):
        raise SystemExit("FAIL: A5+0x0044 input bit changed")
    if (standard_word & 0x000F) != (invincible_word & 0x000F):
        raise SystemExit("FAIL: unrelated configuration bits 0-3 changed")

    shift_deltas = [(int(pc, 0), int(delta)) for pc, delta in address_map["shift_deltas"]]
    relocation_delta = int(address_map["relocation_delta"], 0)

    def mapped(arcade_pc: int) -> int:
        return arcade_pc + relocation_delta + sum(
            delta for shift_pc, delta in shift_deltas if shift_pc < arcade_pc
        )

    for manifest, rom, label in (
        (standard_manifest, standard, "standard"),
        (invincible_manifest, invincible, "invincible"),
    ):
        table_records = [
            item for item in manifest.get("address_rewrites", [])
            if item.get("kind") == "absolute_long_pointer_table"
            and item.get("table_address") == "0x0550A8"
        ]
        if len(table_records) != 1:
            raise SystemExit(f"FAIL: {label} damage dispatch table record missing/duplicated")
        table_record = table_records[0]
        if table_record.get("entry_count") != 66 or table_record.get("fixes") != 66:
            raise SystemExit(f"FAIL: {label} damage dispatch table is not 66/66 relocated")
        rom_table = int(table_record["rom_table_address"], 0)
        for index in range(66):
            source = 0x0550A8 + index * 4
            arcade_target = int.from_bytes(maincpu[source:source + 4], "big")
            actual_target = int.from_bytes(
                rom[rom_table + index * 4:rom_table + index * 4 + 4], "big"
            )
            expected_target = mapped(arcade_target)
            if actual_target != expected_target:
                raise SystemExit(
                    f"FAIL: {label} damage dispatch entry {index} is 0x{actual_target:06X}, "
                    f"expected 0x{expected_target:06X}"
                )

    differences = {
        offset for offset, (normal_byte, invincible_byte) in
        enumerate(zip(standard, invincible)) if normal_byte != invincible_byte
    }
    allowed = {0x18E, 0x18F, patch_rom_pc}  # Genesis checksum plus declared source bit.
    unexpected = differences - allowed
    if unexpected:
        preview = ", ".join(f"0x{offset:06X}" for offset in sorted(unexpected)[:16])
        raise SystemExit(f"FAIL: unrelated standard/_invincible ROM differences: {preview}")
    if patch_rom_pc not in differences:
        raise SystemExit("FAIL: declared invincibility source byte does not differ")

    print("INVINCIBLE_VARIANT_PASS")
    print(f"startup_runtime_pc=0x{startup_pc:06X}")
    print(f"startup_config_read=0x{startup_target:06X}")
    print(f"standard_word=0x{standard_word:04X} -> A5+0x0040=0x{standard_gate:04X}")
    print(f"invincible_word=0x{invincible_word:04X} -> A5+0x0040=0x{invincible_gate:04X}")
    print("A5+0x0044 source bit 7 unchanged")
    print("config_bits_0_3_unchanged")
    print("damage_dispatch_table=66/66")
    print("unrelated_rom_differences=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
