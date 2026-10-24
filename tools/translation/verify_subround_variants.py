#!/usr/bin/env python3
"""RG-018 validation: starting-subround test ROM variants.

Checks (maintained, deterministic):
  1. Selector values match the MAME cheat parameter items exactly.
  2. The arcade->Genesis mapping for the selector byte resolves via the address map.
  3. Every selected variant patches exactly that one byte with the correct value.
  4. No variant modifies the canonical ROM anywhere else.
  5. All 18 variants are present (when --require-all).
  6. Variant names carry the parent build number and the _SR-S suffix.
  7. Invalid round/subround inputs are rejected by the generator.
  8. Patching is deterministic (pure selector function).
Stage playability itself is NOT asserted here (Tighe validates in BlastEm/hardware).
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_subround_variant import (  # noqa: E402
    ARCADE_SELECTOR_PC, DEFAULT_SELECTOR, LITERAL_READ_OFFSET, STAGE_DECODE_READ_OPCODES,
    SUBROUNDS, genesis_offset, selector_value,
)

LABEL_RE = re.compile(r"Round\s+(\d)(?:\s+(Castle|Boss))?\s*$", re.I)
SUB_FROM_LABEL = {None: 1, "castle": 2, "boss": 3}


def cheat_values(xml_path: Path) -> dict[tuple[int, int], int]:
    root = ET.parse(xml_path).getroot()
    for cheat in root.iter("cheat"):
        if (cheat.get("desc") or "").startswith("Select Starting Round"):
            out = {}
            for item in cheat.iter("item"):
                m = LABEL_RE.match((item.text or "").strip())
                if not m:
                    raise ValueError(f"unparsable cheat item label: {item.text!r}")
                rnd = int(m.group(1))
                sub = SUB_FROM_LABEL[(m.group(2) or "").lower() or None]
                out[(rnd, sub)] = int(item.get("value"), 0)
            return out
    raise ValueError("Select Starting Round/Sub-Round cheat not found")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True, type=Path)
    ap.add_argument("--address-map", required=True, type=Path)
    ap.add_argument("--cheat-xml", required=True, type=Path)
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True, help="e.g. rastan_direct_video_test_build_0494")
    ap.add_argument("--require-all", action="store_true")
    args = ap.parse_args()

    import json
    amap = json.loads(args.address_map.read_text())
    relocated = genesis_offset(amap, ARCADE_SELECTOR_PC)
    canon = args.canonical.read_bytes()
    # The stage decoder reads the unrelocated literal operand; patch there.
    off = LITERAL_READ_OFFSET if any(op in canon for op in STAGE_DECODE_READ_OPCODES) else relocated
    fails: list[str] = []

    def ck(name: str, cond: bool, extra: str = "") -> None:
        print(("PASS " if cond else "FAIL ") + name + (("  -> " + extra) if extra and not cond else ""))
        if not cond:
            fails.append(name)

    ck("canonical selector byte is the default 0xFF",
       off < len(canon) and canon[off] == DEFAULT_SELECTOR, f"0x{canon[off]:02X} @0x{off:06X}")

    # 1 + 8: selector values match the cheat and the pure derivation
    cheat = cheat_values(args.cheat_xml)
    ck("cheat exposes all 18 round/subround selectors", len(cheat) == 18, str(len(cheat)))
    for (rnd, sub), val in sorted(cheat.items()):
        ck(f"selector R{rnd}-{sub} ({SUBROUNDS[sub]}) == cheat 0x{val:02X}",
           selector_value(rnd, sub) == val, f"derived 0x{selector_value(rnd, sub):02X}")

    # 7: invalid inputs rejected
    bad = 0
    for r, s in ((0, 1), (7, 1), (1, 0), (1, 4)):
        try:
            selector_value(r, s)
        except ValueError:
            bad += 1
    ck("invalid round/subround inputs rejected", bad == 4, f"{bad}/4")

    # 3 + 4 + 6: each present variant patches exactly the one byte, named correctly
    present = 0
    for rnd in range(1, 7):
        for sub in range(1, 4):
            name = f"{args.prefix}_S{rnd}-{sub}.bin"
            path = args.dist_dir / name
            if not path.exists():
                if args.require_all:
                    ck(f"variant present: {name}", False, "missing")
                continue
            present += 1
            data = path.read_bytes()
            same_len = len(data) == len(canon)
            diffs = [i for i in range(min(len(data), len(canon))) if data[i] != canon[i]] if same_len else [-1]
            want = selector_value(rnd, sub)
            # Round 1 Outside (0xFF) is the canonical default -> byte-identical variant.
            expected_diffs = [] if want == DEFAULT_SELECTOR else [off]
            ck(f"{name}: only the selector byte at 0x{off:06X} is 0x{want:02X}",
               same_len and diffs == expected_diffs and data[off] == want,
               f"len_eq={same_len} diffs={[hex(d) for d in diffs[:4]]}")

    if args.require_all:
        ck("all 18 variants generated", present == 18, f"{present}/18")

    print(f"\n{'ALL SUBROUND-VARIANT CHECKS PASS' if not fails else str(len(fails)) + ' CHECK(S) FAILED'}"
          f"  (selector byte @ genesis 0x{off:06X} = arcade 0x{ARCADE_SELECTOR_PC:05X})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
