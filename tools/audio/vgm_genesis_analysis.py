#!/usr/bin/env python3
"""RG-005 / AUDIO-005 — read-only Genesis VGM analyzer.

Parses a real Sega Genesis VGM command stream (YM2612 + SN76489 PSG) and reports, DETERMINISTICALLY:
  * header (version, clocks, sample/loop totals, data offset)
  * full command-type histogram, with UNSUPPORTED/timing-relevant commands FLAGGED (never silently skipped)
  * per-FM-channel (1-6) activity: key-ons, distinct pitches (fnum/block -> Hz -> note), algorithm/feedback,
    operator DT/MUL/TL, L/R/AMS/FMS, DAC usage on ch6, active time span
  * per-PSG-channel (tone 1-3 + noise) activity: key-ons (atten 15->non-15 transitions), distinct tone
    periods -> Hz -> note, noise mode, active span
  * simultaneous-voice timeline (max concurrent sounding FM + PSG voices), loop boundary in samples/seconds
  * a reusable YM2612 instrument inventory (per channel, each distinct patch snapshot with sample timestamp)

Pitch math uses the EXACT clocks from the file header. No audio is rendered; nothing is modified.

Usage: python3 tools/audio/vgm_genesis_analysis.py "<file.vgm>" [--outdir build/audio/vgm_analysis]
"""
import argparse, gzip, json, math, os, struct, sys
from collections import defaultdict, Counter

SR = 44100  # VGM sample base rate (fixed by spec)


