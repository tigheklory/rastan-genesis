#!/usr/bin/env python3
"""Post-build ROM patcher for the first executable startup slice."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROM_MIN_SIZE = 0x80000
DEFAULT_SPEC_PATH = Path(__file__).resolve().parents[2] / "specs" / "startup_title_remap.json"

SYMBOL_PATTERN = re.compile(r"^([0-9A-Fa-f]+)\s+\S+\s+(\S+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch a Genesis ROM with original Rastan startup code.")
    parser.add_argument("--variant", default="world_rev1")
    parser.add_argument("--maincpu", required=True)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--symbols", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH))
    return parser.parse_args()


def parse_hexish(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"Unsupported hex/int value: {value!r}")


def load_remap_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if "copied_ranges" not in spec:
        raise RuntimeError(f"Startup/title remap spec is missing copied_ranges: {path}")
    return spec


def build_range_lookup(spec: dict) -> dict[str, tuple[int, int]]:
    lookup: dict[str, tuple[int, int]] = {}
    for entry in spec["copied_ranges"]:
        name = entry["name"]
        lookup[name] = (parse_hexish(entry["start"]), parse_hexish(entry["end_exclusive"]))
    return lookup


def build_range_kind_lookup(spec: dict) -> dict[str, str]:
    kind_lookup: dict[str, str] = {}
    for entry in spec["copied_ranges"]:
        name = str(entry["name"])
        kind_lookup[name] = str(entry.get("kind", "original_code_or_data"))
    return kind_lookup


def parse_symbol_table(path: Path, required_names: tuple[str, ...] | None = None) -> dict[str, int]:
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


def ensure_size_at_least(rom_bytes: bytearray, size_bytes: int) -> None:
    if len(rom_bytes) < size_bytes:
        rom_bytes.extend(b"\x00" * (size_bytes - len(rom_bytes)))


def copy_range(rom_bytes: bytearray, maincpu_bytes: bytes, start: int, end: int) -> None:
    rom_bytes[start:end] = maincpu_bytes[start:end]


def value_in_windows(value: int, windows: list[tuple[int, int]]) -> bool:
    for start, end in windows:
        if start <= value < end:
            return True
    return False


def parse_windows(spec_windows: list[dict[str, object]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for window in spec_windows:
        start = parse_hexish(window["start"])
        end = parse_hexish(window["end_exclusive"])
        out.append((start, end))
    return out


def validate_spec_addresses(
    spec: dict,
    range_lookup: dict[str, tuple[int, int]],
    target_windows: list[tuple[int, int]],
    source_windows: list[tuple[int, int]],
) -> None:
    for group in spec.get("absolute_rewrite_groups", []):
        range_name = group["range"]
        if range_name not in range_lookup:
            raise RuntimeError(f"Unknown rewrite range in spec: {range_name}")
        for mapping in group["mappings"]:
            old_address = parse_hexish(mapping["old"])
            if not value_in_windows(old_address, source_windows):
                raise RuntimeError(
                    f"Spec rewrite old address 0x{old_address:08X} in range {range_name} is outside declared arcade windows."
                )

    for rule in spec.get("window_rewrite_rules", []):
        range_name = rule["range"]
        if range_name not in range_lookup:
            raise RuntimeError(f"Unknown window rewrite range in spec: {range_name}")
        old_start_raw = rule.get("arcade_base", rule.get("old_start"))
        old_end_raw = rule.get("arcade_end", rule.get("old_end_exclusive"))
        if old_start_raw is None or old_end_raw is None:
            raise RuntimeError(
                f"Window rewrite rule for range {range_name} must define arcade_base/arcade_end (or old_start/old_end_exclusive)."
            )
        old_start = parse_hexish(old_start_raw)
        old_end = parse_hexish(old_end_raw)
        has_symbol = "symbol" in rule
        has_new_start = "new_start" in rule
        if has_symbol == has_new_start:
            raise RuntimeError(
                f"Window rewrite rule in range {range_name} must set exactly one of symbol or new_start."
            )
        if old_end <= old_start:
            raise RuntimeError(f"Invalid window rewrite bounds in spec for {range_name}.")
        if not value_in_windows(old_start, source_windows):
            raise RuntimeError(
                f"Window rewrite old_start 0x{old_start:08X} in range {range_name} is outside declared arcade windows."
            )
        if not value_in_windows(old_end - 1, source_windows):
            raise RuntimeError(
                f"Window rewrite old_end_exclusive 0x{old_end:08X} in range {range_name} is outside declared arcade windows."
            )
        if has_new_start:
            new_start = parse_hexish(rule["new_start"])
            if not value_in_windows(new_start, target_windows):
                raise RuntimeError(
                    f"Window rewrite new_start 0x{new_start:08X} in range {range_name} is outside declared rewrite target windows."
                )

    for shim in spec.get("shim_jumps", []):
        start = parse_hexish(shim["start"])
        end = parse_hexish(shim["end_exclusive"])
        if not value_in_windows(start, source_windows) or not value_in_windows(end - 1, source_windows):
            raise RuntimeError(f"Shim jump window {shim['id']} is outside declared arcade windows.")

    for entry in spec.get("copied_ranges", []):
        start = parse_hexish(entry["start"])
        end = parse_hexish(entry["end_exclusive"])
        if not value_in_windows(start, source_windows) or not value_in_windows(end - 1, source_windows):
            raise RuntimeError(f"Copied range {entry['name']} is outside declared arcade windows.")

    for window in target_windows:
        if window[1] <= window[0]:
            raise RuntimeError("Invalid declared rewrite target window with non-positive size.")


def parse_opcode_set(values: list[object]) -> set[int]:
    out: set[int] = set()
    for raw in values:
        out.add(parse_hexish(raw) & 0xFFFF)
    return out


def build_rom_call_scan_windows(
    scan_mode: str,
    copied_ranges: list[dict[str, object]],
    range_lookup: dict[str, tuple[int, int]],
    whole_copy_cfg: dict[str, object],
    whole_copy_enabled: bool,
    whole_copy_mode: str | None,
) -> list[tuple[str, int, int]]:
    windows: list[tuple[str, int, int]] = []

    if scan_mode == "whole_maincpu_copy_window":
        if not (whole_copy_enabled and whole_copy_mode == "whole_maincpu_relocated"):
            raise RuntimeError(
                "rom_absolute_call_relocation scan_ranges=whole_maincpu_copy_window requires whole_maincpu_relocated mode."
            )
        source_start = parse_hexish(whole_copy_cfg["source_start"])
        source_end = parse_hexish(whole_copy_cfg["source_end_exclusive"])
        windows.append(("whole_maincpu_copy_window", source_start, source_end))
        return windows

    if scan_mode == "all_original_code_copied_ranges":
        for entry in copied_ranges:
            if entry.get("kind") != "original_code":
                continue
            range_name = str(entry["name"])
            range_start, range_end = range_lookup[range_name]
            windows.append((range_name, range_start, range_end))
        return windows

    raise RuntimeError(f"Unsupported rom_absolute_call_relocation scan_ranges mode: {scan_mode}")


def rewrite_absolute_rom_targets_in_scan_windows(
    rom_bytes: bytearray,
    maincpu_bytes: bytes,
    scan_windows: list[tuple[str, int, int]],
    relocation_delta: int,
    execute_from_relocated_base: bool,
    source_start: int,
    source_end: int,
    opcode_set: set[int],
) -> list[dict[str, object]]:
    if not execute_from_relocated_base or relocation_delta == 0:
        return []

    rewrite_log: list[dict[str, object]] = []

    for range_name, range_start, range_end in scan_windows:
        runtime_start = range_start + relocation_delta
        runtime_end = range_end + relocation_delta

        source_cursor = range_start
        runtime_cursor = runtime_start
        count = 0
        unresolved = 0
        while runtime_cursor + 6 <= runtime_end:
            opcode = int.from_bytes(maincpu_bytes[source_cursor:source_cursor + 2], "big")
            if opcode in opcode_set:
                source_target = int.from_bytes(maincpu_bytes[source_cursor + 2:source_cursor + 6], "big")
                runtime_target = int.from_bytes(rom_bytes[runtime_cursor + 2:runtime_cursor + 6], "big")
                if source_start <= source_target < source_end:
                    relocated_target = source_target + relocation_delta
                    if runtime_target != relocated_target:
                        rom_bytes[runtime_cursor + 2:runtime_cursor + 6] = relocated_target.to_bytes(4, "big")
                        if runtime_target == source_target:
                            unresolved += 1
                    count += 1
                source_cursor += 6
                runtime_cursor += 6
            else:
                source_cursor += 2
                runtime_cursor += 2

        if count > 0:
            rewrite_log.append(
                {
                    "range": range_name,
                    "kind": "absolute_rom_target_relocation",
                    "source_start": f"0x{source_start:06X}",
                    "source_end_exclusive": f"0x{source_end:06X}",
                    "relocation_delta": f"0x{relocation_delta:06X}",
                    "count": count,
                    "unresolved_before_fix": unresolved,
                }
            )

    return rewrite_log


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
    scan_step: int,
) -> int:
    replacements = 0

    for location in range(range_start, range_end - 3, scan_step):
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


def build_normal_continue_stub(target_address: int) -> bytes:
    return (
        bytes((0x4E, 0xF9))
        + target_address.to_bytes(4, "big")
        + (b"\x4E\x71" * 7)
    )


def build_absolute_jump(target_address: int, length: int) -> bytes:
    if length < 6:
        raise ValueError("Absolute jump patch must be at least 6 bytes long.")
    return bytes((0x4E, 0xF9)) + target_address.to_bytes(4, "big") + (b"\x4E\x71" * ((length - 6) // 2))


def accumulated_shift_before(addr: int, shift_deltas: list[tuple[int, int]]) -> int:
    total = 0
    for shift_addr, delta in shift_deltas:
        if shift_addr < addr:
            total += delta
        else:
            break
    return total


def is_lea_abs_long_opcode(opcode: int) -> bool:
    """Return True for LEA abs.l,An encoding in the low 16-bit opcode."""
    b0 = (opcode >> 8) & 0xFF
    b1 = opcode & 0xFF
    return (b0 & 0xC1) == 0x41 and b1 == 0xF9


def maybe_shift_abs_long_expected_bytes(
    expected: bytes,
    shift_deltas: list[tuple[int, int]],
    source_start: int,
    source_end: int,
) -> bytes:
    """
    Adjust single-instruction abs.l expected bytes to match shifted output.

    This keeps opcode_replace validation coupled to shift_table_patcher output
    when the expected sequence is exactly one 6-byte abs.l control-transfer or
    LEA abs.l instruction with a source-range target.
    """
    if len(expected) != 6:
        return expected

    opcode = int.from_bytes(expected[0:2], "big")
    is_abs_long_ref = opcode in (0x4EB9, 0x4EF9) or is_lea_abs_long_opcode(opcode)
    if not is_abs_long_ref:
        return expected

    old_target = int.from_bytes(expected[2:6], "big")
    if not (source_start <= old_target < source_end):
        return expected

    shifted_target = old_target + accumulated_shift_before(old_target, shift_deltas)
    if shifted_target == old_target:
        return expected

    return expected[0:2] + shifted_target.to_bytes(4, "big")


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


def patch_startup_vectors(rom_bytes: bytearray, reset_entry: int) -> None:
    # Keep SGDK-provided initial SP (0x000000..0x000003) and force reset PC to launcher.
    rom_bytes[0x000004:0x000008] = reset_entry.to_bytes(4, "big")


def build_relocation_map(
    variant: str,
    rom_path: Path,
    maincpu_path: Path,
    copied_ranges: list[dict[str, object]],
    symbol_addresses: dict[str, int],
    test_stub_address: int,
    whole_copy_summary: dict[str, object] | None,
    keep_identity_overlays: bool,
    relocation_delta: int,
) -> dict:
    object_entries: list[dict[str, object]] = []
    generated_entries: list[dict[str, object]] = []

    for entry in copied_ranges:
        start = int(str(entry["start"]), 16)
        end = int(str(entry["end_exclusive"]), 16)
        if keep_identity_overlays:
            rom_start = start
            rom_end = end
            placement = "identity_copy"
        else:
            rom_start = start + relocation_delta
            rom_end = end + relocation_delta
            placement = "relocated_window"

        object_entries.append(
            {
                "id": f"maincpu:{start:06X}-{end - 1:06X}",
                "name": entry["name"],
                "kind": "original_code_or_data",
                "source_rom": str(maincpu_path.resolve()),
                "original_start": f"0x{start:06X}",
                "original_end_exclusive": f"0x{end:06X}",
                "genesis_rom_start": f"0x{rom_start:06X}",
                "genesis_rom_end_exclusive": f"0x{rom_end:06X}",
                "placement": placement,
            }
        )

    if whole_copy_summary is not None:
        object_entries.insert(
            0,
            {
                "id": "maincpu:whole_relocated",
                "name": "whole_maincpu_relocated",
                "kind": "original_code_or_data",
                "source_rom": str(maincpu_path.resolve()),
                "original_start": str(whole_copy_summary["source_start"]),
                "original_end_exclusive": str(whole_copy_summary["source_end_exclusive"]),
                "genesis_rom_start": str(whole_copy_summary["dest_start"]),
                "genesis_rom_end_exclusive": str(whole_copy_summary["dest_end_exclusive"]),
                "placement": "relocated_whole_copy",
            },
        )

    stub_base = relocation_delta
    normal_stub_start = 0x03B05C + stub_base
    normal_stub_end = 0x03B070 + stub_base

    generated_entries.extend(
        [
            {
                "id": "startup_common.normal_result_stub",
                "kind": "generated_stub",
                "genesis_rom_start": f"0x{normal_stub_start:06X}",
                "genesis_rom_end_exclusive": f"0x{normal_stub_end:06X}",
                "replaces_original_range": f"0x{normal_stub_start:06X}..0x{normal_stub_end - 1:06X}",
                "reason": "Jump from the branch-based normal path into the Genesis continuation wrapper without shifting ROM layout.",
            },
            {
                "id": "startup_common.test_result_stub",
                "kind": "generated_stub",
                "genesis_rom_start": f"0x{test_stub_address:06X}",
                "genesis_rom_end_exclusive": f"0x{test_stub_address + 14:06X}",
                "replaces_original_range": f"0x{test_stub_address:06X}..0x{test_stub_address + 13:06X}",
                "reason": "Terminate test-mode branch locally and return to Genesis runner.",
            },
            {
                "id": "genesistan_run_original_startup_common",
                "kind": "runner_wrapper",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_run_original_startup_common']:06X}",
                "purpose": "C/asm wrapper that calls the original startup/common slice.",
            },
            {
                "id": "genesistan_sound_send_command",
                "kind": "sound_shim",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_sound_send_command']:06X}",
                "purpose": "Minimal Genesis-side sound command shim for the original 0x03F084 helper.",
            },
            {
                "id": "genesistan_sound_read_status",
                "kind": "sound_shim",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_sound_read_status']:06X}",
                "purpose": "Always-ready sound status shim for the original 0x03F09C helper.",
            },
            {
                "id": "genesistan_run_original_frontend_tick",
                "kind": "runner_wrapper",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_run_original_frontend_tick']:06X}",
                "purpose": "Frame-tick wrapper that enters the original front-end dispatcher at 0x03A008 and returns via a synthetic exception frame.",
            },
            {
                "id": "genesistan_startup_common_exit_normal",
                "kind": "runner_trampoline",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_startup_common_exit_normal']:06X}",
                "purpose": "Return trampoline for the normal branch after patched original flow.",
            },
            {
                "id": "genesistan_startup_common_continue_normal",
                "kind": "runner_continuation",
                "genesis_rom_start": f"0x{symbol_addresses['genesistan_startup_common_continue_normal']:06X}",
                "purpose": "Replays the original 0x03B05C normal-boot continuation before returning to the Genesis host.",
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
    spec_path = Path(args.spec)
    spec = load_remap_spec(spec_path)
    range_lookup = build_range_lookup(spec)
    range_kind_lookup = build_range_kind_lookup(spec)
    required_symbols = tuple(spec.get("required_symbols", []))
    source_windows = parse_windows(spec.get("declared_arcade_windows", []))
    target_windows = parse_windows(spec.get("declared_rewrite_target_windows", []))
    validate_spec_addresses(spec, range_lookup, target_windows, source_windows)

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

    symbol_addresses = parse_symbol_table(symbols_path, required_symbols)
    rom_bytes = bytearray(rom_path.read_bytes())
    preserved_genesis_vectors = bytes(rom_bytes[0x000000:0x000400])
    maincpu_bytes = maincpu_path.read_bytes()

    # Apply variable-length opcode replacements before any other patching.
    shift_deltas: list[tuple[int, int]] = []
    if spec.get("shift_replacements"):
        from shift_table_patcher import apply_shift_table as _apply_shift_table
        _whole = spec.get("whole_maincpu_copy", {})
        _src_start = parse_hexish(_whole.get("source_start", "0x000000"))
        _src_end = parse_hexish(_whole.get("source_end_exclusive", "0x060000"))
        _disasm = str(Path(__file__).resolve().parents[2] / "build" / "maincpu.disasm.txt")
        for _rep in spec["shift_replacements"]:
            _pc = parse_hexish(_rep["arcade_pc"])
            _orig = bytes.fromhex(_rep["original_bytes"].replace(" ", ""))
            _repl = bytes.fromhex(_rep["replacement_bytes"].replace(" ", ""))
            shift_deltas.append((_pc, len(_repl) - len(_orig)))
        shift_deltas.sort(key=lambda x: x[0])
        maincpu_bytes = bytes(
            _apply_shift_table(
                maincpu_bytes,
                spec["shift_replacements"],
                _disasm,
                _src_start,
                _src_end,
                spec.get("jump_table_word_displacements", []),
            )
        )

    ensure_rom_size(rom_bytes)

    whole_copy_cfg = spec.get("whole_maincpu_copy", {})
    whole_copy_mode = spec.get("policy", {}).get("current_copy_mode")
    execute_from_relocated_base = bool(spec.get("policy", {}).get("execute_from_relocated_base", False))
    keep_identity_overlays = bool(spec.get("policy", {}).get("keep_identity_overlays_for_bringup", True))
    whole_copy_enabled = bool(whole_copy_cfg.get("enabled", False))
    whole_copy_summary: dict[str, object] | None = None
    relocation_delta = 0
    if whole_copy_enabled and whole_copy_mode == "whole_maincpu_relocated":
        source_start = parse_hexish(whole_copy_cfg["source_start"])
        source_end = parse_hexish(whole_copy_cfg["source_end_exclusive"])
        dest_start = parse_hexish(whole_copy_cfg["dest_start"])
        relocation_delta = dest_start - source_start
        source_size = source_end - source_start
        if source_size <= 0:
            raise RuntimeError("whole_maincpu_copy has invalid source window size.")
        if source_end > len(maincpu_bytes):
            raise RuntimeError(
                f"whole_maincpu_copy source_end_exclusive 0x{source_end:06X} exceeds maincpu input size 0x{len(maincpu_bytes):06X}."
            )
        if not value_in_windows(dest_start, target_windows):
            raise RuntimeError(
                f"whole_maincpu_copy destination 0x{dest_start:06X} is outside declared rewrite target windows."
            )
        if not value_in_windows(dest_start + source_size - 1, target_windows):
            raise RuntimeError(
                f"whole_maincpu_copy destination end 0x{(dest_start + source_size):06X} is outside declared rewrite target windows."
            )
        ensure_size_at_least(rom_bytes, dest_start + source_size)
        rom_bytes[dest_start:dest_start + source_size] = maincpu_bytes[source_start:source_end]
        whole_copy_summary = {
            "source_start": f"0x{source_start:06X}",
            "source_end_exclusive": f"0x{source_end:06X}",
            "dest_start": f"0x{dest_start:06X}",
            "dest_end_exclusive": f"0x{dest_start + source_size:06X}",
            "size_bytes": source_size,
        }

    # Keep SGDK/launcher vector table intact (all 256 vectors, 0x000000..0x0003FF).
    # 68000 vectors extend beyond 0x0001FF; clobbering 0x000200..0x0003FF causes
    # exception vectors to point into garbage and crash before launcher UI draws.
    rom_bytes[0x000000:0x000400] = preserved_genesis_vectors

    copied_ranges: list[dict[str, object]] = []
    copied_range_entries = spec["copied_ranges"]
    rom_call_reloc_log: list[dict[str, object]] = []
    for entry in spec["copied_ranges"]:
        start = parse_hexish(entry["start"])
        end = parse_hexish(entry["end_exclusive"])
        name = entry["name"]
        if keep_identity_overlays:
            copy_range(rom_bytes, maincpu_bytes, start, end)
        copied_ranges.append(
            {
                "name": name,
                "start": f"0x{start:06X}",
                "end_exclusive": f"0x{end:06X}",
                "size_bytes": end - start,
                "runtime_start": f"0x{(start + (relocation_delta if execute_from_relocated_base else 0)):06X}",
                "runtime_end_exclusive": f"0x{(end + (relocation_delta if execute_from_relocated_base else 0)):06X}",
            }
        )

    rom_call_reloc_cfg = spec.get("rom_absolute_call_relocation", {})
    if bool(rom_call_reloc_cfg.get("enabled", False)):
        source_start = parse_hexish(rom_call_reloc_cfg["source_start"])
        source_end = parse_hexish(rom_call_reloc_cfg["source_end_exclusive"])
        scan_mode = str(rom_call_reloc_cfg.get("scan_ranges", "all_original_code_copied_ranges"))
        scan_windows = build_rom_call_scan_windows(
            scan_mode,
            copied_range_entries,
            range_lookup,
            whole_copy_cfg,
            whole_copy_enabled,
            whole_copy_mode,
        )
        opcode_set = parse_opcode_set(rom_call_reloc_cfg.get("opcodes_with_abs_long_operand", []))
        if source_end <= source_start:
            raise RuntimeError("rom_absolute_call_relocation has invalid source window.")
        rom_call_reloc_log = rewrite_absolute_rom_targets_in_scan_windows(
            rom_bytes,
            maincpu_bytes,
            scan_windows,
            relocation_delta,
            execute_from_relocated_base,
            source_start,
            source_end,
            opcode_set,
        )

    rewrite_log: list[dict[str, object]] = []
    rewrite_log.extend(rom_call_reloc_log)
    for group in spec.get("absolute_rewrite_groups", []):
        range_name = group["range"]
        range_start, range_end = range_lookup[range_name]
        if execute_from_relocated_base:
            range_start += relocation_delta
            range_end += relocation_delta
        for mapping in group["mappings"]:
            old_address = parse_hexish(mapping["old"])
            new_address = symbol_addresses[mapping["symbol"]] + int(mapping.get("offset", 0))
            if not value_in_windows(new_address, target_windows):
                raise RuntimeError(
                    f"Rewrite target 0x{new_address:08X} in range {range_name} is outside declared rewrite target windows."
                )
            count = rewrite_long_in_range(
                rom_bytes,
                range_start,
                range_end,
                old_address,
                new_address,
            )
            rewrite_log.append(
                {
                    "range": range_name,
                    "old": f"0x{old_address:08X}",
                    "new": f"0x{new_address:08X}",
                    "count": count,
                }
            )

    for rule in spec.get("window_rewrite_rules", []):
        range_name = rule["range"]
        range_kind = range_kind_lookup.get(range_name, "original_code_or_data")
        allow_in_code = bool(rule.get("allow_in_code", False))
        if range_kind == "original_code" and not allow_in_code:
            rewrite_log.append(
                {
                    "range": range_name,
                    "kind": "window_rewrite_skipped",
                    "reason": "range_is_code",
                    "hint": "Set allow_in_code=true only for audited table slices.",
                }
            )
            continue
        range_start, range_end = range_lookup[range_name]
        if execute_from_relocated_base:
            range_start += relocation_delta
            range_end += relocation_delta
        old_start_raw = rule.get("arcade_base", rule.get("old_start"))
        old_end_raw = rule.get("arcade_end", rule.get("old_end_exclusive"))
        if old_start_raw is None or old_end_raw is None:
            raise RuntimeError(
                f"Window rewrite rule for range {range_name} must define arcade_base/arcade_end (or old_start/old_end_exclusive)."
            )
        old_start = parse_hexish(old_start_raw)
        old_end = parse_hexish(old_end_raw)
        offset = int(rule.get("offset", 0))
        if "symbol" in rule:
            new_start = symbol_addresses[rule["symbol"]] + offset
            target_desc = f"symbol:{rule['symbol']}"
        else:
            new_start = parse_hexish(rule["new_start"]) + offset
            target_desc = f"literal:{rule['new_start']}"
        scan_step = int(rule.get("scan_step", 2))
        if scan_step <= 0 or (scan_step % 2) != 0:
            raise RuntimeError(f"Invalid window rewrite scan_step={scan_step} in range {range_name}.")
        if not value_in_windows(new_start, target_windows):
            raise RuntimeError(
                f"Window rewrite target start 0x{new_start:08X} in range {range_name} is outside declared rewrite target windows."
            )
        count = rewrite_window_in_range(
            rom_bytes,
            range_start,
            range_end,
            old_start,
            old_end,
            new_start,
            scan_step,
        )
        rewrite_log.append(
            {
                "range": range_name,
                "old_window_start": f"0x{old_start:08X}",
                "old_window_end_exclusive": f"0x{old_end:08X}",
                "new_window_start": f"0x{new_start:08X}",
                "target": target_desc,
                "scan_step": scan_step,
                "count": count,
            }
        )

    for restore in spec.get("verbatim_restores", []):
        start = parse_hexish(restore["start"])
        end = parse_hexish(restore["end_exclusive"])
        if execute_from_relocated_base:
            rom_bytes[start + relocation_delta:end + relocation_delta] = maincpu_bytes[start:end]
        elif keep_identity_overlays:
            rom_bytes[start:end] = maincpu_bytes[start:end]

    for shim in spec.get("shim_jumps", []):
        start = parse_hexish(shim["start"])
        end = parse_hexish(shim["end_exclusive"])
        if execute_from_relocated_base:
            start += relocation_delta
            end += relocation_delta
        target = symbol_addresses[shim["symbol"]]
        if not value_in_windows(target, target_windows):
            raise RuntimeError(
                f"Shim target 0x{target:08X} for {shim['id']} is outside declared rewrite target windows."
            )
        rom_bytes[start:end] = build_absolute_jump(target, end - start)
        rewrite_log.append(
            {
                "range": shim["id"],
                "kind": "shim_jump",
                "old_start": f"0x{start:06X}",
                "old_end_exclusive": f"0x{end:06X}",
                "new_target": f"0x{target:08X}",
            }
        )

    for replacement in spec.get("opcode_replace", []):
        arcade_pc = parse_hexish(replacement["arcade_pc"])
        expected = bytes.fromhex(
            replacement["original_bytes"].replace(" ", ""))
        expected_shifted = maybe_shift_abs_long_expected_bytes(
            expected,
            shift_deltas,
            source_start,
            source_end,
        )
        new_bytes = bytes.fromhex(
            replacement["replacement_bytes"].replace(" ", ""))
        if len(expected) != len(new_bytes):
            raise RuntimeError(
                f"opcode_replace at 0x{arcade_pc:06X}: "
                f"original_bytes and replacement_bytes "
                f"must be the same length.")
        rom_pc = arcade_pc + relocation_delta + accumulated_shift_before(arcade_pc, shift_deltas)
        actual = bytes(rom_bytes[rom_pc:rom_pc + len(expected)])
        if actual != expected and actual != expected_shifted:
            raise RuntimeError(
                f"opcode_replace at 0x{arcade_pc:06X}: "
                f"expected {expected.hex()} "
                f"but found {actual.hex()}")
        rom_bytes[rom_pc:rom_pc + len(new_bytes)] = new_bytes
        rewrite_log.append({
            "kind": "opcode_replace",
            "arcade_pc": f"0x{arcade_pc:06X}",
            "rom_pc": f"0x{rom_pc:06X}",
            "original_bytes": expected.hex(),
            "original_bytes_shift_adjusted": expected_shifted.hex() if expected_shifted != expected else "",
            "replacement_bytes": new_bytes.hex(),
            "note": replacement.get("note", ""),
        })

    # ── Palette pre-conversion (Build 113) ────────────────────────────────────
    # Fill genesistan_palette_rom_table in ROM with Genesis-format colour values.
    # Source: Taito xRGB-444 (bits 11:8=R, 7:4=G, 3:0=B, 4-bit components).
    # Target: Genesis 0000 BBB0 GGG0 RRR0 (3-bit components).
    # Conversion: take top 3 of each 4-bit component, pack into Genesis word.
    # Initial arcade palette RAM is all zeros at power-on; unreachable entries
    # use a greyscale ramp so tiles are visible with some colour.
    palette_rom_sym = symbol_addresses.get("genesistan_palette_rom_table")
    if palette_rom_sym is not None and palette_rom_sym < 0x800000:
        _PALETTE_ENTRIES = 2048
        _palette_data = bytearray(_PALETTE_ENTRIES * 2)

        def _taito_to_genesis(src: int) -> int:
            r3 = ((src >> 8) & 0xF) >> 1
            g3 = ((src >> 4) & 0xF) >> 1
            b3 = (src & 0xF) >> 1
            return (r3 << 1) | (g3 << 5) | (b3 << 9)

        # Greyscale ramp: entry 0 of each 16-entry bank = black,
        # entries 1-15 = increasing brightness.  Applied to ALL 2048 entries
        # since runtime palette writes are not yet intercepted (Build 113).
        import struct as _struct
        for _i in range(_PALETTE_ENTRIES):
            _color = _i % 16
            if _color == 0:
                _gen = 0
            else:
                _v = min(7, (_color * 7 + 14) // 15)
                _gen = (_v << 1) | (_v << 5) | (_v << 9)
            _struct.pack_into(">H", _palette_data, _i * 2, _gen)

        _table_off = palette_rom_sym
        ensure_size_at_least(rom_bytes, _table_off + len(_palette_data))
        rom_bytes[_table_off:_table_off + len(_palette_data)] = _palette_data
        rewrite_log.append({
            "kind": "palette_pre_conversion",
            "rom_offset": f"0x{_table_off:06X}",
            "entries": _PALETTE_ENTRIES,
            "note": "Greyscale ramp, 2048 entries, 16-level per bank.  Build 113 placeholder.",
        })

    # Write Genesis workram base pointer at ROM offset 0x10C000.
    # The arcade frontend tick reloads A5 from this absolute address.
    # On arcade it is work RAM. On Genesis it is ROM, so we patch
    # it to contain the Genesis workram base address.
    workram_anchor_offset = 0x10C000
    workram_addr = symbol_addresses.get("genesistan_arcade_workram_words")
    if workram_addr is not None:
        ensure_size_at_least(rom_bytes, workram_anchor_offset + 4)
        rom_bytes[workram_anchor_offset:workram_anchor_offset + 4] = \
            workram_addr.to_bytes(4, "big")
        rewrite_log.append({
            "kind": "workram_anchor",
            "rom_offset": f"0x{workram_anchor_offset:06X}",
            "value": f"0x{workram_addr:08X}",
            "note": "Genesis workram base at ROM 0x10C000 "
                    "so arcade A5 reload finds correct base.",
        })

    stub_cfg = spec["generated_stubs"]
    test_jump_patch_address = parse_hexish(stub_cfg["test_jump_patch_address"])
    normal_stub_start = parse_hexish(stub_cfg["normal_stub_start"])
    normal_stub_end = parse_hexish(stub_cfg["normal_stub_end_exclusive"])
    test_stub_address = parse_hexish(stub_cfg["test_stub_address"])
    test_stub_end = parse_hexish(stub_cfg["test_stub_end_exclusive"])
    test_result_value = int(stub_cfg["test_result_value"])
    if execute_from_relocated_base:
        test_jump_patch_address += relocation_delta
        normal_stub_start += relocation_delta
        normal_stub_end += relocation_delta
        test_stub_address += relocation_delta
        test_stub_end += relocation_delta

    rom_bytes[test_jump_patch_address:test_jump_patch_address + 4] = test_stub_address.to_bytes(4, "big")
    rom_bytes[normal_stub_start:normal_stub_end] = build_normal_continue_stub(
        symbol_addresses["genesistan_startup_common_continue_normal"],
    )
    rom_bytes[test_stub_address:test_stub_end] = build_status_stub(
        test_result_value,
        symbol_addresses["genesistan_startup_result_code"],
        symbol_addresses["genesistan_startup_common_exit_test"],
    )

    patch_startup_vectors(rom_bytes, symbol_addresses["_reset_entry"])
    checksum = update_genesis_checksum(rom_bytes)
    rom_path.write_bytes(rom_bytes)

    manifest = {
        "variant": args.variant,
        "rom": str(rom_path.resolve()),
        "symbols": str(symbols_path.resolve()),
        "maincpu": str(maincpu_path.resolve()),
        "spec": str(spec_path.resolve()),
        "copied_ranges": copied_ranges,
        "whole_maincpu_copy": whole_copy_summary,
        "execute_from_relocated_base": execute_from_relocated_base,
        "keep_identity_overlays_for_bringup": keep_identity_overlays,
        "relocation_delta": f"0x{(relocation_delta & 0xFFFFFFFF):08X}",
        "rom_absolute_call_relocation": {
            "enabled": bool(rom_call_reloc_cfg.get("enabled", False)),
            "scan_ranges": rom_call_reloc_cfg.get("scan_ranges", "all_original_code_copied_ranges"),
            "source_start": rom_call_reloc_cfg.get("source_start"),
            "source_end_exclusive": rom_call_reloc_cfg.get("source_end_exclusive"),
            "opcode_count": len(rom_call_reloc_cfg.get("opcodes_with_abs_long_operand", [])),
        },
        "preserved_genesis_vector_table": {
            "start": "0x000000",
            "end_exclusive": "0x000400",
            "why": "Preserve SGDK/launcher exception vectors during offset-carry maincpu copy.",
        },
        "address_rewrites": rewrite_log,
        "normal_result_stub": {
            "address": f"0x{normal_stub_start:06X}",
            "jumps_to": f"0x{symbol_addresses['genesistan_startup_common_continue_normal']:08X}",
            "end_exclusive": f"0x{normal_stub_end:06X}",
        },
        "test_result_stub": {
            "address": f"0x{test_stub_address:06X}",
            "writes_status_to": f"0x{symbol_addresses['genesistan_startup_result_code']:08X}",
            "value": test_result_value,
            "jumps_exit_to": f"0x{symbol_addresses['genesistan_startup_common_exit_test']:08X}",
            "end_exclusive": f"0x{test_stub_end:06X}",
        },
        "test_jump_patch": {
            "patched_at": f"0x{test_jump_patch_address:06X}",
            "new_target": f"0x{test_stub_address:06X}",
        },
        "checksum": f"0x{checksum:04X}",
        "startup_vectors": {
            "initial_sp": f"0x{int.from_bytes(rom_bytes[0x000000:0x000004], 'big'):08X}",
            "reset_pc": f"0x{int.from_bytes(rom_bytes[0x000004:0x000008], 'big'):08X}",
            "forced_reset_pc_symbol": "_reset_entry",
        },
        "relocation_map": str(relocation_path.resolve()),
        "goal": "Execute the original startup/title/front-end remap from original ROM bytes using a spec-driven translation pass.",
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
        whole_copy_summary,
        keep_identity_overlays,
        relocation_delta if execute_from_relocated_base else 0,
    )
    relocation_path.write_text(json.dumps(relocation_map, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
