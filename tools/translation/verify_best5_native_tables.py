#!/usr/bin/env python3
"""Verify BEST-5 descriptor provenance, current reflow mapping, and consumers."""
import argparse, json
from pathlib import Path

def mapped(address_map, arcade_pc):
    for segment in address_map["segments"]:
        if "arcade_start" not in segment:
            continue
        lo = int(segment["arcade_start"], 0)
        hi = int(segment["arcade_end_exclusive"], 0)
        if lo <= arcade_pc < hi:
            return int(segment["genesis_start"], 0) + arcade_pc - lo
    raise SystemExit(f"no address-map segment for 0x{arcade_pc:06X}")

def main():
    parser = argparse.ArgumentParser()
    for name in ("maincpu", "rom", "address-map", "number-table", "name-table", "tilemap-source"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    maincpu = args.maincpu.read_bytes()
    rom = args.rom.read_bytes()
    address_map = json.loads(args.address_map.read_text())
    checks = ((0x03C37C, 130, args.number_table), (0x03C454, 48, args.name_table))
    resolved = []
    for arcade_pc, size, table in checks:
        expected = maincpu[arcade_pc:arcade_pc + size]
        if table.read_bytes() != expected:
            raise SystemExit(f"generated BEST-5 table mismatch at 0x{arcade_pc:06X}")
        runtime = mapped(address_map, arcade_pc)
        if rom[runtime:runtime + size] != expected:
            raise SystemExit(f"current mapped arcade table mismatch at 0x{runtime:06X}")
        resolved.append(runtime)
    source = args.tilemap_source.read_text()
    required = ("genesistan_number_descriptor_table", "genesistan_highscore_name_descriptor_table",
                "subi.l  #ARCADE_WORKRAM_A5_BASE", "cmpi.w  #6, (%a0)")
    if any(token not in source for token in required):
        raise SystemExit("BEST-5 source lacks semantic table/source-base/zero-suppression contract")
    if "#0x0003C57C" in source or "0x0003C654" in source:
        raise SystemExit("stale BEST-5 runtime table literal remains")
    print(f"BEST5_REFLOW_VERIFY_PASS number=0x{resolved[0]:06X} name=0x{resolved[1]:06X} A5_BASE=0x0010C000")

if __name__ == "__main__":
    main()
