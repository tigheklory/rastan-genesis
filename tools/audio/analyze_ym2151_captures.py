#!/usr/bin/env python3
"""AUDIO-002 / RG-002 — read-only YM2151 capture analyzer.

Processes the existing captured YM2151 register-write streams in
audio/rastan_music_dump/conversion_attempts/*_ym2151_writes.csv (columns: sample,seconds,register,value)
and emits per-track channel-activity + instrument + pitch/volume + simultaneous-voice reports.

Deterministic, no ROM/production change. Cross-checks the Z80 ROM recovery (AUDIO-001/002) against the
captured hardware behavior. It does NOT make FM/PSG routing decisions — it only reports evidence.

YM2151 register map used (standard, see the YM2151 datasheet):
  0x01 TEST/LFO-reset   0x08 KEY-ON/OFF (bits0-2=channel, bits3-6=operator slots)
  0x0F NOISE enable (ch8)   0x10/0x11 Timer A   0x12 Timer B   0x14 Timer control/IRQ
  0x18 LFRQ  0x19 PMD/AMD  0x1B CT/W
  0x20-0x27 RL|FB|CONNECT (per channel, ch=reg-0x20)
  0x28-0x2F KC key-code (per channel)   0x30-0x37 KF key-fraction (per channel)
  0x38-0x3F PMS|AMS (per channel)
  0x40-0x5F DT1|MUL (per operator)      0x60-0x7F TL total-level (per operator)
  0x80-0x9F KS|AR   0xA0-0xBF AMS-EN|D1R   0xC0-0xDF DT2|D2R   0xE0-0xFF D1L|RR
Operator register index r (0x40..0xFF): channel = r & 7 ; operator slot = (r>>3)&3.
"""
import csv, json, os, sys, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts")
OUT = os.path.join(ROOT, "build/audio/ym2151_track_reports")


def analyze(path):
    ch = {c: {"keyon_events": 0, "kc_writes": 0, "tl_writes": 0, "conn_writes": 0,
              "operators_keyed": set(), "last_kc": None, "connect": None} for c in range(8)}
    noise_used = False
    timers = {"timerA": 0, "timerB": 0, "timerctrl": 0}
    lfo_used = False
    # simultaneous voices: track which channels currently have >=1 operator keyed
    active = set()
    peak_simul = 0
    keyon_timeline = []
    rows = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows += 1
            try:
                reg = int(row["register"], 16); val = int(row["value"], 16)
                sec = float(row["seconds"])
            except (ValueError, KeyError):
                continue
            if reg == 0x08:  # key on/off
                c = val & 7; slots = (val >> 3) & 0xF
                ch[c]["keyon_events"] += 1
                if slots:
                    ch[c]["operators_keyed"].update([i for i in range(4) if slots & (1 << i)])
                    active.add(c); keyon_timeline.append([round(sec, 4), c, slots])
                else:
                    active.discard(c)
                peak_simul = max(peak_simul, len(active))
            elif 0x28 <= reg <= 0x2F:
                c = reg - 0x28; ch[c]["kc_writes"] += 1; ch[c]["last_kc"] = val
            elif 0x20 <= reg <= 0x27:
                c = reg - 0x20; ch[c]["conn_writes"] += 1; ch[c]["connect"] = val & 7
            elif 0x60 <= reg <= 0x7F:
                ch[reg & 7]["tl_writes"] += 1
            elif reg == 0x0F:
                noise_used = noise_used or bool(val & 0x80)
            elif reg in (0x10, 0x11):
                timers["timerA"] += 1
            elif reg == 0x12:
                timers["timerB"] += 1
            elif reg == 0x14:
                timers["timerctrl"] += 1
            elif reg in (0x18, 0x19):
                lfo_used = True
    used = [c for c in range(8) if ch[c]["keyon_events"] > 0 or ch[c]["kc_writes"] > 0]
    # PSG candidacy heuristic (evidence only, NOT a routing decision): a channel using CONNECT=7
    # (all-parallel / simple) with few operators keyed is a lighter voice more tolerable on PSG.
    psg_candidates = [c for c in used if ch[c]["connect"] == 7 and len(ch[c]["operators_keyed"]) <= 2]
    return {
        "rows": rows, "channels_used": used, "channel_count": len(used),
        "peak_simultaneous_voices": peak_simul, "noise_ch8_used": noise_used,
        "lfo_used": lfo_used, "timers": timers,
        "per_channel": {str(c): {"keyon_events": ch[c]["keyon_events"],
                                  "kc_writes": ch[c]["kc_writes"], "tl_writes": ch[c]["tl_writes"],
                                  "connect_algo": ch[c]["connect"],
                                  "operators_keyed": sorted(ch[c]["operators_keyed"])}
                        for c in used},
        "psg_candidate_channels_evidence_only": psg_candidates,
        "keyon_timeline_first50": keyon_timeline[:50],
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    caps = sorted(glob.glob(os.path.join(CAP, "*_ym2151_writes.csv")))
    summary = {}
    for p in caps:
        name = os.path.basename(p)[:-len("_ym2151_writes.csv")]
        rep = analyze(p)
        with open(os.path.join(OUT, name + ".json"), "w") as f:
            json.dump(rep, f, indent=1)
        summary[name] = {k: rep[k] for k in ("channel_count", "channels_used",
                         "peak_simultaneous_voices", "noise_ch8_used", "rows")}
        print("%-44s ch=%d used=%s peak_simul=%d noise=%s" % (
            name[:44], rep["channel_count"], rep["channels_used"],
            rep["peak_simultaneous_voices"], rep["noise_ch8_used"]))
    with open(os.path.join(OUT, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\nwrote %d per-track reports + _summary.json to %s" % (len(caps), OUT))


if __name__ == "__main__":
    sys.exit(main())
