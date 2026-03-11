#!/usr/bin/env python3

import binascii
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
OUT_DIR = ROOT / "examples" / "hello-rastan" / "res" / "sprite"
SHEET = ROOT / "build" / "family1_contact_sheet.png"
REPORT = ROOT / "build" / "family1_frames.txt"

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

FAMILY1_TABLE = 0x4771C
ANIM_TABLE_DEFAULT = 0x45502
ANIM_TABLE_ALT = 0x45562
PLAYER_STATE = 15


@dataclass(frozen=True)
class AnimEntry:
    table_name: str
    state: int
    tile_base: int
    aux_index: int
    frame_code: int
    param_a: int
    param_b: int


@dataclass(frozen=True)
class SpritePart:
    control: int
    x: int
    y: int
    tile_delta: int
    tile_index: int


def chunk(tag: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_indexed_png(path: Path, width: int, height: int, palette_rgb: list[tuple[int, int, int]], alpha: list[int], pixels: bytes) -> None:
    rows = []
    for y in range(height):
        rows.append(b"\x00" + pixels[y * width : (y + 1) * width])
    compressed = zlib.compress(b"".join(rows), 9)

    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)))
        handle.write(chunk(b"PLTE", b"".join(bytes(rgb) for rgb in palette_rgb)))
        handle.write(chunk(b"tRNS", bytes(alpha)))
        handle.write(chunk(b"IDAT", compressed))
        handle.write(chunk(b"IEND", b""))


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


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def parse_anim_entry(data: bytes, table_offset: int, state: int, table_name: str) -> AnimEntry:
    entry_offset = table_offset + (state - 8) * 8
    return AnimEntry(
        table_name=table_name,
        state=state,
        tile_base=be16(data, entry_offset),
        aux_index=data[entry_offset + 2],
        frame_code=data[entry_offset + 3],
        param_a=be16(data, entry_offset + 4),
        param_b=be16(data, entry_offset + 6),
    )


def family1_record_offset(maincpu: bytes, frame_code: int) -> int:
    return FAMILY1_TABLE + be16(maincpu, FAMILY1_TABLE + frame_code * 2)


def decode_parts(maincpu: bytes, anim_entry: AnimEntry) -> tuple[int, list[SpritePart]]:
    offset = family1_record_offset(maincpu, anim_entry.frame_code)
    parts = []

    while True:
        control = maincpu[offset]
        if control == 0xFF:
            break
        y = s8(maincpu[offset + 1])
        tile_delta = maincpu[offset + 2]
        x = s8(maincpu[offset + 3])
        parts.append(
            SpritePart(
                control=control,
                x=x,
                y=y,
                tile_delta=tile_delta,
                tile_index=anim_entry.tile_base + tile_delta,
            )
        )
        offset += 4

    return offset, parts


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


def grayscale_palette() -> tuple[list[tuple[int, int, int]], list[int]]:
    palette = [(0, 0, 0)]
    alpha = [0]
    for value in range(1, 16):
        shade = value * 17
        palette.append((shade, shade, shade))
        alpha.append(255)
    return palette, alpha


def render_parts(sprite_region: bytes, parts: list[SpritePart], out_path: Path) -> tuple[int, int]:
    min_x = min(part.x for part in parts)
    min_y = min(part.y for part in parts)
    max_x = max(part.x + 16 for part in parts)
    max_y = max(part.y + 16 for part in parts)
    width = max_x - min_x
    height = max_y - min_y

    pixels = bytearray(width * height)
    for part in parts:
        tile = decode_tile(sprite_region, part.tile_index)
        dst_x = part.x - min_x
        dst_y = part.y - min_y
        for y in range(16):
            for x in range(16):
                value = tile[y * 16 + x]
                if value == 0:
                    continue
                pixels[(dst_y + y) * width + dst_x + x] = value

    palette, alpha = grayscale_palette()
    write_indexed_png(out_path, width, height, palette, alpha, bytes(pixels))
    return width, height


def render_parts_to_buffer(sprite_region: bytes, parts: list[SpritePart]) -> tuple[int, int, bytes]:
    min_x = min(part.x for part in parts)
    min_y = min(part.y for part in parts)
    max_x = max(part.x + 16 for part in parts)
    max_y = max(part.y + 16 for part in parts)
    width = max_x - min_x
    height = max_y - min_y

    pixels = bytearray(width * height)
    for part in parts:
        tile = decode_tile(sprite_region, part.tile_index)
        dst_x = part.x - min_x
        dst_y = part.y - min_y
        for y in range(16):
            for x in range(16):
                value = tile[y * 16 + x]
                if value == 0:
                    continue
                pixels[(dst_y + y) * width + dst_x + x] = value

    return width, height, bytes(pixels)


