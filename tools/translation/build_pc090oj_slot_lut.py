#!/usr/bin/env python3
"""Generate deterministic 256-byte PC090OJ index -> SAT slot LUT.

Spec authority: docs/design/Andy_pc090oj_implementation_spec.md §1.3.1.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MAPPINGS = [
    # (pc090oj_idx_start, sat_slot_start, count)
    (17, 22, 8),
    (9, 30, 14),
    (0, 44, 12),
    (46, 56, 8),
    (0, 72, 4),
    (239, 76, 4),
]


def build_lut() -> bytes:
    lut = bytearray([0xFF] * 256)
    for idx_start, slot_start, count in MAPPINGS:
        for i in range(count):
            idx = idx_start + i
            if idx >= len(lut):
                continue
            if lut[idx] == 0xFF:  # first-row-wins precedence
                lut[idx] = slot_start + i
    return bytes(lut)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        required=True,
        help="Output LUT path (256-byte binary)",
    )
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lut = build_lut()
    out_path.write_bytes(lut)

    if len(lut) != 256:
        raise RuntimeError(f"Expected 256-byte LUT, got {len(lut)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
