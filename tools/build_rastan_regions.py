#!/usr/bin/env python3

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROMS = ROOT / "roms"
BUILD = ROOT / "build" / "regions"


def load16_byte_pairs(region_size: int, entries: list[tuple[str, int]]) -> bytes:
    data = bytearray(region_size)
    for filename, offset in entries:
        rom = (ROMS / filename).read_bytes()
        data[offset : offset + len(rom) * 2 : 2] = rom
    return bytes(data)


def write_region(name: str, payload: bytes) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    path = BUILD / f"{name}.bin"
    path.write_bytes(payload)
    print(f"wrote {path} ({len(payload)} bytes)")


def main() -> int:
    write_region(
        "maincpu",
        load16_byte_pairs(
            0x60000,
            [
                ("b04-38.19", 0x00000),
                ("b04-37.7", 0x00001),
                ("b04-40.20", 0x20000),
                ("b04-39.8", 0x20001),
                ("b04-42.21", 0x40000),
                ("b04-43-1.9", 0x40001),
            ],
        ),
    )
    write_region(
        "pc080sn",
        load16_byte_pairs(
            0x80000,
            [
                ("b04-01.40", 0x00000),
                ("b04-02.67", 0x00001),
                ("b04-03.39", 0x40000),
                ("b04-04.66", 0x40001),
            ],
        ),
    )
    write_region(
        "pc090oj",
        load16_byte_pairs(
            0x80000,
            [
                ("b04-05.15", 0x00000),
                ("b04-06.28", 0x00001),
                ("b04-07.14", 0x40000),
                ("b04-08.27", 0x40001),
            ],
        ),
    )
    write_region("audiocpu", (ROMS / "b04-19.49").read_bytes())
    write_region("adpcm", (ROMS / "b04-20.76").read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
