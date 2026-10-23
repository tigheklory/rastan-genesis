#!/usr/bin/env python3
"""AUDIO-012 — independent validator for the capture->VGM conversion. Read-only; no ROM/build.

Parses each generated VGM back to (sample,reg,val) events with a SEPARATE parser (not the converter's
own emitter) and checks it against the source CSV: register-write count, exact ordering (incl.
same-timestamp writes), register/value fidelity, cumulative timing, VGM header (magic/version/YM2151
4 MHz clock/end marker), total-sample count, and converter determinism (byte-identical re-run).
Also validates the Lawrence reference VGM header and rejects a truncated VGM. Exit 0 = all pass."""
import csv, glob, os, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts")
VGMDIR = os.path.join(ROOT, "build/audio/capture_vgm")
LAWRENCE = os.path.join(ROOT, "audio/Inglebard Agressive World Handmade Genesis version/LM-Main Stage Theme (1).vgm")
PASS, FAIL = [], []


def ck(n, c, extra=""):
    (PASS if c else FAIL).append(n)
    print(("PASS " if c else "FAIL ") + n + (("  -> " + str(extra)) if extra and not c else ""))


def read_csv_events(path):
    ev = []
    for row in csv.DictReader(open(path, newline="")):
        try:
            ev.append((int(float(row["sample"])), int(row["register"], 16), int(row["value"], 16)))
        except (ValueError, KeyError):
            continue
    return ev


def parse_vgm_ym2151(buf):
    """Independent parse: return (header, events[(sample,reg,val)], flagged)."""
    assert buf[:4] == b"Vgm ", "bad magic"
    ver = struct.unpack_from("<I", buf, 0x08)[0]
    ym2151 = struct.unpack_from("<I", buf, 0x30)[0]
    total = struct.unpack_from("<I", buf, 0x18)[0]
    rel = struct.unpack_from("<I", buf, 0x34)[0]
    o = 0x34 + rel if rel else 0x40
    sample = 0
    ev = []
    flagged = []
    ended = False
    n = len(buf)
    while o < n:
        c = buf[o]
        if c == 0x66:
            ended = True; o += 1; break
        elif c == 0x54:
            ev.append((sample, buf[o + 1], buf[o + 2])); o += 3
        elif c == 0x61:
            sample += buf[o + 1] | (buf[o + 2] << 8); o += 3
        elif c == 0x62:
            sample += 735; o += 1
        elif c == 0x63:
            sample += 882; o += 1
        elif 0x70 <= c <= 0x7F:
            sample += (c & 0xF) + 1; o += 1
        else:
            flagged.append((o, c)); o += 1
    return {"version": ver, "ym2151_clock": ym2151, "total_samples": total, "ended": ended}, ev, flagged


def main():
    sys.path.insert(0, os.path.join(ROOT, "tools/audio"))
    import ym2151_capture_to_vgm as conv

    caps = sorted(glob.glob(os.path.join(CAP, "*_ym2151_writes.csv")))
    ck("captures present (9)", len(caps) == 9, len(caps))
    for p in caps:
        stem = os.path.basename(p)[:-len("_ym2151_writes.csv")]
        vgmp = os.path.join(VGMDIR, stem + ".vgm")
        if not os.path.exists(vgmp):
            ck("%s: VGM exists" % stem[:28], False, "missing"); continue
        csv_ev = read_csv_events(p)
        buf = open(vgmp, "rb").read()
        hdr, vgm_ev, flagged = parse_vgm_ym2151(buf)
        base = stem[:26]
        ck("%s: header magic+ver 1.51" % base, hdr["version"] == 0x151)
        ck("%s: YM2151 clock 4 MHz" % base, hdr["ym2151_clock"] == 4000000, hdr["ym2151_clock"])
        ck("%s: end marker present" % base, hdr["ended"])
        ck("%s: no unsupported cmds" % base, flagged == [], flagged[:3])
        ck("%s: reg-write count matches CSV" % base, len(vgm_ev) == len(csv_ev), (len(vgm_ev), len(csv_ev)))
        # exact order + reg/val + timing
        order_ok = all((vgm_ev[i][1], vgm_ev[i][2]) == (csv_ev[i][1], csv_ev[i][2]) for i in range(min(len(vgm_ev), len(csv_ev))))
        ck("%s: reg/val order preserved" % base, order_ok)
        time_ok = all(vgm_ev[i][0] == csv_ev[i][0] for i in range(min(len(vgm_ev), len(csv_ev))))
        ck("%s: cumulative timing matches CSV samples" % base, time_ok)
        ck("%s: total_samples == last event" % base,
           hdr["total_samples"] == (csv_ev[-1][0] if csv_ev else 0), hdr["total_samples"])
        # determinism: re-convert and compare bytes
        ev2 = conv.read_capture(p)
        vgm2, _ = conv.convert(ev2)
        ck("%s: conversion deterministic (byte-identical)" % base, bytes(vgm2) == buf)

    # same-timestamp ordering: synthesize two writes at the same sample and confirm order preserved
    same_ts = [(10, 0x20, 0xC0), (10, 0x28, 0x4A), (10, 0x08, 0x78)]
    v, _ = conv.convert(same_ts)
    _, ev, _ = parse_vgm_ym2151(v)
    ck("same-timestamp writes keep order (no reordering)",
       [(e[1], e[2]) for e in ev] == [(0x20, 0xC0), (0x28, 0x4A), (0x08, 0x78)], ev)

    # Lawrence VGM header sanity (unchanged reference)
    lb = open(LAWRENCE, "rb").read()
    ck("Lawrence VGM magic ok", lb[:4] == b"Vgm ")
    ck("Lawrence VGM YM2612 clock present", struct.unpack_from("<I", lb, 0x2C)[0] == 7670454,
       struct.unpack_from("<I", lb, 0x2C)[0])

    # truncated VGM rejection
    try:
        parse_vgm_ym2151(b"Vgm ")
        ck("truncated VGM rejected", False, "no error")
    except Exception:
        ck("truncated VGM rejected", True)

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
