#!/usr/bin/env python3
"""Gate independent gameplay-collision and Genesis visual semantics."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "apps/rastan-direct/src/tilemap_hooks.s"
MAINCPU = ROOT / "build/regions/maincpu.bin"


def section(source: str, begin: str, end: str) -> str:
    start = source.index(begin)
    return source[start:source.index(end, start)]


def payload(data: bytes, pointer: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    tiles = tuple(int.from_bytes(data[pointer + i:pointer + i + 2], "big") & 0x3fff
                  for i in range(0, 0x20, 2))
    if int.from_bytes(data[pointer + 0x20:pointer + 0x22], "big") == 0x00ff:
        collision = (int.from_bytes(data[pointer + 0x22:pointer + 0x24], "big"),) * 16
    else:
        collision = tuple(int.from_bytes(data[pointer + 0x20 + i:pointer + 0x22 + i], "big")
                          for i in range(0, 0x20, 2))
    return tiles, collision


def main() -> None:
    source = SOURCE.read_text()
    visual = section(source, "resolve_plane_a_cell:",
                     "/* Build 0419 BG-B fused Plane-A semantic accessor.")
    collision = section(source, "resolve_plane_a_collision_cell:",
                        "/* Build 0420 generated semantic leaf.")
    plane_b = section(source, ".Lplane_b_publish_logical_row_native:",
                      ".Lplane_b_stage_gameplay_producer_cell_native:")
    if "0x20(%a0" in visual:
        raise SystemExit("FAIL: visual-only Plane-A resolver reads collision field")
    if "0x20(%a0" not in collision:
        raise SystemExit("FAIL: collision-only resolver omits independent collision field")
    if "collision" in plane_b.lower() or "native_metatile" in plane_b:
        raise SystemExit("FAIL: Plane-B visual row path depends on collision/metatile record")
    if "#ARCADE_COLLISION_MAP_BASE" not in source:
        raise SystemExit("FAIL: separate gameplay collision-map storage missing")

    data = MAINCPU.read_bytes()
    records: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {}
    for descriptor in range(0x0f08, 0x3a00c, 4):
        pointer = int.from_bytes(data[descriptor + 2:descriptor + 4], "big")
        if pointer <= 0x5fdfc and not pointer & 1:
            records[pointer] = payload(data, pointer)
    by_visual: defaultdict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    by_collision: defaultdict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    for visual_fields, collision_fields in records.values():
        by_visual[visual_fields].add(collision_fields)
        by_collision[collision_fields].add(visual_fields)
    if not any(len(values) > 1 for values in by_visual.values()):
        raise SystemExit("FAIL: corpus does not prove same visual can have different collision")
    if not any(len(values) > 1 for values in by_collision.values()):
        raise SystemExit("FAIL: corpus does not prove same collision can have different visual")
    print("PASS collision/visual semantics: separate WRAM collision map; visual-only and "
          "collision-only APIs are independent; Plane B has no collision dependency; "
          "corpus proves many-to-many visual/collision relationships")


if __name__ == "__main__":
    main()
