#!/usr/bin/env python3
"""Post-build ROM patcher for the first executable startup slice."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROM_MIN_SIZE = 0x80000

STARTUP_COMMON_RANGE = (0x03AE86, 0x03B05C)
TITLE_HELPER_RANGES = (
    (0x03A552, 0x03A566, "helper_title_credit_trim"),
    (0x03B098, 0x03C484, "title_init_block"),
)
HELPER_RANGES = (
    (0x03AD3C, 0x03AD4C, "helper_fill_words"),
    (0x03AD72, 0x03ADBC, "helper_d000_init"),
    (0x03B0C2, 0x03B103, "helper_cfg_copy"),
    (0x03B9F8, 0x03BA88, "helper_200000_init"),
    (0x04EAF6, 0x04F0F6, "table_4eaf6"),
    (0x04FE62, 0x04FE82, "table_4fe62"),
    (0x05B512, 0x05B514, "helper_5b512_rts"),
    (0x05FFA2, 0x060000, "helper_5ffa2_5ffb2"),
)

SYMBOL_NAMES = (
    "genesistan_shadow_200000_words",
    "genesistan_arcade_workram_words",
    "genesistan_shadow_d00000_words",
    "genesistan_shadow_c00000_words",
    "genesistan_shadow_c08000_words",
    "genesistan_shadow_c04000_words",
    "genesistan_shadow_c0c000_words",
    "genesistan_shadow_c20000_words",
    "genesistan_shadow_c40000_words",
    "genesistan_shadow_reg_c50000",
    "genesistan_shadow_reg_d01bfe",
    "genesistan_shadow_reg_350008",
    "genesistan_shadow_reg_380000",
    "genesistan_shadow_reg_3c0000",
    "genesistan_shadow_reg_3e0001",
    "genesistan_shadow_reg_3e0003",
    "genesistan_shadow_dip1",
    "genesistan_shadow_dip2",
    "genesistan_shadow_service_word",
    "genesistan_startup_result_code",
    "genesistan_run_original_startup_common",
    "genesistan_startup_common_exit_normal",
    "genesistan_startup_common_exit_test",
)

SYMBOL_PATTERN = re.compile(r"^([0-9A-Fa-f]+)\s+\S+\s+(\S+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch a Genesis ROM with original Rastan startup code.")
    parser.add_argument("--variant", default="world_rev1")
    parser.add_argument("--maincpu", required=True)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--symbols", required=True)
    parser.add_argument("--manifest", required=True)
    return parser.parse_args()


def parse_symbol_table(path: Path, required_names: tuple[str, ...] | None = SYMBOL_NAMES) -> dict[str, int]:
    symbols: dict[str, int] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = SYMBOL_PATTERN.match(raw_line.strip())
        if match is None:
            continue
        address_text, name = match.groups()
        symbols[name] = int(address_text, 16)

    if required_names is None:
        return symbols

    resolved: dict[str, int] = {}
    for name in required_names:
        if name in symbols:
            resolved[name] = symbols[name]
            continue
        alt_name = f"_{name}"
        if alt_name in symbols:
            resolved[name] = symbols[alt_name]
            continue
        raise RuntimeError(f"Required symbol not found in {path}: {name}")

    return resolved


def ensure_rom_size(rom_bytes: bytearray) -> None:
    if len(rom_bytes) < ROM_MIN_SIZE:
        rom_bytes.extend(b"\x00" * (ROM_MIN_SIZE - len(rom_bytes)))


def copy_range(rom_bytes: bytearray, maincpu_bytes: bytes, start: int, end: int) -> None:
    rom_bytes[start:end] = maincpu_bytes[start:end]


def rewrite_long_in_range(
    rom_bytes: bytearray,
    range_start: int,
    range_end: int,
    old_address: int,
    new_address: int,
) -> int:
    old_bytes = old_address.to_bytes(4, "big")
    new_bytes = new_address.to_bytes(4, "big")
    cursor = range_start
    replacements = 0

    while True:
        location = rom_bytes.find(old_bytes, cursor, range_end)
        if location == -1:
            break
        rom_bytes[location:location + 4] = new_bytes
        replacements += 1
        cursor = location + 4

    return replacements


def rewrite_window_in_range(
    rom_bytes: bytearray,
    range_start: int,
    range_end: int,
    old_start: int,
    old_end: int,
    new_start: int,
) -> int:
    replacements = 0

    for location in range(range_start, range_end - 3, 2):
        value = int.from_bytes(rom_bytes[location:location + 4], "big")
        if old_start <= value < old_end:
            new_value = new_start + (value - old_start)
            rom_bytes[location:location + 4] = new_value.to_bytes(4, "big")
            replacements += 1

    return replacements


def build_status_stub(status_value: int, status_address: int, exit_address: int) -> bytes:
    return (
        bytes((0x33, 0xFC))
        + status_value.to_bytes(2, "big")
        + status_address.to_bytes(4, "big")
        + bytes((0x4E, 0xF9))
        + exit_address.to_bytes(4, "big")
    )


def build_normal_continue_stub(status_address: int, exit_address: int) -> bytes:
    return (
        bytes((0x33, 0xFC))
        + (1).to_bytes(2, "big")
        + status_address.to_bytes(4, "big")
        + bytes((0x4E, 0xB9))
        + (0x0003B098).to_bytes(4, "big")
        + bytes((0x4E, 0xF9))
        + exit_address.to_bytes(4, "big")
    )


def update_genesis_checksum(rom_bytes: bytearray) -> int:
    checksum = 0
    for offset in range(0x200, len(rom_bytes), 2):
        if offset + 1 < len(rom_bytes):
            word = (rom_bytes[offset] << 8) | rom_bytes[offset + 1]
        else:
            word = rom_bytes[offset] << 8
        checksum = (checksum + word) & 0xFFFF
    rom_bytes[0x18E:0x190] = checksum.to_bytes(2, "big")
    return checksum


def build_relocation_map(
    variant: str,
    rom_path: Path,
    maincpu_path: Path,
    copied_ranges: list[dict[str, object]],
    symbol_addresses: dict[str, int],
    test_stub_address: int,
) -> dict:
    object_entries: list[dict[str, object]] = []
    generated_entries: list[dict[str, object]] = []

    for entry in copied_ranges:
        start = int(str(entry["start"]), 16)
        end = int(str(entry["end_exclusive"]), 16)
        object_entries.append(
            {
                "id": f"maincpu:{start:06X}-{end - 1:06X}",
                "name": entry["name"],
                "kind": "original_code_or_data",
                "source_rom": str(maincpu_path.resolve()),
                "original_start": f"0x{start:06X}",
                "original_end_exclusive": f"0x{end:06X}",
                "genesis_rom_start": f"0x{start:06X}",
                "genesis_rom_end_exclusive": f"0x{end:06X}",
                "placement": "identity_copy",
            }
        )

    generated_entries.extend(
        [
            {
                "id": "startup_common.normal_result_stub",
                "kind": "generated_stub",
                "genesis_rom_start": "0x03B05C",
                "genesis_rom_end_exclusive": "0x03B06E",
                "replaces_original_range": "0x03B05C..0x03B06D",
                "reason": "Record normal path result, call original title-init block, and exit to Genesis runner.",
            },
            {
                "id": "startup_common.test_result_stub",
                "kind": "generated_stub",
                "genesis_rom_start": f"0x{test_stub_address:06X}",
                "genesis_rom_end_exclusive": f"0x{test_stub_address + 10:06X}",
                "replaces_original_range": f"0x{test_stub_address:06X}..0x{test_stub_address + 9:06X}",
                "reason": "Terminate test-mode branch locally and return to Genesis runner.",
            },
            {
                "id": "genesistan_run_original_startup_common",
                "kind": "runner_wrapper",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_run_original_startup_common']:06X}",
                "purpose": "C/asm wrapper that calls the original startup/common slice.",
            },
            {
                "id": "genesistan_startup_common_exit_normal",
                "kind": "runner_trampoline",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_startup_common_exit_normal']:06X}",
                "purpose": "Return trampoline for the normal branch after patched original flow.",
            },
            {
                "id": "genesistan_startup_common_exit_test",
                "kind": "runner_trampoline",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_startup_common_exit_test']:06X}",
                "purpose": "Return trampoline for the test branch after patched original flow.",
            },
        ]
    )

    return {
        "variant": variant,
        "rom": str(rom_path.resolve()),
        "source_maincpu": str(maincpu_path.resolve()),
        "policy": "Build from original ROM bytes every time; never patch forward from derived binaries.",
        "objects": object_entries,
        "generated_blocks": generated_entries,
    }


def main() -> int:
    args = parse_args()
    rom_path = Path(args.rom)
    symbols_path = Path(args.symbols)
    maincpu_path = Path(args.maincpu)
    manifest_path = Path(args.manifest)
    relocation_path = manifest_path.with_name("startup_common_relocations.json")

    symbol_addresses = parse_symbol_table(symbols_path, required_names=None)

    if "genesistan_run_original_startup_common" not in symbol_addresses:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "variant": args.variant,
                    "mode": "ui_only",
                    "rom": str(rom_path.resolve()),
                    "symbols": str(symbols_path.resolve()),
                    "note": "UI-only startup build; original startup opcode launcher not linked into this ROM.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        relocation_path.write_text(
            json.dumps(
                {
                    "variant": args.variant,
                    "mode": "ui_only",
                    "objects": [],
                    "generated_blocks": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    symbol_addresses = parse_symbol_table(symbols_path)
    rom_bytes = bytearray(rom_path.read_bytes())
    maincpu_bytes = maincpu_path.read_bytes()
    ensure_rom_size(rom_bytes)

    copied_ranges: list[dict[str, object]] = []
    all_ranges = (
        (STARTUP_COMMON_RANGE[0], STARTUP_COMMON_RANGE[1], "startup_common"),
        *TITLE_HELPER_RANGES,
        *HELPER_RANGES,
    )
    for start, end, name in all_ranges:
        copy_range(rom_bytes, maincpu_bytes, start, end)
        copied_ranges.append(
            {
                "name": name,
                "start": f"0x{start:06X}",
                "end_exclusive": f"0x{end:06X}",
                "size_bytes": end - start,
            }
        )

    startup_mapping = {
        0x00C50000: symbol_addresses["genesistan_shadow_reg_c50000"],
        0x00D01BFE: symbol_addresses["genesistan_shadow_reg_d01bfe"],
        0x00350008: symbol_addresses["genesistan_shadow_reg_350008"],
        0x00380000: symbol_addresses["genesistan_shadow_reg_380000"],
        0x003E0001: symbol_addresses["genesistan_shadow_reg_3e0001"],
        0x003E0003: symbol_addresses["genesistan_shadow_reg_3e0003"],
        0x00200000: symbol_addresses["genesistan_shadow_200000_words"],
        0x0010C000: symbol_addresses["genesistan_arcade_workram_words"],
        0x0010C002: symbol_addresses["genesistan_arcade_workram_words"] + 2,
        0x003C0000: symbol_addresses["genesistan_shadow_reg_3c0000"],
        0x00C00000: symbol_addresses["genesistan_shadow_c00000_words"],
        0x00C08000: symbol_addresses["genesistan_shadow_c08000_words"],
        0x00C04000: symbol_addresses["genesistan_shadow_c04000_words"],
        0x00C0C000: symbol_addresses["genesistan_shadow_c0c000_words"],
        0x00390009: symbol_addresses["genesistan_shadow_dip1"],
        0x0039000B: symbol_addresses["genesistan_shadow_dip2"],
        0x0005FF9E: symbol_addresses["genesistan_shadow_service_word"],
    }

    helper_mapping = {
        0x00D00000: symbol_addresses["genesistan_shadow_d00000_words"],
        0x00D00778: symbol_addresses["genesistan_shadow_d00000_words"] + 0x778,
        0x00200000: symbol_addresses["genesistan_shadow_200000_words"],
    }

    rewrite_log: list[dict[str, object]] = []
    for old_address, new_address in startup_mapping.items():
        count = rewrite_long_in_range(
            rom_bytes,
            STARTUP_COMMON_RANGE[0],
            STARTUP_COMMON_RANGE[1],
            old_address,
            new_address,
        )
        rewrite_log.append(
            {
                "range": "startup_common",
                "old": f"0x{old_address:08X}",
                "new": f"0x{new_address:08X}",
                "count": count,
            }
        )

    count = rewrite_long_in_range(
        rom_bytes, 0x03AD72, 0x03ADBC, 0x00D00000, helper_mapping[0x00D00000]
    )
    rewrite_log.append(
        {
            "range": "helper_d000_init",
            "old": "0x00D00000",
            "new": f"0x{helper_mapping[0x00D00000]:08X}",
            "count": count,
        }
    )
    count = rewrite_long_in_range(
        rom_bytes, 0x03AD72, 0x03ADBC, 0x00D00778, helper_mapping[0x00D00778]
    )
    rewrite_log.append(
        {
            "range": "helper_d000_init",
            "old": "0x00D00778",
            "new": f"0x{helper_mapping[0x00D00778]:08X}",
            "count": count,
        }
    )
    count = rewrite_long_in_range(
        rom_bytes, 0x03B9F8, 0x03BA88, 0x00200000, helper_mapping[0x00200000]
    )
    rewrite_log.append(
        {
            "range": "helper_200000_init",
            "old": "0x00200000",
            "new": f"0x{helper_mapping[0x00200000]:08X}",
            "count": count,
        }
    )

    title_window_mappings = (
        ("title_init_block", 0x03B098, 0x03C484, 0x00C00000, 0x00C04000, symbol_addresses["genesistan_shadow_c00000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00C04000, 0x00C08000, symbol_addresses["genesistan_shadow_c04000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00C08000, 0x00C0C000, symbol_addresses["genesistan_shadow_c08000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00C0C000, 0x00C10000, symbol_addresses["genesistan_shadow_c0c000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x0010C000, 0x00110000, symbol_addresses["genesistan_arcade_workram_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00D00000, 0x00D00800, symbol_addresses["genesistan_shadow_d00000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00C20000, 0x00C20004, symbol_addresses["genesistan_shadow_c20000_words"]),
        ("title_init_block", 0x03B098, 0x03C484, 0x00C40000, 0x00C40004, symbol_addresses["genesistan_shadow_c40000_words"]),
        ("helper_title_credit_trim", 0x03A552, 0x03A566, 0x00C08000, 0x00C0C000, symbol_addresses["genesistan_shadow_c08000_words"]),
    )

    for name, start, end, old_start, old_end, new_start in title_window_mappings:
        count = rewrite_window_in_range(rom_bytes, start, end, old_start, old_end, new_start)
        rewrite_log.append(
            {
                "range": name,
                "old_window_start": f"0x{old_start:08X}",
                "old_window_end_exclusive": f"0x{old_end:08X}",
                "new_window_start": f"0x{new_start:08X}",
                "count": count,
            }
        )

    test_stub_address = 0x0003B070
    rom_bytes[0x03B058:0x03B05C] = test_stub_address.to_bytes(4, "big")
    rom_bytes[0x03B05C:0x03B06E] = build_normal_continue_stub(
        symbol_addresses["genesistan_startup_result_code"],
        symbol_addresses["genesistan_startup_common_exit_normal"],
    )
    rom_bytes[0x03B070:0x03B07A] = build_status_stub(
        GENESISTAN_STARTUP_RESULT_TEST := 2,
        symbol_addresses["genesistan_startup_result_code"],
        symbol_addresses["genesistan_startup_common_exit_test"],
    )

    checksum = update_genesis_checksum(rom_bytes)
    rom_path.write_bytes(rom_bytes)

    manifest = {
        "variant": args.variant,
        "rom": str(rom_path.resolve()),
        "symbols": str(symbols_path.resolve()),
        "maincpu": str(maincpu_path.resolve()),
        "copied_ranges": copied_ranges,
        "address_rewrites": rewrite_log,
        "normal_result_stub": {
            "address": "0x03B05C",
            "writes_status_to": f"0x{symbol_addresses['genesistan_startup_result_code']:08X}",
            "value": 1,
            "calls_original": "0x03B098",
            "jumps_exit_to": f"0x{symbol_addresses['genesistan_startup_common_exit_normal']:08X}",
        },
        "test_result_stub": {
            "address": f"0x{test_stub_address:06X}",
            "writes_status_to": f"0x{symbol_addresses['genesistan_startup_result_code']:08X}",
            "value": 2,
            "jumps_exit_to": f"0x{symbol_addresses['genesistan_startup_common_exit_test']:08X}",
        },
        "test_jump_patch": {
            "patched_at": "0x03B058",
            "new_target": f"0x{test_stub_address:06X}",
        },
        "checksum": f"0x{checksum:04X}",
        "relocation_map": str(relocation_path.resolve()),
        "goal": "Execute the original common startup/basic system-test block from the arcade ROM on Genesis.",
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    relocation_path.parent.mkdir(parents=True, exist_ok=True)
    relocation_map = build_relocation_map(
        args.variant,
        rom_path,
        maincpu_path,
        copied_ranges,
        symbol_addresses,
        test_stub_address,
    )
    relocation_path.write_text(json.dumps(relocation_map, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
