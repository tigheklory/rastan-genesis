#!/usr/bin/env python3
"""Hard guard for rastan-direct bootstrap/layout bytes."""

from __future__ import annotations

import argparse
from pathlib import Path


EXPECTED_RESET_VECTOR_OFFSET = 0x000004
EXPECTED_RESET_VECTOR = 0x00000202
EXPECTED_SP_VECTOR_OFFSET = 0x000000
EXPECTED_SP_VECTOR = 0x00FF0000
EXPECTED_DEFAULT_HANDLER_OFFSET = 0x000200
EXPECTED_DEFAULT_HANDLER = bytes.fromhex("4E73")  # RTE
EXPECTED_START_PROLOGUE_OFFSET = 0x000202
EXPECTED_START_PROLOGUE = bytes.fromhex("46FC27004FF900FF0000")
EXPECTED_VINT_VECTOR_OFFSET = 0x000078
EXPECTED_WRAPPER_LOW_BOUND = 0x00070000
EXPECTED_WRAPPER_HIGH_BOUND = 0x00080000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify rastan-direct low bootstrap bytes and high-wrapper VBlank vector."
    )
    parser.add_argument("--rom", required=True, help="Fresh prepatch ROM binary path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rom_path = Path(args.rom)
    rom_bytes = rom_path.read_bytes()

    min_required = EXPECTED_START_PROLOGUE_OFFSET + len(EXPECTED_START_PROLOGUE)
    if len(rom_bytes) < min_required:
        raise RuntimeError(
            f"{rom_path} is too small for bootstrap guard checks."
        )

    sp_vector = int.from_bytes(
        rom_bytes[EXPECTED_SP_VECTOR_OFFSET:EXPECTED_SP_VECTOR_OFFSET + 4], "big"
    )
    if sp_vector != EXPECTED_SP_VECTOR:
        raise RuntimeError(
            "rastan-direct boot guard FAIL: invalid initial SP vector: "
            f"0x{sp_vector:08X}, expected 0x{EXPECTED_SP_VECTOR:08X}."
        )

    reset_vector = int.from_bytes(
        rom_bytes[EXPECTED_RESET_VECTOR_OFFSET:EXPECTED_RESET_VECTOR_OFFSET + 4], "big"
    )
    if reset_vector != EXPECTED_RESET_VECTOR:
        raise RuntimeError(
            "rastan-direct boot guard FAIL: invalid reset vector: "
            f"0x{reset_vector:08X}, expected 0x{EXPECTED_RESET_VECTOR:08X}."
        )

    default_handler = rom_bytes[
        EXPECTED_DEFAULT_HANDLER_OFFSET:EXPECTED_DEFAULT_HANDLER_OFFSET + len(EXPECTED_DEFAULT_HANDLER)
    ]
    if default_handler != EXPECTED_DEFAULT_HANDLER:
        raise RuntimeError(
            "rastan-direct boot guard FAIL: invalid _default_handler bytes at "
            f"0x{EXPECTED_DEFAULT_HANDLER_OFFSET:06X}: {default_handler.hex().upper()}, "
            f"expected {EXPECTED_DEFAULT_HANDLER.hex().upper()}."
        )

    start_prologue = rom_bytes[
        EXPECTED_START_PROLOGUE_OFFSET:EXPECTED_START_PROLOGUE_OFFSET + len(EXPECTED_START_PROLOGUE)
    ]
    if start_prologue != EXPECTED_START_PROLOGUE:
        raise RuntimeError(
            "rastan-direct boot guard FAIL: invalid _start prologue at "
            f"0x{EXPECTED_START_PROLOGUE_OFFSET:06X}: {start_prologue.hex().upper()}, "
            f"expected {EXPECTED_START_PROLOGUE.hex().upper()}."
        )

    vint_vector = int.from_bytes(
        rom_bytes[EXPECTED_VINT_VECTOR_OFFSET:EXPECTED_VINT_VECTOR_OFFSET + 4], "big"
    )
    if not (EXPECTED_WRAPPER_LOW_BOUND <= vint_vector < EXPECTED_WRAPPER_HIGH_BOUND):
        raise RuntimeError(
            "rastan-direct boot guard FAIL: VBlank vector not in high wrapper region: "
            f"0x{vint_vector:08X}, expected in "
            f"[0x{EXPECTED_WRAPPER_LOW_BOUND:08X}, 0x{EXPECTED_WRAPPER_HIGH_BOUND:08X})."
        )

    print(
        "rastan-direct boot guard PASS: "
        f"SP=0x{sp_vector:08X} RESET=0x{reset_vector:08X} "
        f"VINT=0x{vint_vector:08X} "
        f"_default_handler={default_handler.hex().upper()} "
        f"_start_prologue={start_prologue.hex().upper()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
