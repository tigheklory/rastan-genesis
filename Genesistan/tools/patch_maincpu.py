#!/usr/bin/env python3
"""Static patch scaffold for the Rastan main 68000 program.

This is intentionally conservative. The immediate purpose is to establish the
compile-time translation pipeline location, output contract, and manifest shape
before any destructive opcode rewriting starts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PATCH_CLASSES = (
    "absolute_ram",
    "mmio",
    "control_flow",
    "pointer_table",
    "asset_side",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch Rastan maincpu for Genesistan.")
    parser.add_argument(
        "--input",
        default="build/regions/maincpu.bin",
        help="Path to the extracted arcade maincpu binary.",
    )
    parser.add_argument(
        "--output",
        default="build/genesistan/maincpu_patched.bin",
        help="Path to the patched output blob.",
    )
    parser.add_argument(
        "--manifest",
        default="build/genesistan/maincpu_patch_manifest.json",
        help="Path to the emitted patch manifest.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)

    data = input_path.read_bytes()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Placeholder behavior for the scaffold:
    # emit an unchanged copy plus a manifest proving the pipeline ran.
    output_path.write_bytes(data)

    manifest = {
        "input": str(input_path),
        "output": str(output_path),
        "input_size": len(data),
        "patches": [],
        "patch_classes": list(PATCH_CLASSES),
        "execution_goal": "Run patched original Rastan maincpu code on Genesis.",
        "first_target_slice": {
            "entry_points": ["0x3B098", "0x3BB48", "0x3C2E2"],
            "why": "Startup/title text path is narrow and already understood.",
        },
        "notes": [
            "Scaffold only: no opcode patches applied yet.",
            "Next step is to populate absolute-address and MMIO rewrite rules.",
            "Do not replace gameplay logic here with handwritten behavior.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
