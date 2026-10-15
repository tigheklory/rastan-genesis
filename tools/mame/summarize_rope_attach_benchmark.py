#!/usr/bin/env python3
"""Summarize deterministic MAME rope-attachment benchmark trials."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build", required=True)
    args = parser.parse_args()

    with args.trials.open(newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    if not rows or any(row["result"] != "PASS" for row in rows):
        raise SystemExit("rope benchmark FAIL: one or more trials did not attach")

    frames = [int(row["elapsed_frames"]) for row in rows]
    milliseconds = [float(row["elapsed_milliseconds"]) for row in rows]
    lines = [
        f"build={args.build}",
        f"trials={len(rows)}",
        "elapsed_frames=" + ",".join(map(str, frames)),
        f"median_frames={statistics.median(frames):g}",
        f"min_frames={min(frames)}",
        f"max_frames={max(frames)}",
        f"median_milliseconds={statistics.median(milliseconds):.3f}",
        f"min_milliseconds={min(milliseconds):.3f}",
        f"max_milliseconds={max(milliseconds):.3f}",
        f"deterministic={'YES' if len(set(frames)) == 1 else 'NO'}",
    ]
    args.output.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
