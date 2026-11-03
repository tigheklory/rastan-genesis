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

STARTUP_COMMON_SLICE_START = 0x03AE86
STARTUP_COMMON_SLICE_END = 0x03B05C

STARTUP_DEPENDENCIES = [
    "0x3B9F8",
    "0x3AD72",
    "0x3AD44",
    "0x3AD3C",
    "0x5FFA2",
    "0x5FFB2",
    "0x3B0C2",
]

STARTUP_ABSOLUTE_ACCESSES = [
    {
        "address": "0x00C50000",
        "access": "write16",
        "kind": "mmio",
        "why": "startup control register clear",
    },
    {
        "address": "0x00D01BFE",
        "access": "write16",
        "kind": "mmio",
        "why": "startup board/video register clear",
    },
    {
        "address": "0x00350008",
        "access": "write16",
        "kind": "mmio",
        "why": "startup board state clear",
    },
    {
        "address": "0x00380000",
        "access": "write16",
        "kind": "mmio",
        "why": "startup display/status register clear",
    },
    {
        "address": "0x003E0001",
        "access": "write8",
        "kind": "mmio",
        "why": "startup bank/control select",
    },
    {
        "address": "0x003E0003",
        "access": "write8",
        "kind": "mmio",
        "why": "startup bank/control latch",
    },
    {
        "address": "0x00200000",
        "access": "read16/write16",
        "kind": "memory_test",
        "why": "startup RAM/bus test loop",
    },
    {
        "address": "0x0010C000",
        "access": "read16/write16",
        "kind": "workram",
        "why": "main work RAM clear/copy and A5 base",
    },
    {
        "address": "0x003C0000",
        "access": "write16",
        "kind": "mmio",
        "why": "startup status/control writes",
    },
    {
        "address": "0x00C00000",
        "access": "write_block",
        "kind": "video_ram_window",
        "why": "startup display layer clear",
    },
    {
        "address": "0x00C08000",
        "access": "write_block",
        "kind": "video_text_window",
        "why": "startup title/text layer clear",
    },
    {
        "address": "0x00C04000",
        "access": "write_block",
        "kind": "video_ram_window",
        "why": "startup display buffer clear",
    },
    {
        "address": "0x00C0C000",
        "access": "write_block",
        "kind": "video_ram_window",
        "why": "startup display buffer clear",
    },
    {
        "address": "0x00390009",
        "access": "read8",
        "kind": "dip_bank_1",
        "why": "startup DIP bank 1 read",
    },
    {
        "address": "0x0039000B",
        "access": "read8",
        "kind": "dip_bank_2",
        "why": "startup DIP bank 2 read",
    },
    {
        "address": "0x0005FF9E",
        "access": "read16",
        "kind": "service_io",
        "why": "service/input-derived config bits",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch Rastan maincpu for the Genesis port.")
    parser.add_argument(
        "--variant",
        default="world_rev1",
        help="Program variant identity for the current build.",
    )
    parser.add_argument(
        "--input",
        default="build/regions/maincpu.bin",
        help="Path to the extracted arcade maincpu binary.",
    )
    parser.add_argument(
        "--output",
        default="build/rastan/maincpu_patched.bin",
        help="Path to the patched output blob.",
    )
    parser.add_argument(
        "--manifest",
        default="build/rastan/maincpu_patch_manifest.json",
        help="Path to the emitted patch manifest.",
    )
    parser.add_argument(
        "--startup-output",
        default="build/rastan/startup_common_slice.bin",
        help="Path to the emitted common startup/basic system-test slice.",
    )
    parser.add_argument(
        "--startup-manifest",
        default="build/rastan/startup_common_manifest.json",
        help="Path to the emitted common startup slice manifest.",
    )
    return parser.parse_args()


def build_startup_manifest(startup_output_path: Path, variant: str) -> dict:
    return {
        "name": "startup_common_slice",
        "variant": variant,
        "entry_point": f"0x{STARTUP_COMMON_SLICE_START:06X}",
        "range": {
            "start": f"0x{STARTUP_COMMON_SLICE_START:06X}",
            "end_exclusive": f"0x{STARTUP_COMMON_SLICE_END:06X}",
            "size_bytes": STARTUP_COMMON_SLICE_END - STARTUP_COMMON_SLICE_START,
        },
        "output": str(startup_output_path),
        "goal": "Run the original common startup and basic hardware-test block on Genesis.",
        "normal_boot_continues_at": "0x03B05C",
        "test_mode_jumps_to": "0x000100",
        "test_mode_gate": {
            "source": "btst #2, a5@(25) at 0x03B04E",
            "meaning": "DIP bank 1 switch 3 test-mode branch",
        },
        "scope": [
            "hardware/control clears",
            "RAM/bus test loops",
            "work RAM init",
            "display RAM clears",
            "DIP/config reads",
            "normal/test split decision"
        ],
        "non_goals": [
            "Executing the detailed DIP-selected test program at 0x000100"
        ],
        "dependencies": STARTUP_DEPENDENCIES,
        "absolute_accesses": STARTUP_ABSOLUTE_ACCESSES,
        "known_runtime_facts": [
            "A5 is established as 0x10C000 main work RAM base.",
            "0x390009 and 0x39000B are the DIP-bank reads seen in boot.",
            "0x200000 is hammered twice in 8192-iteration loops for startup test.",
            "0xC08000 belongs to the startup/title text layer used later by 0x3BB48.",
        ],
        "next_patch_classes": [
            "absolute_ram",
            "mmio",
            "control_flow",
        ],
        "notes": [
            "Slice emitted unchanged for now; this is an extraction and planning artifact.",
            "First execution attempt should enter this slice with remapped MMIO and work RAM.",
        ],
    }


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    startup_output_path = Path(args.startup_output)
    startup_manifest_path = Path(args.startup_manifest)

    data = input_path.read_bytes()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    startup_output_path.parent.mkdir(parents=True, exist_ok=True)
    startup_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Placeholder behavior for the scaffold:
    # emit an unchanged copy plus a manifest proving the pipeline ran.
    output_path.write_bytes(data)
    startup_output_path.write_bytes(
        data[STARTUP_COMMON_SLICE_START:STARTUP_COMMON_SLICE_END]
    )

    manifest = {
        "input": str(input_path),
        "output": str(output_path),
        "variant": args.variant,
        "input_size": len(data),
        "patches": [],
        "patch_classes": list(PATCH_CLASSES),
        "execution_goal": "Run patched original Rastan maincpu code on Genesis.",
        "first_target_slice": {
            "id": "startup_common_slice",
            "entry_points": [f"0x{STARTUP_COMMON_SLICE_START:06X}"],
            "normal_boot_followon": "0x03B05C",
            "excludes": ["0x000100 detailed DIP-selected test program"],
            "why": "This is the first substantial common startup/basic system-test block the arcade runs on every boot.",
        },
        "startup_slice_manifest": str(startup_manifest_path),
        "notes": [
            "Scaffold only: no opcode patches applied yet.",
            "Next step is to populate absolute-address and MMIO rewrite rules.",
            "Do not replace gameplay logic here with handwritten behavior.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    startup_manifest_path.write_text(
        json.dumps(build_startup_manifest(startup_output_path, args.variant), indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
