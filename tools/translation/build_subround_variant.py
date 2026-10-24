#!/usr/bin/env python3
"""RG-018: generate a starting-subround test ROM from a parent canonical ROM.

Rastan's original startup reads a packed config byte (arcade 0x05FF9F, the low byte
of the word read at 0x05FF9E by `movew 0x5ff9e,d0` in the 0x03AFEE startup decoder
and the 0x04527E gameplay stage decoder).  Its bits select the starting stage:

    bits 0-2 : round      (0xF8 | (8 - round))   -> R1=111 .. R6=010
    bit 3    : 0 => Boss subround
    bit 5    : 0 => Castle subround
    (bits 3 and 5 both set => Outside subround)
    bit 6    : 0 => invincible (the existing invincible variant; left SET here)

The MAME cheat "Select Starting Round/Sub-Round" (tools/mame/cheat/output.xml) writes
this same arcade byte.  This tool performs the Genesis-native equivalent: it looks up
the relocated Genesis ROM offset of arcade 0x05FF9F via the maintained address map and
patches that single byte on a COPY of the parent canonical ROM.  Nothing else changes,
so the variant shares the parent's build number and embedded crash-handler stamp and
initializes through the game's normal stage setup (no teleport, no new gameplay code).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ARCADE_SELECTOR_PC = 0x05FF9F        # low byte of the config word at arcade 0x05FF9E
DEFAULT_SELECTOR = 0xFF              # R1 Outside, not invincible (canonical default)
SUBROUNDS = {1: "Outside", 2: "Castle", 3: "Boss"}

# The Genesis stage decoder (translated arcade 0x04527E/0x04529C) reads its config
# operand as the UNRELOCATED literal 0x5FF9E/0x5FF9F -- `movew 0x5ff9e,d0` and
# `btst #3/#5,0x5ff9f`. (The startup/invincible decoder's operand WAS relocated, to
# 0x5FFE4, which is why the invincible variant patches 0x5FFE5 and why a naive address-
# map translation of 0x5FF9F -> 0x5FFE5 does NOT reach the stage decoder.)  So the byte
# the stage decoder actually reads is the literal Genesis offset 0x5FF9F, which is 0xFF
# padding on the canonical ROM.  We detect that read form in the ROM and patch there;
# if a future build relocates the operand, we fall back to the address-map location.
STAGE_DECODE_READ_OPCODES = (b"\x30\x39\x00\x05\xff\x9e", b"\x32\x39\x00\x05\xff\x9e")
LITERAL_READ_OFFSET = 0x0005FF9F


def selector_value(round_no: int, subround: int) -> int:
    """Packed selector byte for (round 1-6, subround 1=Outside/2=Castle/3=Boss)."""
    if not 1 <= round_no <= 6:
        raise ValueError(f"round must be 1-6, got {round_no}")
    if subround not in SUBROUNDS:
        raise ValueError(f"subround must be 1,2,3, got {subround}")
    value = 0xF8 | ((8 - round_no) & 0x07)   # bits 0-2 encode the round
    if subround == 2:                        # Castle: clear bit 5
        value &= ~0x20
    elif subround == 3:                      # Boss: clear bit 3
        value &= ~0x08
    return value & 0xFF


def genesis_offset(address_map: dict, arcade_pc: int) -> int:
    for seg in address_map["segments"]:
        if "arcade_start" not in seg:
            continue
        a0 = int(seg["arcade_start"], 0)
        a1 = int(seg["arcade_end_exclusive"], 0)
        g0 = int(seg["genesis_start"], 0)
        if a0 <= arcade_pc < a1:
            return g0 + (arcade_pc - a0)
    raise ValueError(f"arcade 0x{arcade_pc:05X} not found in address map segments")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path, help="parent canonical ROM")
    ap.add_argument("--address-map", required=True, type=Path)
    ap.add_argument("--round", required=True, type=int)
    ap.add_argument("--subround", required=True, type=int)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    value = selector_value(args.round, args.subround)
    amap = json.loads(args.address_map.read_text())
    relocated = genesis_offset(amap, ARCADE_SELECTOR_PC)   # address-map config location

    data = bytearray(args.rom.read_bytes())
    # Patch the byte the stage decoder actually reads.
    if any(op in bytes(data) for op in STAGE_DECODE_READ_OPCODES):
        off, read_form = LITERAL_READ_OFFSET, "unrelocated_stage_decode_operand"
    else:
        off, read_form = relocated, "relocated_config"
    if off >= len(data):
        raise SystemExit(f"selector offset 0x{off:06X} beyond ROM size {len(data)}")
    current = data[off]
    if current != DEFAULT_SELECTOR:
        raise SystemExit(
            f"parent ROM selector byte @0x{off:06X} is 0x{current:02X}, expected the "
            f"default 0x{DEFAULT_SELECTOR:02X}; refusing to patch a non-canonical parent")
    data[off] = value

    # Safety: only the selector byte may change. Round 1 Outside (0xFF) is the
    # canonical default, so that variant is legitimately byte-identical to the parent.
    parent = args.rom.read_bytes()
    changed = [i for i in range(len(parent)) if parent[i] != data[i]]
    expected = [] if value == DEFAULT_SELECTOR else [off]
    if changed != expected:
        raise SystemExit(f"expected changed bytes {expected or '[] (default)'} , got {changed}")

    args.output.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    print(json.dumps({
        "output": str(args.output),
        "round": args.round,
        "subround": args.subround,
        "subround_name": SUBROUNDS[args.subround],
        "arcade_selector_pc": f"0x{ARCADE_SELECTOR_PC:05X}",
        "genesis_offset": f"0x{off:06X}",
        "read_form": read_form,
        "address_map_relocated_offset": f"0x{relocated:06X}",
        "selector_value": f"0x{value:02X}",
        "sha256": sha,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
