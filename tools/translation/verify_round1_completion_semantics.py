#!/usr/bin/env python3
"""Verify PROMT-ID-0104/0105 R1 scene/torch and final-ending semantic cuts."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def mapped(address_map: dict[str, object], arcade_pc: int) -> int:
    for raw in address_map.get("segments", []):
        segment = dict(raw)
        if "arcade_start" not in segment:
            continue
        start = int(str(segment["arcade_start"]), 0)
        end = int(str(segment["arcade_end_exclusive"]), 0)
        if start <= arcade_pc < end:
            return int(str(segment["genesis_start"]), 0) + arcade_pc - start
    raise RuntimeError(f"arcade PC 0x{arcade_pc:06X} absent from address map")


def symbols(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                result[fields[-1]] = int(fields[0], 16)
            except ValueError:
                pass
    return result


def require_jsr(rom: bytes, site: int, target: int, label: str) -> None:
    actual = rom[site:site + 6]
    expected = b"\x4e\xb9" + struct.pack(">I", target)
    if actual != expected:
        raise RuntimeError(
            f"{label}: expected JSR 0x{target:06X} at 0x{site:06X}, got {actual.hex()}"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--maincpu", required=True, type=Path)
    ap.add_argument("--address-map", required=True, type=Path)
    ap.add_argument("--symbols", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--scene-source", required=True, type=Path)
    ap.add_argument("--tilemap-source", required=True, type=Path)
    ap.add_argument("--endround-preload", required=True, type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    maincpu = args.maincpu.read_bytes()
    amap = json.loads(args.address_map.read_text(encoding="utf-8"))
    syms = symbols(args.symbols)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    scene = args.scene_source.read_text(encoding="utf-8")
    tilemap = args.tilemap_source.read_text(encoding="utf-8")

    needed = {
        "genesistan_endround_owner_enter",
        "genesistan_endround_plane_a_clear",
        "genesistan_presentation_mark_ready_after_publish",
    }
    missing = sorted(needed - syms.keys())
    if missing:
        raise RuntimeError("missing linker symbols: " + ", ".join(missing))

    site = mapped(amap, 0x05727A)
    require_jsr(rom, site, syms["genesistan_endround_owner_enter"], "End-Round owner")
    require_jsr(rom, site + 6, mapped(amap, 0x057808), "retained End-Round palette call")
    ready = mapped(amap, 0x0574A2)
    require_jsr(
        rom, ready, syms["genesistan_presentation_mark_ready_after_publish"],
        "End-Round initial presentation completion",
    )
    if rom[ready + 6:ready + 8] != b"\x4e\x75":
        raise RuntimeError("End-Round initial presentation no longer preserves RTS")
    clear = mapped(amap, 0x0575C4)
    require_jsr(rom, clear, syms["genesistan_endround_plane_a_clear"], "End-Round Plane-A clear")
    if rom[clear + 6:clear + 8] != b"\x4e\x75":
        raise RuntimeError("End-Round Plane-A cut does not retire the chip tail with RTS")

    shifts = {int(row["arcade_pc"], 0): row for row in spec["shift_replacements"]}
    for pc in (0x05727A, 0x0574A2, 0x0575C4):
        if pc not in shifts:
            raise RuntimeError(f"missing semantic shift replacement at 0x{pc:06X}")
    torch = [
        row for family in ("opcode_replace", "shift_replacements")
        for row in spec.get(family, []) if int(row["arcade_pc"], 0) == 0x059736
    ]
    if len(torch) != 1 or "genesistan_phase3_fg_anim_native" not in torch[0]["replacement_bytes"]:
        raise RuntimeError("retained 0x0596F4 torch producer lacks native 0x059736 chip-tail cut")

    if "move.b  #1, genesistan_scene_present_pending" not in scene:
        raise RuntimeError("natural gameplay owner does not arm full-scene publication")
    provenance = (
        "lea     plane_a_resident_logical_rows, %a1",
        "move.b  0(%a1,%d7.w), %d0",
        "cmp.w   %d7, %d0",
    )
    if any(token not in tilemap for token in provenance):
        raise RuntimeError("Phase-3 publication is not gated by exact physical-row provenance")
    if "genesistan_endround_plane_a_clear:" not in tilemap or "staged_fg_buffer" not in tilemap:
        raise RuntimeError("native End-Round Plane-A clear is absent")

    if maincpu[0x059792:0x059796] != b"\x00\x04\x00\x06":
        raise RuntimeError("Round-1 torch stream is not the original 4-phase/6-group table")
    expected_destinations = (
        0x00C0AABC, 0x00C0AA3C, 0x00C0ABBC, 0x00C0AB3C,
        0x00C0ACBC, 0x00C0AC3C, 0x00C0AAC0, 0x00C0AA40,
        0x00C0ABC0, 0x00C0AB40, 0x00C0ACC0, 0x00C0AC40,
    )
    stride = 16
    actual_destinations: list[int] = []
    for group in range(6):
        base = 0x059796 + group * stride
        actual_destinations.extend(
            (int.from_bytes(maincpu[base:base + 4], "big"),
             int.from_bytes(maincpu[base + 4:base + 8], "big"))
        )
    if tuple(actual_destinations) != expected_destinations:
        raise RuntimeError("Round-1 torch destination table changed")

    preload = args.endround_preload.read_bytes()
    if len(preload) < 4 or preload[-2:] != b"\xff\xff" or (len(preload) - 2) % 4:
        raise RuntimeError("malformed End-Round generated preload")
    preload_pairs = (len(preload) - 2) // 4
    if preload_pairs != 1067:
        raise RuntimeError(f"End-Round preload has {preload_pairs} pairs, expected 1067")

    # 0x05725A/0x057272 is not an after-every-boss intermission.  The caller
    # enters it only when the retained round selector at 0x10C118 is six.
    # Lock that distinction so R1 validation cannot claim the final ending.
    round6_gate = bytes.fromhex("10390010c1180c400006")
    if maincpu[0x055F42:0x055F42 + len(round6_gate)] != round6_gate:
        raise RuntimeError("final End-Round owner is no longer gated by round selector 6")

    exact_text = (
        b"THIS IS ONLY A \xffPART OF MY LONG\xffSTORY-ONLY A   \xff"
        b"PART TO BECOME \xffA KING.        \xffIF I HAVE      \xff"
        b"ANOTHER CHANCE,\xffI'LL TELL YOU  \xffMY OTHER       \xff"
        b"ADVENTUROUS    \xffSTORIES.       \x00"
    )
    if maincpu[0x057910:0x057910 + len(exact_text)] != exact_text:
        raise RuntimeError("final End-Round exact text source changed")

    print(
        "ROUND1_COMPLETION_SEMANTICS_PASS "
        f"owner=0x{site:06X} ready=0x{ready:06X} plane_a_clear=0x{clear:06X} "
        f"torches=4x6 provenance=exact ending_gate=round6 "
        f"endround_preload={preload_pairs} text=exact"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
