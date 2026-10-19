#!/usr/bin/env python3
"""Verify BEST-5 arcade provenance and generated A5-relative consumers."""
import argparse
import json
import struct
from pathlib import Path


NUMBER_START, NUMBER_SIZE = 0x03C37C, 130
NAME_START, NAME_SIZE = 0x03C454, 48
ARCADE_A5_BASE = 0x0010C000
MAX_SIGNED_WORD_DISPLACEMENT = 0x7FFF


def mapped(address_map, arcade_pc):
    for segment in address_map["segments"]:
        if "arcade_start" not in segment:
            continue
        lo = int(segment["arcade_start"], 0)
        hi = int(segment["arcade_end_exclusive"], 0)
        if lo <= arcade_pc < hi:
            return int(segment["genesis_start"], 0) + arcade_pc - lo
    raise SystemExit(f"no address-map segment for 0x{arcade_pc:06X}")


def read_symbols(path):
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                result[fields[-1]] = int(fields[0], 16)
            except ValueError:
                pass
    return result


def expected_number_table(raw):
    if len(raw) != NUMBER_SIZE or len(raw) % 10:
        raise SystemExit("invalid authoritative BEST-5 numeric table size")
    output = bytearray()
    displacements = []
    for offset in range(0, len(raw), 10):
        count, destination, source = struct.unpack_from(">HII", raw, offset)
        if not ARCADE_A5_BASE <= source <= ARCADE_A5_BASE + MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(f"numeric source outside A5 domain: 0x{source:08X}")
        displacement = source - ARCADE_A5_BASE
        if not 0 <= displacement <= MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(f"numeric displacement does not fit positive ADDA.W: 0x{displacement:X}")
        output.extend(struct.pack(">HIH", count, destination, displacement))
        displacements.append(displacement)
    return bytes(output), displacements


def expected_name_table(raw):
    if len(raw) != NAME_SIZE or len(raw) % 6:
        raise SystemExit("invalid authoritative BEST-5 name table size")
    displacements = []
    for offset in range(0, len(raw), 6):
        _count, _destination, displacement = struct.unpack_from(">HHH", raw, offset)
        if displacement > MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(f"name displacement does not fit positive ADDA.W: 0x{displacement:04X}")
        semantic_source = ARCADE_A5_BASE + displacement
        if not ARCADE_A5_BASE <= semantic_source <= ARCADE_A5_BASE + MAX_SIGNED_WORD_DISPLACEMENT:
            raise SystemExit(f"name source outside A5 domain: 0x{semantic_source:08X}")
        displacements.append(displacement)
    return raw, displacements


def function_body(source, label, next_label):
    try:
        return source[source.index(label):source.index(next_label, source.index(label) + len(label))]
    except ValueError as error:
        raise SystemExit(f"cannot isolate BEST-5 consumer {label}") from error


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "maincpu", "rom", "address-map", "symbols", "number-table", "name-table", "tilemap-source"
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()

    maincpu = args.maincpu.read_bytes()
    rom = args.rom.read_bytes()
    address_map = json.loads(args.address_map.read_text())
    symbols = read_symbols(args.symbols)
    source = args.tilemap_source.read_text()

    number_raw = maincpu[NUMBER_START:NUMBER_START + NUMBER_SIZE]
    name_raw = maincpu[NAME_START:NAME_START + NAME_SIZE]
    expected_number, number_displacements = expected_number_table(number_raw)
    expected_name, name_displacements = expected_name_table(name_raw)
    if args.number_table.read_bytes() != expected_number:
        raise SystemExit("generated BEST-5 numeric table is not the authoritative A5-relative conversion")
    if args.name_table.read_bytes() != expected_name:
        raise SystemExit("generated BEST-5 name table does not preserve the authoritative relative records")

    number_runtime = mapped(address_map, NUMBER_START)
    name_runtime = mapped(address_map, NAME_START)
    if rom[number_runtime:number_runtime + NUMBER_SIZE] != number_raw:
        raise SystemExit(f"mapped original numeric authority mismatch at 0x{number_runtime:06X}")
    if rom[name_runtime:name_runtime + NAME_SIZE] != name_raw:
        raise SystemExit(f"mapped original name authority mismatch at 0x{name_runtime:06X}")

    generated_symbols = {
        "genesistan_number_descriptor_table": expected_number,
        "genesistan_highscore_name_descriptor_table": expected_name,
    }
    for symbol, expected in generated_symbols.items():
        if symbol not in symbols:
            raise SystemExit(f"missing linker symbol: {symbol}")
        address = symbols[symbol]
        if rom[address:address + len(expected)] != expected:
            raise SystemExit(f"final ROM generated-table mismatch at {symbol}=0x{address:06X}")

    numeric_body = function_body(
        source, "genesistan_hook_number_renderer_3c2e2:", "genesistan_hook_glyph_renderer_3bd48:"
    )
    name_body = function_body(
        source, "genesistan_hook_highscore_fg_producer:", "genesistan_hook_tilemap_bg_blockcopy:"
    )
    required_numeric = (
        "genesistan_number_descriptor_table",
        "lsl.w   #3, %d6",
        "movea.l %a5, %a4",
        "adda.w  6(%a0), %a4",
        "cmpi.w  #6, (%a0)",
    )
    required_name = (
        "genesistan_highscore_name_descriptor_table",
        "movea.l %a5, %a2",
        "adda.w  4(%a0), %a2",
    )
    if any(token not in numeric_body for token in required_numeric):
        raise SystemExit("numeric BEST-5 consumer lacks linker/A5-relative/zero-suppression contract")
    if any(token not in name_body for token in required_name):
        raise SystemExit("name BEST-5 consumer lacks linker/A5-relative contract")
    forbidden_runtime = (
        "ARCADE_WORKRAM_A5_BASE",
        "ARCADE_HIGHSCORE_SOURCE_BASE",
        "subi.l  #0x0010C000",
        "adda.l  #0x00FF0000",
    )
    if any(token in numeric_body or token in name_body for token in forbidden_runtime):
        raise SystemExit("BEST-5 consumer retains runtime source conversion or a magic WRAM source")
    if "#0x0003C57C" in source or "0x0003C654" in source:
        raise SystemExit("stale BEST-5 runtime table literal remains")

    factory_oracle_literals = (
        "273100", "257200", "197800", "125400", "112000", "COB", "THS", "YAG", "TKG", "YTN"
    )
    if any(token in source for token in factory_oracle_literals):
        raise SystemExit("factory ranking oracle leaked into production tilemap source")

    all_displacements = number_displacements + name_displacements
    print(
        "BEST5_SOURCE_CONVERSION_VERIFY_PASS "
        f"original_number=0x{number_runtime:06X} original_name=0x{name_runtime:06X} "
        f"generated_number=0x{symbols['genesistan_number_descriptor_table']:06X} "
        f"generated_name=0x{symbols['genesistan_highscore_name_descriptor_table']:06X} "
        f"number_entries={len(number_displacements)} name_entries={len(name_displacements)} "
        f"range=0x{min(all_displacements):04X}-0x{max(all_displacements):04X}"
    )


if __name__ == "__main__":
    main()
