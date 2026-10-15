#!/usr/bin/env python3
"""Compare focused Build 0419/0421 Segment-0 semantic snapshots."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def words(path: Path) -> list[int]:
    data = path.read_bytes()
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]


def state(path: Path) -> dict[str, int]:
    with path.open(newline="") as source:
        row = next(csv.DictReader(source, delimiter="\t"))
    return {key: int(value, 16) if key != "frame" else int(value) for key, value in row.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--record-index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base_state = state(args.baseline / "state.tsv")
    candidate_state = state(args.candidate / "state.tsv")
    comparable = all(base_state[key] == candidate_state[key] for key in (
        "state0", "state2", "state4", "scene", "player_x", "player_y", "record",
        "scroll_a_x", "scroll_a_y", "strip_index", "strip_group", "bg_subcol",
        "bg_walker", "bg_table_index"))
    if not comparable:
        raise SystemExit("snapshot states are not semantically matched")

    rom = args.maincpu.read_bytes()
    record_index = args.record_index.read_bytes()
    descriptor_state = args.baseline.joinpath("descriptor_state.bin").read_bytes()
    front = (base_state["strip_group"] & 0x0f) * 4 + (base_state["strip_index"] & 3)

    rows: list[dict[str, str]] = []
    products = (
        ("Plane A", "staged_plane_a.bin"),
        ("Plane B", "staged_plane_b.bin"),
        ("collision", "collision_map.bin"),
    )
    counts: dict[str, int] = {}
    for product, filename in products:
        baseline = words(args.baseline / filename)
        candidate = words(args.candidate / filename)
        counts[product] = 0
        for cell, (before, after) in enumerate(zip(baseline, candidate)):
            if before == after:
                continue
            counts[product] += 1
            logical_row, logical_col = divmod(cell, 64)
            descriptor_0419 = record_0419 = descriptor_0421 = record_0421 = ""
            if product == "Plane A":
                live_pointer = int.from_bytes(
                    descriptor_state[(logical_row >> 2) * 4:(logical_row >> 2) * 4 + 4], "big")
                block = logical_col >> 2
                delta = block - (base_state["strip_group"] & 0x0f)
                if logical_col > front:
                    delta -= 16
                correct_desc = live_pointer + delta * 4

                block_start = logical_col & ~3
                grouped_delta = block - (base_state["strip_group"] & 0x0f)
                if block_start > front:
                    grouped_delta -= 16
                grouped_desc = live_pointer + grouped_delta * 4

                def record(desc: int) -> int:
                    pointer = int.from_bytes(rom[desc + 2:desc + 4], "big")
                    return int.from_bytes(record_index[pointer:pointer + 2], "big")

                descriptor_0419, record_0419 = f"0x{correct_desc:06X}", str(record(correct_desc))
                descriptor_0421, record_0421 = f"0x{grouped_desc:06X}", str(record(grouped_desc))
            rows.append({
                "product": product,
                "logical_row": str(logical_row),
                "logical_column": str(logical_col),
                "build0419": f"0x{before:04X}",
                "build0421": f"0x{after:04X}",
                "descriptor0419": descriptor_0419,
                "record0419": record_0419,
                "descriptor0421": descriptor_0421,
                "record0421": record_0421,
            })

    args.output.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0]) if rows else [
        "product", "logical_row", "logical_column", "build0419", "build0421",
        "descriptor0419", "record0419", "descriptor0421", "record0421"]
    with (args.output / "semantic_diff.tsv").open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "semantic_diff_summary.txt").write_text(
        f"matched_state=YES\n"
        f"plane_a_differing_words={counts['Plane A']}\n"
        f"plane_b_differing_words={counts['Plane B']}\n"
        f"collision_differing_words={counts['collision']}\n"
        f"first_difference={rows[0] if rows else 'NONE'}\n")


if __name__ == "__main__":
    main()
