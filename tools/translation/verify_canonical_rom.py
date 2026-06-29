#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

FAIL_2_1 = "GATE_FAIL_2_1_INCBIN_SHA_MISMATCH"
FAIL_2_2 = "GATE_FAIL_2_2_HELPER_SHA_MISMATCH"
FAIL_2_3 = "GATE_FAIL_2_3_POSTPATCHER_INVARIANT"
FAIL_2_4 = "GATE_FAIL_2_4_ROM_NAMING"
FAIL_2_5 = "GATE_FAIL_2_5_SYMBOL_RESOLUTION"
FAIL_LEGACY_BOOKMARK_SCHEMA = "GATE_FAIL_LEGACY_BOOKMARK_SCHEMA"
FAIL_2_5_BOOKMARK_SCHEMA = "GATE_FAIL_2_5_BOOKMARK_SCHEMA_VALIDATION"
FAIL_2_6 = "GATE_FAIL_2_6_DEPENDENCY_AUDIT"
FAIL_2_7 = "GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES"
FAIL_2_8 = "GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL"

FAIL_STATE_ORPHANED_SPEC = "GATE_FAIL_STATE_ORPHANED_SPEC"
FAIL_STATE_ORPHANED_FILE = "GATE_FAIL_STATE_ORPHANED_FILE"
FAIL_STATE_MISMATCH = "GATE_FAIL_STATE_MISMATCH"
FAIL_STATE_REVERT_CONTEXT_MISMATCH = "GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH"
FAIL_STATE_REVERT_DURING_ACTIVE = "GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE"
FAIL_STATE_REVERT_NO_CYCLE = "GATE_FAIL_STATE_REVERT_NO_CYCLE"
FAIL_STATE_CORRUPTED = "GATE_FAIL_STATE_CORRUPTED"

CANONICAL_OPCODE_REPLACE_COUNT = 129
# KF-028 fix (2026-06-17): +4 bytes from bsr rastan_direct_update_inputs.
# OPEN-016 Part 2 (2026-06-19): +0x54 bytes from glyph hook,
# plus +0x14 bytes for the Build 0091 helper-crash register setup.
# Build 0096 title BG block-copy staging helper: +0xD4 bytes.
# Build 0097 display-origin scroll bias in vdp_commit_scroll: +0x14 bytes.
# Build 0106 PC080SN scroll-RAM C-lite dispatch/stubs: +0x40 bytes.
# Build 0110 high-score FG producer staging route hook: +0x68 bytes.
# Build 0113 shared PC080SN text-writer dispatcher: +0xBC bytes.
CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CF68

SYMBOL_LINE_RE = re.compile(r"^([0-9A-Fa-f]+)\s+\S+\s+(\S+)$")
LABEL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?:;.*)?$")
INCBIN_RE = re.compile(r"\.incbin\s+\"([^\"]+)\"")
SPEC_SYMBOL_RE = re.compile(r"\{symbol:([A-Za-z_][A-Za-z0-9_]*)(?:[+-](?:0x[0-9A-Fa-f]+|\d+))?\}")
EXPECTED_ROM_RE = re.compile(r"^rastan_direct_video_test_build_(\d{4})\.bin$")
ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|\?=|=)\s*(.*)$")
SYMBOL_TOKEN_PATTERN = re.compile(r"\{symbol:([A-Za-z_][A-Za-z0-9_]*)([+-](?:0x[0-9A-Fa-f]+|\d+))?\}")


@dataclass(frozen=True)
class IncbinEntry:
    asm_path: Path
    symbol: str
    bin_path: Path
    line_no: int


@dataclass(frozen=True)
class BookmarkV2Entry:
    cycle_id: str
    runtime_genesis_pc: int
    span_length: int
    helper_symbol: str
    activator_pattern: str
    nop_padding_word: int
    pre_insert_canonical_bytes: str
    pre_insert_canonical_rom_sha256: str


@dataclass(frozen=True)
class StateFile:
    cycle_id: str
    pre_insert_canonical_rom_sha256: str
    pre_insert_build_counter: int
    timestamp: str


