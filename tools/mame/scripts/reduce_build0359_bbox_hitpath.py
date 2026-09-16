#!/usr/bin/env python3
"""Reduce Build 0359 native-entry brackets using physical beam positions."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

TOTAL_LINES = 262
VISIBLE_LINES = 224
HTOTAL = 488
DOTS_PER_FRAME = TOTAL_LINES * HTOTAL


def describe(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {
        "count": len(values),
        "min_lines": min(values) / HTOTAL,
        "median_lines": statistics.median(values) / HTOTAL,
        "p95_lines": ordered[round((len(ordered) - 1) * 0.95)] / HTOTAL,
        "max_lines": max(values) / HTOTAL,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.input.open(newline="") as source:
        rows = list(csv.DictReader(source))
    for sequence, row in enumerate(rows):
        phase_line = (int(row["beamy"]) - VISIBLE_LINES) % TOTAL_LINES
        row["_stamp"] = (int(row["screen_frame"]) * DOTS_PER_FRAME +
                         phase_line * HTOTAL + int(row["beamx"]))
        row["_sequence"] = sequence
    rows.sort(key=lambda item: (item["_stamp"], item["_sequence"]))

    by_entry: dict[int, dict[str, dict]] = defaultdict(dict)
    by_finalizer: dict[int, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        entry = int(row["entry_id"])
        finalizer = int(row["finalizer_id"])
        if entry:
            by_entry[entry][row["event"]] = row
        if finalizer:
            by_finalizer[finalizer][row["event"]] = row

    records = []
    for entry, events in by_entry.items():
        required = {"ENTRY_START", "BBOX_START", "BBOX_ORIENT_END",
                    "REVERSE_START", "HIT_START", "ENTRY_RTS"}
        if not required.issubset(events) or "REVERSE_MISS" in events:
            continue
        start = events["ENTRY_START"]
        record = {
            "entry_id": entry,
            "finalizer_id": int(start["finalizer_id"]),
            "host_frame": int(start["host_frame"]),
            "screen_frame": int(start["screen_frame"]),
            "state0": int(start["state0"], 16),
            "state2": int(start["state2"], 16),
            "pre_bbox": events["BBOX_START"]["_stamp"] - start["_stamp"],
            "bbox_orientation": (events["BBOX_ORIENT_END"]["_stamp"] -
                                 events["BBOX_START"]["_stamp"]),
            "bbox_viewport_tail": (events["REVERSE_START"]["_stamp"] -
                                   events["BBOX_ORIENT_END"]["_stamp"]),
            "reverse_hit_lookup": (events["HIT_START"]["_stamp"] -
                                   events["REVERSE_START"]["_stamp"]),
            "sat_emit": (events["ENTRY_RTS"]["_stamp"] -
                         events["HIT_START"]["_stamp"]),
            "complete_hit_entry": events["ENTRY_RTS"]["_stamp"] - start["_stamp"],
        }
        records.append(record)

    # Frontend sprite entries share the finalizer but are outside this task's
    # gameplay cost model.  Keep only the established scene/stage 2/3 state.
    records = [record for record in records
               if record["state0"] == 2 and record["state2"] == 3]

    metrics = ("pre_bbox", "bbox_orientation", "bbox_viewport_tail",
               "reverse_hit_lookup", "sat_emit", "complete_hit_entry")
    scenarios = {
        "global": records,
        "stationary": [r for r in records if 407 <= r["screen_frame"] <= 699],
        "horizontal": [r for r in records if 700 <= r["screen_frame"] <= 897],
        "vertical_jump": [r for r in records if 1000 <= r["screen_frame"] <= 1399],
    }
    result = {
        "source": str(args.input),
        "physical_beam": {"total_lines": TOTAL_LINES, "htotal": HTOTAL},
        "event_counts": {name: sum(row["event"] == name for row in rows)
                         for name in sorted({row["event"] for row in rows})},
        "complete_reverse_hit_entries": len(records),
        "scenarios": {
            name: {metric: describe([record[metric] for record in selected])
                   for metric in metrics}
            for name, selected in scenarios.items()
        },
    }

    finalizers = []
    for finalizer, events in by_finalizer.items():
        if {"FINALIZER_ENTRY", "FINALIZER_DONE", "FINALIZER_RTS"}.issubset(events):
            finalizers.append({
                "id": finalizer,
                "screen_frame": int(events["FINALIZER_ENTRY"]["screen_frame"]),
                "emitted": int(events["FINALIZER_DONE"]["d5"], 16),
                "duration": events["FINALIZER_RTS"]["_stamp"] - events["FINALIZER_ENTRY"]["_stamp"],
                "state0": int(events["FINALIZER_ENTRY"]["state0"], 16),
                "state2": int(events["FINALIZER_ENTRY"]["state2"], 16),
            })
    finalizers = [item for item in finalizers
                  if item["state0"] == 2 and item["state2"] == 3]
    if finalizers:
        threshold = sorted(item["emitted"] for item in finalizers)[round((len(finalizers) - 1) * 0.9)]
        heavy = [item for item in finalizers if item["emitted"] >= threshold]
        result["finalizers"] = {
            "count": len(finalizers),
            "duration": describe([item["duration"] for item in finalizers]),
            "sprite_heavy_threshold": threshold,
            "sprite_heavy_duration": describe([item["duration"] for item in heavy]),
            "worst": max(finalizers, key=lambda item: item["duration"]),
        }

    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
