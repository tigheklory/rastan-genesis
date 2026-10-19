#!/usr/bin/env python3
"""Generate linker-owned BEST-5 descriptors from the original arcade tables."""
import argparse
import json
import struct
from pathlib import Path

NUMBER_START, NUMBER_SIZE = 0x03C37C, 130
NAME_START, NAME_SIZE = 0x03C454, 48
ARCADE_A5_BASE = 0x0010C000
MAX_SIGNED_WORD_DISPLACEMENT = 0x7FFF


def number_descriptors(raw):
    """Convert [count.w,dest.l,source.l] to [count.w,dest.l,a5_disp.w]."""
    if len(raw) % 10:
        raise SystemExit("BEST-5 numeric descriptor table is not a whole number of records")
    output = bytearray()
    report = []
    for index in range(0, len(raw), 10):
        count, destination, source = struct.unpack_from(">HII", raw, index)
        if not ARCADE_A5_BASE <= source <= ARCADE_A5_BASE + MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(
                f"BEST-5 numeric source 0x{source:08X} is outside the positive signed-word A5 domain"
            )
        displacement = source - ARCADE_A5_BASE
        output.extend(struct.pack(">HIH", count, destination, displacement))
        report.append({
            "count": count,
            "destination": f"0x{destination:08X}",
            "generated_a5_displacement": f"0x{displacement:04X}",
            "index": index // 10,
            "original_source": f"0x{source:08X}",
        })
    return bytes(output), report


def name_descriptors(raw):
    """Validate existing [count.w,dest.w,a5_disp.w] name records."""
    if len(raw) % 6:
        raise SystemExit("BEST-5 name descriptor table is not a whole number of records")
    report = []
    for index in range(0, len(raw), 6):
        count, destination, displacement = struct.unpack_from(">HHH", raw, index)
        if displacement > MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(
                f"BEST-5 name source displacement 0x{displacement:04X} does not fit positive ADDA.W"
            )
        report.append({
            "count": count,
            "destination": f"0x{destination:04X}",
            "generated_a5_displacement": f"0x{displacement:04X}",
            "index": index // 6,
            "original_semantic_source": f"0x{ARCADE_A5_BASE + displacement:08X}",
        })
    return raw, report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--number-output", type=Path, required=True)
    parser.add_argument("--name-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    maincpu = args.maincpu.read_bytes()
    number_raw = maincpu[NUMBER_START:NUMBER_START + NUMBER_SIZE]
    name_raw = maincpu[NAME_START:NAME_START + NAME_SIZE]
    if len(number_raw) != NUMBER_SIZE or len(name_raw) != NAME_SIZE:
        raise SystemExit("maincpu is too short for BEST-5 descriptor tables")
    number, number_report = number_descriptors(number_raw)
    name, name_report = name_descriptors(name_raw)
    args.number_output.parent.mkdir(parents=True, exist_ok=True)
    args.number_output.write_bytes(number)
    args.name_output.write_bytes(name)
    args.report.write_text(json.dumps({
        "arcade_a5_base": f"0x{ARCADE_A5_BASE:08X}",
        "format": "rastan-best5-native-descriptors-v2",
        "name": {
            "arcade_bytes": NAME_SIZE,
            "arcade_pc": "0x03C454",
            "entries": name_report,
            "generated_bytes": len(name),
            "record_format": "count.w,destination.w,a5_displacement.w",
        },
        "number": {
            "arcade_bytes": NUMBER_SIZE,
            "arcade_pc": "0x03C37C",
            "entries": number_report,
            "generated_bytes": len(number),
            "record_format": "count.w,destination.l,a5_displacement.w",
        },
        "source_contract": (
            "generated from authoritative original maincpu; live sources are positive signed-word "
            "A5-relative displacements; ROM tables are addressed only by linker symbols"
        ),
    }, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()