def fail(fid: str, *lines: str) -> None:
    print(fid)
    for line in lines:
        print(line)
    sys.exit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_hexish(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"Unsupported int/hex value: {value!r}")


def compact_hex(value: str) -> str:
    compact = "".join(value.split())
    if len(compact) % 2 != 0 or re.fullmatch(r"[0-9A-Fa-f]*", compact) is None:
        raise ValueError(f"Invalid hex string: {value!r}")
    return compact


def parse_symbol_table(path: Path) -> Dict[str, int]:
    symbols: Dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = SYMBOL_LINE_RE.match(raw.strip())
        if not m:
            continue
        addr_hex, name = m.groups()
        symbols[name] = int(addr_hex, 16)
    return symbols


def resolve_symbol(symbols: Dict[str, int], name: str) -> int | None:
    if name in symbols:
        return symbols[name]
    alt = f"_{name}"
    if alt in symbols:
        return symbols[alt]
    return None


def resolve_replacement_hex(raw_hex: str, symbols: Dict[str, int]) -> str:
    def _replace(match: re.Match[str]) -> str:
        sym = match.group(1)
        off = match.group(2)
        addr = resolve_symbol(symbols, sym)
        if addr is None:
            fail(FAIL_2_5, f"Unresolved symbol in replacement_bytes template: {sym}")
        if off:
            addr += int(off, 0)
        return f"{addr & 0xFFFFFFFF:08X}"

    expanded = SYMBOL_TOKEN_PATTERN.sub(_replace, raw_hex)
    return compact_hex(expanded)


def scan_incbins(src_dir: Path) -> List[IncbinEntry]:
    asm_workdir = src_dir.parent.resolve()
    out: List[IncbinEntry] = []
    for asm in sorted(src_dir.rglob("*.s")):
        last_label: str | None = None
        for line_no, raw in enumerate(asm.read_text(encoding="utf-8").splitlines(), start=1):
            lm = LABEL_RE.match(raw)
            if lm:
                last_label = lm.group(1)
            im = INCBIN_RE.search(raw)
            if im:
                if not last_label:
                    fail(
                        FAIL_2_1,
                        f"No preceding symbol label for .incbin at {asm}:{line_no}",
                        "Expected a symbol anchor immediately before .incbin.",
                    )
                rel = im.group(1)
                bin_path = (asm_workdir / rel).resolve()
                out.append(IncbinEntry(asm.resolve(), last_label, bin_path, line_no))
    return out


def check_incbin_bytes(rom: bytes, symbols: Dict[str, int], entries: List[IncbinEntry]) -> None:
    for entry in entries:
        if not entry.bin_path.exists():
            fail(
                FAIL_2_1,
                f"Missing .incbin source artifact: {entry.bin_path}",
                f"Referenced by {entry.asm_path}:{entry.line_no} ({entry.symbol})",
            )
        addr = resolve_symbol(symbols, entry.symbol)
        if addr is None:
            fail(
                FAIL_2_1,
                f"Missing symbol for .incbin anchor: {entry.symbol}",
                f"Source: {entry.asm_path}:{entry.line_no}",
            )
        disk = entry.bin_path.read_bytes()
        end = addr + len(disk)
        if addr < 0 or end > len(rom):
            fail(
                FAIL_2_1,
                f"ROM bounds error for .incbin symbol {entry.symbol}",
                f"symbol_addr=0x{addr:06X} length={len(disk)} rom_size={len(rom)}",
            )
        embedded = rom[addr:end]
        h_disk = sha256_bytes(disk)
        h_rom = sha256_bytes(embedded)
        if h_disk != h_rom:
            fail(
                FAIL_2_1,
                f"Symbol: {entry.symbol}",
                f"ASM: {entry.asm_path}:{entry.line_no}",
                f"Artifact: {entry.bin_path}",
                f"ROM offset: 0x{addr:06X}",
                f"Expected SHA256: {h_disk}",
                f"Found SHA256:    {h_rom}",
            )


