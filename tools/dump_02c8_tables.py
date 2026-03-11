#!/usr/bin/env python3
"""Dump key 0x02c8 actor tables from the Rastan maincpu ROM."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build" / "regions" / "maincpu.bin"
OUT = ROOT / "build" / "02c8_tables.txt"


def read_bytes(offset: int, size: int) -> bytes:
    data = ROM.read_bytes()
    return data[offset : offset + size]


def fmt_hex(values: bytes) -> str:
    return " ".join(f"{value:02x}" for value in values)


def dump_table_41cfa(lines: list[str]) -> None:
    base = 0x41D26
    table = read_bytes(base, 17 * 8)
    lines.append("41cfa state records")
    lines.append("state : b8 b13 b14 b15 b16 b17 b19 b2")
    for state in range(17):
        record = table[state * 8 : (state + 1) * 8]
        lines.append(f"{state:2d}: {fmt_hex(record)}")
    lines.append("")


def dump_table_46f1e(lines: list[str]) -> None:
    base = 0x46F3C
    table = read_bytes(base, 16 * 8)
    lines.append("46f1e class records")
    lines.append("class: b8 b13 b14 b15 b16 b17 b19 b2")
    for cls in range(1, 17):
        record = table[(cls - 1) * 8 : cls * 8]
        lines.append(f"{cls:2d}: {fmt_hex(record)}")
    lines.append("")


def dump_stage_class_table(lines: list[str]) -> None:
    base = 0x444E0
    table = read_bytes(base, 6)
    lines.append("444e0 stage -> class seed table")
    lines.append("stage: class")
    for stage_index, actor_class in enumerate(table, start=1):
        lines.append(f"{stage_index:2d}: {actor_class:02x}")
    lines.append("")


def main() -> int:
    if not ROM.exists():
        raise SystemExit(f"missing ROM region: {ROM}")

    lines: list[str] = []
    lines.append(f"source: {ROM}")
    lines.append("")
    dump_table_41cfa(lines)
    dump_table_46f1e(lines)
    dump_stage_class_table(lines)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
