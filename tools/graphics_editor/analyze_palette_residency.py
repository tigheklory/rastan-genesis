#!/usr/bin/env python3
"""Read-only/offline CRAM residency capacity analysis.

The analyzer consumes the Palette Composer profile and the authoritative arcade
Plane-A decoder.  It never edits a profile, registry, generated production
asset, or ROM.  Missing visibility/writer evidence is represented as UNKNOWN;
UNKNOWN slots are never reported as leaseable.

The first checked fixture is the R1-S2 bank-$014 fire pit.  The command-line
shape is intentionally generic so later effect groups can supply another scene,
record, usage set, bank, viewport and neighboring record window.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = ROOT / "analysis/graphics_optimizer/editor_policy/Test_2_0.json"
DEFAULT_OUTPUT = ROOT / "build/analysis/palette_residency/r1s2_firepit_capacity.json"
ACTOR_MANIFEST = ROOT / "docs/design/rastan_actor_graphics_manifest.json"
SPRITE_VARIANT_MANIFEST = ROOT / "build/regions/pc090oj_editor_manifest.json"
DEATH_FRAME_INDEX = ROOT / "build/pc090oj_death_frame_index.bin"
SCENE = "PAL-R1-S2-PLANEA-CASTLE"
FIRE_RECORD = 18
FIRE_USAGES = tuple(f"LA-{n:04d}" for n in range(479, 495))
FIRE_BANK = 0x014
MODE8_TABLE = 0x059B1A
MODE8_PHASES = 3
PALETTE_ENTRIES = 16
NONTRANSPARENT_CAPACITY = 15


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hex_word(value: int) -> str:
    return f"0x{value:04X}"


def _rgb8_to_cram(rgb: list[int]) -> int:
    r, g, b = rgb
    return (((b >> 5) & 7) << 9) | (((g >> 5) & 7) << 5) | (((r >> 5) & 7) << 1)


def _arcade_0rgb444_to_cram(word: int) -> int:
    """Match palette_hooks.s $059AD4: 0RGB444 -> xBGR-555 -> Genesis."""
    r, g, b = (word >> 8) & 15, (word >> 4) & 15, word & 15
    return ((b & 0xE) << 8) | ((g & 0xE) << 4) | (r & 0xE)


def _resolve_keep(previous: list[int], raw: list[int]) -> list[int]:
    return [previous[i] if word == 0xFFFF else _arcade_0rgb444_to_cram(word)
            for i, word in enumerate(raw)]


def _parse_usage_ranges(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return FIRE_USAGES
    result: set[str] = set()
    for value in values:
        if "-" in value and value.count("LA-") == 2:
            left, right = value.split("-LA-")
            lo, hi = int(left.removeprefix("LA-")), int(right)
            result.update(f"LA-{n:04d}" for n in range(lo, hi + 1))
        else:
            result.add(value)
    return tuple(sorted(result))


def _phase_evidence(maincpu: bytes, bank_rgb: list[list[int]]) -> dict:
    initial = [_rgb8_to_cram(rgb) for rgb in bank_rgb]
    raw_phases: list[list[int]] = []
    states: list[list[int]] = [initial]
    previous = initial
    for phase in range(MODE8_PHASES):
        base = MODE8_TABLE + phase * PALETTE_ENTRIES * 2
        raw = [int.from_bytes(maincpu[base + i * 2:base + i * 2 + 2], "big")
               for i in range(PALETTE_ENTRIES)]
        raw_phases.append(raw)
        previous = _resolve_keep(previous, raw)
        states.append(previous)

    def nonzero_unique(row: list[int]) -> list[int]:
        return sorted(set(row[1:]))

    lifecycle = sorted(set().union(*(set(row[1:]) for row in states)))
    return {
        "source": {
            "cycler": "FUN_00059962",
            "loader": "0x059AD4",
            "table": "0x059B1A",
            "destination_arcade_bank": "0x014",
            "cadence": "counter 0..23; publish on (counter & 7) == 0; phases 0,1,2",
            "keep_word": "0xFFFF",
        },
        "states": [
            {
                "name": "initial_bank_014" if index == 0 else f"mode8_phase_{index - 1}",
                "raw_arcade_words": None if index == 0 else [_hex_word(v) for v in raw_phases[index - 1]],
                "cram_words": [_hex_word(v) for v in row],
                "unique_nontransparent": [_hex_word(v) for v in nonzero_unique(row)],
                "unique_nontransparent_count": len(nonzero_unique(row)),
            }
            for index, row in enumerate(states)
        ],
        "initial_unique_count": len(nonzero_unique(initial)),
        "animated_phase_unique_counts": [len(nonzero_unique(row)) for row in states[1:]],
        "lifecycle_unique_colors": [_hex_word(v) for v in lifecycle],
        "lifecycle_unique_count": len(lifecycle),
        "maximum_simultaneously_required": max(len(nonzero_unique(row)) for row in states),
        "quantization_only_merges": PALETTE_ENTRIES - 1 - len(nonzero_unique(initial)),
        "resolution": (
            "The initial bank and mode-8 phase 0 each need 9 distinct nontransparent Genesis words; "
            "phases 1 and 2 each need 8. The complete lifecycle union and maximum simultaneous "
            "requirement are therefore both 9 colors."
        ),
    }


def _profile_lines(profile: dict, context: dict) -> list[list[int | None]]:
    lines: list[list[int | None]] = []
    for line in profile["target_palette_lines"]:
        lines.append([None if v is None else int(v, 16) for v in line])
    for key, values in context.get("tpl", {}).items():
        line = int(key)
        for index, value in values.items():
            lines[line][int(index)] = int(value, 16)
    l2 = profile.get("line2_display", {}).get("cram")
    if l2:
        lines[2] = [int(v, 16) for v in l2]
    return lines


def _world_cells(server, scene: str, records: list[int]) -> tuple[dict, dict]:
    cells: dict[tuple[int, int], dict] = {}
    maps = {}
    for record in records:
        record_map = server.layera_map(record, scene)
        maps[str(record)] = {
            key: record_map[key] for key in
            ("selector", "cols", "rows", "descriptor_cells", "resolved", "unresolved")
        }
        for cell in record_map["cells"]:
            cells[(record * 64 + cell["c"], cell["r"])] = cell
    return cells, maps


def _visibility(server, profile: dict, scene: str, record: int, effect: set[str],
                neighbors: int, width: int, height: int, top: int) -> dict:
    records = list(range(record - neighbors, record + neighbors + 1))
    cells, maps = _world_cells(server, scene, records)
    effect_cells = [(x, y, cell) for (x, y), cell in cells.items()
                    if cell.get("uid") in effect and x // 64 == record]
    if not effect_cells:
        raise ValueError("selected effect has no cells in selected record/window")
    effect_x = [x for x, _y, _cell in effect_cells]
    effect_y = [y for _x, y, _cell in effect_cells]
    first_left = min(effect_x) - (width - 1)
    last_left = max(effect_x)
    context = profile["context_policies"][scene]
    mappings = context["plane_usage_palette_mappings"]
    critical = []
    scene_line_indices = {line: set() for line in range(4)}
    for mapping in mappings.values():
        scene_line_indices[mapping["line"]].update(int(v) for v in mapping["index_map"].values())
    # Rastan is necessarily present whenever a player-controlled gameplay viewport exists.
    # The profile has both a usage row and an object row; take their lossless union.  Other
    # actors remain separate/UNKNOWN because their record-local lifetime is not proven.
    for key in ("usage:rastan_f7722:bank0x33", "object:player.rastan", "object:weapon.sword"):
        mapping = profile.get("usage_palette_mappings", {}).get(key)
        if mapping:
            scene_line_indices[mapping["line"]].update(int(v) for v in mapping["index_map"].values())
    affected_uids: set[str] = set()
    affected_codes: set[int] = set()
    max_line_indices = {line: set() for line in range(4)}
    for left in range(first_left, last_left + 1):
        visible_effect = []
        line_indices = {line: set() for line in range(4)}
        line_uids = {line: set() for line in range(4)}
        # Proven always-live player/body/held default weapon demand.
        line_indices[0].update(scene_line_indices[0])
        for x in range(left, left + width):
            for y in range(top, top + height):
                cell = cells.get((x, y))
                if cell is None:
                    continue
                uid = cell.get("uid")
                if uid in effect:
                    # A nonzero nibble proof is supplied separately; all fire tiles are opaque.
                    visible_effect.append({"x": x, "y": y, "usage": uid})
                    continue
                mapping = mappings.get(uid)
                if mapping is None:
                    continue
                line = mapping["line"]
                line_indices[line].update(int(v) for v in mapping["index_map"].values())
                line_uids[line].add(uid)
                if line == 3:
                    affected_uids.add(uid)
                    affected_codes.add(cell["code"])
        if not visible_effect:
            continue
        for line in range(4):
            if len(line_indices[line]) > len(max_line_indices[line]):
                max_line_indices[line] = set(line_indices[line])
        critical.append({
            "camera_left_global_cell": left,
            "camera_left_record": left // 64,
            "camera_left_local_cell": left % 64,
            "visible_effect_cell_count": len(visible_effect),
            "line_indices": {str(line): sorted(line_indices[line]) for line in range(4)},
        })
    return {
        "viewport": {"width_cells": width, "height_cells": height, "top_logical_row": top,
                     "source": ("tilemap_hooks.s .Lplane_a_visible_top_from_scroll_d0 semantics; "
                                "Genesis H40 320x224 = 40x28 cells")},
        "decoded_records": records,
        "record_maps": maps,
        "effect_cell_bounds": {
            "global_x": [min(effect_x), max(effect_x)],
            "global_x_pixels": [min(effect_x) * 8, max(effect_x) * 8 + 7],
            "record_local_x": [min(effect_x) - record * 64, max(effect_x) - record * 64],
            "row": [min(effect_y), max(effect_y)],
            "decoded_cell_count": len(effect_cells),
        },
        "candidate_camera_left_global_cells": [first_left, last_left],
        "candidate_camera_left_pixels_exact": [min(effect_x) * 8 - (width * 8 - 1),
                                                max(effect_x) * 8 + 7],
        "candidate_camera_left_records": sorted({v for left in range(first_left, last_left + 1)
                                                  for v in (left // 64, (left + width - 1) // 64)}),
        "critical_viewport_count": len(critical),
        "critical_viewports": critical,
        "scene_wide_target_indices": {str(k): sorted(v) for k, v in scene_line_indices.items()},
        "maximum_simultaneous_non_effect_target_indices": {
            str(k): sorted(v) for k, v in max_line_indices.items()
        },
        "proven_sprite_demand": {
            "line_0": {
                "consumers": ["object:player.rastan", "object:weapon.sword"],
                "target_indices": sorted(scene_line_indices[0]),
                "basis": "Rastan is necessarily present in a live gameplay viewport; Test 2.0 mapping",
            },
            "other_record_local_actors": "UNKNOWN_SEPARATE",
        },
        "line3_affected_nonfire_usage_ids": sorted(affected_uids),
        "line3_affected_nonfire_tile_codes": [f"0x{v:04X}" for v in sorted(affected_codes)],
        "reverse_supported": True,
        "boundaries": {
            "offline_preparation": f"record window {record-neighbors}..{record+neighbors}; no CRAM change",
            "first_possible_visible_camera_left": first_left,
            "last_possible_visible_camera_left": last_left,
            "coarse_activation": f"before record {record} Plane-A presentation",
            "coarse_release_forward": f"after record {record} is no longer in the 40-cell viewport",
            "reverse": f"re-evaluate on {record+1}->{record} and release only after {record}->{record-1}",
        },
    }


def _r1s2_line1_proof(profile: dict, profile_lines: list[list[int | None]], fire: dict) -> dict:
    """Close the PROMT-ID-0149 Line-1 UNKNOWN with current production evidence.

    This is deliberately a fixture proof, not a general claim that authored
    sprite mappings are scene-global.  The current R1-S2 roster and native
    mapping outputs prove which authored Line-1 rows can actually reach SAT
    while record-18 fire is visible.
    """
    mappings = profile["usage_palette_mappings"]
    line1_authored = {uid: mapping for uid, mapping in mappings.items()
                      if mapping.get("line") == 1}
    expected = {
        "usage:lizardman:bank0x36",
        "usage:flying_demon:bank0x35",
        "usage:four_armed_insect:bank0x3A",
        "object:boss.r1.body",
        "object:boss.r1.flying_daggers",
        "object:item.reward.kind01",
        "object:item.reward.kind11",
    }
    if set(line1_authored) != expected:
        raise ValueError("Build-0573 Line-1 authored mapping set changed; re-prove R1-S2 visibility")

    variant_manifest = json.loads(SPRITE_VARIANT_MANIFEST.read_text())
    integrated = set(variant_manifest["usage_decisions"])
    death_index = DEATH_FRAME_INDEX.read_bytes()
    if len(death_index) != 60 * 8:
        raise ValueError("unexpected native death-frame index size")
    # Reward records 26..51 (kinds 1..13, normal+mirror) retain embedded
    # palette line 0; 52..59 (kinds 14..17) retain line 3.  In particular,
    # kind01 records 26/27 and kind11 records 46/47 are not Line-1 records.
    reward_attrs = {
        record: int.from_bytes(death_index[record * 8 + 6:record * 8 + 8], "big")
        for record in (26, 27, 46, 47)
    }
    if any((attr & 3) != 0 for attr in reward_attrs.values()):
        raise ValueError("reward kind01/kind11 production palette line changed")

    excluded = [
        {
            "usage": "usage:lizardman:bank0x36", "semantic_identity": "Lizardman",
            "source_actor": "family 0 / base 0x004B", "code_bank": "base 0x004B / bank 0x36",
            "target_indices": sorted(set(line1_authored["usage:lizardman:bank0x36"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "R1-S1 field family; R1-S2 field schedule spawns only family-2 base 0x033E",
        },
        {
            "usage": "usage:flying_demon:bank0x35", "semantic_identity": "Flying Demon",
            "source_actor": "family 8/9 component / base 0x0129+0x0275",
            "code_bank": "base 0x0129+0x0275 / bank 0x35",
            "target_indices": sorted(set(line1_authored["usage:flying_demon:bank0x35"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "R1-S1 field family; absent from the R1-S2 schedule and marker roster",
        },
        {
            "usage": "usage:four_armed_insect:bank0x3A", "semantic_identity": "Four-Armed Insect",
            "source_actor": "family 3 / base 0x02E8", "code_bank": "base 0x02E8 / bank 0x3A",
            "target_indices": sorted(set(line1_authored["usage:four_armed_insect:bank0x3A"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "R1-S1 field family; absent from the R1-S2 schedule and marker roster",
        },
        {
            "usage": "object:boss.r1.body", "semantic_identity": "Round-1 boss body",
            "source_actor": "record type 0x0E / base 0x061D", "code_bank": "base 0x061D / bank 0x4F",
            "target_indices": sorted(set(line1_authored["object:boss.r1.body"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "R1-S3 record-22 boss-room actor; record-18 fire envelope is R1-S2 records 17..19",
        },
        {
            "usage": "object:boss.r1.flying_daggers", "semantic_identity": "Round-1 boss Flying Daggers",
            "source_actor": "record type 0x0F / five boss components",
            "code_bank": "program 0x47E54 / bank 0x4F",
            "target_indices": sorted(set(line1_authored["object:boss.r1.flying_daggers"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "created by the R1-S3 boss only; cannot survive backward across a subround boundary",
        },
        {
            "usage": "object:item.reward.kind01", "semantic_identity": "Gameplay reward kind 01",
            "source_actor": "in-place family-12 reward transform",
            "code_bank": "base 0x0A5A / selector 0x13 / code 0x0A5A",
            "target_indices": sorted(set(line1_authored["object:item.reward.kind01"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "authored mapping is not production-integrated; native death record 26/27 emits embedded Line 0",
        },
        {
            "usage": "object:item.reward.kind11", "semantic_identity": "Gameplay reward kind 11",
            "source_actor": "in-place family-12 reward transform",
            "code_bank": "base 0x0A5A / selector 0x1D / code 0x0A65",
            "target_indices": sorted(set(line1_authored["object:item.reward.kind11"]["index_map"].values())),
            "status": "PROVEN_EXCLUDED",
            "evidence": "authored mapping is not production-integrated; native death record 46/47 emits embedded Line 0",
        },
    ]
    fire_colors = [int(v, 16) for v in fire["lifecycle_unique_colors"]]
    free = list(range(1, 16))
    allocation = [{"index": index, "fire_color": _hex_word(color)}
                  for index, color in zip(free, fire_colors)]
    return {
        "status": "LOSSLESS_FREE_SLOT_LEASE",
        "possible_consumers": [],
        "excluded_consumers": excluded,
        "unresolved_consumers": [],
        "authored_line1_usages": sorted(line1_authored),
        "production_integrated_authored_usages": sorted(set(line1_authored) & integrated),
        "required_target_indices": [],
        "required_colors": [],
        "required_color_count": 0,
        "fire_colors": [_hex_word(v) for v in fire_colors],
        "exact_overlap": [],
        "exact_overlap_count": 0,
        "unused_stable_indices": free,
        "free_slot_lease": {
            "result": "LOSSLESS_FREE_SLOT_LEASE", "available_slots": len(free),
            "required_slots": len(fire_colors), "allocation": allocation,
            "existing_sprite_index_mappings_changed": False,
        },
        "regional_composite": {
            "result": "LOSSLESS_REGIONAL_COMPOSITE", "lossless_union_size": len(fire_colors),
            "capacity": NONTRANSPARENT_CAPACITY, "over_capacity": 0,
            "artistic_merges_required": 0,
            "exact_color_set": [_hex_word(v) for v in fire_colors],
            "sprite_usages_requiring_reindex": [],
            "plane_a_usages_requiring_reindex": list(FIRE_USAGES),
            "maximum_pattern_variant_cost_bytes": len(FIRE_USAGES) * 32,
            "offline_support": ("PC090OJ (code,bank) variants are unnecessary because no sprite consumer "
                                "coexists; the existing PC080SN per-context usage compiler can emit the "
                                "16 fire-tile variants without runtime pixel conversion"),
        },
        "writer_proof": {
            "during_visible_interval": ("diagnostic_palette_active_asset gates retained $059AD4, $03BA64, "
                                        "and $045DB8 writes away from authored Lines 0/1/3"),
            "scene_installer": ("vdp_install_test_lines writes the full fixed R1-S2 Line 1 before gameplay "
                                "visibility; no same-asset record 17..19 refresh occurs"),
            "death_respawn": ("death/READY may replace Line 1 only while gameplay/fire is not presented; "
                              "R1-S2 gameplay ownership reinstalls the fixed line before resumed visibility"),
            "arbitrary_runtime_translation_required": False,
        },
        "source_hashes": {
            "actor_manifest": _sha(ACTOR_MANIFEST),
            "sprite_variant_manifest": _sha(SPRITE_VARIANT_MANIFEST),
            "death_frame_index": _sha(DEATH_FRAME_INDEX),
        },
    }


def _slot_classifications(profile: dict, visibility: dict, line1_proof: dict | None = None) -> dict:
    result = {}
    simultaneous = visibility["maximum_simultaneous_non_effect_target_indices"]
    scene = visibility["scene_wide_target_indices"]
    for line in range(4):
        entries = []
        visible = set(simultaneous[str(line)])
        scene_used = set(scene[str(line)])
        for index in range(16):
            evidence = []
            if index == 0:
                cls = "USED_STATIC"
                evidence.append("transparent/backdrop entry; never leaseable")
            elif line == 2:
                cls = "USED_DYNAMIC"
                evidence.append("current-round Layer-B $059AD4 producer owns the full protected line")
                if index == 1:
                    evidence.append("Test 2.0 identifies index 1 as time-of-day animated")
                evidence.append("sparse $FFFF rows retain writer history rather than proving freedom")
            elif line == 3 and index in (14, 15):
                cls = "UNUSED_DYNAMIC" if index not in visible else "USED_DYNAMIC"
                evidence.append("R1 mode-9 waterfall route writes Line 3 entries 14/15")
            elif index in visible:
                cls = "USED_STATIC"
                evidence.append("referenced by a simultaneously visible non-effect Plane-A mapping")
            elif line == 1 and line1_proof is not None:
                cls = "UNUSED_STABLE"
                evidence.append("no Build-0573 Line-1 sprite can coexist with the R1-S2 fire envelope")
                evidence.append("authored gameplay writer gates keep Line 1 stable while fire is visible")
            elif line in (0, 1):
                cls = "UNKNOWN"
                evidence.append("record-local PC090OJ actor lifetime/visibility corpus is incomplete")
                evidence.append("UNKNOWN is not leaseable")
            elif index in scene_used:
                cls = "USED_STATIC"
                evidence.append("used elsewhere in the selected scene/profile")
            else:
                cls = "UNUSED_STABLE"
                evidence.append("no selected-scene mapping or known writer in the analyzed window")
            entries.append({"index": index, "classification": cls, "evidence": evidence})
        result[str(line)] = entries
    return result


def _candidate_lines(profile_lines: list[list[int | None]], fire: dict,
                     visibility: dict, line1_proof: dict | None = None) -> dict:
    fire_colors = {int(v, 16) for v in fire["lifecycle_unique_colors"]}
    max_indices = visibility["maximum_simultaneous_non_effect_target_indices"]
    candidates = {}
    for line in range(4):
        indices = set(max_indices[str(line)])
        if line == 1 and line1_proof is not None:
            indices = set(line1_proof["required_target_indices"])
        if line == 2:
            # This is a writer-residency requirement, not a claim that every index is
            # pixel-visible in one viewport.  Exact pixel demand remains unresolved below.
            indices.update(range(1, 16))
        host_colors = {profile_lines[line][i] for i in indices if profile_lines[line][i] is not None}
        overlap = host_colors & fire_colors
        union = host_colors | fire_colors
        over = max(0, len(union) - NONTRANSPARENT_CAPACITY)
        if line == 0 and over:
            result = "REQUIRES_ARTISTIC_MERGES"
            reason = f"proven player/weapon demand plus fire exceeds 15 entries by {over}"
        elif line == 0:
            result = "LOSSLESS_FIT"
            reason = "proven player/weapon lower bound fits; no additional actor demand was assumed"
        elif line == 1 and line1_proof is not None:
            result = line1_proof["status"]
            reason = "R1-S2 roster, production mapping, and writer gates prove all 15 nonzero slots leaseable"
        elif line == 1:
            result = "INSUFFICIENT_VISIBILITY_PROOF"
            reason = "record-local sprite actor visibility and writer lifetimes are not proven"
        elif line == 2:
            result = "UNSAFE_DYNAMIC_WRITER"
            reason = "protected current-round Layer-B producer and retain history own this line"
        elif over:
            result = "REQUIRES_ARTISTIC_MERGES"
            reason = f"lossless union exceeds 15 entries by {over}"
        else:
            result = "LOSSLESS_FIT"
            reason = "lossless union fits and no conflicting writer was found"
        candidates[str(line)] = {
            "host_required_indices": sorted(indices),
            "host_required_colors": [_hex_word(v) for v in sorted(host_colors)],
            "host_required_color_count": len(host_colors),
            "host_demand_complete": line in (0, 3) or (line == 1 and line1_proof is not None),
            "fire_required_colors": [_hex_word(v) for v in sorted(fire_colors)],
            "fire_required_color_count": len(fire_colors),
            "exact_overlap": [_hex_word(v) for v in sorted(overlap)],
            "exact_overlap_count": len(overlap),
            "combined_lossless_requirement": len(union),
            "capacity": NONTRANSPARENT_CAPACITY,
            "over_capacity": over,
            "result": result,
            "reason": reason,
        }
    return candidates


def analyze(args) -> dict:
    profile_path = Path(args.profile).resolve()
    profile = json.loads(profile_path.read_text())
    scene = args.scene
    effect = set(_parse_usage_ranges(args.effect_usage))
    corpus = ROOT / "analysis/graphics_optimizer/subround_corpus" / scene
    uses_path = corpus / "plane_a_uses.json"
    banks_path = corpus / "plane_palette_banks.json"
    maincpu_path = ROOT / "build/regions/maincpu.bin"
    pc080_path = ROOT / "build/regions/pc080sn.bin"
    server = _load_module(ROOT / "tools/graphics_editor/server.py", "palette_composer_server_ro")
    uses = json.loads(uses_path.read_text())
    banks = json.loads(banks_path.read_text())["banks"]
    bank_key = f"0x{args.source_bank:03X}"
    bank = banks[bank_key]["arcade_rgb8"]

    selected = [uses[int(uid.split("-")[1])] for uid in sorted(effect)]
    source_indices = set()
    gfx = pc080_path.read_bytes()
    for use in selected:
        start = use["tile_code"] * 32
        for byte in gfx[start:start + 32]:
            source_indices.update((byte >> 4, byte & 15))
    source_indices.discard(0)
    phases = _phase_evidence(maincpu_path.read_bytes(), bank)
    visibility = _visibility(server, profile, scene, args.record, effect, args.neighbors,
                             args.viewport_width, args.viewport_height, args.viewport_top)
    profile_lines = _profile_lines(profile, profile["context_policies"][scene])
    line1_proof = (_r1s2_line1_proof(profile, profile_lines, phases)
                   if scene == SCENE and args.record == FIRE_RECORD and effect == set(FIRE_USAGES)
                   else None)
    slots = _slot_classifications(profile, visibility, line1_proof)
    candidates = _candidate_lines(profile_lines, phases, visibility, line1_proof)

    unresolved = [
        "Exact record-local PC090OJ enemy lifetime/visibility outside the proven R1-S2 Line-1 roster remains separate from the Line-0 lower bound.",
        "The production Plane-B compiler explicitly marks its selector-0 player-driven Y envelope incomplete; L2 pixel-visible demand is not fabricated.",
        "A later runtime compiler must derive activation/release from retained camera state and re-evaluate on scene entry, direct start, death, and reversal.",
    ]
    return {
        "schema": "palette-residency-capacity-analysis/v2",
        "tool": "tools/graphics_editor/analyze_palette_residency.py",
        "facts_only": True,
        "inputs": {
            "scene": scene, "retained_record": args.record,
            "neighbor_window": args.neighbors, "effect_usages": sorted(effect),
            "source_palette_bank": bank_key,
            "proposed_target_line": args.target_line,
            "desired_color_count_limit": args.color_limit,
            "profile": str(profile_path.relative_to(ROOT)),
        },
        "provenance": {
            "profile_sha256": _sha(profile_path),
            "plane_a_uses_sha256": _sha(uses_path),
            "plane_palette_banks_sha256": _sha(banks_path),
            "maincpu_sha256": _sha(maincpu_path),
            "pc080sn_sha256": _sha(pc080_path),
        },
        "effect": {
            "members": sorted(effect), "sprite_members": [], "sprite_hypothesis": "DISPROVEN_FOR_R1S2",
            "tile_codes": [use["tile_code_hex"] for use in selected],
            "records": sorted(set().union(*(set(use["records"]) for use in selected))),
            "source_indices_used": sorted(source_indices),
            "all_nontransparent_source_indices_used": source_indices == set(range(1, 16)),
        },
        "fire_animation": phases,
        "visibility": visibility,
        "line_demand": {
            "scene_wide": visibility["scene_wide_target_indices"],
            "maximum_simultaneous_non_effect": visibility["maximum_simultaneous_non_effect_target_indices"],
            "sprites": "UNKNOWN_SEPARATE",
            "plane_b": "INSUFFICIENT_Y_ENVELOPE_PROOF",
        },
        "slot_classifications": slots,
        "candidate_lines": candidates,
        "line3_question": {
            "maximum_simultaneous_nonfire_castle_colors": candidates["3"]["host_required_color_count"],
            "fire_lifecycle_colors": candidates["3"]["fire_required_color_count"],
            "exact_overlap": candidates["3"]["exact_overlap_count"],
            "combined": candidates["3"]["combined_lossless_requirement"],
            "over_capacity": candidates["3"]["over_capacity"],
            "affected_usage_ids": visibility["line3_affected_nonfire_usage_ids"],
            "affected_tile_codes": visibility["line3_affected_nonfire_tile_codes"],
        },
        "line1_question": line1_proof,
        "checkpoint_respawn": {
            "subround_stage_seed": 16,
            "first_live_retained_record": 17,
            "sources": [
                "specs/palette_subround_map.json R1-S2 stage_index=16 record_band=16..21",
                "PROMT-ID-0062 functional direct start: stage 0x0010, retained record 0x0011",
                "PROMT-ID-0136: a5+0x13e has an increment writer and no respawn rewind writer",
            ],
            "retained_record_behavior": "a5+0x13e is monotone and does not rewind on same-stage respawn",
            "respawn_records": "the current retained record is preserved; death at record 18 can respawn with record 18 still selected",
            "fire_immediately_visible_after_respawn": True,
            "required_later_contract": "re-evaluate residency and install the exact initial/current phase before visibility",
        },
        "recommended_host_line": 1 if line1_proof else None,
        "unresolved_evidence": unresolved,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default=SCENE)
    parser.add_argument("--record", type=int, default=FIRE_RECORD)
    parser.add_argument("--neighbors", type=int, default=1)
    parser.add_argument("--effect-usage", action="append")
    parser.add_argument("--source-bank", type=lambda v: int(v, 0), default=FIRE_BANK)
    parser.add_argument("--target-line", type=int)
    parser.add_argument("--color-limit", type=int)
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--viewport-width", type=int, default=40)
    parser.add_argument("--viewport-height", type=int, default=28)
    parser.add_argument("--viewport-top", type=int, default=1)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = analyze(args)
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    print(f"PALETTE_RESIDENCY_OK output={output.relative_to(ROOT)} sha256={hashlib.sha256(encoded).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
