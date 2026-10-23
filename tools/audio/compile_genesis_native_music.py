#!/usr/bin/env python3
"""Compile an authored YM2612/PSG arrangement into the production Z80 tick stream.

The runtime format is deliberately not VGM.  Each source YM2151 capture is converted
offline by the maintained AUDIO-012 chip converter, grouped at the original Rastan
YM2151 Timer-A rate, and emitted as bounded native-chip write packets:

    u8 event_count; event[event_count]
    event := {0, ym2612_port0_reg, value}
           | {1, ym2612_port1_reg, value}
           | {2, sn76489_value}

The byte 0xff terminates the stream.  Intro and loop are separate cartridge assets,
so the Z80 can restart the proven loop without scanning or interpreting VGM data.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import struct
from collections import defaultdict
from pathlib import Path

YM2151_TIMER_A_HZ = 4_000_000 / (64 * 1024)
VGM_RATE = 44_100
TRACK = "03 - Aggressive World (Scene 1)"


def load_renderer(path: Path):
    spec = importlib.util.spec_from_file_location("rastan_render_genesis_vgm", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def source_loop_samples(vgz_path: Path) -> tuple[int, int, int]:
    raw = gzip.decompress(vgz_path.read_bytes())
    if raw[:4] != b"Vgm ":
        raise ValueError(f"not a VGM/VGZ: {vgz_path}")
    total = struct.unpack_from("<I", raw, 0x18)[0]
    loop_rel = struct.unpack_from("<I", raw, 0x1C)[0]
    loop_len = struct.unpack_from("<I", raw, 0x20)[0]
    if not loop_rel or not loop_len or loop_len > total:
        raise ValueError("Aggressive World source has no valid loop metadata")
    return total, total - loop_len, loop_len


def decode_native_writes(vgm: bytes):
    data_offset = 0x34 + struct.unpack_from("<I", vgm, 0x34)[0]
    i = data_offset
    sample = 0
    writes = []
    while i < len(vgm):
        op = vgm[i]
        i += 1
        if op in (0x52, 0x53):
            writes.append((sample, op - 0x52, vgm[i], vgm[i + 1]))
            i += 2
        elif op == 0x50:
            writes.append((sample, 2, vgm[i], 0))
            i += 1
        elif op == 0x61:
            sample += vgm[i] | (vgm[i + 1] << 8)
            i += 2
        elif op == 0x66:
            break
        else:
            raise ValueError(f"unsupported provisional-render opcode 0x{op:02X}")
    return writes


def encode_ticks(writes, total_samples: int, loop_start_sample: int):
    total_ticks = max(1, round(total_samples * YM2151_TIMER_A_HZ / VGM_RATE))
    loop_tick = round(loop_start_sample * YM2151_TIMER_A_HZ / VGM_RATE)
    grouped = defaultdict(list)
    for sample, kind, reg, value in writes:
        tick = min(total_ticks - 1, round(sample * YM2151_TIMER_A_HZ / VGM_RATE))
        grouped[tick].append((kind, reg, value))

    def span(first: int, last: int) -> bytes:
        out = bytearray()
        for tick in range(first, last):
            events = grouped.get(tick, ())
            if len(events) >= 0xFF:
                raise ValueError(f"tick {tick} contains {len(events)} events")
            out.append(len(events))
            for kind, reg, value in events:
                out.append(kind)
                out.append(reg)
                if kind != 2:
                    out.append(value)
        out.append(0xFF)
        return bytes(out)

    return span(0, loop_tick), span(loop_tick, total_ticks), total_ticks, loop_tick, grouped


def remove_driver_owned_registers(writes):
    """Keep music packets from modifying the permanent driver's scheduler.

    YM2612 port 0 registers 0x24-0x27 are Timer A/B and timer-control state.
    They are capture/converter setup traffic, not authored musical events.  The
    resident Z80 driver exclusively owns them so a song cannot disable its own
    clock, change cadence, or clear/load a timer behind the scheduler.
    """
    kept = []
    removed = []
    for event in writes:
        _, kind, reg, _ = event
        if kind == 0 and 0x24 <= reg <= 0x27:
            removed.append(event)
        else:
            kept.append(event)
    return kept, removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", required=True, type=Path)
    ap.add_argument("--source-vgz", required=True, type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--renderer", required=True, type=Path)
    ap.add_argument("--intro", required=True, type=Path)
    ap.add_argument("--loop", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    args = ap.parse_args()

    profile = json.loads(args.profile.read_text())
    decision = profile["track_routings"][TRACK]
    routing = decision["approved_routing"]
    levels = decision.get("channel_levels", {})
    noise = decision.get("noise_mode", "fixed_1024")
    renderer = load_renderer(args.renderer)
    events = renderer.read_capture(str(args.capture))
    vgm, render_stats = renderer.render(events, routing, noise, levels)
    total, loop_start, loop_len = source_loop_samples(args.source_vgz)
    native_writes, scheduler_writes = remove_driver_owned_registers(
        decode_native_writes(vgm)
    )
    intro, loop, ticks, loop_tick, grouped = encode_ticks(
        native_writes, total, loop_start
    )

    args.intro.parent.mkdir(parents=True, exist_ok=True)
    args.intro.write_bytes(intro)
    args.loop.write_bytes(loop)
    report = {
        "schema": "rastan-genesis-native-audio/v1",
        "track": TRACK,
        "authentic_wire_command": "0x29",
        "original_song_selector": "0x19",
        "profile_revision": profile.get("revision"),
        "profile_revision_id": profile.get("revision_id"),
        "routing": routing,
        "channel_levels": levels,
        "noise_mode": noise,
        "source_total_samples": total,
        "source_loop_start_sample": loop_start,
        "source_loop_samples": loop_len,
        "tick_hz": YM2151_TIMER_A_HZ,
        "total_ticks": ticks,
        "loop_tick": loop_tick,
        "loop_ticks": ticks - loop_tick,
        "intro_bytes": len(intro),
        "loop_bytes": len(loop),
        "native_event_count": sum(len(v) for v in grouped.values()),
        "max_events_per_tick": max(map(len, grouped.values())),
        "scheduler_owned_registers": ["0x24", "0x25", "0x26", "0x27"],
        "scheduler_owned_writes_filtered": len(scheduler_writes),
        "render_stats": render_stats,
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
