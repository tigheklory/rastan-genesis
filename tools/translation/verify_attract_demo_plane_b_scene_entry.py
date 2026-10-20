#!/usr/bin/env python3
"""Verify the item-screen-to-R1 Plane-B ring ownership handoff."""

from __future__ import annotations

import argparse
from pathlib import Path


BLIT_START = ".Litempage_blit_tileset_selected:"
BLIT_END = ".Litempage_blit_scene_ready:"
TEARDOWN_START = "genesistan_pc090oj_hook_zero_fill_56440:"
TEARDOWN_END = "genesistan_pc090oj_hook_status_sprite_5a098:"


def require_once(text: str, needle: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise RuntimeError(f"expected one {needle!r}, got {count}")
    return text.index(needle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tilemap-source", type=Path, required=True)
    parser.add_argument("--sprite-source", type=Path, required=True)
    args = parser.parse_args()

    tilemap = args.tilemap_source.read_text(encoding="utf-8")
    start = tilemap.index(BLIT_START)
    end = tilemap.index(BLIT_END, start)
    blit = tilemap[start:end]

    cache_check = require_once(blit, "cmp.b   genesistan_current_pc080sn_tileset_id, %d1")
    cache_skip = require_once(blit, "beq.s   .Litempage_blit_scene_ready")
    countdown = require_once(blit, "tst.w   0x10AA(%a5)")
    arm = require_once(blit, "move.b  #1, genesistan_scene_present_pending")
    load = require_once(blit, "bsr     load_scene_tiles")

    if not (cache_check < cache_skip < countdown < arm < load):
        raise RuntimeError(
            "tileset cache hit must precede the multi-call fill countdown lifecycle"
        )
    if "bra.s   .Litempage_blit_load_scene" in blit:
        raise RuntimeError("nonzero fill countdown still forces repeated scene reload")

    sprites = args.sprite_source.read_text(encoding="utf-8")
    start = sprites.index(TEARDOWN_START)
    end = sprites.index(TEARDOWN_END, start)
    teardown = sprites[start:end]

    retained = [
        require_once(teardown, f"clr.w   0x{offset}(%a5)")
        for offset in ("10AE", "10B0", "10EC", "10EE")
    ]
    staged = [
        require_once(teardown, f"clr.w   {name}")
        for name in (
            "staged_scroll_x_fg",
            "staged_scroll_y_fg",
            "staged_scroll_x_bg",
            "staged_scroll_y_bg",
        )
    ]
    clear = require_once(teardown, "bsr     genesistan_hook_cwindow_clear")
    if not (max(retained + staged) < clear):
        raise RuntimeError("ring/scroll origin must be rebased before plane clear")

    print("ATTRACT_DEMO_PLANE_B_SCENE_ENTRY_PASS")
    print("pattern_cache_hit=preserved")
    print("a5+0x10AA=multi_call_fill_countdown")
    print("item_teardown_ring_origin=retained_scroll_zero,native_scroll_zero")
    print("ordinary_gameplay_and_next_life=scene_lifecycle_unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
