# Cody — OPEN-016 Descriptor-Pointer Table Relocation Fix

**Date:** 2026-06-18
**Type:** Implementation + static verification
**Scope:** Relocate only the confirmed title glyph/string descriptor-pointer table instance for OPEN-016 / KF-028. No runtime probing. No bookmark cycle. No crash-handler fix. No broader embedded data-pointer table survey.

## Table Bounds

- Runtime Genesis table start: `0x03BD7C`
- Source/arcade table start used by spec: `0x03BB7C`
- Entry size: 4 bytes
- Confirmed entry count: 71
- Runtime Genesis table end inclusive: `0x03BE97`
- First byte after table: `0x03BE98`

Evidence: entries `0..70` are ROM-range descriptor pointers whose relocated targets begin with plausible even `0x00C0xxxx` destination longwords and `0x0000` attribute words. Address `0x03BE98` is not another table entry; it is descriptor data (`0x00C08F4C | 0x0000 | ...`). Therefore the 128-entry assumption was rejected.

## Implementation Mechanism

Added one `absolute_long_pointer_tables` entry to `specs/rastan_direct_remap.json`:

- `table_address`: `0x03BB7C`
- `entry_count`: `71`
- `entry_size_bytes`: `4`

The existing postpatch mechanism maps the source table to runtime Genesis `0x03BD7C` and relocates ROM-range longword targets by `+0x200`. ROM size and code size are unchanged.

## Static Verification

Patched ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
SHA256: `c9fab1b47ccd3dd7dff76dbd4fe8776521287697a9e6824917a1b7a10131b390`
Size: `1559280` bytes (unchanged)

| Index | Entry addr | Before | After | Descriptor first long | Attr |
|---:|---|---|---|---|---|
| 0 | `0x03BD7C` | `0x0003BC98` | `0x0003BE98` | `0x00C08F4C` | `0x0000` |
| 63 | `0x03BE78` | `0x0003C216` | `0x0003C416` | `0x00C08D4C` | `0x0000` |
| 64 | `0x03BE7C` | `0x0003C232` | `0x0003C432` | `0x00C08F4C` | `0x0000` |
| 65 | `0x03BE80` | `0x0003C246` | `0x0003C446` | `0x00C0914C` | `0x0000` |

Required acceptance check passed: `table[65]` at `0x03BE80` is now `0x0003C446`.

Descriptor `0x03C446` begins `00 C0 91 4C 00 00 "OTHERW..."`.

The stale fault path is broken: `table[65]` no longer points to `0x03C246`, so `0x50205741` (`"P WA"`) is no longer reachable as `descriptor[0]` through index 65.

## Build Verification

- Boot guard before postpatch: PASS
- Postpatch: PASS
- Boot guard after postpatch: PASS
- Canonical gate: PASS (`GATE_PASS`)
- `opcode_replace` count: unchanged at 94
- total covered bytes invariant: unchanged at `0x17CAF0`
- postpatch table relocation log: `entry_count=71`, `fixes=71`
- repeat postpatch determinism: PASS, byte-identical SHA `c9fab1b47ccd3dd7dff76dbd4fe8776521287697a9e6824917a1b7a10131b390`

## OPEN-016 Status

The confirmed immediate `0x03BD7C` table instance is fixed. OPEN-016 remains OPEN because the broader embedded absolute data-pointer table survey was explicitly out of scope and remains required.

## Runtime / Bookmark

- Runtime probing: NO
- Bookmark cycle: NO