def check_helper(rom: bytes, symbols: Dict[str, int], helper_symbol: str, expected_sha: str) -> None:
    addr = resolve_symbol(symbols, helper_symbol)
    if addr is None:
        fail(FAIL_2_2, f"Missing helper symbol: {helper_symbol}")
    if addr < 0 or addr + 2 > len(rom):
        fail(
            FAIL_2_2,
            f"Helper symbol out of ROM bounds: {helper_symbol} @ 0x{addr:06X}",
            f"ROM size={len(rom)}",
        )
    helper = rom[addr:addr + 2]
    got_hex = helper.hex().upper()
    got_sha = sha256_bytes(helper)
    if helper != bytes([0x60, 0xFE]) or got_sha.lower() != expected_sha.lower():
        fail(
            FAIL_2_2,
            f"Helper symbol: {helper_symbol}",
            f"Address: 0x{addr:06X}",
            f"Observed bytes: {got_hex}",
            f"Observed SHA256: {got_sha}",
            f"Expected bytes: 60FE",
            f"Expected SHA256: {expected_sha}",
        )


def read_json(path: Path, fail_id: str, label: str) -> dict:
    if not path.exists():
        fail(fail_id, f"Missing {label}: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(fail_id, f"Failed to parse {label}: {path}", f"error={exc}")
    if not isinstance(data, dict):
        fail(fail_id, f"{label} must be a JSON object: {path}")
    return data


def parse_bookmarks_v2(spec: dict) -> list[BookmarkV2Entry]:
    if "diagnostic_bookmarks" in spec:
        fail(
            FAIL_LEGACY_BOOKMARK_SCHEMA,
            "Legacy spec field diagnostic_bookmarks is not supported under OPEN-012.",
            "Use top-level bookmarks_v2 entries.",
        )

    for idx, entry in enumerate(spec.get("opcode_replace", [])):
        if not isinstance(entry, dict):
            continue
        legacy_cycle = str(entry.get("bookmark_cycle", "")).strip()
        if legacy_cycle:
            fail(
                FAIL_LEGACY_BOOKMARK_SCHEMA,
                f"Legacy opcode_replace bookmark_cycle found at opcode_replace[{idx}]={legacy_cycle!r}.",
                "Bookmark activators must use bookmarks_v2 only.",
            )

    raw = spec.get("bookmarks_v2", [])
    if raw in (None, {}):
        return []
    if not isinstance(raw, list):
        fail(FAIL_2_5_BOOKMARK_SCHEMA, "bookmarks_v2 must be an array when present.")

    out: list[BookmarkV2Entry] = []
    seen_cycle_ids: set[str] = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"bookmarks_v2[{idx}] must be an object.")
        if "arcade_pc" in item:
            fail(
                FAIL_2_5_BOOKMARK_SCHEMA,
                f"bookmarks_v2[{idx}] must not contain arcade_pc (OPEN-012 runtime coordinate model).",
            )

        cycle_id = str(item.get("cycle_id", "")).strip()
        if not cycle_id:
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"bookmarks_v2[{idx}] missing cycle_id.")
        if cycle_id in seen_cycle_ids:
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"Duplicate bookmarks_v2 cycle_id: {cycle_id}")
        seen_cycle_ids.add(cycle_id)

        pre_insert_bytes = str(item.get("pre_insert_canonical_bytes", "")).strip()
        pre_insert_sha = str(item.get("pre_insert_canonical_rom_sha256", "")).strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", pre_insert_sha):
            fail(
                FAIL_2_5_BOOKMARK_SCHEMA,
                f"bookmarks_v2[{idx}] pre_insert_canonical_rom_sha256 must be 64 hex chars.",
            )

        try:
            runtime_genesis_pc = parse_hexish(item.get("runtime_genesis_pc"))
        except Exception as exc:  # noqa: BLE001
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"bookmarks_v2[{idx}] invalid runtime_genesis_pc: {exc}")
        try:
            span_length = int(item.get("span_length"))
        except Exception as exc:  # noqa: BLE001
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"bookmarks_v2[{idx}] invalid span_length: {exc}")

        helper_symbol = str(item.get("helper_symbol", "")).strip()
        activator_pattern = str(item.get("activator_pattern", "")).strip()
        nop_padding_raw = str(item.get("nop_padding_byte", "")).strip() or "0x4E71"
        try:
            nop_padding_word = int(nop_padding_raw, 0)
        except Exception as exc:  # noqa: BLE001
            fail(FAIL_2_5_BOOKMARK_SCHEMA, f"bookmarks_v2[{idx}] invalid nop_padding_byte: {exc}")

        out.append(
            BookmarkV2Entry(
                cycle_id=cycle_id,
                runtime_genesis_pc=runtime_genesis_pc,
                span_length=span_length,
                helper_symbol=helper_symbol,
                activator_pattern=activator_pattern,
                nop_padding_word=nop_padding_word,
                pre_insert_canonical_bytes=pre_insert_bytes,
                pre_insert_canonical_rom_sha256=pre_insert_sha,
            )
        )

    if len(out) > 1:
        fail(
            FAIL_2_5_BOOKMARK_SCHEMA,
            "bookmarks_v2 has more than one entry.",
            "Rule 10 allows at most one in-flight bookmark cycle.",
        )
    return out


