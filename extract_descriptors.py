#!/usr/bin/env python3
"""Extract 12-byte descriptor table entries from maincpu.bin"""

import struct

with open("build/regions/maincpu.bin", "rb") as f:
    data = f.read()

def read_entry(offset):
    src, dest, cols, rows = struct.unpack_from(">IIhh", data, offset)
    return src, dest, cols, rows

def print_entry(offset, idx=None):
    src, dest, cols, rows = read_entry(offset)
    prefix = f"  Entry {idx}: " if idx is not None else "  "
    print(f"{prefix}src=0x{src:06X}  dest=0x{dest:06X}  cols={cols} (0x{cols:04X})  rows={rows} (0x{rows:04X})")
    return src, dest, cols, rows

def print_table(label, base, count):
    print(f"\n{label} (base=0x{base:05X}, {count} entries):")
    dests = []
    for i in range(count):
        s, d, c, r = print_entry(base + i * 12, i)
        dests.append(d)
    return dests

# Tables 1-5: single entry each
for i, (addr, label) in enumerate([
    (0x5816A, "Table 1 - call 1 at 0x5744E"),
    (0x58176, "Table 2 - call 2 at 0x5744E"),
    (0x58182, "Table 3 - call 3 at 0x5744E"),
    (0x5818E, "Table 4 - call 4 at 0x5744E"),
    (0x5819A, "Table 5 - 0x574A4"),
], start=1):
    print_table(f"Table {i}: {label}", addr, 1)

# Animation tables
for tbl_num, (addr, count, caller) in [
    (6, (0x581A6, 3, "0x57502 cycling 0-2")),
    (7, (0x581CA, 4, "0x57542 cycling 0-3")),
    (8, (0x581FA, 3, "0x57582 cycling 0-2")),
]:
    dests = print_table(f"Table {tbl_num}: animation for {caller}", addr, count)
    unique_dests = set(dests)
    if len(unique_dests) == 1:
        print(f"  => All {count} frames write to SAME dest_ptr 0x{dests[0]:06X} (confirmed overwrite)")
    else:
        print(f"  => DIFFERENT dest_ptrs: {[f'0x{d:06X}' for d in dests]}")

# Table 9: gameplay HUD
print_table("Table 9: gameplay HUD at 0x5635E (first 6 entries)", 0x5635E, 6)
