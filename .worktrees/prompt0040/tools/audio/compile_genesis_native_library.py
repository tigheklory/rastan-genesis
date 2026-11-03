#!/usr/bin/env python3
"""Compile every authored Audio Composer track and generate ROM registries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(track: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", track.lower()).strip("_")
    return "track_" + value


def asm_symbol(track: str, suffix: str) -> str:
    return f"genesistan_audio_{slug(track)}_{suffix}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--song-map", required=True, type=Path)
    ap.add_argument("--capture-dir", required=True, type=Path)
    ap.add_argument("--vgz-dir", required=True, type=Path)
    ap.add_argument("--compiler", required=True, type=Path)
    ap.add_argument("--renderer", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--assembly-include", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    args = ap.parse_args()

    profile = json.loads(args.profile.read_text())
    mapping = json.loads(args.song_map.read_text())
    tracks = sorted(profile.get("track_routings", {}))
    if not tracks:
        raise ValueError("Audio Composer profile has no authored track_routings")

    dispatch = mapping.get("dispatch", [])
    seen_commands: set[int] = set()
    dispatch_by_track: dict[str, list[dict]] = {}
    for row in dispatch:
        command = int(row["wire_command"], 0)
        if row.get("status") != "proven":
            raise ValueError(f"live dispatch entry is not proven: {row}")
        if not 0x00 <= command <= 0x2B:
            raise ValueError(f"proven dispatch command 0x{command:02X} is outside the arcade BGM range 0x00-0x2B")
        if command in seen_commands:
            raise ValueError(f"duplicate wire command 0x{command:02X}")
        if row["track"] not in tracks:
            raise ValueError(f"dispatch track is not authored: {row['track']}")
        seen_commands.add(command)
        dispatch_by_track.setdefault(row["track"], []).append(row)

    # Diagnostic selectors live in the arcade-ignored command range 0xC0-0xDF.
    # The running game never emits them, so production playback is unchanged;
    # they exist only so a labeled diagnostic harness can exercise every stream.
    diagnostic = mapping.get("diagnostic_selection", [])
    diagnostic_by_track: dict[str, dict] = {}
    for row in diagnostic:
        command = int(row["select_command"], 0)
        if row.get("status") != "diagnostic":
            raise ValueError(f"diagnostic entry is not labeled diagnostic: {row}")
        if not 0xC0 <= command <= 0xDF:
            raise ValueError(f"diagnostic selector 0x{command:02X} is outside the reserved 0xC0-0xDF range")
        if command in seen_commands:
            raise ValueError(f"diagnostic selector 0x{command:02X} collides with a dispatch command")
        if row["track"] not in tracks:
            raise ValueError(f"diagnostic track is not authored: {row['track']}")
        if row["track"] in diagnostic_by_track:
            raise ValueError(f"duplicate diagnostic selector for track {row['track']}")
        seen_commands.add(command)
        diagnostic_by_track[row["track"]] = row

    args.output_dir.mkdir(parents=True, exist_ok=True)
    compiled = []
    for index, track in enumerate(tracks, 1):
        stem = slug(track)
        capture = args.capture_dir / f"{track}_ym2151_writes.csv"
        source_vgz = args.vgz_dir / f"{track}.vgz"
        intro = args.output_dir / f"{stem}_intro.bin"
        loop = args.output_dir / f"{stem}_loop.bin"
        report = args.output_dir / f"{stem}_report.json"
        for source in (capture, source_vgz):
            if not source.is_file():
                raise FileNotFoundError(source)
        subprocess.run(
            [sys.executable, str(args.compiler), "--track", track,
             "--capture", str(capture), "--source-vgz", str(source_vgz),
             "--profile", str(args.profile), "--renderer", str(args.renderer),
             "--intro", str(intro), "--loop", str(loop), "--report", str(report)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        details = json.loads(report.read_text())
        compiled.append({
            "id": index,
            "track": track,
            "slug": stem,
            "intro": str(intro),
            "loop": str(loop),
            "intro_sha256": sha256(intro),
            "loop_sha256": sha256(loop),
            "intro_bytes": intro.stat().st_size,
            "loop_bytes": loop.stat().st_size,
            "intro_ticks": details["loop_tick"],
            "loop_ticks": details["loop_ticks"],
            "has_loop": details["has_source_loop"],
            "wire_commands": [r["wire_command"] for r in dispatch_by_track.get(track, [])],
            "diagnostic_command": (
                diagnostic_by_track[track]["select_command"]
                if track in diagnostic_by_track else None
            ),
        })

    lines = [
        "/* Generated by compile_genesis_native_library.py; do not edit. */",
        "    .section .rodata,\"a\"",
        "    .global genesistan_audio_song_catalog_count",
        "    .global genesistan_audio_song_catalog",
        "    .global genesistan_audio_song_dispatch_count",
        "    .global genesistan_audio_song_dispatch",
        "genesistan_audio_song_catalog_count:",
        f"    .byte {len(compiled)}",
        "    .balign 2",
        "genesistan_audio_song_catalog:",
    ]
    for song in compiled:
        commands = song["wire_commands"]
        command = int(commands[0], 0) if commands else 0xFF
        lines += [
            f"    .byte {song['id']}, 0x{command:02X}",
            "    .word 0",
            f"    .long {asm_symbol(song['track'], 'start')}",
            f"    .long {asm_symbol(song['track'], 'loop') if song['has_loop'] else 0}",
        ]
    # The Z80 dispatch table the driver scans holds proven authentic rows first,
    # then the diagnostic selectors.  Both are matched identically by the driver;
    # the diagnostic commands are simply never emitted by the running game.
    table_rows = (
        [(int(row["wire_command"], 0), row["track"]) for row in dispatch]
        + [(int(row["select_command"], 0), row["track"]) for row in diagnostic]
    )
    lines += [
        "genesistan_audio_song_dispatch_count:",
        f"    .byte {len(table_rows)}",
        "    .balign 2",
        "genesistan_audio_song_dispatch:",
    ]
    by_track = {song["track"]: song for song in compiled}
    for command, track in table_rows:
        song = by_track[track]
        lines += [
            f"    .byte 0x{command:02X}, {song['id']}",
            "    .word 0",
            f"    .long {asm_symbol(song['track'], 'start')}",
            f"    .long {asm_symbol(song['track'], 'loop') if song['has_loop'] else 0}",
        ]
    lines += ["    .section .audio,\"a\"", "    .balign 0x8000"]
    for song in compiled:
        start = asm_symbol(song["track"], "start")
        loop = asm_symbol(song["track"], "loop")
        end = asm_symbol(song["track"], "end")
        intro_rel = Path(song["intro"]).as_posix()
        loop_rel = Path(song["loop"]).as_posix()
        lines += [
            f"    .global {start}", f"    .global {loop}", f"    .global {end}",
            f"{start}:", f"    .incbin \"{intro_rel}\"",
            f"{loop}:", f"    .incbin \"{loop_rel}\"", f"{end}:",
        ]
    args.assembly_include.write_text("\n".join(lines) + "\n")

    manifest = {
        "schema": "rastan-genesis-native-audio-library/v1",
        "profile": str(args.profile),
        "profile_sha256": sha256(args.profile),
        "profile_revision": profile.get("revision"),
        "profile_revision_id": profile.get("revision_id"),
        "authored_track_count": len(compiled),
        "songs": compiled,
        "dispatch": dispatch,
        "diagnostic_selection": diagnostic,
        "song_table_rows": len(table_rows),
        "unmapped_command_policy": mapping["unmapped_command_policy"],
        "fm6_reserved": profile.get("reserved_dac") == "ym2612_fm6_dac",
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"AUDIO_NATIVE_LIBRARY_PASS songs={len(compiled)} "
        f"dispatch={len(dispatch)} diagnostic={len(diagnostic)} table_rows={len(table_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
