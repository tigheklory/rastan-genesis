#!/usr/bin/env python3
"""Reduce the Build 0356 full IRQ6/VBlank-chain physical-beam trace."""

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

TOTAL_LINES = 262
HTOTAL = 488
VISIBLE_LINES = 224
VBLANK_LINES = TOTAL_LINES - VISIBLE_LINES
# On MAME 0.276's NTSC Genesis screen, VDP V-counter E0 is observed at screen
# beam Y=186. The screen frame counter itself advances at a different phase.
VINT_SCREEN_Y = 186
DOTS_PER_FRAME = TOTAL_LINES * HTOTAL
VINT_PHASE = ((VINT_SCREEN_Y - VISIBLE_LINES) % TOTAL_LINES) * HTOTAL
REFRESH_HZ = 59.922743404312
CPU_HZ = 7_670_453


def stamp(row):
    return row["_stamp"]


def latest_vint_boundary(absolute_stamp):
    epoch = (absolute_stamp - VINT_PHASE) // DOTS_PER_FRAME
    return epoch * DOTS_PER_FRAME + VINT_PHASE


def describe(values):
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {
        "count": len(values),
        "min_dots": min(values),
        "median_dots": statistics.median(values),
        "p95_dots": ordered[round((len(ordered) - 1) * 0.95)],
        "max_dots": max(values),
    }


def convert(dots):
    return {
        "dots": dots,
        "scanlines": dots / HTOTAL,
        "microseconds": dots / (REFRESH_HZ * DOTS_PER_FRAME) * 1_000_000,
        "equivalent_68k_cycles": dots * CPU_HZ / (REFRESH_HZ * DOTS_PER_FRAME),
    }


