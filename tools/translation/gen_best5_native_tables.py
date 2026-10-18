#!/usr/bin/env python3
"""Copy the two arcade BEST-5 descriptor tables into stable native symbols."""
import argparse, json
from pathlib import Path

NUMBER_START, NUMBER_SIZE = 0x03C37C, 130
NAME_START, NAME_SIZE = 0x03C454, 48

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--number-output", type=Path, required=True)
    parser.add_argument("--name-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    maincpu = args.maincpu.read_bytes()
    number = maincpu[NUMBER_START:NUMBER_START + NUMBER_SIZE]
    name = maincpu[NAME_START:NAME_START + NAME_SIZE]
    if len(number) != NUMBER_SIZE or len(name) != NAME_SIZE:
        raise SystemExit("maincpu is too short for BEST-5 descriptor tables")
    args.number_output.parent.mkdir(parents=True, exist_ok=True)
    args.number_output.write_bytes(number)
    args.name_output.write_bytes(name)
    args.report.write_text(json.dumps({
        "format": "rastan-best5-native-descriptors-v1",
        "number": {"arcade_pc": "0x03C37C", "bytes": NUMBER_SIZE},
        "name": {"arcade_pc": "0x03C454", "bytes": NAME_SIZE},
        "source_contract": "generated from authoritative original maincpu; addressed by linker symbols",
    }, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()
