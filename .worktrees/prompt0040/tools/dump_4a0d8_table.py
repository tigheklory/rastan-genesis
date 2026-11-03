#!/usr/bin/env python3
"""Dump the 0x4a0d8 stage/family spawn table from the Rastan maincpu ROM."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build" / "regions" / "maincpu.bin"
OUT = ROOT / "build" / "4a0d8_table.txt"


def main() -> int:
    if not ROM.exists():
        raise SystemExit(f"missing ROM region: {ROM}")

    data = ROM.read_bytes()
    base = 0x4A104
    record_size = 8
    stage_count = 8
    family_count = 5

    lines: list[str] = []
    lines.append(f"source: {ROM}")
    lines.append("record format: field4 state3e family/alt54 field36 field1c field34")
    lines.append("")

    for stage_index in range(stage_count):
        lines.append(f"stage_row {stage_index}")
        for family in range(family_count):
            offset = base + (stage_index * family_count + family) * record_size
            rec = data[offset : offset + record_size]
            field4 = rec[0]
            state3e = rec[1]
            packed = rec[2]
            field36 = rec[3]
            field1c = (rec[4] << 8) | rec[5]
            field34 = (rec[6] << 8) | rec[7]
            family_sel = packed & 0x0F
            alt_sel = packed >> 4
            lines.append(
                f"  family {family}: "
                f"f4={field4:02x} s3e={state3e:02x} "
                f"fam={family_sel:x} alt={alt_sel:x} "
                f"f36={field36:02x} f1c={field1c:04x} f34={field34:04x}"
            )
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
