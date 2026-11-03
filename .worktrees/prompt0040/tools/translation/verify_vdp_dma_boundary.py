#!/usr/bin/env python3
"""Build-0418 VDP DMA source-bank and PC080SN alignment gate."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DMA_SOURCE = ROOT / "apps/rastan-direct/src/dma.s"
SCENE_SOURCE = ROOT / "apps/rastan-direct/src/scene_load.s"
SPRITE_SOURCE = ROOT / "apps/rastan-direct/src/pc090oj_hooks.s"
DEFAULT_SYMBOLS = ROOT / "apps/rastan-direct/out/symbol.txt"
DEFAULT_PATTERNS = ROOT / "build/regions/pc080sn_editor_layera.bin"
BANK_BYTES = 0x20000
TILE_BYTES = 32


def fail(message: str) -> None:
    raise SystemExit(f"FAIL VDP DMA boundary gate: {message}")


@dataclass(frozen=True)
class Chunk:
    source: int
    destination: int
    words: int


def split_dma(source: int, destination: int, words: int) -> list[Chunk]:
    """Model the checked autoincrement-2 entry (zero means 0x10000 words)."""
    remaining = 0x10000 if words == 0 else words
    if not 0 < remaining <= 0x10000:
        fail(f"invalid 16-bit DMA word count {words:#x}")
    chunks: list[Chunk] = []
    while remaining:
        offset = source & (BANK_BYTES - 1)
        available = (BANK_BYTES - offset) // 2
        count = min(remaining, available)
        chunks.append(Chunk(source, destination, count))
        advance = count * 2
        source += advance
        destination = (destination + advance) & 0xFFFF
        remaining -= count
    return chunks


def verify_arithmetic() -> None:
    destination = 0x7480
    cases = (
        (0x1FFE0, 16, [(0x1FFE0, 0x7480, 16)]),
        (0x1FFE8, 16, [(0x1FFE8, 0x7480, 12), (0x20000, 0x7498, 4)]),
        (0x1FFF8, 16, [(0x1FFF8, 0x7480, 4), (0x20000, 0x7488, 12)]),
        (0x20000, 16, [(0x20000, 0x7480, 16)]),
    )
    payload = bytes(range(32))
    memory = bytearray(0x40000)
    for source, words, expected in cases:
        memory[source:source + len(payload)] = payload
        chunks = split_dma(source, destination, words)
        actual = [(c.source, c.destination, c.words) for c in chunks]
        if actual != expected:
            fail(f"split {source:#x}/{words} words: {actual!r} != {expected!r}")
        rebuilt = b"".join(memory[c.source:c.source + c.words * 2] for c in chunks)
        if rebuilt != payload:
            fail(f"split {source:#x} does not reconstruct contiguous source bytes")
    full_aligned = split_dma(0x20000, destination, 0)
    if full_aligned != [Chunk(0x20000, destination, 0x10000)]:
        fail(f"aligned zero-count/full-bank transfer is wrong: {full_aligned!r}")
    full_crossing = split_dma(0x20002, destination, 0)
    if full_crossing != [
        Chunk(0x20002, destination, 0xFFFF),
        Chunk(0x40000, (destination + 0x1FFFE) & 0xFFFF, 1),
    ]:
        fail(f"crossing zero-count/full-bank transfer is wrong: {full_crossing!r}")


def verify_static_contract() -> None:
    dma = DMA_SOURCE.read_text()
    scene = SCENE_SOURCE.read_text()
    sprites = SPRITE_SOURCE.read_text()
    required_dma = (
        "lsr.l   #1, %d2",
        "add.w   %d1, %d2",
        "bcc.s   .Ldwtv_issue",
        ".Ldwtv_find_first:",
        "andi.l  #0x0001FFFF, %d2",
        "addi.l  #0x00020000, %d2",
        ".Ldwtv_split:",
        "adda.l  %d3, %a0",
        "add.l   %d3, %d0",
        "bsr.s   .Ldwtv_issue",
        "movea.l (%sp)+, %a0",
        ".Ldwtv_issue:",
    )
    for token in required_dma:
        if token not in dma:
            fail(f"dma.s omits checked-entry contract token {token!r}")
    if not re.search(r"\.balign\s+32\s*\n\s*genesistan_pc080sn_tile_rom:", scene):
        fail("PC080SN corpus label is not immediately preceded by .balign 32")
    sprite_block = sprites[sprites.index(".Lvcs_tile_src_ready:"):
                           sprites.index(".Lvcs_tile_next:")]
    if "bsr     vdp_dma_words_to_vram" not in sprite_block:
        fail("ROM-backed sprite-pattern upload does not use checked DMA entry")
    if "bsr     dma_words_to_vram_noai" in sprite_block:
        fail("ROM-backed sprite-pattern upload still uses unchecked noai entry")


def read_symbol(path: Path, name: str) -> int:
    pattern = re.compile(rf"^([0-9A-Fa-f]+)\s+\S\s+{re.escape(name)}$")
    for line in path.read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            return int(match.group(1), 16)
    fail(f"symbol {name!r} not found in {path}")


def verify_corpus(symbols: Path, patterns: Path) -> tuple[int, int, int]:
    base = read_symbol(symbols, "genesistan_pc080sn_tile_rom")
    if base % TILE_BYTES:
        fail(f"PC080SN corpus base {base:#x} is not 32-byte aligned")
    size = patterns.stat().st_size
    if size % TILE_BYTES:
        fail(f"PC080SN corpus size {size:#x} is not a whole number of patterns")
    for code in range(size // TILE_BYTES):
        if (base + code * TILE_BYTES) % TILE_BYTES:
            fail(f"PC080SN code {code:#x} is not 32-byte aligned")
    a0154 = base + 0x117 * TILE_BYTES
    if (a0154 & (BANK_BYTES - 1)) + TILE_BYTES > BANK_BYTES:
        fail(f"A-0154 source {a0154:#x} crosses a 128-KiB boundary")
    chunks = split_dma(a0154, 0x7480, 16)
    if len(chunks) != 1 or chunks[0].words != 16:
        fail(f"A-0154 must remain one 16-word DMA, got {chunks!r}")
    return base, a0154, size // TILE_BYTES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=Path, default=DEFAULT_SYMBOLS)
    parser.add_argument("--patterns", type=Path, default=DEFAULT_PATTERNS)
    args = parser.parse_args()
    verify_static_contract()
    verify_arithmetic()
    base, a0154, count = verify_corpus(args.symbols, args.patterns)
    print("PASS VDP DMA boundary gate")
    print(f"  PC080SN base={base:#08x} patterns={count} alignment=32")
    print(f"  A-0154 source={a0154:#08x} chunks=1 words=16")
    print("  synthetic boundary-32=16; boundary-24=12+4; boundary-8=4+12; aligned=16")


if __name__ == "__main__":
    main()
