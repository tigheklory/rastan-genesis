#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAINCPU = ROOT / "build" / "regions" / "maincpu.bin"


def read_u16be(blob: bytes, offset: int) -> int:
    return (blob[offset] << 8) | blob[offset + 1]


def dump_state_table(blob: bytes, base: int, count: int, label: str, start_index: int = 0) -> list[str]:
    lines = [f"{label} @ 0x{base:05x}"]
    for index in range(count):
        entry = base + index * 8
        tile_base = read_u16be(blob, entry)
        anim_len = blob[entry + 2]
        frame = blob[entry + 3]
        xoff = read_u16be(blob, entry + 4)
        yoff = read_u16be(blob, entry + 6)
        lines.append(
            f"  state {start_index + index:2d}: "
            f"tile_base=0x{tile_base:04x} anim_len=0x{anim_len:02x} "
            f"frame=0x{frame:02x} xoff=0x{xoff:04x} yoff=0x{yoff:04x}"
        )
    return lines


def dump_palette_table(blob: bytes, base: int, players: int, states_per_player: int, label: str) -> list[str]:
    lines = [f"{label} @ 0x{base:05x}"]
    for player in range(players):
        start = base + player * states_per_player
        values = " ".join(f"{blob[start + i]:02x}" for i in range(states_per_player))
        lines.append(f"  player {player + 1}: {values}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump Rastan animation/palette tables used by 0x4543e / 0x45684")
    parser.add_argument(
        "--maincpu",
        type=Path,
        default=MAINCPU,
        help="Path to interleaved maincpu.bin",
    )
    args = parser.parse_args()

    blob = args.maincpu.read_bytes()

    sections: list[list[str]] = []
    sections.append(dump_state_table(blob, 0x454BA, 3, "state 0x3e table, family selector 0"))
    sections.append(dump_state_table(blob, 0x454D2, 3, "state 0x3e table, family selector 1/3"))
    sections.append(dump_state_table(blob, 0x454EA, 3, "state 0x3e table, family selector 2+"))
    sections.append(dump_state_table(blob, 0x45502, 12, "state table for states 8..19", start_index=8))
    sections.append(dump_state_table(blob, 0x45562, 11, "alternate state table for states 8..18", start_index=8))
    sections.append(dump_palette_table(blob, 0x456EC, 6, 18, "family-2 palette/attribute table"))
    sections.append(dump_palette_table(blob, 0x45722, 6, 12, "default palette/attribute table"))
    sections.append(dump_palette_table(blob, 0x4576A, 6, 12, "alternate palette/attribute table"))

    for idx, section in enumerate(sections):
        if idx:
            print()
        print("\n".join(section))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
