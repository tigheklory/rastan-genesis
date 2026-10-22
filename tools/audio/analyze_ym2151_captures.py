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
    # AUDIO-009 (Cody AUDIO-008 claim 24): a register-0x08 write with a ZERO operator mask is a KEY-OFF,
    # not a key-on. Count key-on / key-off / key-code separately; "ever keyed" = had a real key-on;
    # "sustained" is an explicitly-documented heuristic; musical-voice identity is NOT established here.
    ch = {c: {"key_on_events": 0, "key_off_events": 0, "kc_writes": 0, "tl_writes": 0, "conn_writes": 0,
              "operators_keyed": set(), "distinct_kc": set(), "last_kc": None, "connect": None,
              "first_s": None, "last_s": None} for c in range(8)}
    noise_used = False
    timers = {"timerA": 0, "timerB": 0, "timerctrl": 0}
    lfo_used = False
    active = set()                  # channels currently holding >=1 keyed operator
    peak_keyed = 0                  # peak SIMULTANEOUSLY KEYED channels (occupancy, NOT proven audibility)
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
                if slots:                                   # KEY-ON (>=1 operator slot set)
                    ch[c]["key_on_events"] += 1
                    ch[c]["operators_keyed"].update([i for i in range(4) if slots & (1 << i)])
                    active.add(c); keyon_timeline.append([round(sec, 4), c, slots])
                    if ch[c]["first_s"] is None:
                        ch[c]["first_s"] = sec
                    ch[c]["last_s"] = sec
                else:                                       # KEY-OFF (zero mask)
                    ch[c]["key_off_events"] += 1
                    active.discard(c)
                peak_keyed = max(peak_keyed, len(active))
            elif 0x28 <= reg <= 0x2F:
                c = reg - 0x28; ch[c]["kc_writes"] += 1; ch[c]["last_kc"] = val; ch[c]["distinct_kc"].add(val)
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
    # channels EVER KEYED = had at least one real key-on (NOT inflated by key-offs or KC writes).
    channels_keyed = [c for c in range(8) if ch[c]["key_on_events"] > 0]
    # SUSTAINED heuristic (documented, NOT a sequencer-derived musical identity):
    #   >=20 key-ons AND >=3 distinct key-codes AND active span > 2.0 s.
    SUSTAIN = {"min_key_on": 20, "min_distinct_kc": 3, "min_span_s": 2.0}
    sustained = []
    for c in channels_keyed:
        span = (ch[c]["last_s"] - ch[c]["first_s"]) if ch[c]["first_s"] is not None else 0.0
        if (ch[c]["key_on_events"] >= SUSTAIN["min_key_on"] and len(ch[c]["distinct_kc"]) >= SUSTAIN["min_distinct_kc"]
                and span > SUSTAIN["min_span_s"]):
            sustained.append(c)
    psg_candidates = [c for c in channels_keyed if ch[c]["connect"] == 7 and len(ch[c]["operators_keyed"]) <= 2]
    return {
        "rows": rows,
        "channels_ever_keyed": channels_keyed,
        "channels_ever_keyed_count": len(channels_keyed),
        "peak_simultaneously_keyed": peak_keyed,
        "sustained_channels_heuristic": sustained,
        "sustained_heuristic_definition": SUSTAIN,
        "musically_identified_voices": None,   # NOT established without AUDIO-003 sequence decode
        "noise_ch8_used": noise_used,
        "lfo_used": lfo_used, "timers": timers,
        "metric_note": "Key-on OCCUPANCY (channels_ever_keyed / peak_simultaneously_keyed) does NOT prove "
                       "audible polyphony or musical-voice identity. 'sustained' is the documented heuristic "
                       "above; true musical-voice identity needs AUDIO-003.",
        "per_channel": {str(c): {"key_on_events": ch[c]["key_on_events"],
                                  "key_off_events": ch[c]["key_off_events"],
                                  "kc_writes": ch[c]["kc_writes"], "distinct_kc": len(ch[c]["distinct_kc"]),
                                  "tl_writes": ch[c]["tl_writes"], "connect_algo": ch[c]["connect"],
                                  "operators_keyed": sorted(ch[c]["operators_keyed"]),
                                  "span_s": round((ch[c]["last_s"] - ch[c]["first_s"]), 3)
                                  if ch[c]["first_s"] is not None else 0.0}
                        for c in channels_keyed},
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
        summary[name] = {k: rep[k] for k in ("channels_ever_keyed_count", "channels_ever_keyed",
                         "peak_simultaneously_keyed", "sustained_channels_heuristic",
                         "noise_ch8_used", "rows")}
        print("%-44s keyed=%d %s peak_keyed=%d sustained=%s noise=%s" % (
            name[:44], rep["channels_ever_keyed_count"], rep["channels_ever_keyed"],
            rep["peak_simultaneously_keyed"], rep["sustained_channels_heuristic"], rep["noise_ch8_used"]))
    with open(os.path.join(OUT, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\nwrote %d per-track reports + _summary.json to %s" % (len(caps), OUT))


if __name__ == "__main__":
    sys.exit(main())
