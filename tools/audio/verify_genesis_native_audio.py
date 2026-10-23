#!/usr/bin/env python3
"""Static production contracts for the AUDIO-015 Genesis-native runtime."""

from __future__ import annotations

import argparse
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
    if b"\xFE\x25" not in data:
        raise ValueError("driver does not classify live player-appearance/respawn command 0x25")


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
    parser.add_argument("--intro", required=True, type=Path)
    parser.add_argument("--loop", required=True, type=Path)
    args = parser.parse_args()

    driver = args.driver.read_bytes()
    verify_driver(driver)
    intro_ticks, intro_events = verify_stream(args.intro)
    loop_ticks, loop_events = verify_stream(args.loop)
    print(
        "AUDIO_NATIVE_STATIC_PASS "
        f"driver={len(driver)} init=0x{driver[2] | (driver[3] << 8):04X} "
        f"intro_ticks={intro_ticks} loop_ticks={loop_ticks} "
        f"events={intro_events + loop_events}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
