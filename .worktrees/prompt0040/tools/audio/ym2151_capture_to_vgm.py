#!/usr/bin/env python3
"""AUDIO-012 — deterministic ORIGINAL-ARCADE YM2151 capture -> VGM converter.

Transforms a recorded Rastan YM2151 register-write stream
(audio/rastan_music_dump/conversion_attempts/*_ym2151_writes.csv; columns sample,seconds,register,value)
into a standard, correctly-timed VGM v1.51 stream that any conformant VGM player (e.g. webVGM/VGMPlay on
the user's machine) can play. No musical content is invented or modified.

WHY this is clean: it is 100% first-party code producing a standard container. It does NOT bundle or
depend on any third-party chip-emulation core (the webVGM/VGMPlay cores are MAME-licensed / GPL-family
and were NOT imported — see docs/design/Andy_AUDIO012_webvgm_audio_composer_integration.md).

Timing: the capture `sample` column is already in the 44100 Hz VGM timebase (verified: sample 3 at
6.80e-5 s = 3/44100). Waits are therefore the exact per-event sample deltas; same-sample writes emit no
intervening wait, so original ordering (including same-timestamp writes) is preserved byte-for-byte.
Clock: YM2151 = 4,000,000 Hz (project-authoritative arcade clock). Register/value bytes are copied as-is.

The generated .vgm files are ANALYSIS/PLAYBACK artifacts, NOT Genesis production music assets.
"""
import argparse, csv, glob, json, os, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts")
OUT = os.path.join(ROOT, "build/audio/capture_vgm")
YM2151_CLOCK = 4000000      # arcade-authoritative (Z80/YM2151 = 16 MHz/4)
VGM_RATE = 44100


def read_capture(path):
    """Return ordered [(sample:int, reg:int, val:int)], preserving file order incl. same-sample rows."""
    events = []
    with open(path, newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            try:
                reg = int(row["register"], 16)
                val = int(row["value"], 16)
            except (ValueError, KeyError):
                raise ValueError("row %d: bad register/value %r" % (i, row))
            # sample column is integer 44100 Hz ticks; fall back to seconds*44100 if absent/blank
            s = row.get("sample")
            if s not in (None, ""):
                sample = int(float(s))
            else:
                sample = int(round(float(row["seconds"]) * VGM_RATE))
            events.append((sample, reg, val))
    return events


def emit_wait(data, samples):
    """Append VGM wait command(s) for `samples` (0x61 nn nn, split above 65535)."""
    while samples > 0:
        n = min(samples, 65535)
        data += bytes([0x61, n & 0xFF, (n >> 8) & 0xFF])
        samples -= n


def convert(events):
    """Return (vgm_bytes, stats). YM2151 write = 0x54 aa dd; wait = 0x61 nnnn; end = 0x66."""
    data = bytearray()
    last = 0
    reg_writes = 0
    for sample, reg, val in events:
        delta = sample - last
        if delta < 0:
            raise ValueError("non-monotonic sample time at reg 0x%02X (%d < %d)" % (reg, sample, last))
        if delta:
            emit_wait(data, delta)
            last = sample
        data += bytes([0x54, reg & 0xFF, val & 0xFF])   # YM2151 register write
        reg_writes += 1
    data += bytes([0x66])                                # end of sound data
    total_samples = events[-1][0] if events else 0

    # ---- VGM 1.51 header (0x40 bytes) ----
    hdr = bytearray(0x40)
    hdr[0x00:0x04] = b"Vgm "
    struct.pack_into("<I", hdr, 0x08, 0x151)             # version 1.51
    struct.pack_into("<I", hdr, 0x18, total_samples)     # total # samples
    struct.pack_into("<I", hdr, 0x24, 60)                # rate (informational)
    struct.pack_into("<I", hdr, 0x30, YM2151_CLOCK)      # YM2151 clock (offset 0x30)
    struct.pack_into("<I", hdr, 0x34, 0x0C)              # VGM data offset (rel 0x34 -> 0x40)
    vgm = bytes(hdr) + bytes(data)
    struct.pack_into("<I", bytearray(vgm), 0x04, 0)      # (placeholder; set below on a mutable copy)
    vgm = bytearray(vgm)
    struct.pack_into("<I", vgm, 0x04, len(vgm) - 4)      # EOF offset
    return bytes(vgm), {"reg_writes": reg_writes, "total_samples": total_samples,
                        "duration_s": round(total_samples / VGM_RATE, 3), "bytes": len(vgm)}


def convert_file(path, outdir):
    events = read_capture(path)
    vgm, stats = convert(events)
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.basename(path)[:-len("_ym2151_writes.csv")]
    out = os.path.join(outdir, stem + ".vgm")
    with open(out, "wb") as f:
        f.write(vgm)
    stats.update(track=stem, out=out, source_events=len(events))
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", help="convert only the capture whose stem contains this substring")
    ap.add_argument("--outdir", default=OUT)
    a = ap.parse_args()
    caps = sorted(glob.glob(os.path.join(CAP, "*_ym2151_writes.csv")))
    if a.one:
        caps = [p for p in caps if a.one.lower() in os.path.basename(p).lower()]
    manifest = []
    for p in caps:
        st = convert_file(p, a.outdir)
        manifest.append(st)
        print("%-44s events=%-6d regwrites=%-6d dur=%6.2fs -> %s" % (
            st["track"][:44], st["source_events"], st["reg_writes"], st["duration_s"],
            os.path.relpath(st["out"], ROOT)))
    with open(os.path.join(a.outdir, "_manifest.json"), "w") as f:
        json.dump({"clock_hz": YM2151_CLOCK, "vgm_version": "1.51", "timebase_hz": VGM_RATE,
                   "note": "first-party conversion; no third-party chip core bundled", "tracks": manifest}, f, indent=1)
    print("\nwrote %d VGM(s) + _manifest.json to %s" % (len(manifest), os.path.relpath(a.outdir, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
