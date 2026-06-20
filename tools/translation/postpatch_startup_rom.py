#!/usr/bin/env python3
"""Post-build ROM patcher for the first executable startup slice."""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path


ROM_MIN_SIZE = 0x80000
DEFAULT_SPEC_PATH = Path(__file__).resolve().parents[2] / "specs" / "startup_title_remap.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_BOOKMARK_BASELINE_PATH = PROJECT_ROOT / "build" / "rastan-direct" / "active_bookmark_baseline.json"
BUILD_COUNTER_PATH = PROJECT_ROOT / "build" / "rastan-direct" / "build_counter.txt"

CANONICAL_OPCODE_REPLACE_COUNT = 95
# KF-028 fix (2026-06-17): +4 bytes from bsr rastan_direct_update_inputs.
# OPEN-016 Part 2 (2026-06-19): +0x54 bytes from glyph hook,
# plus +0x14 bytes for the Build 0091 helper-crash register setup.
CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CB58

# DIAGNOSTIC_SYMBOLS — symbols allowed for bookmarks_v2 helper_symbol resolution.
#
# Adding a new symbol to this tuple requires:
#   1. A Rule 10 (or successor) amendment justifying the diagnostic role
#   2. A design doc revision documenting the symbol's purpose
#   3. An AGENTS_LOG entry recording the addition
# This three-place friction prevents silent expansion. Do NOT add symbols
# speculatively.
DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)

SYMBOL_PATTERN = re.compile(r"^([0-9A-Fa-f]+)\s+\S+\s+(\S+)")
SYMBOL_TOKEN_PATTERN = re.compile(r"\{symbol:([A-Za-z_][A-Za-z0-9_]*)([+-](?:0x[0-9A-Fa-f]+|\d+))?\}")


def _compact_hex(value: str) -> str:
    compact = "".join(value.split())
    if len(compact) % 2 != 0 or re.fullmatch(r"[0-9A-Fa-f]*", compact) is None:
        raise RuntimeError(f"Invalid hex string: {value!r}")
    return compact


def _hex_len_bytes(value: str) -> int:
    return len(_compact_hex(value)) // 2


def _to_upper_hex(value: str) -> str:
    return _compact_hex(value).upper()


def _read_counter_value(path: Path) -> int:
    if not path.exists():
        return 0
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid build counter value in {path}: {raw!r}") from exc


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2) + "\n"
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
    tmp.replace(path)


def _bookmarks_v2(spec: dict[str, object]) -> list[dict[str, object]]:
    if "diagnostic_bookmarks" in spec:
        raise RuntimeError(
            "Legacy field 'diagnostic_bookmarks' is no longer supported. "
            "Use top-level 'bookmarks_v2' entries with runtime_genesis_pc."
        )
    raw = spec.get("bookmarks_v2", [])
    if raw in (None, {}):
        return []
    if not isinstance(raw, list):
        raise RuntimeError("bookmarks_v2 must be a JSON array when present.")
    out: list[dict[str, object]] = []
    seen_cycle_ids: set[str] = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise RuntimeError(f"bookmarks_v2[{idx}] must be an object.")
        cycle_id = str(item.get("cycle_id", "")).strip()
        if not cycle_id:
            raise RuntimeError(f"bookmarks_v2[{idx}] missing required cycle_id.")
        if cycle_id in seen_cycle_ids:
            raise RuntimeError(f"bookmarks_v2 contains duplicate cycle_id={cycle_id!r}.")
        seen_cycle_ids.add(cycle_id)
        out.append(item)
    if len(out) > 1:
        raise RuntimeError(
            "bookmarks_v2 has more than one entry. Rule 10 allows at most one in-flight bookmark cycle."
        )
    return out


def _reject_legacy_bookmark_cycle(spec: dict[str, object]) -> None:
    for idx, entry in enumerate(spec.get("opcode_replace", [])):
        if not isinstance(entry, dict):
            continue
        cycle = str(entry.get("bookmark_cycle", "")).strip()
        if cycle:
            raise RuntimeError(
                "Legacy opcode_replace bookmark field 'bookmark_cycle' is no longer supported under bookmarks_v2. "
                f"Found at opcode_replace[{idx}]={cycle!r}."
            )


