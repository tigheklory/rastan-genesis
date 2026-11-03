#!/usr/bin/env python3
"""Print a stable address-based slice from build/maincpu.disasm.txt."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DISASM = Path("build/maincpu.disasm.txt")
ADDR_RE = re.compile(r"^\s*([0-9a-f]+):")


def parse_addr(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a disassembly slice by address.")
    parser.add_argument("start", type=parse_addr, help="start address, e.g. 0x42838")
    parser.add_argument("end", type=parse_addr, nargs="?", help="end address, inclusive")
    parser.add_argument("--before", type=int, default=0, help="extra lines before the start match")
    parser.add_argument("--after", type=int, default=0, help="extra lines after the end match")
    args = parser.parse_args()

    lines = DISASM.read_text().splitlines()
    indexed: list[tuple[int, str]] = []
    for line in lines:
        match = ADDR_RE.match(line)
        if match:
            indexed.append((int(match.group(1), 16), line))

    if not indexed:
        raise SystemExit("No address lines found in build/maincpu.disasm.txt")

    end_addr = args.end if args.end is not None else args.start
    start_idx = None
    end_idx = None
    for idx, (addr, _) in enumerate(indexed):
        if start_idx is None and addr >= args.start:
            start_idx = idx
        if addr <= end_addr:
            end_idx = idx
        if addr > end_addr and end_idx is not None:
            break

    if start_idx is None:
        raise SystemExit(f"Start address 0x{args.start:x} not found")
    if end_idx is None:
        end_idx = len(indexed) - 1

    start_idx = max(0, start_idx - args.before)
    end_idx = min(len(indexed) - 1, end_idx + args.after)

    for _, line in indexed[start_idx : end_idx + 1]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
