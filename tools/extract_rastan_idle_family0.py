#!/usr/bin/env python3

import binascii
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
OUT = ROOT / "examples" / "hello-rastan" / "res" / "sprite" / "rastan_idle_family0.png"
REPORT = ROOT / "build" / "rastan_idle_family0.txt"

MAINCPU_ROMS = [
    ("b04-38.19", 0x00000),
    ("b04-37.7", 0x00001),
    ("b04-40.20", 0x20000),
    ("b04-39.8", 0x20001),
    ("b04-42.21", 0x40000),
    ("b04-43-1.9", 0x40001),
]

SPRITE_ROMS = [
    ("b04-05.15", 0x00000, 0),
    ("b04-06.28", 0x00000, 1),
    ("b04-07.14", 0x40000, 0),
    ("b04-08.27", 0x40000, 1),
]

FAMILY0_TABLE = 0x3D09E
TILE_BASE = 0x004B
FRAME_CODE = 0x17

# Approximate in-game palette for the first useful sprite test.
PALETTE = [
    (0x00, 0x00, 0x00),
    (0xF8, 0xF8, 0xF8),
    (0xC8, 0xC8, 0xC8),
    (0x78, 0x78, 0x78),
    (0xF8, 0xD0, 0xA8),
    (0xD8, 0x98, 0x78),
    (0x9A, 0x58, 0x48),
    (0x20, 0x18, 0x18),
    (0x40, 0xB0, 0x38),
    (0x18, 0x68, 0x18),
    (0xF8, 0xD8, 0x38),
    (0xC8, 0x88, 0x18),
    (0xD8, 0x30, 0x20),
    (0x78, 0x10, 0x10),
    (0x38, 0x38, 0x58),
    (0xA8, 0xA0, 0xC8),
]


def chunk(tag: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_indexed_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = []
    for y in range(height):
        rows.append(b"\x00" + pixels[y * width : (y + 1) * width])
    compressed = zlib.compress(b"".join(rows), 9)

    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)))
        handle.write(chunk(b"PLTE", b"".join(bytes(rgb) for rgb in PALETTE)))
        handle.write(chunk(b"tRNS", bytes([0] + [255] * 15)))
        handle.write(chunk(b"IDAT", compressed))
        handle.write(chunk(b"IEND", b""))


def load16_byte_pairs(region_size: int, entries: list[tuple[str, int]]) -> bytes:
    data = bytearray(region_size)
    for filename, offset in entries:
        rom = (ROMS / filename).read_bytes()
        data[offset : offset + len(rom) * 2 : 2] = rom
    return bytes(data)


def build_sprite_region() -> bytes:
    region = bytearray(0x80000)
    for filename, base, odd in SPRITE_ROMS:
        data = (ROMS / filename).read_bytes()
        start = base + odd
        region[start : start + len(data) * 2 : 2] = data
    return bytes(region)


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def decode_frame(maincpu: bytes) -> list[tuple[int, int, int, int]]:
    off = int.from_bytes(maincpu[FAMILY0_TABLE + FRAME_CODE * 2 : FAMILY0_TABLE + FRAME_CODE * 2 + 2], "big")
    ptr = FAMILY0_TABLE + off
    parts: list[tuple[int, int, int, int]] = []
    while True:
        control = maincpu[ptr]
        if control == 0xFF:
            return parts
        y = s8(maincpu[ptr + 1])
        tile_delta = maincpu[ptr + 2]
        x = s8(maincpu[ptr + 3])
        parts.append((x, y, TILE_BASE + tile_delta, control))
        ptr += 4


def decode_tile(region: bytes, tile_index: int) -> list[int]:
    start = tile_index * 128
    tile = region[start : start + 128]
    pixels = []
    for y in range(16):
        row = tile[y * 8 : (y + 1) * 8]
        for byte in row:
            pixels.append((byte >> 4) & 0x0F)
            pixels.append(byte & 0x0F)
    return pixels


def render(parts: list[tuple[int, int, int, int]], sprite_region: bytes) -> tuple[int, int, bytes]:
    min_x = min(x for x, _, _, _ in parts)
    min_y = min(y for _, y, _, _ in parts)
    max_x = max(x + 16 for x, _, _, _ in parts)
    max_y = max(y + 16 for _, y, _, _ in parts)
    width = max_x - min_x
    height = max_y - min_y
    pixels = bytearray(width * height)

    for x, y, tile_index, _ in parts:
        tile = decode_tile(sprite_region, tile_index)
        ox = x - min_x
        oy = y - min_y
        for ty in range(16):
            for tx in range(16):
                value = tile[ty * 16 + tx]
                if value:
                    pixels[(oy + ty) * width + ox + tx] = value

    return width, height, bytes(pixels)


def main() -> int:
    maincpu = load16_byte_pairs(0x60000, MAINCPU_ROMS)
    sprite_region = build_sprite_region()
    parts = decode_frame(maincpu)
    width, height, pixels = render(parts, sprite_region)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_indexed_png(OUT, width, height, pixels)
    REPORT.write_text(
        "\n".join(
            [
                "Rastan family-0 idle candidate",
                f"table=0x{FAMILY0_TABLE:06x}",
                f"tile_base=0x{TILE_BASE:04x}",
                f"frame=0x{FRAME_CODE:02x}",
                f"size={width}x{height}",
            ]
        )
        + "\n"
    )
    print(f"Wrote {OUT}")
    print(f"Size {width}x{height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
