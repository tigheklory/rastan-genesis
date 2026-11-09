#!/usr/bin/env python3
"""Content-level verifier for PROMT-ID-0108 Round-1 MAME captures."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def words(path: Path) -> tuple[int, ...]:
    data = path.read_bytes()
    return struct.unpack(f">{len(data) // 2}H", data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--maincpu", type=Path, required=True)
    ap.add_argument("--stageclear-preload", type=Path, required=True)
    ap.add_argument("--native-patterns", type=Path, required=True)
    args = ap.parse_args()

    summary = (args.trace / "summary.txt").read_text(encoding="utf-8")
    for token in ("result=PASS", "scene_clear_command_27=YES", "round2_ready_observed=YES", "round2=YES"):
        if token not in summary:
            raise RuntimeError(f"runtime summary lacks {token}")

    maincpu = args.maincpu.read_bytes()
    preload = args.stageclear_preload.read_bytes()
    slots = dict(struct.unpack_from(">HH", preload, i) for i in range(0, len(preload) - 2, 4))
    stage = words(args.trace / "presentation_state_11_vram_plane_b.bin")
    staged = words(args.trace / "presentation_state_11_staged_plane_b.bin")
    if stage != staged:
        raise RuntimeError("Stage Clear staged/final Plane-B names differ")

    source = struct.unpack_from(">224H", maincpu, 0x056A22)
    for index, raw in enumerate(source):
        row, col = divmod(index, 14)
        expected = slots[raw & 0x3FFF]
        actual = stage[(10 + row) * 64 + 10 + col] & 0x07FF
        if actual != expected:
            raise RuntimeError(f"Stage Clear figure mismatch at {row},{col}: {actual:03X}!={expected:03X}")

    glyph = {chr(ord("A") + i): 0x17 + i for i in range(16)}
    glyph.update({"R": 0x27, "S": 0x28, "T": 0x29, "U": 0x2A, "V": 0x2B,
                  "W": 0x2C, "Y": 0x2D, ".": 0x06, "2": 0x0A, " ": 0})
    def require_text(plane: tuple[int, ...], row: int, col: int, text: str) -> None:
        for i, char in enumerate(text):
            actual = plane[row * 64 + col + i] & 0x07FF
            if actual != glyph[char]:
                raise RuntimeError(f"text {text!r} mismatch at {row},{col+i}: {actual:03X}")

    for row, text in zip((12, 14, 16, 18),
                         ("YOU ARE A BRAVE", "FIGHTER TO HAVE", "CLEARED SUCH A ", "DIFFICULT STAGE.")):
        require_text(stage, row, 25, text)
    ready = words(args.trace / "round2_ready_vram_plane_b.bin")
    require_text(ready, 12, 18, "ROUND 2")
    require_text(ready, 14, 19, "READY")

    plane_a = words(args.trace / "boss_vram_plane_a.bin")
    plane_b = words(args.trace / "boss_vram_plane_b.bin")
    if len(set(plane_a)) < 100 or len(set(plane_b)) < 300:
        raise RuntimeError("boss-room final VDP planes are not richly populated")
    vram = (args.trace / "boss_vram.bin").read_bytes()
    torch_codes = set()
    for group in range(6):
        torch_codes.update(struct.unpack_from(">4H", maincpu, 0x05979E + group * 16))
    native = args.native_patterns.read_bytes()
    torch_pixels = {native[(code & 0x3FFF) * 32:((code & 0x3FFF) + 1) * 32] for code in torch_codes}
    torch_cells = ((10,47), (10,15), (11,47), (11,15), (12,47), (12,15),
                   (11,48), (10,16), (12,48), (11,16), (13,48), (12,16))
    for row, col in torch_cells:
        slot = plane_a[row * 64 + col] & 0x07FF
        if vram[slot * 32:(slot + 1) * 32] not in torch_pixels:
            raise RuntimeError(f"runtime torch at {row},{col} references wrong pixel matrix")

    print("ROUND1_RUNTIME_CONTENT_PASS figure=224/224 message=exact ready=exact torches=12/12 planes=rich")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
