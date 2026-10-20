#!/usr/bin/env python3
"""Build the semantic GAME OVER / gameplay-HUD PC090OJ profile slice.

The historical filename is retained so existing build references remain stable.
Pixels are no longer forced to a hard-coded white index: each semantic family
uses its current Palette Composer ``index_map`` and line decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CELL_BYTES = 128
CODE_FIRST = 0x02A
CODE_LAST = 0x048
FAMILIES = {
    "object:hud.score_digits": tuple(range(0x02A, 0x034)),
    "object:attract.game_over": (0x037, 0x038, 0x03F, 0x040, 0x041, 0x042, 0x043, 0x044),
    "object:hud.p1_label": (0x039, 0x046, 0x048),
}


def transform(cell: bytes, index_map: dict[int, int]) -> bytes:
    out = bytearray()
    for value in cell:
        hi = (value >> 4) & 0x0F
        lo = value & 0x0F
        out.append(
            ((index_map.get(hi, hi) if hi else 0) << 4)
            | (index_map.get(lo, lo) if lo else 0)
        )
    return bytes(out)


def build_slice(data: bytes, profile: dict) -> tuple[bytes, dict]:
    if len(data) % CELL_BYTES:
        raise ValueError(f"input size {len(data)} is not a multiple of {CELL_BYTES}")
    if len(data) // CELL_BYTES <= CODE_LAST:
        raise ValueError(f"input has too few cells; need code 0x{CODE_LAST:03X}")

    mappings = profile.get("usage_palette_mappings", {})
    code_owner: dict[int, str] = {}
    resolved = {}
    for uid, codes in FAMILIES.items():
        mapping = mappings.get(uid)
        if not mapping:
            raise ValueError(f"current Test profile lacks required semantic mapping {uid}")
        line = int(mapping["line"])
        if not 0 <= line <= 3:
            raise ValueError(f"{uid} has invalid Genesis line {line}")
        index_map = {int(src): int(dst) for src, dst in mapping.get("index_map", {}).items()}
        if not index_map:
            raise ValueError(f"current Test profile has empty index_map for {uid}")
        for src, dst in index_map.items():
            if not 1 <= src <= 15 or not 1 <= dst <= 15:
                raise ValueError(f"{uid} has invalid nontransparent mapping {src}->{dst}")
        for code in codes:
            if code in code_owner:
                raise ValueError(f"semantic code 0x{code:03X} has two owners")
            code_owner[code] = uid
        resolved[uid] = {
            "line": line,
            "index_map": {str(src): dst for src, dst in sorted(index_map.items())},
            "codes": [f"0x{code:03X}" for code in codes],
        }

    out = bytearray()
    for code in range(CODE_FIRST, CODE_LAST + 1):
        start = code * CELL_BYTES
        cell = data[start:start + CELL_BYTES]
        uid = code_owner.get(code)
        if uid is None:
            out.extend(cell)
        else:
            mapping = {int(src): int(dst) for src, dst in resolved[uid]["index_map"].items()}
            out.extend(transform(cell, mapping))
    return bytes(out), resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    profile_bytes = args.profile.read_bytes()
    profile = json.loads(profile_bytes)
    source = args.input.read_bytes()
    output, families = build_slice(source, profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {
        "schema": "pc090oj-semantic-profile-slice/v1",
        "profile": str(args.profile.resolve()),
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "source": str(args.input.resolve()),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "output": str(args.output.resolve()),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "code_range": [f"0x{CODE_FIRST:03X}", f"0x{CODE_LAST:03X}"],
        "families": families,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"semantic PC090OJ profile slice: {len(output)} bytes; "
        f"profile_sha={report['profile_sha256']} asset_sha={report['output_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