def event_delta(events, start, end):
    if start not in events or end not in events:
        return None
    return stamp(events[end][-1]) - stamp(events[start][0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--host-frames", type=int, default=1800)
    args = parser.parse_args()

    rows = []
    with args.input.open(newline="") as source:
        for line in source:
            if line.startswith("event,"):
                rows = [row for row in csv.DictReader([line] + list(source))
                        if row.get("event") and row["event"] != "META"]
                break
    timed_rows = [row for row in rows
                  if int(row["beamy"]) >= 0 and int(row["beamx"]) >= 0]
    for sequence, row in enumerate(timed_rows):
        phase_line = (int(row["beamy"]) - VISIBLE_LINES) % TOTAL_LINES
        row["_stamp"] = (int(row["frame"]) * DOTS_PER_FRAME +
                         phase_line * HTOTAL + int(row["beamx"]))
        row["_sequence"] = sequence
    timed_rows.sort(key=lambda row: (stamp(row), row["_sequence"]))

    chains = []
    current = None
    prior_rte = None
    interrupted_pcs = Counter()
    for row in timed_rows:
        event = row["event"]
        if event == "IRQ6_SERVICE_ENTRY":
            if current is not None:
                current["complete"] = False
                chains.append(current)
            current = {"events": {}, "complete": False, "prior_rte": prior_rte}
            interrupted_pcs[row["stack_pc"].upper()] += 1
        if current is not None:
            current["events"].setdefault(event, []).append(row)
        if event == "ARCADE_RTE":
            prior_rte = row
            if current is not None:
                current["complete"] = True
                chains.append(current)
                current = None
    if current is not None:
        chains.append(current)

    records = []
    segments = [
        ("save_to_input", "IRQ6_SERVICE_ENTRY", "INPUT_ENTRY"),
        ("input", "INPUT_ENTRY", "PREPARE_ENTRY"),
        ("prepare", "PREPARE_ENTRY", "PUBLISH_CALL_SITE"),
        ("publisher", "PUBLISH_ENTRY", "PUBLISH_RTS"),
        ("publish_call_overhead", "PUBLISH_CALL_SITE", "PUBLISH_ENTRY"),
        ("publish_return_overhead", "PUBLISH_RTS", "PUBLISH_RETURN"),
        ("native_tail", "PUBLISH_RETURN", "ARCADE_IRQ_ENTRY"),
        ("arcade_prefix", "ARCADE_IRQ_ENTRY", "ARCADE_PREFIX_END"),
        ("arcade_3ad7c", "ARCADE_PREFIX_END", "ARCADE_3AD7C_END"),
        ("arcade_3ade2", "ARCADE_3AD7C_END", "ARCADE_3ADE2_END"),
        ("arcade_3a2a8", "ARCADE_3ADE2_END", "ARCADE_3A2A8_END"),
        ("arcade_3f0fa", "ARCADE_3A2A8_END", "ARCADE_3F0FA_END"),
        ("arcade_3f15c", "ARCADE_3F0FA_END", "ARCADE_DISPATCH_ENTRY"),
        ("arcade_state_dispatch", "ARCADE_DISPATCH_ENTRY", "ARCADE_DISPATCH_RETURN"),
        ("arcade_tail_call", "ARCADE_DISPATCH_RETURN", "ARCADE_TAIL_CALL_RETURN"),
        ("arcade_mask_to_rte", "ARCADE_TAIL_CALL_RETURN", "ARCADE_RTE"),
        ("arcade_optional", "ARCADE_OPTIONAL_CALL", "ARCADE_OPTIONAL_RETURN"),
        ("arcade_update", "ARCADE_UPDATE_CALL", "ARCADE_PREFIX_END"),
        ("update_55b96", "UPDATE_42130_ENTRY", "UPDATE_55B96_END"),
        ("update_45f72", "UPDATE_55B96_END", "UPDATE_45F72_END"),
        ("update_5996e", "UPDATE_45F72_END", "UPDATE_5996E_END"),
        ("update_59964", "UPDATE_5996E_END", "UPDATE_59964_END"),
        ("update_47204", "UPDATE_59964_END", "UPDATE_47204_END"),
        ("update_frame_begin", "UPDATE_47204_END", "UPDATE_FRAME_BEGIN_END"),
        ("update_player", "UPDATE_FRAME_BEGIN_END", "UPDATE_PLAYER_END"),
        ("gameplay_core_51210", "GAMEPLAY_CORE_ENTRY", "CORE_51210_END"),
        ("gameplay_core_40d66", "CORE_51210_END", "CORE_40D66_END"),
        ("gameplay_core_422e6", "CORE_40D66_END", "CORE_422E6_END"),
        ("gameplay_core_445e0", "CORE_422E6_END", "CORE_445E0_END"),
        ("gameplay_core_44bb4", "CORE_445E0_END", "CORE_44BB4_END"),
        ("gameplay_core_452d8", "CORE_44BB4_END", "CORE_452D8_END"),
        ("gameplay_core_4a1a6", "CORE_452D8_END", "CORE_4A1A6_END"),
        ("native_41dae", "NATIVE_41DAE_ENTRY", "NATIVE_41DAE_RTS"),
        ("native_stage_dispatch", "NATIVE_STAGE41_ENTRY", "NATIVE_STAGE41_RTS"),
        ("native_finalizer", "NATIVE_FINALIZER_ENTRY", "NATIVE_FINALIZER_RTS"),
        ("native_finalizer_route", "NATIVE_FINALIZER_ENTRY", "NATIVE_GAMEPLAY_ENTRY"),
        ("native_gameplay_setup", "NATIVE_GAMEPLAY_ENTRY", "NATIVE_LANE_HUD"),
        ("native_lane_hud", "NATIVE_LANE_HUD", "NATIVE_LANE_FRONT_EFFECT"),
        ("native_lane_front_effect", "NATIVE_LANE_FRONT_EFFECT", "NATIVE_LANE_PLAYER_FRONT"),
        ("native_lane_player_front", "NATIVE_LANE_PLAYER_FRONT", "NATIVE_LANE_MIDDLE"),
        ("native_lane_middle", "NATIVE_LANE_MIDDLE", "NATIVE_LANE_PLAYER_BODY"),
        ("native_lane_player_body", "NATIVE_LANE_PLAYER_BODY", "NATIVE_LANE_BACK_ENEMY"),
        ("native_lane_back_enemy", "NATIVE_LANE_BACK_ENEMY", "NATIVE_GAMEOVER_ENTRY"),
        ("native_gameover", "NATIVE_GAMEOVER_ENTRY", "NATIVE_DONE_SCAN"),
        ("native_finalizer_bookkeeping", "NATIVE_DONE_SCAN", "NATIVE_FINALIZER_RTS"),
    ]
    for chain in chains:
        events = chain["events"]
        if "IRQ6_SERVICE_ENTRY" not in events:
            continue
        entry = events["IRQ6_SERVICE_ENTRY"][0]
        record = {
            "_entry_stamp": stamp(entry),
            "entry_frame": int(entry["frame"]),
            "entry_y": int(entry["beamy"]),
            "entry_x": int(entry["beamx"]),
            "entry_sr": int(entry["sr"], 16),
            "entry_ipm": int(entry["ipm"]),
            "entry_vcounter": int(entry["hvc"], 16) >> 8,
            "entry_hcounter": int(entry["hvc"], 16) & 0xFF,
            "interrupted_sr": int(entry["stack_sr"], 16),
            "interrupted_pc": int(entry["stack_pc"], 16),
            "state": [int(entry[key], 16) for key in ("state0", "state2", "state4")],
            "scene": int(entry["scene"], 16),
            "complete": chain["complete"],
        }
        for name, start, end in segments:
            record[name] = event_delta(events, start, end)
        record["prepublication"] = event_delta(events, "IRQ6_SERVICE_ENTRY", "PUBLISH_ENTRY")
        record["arcade_tick"] = event_delta(events, "ARCADE_IRQ_ENTRY", "ARCADE_RTE")
        record["full_chain"] = event_delta(events, "IRQ6_SERVICE_ENTRY", "ARCADE_RTE")
        record["publication_entry_y"] = (int(events["PUBLISH_ENTRY"][0]["beamy"])
                                         if "PUBLISH_ENTRY" in events else None)
        publisher = events.get("PUBLISH_ENTRY", [None])[0]
        record["publication_entry_vcounter"] = (int(publisher["hvc"], 16) >> 8
                                                  if publisher else None)
        count_events = {
            "native_hud_count": "NATIVE_LANE_HUD",
            "native_front_effect_count": "NATIVE_LANE_FRONT_EFFECT",
            "native_player_front_count": "NATIVE_LANE_PLAYER_FRONT",
            "native_middle_count": "NATIVE_LANE_MIDDLE",
            "native_player_body_count": "NATIVE_LANE_PLAYER_BODY",
            "native_back_enemy_count": "NATIVE_LANE_BACK_ENEMY",
            "native_emitted_count": "NATIVE_DONE_SCAN",
        }
        for field, event_name in count_events.items():
            event_rows = events.get(event_name)
            record[field] = int(event_rows[0]["value"], 16) if event_rows else None
        boundary = latest_vint_boundary(stamp(entry))
        record["dots_since_vint_boundary"] = stamp(entry) - boundary
        record["service_in_active_display"] = (
            record["dots_since_vint_boundary"] >= VBLANK_LINES * HTOTAL)
        record["publisher_in_active_display"] = False
        if publisher:
            publisher_boundary = latest_vint_boundary(stamp(publisher))
            record["publisher_in_active_display"] = (
                stamp(publisher) - publisher_boundary >= VBLANK_LINES * HTOTAL)
        prior = chain["prior_rte"]
        record["dots_from_prior_rte"] = stamp(entry) - stamp(prior) if prior else None
        record["prior_rte_after_boundary"] = bool(prior and stamp(prior) > boundary)
        record["service_period"] = None
        if not chain["complete"]:
            record["case"] = "E_INCOMPLETE"
        elif record["service_in_active_display"] and record["prior_rte_after_boundary"]:
            record["case"] = "C_MASKED_CONTINUATION"
        elif record["service_in_active_display"]:
            record["case"] = "E_ACTIVE_UNATTRIBUTED"
        elif record["publisher_in_active_display"]:
            record["case"] = "B_PREPUBLICATION_DELAY"
        elif not record["service_in_active_display"]:
            record["case"] = "A_SERVICE_AND_PUBLISH_IN_VBLANK"
        else:
            record["case"] = "D_ACTIVE_UNATTRIBUTED"
        records.append(record)

    for prior, current in zip(records, records[1:]):
        current["service_period"] = current["_entry_stamp"] - prior["_entry_stamp"]

    complete = [record for record in records if record["complete"]]
    gameplay = [record for record in complete if record["state"] == [2, 3, 0]]
    reg1 = [row for row in rows if row["event"] == "VDP_REG1_WRITE"]
    reg1_values = Counter(row["value"].upper() for row in reg1)
    reg1_vint_off = [row for row in reg1 if (int(row["value"], 16) & 0x20) == 0]

    finalizer_pairs = [(record["native_emitted_count"], record["native_finalizer"])
                       for record in gameplay
                       if record.get("native_emitted_count") is not None
                       and record.get("native_finalizer") is not None]
    grouped_finalizer = {}
    for emitted in sorted({pair[0] for pair in finalizer_pairs}):
        values = [duration for count, duration in finalizer_pairs if count == emitted]
        grouped_finalizer[str(emitted)] = describe(values)
    finalizer_correlation = None
    if len(finalizer_pairs) >= 2 and len({pair[0] for pair in finalizer_pairs}) >= 2:
        finalizer_correlation = statistics.correlation(
            [pair[0] for pair in finalizer_pairs],
            [pair[1] for pair in finalizer_pairs])

    measured_names = [name for name, _, _ in segments] + ["prepublication", "arcade_tick", "full_chain"]
    result = {
        "constants": {
            "total_lines": TOTAL_LINES,
            "visible_lines": VISIBLE_LINES,
            "vblank_lines": VBLANK_LINES,
            "vint_screen_y": VINT_SCREEN_Y,
            "htotal": HTOTAL,
            "dots_per_frame": DOTS_PER_FRAME,
            "refresh_hz": REFRESH_HZ,
            "cpu_hz": CPU_HZ,
        },
        "host_frames": args.host_frames,
        "event_counts": dict(Counter(row["event"] for row in rows)),
        "chain_count": len(records),
        "complete_chain_count": len(complete),
        "gameplay_chain_count": len(gameplay),
        "frames_without_service": args.host_frames - len(records),
        "case_counts": dict(Counter(record["case"] for record in complete)),
        "gameplay_case_counts": dict(Counter(record["case"] for record in gameplay)),
        "service_active_display_count": sum(record["service_in_active_display"] for record in gameplay),
        "publisher_active_display_count": sum(record["publisher_in_active_display"] for record in gameplay),
        "interrupted_ipm_histogram": dict(Counter(
            (record["interrupted_sr"] >> 8) & 7 for record in gameplay)),
        "service_vcounter_histogram": dict(Counter(
            record["entry_vcounter"] for record in gameplay)),
        "service_period": describe([record["service_period"] for record in gameplay
                                    if record["service_period"] is not None]),
        "distributions": {name: describe([record[name] for record in gameplay if record[name] is not None])
                          for name in measured_names},
        "converted_medians": {name: convert(statistics.median(
            record[name] for record in gameplay if record[name] is not None))
            for name in measured_names if any(record[name] is not None for record in gameplay)},
        "worst_complete_chain": max(gameplay, key=lambda record: record["full_chain"] or -1,
                                    default=None),
        "interrupted_pc_histogram": interrupted_pcs.most_common(30),
        "vdp_reg1": {
            "count": len(reg1),
            "values": dict(reg1_values),
            "vint_disabled_count": len(reg1_vint_off),
        },
        "native_sprite_counts": {
            field: describe([record[field] for record in gameplay
                             if record.get(field) is not None])
            for field in (
                "native_hud_count", "native_front_effect_count",
                "native_player_front_count", "native_middle_count",
                "native_player_body_count", "native_back_enemy_count",
                "native_emitted_count")
        },
        "native_finalizer_by_emitted_count": grouped_finalizer,
        "native_emitted_count_finalizer_correlation": finalizer_correlation,
    }
    args.json.write_text(json.dumps(result, indent=2) + "\n")

    fields = [
        "entry_frame", "entry_y", "entry_x", "state", "scene", "case",
        "service_in_active_display", "publisher_in_active_display",
        "entry_vcounter", "entry_hcounter", "publication_entry_vcounter",
        "dots_since_vint_boundary", "prior_rte_after_boundary",
        "dots_from_prior_rte", "service_period",
        "prepublication", "publisher", "arcade_tick", "arcade_state_dispatch", "full_chain",
        "interrupted_pc", "interrupted_sr", "entry_sr", "complete",
        "native_hud_count", "native_front_effect_count",
        "native_player_front_count", "native_middle_count",
        "native_player_body_count", "native_back_enemy_count",
        "native_emitted_count",
    ]
    with args.csv.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key) for key in fields})


if __name__ == "__main__":
    main()
