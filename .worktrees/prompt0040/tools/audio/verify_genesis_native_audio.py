#!/usr/bin/env python3
"""Static production contracts for the AUDIO-015 Genesis-native runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DRIVER_LIMIT = 0x1F80
TIMER_REGISTERS = set(range(0x24, 0x28))


def verify_driver(data: bytes) -> None:
    if len(data) >= DRIVER_LIMIT:
        raise ValueError(f"driver overlaps stack/state: {len(data)} >= 0x{DRIVER_LIMIT:X}")
    if data[:2] != b"\xF3\xC3":
        raise ValueError("reset entry is not DI; JP init")
    init = data[2] | (data[3] << 8)
    if init + 3 > len(data) or data[init : init + 3] != b"\x31\x80\x1F":
        raise ValueError(f"reset JP target 0x{init:04X} is not LD SP,0x1F80")
    if data[0x38:0x3A] != b"\xED\x4D":
        raise ValueError("IM1 vector 0x0038 is not RETI")
    if data[0x66:0x68] != b"\xED\x45":
        raise ValueError("NMI vector 0x0066 is not RETN")
    timer_rearm = data.find(b"\x3E\x27\x1E\x28\xCD")
    if (
        timer_rearm < 0
        or data[timer_rearm + 7 : timer_rearm + 12] != b"\x3E\x26\x1E\xC9\xCD"
        or data[timer_rearm + 14 : timer_rearm + 19] != b"\x3E\x27\x1E\x0A\xC3"
    ):
        raise ValueError("Timer B lacks clear/unload -> C9 -> load/enable rearm sequence")
    if b"\x3A\xFF\x1D" not in data or b"\x21\x00\x1E" not in data:
        raise ValueError("driver does not scan the generated song table at 0x1DFF/0x1E00")


def verify_stream(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    cursor = 0
    ticks = 0
    events = 0
    while cursor < len(data):
        count = data[cursor]
        cursor += 1
        if count == 0xFF:
            if cursor != len(data):
                raise ValueError(f"{path}: bytes follow terminal 0xFF")
            return ticks, events
        ticks += 1
        for _ in range(count):
            if cursor >= len(data):
                raise ValueError(f"{path}: truncated event kind")
            kind = data[cursor]
            cursor += 1
            if kind == 2:
                if cursor >= len(data):
                    raise ValueError(f"{path}: truncated PSG event")
                cursor += 1
            elif kind in (0, 1):
                if cursor + 1 >= len(data):
                    raise ValueError(f"{path}: truncated YM2612 event")
                register = data[cursor]
                cursor += 2
                if kind == 0 and register in TIMER_REGISTERS:
                    raise ValueError(
                        f"{path}: music packet writes driver-owned timer register 0x{register:02X}"
                    )
            else:
                raise ValueError(f"{path}: unsupported event kind {kind}")
            events += 1
    raise ValueError(f"{path}: missing terminal 0xFF")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    driver = args.driver.read_bytes()
    verify_driver(driver)
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("schema") != "rastan-genesis-native-audio-library/v1":
        raise ValueError("unexpected native audio library schema")
    if not manifest.get("fm6_reserved"):
        raise ValueError("Audio Composer profile does not reserve YM2612 FM6/DAC")

    # Proven authentic dispatch: every row proven, in the arcade BGM range, and
    # the hardware-accepted appearance mapping 0x25 must remain present.
    dispatch_commands = []
    for row in manifest["dispatch"]:
        if row.get("status") != "proven":
            raise ValueError(f"dispatch entry not proven: {row}")
        command = int(row["wire_command"], 0)
        if not 0x00 <= command <= 0x2B:
            raise ValueError(f"proven dispatch command 0x{command:02X} outside arcade BGM range")
        dispatch_commands.append(command)
    if 0x25 not in dispatch_commands:
        raise ValueError("accepted appearance mapping 0x25 is missing from dispatch")
    if len(dispatch_commands) != len(set(dispatch_commands)):
        raise ValueError("duplicate proven dispatch command")

    # Diagnostic selection: a reserved 0xC0-0xDF selector for EVERY authored song,
    # disjoint from the proven commands.  These are never emitted by the game.
    diagnostic = manifest.get("diagnostic_selection", [])
    diag_commands = []
    diag_tracks = set()
    authored_tracks = {song["track"] for song in manifest["songs"]}
    for row in diagnostic:
        if row.get("status") != "diagnostic":
            raise ValueError(f"diagnostic entry not labeled diagnostic: {row}")
        command = int(row["select_command"], 0)
        if not 0xC0 <= command <= 0xDF:
            raise ValueError(f"diagnostic selector 0x{command:02X} outside reserved 0xC0-0xDF")
        diag_commands.append(command)
        diag_tracks.add(row["track"])
    if diag_tracks != authored_tracks:
        raise ValueError(
            "diagnostic selection must cover every authored song; "
            f"missing={sorted(authored_tracks - diag_tracks)}"
        )
    if len(diag_commands) != len(set(diag_commands)):
        raise ValueError("duplicate diagnostic selector")
    if set(diag_commands) & set(dispatch_commands):
        raise ValueError("diagnostic selector collides with a proven dispatch command")

    ticks = events = 0
    for song in manifest["songs"]:
        intro_ticks, intro_events = verify_stream(Path(song["intro"]))
        loop_ticks, loop_events = verify_stream(Path(song["loop"]))
        if intro_ticks != song["intro_ticks"] or loop_ticks != song["loop_ticks"]:
            raise ValueError(f"manifest tick mismatch: {song['track']}")
        ticks += intro_ticks + loop_ticks
        events += intro_events + loop_events
    print(
        "AUDIO_NATIVE_STATIC_PASS "
        f"driver={len(driver)} init=0x{driver[2] | (driver[3] << 8):04X} "
        f"songs={len(manifest['songs'])} dispatch={len(dispatch_commands)} "
        f"diagnostic={len(diag_commands)} ticks={ticks} events={events}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
