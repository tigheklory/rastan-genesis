#!/usr/bin/env python3
"""Verify PROMT-ID-0106 R1 transition, torch, Stage Clear and ending cuts."""

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
    ap.add_argument("--stageclear-preload", required=True, type=Path)
    ap.add_argument("--boundary-packages", required=True, type=Path)
    ap.add_argument("--boundary-report", required=True, type=Path)
    ap.add_argument("--slot-patterns", required=True, type=Path)
    ap.add_argument("--native-patterns", required=True, type=Path)
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
        "genesistan_stageclear_owner_enter",
        "genesistan_gameplay_scene_restore_after_teardown",
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

    stage_owner = mapped(amap, 0x055F58)
    require_jsr(rom, stage_owner, syms["genesistan_stageclear_owner_enter"], "Stage Clear owner")
    if rom[stage_owner + 6:stage_owner + 10] != bytes.fromhex("302D013E"):
        raise RuntimeError("Stage Clear owner no longer preserves current-record load")
    stage_ready = mapped(amap, 0x055F8C)
    require_jsr(rom, stage_ready, mapped(amap, 0x0561D6), "retained Stage Clear text")
    require_jsr(rom, stage_ready + 6, syms["genesistan_presentation_mark_ready_after_publish"],
                "Stage Clear coherent publication")

    scene_restore = mapped(amap, 0x055F2A)
    require_jsr(
        rom, scene_restore, syms["genesistan_gameplay_scene_restore_after_teardown"],
        "natural post-teardown gameplay scene restore",
    )
    if rom[scene_restore + 6:scene_restore + 8] != b"\x4e\x75":
        raise RuntimeError("post-teardown scene restore no longer preserves the common return")

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

    if "genesistan_gameplay_scene_restore_after_teardown:" not in tilemap:
        raise RuntimeError("natural post-teardown native scene producer is absent")
    restore_contract = (
        "move.b  #1, fg_scene_scroll_reseed_pending",
        "bsr     genesistan_plane_a_scene_scroll_reseed_native",
    )
    if any(token not in tilemap for token in restore_contract):
        raise RuntimeError("post-teardown scene restore does not reuse the complete native producer")
    owner_body = scene.split("genesistan_gameplay_owner_reset:", 1)[1].split("rts", 1)[0]
    if "genesistan_scene_present_pending" in owner_body:
        raise RuntimeError("gameplay owner still arms the already-passed 0x050482 completion latch")
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

    torch_codes = set()
    for group in range(6):
        base = 0x059796 + group * stride + 8
        torch_codes.update(struct.unpack_from(">4H", maincpu, base))
    report = json.loads(args.boundary_report.read_text(encoding="utf-8"))
    package_id = report["record_to_package"][22]
    packages = args.boundary_packages.read_bytes()
    desc = 46 * 4 + package_id * 16
    map_offset, map_count = struct.unpack_from(">IH", packages, desc)
    package_map = dict(struct.unpack_from(">HH", packages, map_offset + i * 4)
                       for i in range(map_count))
    missing_torches = sorted(torch_codes - package_map.keys())
    if missing_torches:
        raise RuntimeError("record-22 package lacks torch codes: " +
                           ", ".join(f"0x{x:04X}" for x in missing_torches))
    debug = json.loads(args.slot_patterns.read_text(encoding="utf-8"))
    native = args.native_patterns.read_bytes()
    slot_debug = debug["packages"][package_id]
    pixel_failures = []
    matrices = set()
    for code in sorted(torch_codes):
        slot = package_map[code]
        entry = slot_debug.get(str(slot))
        expected = native[code * 32:(code + 1) * 32]
        matrices.add(expected)
        if entry is None or bytes.fromhex(entry[1]) != expected:
            pixel_failures.append((code, slot))
    if pixel_failures:
        raise RuntimeError(f"torch slot pixel mismatch: {pixel_failures}")
    if len(matrices) != 18 or any(not any(blob) for blob in matrices):
        raise RuntimeError("torch animation does not retain 18 distinct nonblank pixel matrices")

    preload = args.endround_preload.read_bytes()
    if len(preload) < 4 or preload[-2:] != b"\xff\xff" or (len(preload) - 2) % 4:
        raise RuntimeError("malformed End-Round generated preload")
    preload_pairs = (len(preload) - 2) // 4
    if preload_pairs != 1067:
        raise RuntimeError(f"End-Round preload has {preload_pairs} pairs, expected 1067")

    stage_preload = args.stageclear_preload.read_bytes()
    if len(stage_preload) < 4 or stage_preload[-2:] != b"\xff\xff":
        raise RuntimeError("malformed Stage Clear generated preload")
    stage_pairs = dict(struct.unpack_from(">HH", stage_preload, i)
                       for i in range(0, len(stage_preload) - 2, 4))
    r1_art = {struct.unpack_from(">H", maincpu, 0x056A22 + i * 2)[0] & 0x3FFF
              for i in range(14 * 16)}
    missing_art = sorted(r1_art - stage_pairs.keys())
    if missing_art:
        raise RuntimeError("Stage Clear residency lacks R1 figure tiles: " +
                           ", ".join(f"0x{x:04X}" for x in missing_art[:12]))

    exact_r1_text = (b"YOU ARE A BRAVE\xffFIGHTER TO HAVE\xffCLEARED SUCH A \xff"
                     b"DIFFICULT STAGE. \x00")
    if maincpu[0x05653E:0x05653E + len(exact_r1_text)] != exact_r1_text:
        raise RuntimeError("Round-1 Stage Clear exact text source changed")
    if maincpu[0x055F68:0x055F72] != bytes.fromhex("303C00274EB90003A0EC"):
        raise RuntimeError("Stage Clear no longer sends authentic command 0x27 before state 10")

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
        f"natural_restore=0x{scene_restore:06X} "
        f"torches=4x6 pixels=18/18 provenance=exact stageclear_tiles={len(stage_pairs)} "
        f"stageclear_command=0x27 ending_gate=round6 endround_preload={preload_pairs} text=exact"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
