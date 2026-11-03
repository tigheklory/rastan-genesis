#!/usr/bin/env python3
"""AUDIO-004 / RG-004 — read-only FM-instrument + channel-role + PSG-candidacy analysis from the
existing YM2151 register-write captures (audio/rastan_music_dump/conversion_attempts/*_ym2151_writes.csv).

NO ROM/production change. This extracts the ACTUAL programmed per-channel FM patch state and note
activity FROM THE CAPTURES (not from the ROM instrument table, which is an un-decoded AUDIO-003
prerequisite — so instrument identity here is capture-derived, tagged accordingly). It classifies each
channel's role (musical vs sporadic/SFX vs idle), tests the "~six music voices" hypothesis, and emits a
heuristic FM->PSG candidacy per channel. It does NOT render audio or decide routing.

YM2151 register map (standard):
  0x08 KEY (bits0-2 ch, bits3-6 operator slots)   0x0F NE|NFRQ (ch8 noise)
  0x20-0x27 RL(6-7)|FB(3-5)|CONNECT/algorithm(0-2) per channel (ch=reg-0x20)
  0x28-0x2F KC   0x30-0x37 KF   0x38-0x3F PMS(4-6)|AMS(0-1)
  0x40-0x5F DT1|MUL per operator   0x60-0x7F TL   0x80-0x9F KS|AR   0xA0-0xBF AMEN|D1R
  0xC0-0xDF DT2|D2R   0xE0-0xFF D1L|RR.  Operator reg r: ch=r&7, op=(r>>3)&3.
Algorithm -> carrier operators (OPM/OPN2): 0-3 ->1 carrier (deep FM); 4 ->2; 5,6 ->3; 7 ->4 (additive).
"""
import csv, glob, json, os, sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts")
OUT = os.path.join(ROOT, "build/audio/fm_psg_analysis")

ALGO_CARRIERS = {0: 1, 1: 1, 2: 1, 3: 1, 4: 2, 5: 3, 6: 3, 7: 4}


def analyze(path):
    ch = {c: {"keyon": 0, "keyoff": 0, "kc_writes": 0, "kc_set": set(), "tl_writes": 0,
              "algo": None, "fb": None, "muls": {}, "first_keyon_s": None, "last_keyon_s": None}
          for c in range(8)}
    noise_writes = 0
    rows = 0
    for row in csv.DictReader(open(path, newline="")):
        rows += 1
        try:
            reg = int(row["register"], 16); val = int(row["value"], 16); sec = float(row["seconds"])
        except (ValueError, KeyError):
            continue
        if reg == 0x08:
            c = val & 7; slots = (val >> 3) & 0xF
            if slots:
                ch[c]["keyon"] += 1
                ch[c]["first_keyon_s"] = sec if ch[c]["first_keyon_s"] is None else ch[c]["first_keyon_s"]
                ch[c]["last_keyon_s"] = sec
            else:
                ch[c]["keyoff"] += 1
        elif 0x20 <= reg <= 0x27:
            c = reg - 0x20; ch[c]["algo"] = val & 7; ch[c]["fb"] = (val >> 3) & 7
        elif 0x28 <= reg <= 0x2F:
            c = reg - 0x28; ch[c]["kc_writes"] += 1; ch[c]["kc_set"].add(val)
        elif 0x40 <= reg <= 0x5F:
            c = reg & 7; op = (reg >> 3) & 3; ch[c]["muls"][op] = val & 0x0F
        elif 0x60 <= reg <= 0x7F:
            ch[reg & 7]["tl_writes"] += 1
        elif reg == 0x0F:
            noise_writes += 1 if (val & 0x80) else 0

    out = {"rows": rows, "noise_ch8_writes": noise_writes, "channels": {}}
    musical = 0
    for c in range(8):
        k = ch[c]
        active = k["keyon"] > 0
        span = (k["last_keyon_s"] - k["first_keyon_s"]) if (k["first_keyon_s"] is not None) else 0.0
        # role heuristic (capture-based): musical = many key-ons + distinct pitches over a span;
        #   sporadic/SFX candidate = few key-ons or very few distinct pitches; idle = none.
        role = "idle"
        if active:
            if k["keyon"] >= 20 and len(k["kc_set"]) >= 3 and span > 2.0:
                role = "musical"; musical += 1
            elif k["keyon"] >= 3:
                role = "sporadic_or_sfx_candidate"
            else:
                role = "sparse"
        carriers = ALGO_CARRIERS.get(k["algo"], None) if k["algo"] is not None else None
        # PSG candidacy heuristic (INFERRED, not a fidelity claim): a channel is a *better* PSG candidate
        # when its timbre is simple/bright/stable -> high algorithm (more carriers / additive), low
        # feedback, and monophonic lead/bass behavior. Deep FM (algo 0-3, high feedback) should stay FM.
        psg = "unknown"
        if role in ("musical", "sparse", "sporadic_or_sfx_candidate") and k["algo"] is not None:
            if k["algo"] >= 6 and (k["fb"] or 0) <= 2:
                psg = "candidate"            # simple/bright -> try PSG
            elif k["algo"] in (4, 5):
                psg = "marginal"             # partial FM -> PSG loses timbre, evaluate
            else:
                psg = "keep_fm"              # deep FM (algo 0-3) -> PSG cannot reproduce
        out["channels"][str(c)] = {
            "role": role, "keyon": k["keyon"], "distinct_pitches": len(k["kc_set"]),
            "kc_min": (min(k["kc_set"]) if k["kc_set"] else None),
            "kc_max": (max(k["kc_set"]) if k["kc_set"] else None),
            "active_span_s": round(span, 2),
            "algorithm": k["algo"], "feedback": k["fb"], "carrier_operators": carriers,
            "operator_mul": k["muls"], "tl_writes": k["tl_writes"],
            "psg_candidacy_inferred": psg}
    out["musical_voice_count"] = musical
    out["psg_candidate_channels"] = [c for c in range(8)
                                     if out["channels"][str(c)]["psg_candidacy_inferred"] == "candidate"]
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = {}
    for p in sorted(glob.glob(os.path.join(CAP, "*_ym2151_writes.csv"))):
        name = os.path.basename(p)[:-len("_ym2151_writes.csv")]
        rep = analyze(p)
        json.dump(rep, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
        summary[name] = {"musical_voice_count": rep["musical_voice_count"],
                         "psg_candidate_channels": rep["psg_candidate_channels"],
                         "roles": {c: rep["channels"][c]["role"] for c in rep["channels"]}}
        cand = rep["psg_candidate_channels"]
        print("%-44s musical=%d psg_candidates=%s" % (name[:44], rep["musical_voice_count"], cand))
    json.dump(summary, open(os.path.join(OUT, "_summary.json"), "w"), indent=1)
    print("\nwrote %d reports + _summary.json to %s" % (len(summary), OUT))


if __name__ == "__main__":
    sys.exit(main())
