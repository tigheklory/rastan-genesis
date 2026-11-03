#!/usr/bin/env python3
"""Offline model of Rastan's PC090OJ compositor dispatch at 0x3D054/0x3C902.

The public API models SAT words, not a guessed image layout. The general
program is fully implemented. Coordinate-only special programs require the
pre-seeded SAT tile/attribute words that the arcade handlers preserve; they
are reported explicitly instead of being mis-decoded as general programs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
MAINCPU = (ROOT / "build/regions/maincpu.bin").read_bytes()
PC090OJ = (ROOT / "build/regions/pc090oj.bin").read_bytes()

COMPOSITOR_TABLES = {
    0: 0x03D09E,
    1: 0x04771C,
    2: 0x03F0CE,
    3: 0x040004,
    4: 0x04002C,
}

SPECIAL_HANDLERS = {
    0x10: 0x03C830,
    0x20: 0x03C7A4,
    0x30: 0x03C6DC,
    0x50: 0x03C4D2,
    0x60: 0x03C4D2,
    0x90: 0x03C75C,
    0xA0: 0x03C550,
    0xB0: 0x03C636,
    0xC0: 0x03C586,
}


def be16(address: int) -> int:
    return int.from_bytes(MAINCPU[address : address + 2], "big")


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


@dataclass(frozen=True)
class ActorRenderState:
    base_graphics: int
    anim_index: int
    compositor_selector: int
    x_16: int = 0
    y_1a: int = 0
    y_adjust_18: int = 0
    facing_02: int = 0
    mirror_control_20: int = 0
    state_03: int = 0
    palette_attr_27: int = 0
    piece_budget: int = 20


@dataclass(frozen=True)
class SATPiece:
    word0: int
    y: int
    tile: int
    x: int
    hidden: bool = False

    @property
    def hflip(self) -> bool:
        return bool(self.word0 & 0x4000)

    @property
    def vflip(self) -> bool:
        return bool(self.word0 & 0x8000)

    @property
    def palette(self) -> int:
        return self.word0 & 0x000F

    def as_dict(self) -> dict:
        return {
            "tile": f"0x{self.tile & 0x1FFF:04X}",
            "x": self.x & 0x1FF,
            "y": self.y & 0x1FF,
            "hflip": self.hflip,
            "vflip": self.vflip,
            "palette": self.palette,
            "word0": f"0x{self.word0 & 0xFFFF:04X}",
            "hidden": self.hidden,
        }


class SpecialCompositorProgram(RuntimeError):
    def __init__(self, mode: int, program_address: int):
        super().__init__(
            f"program 0x{program_address:06X} uses coordinate-only mode "
            f"0x{mode:02X} (handler 0x{SPECIAL_HANDLERS[mode]:06X}); seeded SAT required"
        )
        self.mode = mode
        self.program_address = program_address


def program_address(anim_index: int, compositor_selector: int) -> int:
    """Apply the exact 0x3D054 selector-to-table dispatch."""
    try:
        table = COMPOSITOR_TABLES[compositor_selector]
    except KeyError as exc:
        raise ValueError(f"unsupported compositor selector {compositor_selector}") from exc
    return table + be16(table + (anim_index & 0xFF) * 2)


def _branch_3c960(state: ActorRenderState) -> bool:
    """Model the D6 bit-0 / actor+0x03 / D7 selection at 0x3CA26."""
    facing = bool(state.facing_02 & 0xFF)
    if state.mirror_control_20 & 1:
        return bool(state.state_03) or not facing
    return facing


def run_general(state: ActorRenderState, *, include_hidden: bool = False) -> list[SATPiece]:
    """Execute the general 0x3C902 path and return arcade SAT-equivalent words.

    Program records are ``control, y, tile_delta, x``. Control 0x40 negates
    the tile delta; 0x70 adds actor+0x18 to Y; 0x80 sets PC090OJ HFLIP.
    Facing selects the 0x3C960/0x3C9A6 coordinate branch. VFLIP is not emitted
    by this path. A 0xFF terminator parks the rest of the caller's SAT budget at
    Y=0x180, exactly as the arcade loop does.
    """
    address = program_address(state.anim_index, state.compositor_selector)
    first_mode = MAINCPU[address] & 0xF0
    if first_mode in SPECIAL_HANDLERS:
        raise SpecialCompositorProgram(first_mode, address)

    pieces: list[SATPiece] = []
    cursor = address
    branch_3c960 = _branch_3c960(state)
    terminated = False
    for _ in range(state.piece_budget):
        control = MAINCPU[cursor]
        cursor += 1
        if terminated or control == 0xFF:
            terminated = True
            if include_hidden:
                pieces.append(SATPiece(0, 0x180, 0, 0, True))
            continue

        mode = control & 0xF0
        if mode in SPECIAL_HANDLERS:
            raise SpecialCompositorProgram(mode, address)
        if mode not in (0x00, 0x40, 0x70, 0x80):
            raise ValueError(f"unknown general control 0x{control:02X} at 0x{cursor - 1:06X}")

        y_delta = s8(MAINCPU[cursor])
        tile_delta = MAINCPU[cursor + 1]
        x_delta = s8(MAINCPU[cursor + 2])
        cursor += 3

        negate_tile = mode == 0x40
        tile = state.base_graphics + (-tile_delta if negate_tile else tile_delta)
        word0 = control
        if state.palette_attr_27 & 0x40:
            word0 = (word0 & 0xFF00) | state.palette_attr_27

        y = state.y_1a + y_delta
        if mode == 0x70:
            y += state.y_adjust_18

        if branch_3c960:
            if mode == 0x80:
                word0 |= 0x4000
            x = state.x_16 + x_delta
        else:
            word0 |= 0x4000
            x = state.x_16 - x_delta - 16

        pieces.append(SATPiece(word0 & 0xFFFF, y & 0xFFFF, tile & 0xFFFF, x & 0xFFFF))
    return pieces


def visible_pieces(state: ActorRenderState) -> list[SATPiece]:
    return [piece for piece in run_general(state) if not piece.hidden]


def decode_tile(code: int) -> list[list[int]]:
    """Decode one MAME ``gfx_16x16x4_packed_msb`` PC090OJ tile."""
    base = (code & 0x1FFF) * 128
    pixels = [[0] * 16 for _ in range(16)]
    for row in range(16):
        for pair in range(8):
            value = PC090OJ[base + row * 8 + pair]
            pixels[row][pair * 2] = value >> 4
            pixels[row][pair * 2 + 1] = value & 0x0F
    return pixels


def relative_piece_dicts(pieces: Iterable[SATPiece]) -> list[dict]:
    visible = [piece for piece in pieces if not piece.hidden]
    if not visible:
        return []
    origin_x = min(piece.x & 0x1FF for piece in visible)
    origin_y = min(piece.y & 0x1FF for piece in visible)
    result = []
    for piece in visible:
        item = piece.as_dict()
        item["x"] = (piece.x & 0x1FF) - origin_x
        item["y"] = (piece.y & 0x1FF) - origin_y
        result.append(item)
    return result


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=lambda value: int(value, 0))
    parser.add_argument("anim", type=lambda value: int(value, 0))
    parser.add_argument("selector", type=lambda value: int(value, 0))
    parser.add_argument("--facing", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--attr", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--budget", type=int, default=20)
    args = parser.parse_args()
    actor = ActorRenderState(
        args.base, args.anim, args.selector, facing_02=args.facing,
        palette_attr_27=args.attr, piece_budget=args.budget,
    )
    print(json.dumps({
        "program_address": f"0x{program_address(args.anim, args.selector):06X}",
        "pieces": [piece.as_dict() for piece in run_general(actor, include_hidden=True)],
    }, indent=2))