def read_state_file(path: Path) -> StateFile | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(FAIL_STATE_CORRUPTED, f"State file is not valid JSON: {path}", f"error={exc}")

    if not isinstance(payload, dict):
        fail(FAIL_STATE_CORRUPTED, f"State file must be an object: {path}")

    cycle_id = str(payload.get("cycle_id", "")).strip()
    pre_sha = str(payload.get("pre_insert_canonical_rom_sha256", "")).strip().lower()
    build_counter = payload.get("pre_insert_build_counter")
    timestamp = str(payload.get("timestamp", "")).strip()

    if not cycle_id or not re.fullmatch(r"BM-\d{3}", cycle_id):
        fail(FAIL_STATE_CORRUPTED, f"State file cycle_id invalid/missing: {payload.get('cycle_id')!r}")
    if not re.fullmatch(r"[0-9a-f]{64}", pre_sha):
        fail(
            FAIL_STATE_CORRUPTED,
            "State file pre_insert_canonical_rom_sha256 invalid/missing.",
            f"value={payload.get('pre_insert_canonical_rom_sha256')!r}",
        )
    if not isinstance(build_counter, int):
        fail(
            FAIL_STATE_CORRUPTED,
            "State file pre_insert_build_counter invalid/missing.",
            f"value={build_counter!r}",
        )
    if not timestamp:
        fail(FAIL_STATE_CORRUPTED, "State file timestamp missing.")

    return StateFile(
        cycle_id=cycle_id,
        pre_insert_canonical_rom_sha256=pre_sha,
        pre_insert_build_counter=build_counter,
        timestamp=timestamp,
    )


