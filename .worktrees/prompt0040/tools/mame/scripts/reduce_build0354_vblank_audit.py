#!/usr/bin/env python3
"""Reduce the read-only Build 0354 debugger event stream."""

import argparse
import csv
import json
import statistics
from pathlib import Path

TOTAL_LINES = 262
HTOTAL = 488
REFRESH_HZ = 59.922743404312
CPU_HZ = 7_670_453
DOTS_PER_FRAME = TOTAL_LINES * HTOTAL
SECONDS_PER_DOT = 1.0 / (REFRESH_HZ * DOTS_PER_FRAME)
CYCLES_PER_DOT = CPU_HZ * SECONDS_PER_DOT


def stamp(row):
    return row["_stamp"]


def delta(events, start, end):
    starts = events.get(start, [])
    ends = events.get(end, [])
    if not starts or not ends:
        return 0
    return stamp(ends[-1]) - stamp(starts[0])


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return 0
    return values[round((len(values) - 1) * fraction)]


def describe(values):
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min_dots": min(values),
        "median_dots": statistics.median(values),
        "p95_dots": percentile(values, 0.95),
        "max_dots": max(values),
    }


def convert(dots):
    return {
        "dots": dots,
        "scanlines": dots / HTOTAL,
        "microseconds": dots * SECONDS_PER_DOT * 1_000_000,
        "equivalent_68k_cycles": dots * CYCLES_PER_DOT,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--right-start", type=int, default=700)
    parser.add_argument("--jump-start", type=int, default=1000)
    parser.add_argument("--jump-end", type=int, default=1400)
    args = parser.parse_args()

    rows = []
    with args.input.open(newline="") as source:
        for line in source:
            if line.startswith("META,"):
                continue
            if line.startswith("event,"):
                reader = csv.DictReader([line] + list(source))
                rows.extend(row for row in reader if row.get("event") and row["event"] != "META")
                break

    publications = []
    current = None
    for row in rows:
        if row["event"] == "PUB_ENTRY":
            current = {"events": {}, "beam_epoch": 0, "prior_beam": None}
        if current is None:
            continue
        beam = int(row["beamy"]) * HTOTAL + int(row["beamx"])
        if current["prior_beam"] is not None and beam < current["prior_beam"]:
            current["beam_epoch"] += DOTS_PER_FRAME
        row["_stamp"] = current["beam_epoch"] + beam
        current["prior_beam"] = beam
        current["events"].setdefault(row["event"], []).append(row)
        if row["event"] != "PUB_EXIT":
            continue

        events = current["events"]
        entry = events["PUB_ENTRY"][0]
        sprite = events.get("SPRITE_ENTRY", [entry])[0]
        frame = int(entry["frame"])
        state = tuple(int(entry[key], 16) for key in ("state0", "state2", "state4"))
        component_pairs = {
            "palette": ("PALETTE_ENTRY", "PALETTE_END_MARK1_START"),
            "tiles": ("TILES_ENTRY", "TILES_END_MARK2_START"),
            "plane_b": ("PLANE_B_ENTRY", "PLANE_B_END_MARK3_START"),
            "plane_a": ("PLANE_A_ENTRY", "PLANE_A_END_MARK4_START"),
            "sprite": ("SPRITE_ENTRY", "SPRITE_END_MARK5_START"),
            "scroll": ("SCROLL_ENTRY", "SCROLL_END_MARK6_START"),
            "sprite_tile": ("SPRITE_TILE_ENTRY", "SPRITE_TILE_END"),
            "sprite_palette": ("SPRITE_PALETTE_ENTRY", "SPRITE_PALETTE_END"),
            "sprite_sat": ("SPRITE_SAT_ENTRY", "SPRITE_SAT_END"),
        }
        record = {
            "frame": frame,
            "state": state,
            "entry_v": int(entry["beamy"]),
            "exit_v": int(events["PUB_EXIT"][-1]["beamy"]),
            "total": delta(events, "PUB_ENTRY", "PUB_EXIT"),
            "worklist_count": int(sprite["worklist_count"], 16),
            "emitted_count": int(sprite["emitted_count"], 16),
            "frame_ready": int(sprite["frame_ready"], 16),
            "actual_dma": len(events.get("PATTERN_DMA_CALL", [])),
        }
        for name, pair in component_pairs.items():
            record[name] = delta(events, *pair)
        record["canceled"] = max(0, record["worklist_count"] - record["actual_dma"])
        calls = events.get("PATTERN_DMA_CALL", [])
        record["unique_codes"] = len({int(row["d6"], 16) for row in calls})
        record["unique_slots"] = len({int(row["d4"], 16) for row in calls})
        record["codes"] = [int(row["d6"], 16) for row in calls]
        record["slots"] = [int(row["d4"], 16) for row in calls]
        record["pattern_bytes"] = record["actual_dma"] * 128
        record["sat_bytes"] = 640 if events.get("SPRITE_SAT_ENTRY") else 0
        record["sprite_other"] = max(0, record["sprite"] - record["sprite_tile"] - record["sprite_palette"] - record["sprite_sat"])
        marker_pairs = [
            ("MARK0_START", "MARK0_END"),
            ("PALETTE_END_MARK1_START", "MARK1_END"),
            ("TILES_END_MARK2_START", "MARK2_END"),
            ("PLANE_B_END_MARK3_START", "MARK3_END"),
            ("PLANE_A_END_MARK4_START", "MARK4_END"),
            ("SPRITE_END_MARK5_START", "MARK5_END"),
            ("SCROLL_END_MARK6_START", "MARK6_END"),
        ]
        record["markers"] = sum(delta(events, *pair) for pair in marker_pairs)
        record["dma_intervals"] = []
        for start, end in zip(events.get("PATTERN_DMA_CALL", []), events.get("PATTERN_DMA_END", [])):
            record["dma_intervals"].append({
                "dots": stamp(end) - stamp(start),
                "start_frame": int(start["frame"]), "start_v": int(start["beamy"]),
                "end_frame": int(end["frame"]), "end_v": int(end["beamy"]),
            })
        publications.append(record)
        current = None

    gameplay = [p for p in publications if p["state"] == (2, 3, 0)]
    categories = {
        "stationary": [p for p in gameplay if p["frame"] < args.right_start],
        "horizontal": [p for p in gameplay if args.right_start <= p["frame"] < args.jump_start],
        "vertical": [p for p in gameplay if args.jump_start <= p["frame"] < args.jump_end],
        "horizontal_late": [p for p in gameplay if p["frame"] >= args.jump_end],
    }

    def median_record(records):
        if not records:
            return None
        target = statistics.median(p["total"] for p in records)
        return min(records, key=lambda p: abs(p["total"] - target))

    representatives = {name: median_record(records) for name, records in categories.items()}
    vertical_rows = [p for p in categories["vertical"] if p["plane_a"] > 1000]
    representatives["vertical"] = median_record(vertical_rows or categories["vertical"])
    representatives["sprite_heavy"] = max(gameplay, key=lambda p: (p["sprite"], p["actual_dma"]), default=None)
    representatives["worst"] = max(gameplay, key=lambda p: p["total"], default=None)

    all_dma = [interval for p in gameplay for interval in p["dma_intervals"]]
    vblank_dma = [x["dots"] for x in all_dma if x["start_v"] >= 224]
    active_dma = [x["dots"] for x in all_dma if x["start_v"] < 224]
    marker_values = [p["markers"] for p in gameplay]

    consecutive_reuploads = 0
    prior_codes = set()
    for p in sorted(gameplay, key=lambda item: item["frame"]):
        codes = set(p["codes"])
        if codes & prior_codes:
            consecutive_reuploads += len(codes & prior_codes)
        prior_codes = codes

    result = {
        "constants": {
            "total_lines": TOTAL_LINES, "htotal": HTOTAL, "refresh_hz": REFRESH_HZ,
            "cpu_hz": CPU_HZ, "seconds_per_dot": SECONDS_PER_DOT,
            "cycles_per_dot": CYCLES_PER_DOT,
            "frame_time_us": 1_000_000 / REFRESH_HZ,
            "scanline_time_us": 1_000_000 / REFRESH_HZ / TOTAL_LINES,
            "vblank_time_us": 38 * 1_000_000 / REFRESH_HZ / TOTAL_LINES,
            "vblank_equivalent_cycles": 38 * CPU_HZ / REFRESH_HZ / TOTAL_LINES,
        },
        "publication_count": len(publications),
        "gameplay_publication_count": len(gameplay),
        "category_counts": {name: len(records) for name, records in categories.items()},
        "representatives": {},
        "gameplay_distributions": {key: describe([p[key] for p in gameplay]) for key in
            ("total", "palette", "tiles", "plane_b", "plane_a", "sprite", "scroll",
             "sprite_tile", "sprite_palette", "sprite_sat", "sprite_other", "markers")},
        "worklist": {
            "count": describe([p["worklist_count"] for p in gameplay]),
            "actual": describe([p["actual_dma"] for p in gameplay]),
            "canceled": describe([p["canceled"] for p in gameplay]),
            "pattern_bytes": describe([p["pattern_bytes"] for p in gameplay]),
            "emitted_count": describe([p["emitted_count"] for p in gameplay]),
            "frames_with_duplicate_codes": sum(1 for p in gameplay if p["actual_dma"] != p["unique_codes"]),
            "frames_with_duplicate_slots": sum(1 for p in gameplay if p["actual_dma"] != p["unique_slots"]),
            "consecutive_frame_code_reuploads": consecutive_reuploads,
        },
        "dma_duration": {"vblank": describe(vblank_dma), "active": describe(active_dma)},
        "marker_total": describe(marker_values),
    }
    for name, record in representatives.items():
        if record is None:
            result["representatives"][name] = None
            continue
        result["representatives"][name] = {
            key: record[key] for key in (
                "frame", "state", "entry_v", "exit_v", "total", "palette", "tiles", "plane_b", "plane_a",
                "sprite", "scroll", "sprite_tile", "sprite_palette", "sprite_sat", "sprite_other", "markers",
                "worklist_count", "actual_dma", "canceled", "unique_codes", "unique_slots", "pattern_bytes",
                "emitted_count", "sat_bytes")
        }
        result["representatives"][name]["converted"] = {
            key: convert(record[key]) for key in
            ("total", "palette", "tiles", "plane_b", "plane_a", "sprite", "scroll",
             "sprite_tile", "sprite_palette", "sprite_sat", "sprite_other", "markers")
        }

    args.json.write_text(json.dumps(result, indent=2) + "\n")
    with args.csv.open("w", newline="") as target:
        fields = ["name", "frame", "entry_v", "exit_v", "palette", "tiles", "plane_b", "plane_a", "sprite", "scroll", "total", "worklist_count", "actual_dma", "canceled", "pattern_bytes", "emitted_count"]
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for name, record in representatives.items():
            if record:
                row = {key: record.get(key, "") for key in fields}
                row["name"] = name
                writer.writerow(row)


if __name__ == "__main__":
    main()
