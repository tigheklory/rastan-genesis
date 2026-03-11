#!/usr/bin/env python3

import binascii
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
OUT = ROOT / "build" / "family0_probe.png"

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

FRAME_TABLE = 0x3D09E
TILE_BASE = 0x0420
FRAMES = list(range(0xC9, 0xD8))


def chunk(tag: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_rgba_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = []
    for y in range(height):
        rows.append(b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4])
    compressed = zlib.compress(b"".join(rows), 9)
    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
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


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def decode_frame(maincpu: bytes, frame_code: int) -> list[tuple[int, int, int]]:
    off = int.from_bytes(maincpu[FRAME_TABLE + frame_code * 2 : FRAME_TABLE + frame_code * 2 + 2], "big")
    ptr = FRAME_TABLE + off
    parts = []
    while True:
        control = maincpu[ptr]
        if control == 0xFF:
            return parts
        y = s8(maincpu[ptr + 1])
        tile_delta = maincpu[ptr + 2]
        x = s8(maincpu[ptr + 3])
        parts.append((x, y, TILE_BASE + tile_delta))
        ptr += 4


def draw_frame(sprite_region: bytes, parts: list[tuple[int, int, int]]) -> tuple[int, int, bytes]:
    min_x = min(x for x, _, _ in parts)
    min_y = min(y for _, y, _ in parts)
    max_x = max(x + 16 for x, _, _ in parts)
    max_y = max(y + 16 for _, y, _ in parts)
    width = max_x - min_x
    height = max_y - min_y
    pixels = bytearray(width * height)
    for x, y, tile_index in parts:
        tile = decode_tile(sprite_region, tile_index)
        ox = x - min_x
        oy = y - min_y
        for ty in range(16):
            for tx in range(16):
                px = tile[ty * 16 + tx]
                if px:
                    pixels[(oy + ty) * width + ox + tx] = px
    return width, height, bytes(pixels)


def put_rgba(buf: bytearray, width: int, x: int, y: int, rgba: tuple[int, int, int, int]) -> None:
    if x < 0 or y < 0:
        return
    i = (y * width + x) * 4
    buf[i : i + 4] = bytes(rgba)


def main() -> int:
    maincpu = load16_byte_pairs(0x60000, MAINCPU_ROMS)
    sprite_region = build_sprite_region()

    cell_w = 96
    cell_h = 96
    cols = 4
    rows = (len(FRAMES) + cols - 1) // cols
    width = cols * cell_w
    height = rows * cell_h
    image = bytearray(width * height * 4)

    for idx, frame_code in enumerate(FRAMES):
        cx = (idx % cols) * cell_w
        cy = (idx // cols) * cell_h
        for y in range(cell_h):
            for x in range(cell_w):
                border = x in (0, cell_w - 1) or y in (0, cell_h - 1)
                shade = 16 if border else 0
                put_rgba(image, width, cx + x, cy + y, (shade, shade, shade, 255))

        parts = decode_frame(maincpu, frame_code)
        sw, sh, pixels = draw_frame(sprite_region, parts)
        ox = cx + (cell_w - sw) // 2
        oy = cy + (cell_h - sh) // 2
        for y in range(sh):
            for x in range(sw):
                px = pixels[y * sw + x]
                if px == 0:
                    continue
                shade = px * 17
                put_rgba(image, width, ox + x, oy + y, (shade, shade, shade, 255))

        marker = (frame_code - FRAMES[0]) * 4
        for x in range(24):
            put_rgba(image, width, cx + 8 + x, cy + 8, (255, 255, 255, 255))
            put_rgba(image, width, cx + 8 + x, cy + 9, (255, 255, 255, 255))
        for x in range(10):
            put_rgba(image, width, cx + 8 + marker + x, cy + cell_h - 10, (255, 96, 96, 255))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(OUT, width, height, bytes(image))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
