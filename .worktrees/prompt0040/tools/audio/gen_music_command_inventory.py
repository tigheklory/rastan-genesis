#!/usr/bin/env python3
"""AUDIO-009 — regenerate the Rastan music command inventory with the CORRECT descriptor grammar.

Supersedes the AUDIO-002 inline inventory, which mis-described a descriptor lead byte >= 0x12 (e.g. 0x82)
as a "count of 130 / single_subsequence". Verified against the original Z80 instructions at 0x02AA-0x02FE
(build/audio/audiocpu.disasm.txt), the real song-select grammar is:

  song table : 44 little-endian words at ROM 0x2300 -> descriptor pointers.
  descriptor : first byte B = (BC).
     B == 0        -> empty (RET Z).
     B <  0x12     -> ORDINARY COUNTED form: B is a COUNT; followed by B two-byte records.
                        record: low=C, high=A. high == 0  -> DIRECT COMMAND (byte C).
                                                high != 0  -> little-endian SUBSEQUENCE pointer (BC).
     B >= 0x12     -> SPECIAL CHANNEL/CONTROL IDENTIFIER: B is NOT a count; it is passed directly to
                        0x02FE (the channel/control installer, which special-cases 0x82/0x83 -> 0x8E00
                        ADPCM state and the 0x0348 channel table). The five commands 0x03,0x0A,0x0D,
                        0x21,0x26 use descriptors whose lead byte is 0x82.

Read-only; no ROM/production change. Preserves ROM offsets, raw bytes, and provenance.
"""
import json, os, sys, struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIOCPU = os.path.join(ROOT, "build/regions/audiocpu.bin")
OUT = os.path.join(ROOT, "build/audio/music_command_inventory.json")
SONG_TABLE = 0x2300
N_COMMANDS = 0x2C          # commands 0x00..0x2B are BGM (per AUDIO-001 dispatch 0x0254)
COUNT_THRESHOLD = 0x12     # verified at 0x02C3 (CP 0x12)


def w16(b, o):
    return b[o] | (b[o + 1] << 8)


def parse_descriptor(b, ptr):
    """Return the descriptor model at ROM offset `ptr`, per the verified grammar."""
    if ptr + 1 > len(b):
        return {"descriptor_offset": "0x%04X" % ptr, "form": "out_of_range"}
    lead = b[ptr]
    out = {"descriptor_offset": "0x%04X" % ptr, "lead_byte": "0x%02X" % lead}
    if lead == 0:
        out["form"] = "empty"
        return out
    if lead >= COUNT_THRESHOLD:
        # NOT a count — a channel/control identifier consumed by 0x02FE.
        out["form"] = "channel_control_identifier"
        out["identifier"] = "0x%02X" % lead
        out["note"] = ("lead byte >= 0x12 -> NOT a count; passed to 0x02FE (channel/control installer). "
                       "0x82/0x83 special-case the 0x8E00 ADPCM state + 0x0348 channel table.")
        return out
    # ordinary counted form
    out["form"] = "counted"
    out["count"] = lead
    entries = []
    o = ptr + 1
    for _ in range(lead):
        if o + 1 >= len(b):
            entries.append({"error": "truncated", "offset": "0x%04X" % o})
            break
        low, high = b[o], b[o + 1]
        if high == 0:
            entries.append({"kind": "direct_command", "command": "0x%02X" % low,
                            "raw": "0x%02X%02X" % (high, low)})
        else:
            entries.append({"kind": "subsequence_ptr", "ptr": "0x%04X" % (low | (high << 8)),
                            "raw": "0x%02X%02X" % (high, low)})
        o += 2
    out["entries"] = entries
    return out


def main():
    b = open(AUDIOCPU, "rb").read()
    commands = {}
    special_cmds, counted_cmds = [], []
    subseq_ptrs = set()
    for cmd in range(N_COMMANDS):
        ptr = w16(b, SONG_TABLE + cmd * 2)
        desc = parse_descriptor(b, ptr)
        desc["song_table_entry_offset"] = "0x%04X" % (SONG_TABLE + cmd * 2)
        commands["0x%02X" % cmd] = desc
        if desc.get("form") == "channel_control_identifier":
            special_cmds.append("0x%02X" % cmd)
        elif desc.get("form") == "counted":
            counted_cmds.append("0x%02X" % cmd)
            for e in desc.get("entries", []):
                if e.get("kind") == "subsequence_ptr":
                    subseq_ptrs.add(int(e["ptr"], 16))
    inv = {
        "source_rom": "build/regions/audiocpu.bin (b04-19.49)",
        "provenance": "AUDIO-009: grammar verified against Z80 0x02AA-0x02FE in build/audio/audiocpu.disasm.txt. "
                      "Supersedes the AUDIO-002 'count>=0x12 single_subseq' interpretation (WRONG).",
        "song_table": "0x%04X" % SONG_TABLE,
        "song_table_entries": N_COMMANDS,
        "count_threshold": "0x%02X" % COUNT_THRESHOLD,
        "descriptor_format": {
            "lead_byte==0": "empty",
            "lead_byte<0x12": "COUNT of N two-byte records (high==0 direct command, else LE subseq pointer)",
            "lead_byte>=0x12": "channel/control IDENTIFIER (NOT a count); handled by 0x02FE",
        },
        "banking": "none for music; all observed subsequence pointers < 0x4000 (fixed low ROM). This proves "
                   "only the referenced sequence set, NOT that instruments/all assets are unbanked.",
        "command_to_track_name": "UNRESOLVED (captures named by musical identity, NOT proven to a command byte)",
        "channel_control_identifier_commands": special_cmds,
        "counted_commands": counted_cmds,
        "observed_subsequence_pointer_range": ["0x%04X" % min(subseq_ptrs), "0x%04X" % max(subseq_ptrs)]
        if subseq_ptrs else None,
        "commands": commands,
    }
    json.dump(inv, open(OUT, "w"), indent=1)
    print("wrote", OUT)
    print("channel/control-identifier (lead>=0x12) commands:", special_cmds)
    print("counted commands:", len(counted_cmds))
    for c in special_cmds:
        print("  %s -> %s" % (c, commands[c]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