def read_file(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":          # gzip (.vgz) container
        raw = gzip.decompress(raw)
    return raw


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def note_name(freq):
    if not freq or freq <= 0:
        return None
    midi = 69 + 12 * math.log2(freq / 440.0)
    n = int(round(midi))
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return "%s%d" % (names[n % 12], n // 12 - 1)


def parse_header(b):
    if b[:4] != b"Vgm ":
        raise SystemExit("not a VGM file (bad magic %r)" % b[:4])
    ver = u32(b, 0x08)
    data_off = 0x40
    if ver >= 0x150:
        rel = u32(b, 0x34)
        data_off = 0x34 + rel if rel else 0x40
    ym2612 = u32(b, 0x2C) if ver >= 0x110 and len(b) > 0x30 else 0
    sn = u32(b, 0x0C)
    return {
        "version_bcd": "%d.%02d" % (ver >> 8, ver & 0xFF),
        "version_raw": ver,
        "eof_offset": u32(b, 0x04) + 0x04,
        "sn76489_clock": sn,
        "ym2612_clock": ym2612,
        "total_samples": u32(b, 0x18),
        "loop_offset": (u32(b, 0x1C) + 0x1C) if u32(b, 0x1C) else 0,
        "loop_samples": u32(b, 0x20),
        "data_offset": data_off,
        "total_seconds": round(u32(b, 0x18) / SR, 3),
        "loop_seconds": round(u32(b, 0x20) / SR, 3),
    }


# ---- YM2612 state ----------------------------------------------------------
OP_ORDER = [0, 1, 2, 3]  # register slot offsets *4 (S1,S3,S2,S4 chip order; index only for reporting)


class FMChan:
    def __init__(self, idx):
        self.idx = idx            # 1..6
        self.algo = None
        self.fb = None
        self.lr = None            # stereo + AMS/FMS (reg B4)
        self.fnum = 0
        self.block = 0
        self.dtmul = {}           # op -> (dt, mul)
        self.tl = {}              # op -> tl
        self.rs_ar = {}           # op -> (rs, ar)         reg 0x50
        self.am_d1r = {}          # op -> (am, d1r)        reg 0x60
        self.d2r = {}             # op -> d2r              reg 0x70
        self.d1l_rr = {}          # op -> (d1l/sl, rr)     reg 0x80
        self.keyon = 0
        self.keyoff = 0
        self.pitches = set()      # (block,fnum)
        self.first_s = None
        self.last_s = None
        self.sounding = False
        self.patches = []         # instrument snapshots

    def freq(self, clock):
        if not self.fnum:
            return 0.0
        return self.fnum * clock / (144.0 * (2 ** (21 - self.block)))

    def snapshot(self, clock, sec):
        snap = {
            "algorithm": self.algo, "feedback": self.fb, "lr_ams_fms": self.lr,
            "operators": {str(op): {
                "dt": self.dtmul.get(op, (None, None))[0],
                "mul": self.dtmul.get(op, (None, None))[1],
                "tl": self.tl.get(op),
                "rs": self.rs_ar.get(op, (None, None))[0],
                "ar": self.rs_ar.get(op, (None, None))[1],
                "d1r": self.am_d1r.get(op, (None, None))[1],
                "d2r": self.d2r.get(op),
                "sl": self.d1l_rr.get(op, (None, None))[0],
                "rr": self.d1l_rr.get(op, (None, None))[1],
            } for op in range(4)},
        }
        key = json.dumps(snap, sort_keys=True)
        if not self.patches or self.patches[-1]["_key"] != key:
            self.patches.append({"_key": key, "at_s": round(sec, 3), **snap})


def parse(path):
    b = read_file(path)
    hdr = parse_header(b)
    clk = hdr["ym2612_clock"] or 7670454
    snclk = hdr["sn76489_clock"] or 3579545

    fm = {i: FMChan(i) for i in range(1, 7)}
    # PSG
    psg = {c: {"period": 0, "atten": 15, "keyon": 0, "periods": set(), "first_s": None,
               "last_s": None, "sounding": False} for c in range(4)}  # 0-2 tone, 3 noise
    psg_latch = {"chan": 0, "type": 0}
    noise_mode = {"fb": None, "rate": None}

    dac_enabled = False
    dac_samples = 0            # direct YM2612 0x2A / 0x8n data writes
    dac_stream_starts = 0      # DAC-stream playback triggers (0x93 / 0x95)
    dac_stream_stops = 0
    cmd_hist = Counter()
    flagged = []
    sample = 0
    loop_sample_pos = None
    # timeline buckets for simultaneous voices (per 1/60 s frame)
    FRAME = SR // 60
    voices_tl = defaultdict(lambda: {"fm": set(), "psg": set()})

    o = hdr["data_offset"]
    n = len(b)
    loop_abs = hdr["loop_offset"]
    peak = {"total": 0, "fm": 0, "psg": 0, "at_s": 0.0}

    def update_peak(sec):
        nfm = sum(1 for i in range(1, 7) if fm[i].sounding)
        npsg = sum(1 for c in range(4) if psg[c]["sounding"])
        if nfm + npsg > peak["total"]:
            peak.update(total=nfm + npsg, fm=nfm, psg=npsg, at_s=round(sec, 3))

    def touch_fm(ch, sec, on):
        c = fm[ch]
        if on:
            c.keyon += 1
            c.sounding = True
            if c.first_s is None:
                c.first_s = sec
            c.last_s = sec
        else:
            c.keyoff += 1
            c.sounding = False
        update_peak(sec)

    while o < n:
        if loop_abs and loop_sample_pos is None and o >= loop_abs:
            loop_sample_pos = sample
        cmd = b[o]
        cmd_hist[cmd] += 1
        sec = sample / SR
        frame = sample // FRAME

        if cmd == 0x66:                         # end of data
            o += 1
            break
        elif cmd == 0x50:                       # PSG write
            val = b[o + 1]; o += 2
            if val & 0x80:
                psg_latch["chan"] = (val >> 5) & 3
                psg_latch["type"] = (val >> 4) & 1
                ch = psg_latch["chan"]
                if psg_latch["type"] == 1:      # volume/atten
                    atten = val & 0x0F
                    was = psg[ch]["atten"]
                    psg[ch]["atten"] = atten
                    if was == 15 and atten != 15:
                        psg[ch]["keyon"] += 1
                        psg[ch]["sounding"] = True
                        if psg[ch]["first_s"] is None:
                            psg[ch]["first_s"] = sec
                        psg[ch]["last_s"] = sec
                        update_peak(sec)
                    elif atten == 15:
                        psg[ch]["sounding"] = False
                else:                            # tone low 4 bits / noise ctrl
                    if ch == 3:
                        noise_mode["fb"] = (val >> 2) & 1
                        noise_mode["rate"] = val & 3
                    else:
                        psg[ch]["period"] = (psg[ch]["period"] & 0x3F0) | (val & 0x0F)
            else:
                ch = psg_latch["chan"]
                if psg_latch["type"] == 0 and ch != 3:
                    psg[ch]["period"] = (psg[ch]["period"] & 0x00F) | ((val & 0x3F) << 4)
                    if psg[ch]["period"]:
                        psg[ch]["periods"].add(psg[ch]["period"])
        elif cmd == 0x52 or cmd == 0x53:        # YM2612 port0 / port1
            reg = b[o + 1]; dat = b[o + 2]; o += 3
            port = 0 if cmd == 0x52 else 1
            base = 1 + 3 * port                 # port0 -> ch1-3, port1 -> ch4-6
            if reg == 0x28:                     # key on/off
                sel = dat & 0x0F
                chmap = {0: 1, 1: 2, 2: 3, 4: 4, 5: 5, 6: 6}
                if sel in chmap:
                    ch = chmap[sel]
                    ops_on = (dat >> 4) & 0x0F
                    touch_fm(ch, sec, ops_on != 0)
                    if ops_on:
                        fm[ch].snapshot(clk, sec)
            elif reg == 0x2A:
                dac_samples += 1
            elif reg == 0x2B:
                dac_enabled = bool(dat & 0x80)
            elif 0x30 <= reg <= 0x9F:
                ch = base + (reg & 3)
                if (reg & 3) == 3 or ch > 6:
                    pass                        # invalid channel index in this reg block
                else:
                    op = (reg >> 2) & 3
                    c = fm[ch]
                    if 0x30 <= reg <= 0x3F:
                        c.dtmul[op] = ((dat >> 4) & 7, dat & 0x0F)
                    elif 0x40 <= reg <= 0x4F:
                        c.tl[op] = dat & 0x7F
                    elif 0x50 <= reg <= 0x5F:
                        c.rs_ar[op] = ((dat >> 6) & 3, dat & 0x1F)
                    elif 0x60 <= reg <= 0x6F:
                        c.am_d1r[op] = ((dat >> 7) & 1, dat & 0x1F)
                    elif 0x70 <= reg <= 0x7F:
                        c.d2r[op] = dat & 0x1F
                    elif 0x80 <= reg <= 0x8F:
                        c.d1l_rr[op] = ((dat >> 4) & 0x0F, dat & 0x0F)
            elif 0xA0 <= reg <= 0xA2:
                ch = base + (reg & 3); fm[ch].fnum = (fm[ch].fnum & 0x700) | dat
            elif 0xA4 <= reg <= 0xA6:
                ch = base + (reg & 3)
                fm[ch].fnum = (fm[ch].fnum & 0x0FF) | ((dat & 7) << 8)
                fm[ch].block = (dat >> 3) & 7
                if fm[ch].fnum:
                    fm[ch].pitches.add((fm[ch].block, fm[ch].fnum))
            elif 0xB0 <= reg <= 0xB2:
                ch = base + (reg & 3); fm[ch].algo = dat & 7; fm[ch].fb = (dat >> 3) & 7
            elif 0xB4 <= reg <= 0xB6:
                ch = base + (reg & 3); fm[ch].lr = dat
        elif cmd == 0x61:                       # wait nn nn
            w = b[o + 1] | (b[o + 2] << 8); o += 3; sample += w
        elif cmd == 0x62:
            o += 1; sample += 735
        elif cmd == 0x63:
            o += 1; sample += 882
        elif 0x70 <= cmd <= 0x7F:               # wait 1..16
            sample += (cmd & 0x0F) + 1; o += 1
        elif 0x80 <= cmd <= 0x8F:               # YM2612 DAC + wait
            dac_samples += 1; sample += (cmd & 0x0F); o += 1
        elif cmd == 0x67:                        # data block: 0x67 0x66 tt size(4) data
            size = u32(b, o + 3); o += 7 + size
        elif cmd == 0x68:                        # PCM RAM write: 0x68 0x66 ... 11 bytes after cmd
            o += 12
        elif cmd == 0xE0:                        # seek PCM data bank
            o += 5
        elif 0x90 <= cmd <= 0x95:               # DAC stream control (variable)
            lengths = {0x90: 5, 0x91: 5, 0x92: 6, 0x93: 11, 0x94: 2, 0x95: 5}
            if cmd in (0x93, 0x95):             # Start Stream / Start Stream fast-call = a playback trigger
                dac_stream_starts += 1
            elif cmd == 0x94:
                dac_stream_stops += 1
            o += lengths[cmd]
        elif cmd == 0x4F:                        # AUDIO-009: SN76489 GG stereo = 2 bytes (0x4F dd), NOT 3
            o += 2
        elif cmd in (0x51, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F):
            o += 3                               # second-chip reg+data writes we don't track
        elif 0x30 <= cmd <= 0x3F:                # reserved/one-operand range (0x3F included)
            o += 2
        elif 0x40 <= cmd <= 0x4E:
            o += (3 if hdr["version_raw"] >= 0x160 else 2)
        else:
            flagged.append({"offset": o, "cmd": "0x%02X" % cmd})
            o += 1

    # record simultaneous-voice peak by scanning again is costly; approximate via active spans
    total_s = hdr["total_seconds"]
    fm_out = {}
    dac_active = (dac_enabled or dac_samples > 0 or dac_stream_starts > 0)
    for i in range(1, 7):
        c = fm[i]
        # FM6 "active" means it is driving the DAC, whether by direct 0x2A writes OR by DAC-stream triggers.
        active = c.keyon > 0 or (i == 6 and dac_active)
        fm_out[str(i)] = {
            "active": active, "keyon": c.keyon, "keyoff": c.keyoff,
            "distinct_pitches": len(c.pitches),
            "algorithm": c.algo, "feedback": c.fb, "lr_ams_fms": c.lr,
            "span_s": round((c.last_s - c.first_s), 3) if c.first_s is not None else 0.0,
            "pitch_hz_range": _hz_range(c, clk),
            "note_range": _note_range(c, clk),
            "operators": {str(op): {"dt_mul": c.dtmul.get(op), "tl": c.tl.get(op)} for op in range(4)},
            "distinct_patches": len([p for p in c.patches]),
            "is_dac_channel": (i == 6 and dac_active),
            "dac_mechanism": ("direct_2a_writes" if (i == 6 and dac_samples > 0)
                              else "dac_stream_triggers" if (i == 6 and dac_stream_starts > 0)
                              else None),
        }
    psg_out = {}
    names = {0: "tone1", 1: "tone2", 2: "tone3", 3: "noise"}
    for ch in range(4):
        p = psg[ch]
        if ch == 3:
            freqs = []
        else:
            freqs = [snclk / (32.0 * per) for per in p["periods"] if per]
        psg_out[names[ch]] = {
            "active": p["keyon"] > 0,
            "keyon": p["keyon"],
            "distinct_periods": len(p["periods"]) if ch != 3 else None,
            "pitch_hz_range": ([round(min(freqs), 2), round(max(freqs), 2)] if freqs else None),
            "note_range": ([note_name(min(freqs)), note_name(max(freqs))] if freqs else None),
            "first_s": round(p["first_s"], 3) if p["first_s"] is not None else None,
            "last_s": round(p["last_s"], 3) if p["last_s"] is not None else None,
            "span_s": round((p["last_s"] - p["first_s"]), 3) if p["first_s"] is not None else 0.0,
            "noise_mode": (noise_mode if ch == 3 else None),
        }

    instruments = {}
    for i in range(1, 7):
        snaps = [{k: v for k, v in p.items() if k != "_key"} for p in fm[i].patches]
        if snaps:
            instruments[str(i)] = snaps

    return {
        "file": os.path.basename(path),
        "header": hdr,
        "command_histogram": {("0x%02X" % k): v for k, v in sorted(cmd_hist.items())},
        "flagged_unsupported": flagged,
        "dac": {"enabled_seen": dac_enabled, "direct_sample_writes": dac_samples,
                "stream_starts": dac_stream_starts, "stream_stops": dac_stream_stops,
                "active": dac_active,
                "note": "direct_sample_writes counts only 0x2A/0x8n writes; stream_starts counts DAC-stream "
                        "playback triggers (0x93/0x95). A VGM can play all its DAC via streams with "
                        "direct_sample_writes == 0, so DAC activity = active, not direct_sample_writes."},
        "loop_sample_position": loop_sample_pos,
        "peak_simultaneous_voices": peak,
        "fm_channels": fm_out,
        "psg_channels": psg_out,
        "fm_channels_active": [i for i in range(1, 7) if fm_out[str(i)]["active"]],
        "psg_channels_active": [names[ch] for ch in range(4) if psg_out[names[ch]]["active"]],
        "instrument_inventory": instruments,
    }


def _hz_range(c, clk):
    fs = [c.fnum and (fnum * clk / (144.0 * (2 ** (21 - blk)))) for (blk, fnum) in c.pitches]
    fs = [f for f in fs if f]
    return [round(min(fs), 2), round(max(fs), 2)] if fs else None


def _note_range(c, clk):
    fs = [(fnum * clk / (144.0 * (2 ** (21 - blk)))) for (blk, fnum) in c.pitches]
    fs = [f for f in fs if f]
    return [note_name(min(fs)), note_name(max(fs))] if fs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vgm")
    ap.add_argument("--outdir", default="build/audio/vgm_analysis")
    a = ap.parse_args()
    rep = parse(a.vgm)
    os.makedirs(a.outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.vgm))[0]
    out = os.path.join(a.outdir, stem + ".json")
    json.dump(rep, open(out, "w"), indent=1)
    h = rep["header"]
    print("== %s ==" % rep["file"])
    print("VGM %s  YM2612=%d Hz  SN76489=%d Hz  total=%.1fs loop=%.1fs" % (
        h["version_bcd"], h["ym2612_clock"], h["sn76489_clock"], h["total_seconds"], h["loop_seconds"]))
    print("FM active:", rep["fm_channels_active"], " PSG active:", rep["psg_channels_active"],
          " DAC: direct_writes=%d stream_triggers=%d active=%s" % (
              rep["dac"]["direct_sample_writes"], rep["dac"]["stream_starts"], rep["dac"]["active"]))
    for i in range(1, 7):
        c = rep["fm_channels"][str(i)]
        if c["active"]:
            print("  FM%d: keyon=%d pitches=%d algo=%s fb=%s notes=%s span=%.1fs patches=%d%s" % (
                i, c["keyon"], c["distinct_pitches"], c["algorithm"], c["feedback"],
                c["note_range"], c["span_s"], c["distinct_patches"],
                "  [DAC]" if c["is_dac_channel"] else ""))
    for nm in ["tone1", "tone2", "tone3", "noise"]:
        p = rep["psg_channels"][nm]
        if p["active"]:
            print("  PSG %-5s keyon=%d periods=%s notes=%s span=%.1fs" % (
                nm, p["keyon"], p["distinct_periods"], p["note_range"], p["span_s"]))
    if rep["flagged_unsupported"]:
        print("  FLAGGED unsupported commands:", rep["flagged_unsupported"][:10],
              "(+%d more)" % max(0, len(rep["flagged_unsupported"]) - 10))
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