def normalize_revert_context(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def determine_state_context(
    state: StateFile | None,
    bookmarks_v2_entries: list[BookmarkV2Entry],
    revert_cycle: str | None,
) -> str:
    has_state = state is not None
    has_spec = len(bookmarks_v2_entries) > 0
    has_revert = revert_cycle is not None
    spec_cycle = bookmarks_v2_entries[0].cycle_id if has_spec else None

    if not has_state and not has_spec and not has_revert:
        return "canonical"

    if not has_state and has_spec and not has_revert:
        fail(
            FAIL_STATE_ORPHANED_SPEC,
            "bookmarks_v2 is non-empty but active_bookmark_baseline.json is absent.",
            f"spec_cycle_id={spec_cycle}",
        )

    if has_state and has_spec and not has_revert:
        if state.cycle_id != spec_cycle:
            fail(
                FAIL_STATE_MISMATCH,
                "active_bookmark_baseline.json cycle_id does not match spec bookmarks_v2 cycle_id.",
                f"state_cycle_id={state.cycle_id}",
                f"spec_cycle_id={spec_cycle}",
            )
        return "diagnostic"

    if has_state and not has_spec and not has_revert:
        fail(
            FAIL_STATE_ORPHANED_FILE,
            "active_bookmark_baseline.json exists but bookmarks_v2 is empty and no explicit revert context provided.",
            f"state_cycle_id={state.cycle_id}",
        )

    if has_state and not has_spec and has_revert:
        if state.cycle_id != revert_cycle:
            fail(
                FAIL_STATE_REVERT_CONTEXT_MISMATCH,
                "Explicit revert cycle does not match active_bookmark_baseline.json cycle_id.",
                f"state_cycle_id={state.cycle_id}",
                f"revert_cycle_id={revert_cycle}",
            )
        return "authorized_revert"

    if has_state and has_spec and has_revert:
        fail(
            FAIL_STATE_REVERT_DURING_ACTIVE,
            "Explicit revert context provided while bookmarks_v2 is still non-empty (active cycle).",
            f"state_cycle_id={state.cycle_id}",
            f"spec_cycle_id={spec_cycle}",
            f"revert_cycle_id={revert_cycle}",
        )

    if not has_state and has_revert:
        fail(
            FAIL_STATE_REVERT_NO_CYCLE,
            "Explicit revert context provided but no active_bookmark_baseline.json exists.",
            f"revert_cycle_id={revert_cycle}",
            f"bookmarks_v2_count={len(bookmarks_v2_entries)}",
        )

    fail(
        FAIL_STATE_CORRUPTED,
        "Unhandled state-context combination.",
        f"has_state={has_state} has_spec={has_spec} has_revert={has_revert}",
    )
    return "unreachable"


def check_postpatcher_invariant(
    manifest_path: Path,
    state_context: str,
) -> None:
    manifest = read_json(manifest_path, FAIL_2_3, "patch manifest")
    address_map_path = manifest_path.with_name("address_map.json")
    address_map = read_json(address_map_path, FAIL_2_3, "address map")

    expected_count = CANONICAL_OPCODE_REPLACE_COUNT
    expected_coverage = CANONICAL_TOTAL_GENESIS_BYTES_COVERED
    expected_context = "canonical"
    if state_context == "diagnostic":
        expected_context = "diagnostic"

    observed_context = str(manifest.get("build_context", "canonical")).strip().lower()
    if observed_context and observed_context != expected_context:
        fail(
            FAIL_2_3,
            f"Manifest build_context mismatch: expected {expected_context}, found {observed_context}.",
        )

    segments = address_map.get("segments")
    if not isinstance(segments, list):
        fail(FAIL_2_3, f"address_map segments missing/invalid in {address_map_path}")

    observed_count = 0
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        if str(seg.get("kind", "")) == "patched_site" and str(seg.get("origin", "")) == "opcode_replace":
            observed_count += 1

    segment_coverage = address_map.get("segment_coverage", {})
    observed_coverage_raw = None
    if isinstance(segment_coverage, dict):
        observed_coverage_raw = segment_coverage.get("total_genesis_bytes_covered")
    if observed_coverage_raw is None:
        fail(FAIL_2_3, "address_map segment_coverage.total_genesis_bytes_covered missing.")
    observed_coverage = int(observed_coverage_raw)

    manifest_expected_count = manifest.get("postpatch_expected_opcode_replace_sites")
    if manifest_expected_count is not None and int(manifest_expected_count) != expected_count:
        fail(
            FAIL_2_3,
            "Manifest expected opcode_replace sites mismatch with gate-computed expectation.",
            f"manifest_expected={manifest_expected_count}",
            f"gate_expected={expected_count}",
        )
    manifest_expected_cov = manifest.get("postpatch_expected_total_genesis_bytes_covered")
    if manifest_expected_cov is not None and int(str(manifest_expected_cov), 0) != expected_coverage:
        fail(
            FAIL_2_3,
            "Manifest expected total_genesis_bytes_covered mismatch with gate-computed expectation.",
            f"manifest_expected={manifest_expected_cov}",
            f"gate_expected=0x{expected_coverage:X}",
        )

    if observed_count != expected_count or observed_coverage != expected_coverage:
        fail(
            FAIL_2_3,
            "Postpatch invariant mismatch.",
            f"state_context={state_context}",
            f"expected_opcode_replace_sites={expected_count}",
            f"observed_opcode_replace_sites={observed_count}",
            f"expected_total_genesis_bytes_covered=0x{expected_coverage:X}",
            f"observed_total_genesis_bytes_covered=0x{observed_coverage:X}",
        )


def check_rom_naming(numbered_name: str, counter_path: Path) -> None:
    base = Path(numbered_name).name
    m = EXPECTED_ROM_RE.match(base)
    if not m:
        fail(
            FAIL_2_4,
            f"Observed numbered artifact name: {base}",
            "Expected format: rastan_direct_video_test_build_NNNN.bin",
        )
    observed_n = int(m.group(1))
    if counter_path.exists():
        try:
            current = int(counter_path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            fail(FAIL_2_4, f"Invalid build counter content in {counter_path}")
    else:
        current = 0
    expected_n = current + 1
    if observed_n != expected_n:
        fail(
            FAIL_2_4,
            f"Observed numbered build: {observed_n:04d}",
            f"Expected next build from counter {counter_path}: {expected_n:04d}",
            f"Counter current value: {current}",
        )


def check_symbol_resolution(
    rom: bytes,
    symbols: Dict[str, int],
    spec_path: Path,
    helper_symbol: str,
    incbins: List[IncbinEntry],
) -> None:
    spec_text = spec_path.read_text(encoding="utf-8")
    needed = sorted(set(SPEC_SYMBOL_RE.findall(spec_text)))
    unresolved: List[str] = []
    for name in needed:
        if resolve_symbol(symbols, name) is None:
            unresolved.append(name)
    if unresolved:
        fail(
            FAIL_2_5,
            "Unresolved symbols from spec templates:",
            *[f"- {name}" for name in unresolved],
        )

    check_symbols = {helper_symbol}
    check_symbols.update(entry.symbol for entry in incbins)
    for name in sorted(check_symbols):
        addr = resolve_symbol(symbols, name)
        if addr is None:
            fail(FAIL_2_5, f"Missing required gate symbol: {name}")
        if not (0 <= addr < len(rom)):
            fail(
                FAIL_2_5,
                f"Symbol out of ROM bounds: {name}",
                f"Address: 0x{addr:06X}",
                f"ROM size: {len(rom)}",
            )


def normalize_make_lines(text: str) -> List[str]:
    lines = text.splitlines()
    out: List[str] = []
    buf = ""
    for raw in lines:
        cur = raw
        if cur.rstrip().endswith("\\"):
            buf += cur.rstrip()[:-1] + " "
            continue
        if buf:
            out.append((buf + cur).strip())
            buf = ""
        else:
            out.append(cur.strip())
    if buf:
        out.append(buf.strip())
    return out


def parse_make_vars(lines: List[str]) -> Dict[str, str]:
    vars_map: Dict[str, str] = {}
    for line in lines:
        if not line or line.startswith("#") or line.startswith("\t"):
            continue
        m = ASSIGN_RE.match(line)
        if not m:
            continue
        key, value = m.groups()
        vars_map[key] = value.strip()
    return vars_map


def expand_make_vars(value: str, vars_map: Dict[str, str], depth: int = 0) -> str:
    if depth > 20:
        return value

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in vars_map:
            return expand_make_vars(vars_map[name], vars_map, depth + 1)
        return match.group(0)

    return re.sub(r"\$\(([^)]+)\)", repl, value)


def parse_make_rules(lines: List[str], vars_map: Dict[str, str], makefile_path: Path) -> Dict[Path, Set[Path]]:
    rules: Dict[Path, Set[Path]] = {}
    for line in lines:
        if not line or line.startswith("#") or line.startswith("\t"):
            continue
        if ":" not in line:
            continue
        if ASSIGN_RE.match(line):
            continue

        lhs, rhs = line.split(":", 1)
        lhs = lhs.strip()
        rhs = rhs.strip()
        dep_part = rhs.split("|", 1)[0].strip()
        targets = [t for t in lhs.split() if t]
        deps = [d for d in dep_part.split() if d]

        norm_deps: Set[Path] = set()
        for dep in deps:
            expanded = expand_make_vars(dep, vars_map)
            if expanded.startswith("$"):
                continue
            p = Path(expanded)
            if not p.is_absolute():
                p = (makefile_path.parent / p).resolve()
            norm_deps.add(p)

        for target in targets:
            expanded_t = expand_make_vars(target, vars_map)
            if expanded_t.startswith("$"):
                continue
            pt = Path(expanded_t)
            if not pt.is_absolute():
                pt = (makefile_path.parent / pt).resolve()
            rules[pt] = norm_deps
    return rules


def check_dependency_audit(src_dir: Path, makefile_path: Path, incbins: List[IncbinEntry]) -> None:
    lines = normalize_make_lines(makefile_path.read_text(encoding="utf-8"))
    vars_map = parse_make_vars(lines)
    rules = parse_make_rules(lines, vars_map, makefile_path)
    by_asm: Dict[Path, List[IncbinEntry]] = {}
    for entry in incbins:
        by_asm.setdefault(entry.asm_path, []).append(entry)

    out_dir = (makefile_path.parent / "out").resolve()
    for asm_path, entries in sorted(by_asm.items(), key=lambda kv: str(kv[0])):
        target = (out_dir / f"{asm_path.stem}.o").resolve()
        deps = rules.get(target)
        if deps is None:
            fail(
                FAIL_2_6,
                f"Missing Makefile rule for target object: {target}",
                f"Derived from source: {asm_path}",
            )
        missing: List[str] = []
        for entry in entries:
            if entry.bin_path.resolve() not in deps:
                missing.append(f"{entry.bin_path} (from {asm_path}:{entry.line_no})")
        if missing:
            fail(
                FAIL_2_6,
                f"Dependency hole in Makefile rule for {target}",
                "Missing .incbin dependencies:",
                *[f"- {m}" for m in missing],
            )


def build_bookmark_activator_bytes(helper_addr: int, span_length: int, nop_padding_word: int) -> bytes:
    if span_length < 6 or ((span_length - 6) % 2) != 0:
        fail(
            FAIL_2_7,
            f"bookmark span_length must be >=6 and (span_length-6) divisible by 2; got {span_length}",
        )
    out = bytearray()
    out.extend((0x4E, 0xF9))
    out.extend((helper_addr & 0xFFFFFFFF).to_bytes(4, "big"))
    for _ in range((span_length - 6) // 2):
        out.extend((nop_padding_word & 0xFFFF).to_bytes(2, "big"))
    return bytes(out)


def check_bookmark_activator_bytes(
    rom: bytes,
    symbols: Dict[str, int],
    bookmarks_v2_entries: list[BookmarkV2Entry],
) -> None:
    for entry in bookmarks_v2_entries:
        helper_addr = resolve_symbol(symbols, entry.helper_symbol)
        if helper_addr is None:
            fail(
                FAIL_2_7,
                f"Missing helper symbol for bookmark cycle {entry.cycle_id}: {entry.helper_symbol}",
            )
        if entry.activator_pattern != "JMP_LONG_ABS":
            fail(
                FAIL_2_7,
                f"Unsupported activator_pattern for cycle {entry.cycle_id}: {entry.activator_pattern}",
            )
        expected = build_bookmark_activator_bytes(helper_addr, entry.span_length, entry.nop_padding_word)
        start = entry.runtime_genesis_pc
        end = start + entry.span_length
        if start < 0 or end > len(rom):
            fail(
                FAIL_2_7,
                f"Bookmark ROM range out of bounds for cycle {entry.cycle_id}.",
                f"runtime_genesis_pc=0x{start:08X}",
                f"span_length={entry.span_length}",
                f"rom_size=0x{len(rom):X}",
            )
        observed = rom[start:end]
        if observed != expected:
            fail(
                FAIL_2_7,
                f"Bookmark activator bytes mismatch for cycle {entry.cycle_id}.",
                f"runtime_genesis_pc=0x{start:08X}",
                f"expected={expected.hex().upper()}",
                f"observed={observed.hex().upper()}",
            )


def check_revert_byte_identical(rom: bytes, state: StateFile, state_file_path: Path) -> None:
    observed_sha = sha256_bytes(rom)
    expected_sha = state.pre_insert_canonical_rom_sha256
    if observed_sha != expected_sha:
        fail(
            FAIL_2_8,
            "Authorized revert failed byte-identical check.",
            f"cycle_id={state.cycle_id}",
            f"expected_pre_insert_sha={expected_sha}",
            f"observed_revert_sha={observed_sha}",
        )
    try:
        state_file_path.unlink()
    except FileNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        fail(
            FAIL_STATE_CORRUPTED,
            "Failed to delete active_bookmark_baseline.json after successful revert check.",
            f"path={state_file_path}",
            f"error={exc}",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify canonical/diagnostic ROM determinism gate checks.")
    parser.add_argument("--rom", required=True)
    parser.add_argument("--symbols", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--src-dir", required=True)
    parser.add_argument("--makefile", required=True)
    parser.add_argument("--postpatch-script", required=True)  # retained for compatibility
    parser.add_argument("--patch-manifest", required=True)
    parser.add_argument("--helper-symbol", default="genesistan_diag_bookmark")
    parser.add_argument("--helper-canonical-sha", required=True)
    parser.add_argument("--numbered-counter", required=True)
    parser.add_argument("--numbered-name", required=True)
    parser.add_argument("--bookmark-revert", default="")
    parser.add_argument("--state-file", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    rom_path = Path(args.rom).resolve()
    symbols_path = Path(args.symbols).resolve()
    spec_path = Path(args.spec).resolve()
    src_dir = Path(args.src_dir).resolve()
    makefile_path = Path(args.makefile).resolve()
    manifest_path = Path(args.patch_manifest).resolve()
    counter_path = Path(args.numbered_counter).resolve()

    if args.state_file.strip():
        state_file_path = Path(args.state_file).resolve()
    else:
        state_file_path = (Path(__file__).resolve().parents[2] / "build" / "rastan-direct" / "active_bookmark_baseline.json")

    if not rom_path.exists():
        fail(FAIL_2_5, f"ROM path does not exist: {rom_path}")
    if not symbols_path.exists():
        fail(FAIL_2_5, f"Symbol table path does not exist: {symbols_path}")
    if not spec_path.exists():
        fail(FAIL_2_5, f"Spec path does not exist: {spec_path}")
    if not src_dir.exists():
        fail(FAIL_2_5, f"Source directory does not exist: {src_dir}")
    if not makefile_path.exists():
        fail(FAIL_2_6, f"Makefile path does not exist: {makefile_path}")

    rom = rom_path.read_bytes()
    symbols = parse_symbol_table(symbols_path)
    spec = read_json(spec_path, FAIL_2_5, "spec")
    bookmarks_v2_entries = parse_bookmarks_v2(spec)
    state = read_state_file(state_file_path)
    revert_cycle = normalize_revert_context(args.bookmark_revert)
    state_context = determine_state_context(state, bookmarks_v2_entries, revert_cycle)

    incbins = scan_incbins(src_dir)

    check_incbin_bytes(rom, symbols, incbins)  # §2.1
    check_helper(rom, symbols, args.helper_symbol, args.helper_canonical_sha)  # §2.2
    check_postpatcher_invariant(
        manifest_path,
        state_context=state_context,
    )  # §2.3
    check_rom_naming(args.numbered_name, counter_path)  # §2.4
    check_symbol_resolution(rom, symbols, spec_path, args.helper_symbol, incbins)  # §2.5
    check_dependency_audit(src_dir, makefile_path, incbins)  # §2.6

    if state_context == "diagnostic":
        check_bookmark_activator_bytes(rom, symbols, bookmarks_v2_entries)  # §2.7
    if state_context == "authorized_revert":
        if state is None:
            fail(FAIL_STATE_CORRUPTED, "authorized_revert context resolved without state file payload.")
        check_revert_byte_identical(rom, state, state_file_path)  # §2.8

    print("GATE_PASS")
    print(f"ROM: {rom_path}")
    print(f"Numbered name verified: {Path(args.numbered_name).name}")
    print(f"State context: {state_context}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
