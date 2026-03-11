#!/usr/bin/env python3

import binascii
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
OUT_DIR = ROOT / "build" / "player_tied_candidates"
REPORT = OUT_DIR / "README.md"

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

FRAME_TABLES = {
    0: 0x3D09E,
    1: 0x4771C,
    2: 0x3F0CE,
    3: 0x40004,
    4: 0x4002C,
}

DEFAULT_STATE_TABLE = 0x45502
ALT_STATE_TABLE = 0x45562

CANDIDATES = [
    {
        "slug": "0508_state8",
        "title": "0x0508 state 8 direct-copy candidate",
        "source": "0x45342 seeds state 8 and 0x428b2 copies player X/Y into this actor family",
        "state": 8,
    },
    {
        "slug": "0508_state9",
        "title": "0x0508 state 9 direct-copy candidate",
        "source": "0x45342 seeds state 9 and 0x428b2 copies player X/Y into this actor family",
        "state": 9,
    },
    {
        "slug": "0748_state11",
        "title": "0x0748 class-11 helper-strip candidate",
        "source": "0x45642 builds class 11 helpers and 0x45c0c copies player X/Y-16 into their display coordinates",
        "state": 11,
    },
]


def chunk(tag: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_indexed_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = []
    for y in range(height):
        rows.append(b"\x00" + pixels[y * width : (y + 1) * width])
    compressed = zlib.compress(b"".join(rows), 9)

    palette = [(0, 0, 0)]
    alpha = [0]
    for value in range(1, 16):
        shade = value * 17
        palette.append((shade, shade, shade))
        alpha.append(255)

    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)))
        handle.write(chunk(b"PLTE", b"".join(bytes(rgb) for rgb in palette)))
        handle.write(chunk(b"tRNS", bytes(alpha)))
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


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def parse_anim_entry(maincpu: bytes, table_base: int, state: int) -> dict[str, int]:
    entry_offset = table_base + (state - 8) * 8
    return {
        "tile_base": be16(maincpu, entry_offset),
        "anim_len": maincpu[entry_offset + 2],
        "frame_code": maincpu[entry_offset + 3],
        "xoff": be16(maincpu, entry_offset + 4),
        "yoff": be16(maincpu, entry_offset + 6),
    }


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


def decode_frame(maincpu: bytes, family: int, tile_base: int, frame_code: int) -> list[tuple[int, int, int]]:
    table = FRAME_TABLES[family]
    off = be16(maincpu, table + frame_code * 2)
    ptr = table + off
    parts = []
    while True:
        control = maincpu[ptr]
        if control == 0xFF:
            return parts
        y = s8(maincpu[ptr + 1])
        tile_delta = maincpu[ptr + 2]
        x = s8(maincpu[ptr + 3])
        parts.append((x, y, tile_base + tile_delta))
        ptr += 4


def render_parts(sprite_region: bytes, parts: list[tuple[int, int, int]]) -> tuple[int, int, bytes]:
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


def main() -> int:
    maincpu = load16_byte_pairs(0x60000, MAINCPU_ROMS)
    sprite_region = build_sprite_region()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Player-Tied Candidate Gallery",
        "",
        "These images are ROM-derived sprite candidates tied to the confirmed player world coordinates by code path.",
        "",
        "They are not all the confirmed player body.",
        "They are grouped by routines that directly copy or closely slave display coordinates to `a5+0x10be / a5+0x10c0`.",
        "",
        "Confirmed coordinate-copy anchors:",
        "",
        "- `0x428b2`: copies player X/Y into the `0x0508` actor cluster",
        "- `0x447b6`: copies player X/Y into `0x02c8` actors of class `10/11/18`",
        "- `0x45c0c`: copies player X/Y-16 into helper-strip actors",
        "",
    ]

    for candidate in CANDIDATES:
        report_lines.extend(
            [
                f"## {candidate['title']}",
                "",
                f"- source: `{candidate['source']}`",
                f"- state: `0x{candidate['state']:02x}`",
                "",
            ]
        )

        for variant_name, table_base in (("default", DEFAULT_STATE_TABLE), ("alt", ALT_STATE_TABLE)):
            anim = parse_anim_entry(maincpu, table_base, candidate["state"])
            report_lines.extend(
                [
                    f"### {variant_name} table",
                    "",
                    f"- tile_base: `0x{anim['tile_base']:04x}`",
                    f"- frame_code: `0x{anim['frame_code']:02x}`",
                    f"- anim_len: `0x{anim['anim_len']:02x}`",
                    "",
                ]
            )

            for family in sorted(FRAME_TABLES):
                parts = decode_frame(maincpu, family, anim["tile_base"], anim["frame_code"])
                if not parts:
                    continue
                width, height, pixels = render_parts(sprite_region, parts)
                filename = f"{candidate['slug']}_{variant_name}_family{family}.png"
                out_path = OUT_DIR / filename
                write_indexed_png(out_path, width, height, pixels)
                report_lines.append(
                    f"- family `{family}`: [{filename}]({out_path}) `{width}x{height}`"
                )

            report_lines.append("")

    REPORT.write_text("\n".join(report_lines) + "\n")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
