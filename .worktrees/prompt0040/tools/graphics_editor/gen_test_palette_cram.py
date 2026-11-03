#!/usr/bin/env python3
"""Generate the static gameplay Test-profile CRAM lines consumed by production.

The gameplay palette owner installs Palette Composer lines 0, 1, and 3 at the
scene semantic boundary. Line 2 remains arcade-controlled Plane-B state. Entry
zero is normalized to transparent black because sprite/tile pixel index zero is
transparent and Genesis CRAM color zero is also the backdrop color.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


LINES = (0, 1, 3)
WORDS_PER_LINE = 16


def parse_word(value: object, line: int, index: int) -> int:
    if index == 0:
        return 0
    if value is None:
        raise ValueError(f"Test profile line {line} entry {index} is unassigned")
    word = int(str(value), 16)
    if word & ~0x0EEE:
        raise ValueError(f"Test profile line {line} entry {index} is not legal Genesis CRAM: {value}")
    return word


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--line0-output", type=Path, required=True)
    parser.add_argument("--line1-output", type=Path, required=True)
    parser.add_argument("--line3-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    profile_bytes = args.profile.read_bytes()
    profile = json.loads(profile_bytes)
    target = profile.get("target_palette_lines")
    if not isinstance(target, list) or len(target) != 4:
        raise SystemExit("Test profile must contain four target_palette_lines")

    words: dict[int, list[int]] = {}
    outputs = {
        0: args.line0_output,
        1: args.line1_output,
        3: args.line3_output,
    }
    payloads: dict[int, bytes] = {}
    for line in LINES:
        if len(target[line]) != WORDS_PER_LINE:
            raise SystemExit(f"Test profile line {line} must contain 16 entries")
        words[line] = [parse_word(value, line, index) for index, value in enumerate(target[line])]
        payloads[line] = b"".join(word.to_bytes(2, "big") for word in words[line])

    for line, output in outputs.items():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payloads[line])
    report = {
        "schema": "rastan-test-palette-cram/v1",
        "profile": str(args.profile.resolve()),
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "outputs": {
            str(line): {
                "path": str(outputs[line].resolve()),
                "sha256": hashlib.sha256(payloads[line]).hexdigest(),
                "bytes": len(payloads[line]),
            }
            for line in LINES
        },
        "line_order": list(LINES),
        "words_per_line": WORDS_PER_LINE,
        "transparent_entry_zero": "normalized to 0x0000; source index 0 is transparent",
        "lines": {str(line): [f"0x{word:04X}" for word in words[line]] for line in LINES},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"Test CRAM lines 0/1/3: profile_sha={report['profile_sha256']} "
        + " ".join(
            f"line{line}_sha={report['outputs'][str(line)]['sha256']}"
            for line in LINES
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
