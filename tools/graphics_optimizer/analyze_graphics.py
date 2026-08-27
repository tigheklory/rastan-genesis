#!/usr/bin/env python3
"""Offline original-arcade graphics/palette analyzer and Genesis packing optimizer.

Production inputs are reconstructed arcade regions, static semantic tables and an explicit
optimization policy. Runtime captures are evidence citations only and are never read here.
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TRANSLATION = ROOT / "tools" / "translation"
sys.path.insert(0, str(TRANSLATION))

import compile_pc080sn_genesis as compiler
import preconvert_pc090oj_tiles as sprite_converter
import reindex_graphics_for_palette as reindexer

MANIFEST = Path(__file__).with_name("scope_manifest.json")
PLANE_A_TOOL = ROOT / "tools" / "audit_round1_phase1_plane_a.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


plane_a_decoder = load_module(PLANE_A_TOOL, "plane_a_audit_decoder")


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_ranges(values):
    out = []
    for value in values:
        if "-" in value:
            lo, hi = (int(part, 0) for part in value.split("-", 1))
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(value, 0))
    return sorted(set(out))


def pixels8(raw: bytes):
    return [(raw[row * 4 + col // 2] >> (4 if col % 2 == 0 else 0)) & 15
            for row in range(8) for col in range(8)]


def pixels16(raw: bytes):
    return [(raw[row * 8 + col // 2] >> (4 if col % 2 == 0 else 0)) & 15
            for row in range(16) for col in range(16)]


def flip8(raw: bytes, horizontal=False, vertical=False):
    px = pixels8(raw)
    rows = [px[i:i + 8] for i in range(0, 64, 8)]
    if horizontal:
        rows = [list(reversed(row)) for row in rows]
    if vertical:
        rows.reverse()
    return reindexer._pack([v for row in rows for v in row])


def rgb_from_arcade(word: int):
    def expand5(v):
        return (v << 3) | (v >> 2)
    return [expand5(word & 31), expand5((word >> 5) & 31), expand5((word >> 10) & 31)]


def rgb_from_genesis(word: int):
    levels = [0, 36, 73, 109, 146, 182, 219, 255]
    return [levels[(word >> 1) & 7], levels[(word >> 5) & 7], levels[(word >> 9) & 7]]


def srgb_linear(v):
    v /= 255.0
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def rgb_lab(rgb):
    r, g, b = map(srgb_linear, rgb)
    x = (r * .4124564 + g * .3575761 + b * .1804375) / .95047
    y = (r * .2126729 + g * .7151522 + b * .0721750)
    z = (r * .0193339 + g * .1191920 + b * .9503041) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)]


def delta_e_2000(lab1, lab2):
    # Sharma et al. CIEDE2000, unit weighting factors.
    L1, a1, b1 = lab1; L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cbar = (C1 + C2) / 2
    G = .5 * (1 - math.sqrt(Cbar ** 7 / (Cbar ** 7 + 25 ** 7)))
    ap1, ap2 = (1 + G) * a1, (1 + G) * a2
    cp1, cp2 = math.hypot(ap1, b1), math.hypot(ap2, b2)
    hp1 = math.degrees(math.atan2(b1, ap1)) % 360
    hp2 = math.degrees(math.atan2(b2, ap2)) % 360
    dL, dC = L2 - L1, cp2 - cp1
    dh = hp2 - hp1
    if cp1 * cp2 == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dH = 2 * math.sqrt(cp1 * cp2) * math.sin(math.radians(dh / 2))
    Lbar, Cbarp = (L1 + L2) / 2, (cp1 + cp2) / 2
    if cp1 * cp2 == 0: hbar = hp1 + hp2
    elif abs(hp1 - hp2) <= 180: hbar = (hp1 + hp2) / 2
    elif hp1 + hp2 < 360: hbar = (hp1 + hp2 + 360) / 2
    else: hbar = (hp1 + hp2 - 360) / 2
    T = (1 - .17 * math.cos(math.radians(hbar - 30)) +
         .24 * math.cos(math.radians(2 * hbar)) +
         .32 * math.cos(math.radians(3 * hbar + 6)) -
         .20 * math.cos(math.radians(4 * hbar - 63)))
    dtheta = 30 * math.exp(-((hbar - 275) / 25) ** 2)
    Rc = 2 * math.sqrt(Cbarp ** 7 / (Cbarp ** 7 + 25 ** 7))
    Sl = 1 + .015 * (Lbar - 50) ** 2 / math.sqrt(20 + (Lbar - 50) ** 2)
    Sc, Sh = 1 + .045 * Cbarp, 1 + .015 * Cbarp * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dL / Sl) ** 2 + (dC / Sc) ** 2 + (dH / Sh) ** 2 +
                     Rt * (dC / Sc) * (dH / Sh))


def resolve_scope(mc: bytes, round_number: int, phase: int):
    records = compiler.decode_stage_records(mc, round_number - 1)
    event_seen = 0
    selected = []
    for record in records:
        selected.append(record)
        if 4 in record["events"]:
            event_seen += 1
            if event_seen == phase:
                break
    if event_seen < phase:
        raise SystemExit(f"unsupported phase {phase}: round {round_number} has only {event_seen} phase boundaries")
    progression = [r for r in compiler.decode_plane_b_progression(mc, round_number - 1)
                   if r["segment"] in {s["segment"] for s in selected}]
    descriptors = set()
    for r in progression:
        before = r["descriptor_before"]
        count = 4 if r["descriptor_action"] == "scene_fill_4" else (2 if r["descriptor_action"] == "horizontal_2" else 0)
        descriptors.update(range(before, before + count))
    # Physical Plane-B residency is a round property in the original producer.  Keep it
    # separate from the phase-local progression/state timeline.
    round_descriptors = set()
    for r in compiler.decode_plane_b_progression(mc, round_number - 1):
        before = r["descriptor_before"]
        count = 4 if r["descriptor_action"] == "scene_fill_4" else (2 if r["descriptor_action"] == "horizontal_2" else 0)
        round_descriptors.update(range(before, before + count))
    return records, selected, progression, sorted(descriptors), sorted(round_descriptors)


def decode_palettes(mc: bytes, banks, scene):
    result = {}
    for bank in sorted(set(banks)):
        # FUN_0003BA20 builds the 32 scene palettes at a5+0x1600. The original
        # arcade publishes that same set twice: FUN_00045D7C -> banks 0..31 and
        # FUN_00045DC4 -> banks 48..79. The startup pool is therefore not the
        # authoritative gameplay source for low PC080SN banks.
        if 0 <= bank < 32:
            words = compiler.decode_scene_arcade_palettes(mc, scene)[bank]
            record = compiler.PALETTE_SCENE_RECORDS + (scene - 1) * 32 + bank
            block = mc[record]
            source = (f"scene {scene} index {bank} record@0x{record:05X} block {block} "
                      f"@0x{compiler.PALETTE_ROM_COLORS + block * 32:05X}; "
                      "FUN_0003BA20 -> a5+0x1600, FUN_00045D7C -> arcade banks 0..31")
        else:
            words, source = compiler.decode_arcade_palette_bank(mc, bank, scene)
        if len(words) != 16:
            raise SystemExit(f"palette bank {bank:#x} has no complete static decode")
        result[bank] = {
            "bank": bank,
            "bank_hex": f"0x{bank:03X}",
            "source": source,
            "entries": [{
                "index": i,
                "arcade_xbgr555": f"0x{word:04X}",
                "arcade_rgb": rgb_from_arcade(word),
                "lab": [round(v, 5) for v in rgb_lab(rgb_from_arcade(word))],
                "genesis_cram": f"0x{compiler.arcade_xbgr555_to_genesis(word):04X}",
                "genesis_rgb": rgb_from_genesis(compiler.arcade_xbgr555_to_genesis(word))
            } for i, word in enumerate(words)]
        }
    return result


def decode_plane_a(mc, gfx, segments):
    cells = []
    for segment in segments:
        cells.extend(plane_a_decoder.reconstruct_segment(mc, gfx, segment, "visible"))
    uses = {}
    for cell in cells:
        bank = cell.attr & 0x1ff
        flip = (cell.attr >> 14) & 3
        key = (cell.tile_code, bank, flip, cell.exact_hash)
        row = uses.setdefault(key, {
            "tile_code": cell.tile_code, "tile_code_hex": f"0x{cell.tile_code:04X}",
            "physical_pattern": cell.exact_hash, "palette_bank": bank,
            "palette_bank_hex": f"0x{bank:03X}", "flip": flip,
            "priority_bits": None, "map_cell_count": 0, "records": set(),
            "coordinate_samples": [], "source_address": f"0x{cell.source_address:06X}"
        })
        row["map_cell_count"] += 1
        row["records"].add(cell.segment)
        if len(row["coordinate_samples"]) < 12:
            row["coordinate_samples"].append([cell.world_column, cell.world_row])
    out = []
    for row in uses.values():
        row["records"] = sorted(row["records"])
        out.append(row)
    return cells, sorted(out, key=lambda r: (r["palette_bank"], r["tile_code"], r["flip"]))


def decode_plane_b(mc, gfx, descriptors, progression):
    uses = {}
    states = []
    active = set()
    for record in progression:
        if record["descriptor_action"] != "vertical_0":
            before = record["descriptor_before"]
            count = 4 if record["descriptor_action"] == "scene_fill_4" else 2
            active.update(range(before, before + count))
        states.append({
            "state_id": f"record_{record['segment']:02d}", "record": record["segment"],
            "trigger": record["descriptor_action"], "active_descriptors": sorted(active),
            "palette_banks": sorted({int.from_bytes(mc[compiler.PLANE_B_DESC_TABLE + d * 6:compiler.PLANE_B_DESC_TABLE + d * 6 + 2], "big") & 0x1ff for d in active})
        })
    for descriptor in descriptors:
        base = compiler.PLANE_B_DESC_TABLE + descriptor * 6
        attr = int.from_bytes(mc[base:base + 2], "big")
        src = int.from_bytes(mc[base + 2:base + 6], "big") & 0xffffff
        bank, flip = attr & 0x1ff, (attr >> 14) & 3
        for row in range(64):
            for col in range(16):
                code = int.from_bytes(mc[src + row * 32 + col * 2:src + row * 32 + col * 2 + 2], "big") & 0x3fff
                raw = gfx[code * 32:(code + 1) * 32]
                key = (code, bank, flip, sha(raw))
                item = uses.setdefault(key, {
                    "tile_code": code, "tile_code_hex": f"0x{code:04X}",
                    "physical_pattern": sha(raw), "palette_bank": bank,
                    "palette_bank_hex": f"0x{bank:03X}", "flip": flip,
                    "map_cell_count": 0, "descriptors": set(), "coordinate_samples": []
                })
                item["map_cell_count"] += 1; item["descriptors"].add(descriptor)
                if len(item["coordinate_samples"]) < 8:
                    item["coordinate_samples"].append([descriptor, col, row])
    out = []
    for item in uses.values():
        item["descriptors"] = sorted(item["descriptors"]); out.append(item)
    return sorted(out, key=lambda r: (r["palette_bank"], r["tile_code"])), states


def decode_sprites(pc090oj, manifest, round_number):
    families, frames = [], []
    profile = f"round{round_number}"
    if profile not in manifest["sprite_semantics"]:
        raise SystemExit(
            f"missing original-arcade sprite semantic profile {profile} in {MANIFEST}; "
            "decode that round's producer families before optimization"
        )
    profile_spec = manifest["sprite_semantics"][profile]
    entries = profile_spec["classes"] if isinstance(profile_spec, dict) else profile_spec
    for entry in entries:
        codes = parse_ranges(entry["codes"])
        relationship = entry.get("palette_relationship", {})
        palette_status = relationship.get("status", "unknown")
        proven_banks = parse_ranges(relationship.get("proven_banks", []))
        candidate_banks = parse_ranges(relationship.get("legal_candidates", []))
        if palette_status != "proven" and proven_banks:
            raise SystemExit(f"{entry['id']}: non-proven palette relationship cannot provide proven_banks")
        composites = entry.get("composites", [])
        composite_codes = {
            int(component["code"], 0)
            for composite in composites
            for component in composite["components"]
        }
        codes = sorted(set(codes) | composite_codes)
        patterns, pixel_count = set(), 0
        for code in codes:
            raw = pc090oj[code * 128:(code + 1) * 128]
            if len(raw) != 128: raise SystemExit(f"sprite code {code:#x} outside PC090OJ region")
            patterns.add(sha(raw)); pixel_count += sum(1 for p in pixels16(raw) if p)
        for composite in composites:
            components = []
            for source in composite["components"]:
                code = int(source["code"], 0)
                raw = pc090oj[code * 128:(code + 1) * 128]
                components.append({**source, "code": code, "code_hex": f"0x{code:04X}",
                                   "pattern_hash": sha(raw), "flip_h": source.get("flip_h", 0),
                                   "flip_v": source.get("flip_v", 0)})
            frames.append({"family_id": entry["id"], "family_name": entry["name"],
                           "frame_id": composite["id"], "component_cells": components,
                           "palette_banks": proven_banks,
                           "palette_candidate_banks": candidate_banks,
                           "palette_status": palette_status,
                           "render_mode": "proven_color" if proven_banks else "palette_neutral",
                           "composite_status": composite["status"],
                           "evidence": composite.get("evidence", entry["evidence"])})
        if not composites and codes:
            # The art vocabulary is intentionally one unresolved frame record.  Individual
            # hardware cells are not misrepresented as independent logical sprites.
            frames.append({"family_id": entry["id"], "family_name": entry["name"],
                           "frame_id": "unresolved_pose_art_vocabulary",
                           "component_cells": [{"code": code, "code_hex": f"0x{code:04X}",
                                                "x": (n % 8) * 16, "y": (n // 8) * 16,
                                                "flip_h": 0, "flip_v": 0,
                                                "pattern_hash": sha(pc090oj[code * 128:(code + 1) * 128])}
                                               for n, code in enumerate(codes)],
                           "palette_banks": proven_banks,
                           "palette_candidate_banks": candidate_banks,
                           "palette_status": palette_status,
                           "render_mode": "proven_color" if proven_banks else "palette_neutral",
                           "composite_status": "unresolved pose geometry; displayed as an art vocabulary, not as independent logical sprites",
                           "evidence": entry["evidence"]})
        families.append({**entry, "codes": codes, "palette_banks": proven_banks,
                         "palette_candidate_banks": candidate_banks,
                         "composites": [f["frame_id"] for f in frames if f["family_id"] == entry["id"]],
                         "physical_cells": len(patterns), "nontransparent_pixel_count": pixel_count,
                         "semantic_status": (
                             f"class={entry.get('class_resolution', 'unresolved')}; "
                             f"graphics={entry.get('graphics_resolution', 'unresolved')}; "
                             f"palette={palette_status}"
                         )})
    return families, frames


def decode_arcade_object_semantic_domain(mc, plane_a_cells, profile_spec):
    """Recover phase-local actor marker routes from original PC080SN descriptors.

    FUN_000559B2 publishes each visual descriptor word and its paired collision word.
    The collision half starts at descriptor+0x20, retaining the same 4x4 subcell
    coordinate. A leading 0x00FF selects the constant word at descriptor+0x22.
    """
    marker_uses = defaultdict(lambda: {"cell_count": 0, "words": set(), "samples": []})
    seen_positions = set()
    for cell in plane_a_cells:
        position = (cell.world_column, cell.world_row)
        if position in seen_positions:
            continue
        seen_positions.add(position)
        collision_base = cell.descriptor + 0x20
        if int.from_bytes(mc[collision_base:collision_base + 2], "big") == 0x00FF:
            source = collision_base + 2
        else:
            source = (collision_base + (cell.world_row & 3) * 8 +
                      (cell.segment_column & 3) * 2)
        word = int.from_bytes(mc[source:source + 2], "big")
        marker = word >> 8
        if marker < 0x40:
            continue
        item = marker_uses[marker]
        item["cell_count"] += 1
        item["words"].add(word)
        if len(item["samples"]) < 12:
            item["samples"].append({
                "segment": cell.segment,
                "world_column": cell.world_column,
                "world_row": cell.world_row,
                "descriptor": f"0x{cell.descriptor:04X}",
                "collision_source": f"arcade_rom/data 0x{source:06X}",
                "collision_word": f"0x{word:04X}",
            })
    routes = profile_spec.get("spawn_marker_routes", {})
    decoded_markers = []
    for marker, item in sorted(marker_uses.items()):
        marker_hex = f"0x{marker:02X}"
        route = routes.get(marker_hex, {})
        decoded_markers.append({
            "marker": marker_hex,
            "cell_count": item["cell_count"],
            "collision_words": [f"0x{word:04X}" for word in sorted(item["words"])],
            "class_id": route.get("class_id"),
            "spawn_route": route.get("route", "not classified in semantic manifest"),
            "graphics_bearing": route.get("graphics_bearing", "unresolved; conservative blocker required"),
            "samples": item["samples"],
        })

    record_routes = profile_spec.get("record_loader_routes", {})
    record_rows = []
    for record_value in range(8, 13):
        offset = 0x045592 + (record_value - 8) * 8
        record_rows.append({
            "record_value": record_value,
            "class_id": record_routes.get(str(record_value)),
            "source": f"arcade_rom/data 0x{offset:06X}",
            "base_tile": f"0x{int.from_bytes(mc[offset:offset + 2], 'big'):04X}",
            "family": mc[offset + 2],
            "class": f"0x{mc[offset + 3]:02X}",
            "field_0x28": f"0x{int.from_bytes(mc[offset + 4:offset + 6], 'big'):04X}",
            "field_0x2C": f"0x{int.from_bytes(mc[offset + 6:offset + 8], 'big'):04X}",
        })

    return {
        "schema_version": 1,
        "authority": "original arcade ROM/data and decompiled producer semantics",
        "phase_local_collision_publisher": {
            "producer": "arcade_pc 0x0559B2 FUN_000559B2",
            "visual_word": "descriptor + row_in_4x4*8 + column_in_4x4*2",
            "collision_word": "descriptor + 0x20 + row_in_4x4*8 + column_in_4x4*2; descriptor+0x22 when descriptor+0x20 is 0x00FF",
            "consumer": "arcade_pc 0x041180 actor_spawn_ground_and_activate_41180",
        },
        "phase_local_markers": decoded_markers,
        "manifest_routes_absent_from_map": sorted(set(routes) - {f"0x{x:02X}" for x in marker_uses}),
        "actor_record_loader": {
            "producer": "arcade_pc 0x04543E actor_record_loader_4543e",
            "table": "arcade_rom/data 0x045592",
            "stride": 8,
            "indexed_rows_8_through_12": record_rows,
        },
        "runtime_family_class_proof": {
            "source": "states/traces/direct_native_sprite_provenance_20260805_124225/dispatch.csv",
            "input_to_generated_assets": False,
            "role": "original-arcade semantic proof cited by the manifest; the generator does not read the trace",
            "observed_pairs": {
                "family_0": ["0x17", "0x18", "0x19", "0x1C", "0x1D", "0x1E", "0x1F", "0x70"],
                "family_2": ["0x0B", "0x0C", "0x0D", "0x0E", "0x0F", "0x10", "0x11", "0x12", "0x13"],
            },
        },
        "scope_limit": "Collision markers enumerate map-driven routes only; player, HUD, timer, drop, projectile and effect producers are enumerated separately in the legal class manifest.",
    }


def sprite_class_coverage(families, profile_spec, semantic_domain):
    legal = [family["id"] for family in families]
    resolved, unresolved = [], []
    blockers = []
    for family in families:
        complete = (
            family.get("class_resolution") == "resolved" and
            family.get("graphics_resolution") == "resolved" and
            family.get("palette_relationship", {}).get("status") == "proven"
        )
        (resolved if complete else unresolved).append(family["id"])
        if not complete:
            palette_status = family.get("palette_relationship", {}).get("status", "unknown")
            blockers.append({
                "class_id": family["id"],
                "class_resolution": family.get("class_resolution", "unresolved"),
                "graphics_resolution": family.get("graphics_resolution", "unresolved"),
                "palette_status": palette_status,
                "legal_palette_candidates": [f"0x{bank:02X}" for bank in family["palette_candidate_banks"]],
                "known_art_cells": family["physical_cells"],
                "feasibility_treatment": (
                    "conservative blocker; not counted as zero and not assigned colors"
                    if palette_status != "proven" else
                    "proven palette contributes to the known lower bound; unresolved class semantics still block closure"
                ),
            })
    domain = profile_spec.get("legal_class_domain", {})
    declared = domain.get("class_ids", [])
    discovered_route_ids = [
        route.get("class_id")
        for route in semantic_domain["phase_local_markers"]
    ] + [
        row.get("class_id")
        for row in semantic_domain["actor_record_loader"]["indexed_rows_8_through_12"]
    ]
    route_coverage_exact = (
        all(discovered_route_ids) and
        set(discovered_route_ids).issubset(set(declared))
    )
    partition_exact = (
        len(legal) == len(set(legal)) and
        sorted(legal) == sorted(declared) and
        sorted(legal) == sorted(resolved + unresolved) and
        route_coverage_exact
    )
    class_enumeration_complete = bool(domain.get("class_enumeration_complete", False))
    semantic_domain_enumerated = partition_exact and class_enumeration_complete
    return {
        "schema_version": 1,
        "coverage_rule": profile_spec.get("coverage_rule"),
        "original_arcade_chain": profile_spec.get("original_arcade_chain"),
        "legal_graphics_bearing_classes": legal,
        "resolved_classes": resolved,
        "explicitly_unresolved_classes": unresolved,
        "legal_class_domain": domain,
        "legal_equals_resolved_plus_unresolved": partition_exact,
        "discovered_route_ids": discovered_route_ids,
        "discovered_routes_in_legal_domain": route_coverage_exact,
        "counts": {"legal": len(legal), "resolved": len(resolved), "unresolved": len(unresolved)},
        "semantic_domain_enumerated": semantic_domain_enumerated,
        "class_enumeration_complete": class_enumeration_complete,
        "class_enumeration_blocker": domain.get("incomplete_reason"),
        "semantic_resolution_complete": not unresolved,
        "optimization_closed": semantic_domain_enumerated and not unresolved,
        "unresolved_blockers": blockers,
    }


def owner_usage(plane_a_uses, plane_b_uses, sprite_families, palettes, pc080sn, pc090oj, plane_b_states):
    stats = defaultdict(lambda: {"owners": set(), "palette_banks": set(), "sprite_families": set(),
                                "sprite_frames": set(), "physical_patterns": set(), "pixel_count": 0,
                                "logical_tile_count": 0, "map_cell_weight": 0, "plane_b_state_count": 0,
                                "owner_usage": defaultdict(lambda: {"pixel_count": 0,
                                                                    "logical_tile_count": 0,
                                                                    "map_cell_weight": 0,
                                                                    "physical_patterns": set()})})
    def add_pattern(owner, bank, raw, weight, identity, logical=False, family=None, frame=None):
        px = Counter(pixels16(raw) if len(raw) == 128 else pixels8(raw))
        for index, count in px.items():
            if index == 0: continue
            word = int(palettes[bank]["entries"][index]["arcade_xbgr555"], 16)
            s = stats[word]; s["owners"].add(owner); s["palette_banks"].add(bank)
            s["physical_patterns"].add(identity); s["pixel_count"] += count * weight
            if logical: s["logical_tile_count"] += 1
            s["map_cell_weight"] += weight
            os = s["owner_usage"][owner]
            os["pixel_count"] += count * weight
            os["map_cell_weight"] += weight
            os["physical_patterns"].add(identity)
            if logical: os["logical_tile_count"] += 1
            if family: s["sprite_families"].add(family)
            if frame: s["sprite_frames"].add(frame)
    for use in plane_a_uses:
        raw = pc080sn[use["tile_code"] * 32:(use["tile_code"] + 1) * 32]
        add_pattern("plane_a", use["palette_bank"], raw, use["map_cell_count"], use["physical_pattern"], True)
    for use in plane_b_uses:
        raw = pc080sn[use["tile_code"] * 32:(use["tile_code"] + 1) * 32]
        add_pattern("plane_b", use["palette_bank"], raw, use["map_cell_count"], use["physical_pattern"], True)
    for fam in sprite_families:
        for code in fam["codes"]:
            raw = pc090oj[code * 128:(code + 1) * 128]
            for bank in fam["palette_banks"]:
                add_pattern("sprite", bank, raw, 1, sha(raw), family=fam["name"], frame=f"{fam['id']}:{code:04X}")
    for stat in stats.values():
        stat["plane_b_state_count"] = sum(
            1 for state in plane_b_states
            if set(state["palette_banks"]) & stat["palette_banks"] and "plane_b" in stat["owners"]
        )
    rows = []
    for word, s in stats.items():
        g = compiler.arcade_xbgr555_to_genesis(word)
        per_owner = {}
        for owner, values in s.pop("owner_usage").items():
            per_owner[owner] = {
                **values,
                "physical_patterns": sorted(values["physical_patterns"]),
                "physical_pattern_count": len(values["physical_patterns"]),
            }
        rows.append({"color_id": f"arcade_{word:04X}", "arcade_xbgr555": f"0x{word:04X}",
                     "arcade_rgb": rgb_from_arcade(word), "lab": [round(v, 5) for v in rgb_lab(rgb_from_arcade(word))],
                     "genesis_cram": f"0x{g:04X}", "genesis_rgb": rgb_from_genesis(g),
                     "owner_usage": per_owner,
                     **{k: sorted(v) if isinstance(v, set) else v for k, v in s.items()}})
    return sorted(rows, key=lambda r: int(r["arcade_xbgr555"], 16))


def near_clusters(colors):
    out = {str(t): [] for t in (1, 2, 3, 5, 8)}
    for i, a in enumerate(colors):
        for b in colors[i + 1:]:
            de = delta_e_2000(a["lab"], b["lab"])
            if de <= 8:
                row = {"a": a["color_id"], "b": b["color_id"], "delta_e_2000": round(de, 4),
                       "exact_source_equal": False, "genesis_equal": a["genesis_cram"] == b["genesis_cram"],
                       "owners": sorted(set(a["owners"]) | set(b["owners"])),
                       "potential_entry_saving": 1}
                for threshold in (1, 2, 3, 5, 8):
                    if de <= threshold: out[str(threshold)].append(row)
    return out


def color_reuse_summary(colors):
    owner_sets = {owner: {row["arcade_xbgr555"] for row in colors if owner in row["owners"]}
                  for owner in ("sprite", "plane_a", "plane_b")}
    genesis_groups = defaultdict(list)
    for row in colors:
        genesis_groups[row["genesis_cram"]].append(row["arcade_xbgr555"])
    return {
        "exact_source_colors_shared_by_multiple_sprite_families": sum(
            1 for row in colors if len(row["sprite_families"]) > 1),
        "distinct_arcade_color_groups_collapsing_to_one_genesis_value": sum(
            1 for values in genesis_groups.values() if len(set(values)) > 1),
        "sprite_plane_a_exact_reuse": len(owner_sets["sprite"] & owner_sets["plane_a"]),
        "sprite_plane_b_exact_reuse": len(owner_sets["sprite"] & owner_sets["plane_b"]),
        "plane_a_plane_b_exact_reuse": len(owner_sets["plane_a"] & owner_sets["plane_b"]),
        "all_three_exact_reuse": len(set.intersection(*owner_sets.values())),
    }


def palette_pair_candidates(palettes, first_bank, second_bank, first_indices=None, second_indices=None):
    first_indices = first_indices or range(1, 16)
    second_indices = second_indices or range(1, 16)
    rows = []
    for ai in first_indices:
        a = palettes[first_bank]["entries"][ai]
        for bi in second_indices:
            b = palettes[second_bank]["entries"][bi]
            rows.append({"a_bank": first_bank, "a_index": ai, "a_rgb": a["arcade_rgb"],
                         "a_genesis": a["genesis_cram"], "b_bank": second_bank,
                         "b_index": bi, "b_rgb": b["arcade_rgb"], "b_genesis": b["genesis_cram"],
                         "exact_source_equal": a["arcade_xbgr555"] == b["arcade_xbgr555"],
                         "genesis_equal": a["genesis_cram"] == b["genesis_cram"],
                         "delta_e_2000": round(delta_e_2000(a["lab"], b["lab"]), 4)})
    return sorted(rows, key=lambda row: row["delta_e_2000"])


def cross_owner_questions(palettes):
    # Green/brown index sets are selected by source RGB category, not by a guessed semantic
    # pixel label.  The output explicitly says where art-level identity remains unproven.
    rastan_green = [entry["index"] for entry in palettes[0x33]["entries"][1:]
                    if entry["arcade_rgb"][1] > entry["arcade_rgb"][0] * 1.2 and
                    entry["arcade_rgb"][1] > entry["arcade_rgb"][2] * 1.2]
    lizard_green = [entry["index"] for entry in palettes[0x36]["entries"][1:]
                    if entry["arcade_rgb"][1] > entry["arcade_rgb"][0] * 1.2 and
                    entry["arcade_rgb"][1] > entry["arcade_rgb"][2] * 1.2]
    return {
        "rastan_eye_green_vs_lizardman": {
            "status": "palette-level candidates proven; the exact Rastan eye pixel index is not labeled by original data",
            "coexistence": True,
            "closest_pairs": palette_pair_candidates(palettes, 0x33, 0x36, rastan_green, lizard_green)[:8],
        },
        "rastan_brown_vs_bats": {
            "status": "unresolved: Stage-1 bat object attribute nibble remains class-state dependent",
            "coexistence": True,
            "entry_saving_authorized": False,
            "reason": "The analyzer will not assign a bat palette bank from artwork appearance or Genesis output."
        }
    }


def clustered_color_count(values, color_labs, threshold):
    """Conservative greedy cover used only for advisory near-color pressure.

    The representative is always an existing target color; this does not emit assets or
    authorize an approximation.  Exact optimization never calls this function.
    """
    representatives = []
    for value in sorted(values):
        if not any(delta_e_2000(color_labs[value], color_labs[rep]) <= threshold
                   for rep in representatives):
            representatives.append(value)
    return len(representatives)


def bank_colors(bank, palettes, used_only=None):
    indices = used_only.get(bank, set(range(1, 16))) if used_only else set(range(1, 16))
    return {palettes[bank]["entries"][i]["genesis_cram"] for i in indices if i != 0}


def partition_banks(banks, palettes, used_by_bank, line_count, limit=15):
    banks = sorted(set(banks), key=lambda b: -len(bank_colors(b, palettes, used_by_bank)))
    best = None
    lines = [set() for _ in range(line_count)]; assignment = [[] for _ in range(line_count)]
    def walk(pos):
        nonlocal best
        if pos == len(banks):
            score = sum(len(x) for x in lines)
            candidate = (score, [list(x) for x in assignment], [sorted(x) for x in lines])
            if best is None or candidate[0] < best[0]: best = candidate
            return
        b = banks[pos]; colors = bank_colors(b, palettes, used_by_bank)
        for idx in range(line_count):
            union = lines[idx] | colors
            if len(union) <= limit:
                old = lines[idx]; lines[idx] = union; assignment[idx].append(b)
                walk(pos + 1)
                assignment[idx].pop(); lines[idx] = old
            if not assignment[idx]: break
    walk(0)
    return best


def used_indices(owner_uses, pc080sn, sprite_families, pc090oj):
    out = defaultdict(set)
    for use in owner_uses:
        out[use["palette_bank"]].update(pixels8(pc080sn[use["tile_code"] * 32:(use["tile_code"] + 1) * 32]))
    for fam in sprite_families:
        for bank in fam["palette_banks"]:
            for code in fam["codes"]:
                out[bank].update(pixels16(pc090oj[code * 128:(code + 1) * 128]))
    return {k: v - {0} for k, v in out.items()}


def optimize(policy, palettes, plane_a_uses, plane_b_uses, sprite_families, pc080sn,
             pc090oj, semantic_states, sprite_coverage, threshold=0):
    # Approximate runs report entry-pressure only; they never emit remapped production bytes.
    a_used = used_indices(plane_a_uses, pc080sn, [], pc090oj)
    b_used = used_indices(plane_b_uses, pc080sn, [], pc090oj)
    s_used = used_indices([], pc080sn, sprite_families, pc090oj)
    abanks, bbanks = sorted(a_used), sorted(b_used)
    sbanks = sorted(s_used)
    sprite_fit = partition_banks(sbanks, palettes, s_used, policy["sprite_lines"])
    a_fit = partition_banks(abanks, palettes, a_used, policy["plane_a_lines"])
    b_fit = partition_banks(bbanks, palettes, b_used, policy["plane_b_lines"])
    known_subset_fixed = bool(sprite_fit and a_fit and b_fit)
    state_rows, semantic_ok = [], True
    for state in semantic_states:
        aset = state["plane_a_banks"]
        bset = state["plane_b_banks"]
        a_colors = set().union(*(bank_colors(b, palettes, a_used) for b in aset)) if aset else set()
        b_colors = set().union(*(bank_colors(b, palettes, b_used) for b in bset)) if bset else set()
        s_colors = set().union(*(bank_colors(b, palettes, s_used) for b in sbanks)) if sbanks else set()
        af = partition_banks(aset, palettes, a_used, policy["plane_a_lines"])
        bf = partition_banks(bset, palettes, b_used, policy["plane_b_lines"])
        sf = sprite_fit
        ok = bool(af and bf and sf); semantic_ok &= ok
        state_rows.append({"state_id": state["state_id"], "feasible": ok,
                           "sprite_exact_distinct_colors": len(s_colors),
                           "plane_a_exact_distinct_colors": len(a_colors),
                           "plane_b_exact_distinct_colors": len(b_colors),
                           "sprite_color_pressure_per_line": max((len(x) for x in sf[2]), default=0) if sf else None,
                           "plane_a_color_pressure_per_line": max((len(x) for x in af[2]), default=0) if af else None,
                           "plane_b_color_pressure_per_line": max((len(x) for x in bf[2]), default=0) if bf else None})
    pressures = {
        "sprite": len(set().union(*(bank_colors(b, palettes, s_used) for b in sbanks))) if sbanks else 0,
        "plane_a_fixed_union": len(set().union(*(bank_colors(b, palettes, a_used) for b in abanks))) if abanks else 0,
        "plane_b_fixed_union": len(set().union(*(bank_colors(b, palettes, b_used) for b in bbanks))) if bbanks else 0
    }
    deficits = {"sprites": 0 if sprite_fit else max(0, len(set().union(*(bank_colors(b, palettes, s_used) for b in sbanks))) - policy["sprite_lines"] * 15),
                "plane_a": 0 if a_fit else max(0, pressures["plane_a_fixed_union"] - policy["plane_a_lines"] * 15),
                "plane_b": 0 if b_fit else max(0, pressures["plane_b_fixed_union"] - policy["plane_b_lines"] * 15)}
    advisory = None
    if threshold:
        color_labs = {}
        for palette in palettes.values():
            for entry in palette["entries"][1:]:
                color_labs.setdefault(entry["genesis_cram"], entry["lab"])
        owner_values = {
            "sprites": set().union(*(bank_colors(b, palettes, s_used) for b in sbanks)) if sbanks else set(),
            "plane_a": set().union(*(bank_colors(b, palettes, a_used) for b in abanks)) if abanks else set(),
            "plane_b": set().union(*(bank_colors(b, palettes, b_used) for b in bbanks)) if bbanks else set(),
        }
        advisory = {}
        for owner, values in owner_values.items():
            line_count = policy["sprite_lines"] if owner == "sprites" else 1
            reduced = clustered_color_count(values, color_labs, threshold)
            advisory[owner] = {
                "exact_distinct_target_colors": len(values),
                "advisory_clustered_colors": reduced,
                "candidate_entry_savings": len(values) - reduced,
                "line_capacity": line_count * 15,
                "advisory_capacity_fit": reduced <= line_count * 15,
            }
    known_subset_semantic = semantic_ok
    coverage_complete = sprite_coverage["optimization_closed"]
    return {"model": "fixed and semantic exact packing" if threshold == 0 else f"decision-support near-color threshold deltaE<={threshold}",
            "threshold": threshold, "exact_only_assets": threshold == 0,
            "coverage_complete": coverage_complete,
            "fixed_feasible": known_subset_fixed if coverage_complete else False,
            "semantic_state_feasible": known_subset_semantic if coverage_complete else False,
            "known_resolved_subset_fixed_feasible": known_subset_fixed,
            "known_resolved_subset_semantic_feasible": known_subset_semantic,
            "fixed_assignments": ({"sprites": sprite_fit[1:] if sprite_fit else None,
                                   "plane_a": a_fit[1:] if a_fit else None,
                                   "plane_b": b_fit[1:] if b_fit else None}
                                  if coverage_complete else None),
            "known_resolved_subset_assignments": {
                "sprites": sprite_fit[1:] if sprite_fit else None,
                "plane_a": a_fit[1:] if a_fit else None,
                "plane_b": b_fit[1:] if b_fit else None,
            },
            "unresolved_class_blockers": sprite_coverage["unresolved_blockers"],
            "pressures": pressures, "deficits": deficits, "semantic_states": state_rows,
            "near_color_advisory": advisory,
            "objective_order": ["exact target colors", "legal coexistence", "pattern capacity", "fewest state transitions", "fewest variants", "least DMA", "stable ownership"],
            "note": (
                "Only proven object-to-palette relationships enter color packing. Unknown-bank art "
                "has no assigned colors. The known resolved subset is reported for diagnostics, but "
                "overall feasibility fails closed while any legal graphics-bearing class is unresolved. "
                "Near-color thresholds are advisory only; no approximate merge or asset was generated."
            )}


def pattern_report(plane_a_uses, plane_b_uses, sprite_frames, pc080sn, pc090oj,
                   capacities, semantic_states, sprite_coverage):
    by_owner = {}
    for owner, uses in (("plane_a", plane_a_uses), ("plane_b", plane_b_uses)):
        raws = [pc080sn[u["tile_code"] * 32:(u["tile_code"] + 1) * 32] for u in uses]
        exact = {sha(r) for r in raws}
        normalized = {min(sha(flip8(r, h, v)) for h, v in ((0,0),(1,0),(0,1),(1,1))) for r in raws}
        by_owner[owner] = {"logical_uses": len(uses), "source_patterns": len(raws), "exact_patterns": len(exact),
                           "flip_normalized_patterns": len(normalized), "exact_dedup_savings": len(raws)-len(exact),
                           "flip_equivalent_savings": len(exact)-len(normalized)}
    sprite_codes = [component["code"] for frame in sprite_frames for component in frame["component_cells"]]
    sprite_raw = [pc090oj[code * 128:(code + 1) * 128] for code in sprite_codes]
    by_owner["sprites"] = {"logical_frames": len(sprite_frames), "source_cells": len(sprite_raw),
                            "exact_cells": len({sha(r) for r in sprite_raw}),
                            "required_8x8_patterns": len({sha(r) for r in sprite_raw}) * 4,
                            "flip_normalization": "not applied: composite transform not proven",
                            "coverage_complete": sprite_coverage["optimization_closed"],
                            "unresolved_class_count": sprite_coverage["counts"]["unresolved"],
                            "capacity_interpretation": (
                                "exact" if sprite_coverage["optimization_closed"] else
                                "known lower bound only; unresolved classes conservatively block PASS"
                            )}
    state_rows = []
    for state in semantic_states:
        active = set(state["records"])
        hashes = {use["physical_pattern"] for use in plane_a_uses
                  if active & set(use["records"])}
        state["plane_a_physical_patterns"] = len(hashes)
        state["plane_a_capacity"] = capacities["plane_a_epoch_patterns"]
        state["plane_a_capacity_fit"] = len(hashes) <= capacities["plane_a_epoch_patterns"]
        state_rows.append({"state_id": state["state_id"],
                           "plane_a_physical_patterns": len(hashes),
                           "capacity": capacities["plane_a_epoch_patterns"],
                           "fits": state["plane_a_capacity_fit"]})
    by_owner["capacity_assessment"] = {
        "plane_a_semantic_states": state_rows,
        "plane_a_max_simultaneous_patterns": max((row["plane_a_physical_patterns"] for row in state_rows), default=0),
        "plane_a_global_vocabulary_is_not_simultaneous": by_owner["plane_a"]["exact_patterns"],
        "plane_b_fixed_patterns": by_owner["plane_b"]["exact_patterns"],
        "plane_b_capacity": capacities["plane_b_fixed_patterns"],
        "plane_b_capacity_fit": by_owner["plane_b"]["exact_patterns"] <= capacities["plane_b_fixed_patterns"],
        "sprite_required_8x8_patterns": by_owner["sprites"]["required_8x8_patterns"],
        "sprite_capacity": capacities["native_sprite_8x8_patterns"],
        "sprite_known_subset_capacity_fit": by_owner["sprites"]["required_8x8_patterns"] <= capacities["native_sprite_8x8_patterns"],
        "sprite_capacity_fit": (
            by_owner["sprites"]["required_8x8_patterns"] <= capacities["native_sprite_8x8_patterns"]
            and sprite_coverage["optimization_closed"]
        ),
        "sprite_capacity_blockers": sprite_coverage["unresolved_blockers"],
    }
    return by_owner, capacities


def render_tile(raw, palette, size=4):
    px = pixels16(raw) if len(raw) == 128 else pixels8(raw)
    side = 16 if len(raw) == 128 else 8
    im = Image.new("RGB", (side, side))
    im.putdata([tuple(palette[p]) for p in px])
    return im.resize((side * size, side * size), Image.Resampling.NEAREST)


def flip16_image(image, horizontal=False, vertical=False):
    if horizontal:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if vertical:
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return image


def neutral_sprite_palette():
    # Index-preserving neutral ramp: unknown palette identity remains visibly unresolved.
    return [(0, 0, 0)] + [(value, value, value) for value in range(17, 256, 17)]


def composite_image(frame, palettes, region, scale=3):
    components = frame["component_cells"]
    min_x = min(component["x"] for component in components)
    min_y = min(component["y"] for component in components)
    max_x = max(component["x"] for component in components) + 16
    max_y = max(component["y"] for component in components) + 16
    image = Image.new("RGBA", ((max_x - min_x) * scale, (max_y - min_y) * scale), (0, 0, 0, 0))
    if frame["palette_status"] == "proven" and frame["palette_banks"]:
        bank = frame["palette_banks"][0]
        palette = [entry["arcade_rgb"] for entry in palettes[bank]["entries"]]
    else:
        palette = neutral_sprite_palette()
    for component in components:
        code = component["code"]
        raw = region[code * 128:(code + 1) * 128]
        tile = render_tile(raw, palette, scale).convert("RGBA")
        source_pixels = pixels16(raw)
        alpha = Image.new("L", (16, 16)); alpha.putdata([255 if value else 0 for value in source_pixels])
        alpha = alpha.resize((16 * scale, 16 * scale), Image.Resampling.NEAREST)
        tile.putalpha(alpha)
        tile = flip16_image(tile, component.get("flip_h", 0), component.get("flip_v", 0))
        image.alpha_composite(tile, ((component["x"] - min_x) * scale,
                                     (component["y"] - min_y) * scale))
    return image


def sprite_atlas(path, frames, palettes, region, columns=4):
    rendered = [(frame, composite_image(frame, palettes, region)) for frame in frames]
    image_h = max((image.height for _, image in rendered), default=192)
    cell_w = max(max((image.width for _, image in rendered), default=192) + 24, 360)
    cell_h = image_h + 72
    rows = max(1, math.ceil(len(rendered) / columns))
    sheet = Image.new("RGBA", (columns * cell_w, rows * cell_h), (18, 18, 18, 255))
    draw = ImageDraw.Draw(sheet); font = ImageFont.load_default()
    for n, (frame, image) in enumerate(rendered):
        x = (n % columns) * cell_w + 12; y = (n // columns) * cell_h + 12
        sheet.alpha_composite(image, (x, y))
        label_y = y + image_h + 4
        title = f"{frame['family_name']} / {frame['frame_id']}"
        status = f"{len(frame['component_cells'])} cells; {frame['composite_status']}"
        draw.text((x, label_y), title[:56], fill="white", font=font)
        draw.text((x, label_y + 14), status[:56], fill="#ffd86b", font=font)
        palette_label = (
            ",".join(f"0x{bank:02X}" for bank in frame["palette_banks"])
            if frame["palette_status"] == "proven"
            else "PALETTE UNKNOWN; NEUTRAL RENDER"
        )
        draw.text((x, label_y + 28), palette_label, fill="#b9e4ff", font=font)
    path.parent.mkdir(parents=True, exist_ok=True); sheet.convert("RGB").save(path)


def atlas(path, entries, palettes, region, cell_bytes, columns=16, max_items=10000):
    entries = entries[:max_items]
    tile_side = 64 if cell_bytes == 128 else 48
    label_h = 22; rows = max(1, math.ceil(len(entries) / columns))
    im = Image.new("RGB", (columns * tile_side, rows * (tile_side + label_h)), (24,24,24))
    d = ImageDraw.Draw(im); font = ImageFont.load_default()
    for n, entry in enumerate(entries):
        code = entry.get("base_code", entry.get("tile_code")); bank = entry["palette_banks"][0] if "palette_banks" in entry else entry["palette_bank"]
        raw = region[code * cell_bytes:(code + 1) * cell_bytes]
        pal = [x["arcade_rgb"] for x in palettes[bank]["entries"]]
        art = render_tile(raw, pal, max(1, tile_side // (16 if cell_bytes == 128 else 8)))
        x = (n % columns) * tile_side; y = (n // columns) * (tile_side + label_h)
        im.paste(art.crop((0,0,tile_side,tile_side)), (x,y)); d.text((x+1,y+tile_side+2), f"{code:04X} p{bank:02X}", font=font, fill="white")
    path.parent.mkdir(parents=True, exist_ok=True); im.save(path)


def html_site(out, summary, colors, sprite_families, optimization, near, coexist,
              pattern_inventory, reuse, cross_owner, sprite_coverage):
    cards = "".join(f'<div class="color"><i style="background:rgb({c["arcade_rgb"][0]},{c["arcade_rgb"][1]},{c["arcade_rgb"][2]})"></i><b>{c["arcade_xbgr555"]}</b><small>{", ".join(c["owners"])}</small></div>' for c in colors)
    fam_rows = "".join(
        f"<tr><td>{f['name']}</td><td>{len(f['composites'])}</td><td>{f['physical_cells']}</td>"
        f"<td>{', '.join(f'{b:#04x}' for b in f['palette_banks']) or 'none'}</td>"
        f"<td>{', '.join(f'{b:#04x}' for b in f['palette_candidate_banks']) or 'none'}</td>"
        f"<td>{f['semantic_status']}</td></tr>" for f in sprite_families)
    near_rows = "".join(f"<tr><td>&le; {threshold}</td><td>{len(rows)}</td></tr>" for threshold, rows in near.items())
    body = f'''<!doctype html><meta charset="utf-8"><title>Round 1 Phase 1 Graphics Optimizer</title>
<style>body{{font:15px Georgia;background:#f3ead7;color:#201b16;margin:0}}header{{background:linear-gradient(120deg,#7d2418,#b94b22);color:#fff;padding:24px}}nav{{position:sticky;top:0;background:#201b16;padding:10px;z-index:2}}nav a{{color:#ffd86b;margin-right:18px}}section{{padding:22px;max-width:1200px;margin:auto}}img{{image-rendering:pixelated;max-width:100%;background:#111}}table{{border-collapse:collapse;width:100%}}td,th{{padding:7px;border-bottom:1px solid #bda98b;text-align:left}}.colors{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}}.color{{display:grid;grid-template-columns:38px 1fr;padding:7px;background:#fff}}.color i{{grid-row:1/3;width:30px;height:30px;border:1px solid #333}}small{{display:block}}code,pre{{background:#fff;padding:6px;overflow:auto}}.verdict{{font-size:1.2rem;border-left:8px solid #b94b22;padding:12px;background:#fff}}</style>
<header><h1>Round 1 / Phase 1 Graphics + Color Optimizer</h1><p>Original arcade ROM static compilation. No Genesis runtime state is an input.</p></header>
<nav><a href="#overview">Overview</a><a href="#sprites">Sprites</a><a href="#a">Plane A</a><a href="#b">Plane B</a><a href="#colors">Colors</a><a href="#coexist">Coexistence</a><a href="#fit">Exact 2+1+1</a><a href="#near">Near colors</a><a href="#patterns">Pattern/VRAM</a></nav>
<section id="overview"><h2>Overview</h2><p class="verdict">Sprite semantic closure: <b>{'YES' if sprite_coverage['optimization_closed'] else 'NO'}</b>. Fixed exact 2+1+1: <b>{'YES' if optimization['fixed_feasible'] else 'NO'}</b>. Semantic-state exact 2+1+1: <b>{'YES' if optimization['semantic_state_feasible'] else 'NO'}</b>. Known-subset figures are diagnostic only while unresolved legal classes remain.</p><pre>{json.dumps(summary,indent=2)}</pre></section>
<section id="sprites"><h2>Sprites</h2><p>Every currently established legal graphics-bearing class is classified as resolved or explicitly unresolved. Unknown-bank art is grayscale and contributes no colors. Unresolved classes conservatively block feasibility rather than being counted as zero. See the <a href="arcade_object_semantic_domain.json">original-arcade marker and record-loader domain</a>.</p><pre>{json.dumps(sprite_coverage,indent=2)}</pre><table><tr><th>Family</th><th>Composite records</th><th>Physical cells</th><th>Proven banks</th><th>Candidate banks (not colors)</th><th>Status</th></tr>{fam_rows}</table><img src="sprites/contact_sheet.png"></section>
<section id="a"><h2>Plane A</h2><p>Every distinct pattern + logical palette use.</p><img src="plane_a/contact_sheet.png"></section>
<section id="b"><h2>Plane B</h2><p>The fixed Round-1 physical vocabulary is rendered under the phase-local palette timeline.</p><label>Palette state <select id="bstate" onchange="document.getElementById('bsheet').src='plane_b/state_'+this.value.padStart(2,'0')+'.png'">{''.join(f'<option value="{n}">{n}</option>' for n in range(summary['plane_b_states']))}</select></label><img id="bsheet" src="plane_b/state_00.png"><p><a href="palette_states.json">State timeline and source banks</a></p></section>
<section id="colors"><h2>Master Colors</h2><input id="q" placeholder="filter" oninput="for(const e of document.querySelectorAll('.color'))e.hidden=!e.innerText.toLowerCase().includes(this.value.toLowerCase())"><div class="colors">{cards}</div></section>
<section id="coexist"><h2>Coexistence</h2><p>Unproven mutual exclusion is conservatively treated as coexistence.</p><pre>{json.dumps(coexist,indent=2)}</pre><h3>Exact reuse</h3><pre>{json.dumps(reuse,indent=2)}</pre><h3>Required comparisons</h3><pre>{json.dumps(cross_owner,indent=2)}</pre></section>
<section id="fit"><h2>Exact 2 Sprite + 1 B + 1 A</h2><pre>{json.dumps(optimization,indent=2)}</pre></section>
<section id="near"><h2>Near-color candidates</h2><p>CIEDE2000 clusters are decision support only. No approximate asset is emitted.</p><table><tr><th>Threshold</th><th>Candidate pairs</th></tr>{near_rows}</table><p>See <code>near_color_clusters.json</code> for owners, RGB values, quantized equality and savings.</p></section>
<section id="patterns"><h2>Pattern/VRAM</h2><pre>{json.dumps(pattern_inventory,indent=2)}</pre><p>Sprite flip normalization stays disabled until full-composite transformation is proven.</p></section>'''
    (out / "index.html").write_text(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--phase", type=int, required=True)
    ap.add_argument("--scene", type=int, default=1)
    ap.add_argument("--palette-policy", default="2sprite-1b-1a")
    ap.add_argument("--out", "--output", dest="out")
    ap.add_argument("--enemy-lexicon", type=Path,
                    help="optional whole-game lexicon optimizer_input.json; merged without replacing the established scope ledger")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    if args.enemy_lexicon:
        lexicon = json.loads(args.enemy_lexicon.read_text())
        scope_key = f"round{args.round}_phase{args.phase}"
        additions = lexicon.get("optimizer_classes_by_scope", {}).get(scope_key, [])
        profile = manifest["sprite_semantics"][f"round{args.round}"]
        known_ids = {entry["id"] for entry in profile["classes"]}
        additions = [entry for entry in additions if entry["id"] not in known_ids]
        profile["classes"].extend(additions)
        profile["legal_class_domain"]["class_ids"].extend(entry["id"] for entry in additions)
        profile["legal_class_domain"]["class_enumeration_complete"] = True
        profile["legal_class_domain"]["status"] = "whole-game static/dynamic fail-closed lexicon merged"
        profile["legal_class_domain"]["incomplete_reason"] = (
            "Legal candidate enumeration is closed fail-closed; unresolved semantic names, "
            "compositions, and palette relationships still block optimization closure."
        )
    if args.palette_policy not in manifest["palette_policies"]: raise SystemExit("unknown palette policy")
    policy = manifest["palette_policies"][args.palette_policy]
    out = Path(args.out) if args.out else ROOT / "analysis" / "graphics_optimizer" / f"round{args.round}_phase{args.phase}"
    out.mkdir(parents=True, exist_ok=True)
    mc = (ROOT / "build/regions/maincpu.bin").read_bytes()
    pc080sn = (ROOT / "build/regions/pc080sn.bin").read_bytes()
    pc090oj = (ROOT / "build/regions/pc090oj.bin").read_bytes()
    all_records, records, bprogress, descriptors, round_descriptors = resolve_scope(mc, args.round, args.phase)
    segments = [r["segment"] for r in records]
    a_cells, a_uses = decode_plane_a(mc, pc080sn, segments)
    b_uses, b_states = decode_plane_b(mc, pc080sn, round_descriptors, bprogress)
    sprite_families, sprite_frames = decode_sprites(pc090oj, manifest, args.round)
    profile_spec = manifest["sprite_semantics"][f"round{args.round}"]
    object_semantic_domain = decode_arcade_object_semantic_domain(mc, a_cells, profile_spec)
    sprite_coverage = sprite_class_coverage(sprite_families, profile_spec, object_semantic_domain)
    proven_sprite_banks = {bank for family in sprite_families for bank in family["palette_banks"]}
    all_banks = {u["palette_bank"] for u in a_uses + b_uses} | proven_sprite_banks
    palettes = decode_palettes(mc, all_banks, args.scene)
    colors = owner_usage(a_uses, b_uses, sprite_families, palettes, pc080sn, pc090oj, b_states)
    near = near_clusters(colors)
    # Epochs are the proven producer-semantic groups used by the current offline compiler.
    epoch_defs = compiler.BOUNDARY_PHASE1_EPOCH_RECORDS
    semantic_states = []
    for idx, group in enumerate(epoch_defs):
        active_records = [s for s in group if s in segments]
        if not active_records: continue
        semantic_states.append({"state_id": f"plane_a_epoch_{idx}", "records": active_records,
                                "plane_a_banks": sorted({u["palette_bank"] for u in a_uses if set(u["records"]) & set(active_records)}),
                                "plane_b_banks": sorted({b for state in b_states if state["record"] in active_records for b in state["palette_banks"]}),
                                "sprite_families": [f["id"] for f in sprite_families],
                                "conservative": True})
    used_a = used_indices(a_uses, pc080sn, [], pc090oj); used_b = used_indices(b_uses, pc080sn, [], pc090oj)
    used_s = used_indices([], pc080sn, sprite_families, pc090oj)
    capacities = manifest["target_capacity"]
    pattern_inventory, capacities = pattern_report(
        a_uses, b_uses, sprite_frames, pc080sn, pc090oj, capacities, semantic_states,
        sprite_coverage)
    optimization = optimize(policy, palettes, a_uses, b_uses, sprite_families,
                            pc080sn, pc090oj, semantic_states, sprite_coverage)
    scope = {"schema_version": 1, "round": args.round, "scene": args.scene, "phase": args.phase,
             "records": records, "segments": segments,
             "phase_plane_b_descriptors": descriptors,
             "round_plane_b_descriptors": round_descriptors,
             "source_authority": ["build/regions/maincpu.bin", "build/regions/pc080sn.bin", "build/regions/pc090oj.bin"],
             "source_sha256": {"maincpu": sha(mc), "pc080sn": sha(pc080sn), "pc090oj": sha(pc090oj)},
             "mame_capture_is_input": False, "policy": args.palette_policy}
    distinct_b_states = {}
    for state in b_states:
        key = tuple(state["palette_banks"])
        distinct_b_states.setdefault(key, {"palette_banks": state["palette_banks"], "records": [], "triggers": []})
        distinct_b_states[key]["records"].append(state["record"])
        distinct_b_states[key]["triggers"].append(state["trigger"])
    palette_states = {"palettes": list(palettes.values()), "plane_b_state_timeline": b_states,
                      "plane_b_distinct_states": list(distinct_b_states.values()),
                      "sprite_colbank": {"sprite_ctrl": "0x0060", "base": "0x30", "legal_effective_banks": [f"0x{x:02X}" for x in range(0x30,0x40)],
                                         "formula": "(sprite_ctrl & 0xE0) >> 1 | (object_attr & 0x0F)"}}
    source_proof = {
        "production_inputs": ["build/regions/maincpu.bin", "build/regions/pc080sn.bin",
                              "build/regions/pc090oj.bin"],
        "mame_is_semantics_proof_not_generated_asset_input": True,
        "palette_scene_loader": {
            "scene_record_table": "arcade_rom/data 0x03BA88",
            "record_stride": 32,
            "palette_block_pool": "arcade_rom/data 0x04FD02",
            "staging": "arcade_workram a5+0x1600",
            "producer": "arcade_pc FUN_0003BA20",
            "publish_low_banks": "arcade_pc FUN_00045D7C -> banks 0..31",
            "publish_sprite_banks": "arcade_pc FUN_00045DC4 -> banks 48..79",
        },
        "pc090oj_color_semantics": {
            "rastan_driver": "sprite_colbank=(sprite_ctrl&0xe0)>>1",
            "pc090oj_device": "effective color=(object_attr&0x0f)|sprite_colbank",
            "round1_sprite_ctrl": "0x0060",
            "round1_legal_effective_banks": [f"0x{x:02X}" for x in range(0x30, 0x40)],
            "requested_49_to_127_resolution": (
                "banks 49..63 are legal Round-1 choices and are decoded from the scene palette "
                "publisher; banks 64..127 cannot be selected under Round-1 sprite_ctrl 0x60"
            ),
            "optimizer_rule": (
                "Only a proven object-to-palette-bank relationship contributes colored sprite data. "
                "Legal candidate ranges remain metadata and blockers; they do not enter colors.json, "
                "coexistence color counts, or the two-sprite-line solver."
            ),
        },
        "representative_original_arcade_mame_proof": {
            "path": "states/traces/gameplay_hud_suppression_lizard_palette_20260719_124512/arcpal.txt",
            "frame": 300,
            "bank_0x33": ["0x0000", "0x0842", "0x739C", "0x429E", "0x2154", "0x190C", "0x0012", "0x000C", "0x03DE", "0x01DE", "0x0240", "0x0180", "0x4A52", "0x318C", "0x0100", "0x001E"],
            "bank_0x36": ["0x0000", "0x4318", "0x00C0", "0x0246", "0x01C0", "0x030E", "0x2948", "0x318A", "0x6356", "0x6B9A", "0x10D2", "0x2996", "0x210A", "0x380E", "0x01CE", "0x39CE"],
            "note": "The trace directly labels and captures effective arcade banks 0x33 and 0x36."
        },
    }
    coexist = {"rule": "unproven mutual exclusion is treated as coexistence; unknown palette requirements block exact color feasibility",
               "nodes": [f["id"] for f in sprite_families] + [s["state_id"] for s in semantic_states],
               "complete_sprite_clique": True, "semantic_states": [s["state_id"] for s in semantic_states],
               "sprite_classes": [{
                   "id": family["id"],
                   "proven_palette_banks": [f"0x{bank:02X}" for bank in family["palette_banks"]],
                   "unknown_palette_candidates": [f"0x{bank:02X}" for bank in family["palette_candidate_banks"]],
                   "color_requirement": "known" if family["palette_banks"] else "unknown",
                   "feasibility": "included" if family["palette_banks"] else "conservative blocker",
               } for family in sprite_families]}
    equivalence = {"owners": pattern_inventory, "variant_rule": "same source pattern with incompatible exact target index maps requires a physical variant",
                   "sprite_flip_normalization": "disabled until complete composite transform is proven"}
    reuse = color_reuse_summary(colors)
    cross_owner = cross_owner_questions(palettes)
    statistics = {
        "top_sprite_colors_by_family_count": sorted(
            (row for row in colors if "sprite" in row["owners"]),
            key=lambda row: (len(row["sprite_families"]), row["owner_usage"]["sprite"]["pixel_count"]),
            reverse=True)[:32],
        "top_plane_a_colors_by_logical_tile_count": sorted(
            (row for row in colors if "plane_a" in row["owners"]),
            key=lambda row: row["owner_usage"]["plane_a"]["logical_tile_count"],
            reverse=True)[:32],
        "top_plane_a_colors_by_map_usage": sorted(
            (row for row in colors if "plane_a" in row["owners"]),
            key=lambda row: row["owner_usage"]["plane_a"]["map_cell_weight"],
            reverse=True)[:32],
        "top_plane_b_colors_by_map_usage": sorted(
            (row for row in colors if "plane_b" in row["owners"]),
            key=lambda row: row["owner_usage"]["plane_b"]["map_cell_weight"],
            reverse=True)[:32],
        "sprite_family_count": len(sprite_families),
        "complete_or_explicitly_unresolved_composite_records": len(sprite_frames),
    }
    dump(out / "scope.json", scope); dump(out / "sprite_families.json", sprite_families)
    dump(out / "sprite_frames.json", sprite_frames); dump(out / "plane_a_uses.json", a_uses)
    dump(out / "sprite_class_coverage.json", sprite_coverage)
    dump(out / "arcade_object_semantic_domain.json", object_semantic_domain)
    dump(out / "plane_b_uses.json", b_uses); dump(out / "palette_states.json", palette_states)
    dump(out / "colors.json", colors); dump(out / "color_usage.json", colors)
    dump(out / "near_color_clusters.json", near); dump(out / "semantic_states.json", semantic_states)
    dump(out / "coexistence_graph.json", coexist); dump(out / "pattern_inventory.json", {"owners": pattern_inventory, "capacities": capacities})
    dump(out / "pattern_equivalence.json", equivalence)
    dump(out / "source_proof.json", source_proof)
    dump(out / "color_reuse_summary.json", reuse)
    dump(out / "cross_owner_opportunities.json", cross_owner)
    dump(out / "statistics.json", statistics)
    for threshold in (0, 1, 2, 3, 5, 8):
        result = optimization if threshold == 0 else optimize(
            policy, palettes, a_uses, b_uses, sprite_families, pc080sn, pc090oj,
            semantic_states, sprite_coverage, threshold)
        name = "exact" if threshold == 0 else f"de{threshold}"
        dump(out / "optimization" / f"policy_{args.palette_policy.replace('-', '_')}_{name}.json", result)
    dry = {"status": "dry-run-blocked", "production_connected": False, "exact_feasible": optimization["semantic_state_feasible"],
           "palette_policy": policy, "target_palettes": optimization["fixed_assignments"],
           "reindexer": "tools/translation/reindex_graphics_for_palette.py", "capacity": capacities,
           "asset_bytes_emitted": False,
           "reason": "Unresolved legal graphics-bearing sprite classes block exact feasibility. Unknown object palette banks are not assigned colors; near-color runs are advisory only."}
    dump(out / "candidate_assets" / "manifest.json", dry)
    dump(out / "optimizer_config.json", {"policy_id": args.palette_policy, **policy})
    sprite_atlas(out / "sprites" / "contact_sheet.png", sprite_frames, palettes, pc090oj)
    atlas(out / "plane_a" / "contact_sheet.png", a_uses, palettes, pc080sn, 32, 16)
    atlas(out / "plane_b" / "contact_sheet.png", b_uses, palettes, pc080sn, 32, 16)
    for state_number, state in enumerate(distinct_b_states.values()):
        state_banks = set(state["palette_banks"])
        state_uses = [use for use in b_uses if use["palette_bank"] in state_banks]
        atlas(out / "plane_b" / f"state_{state_number:02d}.png",
              state_uses, palettes, pc080sn, 32, 16)
    owner_color_counts = {owner: sum(1 for row in colors if owner in row["owners"])
                          for owner in ("sprite", "plane_a", "plane_b")}
    owner_genesis_counts = {owner: len({row["genesis_cram"] for row in colors if owner in row["owners"]})
                            for owner in ("sprite", "plane_a", "plane_b")}
    summary = {"sprite_families": len(sprite_families), "sprite_frames": len(sprite_frames),
               "sprite_classes_resolved": sprite_coverage["counts"]["resolved"],
               "sprite_classes_unresolved": sprite_coverage["counts"]["unresolved"],
               "sprite_semantic_domain_enumerated": sprite_coverage["semantic_domain_enumerated"],
               "sprite_semantic_resolution_complete": sprite_coverage["semantic_resolution_complete"],
               "plane_a_logical_uses": len(a_uses), "plane_a_physical_patterns": len({u['physical_pattern'] for u in a_uses}),
               "plane_a_banks": [f"0x{x:03X}" for x in sorted(used_a)],
               "plane_b_logical_uses": len(b_uses), "plane_b_physical_patterns": len({u['physical_pattern'] for u in b_uses}),
               "plane_b_banks": [f"0x{x:03X}" for x in sorted(used_b)],
               "plane_b_state_events": len(b_states), "plane_b_states": len(distinct_b_states),
               "sprite_banks": [f"0x{x:02X}" for x in sorted(used_s)], "source_colors": len(colors),
               "genesis_distinct_colors": len({c['genesis_cram'] for c in colors}),
               "source_colors_by_owner": owner_color_counts,
               "genesis_colors_by_owner": owner_genesis_counts,
               "plane_a_max_simultaneous_patterns": pattern_inventory["capacity_assessment"]["plane_a_max_simultaneous_patterns"],
               "all_pattern_capacity_checks_pass": sprite_coverage["optimization_closed"] and all(
                   row["fits"] for row in pattern_inventory["capacity_assessment"]["plane_a_semantic_states"]
               ) and pattern_inventory["capacity_assessment"]["plane_b_capacity_fit"] and pattern_inventory["capacity_assessment"]["sprite_capacity_fit"],
               "fixed_exact": optimization["fixed_feasible"], "semantic_exact": optimization["semantic_state_feasible"]}
    dump(out / "summary.json", summary)
    html_site(out, summary, colors, sprite_families, optimization, near, coexist,
              pattern_inventory, reuse, cross_owner, sprite_coverage)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
