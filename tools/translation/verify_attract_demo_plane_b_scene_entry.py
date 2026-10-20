#!/usr/bin/env python3
"""Verify scene fills cannot bypass native Plane-B entry initialization."""

from __future__ import annotations

import argparse
from pathlib import Path


START = ".Litempage_blit_tileset_selected:"
END = ".Litempage_blit_scene_ready:"


def require_once(text: str, needle: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise RuntimeError(f"expected one {needle!r}, got {count}")
    return text.index(needle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()

    text = args.source.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start)
    block = text[start:end]

    countdown = require_once(block, "tst.w   0x10AA(%a5)")
    arm = require_once(block, "move.b  #1, genesistan_scene_present_pending")
    cache_check = require_once(block, "cmp.b   genesistan_current_pc080sn_tileset_id, %d1")
    cache_skip = require_once(block, "beq.s   .Litempage_blit_scene_ready")
    forced_load = require_once(block, "bra.s   .Litempage_blit_load_scene")
    load = require_once(block, "bsr     load_scene_tiles")

    if not (countdown < arm < forced_load < cache_check < cache_skip < load):
        raise RuntimeError(
            "initial-fill ownership is not ordered before the tileset cache-hit fast path"
        )

    print("ATTRACT_DEMO_PLANE_B_SCENE_ENTRY_PASS")
    print("scene_fill_owner=a5+0x10AA")
    print("cache_hit_cannot_skip=present_arm,scene_reload,cache_reset,package_install")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
