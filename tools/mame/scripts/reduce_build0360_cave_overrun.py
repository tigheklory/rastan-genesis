#!/usr/bin/env python3
"""Reduce debugger events from the Build 0359 cave-overrun measurement."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

TOTAL_LINES = 262
VISIBLE_LINES = 224
HTOTAL = 488
DOTS_PER_FRAME = TOTAL_LINES * HTOTAL
HEX_FIELDS = {
    "pc", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
    "state0", "state2", "state4", "segment", "player_mode", "player_x",
    "player_y", "fg_x", "fg_y", "bg_x", "bg_y", "scene", "hud_count",
    "front_effect_count", "player_front_count", "middle_count",
    "player_body_count", "back_enemy_count", "tile_dma_count", "dropped_count",
}


def value(row: dict[str, str], name: str) -> int:
    return int(row[name], 16) if name in HEX_FIELDS else int(row[name])


def stamp(row: dict[str, str]) -> int:
    phase_line = (value(row, "beamy") - VISIBLE_LINES) % TOTAL_LINES
    return value(row, "screen_frame") * DOTS_PER_FRAME + phase_line * HTOTAL + value(row, "beamx")


def lines(dots: int) -> float:
    return dots / HTOTAL


def describe(values: list[int]) -> dict[str, int | float]:
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {
        "count": len(values),
        "min_lines": lines(ordered[0]),
        "median_lines": lines(round(statistics.median(ordered))),
        "p95_lines": lines(ordered[round((len(ordered) - 1) * 0.95)]),
        "max_lines": lines(ordered[-1]),
    }


COUNT_FIELDS = [
    "total_calls", "back_calls", "emitted", "back_emitted",
    "other_rejects", "back_other_rejects", "viewport_rejects",
    "back_viewport_rejects", "misses", "back_misses", "victim_iterations",
    "back_victim_iterations", "victim_loop_transitions",
    "back_victim_loop_transitions", "replacements", "back_replacements",
    "nofree_drops", "back_nofree_drops", "qfull_drops", "back_qfull_drops",
]
DOT_FIELDS = [
    "duration_dots", "back_lane_dots", "resident_hit_dots",
    "back_resident_hit_dots", "miss_hit_dots", "back_miss_hit_dots",
    "other_reject_dots", "back_other_reject_dots", "viewport_reject_dots",
    "back_viewport_reject_dots", "miss_drop_dots", "back_miss_drop_dots",
    "residency_work_dots", "back_residency_work_dots", "victim_search_dots",
    "back_victim_search_dots", "victim_loop_span_dots",
    "back_victim_loop_span_dots", "replacement_dots", "back_replacement_dots",
]


def new_record(row: dict[str, str], finalizer_id: int) -> dict[str, int]:
    record = {name: 0 for name in COUNT_FIELDS + DOT_FIELDS}
    record.update({
        "finalizer_id": finalizer_id,
        "screen_frame": value(row, "screen_frame"),
        "start_stamp": stamp(row),
        "start_beamy": value(row, "beamy"),
        "start_beamx": value(row, "beamx"),
        "d5_emitted": -1,
    })
    for name in (
        "state0", "state2", "state4", "segment", "player_mode", "player_x",
        "player_y", "fg_x", "fg_y", "bg_x", "bg_y", "scene", "hud_count",
        "front_effect_count", "player_front_count", "middle_count",
        "player_body_count", "back_enemy_count",
    ):
        record[name] = value(row, name)
    return record


def reduce_events(rows: list[dict[str, str]]) -> tuple[list[dict[str, int]], dict[str, int]]:
    records: list[dict[str, int]] = []
    event_counts: dict[str, int] = {}
    current: dict[str, int] | None = None
    entry: dict[str, int | bool] | None = None
    finalizer_id = 0
    back = False
    pending_back_start = 0

    def add(name: str, amount: int = 1) -> None:
        assert current is not None
        current[name] += amount
        if entry and entry["back"]:
            current["back_" + name] += amount

    for row in rows:
        event = row["event"]
        event_counts[event] = event_counts.get(event, 0) + 1
        now = stamp(row)
        if event == "BACK_START":
            back = True
            pending_back_start = now
            if current:
                current["back_start_stamp"] = now
        elif event == "BACK_END":
            if current:
                current["back_lane_dots"] = max(0, now - current.get("back_start_stamp", pending_back_start or now))
            back = False
            pending_back_start = 0
        elif event == "ENTRY_START":
            if not current:
                finalizer_id += 1
                current = new_record(row, finalizer_id)
                if back and pending_back_start:
                    current["back_start_stamp"] = pending_back_start
            entry = {
                "start": now, "back": back, "bbox": False, "reverse": False,
                "miss": False, "miss_stamp": 0, "victim_start": 0,
                "victim_end": 0, "last_victim_stamp": 0,
                "replacement_start": 0, "hit": False,
                "hit_stamp": 0,
            }
            current["total_calls"] += 1
            if back:
                current["back_calls"] += 1
        elif not current:
            continue
        elif not entry and event not in {"FINALIZER_DONE", "FINALIZER_RTS"}:
            continue
        elif event == "BBOX_START":
            entry["bbox"] = True
        elif event == "REVERSE_START":
            entry["reverse"] = True
        elif event == "REVERSE_MISS":
            if not entry["miss"]:
                entry["miss"] = True
                entry["miss_stamp"] = now
                add("misses")
        elif event == "VICTIM_LOOP":
            if not entry["victim_start"]:
                entry["victim_start"] = now
            if entry["last_victim_stamp"]:
                add("victim_loop_transitions")
                add("victim_loop_span_dots", max(0, now - int(entry["last_victim_stamp"])))
            entry["last_victim_stamp"] = now
            add("victim_iterations")
        elif event == "NO_FREE":
            entry["victim_end"] = now
            add("nofree_drops")
        elif event == "QUEUE_FULL":
            add("qfull_drops")
        elif event == "HIT":
            entry["hit"] = True
            entry["hit_stamp"] = now
        elif event == "ENTRY_RTS":
            elapsed = max(0, now - int(entry["start"]))
            if entry["hit"]:
                add("emitted")
                add("miss_hit_dots" if entry["miss"] else "resident_hit_dots", elapsed)
                if entry["miss"]:
                    add("replacements")
            elif entry["miss"]:
                add("miss_drop_dots", elapsed)
            elif entry["bbox"] and not entry["reverse"]:
                add("viewport_rejects")
                add("viewport_reject_dots", elapsed)
            else:
                add("other_rejects")
                add("other_reject_dots", elapsed)
            if entry["miss"]:
                end = int(entry["hit_stamp"]) or now
                add("residency_work_dots", max(0, end - int(entry["miss_stamp"])))
            if entry["victim_start"]:
                end = int(entry["victim_end"]) or now
                add("victim_search_dots", max(0, end - int(entry["victim_start"])))
            entry = None
        elif event == "FINALIZER_RTS":
            current["end_beamy"] = value(row, "beamy")
            current["end_beamx"] = value(row, "beamx")
            current["duration_dots"] = max(0, now - current["start_stamp"])
            current["d5_emitted"] = current["emitted"]
            records.append(current)
            current = None
            entry = None
            back = False
    return records, event_counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames-csv", type=Path)
    args = parser.parse_args()

    with args.input.open(newline="") as source:
        rows = list(csv.DictReader(source))
    records, event_counts = reduce_events(rows)
    gameplay = [r for r in records if r["state0"] == 2 and r["state2"] == 3]
    map_record1 = [r for r in gameplay if r["segment"] == 1]
    map_record2 = [r for r in gameplay if r["segment"] == 2]
    entrance_subset = [
        r for r in map_record1
        if 0x0169 <= r["fg_x"] <= 0x016F and 0x0105 <= r["fg_y"] <= 0x0149
    ]

    # In the completed Build 0359 capture, the first-cave stress interval begins
    # when the arcade-owned map-record field A5+0x013E advances 1 -> 2 at
    # external frame 1301. Record 2 remains active through the operator-confirmed
    # no-kill cave wait and hurry-up swarm until MAME exits. "Segment 1" in the
    # test-route name is not the numeric value of this map-record field.
    cave = map_record2

    result: dict[str, object] = {
        "source": str(args.input),
        "filter": {
            "state": "2/3",
            "arcade_map_record_a5_013e": 2,
            "start_external_frame": min((r["screen_frame"] for r in cave), default=None),
            "end_external_frame": max((r["screen_frame"] for r in cave), default=None),
            "semantic_region": "first-cave Segment-1 no-kill route",
            "workload": "operator-confirmed large bats, small bats, Lizardmen, and hurry-up swarm",
            "route_name_vs_map_record_note": (
                "Segment 1 is the named test route; A5+0x013E is map record 2 "
                "during the sustained cave interval"
            ),
        },
        "event_counts": event_counts,
        "rows": {"events": len(rows), "complete_finalizers": len(records),
                 "gameplay": len(gameplay), "map_record1": len(map_record1),
                 "map_record2": len(map_record2),
                 "entrance_coordinate_subset": len(entrance_subset),
                 "cave": len(cave)},
    }
    if not cave:
        result["classification"] = "NO_CAVE_ROWS"
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        return 2

    totals = {name: sum(r[name] for r in cave) for name in COUNT_FIELDS}
    result["totals"] = totals
    result["timing_totals"] = {
        name: {"dots": sum(r[name] for r in cave), "lines": lines(sum(r[name] for r in cave))}
        for name in DOT_FIELDS
    }
    result["distributions"] = {name: describe([r[name] for r in cave]) for name in DOT_FIELDS}
    worst = max(cave, key=lambda r: r["back_lane_dots"])
    result["worst_back_enemy_frame"] = {
        **{name: worst[name] for name in (
            "finalizer_id", "screen_frame", "segment", "player_mode", "player_x",
            "player_y", "fg_x", "fg_y", "bg_x", "bg_y", *COUNT_FIELDS, *DOT_FIELDS,
        )},
        "back_lane_lines": lines(worst["back_lane_dots"]),
    }
    result["derived"] = {
        "emitted_calls": totals["emitted"],
        "non_emitting_calls": totals["other_rejects"] + totals["viewport_rejects"]
                              + totals["nofree_drops"] + totals["qfull_drops"],
        "call_accounting_delta": totals["total_calls"] - totals["emitted"]
                                 - totals["other_rejects"] - totals["viewport_rejects"]
                                 - totals["nofree_drops"] - totals["qfull_drops"],
        "back_call_accounting_delta": totals["back_calls"] - totals["back_emitted"]
                                      - totals["back_other_rejects"]
                                      - totals["back_viewport_rejects"]
                                      - totals["back_nofree_drops"]
                                      - totals["back_qfull_drops"],
        "resident_hit_lines_per_call": lines(sum(r["resident_hit_dots"] for r in cave))
                                       / max(1, totals["emitted"] - totals["replacements"]),
        "back_resident_hit_lines_per_call": lines(sum(r["back_resident_hit_dots"] for r in cave))
                                            / max(1, totals["back_emitted"]
                                                  - totals["back_replacements"]),
        "viewport_reject_lines_per_call": lines(sum(r["viewport_reject_dots"] for r in cave))
                                          / max(1, totals["viewport_rejects"]),
        "back_viewport_reject_lines_per_call": lines(sum(r["back_viewport_reject_dots"] for r in cave))
                                               / max(1, totals["back_viewport_rejects"]),
        "victim_loop_lines_per_observed_transition": (
            lines(sum(r["victim_loop_span_dots"] for r in cave))
            / max(1, totals["victim_loop_transitions"])
        ),
        "back_victim_loop_lines_per_observed_transition": (
            lines(sum(r["back_victim_loop_span_dots"] for r in cave))
            / max(1, totals["back_victim_loop_transitions"])
        ),
    }
    reject_dots = sum(r["back_other_reject_dots"] + r["back_viewport_reject_dots"] for r in cave)
    residency_dots = sum(r["back_residency_work_dots"] for r in cave)
    back_rejects = totals["back_other_rejects"] + totals["back_viewport_rejects"]
    if reject_dots > residency_dots and back_rejects > totals["back_emitted"]:
        target = "EARLY REJECTION"
    elif residency_dots > reject_dots and totals["back_misses"] > 0:
        target = "RESIDENCY MISS PATH"
    else:
        target = "STAGE DISPATCH"
    result["next_implementation_target"] = target
    result["target_basis"] = {
        "back_reject_lines": lines(reject_dots),
        "back_residency_work_lines": lines(residency_dots),
        "back_reject_calls": back_rejects,
        "back_emitted_calls": totals["back_emitted"],
        "back_misses": totals["back_misses"],
    }

    if args.frames_csv:
        fields = list(cave[0])
        with args.frames_csv.open("w", newline="") as destination:
            writer = csv.DictWriter(destination, fieldnames=fields)
            writer.writeheader()
            writer.writerows(cave)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
