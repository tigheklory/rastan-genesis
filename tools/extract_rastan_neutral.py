#!/usr/bin/env python3

import binascii
import struct
import subprocess
import zlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
REF_IMAGE = ROOT / "examples" / "hello-rastan" / "res" / "sprite" / "rastan_reference.png"
OUT_IMAGE = ROOT / "examples" / "hello-rastan" / "res" / "sprite" / "rastan_neutral_rom.png"
REPORT = ROOT / "build" / "rastan_neutral_report.txt"

SPRITE_ROMS = [
    ("b04-05.15", 0x00000, 0),
    ("b04-06.28", 0x00000, 1),
    ("b04-07.14", 0x40000, 0),
    ("b04-08.27", 0x40000, 1),
]


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


def load_rgba(path: Path, width: int, height: int) -> bytes:
    return subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-",
        ]
    )


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


def crop_ref_cell(rgba: bytes, x0: int, y0: int) -> list[tuple[int, int, int, int]]:
    width = 128
    cell = []
    for y in range(y0, y0 + 16):
        for x in range(x0, x0 + 16):
            i = (y * width + x) * 4
            cell.append(tuple(rgba[i : i + 4]))
    return cell


def score_tile(tile: list[int], ref: list[tuple[int, int, int, int]]) -> tuple[int, dict[int, tuple[int, int, int]]]:
    per_index = defaultdict(list)
    mismatch = 0

    for pix, rgba in zip(tile, ref):
        if pix == 0 and rgba[3] == 0:
            continue
        if pix == 0 and rgba[3] != 0:
            mismatch += 12
            continue
        if pix != 0 and rgba[3] == 0:
            mismatch += 12
            continue
        per_index[pix].append(rgba[:3])

    mapping = {}
    for pix, samples in per_index.items():
        mapping[pix] = Counter(samples).most_common(1)[0][0]

    for pix, rgba in zip(tile, ref):
        if pix == 0 or rgba[3] == 0:
            continue
        if mapping[pix] != rgba[:3]:
            mismatch += 1

    return mismatch, mapping


def main() -> int:
    region = build_sprite_region()
    reference = load_rgba(REF_IMAGE, 128, 48)

    ref_cells = []
    for cell_y in range(3):
        for cell_x in range(2):
            ref_cells.append(crop_ref_cell(reference, cell_x * 16, cell_y * 16))

    chosen_tiles = []
    global_map_samples = defaultdict(list)

    decoded_tiles = [decode_tile(region, i) for i in range(len(region) // 128)]

    for cell_index, ref_cell in enumerate(ref_cells):
        best_tile = None
        best_score = None
        best_map = None
        for tile_index, tile in enumerate(decoded_tiles):
            score, mapping = score_tile(tile, ref_cell)
            if best_score is None or score < best_score:
                best_score = score
                best_tile = tile_index
                best_map = mapping
        chosen_tiles.append(best_tile)
        for key, value in best_map.items():
            global_map_samples[key].append(value)

    palette_rgb = [(0, 0, 0)]
    alpha = [0]
    for color_index in range(1, 16):
        if global_map_samples[color_index]:
            palette_rgb.append(Counter(global_map_samples[color_index]).most_common(1)[0][0])
            alpha.append(255)
        else:
            palette_rgb.append((0, 0, 0))
            alpha.append(0)

    out_pixels = bytearray()
    for row in range(3):
        tile_rows = [decoded_tiles[chosen_tiles[row * 2 + col]] for col in range(2)]
        for y in range(16):
            for col in range(2):
                tile = tile_rows[col]
                out_pixels.extend(tile[y * 16 : (y + 1) * 16])

    write_indexed_png(OUT_IMAGE, 32, 48, palette_rgb, alpha, bytes(out_pixels))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "Chosen 16x16 sprite tile indices for hello-rastan neutral pose:\n"
        + "\n".join(
            f"cell {i}: tile {tile}" for i, tile in enumerate(chosen_tiles)
        )
        + "\n"
    )
    print(f"Wrote {OUT_IMAGE}")
    print(REPORT.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