def _build_bookmark_activator_bytes(helper_addr: int, span_length: int, nop_padding_word: int) -> bytes:
    if span_length < 6 or ((span_length - 6) % 2) != 0:
        raise RuntimeError(
            f"bookmarks_v2 span_length must be >= 6 and (span_length-6) divisible by 2; got {span_length}."
        )
    out = bytearray()
    out.extend((0x4E, 0xF9))
    out.extend((helper_addr & 0xFFFFFFFF).to_bytes(4, "big"))
    for _ in range((span_length - 6) // 2):
        out.extend((nop_padding_word & 0xFFFF).to_bytes(2, "big"))
    return bytes(out)


def _write_active_bookmark_baseline(bookmark_entry: dict[str, object]) -> None:
    cycle_id = str(bookmark_entry.get("cycle_id", "")).strip()
    pre_insert_sha = str(bookmark_entry.get("pre_insert_canonical_rom_sha256", "")).strip()
    if not cycle_id:
        raise RuntimeError("bookmarks_v2[0] missing required cycle_id for state-file write.")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", pre_insert_sha):
        raise RuntimeError(
            "bookmarks_v2[0] pre_insert_canonical_rom_sha256 must be a 64-hex SHA256 string."
        )
    payload = {
        "cycle_id": cycle_id,
        "pre_insert_canonical_rom_sha256": pre_insert_sha.lower(),
        "pre_insert_build_counter": _read_counter_value(BUILD_COUNTER_PATH),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    _atomic_write_json(ACTIVE_BOOKMARK_BASELINE_PATH, payload)


def _apply_bookmarks_v2(
    rom_bytes: bytearray,
    bookmarks_v2: list[dict[str, object]],
    symbol_addresses: dict[str, int],
    helper_guard_symbol: str = "genesistan_diag_bookmark",
) -> list[dict[str, object]]:
    if not bookmarks_v2:
        return []

    helper_guard_addr = resolve_symbol_address(symbol_addresses, helper_guard_symbol)
    helper_guard_start = helper_guard_addr
    helper_guard_end = helper_guard_addr + 2
    sensitive_region_low = 0x00000400
    helper_data_region_end = 0x000F1DBC
    applied: list[dict[str, object]] = []

    for idx, entry in enumerate(bookmarks_v2):
        if "arcade_pc" in entry:
            raise RuntimeError(
                f"bookmarks_v2[{idx}] must not contain arcade_pc. "
                "Use runtime_genesis_pc (trace-space coordinate) only."
            )
        cycle_id = str(entry.get("cycle_id", "")).strip()
        runtime_genesis_pc = parse_hexish(entry.get("runtime_genesis_pc"))
        span_length = int(entry.get("span_length"))
        helper_symbol = str(entry.get("helper_symbol", "")).strip()
        activator_pattern = str(entry.get("activator_pattern", "")).strip()
        nop_padding_raw = str(entry.get("nop_padding_byte", "")).strip() or "0x4E71"
        pre_insert_bytes = str(entry.get("pre_insert_canonical_bytes", "")).strip()

        if helper_symbol not in DIAGNOSTIC_SYMBOLS:
            raise RuntimeError(
                f"bookmarks_v2[{idx}] helper_symbol={helper_symbol!r} is not in DIAGNOSTIC_SYMBOLS allowlist."
            )
        if activator_pattern != "JMP_LONG_ABS":
            raise RuntimeError(
                f"bookmarks_v2[{idx}] unsupported activator_pattern={activator_pattern!r}; "
                "supported: JMP_LONG_ABS."
            )
        if runtime_genesis_pc < sensitive_region_low:
            raise RuntimeError(
                f"bookmarks_v2[{idx}] runtime_genesis_pc=0x{runtime_genesis_pc:08X} is in preserved-vectors region "
                "(< 0x00000400)."
            )
        if span_length < 6 or ((span_length - 6) % 2) != 0:
            raise RuntimeError(
                f"bookmarks_v2[{idx}] invalid span_length={span_length}; must be >=6 and (span_length-6) divisible by 2."
            )
        if runtime_genesis_pc < 0 or runtime_genesis_pc + span_length > len(rom_bytes):
            raise RuntimeError(
                f"bookmarks_v2[{idx}] out of bounds: runtime_genesis_pc=0x{runtime_genesis_pc:08X}, "
                f"span_length={span_length}, rom_size=0x{len(rom_bytes):X}."
            )

        span_start = runtime_genesis_pc
        span_end = runtime_genesis_pc + span_length
        if not (span_end <= helper_guard_start or span_start >= helper_guard_end):
            raise RuntimeError(
                f"bookmarks_v2[{idx}] span overlaps helper bytes: cycle_id={cycle_id!r}, "
                f"span=[0x{span_start:08X},0x{span_end:08X}), "
                f"helper=[0x{helper_guard_start:08X},0x{helper_guard_end:08X})."
            )
        if span_end > helper_data_region_end:
            print(
                "WARNING: bookmarks_v2 target extends beyond helper/data-adjacent region upper bound "
                f"(0x{helper_data_region_end:08X}): cycle_id={cycle_id!r} span_end=0x{span_end:08X}"
            )

        if pre_insert_bytes:
            if _hex_len_bytes(pre_insert_bytes) != span_length:
                raise RuntimeError(
                    f"bookmarks_v2[{idx}] pre_insert_canonical_bytes length mismatch: "
                    f"expected {span_length} bytes, got {_hex_len_bytes(pre_insert_bytes)} bytes."
                )

        helper_addr = resolve_symbol_address(symbol_addresses, helper_symbol)
        nop_padding_word = int(nop_padding_raw, 0)
        if nop_padding_word < 0 or nop_padding_word > 0xFFFF:
            raise RuntimeError(
                f"bookmarks_v2[{idx}] nop_padding_byte must fit 16-bit word; got {nop_padding_raw!r}."
            )
        activator_bytes = _build_bookmark_activator_bytes(helper_addr, span_length, nop_padding_word)
        rom_bytes[span_start:span_end] = activator_bytes
        applied.append(
            {
                "cycle_id": cycle_id,
                "runtime_genesis_pc": f"0x{runtime_genesis_pc:08X}",
                "span_length": span_length,
                "helper_symbol": helper_symbol,
                "helper_address": f"0x{helper_addr:08X}",
                "activator_pattern": activator_pattern,
                "activator_bytes": activator_bytes.hex(),
            }
        )

    _write_active_bookmark_baseline(bookmarks_v2[0])
    return applied


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


def resolve_symbol_address(symbol_addresses: dict[str, int], name: str) -> int:
    if name in symbol_addresses:
        return symbol_addresses[name]
    alt_name = f"_{name}"
    if alt_name in symbol_addresses:
        return symbol_addresses[alt_name]
    raise RuntimeError(f"Replacement references missing symbol: {name}")


def resolve_replacement_hex(raw_hex: str, symbol_addresses: dict[str, int]) -> str:
    def _replace(match: re.Match[str]) -> str:
        symbol_name = match.group(1)
        offset_text = match.group(2)
        addr = resolve_symbol_address(symbol_addresses, symbol_name)
        if offset_text:
            addr += int(offset_text, 0)
        return f"{addr & 0xFFFFFFFF:08X}"

    expanded = SYMBOL_TOKEN_PATTERN.sub(_replace, raw_hex)
    compact = "".join(expanded.split())
    if len(compact) % 2 != 0:
        raise RuntimeError(f"replacement_bytes is not byte-aligned after symbol expansion: {raw_hex!r}")
    if compact and re.fullmatch(r"[0-9A-Fa-f]+", compact) is None:
        raise RuntimeError(f"replacement_bytes contains non-hex data after symbol expansion: {raw_hex!r}")
    return compact


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


def _hex6(value: int) -> str:
    return f"0x{value:06X}"


def _hex8(value: int) -> str:
    return f"0x{value:08X}"


def _segment_bounds(segment: dict[str, object]) -> tuple[int, int]:
    return parse_hexish(segment["genesis_start"]), parse_hexish(segment["genesis_end_exclusive"])


def _append_segment(segments: list[dict[str, object]], sequence: list[int], record: dict[str, object]) -> None:
    sequence[0] += 1
    rec = dict(record)
    rec["_seq"] = sequence[0]
    segments.append(rec)


def _slice_segment(segment: dict[str, object], new_start: int, new_end: int) -> dict[str, object]:
    old_start, old_end = _segment_bounds(segment)
    if not (old_start <= new_start <= new_end <= old_end):
        raise RuntimeError("Invalid segment slice bounds.")

    out = dict(segment)
    out["genesis_start"] = _hex6(new_start)
    out["genesis_end_exclusive"] = _hex6(new_end)
    out["size_bytes"] = new_end - new_start

    kind = str(segment["kind"])
    if kind == "arcade_copy":
        identity_offset = int(segment["identity_offset"])
        out["arcade_start"] = _hex6(new_start - identity_offset)
        out["arcade_end_exclusive"] = _hex6(new_end - identity_offset)
    elif kind == "patched_site":
        shift_delta = int(segment["shift_delta"])
        offset = new_start - old_start
        if shift_delta != 0 and (new_start != old_start or new_end != old_end):
            raise RuntimeError(
                "Cannot slice a non-zero shift_delta patched_site segment; "
                "no interior mapping is defined."
            )
        if shift_delta == 0:
            arc_start = parse_hexish(segment["arcade_start"]) + offset
            out["arcade_start"] = _hex6(arc_start)
            out["arcade_end_exclusive"] = _hex6(arc_start + (new_end - new_start))
            hex_off = offset * 2
            hex_len = (new_end - new_start) * 2
            out["original_bytes"] = str(segment["original_bytes"])[hex_off:hex_off + hex_len]
            out["replacement_bytes"] = str(segment["replacement_bytes"])[hex_off:hex_off + hex_len]
    return out


def _segment_signature(segment: dict[str, object]) -> tuple[object, ...]:
    kind = str(segment["kind"])
    if kind == "arcade_copy":
        return (
            kind,
            segment["source"],
            int(segment["identity_offset"]),
        )
    if kind == "patched_site":
        return (
            kind,
            segment["origin"],
            segment["arcade_start"],
            segment["arcade_end_exclusive"],
            segment["original_bytes"],
            segment["replacement_bytes"],
            segment["note"],
            int(segment["shift_delta"]),
        )
    if kind == "preserved_vectors":
        return (kind, segment["tag"])
    if kind == "genesis_only":
        return (kind, segment["tag"])
    raise RuntimeError(f"Unknown segment kind for signature: {kind}")


def _merge_adjacent_segments(segments: list[dict[str, object]]) -> list[dict[str, object]]:
    if not segments:
        return []
    merged: list[dict[str, object]] = [dict(segments[0])]
    for segment in segments[1:]:
        prev = merged[-1]
        prev_start, prev_end = _segment_bounds(prev)
        cur_start, cur_end = _segment_bounds(segment)
        if prev_end == cur_start and _segment_signature(prev) == _segment_signature(segment):
            prev["genesis_end_exclusive"] = _hex6(cur_end)
            prev["size_bytes"] = cur_end - prev_start
            if str(prev["kind"]) == "arcade_copy":
                identity_offset = int(prev["identity_offset"])
                prev["arcade_end_exclusive"] = _hex6(cur_end - identity_offset)
            continue
        merged.append(dict(segment))
    return merged


def _overlay_segment(intervals: list[dict[str, object]], overlay: dict[str, object]) -> list[dict[str, object]]:
    ov_start, ov_end = _segment_bounds(overlay)
    if ov_end <= ov_start:
        raise RuntimeError("Overlay segment has non-positive size.")

    result: list[dict[str, object]] = []
    inserted = False

    for segment in intervals:
        seg_start, seg_end = _segment_bounds(segment)

        if seg_end <= ov_start:
            result.append(segment)
            continue
        if seg_start >= ov_end:
            if not inserted:
                result.append(dict(overlay))
                inserted = True
            result.append(segment)
            continue

        # overlap
        if seg_start < ov_start:
            result.append(_slice_segment(segment, seg_start, ov_start))

        if not inserted:
            result.append(dict(overlay))
            inserted = True

        if seg_end > ov_end:
            right_piece = _slice_segment(segment, ov_end, seg_end)
            if (
                str(segment["kind"]) == "arcade_copy"
                and str(overlay["kind"]) == "patched_site"
                and str(overlay["origin"]) == "shift_replacement"
                and int(overlay["shift_delta"]) != 0
            ):
                right_arc_start = parse_hexish(overlay["arcade_end_exclusive"])
                right_piece["arcade_start"] = _hex6(right_arc_start)
                right_piece["arcade_end_exclusive"] = _hex6(right_arc_start + (seg_end - ov_end))
                right_piece["identity_offset"] = ov_end - right_arc_start
            result.append(right_piece)

    if not inserted:
        result.append(dict(overlay))

    result.sort(key=lambda s: parse_hexish(s["genesis_start"]))
    return result


def _strip_internal_keys(segment: dict[str, object]) -> dict[str, object]:
    out = {k: v for k, v in segment.items() if not k.startswith("_")}
    return out


def _validate_segment_keys(segment: dict[str, object]) -> None:
    common = {"genesis_start", "genesis_end_exclusive", "size_bytes", "kind"}
    kind = str(segment["kind"])
    if kind == "arcade_copy":
        allowed = common | {"arcade_start", "arcade_end_exclusive", "source", "identity_offset"}
    elif kind == "patched_site":
        allowed = common | {
            "arcade_start",
            "arcade_end_exclusive",
            "origin",
            "original_bytes",
            "replacement_bytes",
            "note",
            "shift_delta",
        }
    elif kind == "preserved_vectors":
        allowed = common | {"tag"}
    elif kind == "genesis_only":
        allowed = common | {"tag"}
    else:
        raise RuntimeError(f"Unknown segment kind: {kind}")

    extras = set(segment.keys()) - allowed
    missing = allowed - set(segment.keys())
    if extras:
        raise RuntimeError(f"Segment has unexpected keys for kind={kind}: {sorted(extras)}")
    if missing:
        raise RuntimeError(f"Segment missing required keys for kind={kind}: {sorted(missing)}")


def _finalize_address_map_segments(
    raw_segments: list[dict[str, object]],
    rom_size: int,
    wrapper_start: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if rom_size <= 0:
        raise RuntimeError("ROM size must be positive for address_map emission.")

    base = [dict(s) for s in raw_segments if str(s.get("kind")) == "arcade_copy"]
    patched = [dict(s) for s in raw_segments if str(s.get("kind")) == "patched_site"]
    preserved = [dict(s) for s in raw_segments if str(s.get("kind")) == "preserved_vectors"]
    genesis_only = [dict(s) for s in raw_segments if str(s.get("kind")) == "genesis_only"]

    intervals = sorted(base, key=lambda s: parse_hexish(s["genesis_start"]))

    for overlay in sorted(patched, key=lambda s: parse_hexish(s["genesis_start"])):
        intervals = _overlay_segment(intervals, overlay)

    wrapper = [s for s in genesis_only if str(s.get("tag")) == "wrapper"]
    non_wrapper_genesis = [s for s in genesis_only if str(s.get("tag")) != "wrapper"]

    for overlay in sorted(wrapper, key=lambda s: parse_hexish(s["genesis_start"])):
        if parse_hexish(overlay["genesis_start"]) != wrapper_start:
            raise RuntimeError(
                f"Wrapper lower bound mismatch: expected 0x{wrapper_start:06X}, "
                f"got {overlay['genesis_start']}"
            )
        intervals = _overlay_segment(intervals, overlay)

    for overlay in sorted(non_wrapper_genesis, key=lambda s: parse_hexish(s["genesis_start"])):
        intervals = _overlay_segment(intervals, overlay)

    for overlay in sorted(preserved, key=lambda s: parse_hexish(s["genesis_start"])):
        intervals = _overlay_segment(intervals, overlay)

    intervals = _merge_adjacent_segments(
        sorted(intervals, key=lambda s: parse_hexish(s["genesis_start"]))
    )

    padded: list[dict[str, object]] = []
    cursor = 0
    raw_gaps: list[dict[str, str]] = []
    overlaps: list[dict[str, str]] = []
    for segment in intervals:
        seg_start, seg_end = _segment_bounds(segment)
        if seg_start < cursor:
            overlaps.append({"at": _hex6(seg_start), "cursor": _hex6(cursor)})
        if seg_start > cursor:
            raw_gaps.append({"start": _hex6(cursor), "end_exclusive": _hex6(seg_start)})
            padded.append(
                {
                    "genesis_start": _hex6(cursor),
                    "genesis_end_exclusive": _hex6(seg_start),
                    "size_bytes": seg_start - cursor,
                    "kind": "genesis_only",
                    "tag": "padding",
                }
            )
        padded.append(segment)
        cursor = max(cursor, seg_end)
    if cursor < rom_size:
        raw_gaps.append({"start": _hex6(cursor), "end_exclusive": _hex6(rom_size)})
        padded.append(
            {
                "genesis_start": _hex6(cursor),
                "genesis_end_exclusive": _hex6(rom_size),
                "size_bytes": rom_size - cursor,
                "kind": "genesis_only",
                "tag": "padding",
            }
        )

    final_segments = _merge_adjacent_segments(
        sorted((_strip_internal_keys(s) for s in padded), key=lambda s: parse_hexish(s["genesis_start"]))
    )

    if not final_segments:
        raise RuntimeError("Final address map has no segments.")
    if parse_hexish(final_segments[0]["genesis_start"]) != 0:
        raise RuntimeError("First segment does not start at genesis offset 0x000000.")
    if parse_hexish(final_segments[-1]["genesis_end_exclusive"]) != rom_size:
        raise RuntimeError("Last segment does not end at ROM size.")

    gaps_after: list[dict[str, str]] = []
    overlaps_after: list[dict[str, str]] = []
    covered = 0
    for idx, segment in enumerate(final_segments):
        _validate_segment_keys(segment)
        seg_start, seg_end = _segment_bounds(segment)
        if segment["size_bytes"] != (seg_end - seg_start):
            raise RuntimeError("Segment size_bytes does not match start/end bounds.")
        covered += segment["size_bytes"]

        if idx + 1 < len(final_segments):
            next_start, _ = _segment_bounds(final_segments[idx + 1])
            if seg_end < next_start:
                gaps_after.append({"start": _hex6(seg_end), "end_exclusive": _hex6(next_start)})
            elif seg_end > next_start:
                overlaps_after.append({"at": _hex6(next_start), "prev_end": _hex6(seg_end)})

        if str(segment["kind"]) == "arcade_copy":
            arc_start = parse_hexish(segment["arcade_start"])
            arc_end = parse_hexish(segment["arcade_end_exclusive"])
            if (arc_end - arc_start) != (seg_end - seg_start):
                raise RuntimeError("arcade_copy segment has mismatched arcade/genesis lengths.")
            if (seg_start - arc_start) != int(segment["identity_offset"]):
                raise RuntimeError("arcade_copy segment identity_offset mismatch.")
        if str(segment["kind"]) == "patched_site":
            arc_start = parse_hexish(segment["arcade_start"])
            arc_end = parse_hexish(segment["arcade_end_exclusive"])
            if (len(str(segment["original_bytes"])) // 2) != (arc_end - arc_start):
                raise RuntimeError("patched_site original_bytes length mismatch.")
            if (len(str(segment["replacement_bytes"])) // 2) != (seg_end - seg_start):
                raise RuntimeError("patched_site replacement_bytes length mismatch.")

    if covered != rom_size:
        raise RuntimeError(
            f"Segment coverage mismatch: covered=0x{covered:X} expected=0x{rom_size:X}"
        )
    if gaps_after or overlaps_after:
        raise RuntimeError(
            f"Address map segment continuity failure: gaps={gaps_after}, overlaps={overlaps_after}"
        )

    coverage = {
        "total_genesis_bytes_covered": covered,
        "gaps": [],
        "overlaps": [],
    }
    return final_segments, coverage


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
    _reject_legacy_bookmark_cycle(spec)
    bookmarks_v2 = _bookmarks_v2(spec)
    is_diagnostic_mode = len(bookmarks_v2) > 0
    policy = spec.get("policy", {})
    patcher_profile = str(policy.get("patcher_profile", "startup_title_remap"))
    is_rastan_direct_profile = patcher_profile == "rastan_direct"
    range_lookup = build_range_lookup(spec)
    range_kind_lookup = build_range_kind_lookup(spec)
    required_symbols = tuple(spec.get("required_symbols", []))
    if is_rastan_direct_profile:
        # main_68k/arcade_tick_logic were removed in the runtime decomposition;
        # this symbol is a stale validation requirement for that deleted path.
        required_symbols = tuple(
            name for name in required_symbols if name != "rastan_direct_arcade_tick_entry"
        )
    source_windows = parse_windows(spec.get("declared_arcade_windows", []))
    target_windows = parse_windows(spec.get("declared_rewrite_target_windows", []))
    validate_spec_addresses(spec, range_lookup, target_windows, source_windows)
    wrapper_start = 0x00070000

    whole_copy_cfg = spec.get("whole_maincpu_copy", {})
    whole_copy_mode = spec.get("policy", {}).get("current_copy_mode")
    execute_from_relocated_base = bool(spec.get("policy", {}).get("execute_from_relocated_base", False))
    keep_identity_overlays = bool(spec.get("policy", {}).get("keep_identity_overlays_for_bringup", True))
    whole_copy_enabled = bool(whole_copy_cfg.get("enabled", False))
    planned_relocation_delta = 0
    if whole_copy_enabled and whole_copy_mode == "whole_maincpu_relocated":
        planned_relocation_delta = (
            parse_hexish(whole_copy_cfg["dest_start"])
            - parse_hexish(whole_copy_cfg["source_start"])
        )

    all_symbol_addresses = parse_symbol_table(symbols_path, required_names=None)
    symbol_addresses = all_symbol_addresses

    if (not is_rastan_direct_profile) and ("genesistan_run_original_startup_common" not in symbol_addresses):
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

    required_symbol_addresses = parse_symbol_table(symbols_path, required_symbols)
    diagnostic_symbol_addresses: dict[str, int] = {}
    for name in DIAGNOSTIC_SYMBOLS:
        if name in all_symbol_addresses:
            diagnostic_symbol_addresses[name] = all_symbol_addresses[name]
            continue
        alt_name = f"_{name}"
        if alt_name in all_symbol_addresses:
            diagnostic_symbol_addresses[name] = all_symbol_addresses[alt_name]
    symbol_addresses = {**required_symbol_addresses, **diagnostic_symbol_addresses}
    rom_bytes = bytearray(rom_path.read_bytes())
    preserve_low_rom_end = 0x000400
    if is_rastan_direct_profile:
        crash_handler_end = all_symbol_addresses.get("genesistan_crash_handler_end")
        if crash_handler_end is None:
            crash_handler_end = all_symbol_addresses.get("_genesistan_crash_handler_end")
        if crash_handler_end is not None:
            preserve_low_rom_end = max(preserve_low_rom_end, int(crash_handler_end))
    if preserve_low_rom_end > len(rom_bytes):
        raise RuntimeError(
            f"preserve_low_rom_end 0x{preserve_low_rom_end:06X} exceeds ROM size 0x{len(rom_bytes):06X}"
        )
    preserved_genesis_vectors = bytes(rom_bytes[0x000000:preserve_low_rom_end])
    maincpu_bytes = maincpu_path.read_bytes()
    segments: list[dict[str, object]] = []
    segment_sequence = [0]

    # Apply variable-length opcode replacements before any other patching.
    # Pass A behavior for entries with relocate_after_shift=true:
    # write replacement_template + zero operand placeholder, then defer operand
    # materialization to Pass B after the final shift table is known.
    shift_deltas: list[tuple[int, int]] = []
    deferred_operand_entries: list[dict[str, object]] = []
    if spec.get("shift_replacements"):
        from shift_table_patcher import apply_shift_table as _apply_shift_table
        _whole = spec.get("whole_maincpu_copy", {})
        _src_start = parse_hexish(_whole.get("source_start", "0x000000"))
        _src_end = parse_hexish(_whole.get("source_end_exclusive", "0x060000"))
        _disasm = str(Path(__file__).resolve().parents[2] / "build" / "maincpu.disasm.txt")
        resolved_shift_replacements: list[dict[str, object]] = []
        for _rep in spec["shift_replacements"]:
            _resolved_rep = dict(_rep)
            _pc = parse_hexish(_rep["arcade_pc"])
            _orig = bytes.fromhex(_rep["original_bytes"].replace(" ", ""))
            _is_deferred = bool(_rep.get("relocate_after_shift", False))
            if _is_deferred:
                _template_hex = resolve_replacement_hex(
                    str(_rep["replacement_template"]),
                    symbol_addresses,
                )
                _operand_kind = str(_rep.get("operand_kind", ""))
                _operand_width = int(_rep.get("operand_width", 0))
                _operand_arcade_target = parse_hexish(_rep["operand_arcade_target"])
                if _operand_kind != "abs_l_32bit":
                    raise RuntimeError(
                        f"shift_replacement at 0x{_pc:06X}: "
                        f"unsupported deferred operand_kind={_operand_kind!r}"
                    )
                if _operand_width != 4:
                    raise RuntimeError(
                        f"shift_replacement at 0x{_pc:06X}: "
                        f"unsupported deferred operand_width={_operand_width}"
                    )
                _resolved_rep["replacement_bytes"] = _template_hex + ("00" * _operand_width)
                deferred_operand_entries.append(
                    {
                        "arcade_pc": _pc,
                        "operand_arcade_target": _operand_arcade_target,
                        "operand_width": _operand_width,
                        "operand_kind": _operand_kind,
                        "replacement_template": _template_hex,
                        "opcode_size": len(bytes.fromhex(_template_hex)),
                    }
                )
            else:
                _resolved_rep["replacement_bytes"] = resolve_replacement_hex(
                    str(_rep["replacement_bytes"]),
                    symbol_addresses,
                )
            resolved_shift_replacements.append(_resolved_rep)
            _repl = bytes.fromhex(str(_resolved_rep["replacement_bytes"]))
            shift_deltas.append((_pc, len(_repl) - len(_orig)))
        shift_deltas.sort(key=lambda x: x[0])
        maincpu_bytes = bytes(
            _apply_shift_table(
                maincpu_bytes,
                resolved_shift_replacements,
                _disasm,
                _src_start,
                _src_end,
                spec.get("jump_table_word_displacements", []),
                [],
            )
        )
        for _resolved_rep in resolved_shift_replacements:
            _pc = parse_hexish(_resolved_rep["arcade_pc"])
            _orig = bytes.fromhex(str(_resolved_rep["original_bytes"]).replace(" ", ""))
            _repl = bytes.fromhex(str(_resolved_rep["replacement_bytes"]).replace(" ", ""))
            _rom_pc = _pc + planned_relocation_delta + accumulated_shift_before(_pc, shift_deltas)
            _append_segment(
                segments,
                segment_sequence,
                {
                    "genesis_start": _hex6(_rom_pc),
                    "genesis_end_exclusive": _hex6(_rom_pc + len(_repl)),
                    "size_bytes": len(_repl),
                    "kind": "patched_site",
                    "arcade_start": _hex6(_pc),
                    "arcade_end_exclusive": _hex6(_pc + len(_orig)),
                    "origin": "shift_replacement",
                    "original_bytes": _orig.hex(),
                    "replacement_bytes": _repl.hex(),
                    "note": str(_resolved_rep.get("note", "")),
                    "shift_delta": len(_repl) - len(_orig),
                },
            )

    ensure_rom_size(rom_bytes)
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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(dest_start),
                "genesis_end_exclusive": _hex6(dest_start + source_size),
                "size_bytes": source_size,
                "kind": "arcade_copy",
                "arcade_start": _hex6(source_start),
                "arcade_end_exclusive": _hex6(source_end),
                "source": "whole_maincpu_copy",
                "identity_offset": dest_start - source_start,
            },
        )
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
    #
    # For rastan_direct, apply the preserved block *after* rewrite passes so scan/rewrite
    # logic cannot mutate boot code bytes in the final executable ROM artifact.
    if not is_rastan_direct_profile:
        rom_bytes[0x000000:preserve_low_rom_end] = preserved_genesis_vectors
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": "0x000000",
                "genesis_end_exclusive": _hex6(preserve_low_rom_end),
                "size_bytes": preserve_low_rom_end,
                "kind": "preserved_vectors",
                "tag": "genesis_vectors_header",
            },
        )

    copied_ranges: list[dict[str, object]] = []
    copied_range_entries = spec["copied_ranges"]
    rom_call_reloc_log: list[dict[str, object]] = []
    for entry in spec["copied_ranges"]:
        start = parse_hexish(entry["start"])
        end = parse_hexish(entry["end_exclusive"])
        name = entry["name"]
        if keep_identity_overlays:
            copy_range(rom_bytes, maincpu_bytes, start, end)
            _append_segment(
                segments,
                segment_sequence,
                {
                    "genesis_start": _hex6(start),
                    "genesis_end_exclusive": _hex6(end),
                    "size_bytes": end - start,
                    "kind": "arcade_copy",
                    "arcade_start": _hex6(start),
                    "arcade_end_exclusive": _hex6(end),
                    "source": f"copied_range:{name}",
                    "identity_offset": 0,
                },
            )
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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(start),
                "genesis_end_exclusive": _hex6(end),
                "size_bytes": end - start,
                "kind": "genesis_only",
                "tag": "shim_jump",
            },
        )

    for table in spec.get("absolute_long_pointer_tables", []):
        table_addr = parse_hexish(table["table_address"])
        entry_count = int(table["entry_count"])
        entry_size = int(table.get("entry_size_bytes", 4))
        if entry_size != 4:
            raise RuntimeError(
                f"absolute_long_pointer_table at 0x{table_addr:06X}: "
                f"unsupported entry_size_bytes={entry_size}"
            )

        rom_table_addr = table_addr + relocation_delta + accumulated_shift_before(table_addr, shift_deltas)
        fixes = 0
        target_relocation = relocation_delta if execute_from_relocated_base else 0
        for i in range(entry_count):
            entry_addr = rom_table_addr + (i * 4)
            old_target = int.from_bytes(rom_bytes[entry_addr:entry_addr + 4], "big")
            if not (source_start <= old_target < source_end):
                continue
            new_target = (
                old_target
                + target_relocation
                + accumulated_shift_before(old_target, shift_deltas)
            )
            if new_target == old_target:
                continue
            rom_bytes[entry_addr:entry_addr + 4] = new_target.to_bytes(4, "big")
            fixes += 1

        rewrite_log.append(
            {
                "kind": "absolute_long_pointer_table",
                "table_address": f"0x{table_addr:06X}",
                "rom_table_address": f"0x{rom_table_addr:06X}",
                "entry_count": entry_count,
                "fixes": fixes,
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
            resolve_replacement_hex(
                str(replacement["replacement_bytes"]),
                symbol_addresses,
            )
        )
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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(rom_pc),
                "genesis_end_exclusive": _hex6(rom_pc + len(new_bytes)),
                "size_bytes": len(new_bytes),
                "kind": "patched_site",
                "arcade_start": _hex6(arcade_pc),
                "arcade_end_exclusive": _hex6(arcade_pc + len(expected)),
                "origin": "opcode_replace",
                "original_bytes": expected.hex(),
                "replacement_bytes": new_bytes.hex(),
                "note": str(replacement.get("note", "")),
                "shift_delta": len(new_bytes) - len(expected),
            },
        )

    # Direct ROM-site opcode replacement (for fixed Genesis ROM addresses that are
    # outside source-space arcade_pc + relocation mapping).
    for replacement in spec.get("rom_opcode_replace", []):
        rom_pc = parse_hexish(replacement["rom_pc"])
        expected = bytes.fromhex(replacement["original_bytes"].replace(" ", ""))
        new_bytes = bytes.fromhex(
            resolve_replacement_hex(
                str(replacement["replacement_bytes"]),
                symbol_addresses,
            )
        )
        if len(expected) != len(new_bytes):
            raise RuntimeError(
                f"rom_opcode_replace at 0x{rom_pc:06X}: "
                f"original_bytes and replacement_bytes must be the same length."
            )
        actual = bytes(rom_bytes[rom_pc:rom_pc + len(expected)])
        if actual != expected:
            raise RuntimeError(
                f"rom_opcode_replace at 0x{rom_pc:06X}: "
                f"expected {expected.hex()} but found {actual.hex()}"
            )
        rom_bytes[rom_pc:rom_pc + len(new_bytes)] = new_bytes
        rewrite_log.append(
            {
                "kind": "rom_opcode_replace",
                "rom_pc": f"0x{rom_pc:06X}",
                "original_bytes": expected.hex(),
                "replacement_bytes": new_bytes.hex(),
                "note": replacement.get("note", ""),
            }
        )
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(rom_pc),
                "genesis_end_exclusive": _hex6(rom_pc + len(new_bytes)),
                "size_bytes": len(new_bytes),
                "kind": "genesis_only",
                "tag": "rom_patch",
            },
        )

    # Pass B: resolve deferred abs.l operands after Pass A finalizes layout.
    operand_relocation_log: list[dict[str, object]] = []
    for deferred in deferred_operand_entries:
        arcade_pc = int(deferred["arcade_pc"])
        operand_arcade_target = int(deferred["operand_arcade_target"])
        operand_width = int(deferred["operand_width"])
        opcode_size = int(deferred["opcode_size"])
        replacement_template = bytes.fromhex(str(deferred["replacement_template"]))
        shift_before_target = accumulated_shift_before(operand_arcade_target, shift_deltas)
        final_operand = operand_arcade_target + relocation_delta + shift_before_target
        genesis_callsite = arcade_pc + relocation_delta + accumulated_shift_before(arcade_pc, shift_deltas)

        template_actual = bytes(rom_bytes[genesis_callsite:genesis_callsite + opcode_size])
        if template_actual != replacement_template:
            raise RuntimeError(
                f"relocate_after_shift at 0x{arcade_pc:06X}: "
                f"template mismatch at ROM 0x{genesis_callsite:06X}; "
                f"expected {replacement_template.hex()} got {template_actual.hex()}"
            )

        max_operand = (1 << (operand_width * 8)) - 1
        if final_operand < 0 or final_operand > max_operand:
            raise RuntimeError(
                f"relocate_after_shift at 0x{arcade_pc:06X}: "
                f"final operand 0x{final_operand:X} exceeds width={operand_width}"
            )

        operand_rom_pc = genesis_callsite + opcode_size
        rom_bytes[operand_rom_pc:operand_rom_pc + operand_width] = final_operand.to_bytes(operand_width, "big")
        rom_bytes_written = bytes(
            rom_bytes[genesis_callsite:genesis_callsite + opcode_size + operand_width]
        ).hex().upper()
        entry_log = {
            "kind": "relocate_after_shift_operand",
            "arcade_pc": f"0x{arcade_pc:06X}",
            "arcade_target": f"0x{operand_arcade_target:06X}",
            "shift_before_target": shift_before_target,
            "final_operand": f"0x{final_operand:06X}",
            "genesis_callsite": f"0x{genesis_callsite:06X}",
            "rom_bytes_written": rom_bytes_written,
        }
        operand_relocation_log.append(entry_log)
        rewrite_log.append(entry_log)

    # Required report for relocate_after_shift processing.
    operand_report_path = Path(__file__).resolve().parents[2] / "dist" / "operand_relocation_report.txt"
    operand_report_path.parent.mkdir(parents=True, exist_ok=True)
    report_lines: list[str] = []
    for item in operand_relocation_log:
        report_lines.extend(
            [
                f"arcade_pc: {item['arcade_pc']}",
                f"arcade_target: {item['arcade_target']}",
                f"shift_before_target: {item['shift_before_target']}",
                f"final_operand: {item['final_operand']}",
                f"genesis_callsite: {item['genesis_callsite']}",
                f"rom_bytes_written: {item['rom_bytes_written']}",
                "",
            ]
        )
    if not report_lines:
        report_lines.append("no relocate_after_shift entries processed")
    operand_report_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    # Apply runtime-PC bookmarks after opcode_replace (and deferred operand fixes)
    # so activator bytes target the final post-relocation instruction stream.
    bookmarks_v2_applied = _apply_bookmarks_v2(rom_bytes, bookmarks_v2, symbol_addresses)

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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(_table_off),
                "genesis_end_exclusive": _hex6(_table_off + len(_palette_data)),
                "size_bytes": len(_palette_data),
                "kind": "genesis_only",
                "tag": "palette_table",
            },
        )

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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(workram_anchor_offset),
                "genesis_end_exclusive": _hex6(workram_anchor_offset + 4),
                "size_bytes": 4,
                "kind": "genesis_only",
                "tag": "workram_anchor",
            },
        )

    expectations = spec.get("expectations", {})
    expected_opcode_replace_count = expectations.get("opcode_replace_count")
    if expected_opcode_replace_count is not None:
        expected_count = int(expected_opcode_replace_count)
        applied_count = sum(
            1 for item in rewrite_log
            if str(item.get("kind", "")) in ("opcode_replace", "rom_opcode_replace")
        )
        if applied_count != expected_count:
            raise RuntimeError(
                f"Expected {expected_count} opcode replacements but applied {applied_count}."
            )

    test_jump_patch_address: int | None = None
    normal_stub_start: int | None = None
    normal_stub_end: int | None = None
    test_stub_address: int | None = None
    test_stub_end: int | None = None
    test_result_value: int | None = None

    if not is_rastan_direct_profile:
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
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(normal_stub_start),
                "genesis_end_exclusive": _hex6(normal_stub_end),
                "size_bytes": normal_stub_end - normal_stub_start,
                "kind": "genesis_only",
                "tag": "generated_stub",
            },
        )
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(test_stub_address),
                "genesis_end_exclusive": _hex6(test_stub_end),
                "size_bytes": test_stub_end - test_stub_address,
                "kind": "genesis_only",
                "tag": "generated_stub",
            },
        )

        patch_startup_vectors(rom_bytes, symbol_addresses["_reset_entry"])

    direct_cfg = spec.get("direct_execution", {})
    direct_entry_symbol = str(direct_cfg.get("entry_symbol", "")) if is_rastan_direct_profile else ""
    direct_entry_symbol_addr = None
    if is_rastan_direct_profile and direct_entry_symbol:
        direct_entry_symbol_addr = resolve_symbol_address(all_symbol_addresses, direct_entry_symbol)

    if is_rastan_direct_profile:
        rom_bytes[0x000000:preserve_low_rom_end] = preserved_genesis_vectors
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": "0x000000",
                "genesis_end_exclusive": _hex6(preserve_low_rom_end),
                "size_bytes": preserve_low_rom_end,
                "kind": "preserved_vectors",
                "tag": "genesis_vectors_header",
            },
        )

    checksum = update_genesis_checksum(rom_bytes)
    rom_path.write_bytes(rom_bytes)

    expected_opcode_replace_sites_for_context: int | None = None
    expected_total_coverage_for_context: int | None = None
    build_context_label = "diagnostic" if is_diagnostic_mode else "canonical"
    address_map_path = manifest_path.with_name("address_map.json")
    if is_rastan_direct_profile:
        _append_segment(
            segments,
            segment_sequence,
            {
                "genesis_start": _hex6(wrapper_start),
                "genesis_end_exclusive": _hex6(len(rom_bytes)),
                "size_bytes": len(rom_bytes) - wrapper_start,
                "kind": "genesis_only",
                "tag": "wrapper",
            },
        )
        finalized_segments, segment_coverage = _finalize_address_map_segments(
            segments,
            len(rom_bytes),
            wrapper_start,
        )
        opcode_replace_logs = [
            item for item in rewrite_log
            if str(item.get("kind", "")) == "opcode_replace"
        ]
        opcode_replace_sites = [
            seg for seg in finalized_segments
            if str(seg.get("kind", "")) == "patched_site"
            and str(seg.get("origin", "")) == "opcode_replace"
        ]
        if len(opcode_replace_logs) != len(opcode_replace_sites):
            raise RuntimeError(
                "Address-map invariant failure: opcode_replace rewrite_log count "
                "does not match patched_site opcode_replace segment count."
            )
        # Opcode-replace invariants are strict canonical values in all build
        # contexts. bookmarks_v2 writes are a separate post-relocation stage.
        expected_count = CANONICAL_OPCODE_REPLACE_COUNT
        expected_coverage = CANONICAL_TOTAL_GENESIS_BYTES_COVERED

        observed_coverage = int(segment_coverage["total_genesis_bytes_covered"])
        observed_count = len(opcode_replace_sites)
        expected_opcode_replace_sites_for_context = expected_count
        expected_total_coverage_for_context = expected_coverage
        if observed_coverage != expected_coverage or observed_count != expected_count:
            raise RuntimeError(
                "Build 0029 invariant failure: expected "
                f"total_genesis_bytes_covered=0x{expected_coverage:X} and "
                f"opcode_replace patched_site count={expected_count}; got "
                f"total_genesis_bytes_covered=0x{observed_coverage:X} "
                f"opcode_replace patched_site count={observed_count}. "
                f"build_context={build_context_label}."
            )
        _site_keys = {
            (
                str(seg["arcade_start"]),
                str(seg["genesis_start"]),
                str(seg["original_bytes"]),
                str(seg["replacement_bytes"]),
                str(seg["note"]),
            )
            for seg in opcode_replace_sites
        }
        _log_keys = {
            (
                str(item["arcade_pc"]),
                str(item["rom_pc"]),
                str(item["original_bytes"]),
                str(item["replacement_bytes"]),
                str(item.get("note", "")),
            )
            for item in opcode_replace_logs
        }
        if _site_keys != _log_keys:
            raise RuntimeError(
                "Build 0029 invariant failure: opcode_replace patched_site segments "
                "do not correspond 1:1 with rewrite_log opcode_replace entries."
            )

        arcade_source_start = parse_hexish(whole_copy_cfg.get("source_start", "0x000000"))
        arcade_source_end = parse_hexish(
            whole_copy_cfg.get(
                "source_end_exclusive",
                f"0x{len(maincpu_bytes):06X}",
            )
        )
        address_map = {
            "schema_version": 1,
            "build_inputs": {
                "variant": args.variant,
                "patcher_profile": patcher_profile,
                "spec_path": str(spec_path.resolve()),
                "manifest_path": str(manifest_path.resolve()),
                "rom_path": str(rom_path.resolve()),
                "symbols_path": str(symbols_path.resolve()),
                "maincpu_path": str(maincpu_path.resolve()),
            },
            "genesis_rom_size_bytes": len(rom_bytes),
            "relocation_delta": _hex6(relocation_delta),
            "arcade_source_start": _hex6(arcade_source_start),
            "arcade_source_end_exclusive": _hex6(arcade_source_end),
            "wrapper_region": {
                "genesis_start": _hex6(wrapper_start),
                "genesis_end_exclusive": _hex6(len(rom_bytes)),
            },
            "segments": finalized_segments,
            "segment_coverage": segment_coverage,
            "shift_deltas": [[_hex6(addr), delta] for addr, delta in shift_deltas],
        }
        address_map_path.parent.mkdir(parents=True, exist_ok=True)
        address_map_path.write_text(json.dumps(address_map, indent=2) + "\n", encoding="utf-8")

    manifest: dict[str, object] = {
        "variant": args.variant,
        "patcher_profile": patcher_profile,
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
        "preserved_low_rom_bootstrap": {
            "start": "0x000000",
            "end_exclusive": _hex6(preserve_low_rom_end),
            "why": (
                "Preserve reset/vectors/header/bootstrap in low ROM while relocated arcade ROM "
                "occupies 0x000200.."
                if is_rastan_direct_profile
                else "Preserve SGDK/launcher exception vectors during offset-carry maincpu copy."
            ),
        },
        "preserved_genesis_vector_table": {
            "start": "0x000000",
            "end_exclusive": _hex6(preserve_low_rom_end),
            "why": (
                "Preserve reset/vectors/header/bootstrap in low ROM while relocated arcade ROM "
                "occupies 0x000200.."
                if is_rastan_direct_profile
                else "Preserve SGDK/launcher exception vectors during offset-carry maincpu copy."
            ),
        },
        "address_rewrites": rewrite_log,
        "checksum": f"0x{checksum:04X}",
        "relocation_map": str(relocation_path.resolve()),
        "goal": (
            "Execute the original startup/title/front-end remap from original ROM bytes using a spec-driven translation pass."
            if not is_rastan_direct_profile
            else "Apply rastan-direct spec-driven ROM relocation and opcode patching using the existing postpatch pipeline."
        ),
        "expectations": {
            "opcode_replace_count": expected_opcode_replace_count,
        },
        "patch_counts": {
            "opcode_replace_and_rom_opcode_replace": sum(
                1 for item in rewrite_log
                if str(item.get("kind", "")) in ("opcode_replace", "rom_opcode_replace")
            ),
        },
        "build_context": build_context_label,
    }
    if expected_opcode_replace_sites_for_context is not None:
        manifest["postpatch_expected_opcode_replace_sites"] = expected_opcode_replace_sites_for_context
    if expected_total_coverage_for_context is not None:
        manifest["postpatch_expected_total_genesis_bytes_covered"] = f"0x{expected_total_coverage_for_context:X}"
    manifest["bookmarks_v2_count"] = len(bookmarks_v2)
    manifest["bookmarks_v2_applied"] = bookmarks_v2_applied

    if not is_rastan_direct_profile:
        manifest["normal_result_stub"] = {
            "address": f"0x{normal_stub_start:06X}",
            "jumps_to": f"0x{symbol_addresses['genesistan_startup_common_continue_normal']:08X}",
            "end_exclusive": f"0x{normal_stub_end:06X}",
        }
        manifest["test_result_stub"] = {
            "address": f"0x{test_stub_address:06X}",
            "writes_status_to": f"0x{symbol_addresses['genesistan_startup_result_code']:08X}",
            "value": test_result_value,
            "jumps_exit_to": f"0x{symbol_addresses['genesistan_startup_common_exit_test']:08X}",
            "end_exclusive": f"0x{test_stub_end:06X}",
        }
        manifest["test_jump_patch"] = {
            "patched_at": f"0x{test_jump_patch_address:06X}",
            "new_target": f"0x{test_stub_address:06X}",
        }
        manifest["startup_vectors"] = {
            "initial_sp": f"0x{int.from_bytes(rom_bytes[0x000000:0x000004], 'big'):08X}",
            "reset_pc": f"0x{int.from_bytes(rom_bytes[0x000004:0x000008], 'big'):08X}",
            "forced_reset_pc_symbol": "_reset_entry",
        }
    else:
        manifest["direct_execution"] = {
            "entry_arcade_pc": direct_cfg.get("entry_arcade_pc"),
            "entry_symbol": direct_entry_symbol,
            "entry_symbol_address": (
                f"0x{direct_entry_symbol_addr:08X}"
                if direct_entry_symbol_addr is not None
                else None
            ),
        }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    relocation_path.parent.mkdir(parents=True, exist_ok=True)
    if is_rastan_direct_profile:
        relocation_map = {
            "variant": args.variant,
            "mode": "rastan_direct",
            "rom": str(rom_path.resolve()),
            "source_maincpu": str(maincpu_path.resolve()),
            "policy": "Build from original ROM bytes every time; never patch forward from derived binaries.",
            "objects": [
                {
                    "id": "maincpu:whole_relocated",
                    "name": "whole_maincpu_relocated",
                    "kind": "original_code_or_data",
                    "source_rom": str(maincpu_path.resolve()),
                    "original_start": str(whole_copy_summary["source_start"]) if whole_copy_summary else None,
                    "original_end_exclusive": str(whole_copy_summary["source_end_exclusive"]) if whole_copy_summary else None,
                    "genesis_rom_start": str(whole_copy_summary["dest_start"]) if whole_copy_summary else None,
                    "genesis_rom_end_exclusive": str(whole_copy_summary["dest_end_exclusive"]) if whole_copy_summary else None,
                    "placement": "relocated_whole_copy",
                }
            ],
            "generated_blocks": [],
        }
    else:
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