def render_contact_sheet(sprite_region: bytes, entries: list[AnimEntry]) -> None:
    cell_w = 96
    cell_h = 96
    cols = 4
    rows = (len(entries) + cols - 1) // cols
    width = cell_w * cols
    height = cell_h * rows
    image = bytearray(width * height * 4)

    def put_px(x: int, y: int, rgba: tuple[int, int, int, int]) -> None:
        if x < 0 or y < 0 or x >= width or y >= height:
            return
        i = (y * width + x) * 4
        image[i : i + 4] = bytes(rgba)

    for idx, entry in enumerate(entries):
        _, parts = decode_parts(load16_byte_pairs(0x60000, MAINCPU_ROMS), entry)
        sprite_w, sprite_h, sprite_pixels = render_parts_to_buffer(sprite_region, parts)
        cell_x = (idx % cols) * cell_w
        cell_y = (idx // cols) * cell_h

        for y in range(cell_h):
            for x in range(cell_w):
                shade = 12 if (x in (0, cell_w - 1) or y in (0, cell_h - 1)) else 0
                put_px(cell_x + x, cell_y + y, (shade, shade, shade, 255))

        dst_x = cell_x + (cell_w - sprite_w) // 2
        dst_y = cell_y + 18 + (cell_h - 22 - sprite_h) // 2
        for y in range(sprite_h):
            for x in range(sprite_w):
                value = sprite_pixels[y * sprite_w + x]
                if value == 0:
                    continue
                shade = value * 17
                put_px(dst_x + x, dst_y + y, (shade, shade, shade, 255))

        bar_width = min(80, 10 + len(f"{entry.table_name} s{entry.state} f{entry.frame_code:02x}") * 6)
        for x in range(bar_width):
            put_px(cell_x + 8 + x, cell_y + 8, (255, 255, 255, 255))
            put_px(cell_x + 8 + x, cell_y + 9, (255, 255, 255, 255))

        info_y = cell_y + cell_h - 12
        marker = (entry.frame_code * 3) % (cell_w - 16)
        for x in range(12):
            put_px(cell_x + 2 + marker + x, info_y, (255, 128, 128, 255))
            put_px(cell_x + 2 + marker + x, info_y + 1, (255, 128, 128, 255))

    write_rgba_png(SHEET, width, height, bytes(image))


def describe_entry(maincpu: bytes, entry: AnimEntry) -> str:
    record_offset, parts = decode_parts(maincpu, entry)
    lines = [
        f"{entry.table_name} state {entry.state}: tile_base=0x{entry.tile_base:04x} aux=0x{entry.aux_index:02x} "
        f"frame=0x{entry.frame_code:02x} param_a=0x{entry.param_a:04x} param_b=0x{entry.param_b:04x}",
        f"  frame_record=0x{family1_record_offset(maincpu, entry.frame_code):06x} end=0x{record_offset:06x}",
    ]
    for index, part in enumerate(parts):
        lines.append(
            f"  part {index}: ctrl=0x{part.control:02x} tile_delta=0x{part.tile_delta:02x} "
            f"tile=0x{part.tile_index:04x} x={part.x:+d} y={part.y:+d}"
        )
    return "\n".join(lines)


def main() -> int:
    maincpu = load16_byte_pairs(0x60000, MAINCPU_ROMS)
    sprite_region = build_sprite_region()

    default_entries = [parse_anim_entry(maincpu, ANIM_TABLE_DEFAULT, state, "default") for state in range(8, 16)]
    alt_entries = [parse_anim_entry(maincpu, ANIM_TABLE_ALT, state, "alt") for state in range(8, 16)]

    target_entry = parse_anim_entry(maincpu, ANIM_TABLE_DEFAULT, PLAYER_STATE, "default")
    _, target_parts = decode_parts(maincpu, target_entry)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target_image = OUT_DIR / "rastan_family1_state15.png"
    width, height = render_parts(sprite_region, target_parts, target_image)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "Rastan family-1 frame decode",
        "",
        "This is driven from the 68000 animation path:",
        "- 0x457d0 sets family 1, state 15",
        "- 0x4543e resolves that to tile base + frame code",
        "- 0x4770e resolves the family-1 frame record",
        "- 0x3c902 style record bytes provide y, tile delta, and x",
        "",
        f"Rendered sample: {target_image}",
        f"Rendered dimensions: {width}x{height}",
        "",
        "Target entry:",
        describe_entry(maincpu, target_entry),
        "",
        "Default family-1 states 8-15:",
    ]
    report_lines.extend(describe_entry(maincpu, entry) for entry in default_entries)
    report_lines.append("")
    report_lines.append("Alternate family-1 states 8-15:")
    report_lines.extend(describe_entry(maincpu, entry) for entry in alt_entries)
    report_lines.append("")
    report_lines.append("Palette note: this render uses a grayscale placeholder palette.")

    REPORT.write_text("\n".join(report_lines) + "\n")
    render_contact_sheet(sprite_region, default_entries + alt_entries)
    print(f"Wrote {target_image}")
    print(f"Wrote {REPORT}")
    print(f"Wrote {SHEET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
