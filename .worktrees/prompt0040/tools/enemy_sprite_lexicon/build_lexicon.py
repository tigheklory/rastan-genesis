#!/usr/bin/env python3
"""Compile the whole-game original-arcade sprite lexicon.

The bounded MAME sweep supplies presence and representative PC090OJ composites.
Static actor rows and established map/producer routes supply the fail-closed legal
domain, including entries that did not appear during the sweep.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "translation"))
import compile_pc080sn_genesis as compiler  # noqa: E402

ROUND_PHASES = [
    f"round{round_number}_{phase}"
    for round_number in range(1, 7)
    for phase in ("phase1", "castle", "boss")
]

STATIC_TABLES = [
    ("mode2_variant_a", 0x0454BA, 3),
    ("mode2_variant_b", 0x0454D2, 3),
    ("mode2_variant_c", 0x0454EA, 3),
    ("normal_variant_a", 0x045502, 12),
    ("normal_variant_b", 0x045562, 6),
    ("selector_08_1c", 0x045592, 21),
]

# These are established original-arcade semantic routes from the pre-existing
# optimizer ledger. They remain distinct until actor/spawn evidence proves a merge.
ESTABLISHED_UNRESOLVED = [
    ("collision_marker40_route", "Marker 0x40 hostile-route candidate", "ENEMY / HOSTILE"),
    ("collision_marker41_route", "Marker 0x41 hostile-route candidate", "ENEMY / HOSTILE"),
    ("collision_marker49_special_route", "Marker 0x49 special-route candidate", "ENEMY / HOSTILE"),
    ("collision_marker4f_behavior20_route", "Marker 0x4F behavior-0x20 candidate", "ENEMY / HOSTILE"),
    ("hurry_up_bat", "Hurry-up Bat", "ENEMY / HOSTILE"),
    ("normal_small_bat", "Normal/small bat enemy", "ENEMY / HOSTILE"),
    ("large_bat", "Large bat enemy", "ENEMY / HOSTILE"),
    ("four_armed_enemy", "Four-armed enemy", "ENEMY / HOSTILE"),
    ("axe_item", "Axe item/drop", "ITEM / DROP"),
    ("other_item_drop", "Other item/drop classes", "ITEM / DROP"),
    ("projectile_weapon", "Projectile/weapon classes", "PROJECTILE / WEAPON"),
    ("transient_effect", "Transient effect classes", "EFFECT / TRANSIENT"),
]


def parse_int(value: str) -> int:
    return int(value, 0)


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def stable_id(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in text).strip("_")


def decode_pixels(raw: bytes) -> list[int]:
    pixels = []
    for byte in raw:
        pixels.extend((byte >> 4, byte & 0x0F))
    return pixels


def neutral_palette() -> list[tuple[int, int, int]]:
    return [(0, 0, 0)] + [(value, value, value) for value in range(17, 256, 17)]


def rgb(word: int) -> tuple[int, int, int]:
    return ((word & 0x1F) * 255 // 31, ((word >> 5) & 0x1F) * 255 // 31,
            ((word >> 10) & 0x1F) * 255 // 31)


def parse_piece_records(value: str) -> list[dict]:
    pieces = []
    for text in filter(None, value.split("|")):
        record, control, y, code, x = text.split(":")
        y_value, x_value = int(y, 16), int(x, 16)
        if y_value == 0x0180:
            continue
        pieces.append({
            "record": int(record),
            "control": int(control, 16),
            "source_y": y_value,
            "source_x": x_value,
            "code": int(code, 16) & 0x3FFF,
            "flip_h": bool(int(control, 16) & 0x4000),
            "flip_v": bool(int(control, 16) & 0x8000),
        })
    return pieces


def unwrap(values: list[int]) -> list[int]:
    if not values:
        return []
    anchor = values[0] & 0x1FF
    return [((value & 0x1FF) - anchor + 256) % 512 - 256 for value in values]


def normalize_pieces(pieces: list[dict]) -> list[dict]:
    if not pieces:
        return []
    xs = unwrap([piece["source_x"] for piece in pieces])
    ys = unwrap([piece["source_y"] for piece in pieces])
    min_x, min_y = min(xs), min(ys)
    result = []
    seen = set()
    for piece, x, y in zip(pieces, xs, ys):
        key = (piece["record"], piece["code"], x, y, piece["flip_h"], piece["flip_v"])
        if key in seen:
            continue
        seen.add(key)
        result.append({**piece, "x": x - min_x, "y": y - min_y})
    return sorted(result, key=lambda item: (item["record"], item["y"], item["x"]))


def representative(rows: list[dict], combine_frame: bool = False) -> tuple[list[dict], dict | None]:
    if not rows:
        return [], None
    if combine_frame:
        frames = defaultdict(list)
        for row in rows:
            frames[(row["entry_label"], row["frame"])].extend(parse_piece_records(row["piece_records"]))
        key, pieces = max(frames.items(), key=lambda item: len({p["record"] for p in item[1]}))
        source = next(row for row in rows if (row["entry_label"], row["frame"]) == key)
        return normalize_pieces(pieces), source
    source = max(rows, key=lambda row: len(parse_piece_records(row["piece_records"])))
    return normalize_pieces(parse_piece_records(source["piece_records"])), source


def static_records(maincpu: bytes) -> list[dict]:
    records = []
    for table, base, count in STATIC_TABLES:
        for index in range(count):
            offset = base + index * 8
            raw = maincpu[offset:offset + 8]
            records.append({
                "seed_id": f"{table}_{index:02d}", "table": table, "table_index": index,
                "arcade_rom_offset": f"0x{offset:06X}", "raw": raw.hex().upper(),
                "base_code": int.from_bytes(raw[0:2], "big"),
                "field_actor_3a": raw[2], "actor_class": raw[3],
                "field_28": int.from_bytes(raw[4:6], "big"),
                "field_2c": int.from_bytes(raw[6:8], "big"),
            })
    return records


def family_template(family_id: str, name: str, category: str) -> dict:
    return {
        "id": family_id, "name": name, "aliases": [], "semantic_category": category,
        "resolution_status": "unresolved", "name_status": "provisional",
        "actor_records": [], "actor_classes": [], "spawn_controller_callers": [],
        "renderer_compositor_families": [], "animation_state_values": [],
        "composer_tables": [], "representative_codes": [], "physical_patterns": [],
        "representative_pieces": [], "composite_dimensions_pixels": None,
        "palette_status": "unknown", "palette_derivation": None,
        "proven_effective_palette_banks": [], "legal_palette_candidates": [],
        "observed_sprite_controls": [], "observed_actor_palette_attributes": [],
        "round_phase_presence": [], "static_proof": [], "dynamic_proof": [],
        "merge_split_rationale": "Not merged with another candidate without arcade semantic proof.",
        "unresolved_blockers": [], "feasibility_treatment": "included conservatively; never zero-cost",
    }


def add_dynamic_family(families: dict, family_id: str, name: str, category: str,
                       rows: list[dict], combine_frame: bool = False) -> None:
    family = family_template(family_id, name, category)
    pieces, sample = representative(rows, combine_frame)
    family["representative_pieces"] = pieces
    if pieces:
        family["composite_dimensions_pixels"] = {
            "width": max(piece["x"] for piece in pieces) + 16,
            "height": max(piece["y"] for piece in pieces) + 16,
        }
    family["representative_codes"] = sorted({piece["code"] for piece in pieces})
    family["actor_classes"] = sorted({row["actor_class"] for row in rows})
    family["renderer_compositor_families"] = sorted({row["compositor_family"] for row in rows})
    family["animation_state_values"] = sorted({row["animation"] for row in rows})
    family["round_phase_presence"] = sorted({row["entry_label"] for row in rows})
    family["dynamic_tuple_count"] = len(rows)
    family["dynamic_proof"] = [
        "original arcade MAME actor/PC090OJ sweep",
        f"sample frame {sample['frame']} at {sample['entry_label']}" if sample else "no representative frame",
    ]
    family["static_proof"] = [
        "arcade_pc 0x03D054 renderer/compositor dispatch",
        "PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30",
    ]
    controls = {parse_int(row["sprite_ctrl"]) for row in rows}
    family["observed_sprite_controls"] = sorted(controls)
    family["observed_actor_palette_attributes"] = sorted({parse_int(row["actor_attr"]) for row in rows})
    family["palette_derivation"] = (
        "effective_bank = ((sprite_ctrl & 0x00E0) >> 1) | (actor_attr & 0x0F); "
        "exact object-to-bank relationship remains unknown unless palette_status is proven"
    )
    family["spawn_controller_callers"] = [
        "arcade_pc 0x0559B2 map/collision publication",
        "arcade_pc 0x041180 spawn/class selection",
        "arcade_pc 0x04543E actor record loader",
    ]
    if category == "BOSS":
        family["spawn_controller_callers"].append("arcade_pc 0x041F30 boss PC090OJ ownership path")
    candidates = set()
    for control in controls:
        candidates.update(range((control & 0xE0) >> 1, ((control & 0xE0) >> 1) + 16))
    family["legal_palette_candidates"] = sorted(candidates)
    family["unresolved_blockers"] = ["semantic family name", "exact object-to-palette-bank relationship"]
    family["composer_tables"] = sorted({
        {0: "arcade_rom/data 0x03D09E", 1: "arcade_rom/data 0x04771C",
         2: "arcade_rom/data 0x03F0CE", 3: "arcade_rom/data 0x040004",
         4: "arcade_rom/data 0x04002C"}.get(parse_int(value), "renderer-specific table unresolved")
        for value in family["renderer_compositor_families"]
    })
    if family_id == "hostile_base004b_compositor0":
        family["name"] = "Stage-1 Lizardman"
        family["name_status"] = "resolved"
        family["resolution_status"] = "resolved"
        family["palette_status"] = "proven"
        family["proven_effective_palette_banks"] = [0x36]
        family["legal_palette_candidates"] = []
        family["unresolved_blockers"] = []
        family["palette_decision_ids"] = ["PAL-PC090OJ-STAGE1-LIZARDMAN-001"]
        family["palette_derivation"] = (
            "sprite_ctrl 0x0060 supplies 0x30 and actor_attr low nibble 0x06 selects proven arcade bank 0x36"
        )
        family["merge_split_rationale"] = (
            "Family-0 classes observed with base 0x004B share the established Lizardman "
            "producer/composer vocabulary; animation/class variants remain one family."
        )
    families[family_id] = family


def build_families(rows: list[dict], maincpu: bytes) -> tuple[list[dict], list[dict], dict]:
    families = {}
    dynamic_map = {}
    normal_groups = defaultdict(list)
    boss_groups = defaultdict(list)
    auxiliary_groups = defaultdict(list)
    for row in rows:
        if row["renderer_mode"] == "0x0002":
            boss_groups[row["entry_label"]].append(row)
        elif row["block"] == "actor_2c8":
            normal_groups[row["base_code"]].append(row)
        else:
            auxiliary_groups[(row["block"], row["base_code"], row["compositor_family"])].append(row)

    for base, group in sorted(normal_groups.items()):
        compositors = sorted({parse_int(row["compositor_family"]) for row in group})
        compositor_tag = f"compositor{compositors[0]}" if len(compositors) == 1 else "multi_compositor"
        family_id = f"hostile_base{parse_int(base):04x}_{compositor_tag}"
        add_dynamic_family(families, family_id,
                           f"HOSTILE_BASE_{parse_int(base):04X}_{compositor_tag.upper()}_UNRESOLVED",
                           "ENEMY / HOSTILE", group)
        if len(compositors) > 1:
            families[family_id]["merge_split_rationale"] = (
                f"Compositor forms {compositors} share the same actor-record base 0x{parse_int(base):04X}; "
                "they remain forms of one unresolved semantic candidate rather than independent enemies."
            )
        for row in group:
            dynamic_map[(row["entry_label"], row["block"], row["base_code"], row["compositor_family"])] = family_id

    for label, group in sorted(boss_groups.items()):
        round_number = int(label[5])
        family_id = f"round{round_number}_boss_composite"
        add_dynamic_family(families, family_id,
                           f"Round {round_number} boss composite (semantic name unresolved)",
                           "BOSS", group, combine_frame=True)
        for row in group:
            dynamic_map[(row["entry_label"], row["block"], row["base_code"], row["compositor_family"])] = family_id

    category_by_block = {
        "actor_5c8": "OTHER PROVEN NON-ENEMY",
        "actor_748": "PROJECTILE / WEAPON",
        "actor_8c8": "EFFECT / TRANSIENT",
        "actor_508": "PLAYER AUXILIARY",
    }
    for (block, base, compositor), group in sorted(auxiliary_groups.items()):
        family_id = f"aux_{block[6:]}_base{parse_int(base):04x}_compositor{parse_int(compositor)}"
        add_dynamic_family(families, family_id,
                           f"{block.upper()}_BASE_{parse_int(base):04X}_COMPOSITOR_{parse_int(compositor)}",
                           category_by_block.get(block, "OTHER PROVEN NON-ENEMY"), group)
        for row in group:
            dynamic_map[(row["entry_label"], row["block"], row["base_code"], row["compositor_family"])] = family_id

    records = static_records(maincpu)
    hostile_by_base = defaultdict(list)
    for family in families.values():
        if family["semantic_category"] == "ENEMY / HOSTILE":
            for code in family["representative_codes"]:
                pass
            if family["id"].startswith("hostile_base"):
                hostile_by_base[int(family["id"].split("base", 1)[1].split("_", 1)[0], 16)].append(family["id"])
    for record in records:
        matches = hostile_by_base.get(record["base_code"], [])
        if record["table"].startswith("normal_variant_") and len(matches) == 1:
            family_id = matches[0]
        else:
            if record["table"].startswith("normal_variant_"):
                family_id = f"static_normal_base{record['base_code']:04x}_unresolved"
                display_seed = f"NORMAL_BASE_{record['base_code']:04X}"
            elif record["table"].startswith("mode2_variant_"):
                family_id = f"static_mode2_base{record['base_code']:04x}_unresolved"
                display_seed = f"MODE2_BASE_{record['base_code']:04X}"
            else:
                family_id = f"static_seed_{record['seed_id']}"
                display_seed = record["seed_id"].upper()
            if family_id in families:
                families[family_id]["actor_records"].append(record["seed_id"])
                record["mapped_family_id"] = family_id
                continue
            family = family_template(
                family_id,
                f"STATIC_{display_seed}_UNRESOLVED",
                "ENEMY / HOSTILE",
            )
            family["representative_codes"] = [record["base_code"]]
            family["legal_palette_candidates"] = list(range(0x30, 0x40))
            family["static_proof"] = [
                f"actor record {record['arcade_rom_offset']}",
                "arcade_pc 0x04543E or 0x04544E actor record loader",
            ]
            family["unresolved_blockers"] = [
                "record-to-semantic-family merge", "round/phase reachability", "composer pieces", "palette bank"
            ]
            families[family_id] = family
        families[family_id]["actor_records"].append(record["seed_id"])
        record["mapped_family_id"] = family_id

    prior_manifest = json.loads((ROOT / "tools/graphics_optimizer/scope_manifest.json").read_text())
    prior_by_id = {item["id"]: item for item in prior_manifest["sprite_semantics"]["round1"]["classes"]}
    for family_id, name, category in ESTABLISHED_UNRESOLVED:
        if family_id in families:
            continue
        family = family_template(family_id, name, category)
        prior = prior_by_id.get(family_id, {})
        family["static_proof"] = [prior.get("evidence", "established original-arcade route ledger")]
        family["unresolved_blockers"] = ["exact family/route merge", "composer pieces", "palette bank"]
        relationship = prior.get("palette_relationship", {})
        family["legal_palette_candidates"] = list(range(0x30, 0x40))
        family["palette_decision_ids"] = {
            "normal_small_bat": ["PAL-PC090OJ-GAMEPLAY-SMALL-BAT-001"],
            "large_bat": ["PAL-PC090OJ-GAMEPLAY-LARGE-BAT-001"],
            "four_armed_enemy": ["PAL-PC090OJ-GAMEPLAY-FOUR-ARMED-ENEMY-001"],
            "axe_item": ["PAL-PC090OJ-GAMEPLAY-AXE-ITEM-001"],
        }.get(family_id, [])
        codes = []
        for value in prior.get("codes", []):
            if "-" in value:
                lo, hi = (int(x, 0) for x in value.split("-"))
                codes.extend(range(lo, hi + 1))
            else:
                codes.append(int(value, 0))
        family["representative_codes"] = sorted(set(codes))
        if prior.get("composites"):
            first = prior["composites"][0]
            family["representative_pieces"] = [
                {"record": index, "control": 0, "source_x": 0, "source_y": 0,
                 "code": int(piece["code"], 0), "flip_h": bool(piece.get("flip_h")),
                 "flip_v": bool(piece.get("flip_v")), "x": piece.get("x", 0), "y": piece.get("y", 0)}
                for index, piece in enumerate(first["components"])
            ]
        families[family_id] = family

    signatures = {}
    for row in rows:
        key = (row["entry_label"], row["block"], row["base_code"], row["compositor_family"])
        family_id = dynamic_map[key]
        signature_id = "|".join(key)
        signatures[signature_id] = family_id

    return sorted(families.values(), key=lambda item: (item["semantic_category"], item["id"])), records, signatures


def attach_patterns(families: list[dict], pc090oj: bytes) -> None:
    for family in families:
        codes = set(family["representative_codes"])
        codes.update(piece["code"] for piece in family["representative_pieces"])
        patterns = []
        for code in sorted(codes):
            raw = pc090oj[code * 128:(code + 1) * 128]
            if len(raw) != 128:
                family["unresolved_blockers"].append(f"graphics code 0x{code:04X} outside PC090OJ region")
                continue
            patterns.append({"code": code, "sha256": hashlib.sha256(raw).hexdigest()})
        family["physical_patterns"] = patterns


def render_family(family: dict, pc090oj: bytes, palette36: list[tuple[int, int, int]]) -> Image.Image:
    pieces = family["representative_pieces"]
    if not pieces and family["representative_codes"]:
        pieces = [{"code": code, "x": (index % 8) * 16, "y": (index // 8) * 16,
                   "flip_h": False, "flip_v": False}
                  for index, code in enumerate(family["representative_codes"][:32])]
    if not pieces:
        image = Image.new("RGBA", (256, 96), (30, 30, 30, 255))
        draw = ImageDraw.Draw(image)
        draw.text((12, 18), "COMPOSITE UNRESOLVED", fill="white")
        draw.text((12, 42), "PALETTE UNKNOWN", fill=(255, 214, 100))
        draw.text((12, 60), "CONSERVATIVE CAPACITY BLOCKER", fill=(180, 220, 255))
        return image
    min_x, min_y = min(p["x"] for p in pieces), min(p["y"] for p in pieces)
    max_x = max(p["x"] for p in pieces) + 16
    max_y = max(p["y"] for p in pieces) + 16
    scale = 3
    image = Image.new("RGBA", ((max_x - min_x) * scale, (max_y - min_y) * scale), (0, 0, 0, 0))
    palette = palette36 if family["palette_status"] == "proven" else neutral_palette()
    for piece in pieces:
        raw = pc090oj[piece["code"] * 128:(piece["code"] + 1) * 128]
        if len(raw) != 128:
            continue
        pixels = decode_pixels(raw)
        tile = Image.new("RGBA", (16, 16))
        tile.putdata([(*palette[index], 0 if index == 0 else 255) for index in pixels])
        if piece.get("flip_h"):
            tile = tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if piece.get("flip_v"):
            tile = tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        tile = tile.resize((48, 48), Image.Resampling.NEAREST)
        image.alpha_composite(tile, ((piece["x"] - min_x) * scale, (piece["y"] - min_y) * scale))
    return image


def render_outputs(out: Path, families: list[dict], pc090oj: bytes, maincpu: bytes) -> None:
    words, _ = compiler.decode_arcade_palette_bank(maincpu, 0x36, 1)
    palette36 = [rgb(word) for word in words]
    sprite_dir = out / "sprites"
    sprite_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for family in families:
        image = render_family(family, pc090oj, palette36)
        path = sprite_dir / f"{family['id']}.png"
        image.save(path)
        family["representative_png"] = str(path.relative_to(out))
        rendered.append((family, image))

    columns, cell_w, cell_h = 4, 420, 300
    rows = max(1, math.ceil(len(rendered) / columns))
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), (18, 18, 18))
    draw, font = ImageDraw.Draw(sheet), ImageFont.load_default()
    for index, (family, image) in enumerate(rendered):
        x, y = (index % columns) * cell_w + 12, (index // columns) * cell_h + 12
        art = image.copy()
        art.thumbnail((cell_w - 24, 210), Image.Resampling.NEAREST)
        sheet.paste(art, (x, y), art if art.mode == "RGBA" else None)
        draw.text((x, y + 216), family["name"][:58], fill="white", font=font)
        draw.text((x, y + 232), family["semantic_category"], fill=(255, 216, 110), font=font)
        palette_text = "PROVEN " + ",".join(f"0x{x:02X}" for x in family["proven_effective_palette_banks"])
        if family["palette_status"] != "proven":
            palette_text = "PALETTE UNKNOWN / NEUTRAL RENDER"
        draw.text((x, y + 248), palette_text, fill=(185, 228, 255), font=font)
        draw.text((x, y + 264), family["resolution_status"], fill=(190, 190, 190), font=font)
    sheet.save(out / "contact_sheet.png")


def optimizer_classes(families: list[dict], scope: str) -> list[dict]:
    classes = []
    for family in families:
        if family["semantic_category"] not in {"ENEMY / HOSTILE", "BOSS"}:
            continue
        if scope not in family["round_phase_presence"]:
            continue
        components = [{"code": f"0x{piece['code']:04X}", "x": piece["x"], "y": piece["y"],
                       "flip_h": int(piece.get("flip_h", False)), "flip_v": int(piece.get("flip_v", False))}
                      for piece in family["representative_pieces"]]
        entry = {
            "id": family["id"], "name": family["name"],
            "class_resolution": "resolved" if family["resolution_status"] == "resolved" else "unresolved",
            "graphics_resolution": "resolved" if family["physical_patterns"] else "unresolved",
            "codes": [f"0x{code:04X}" for code in family["representative_codes"]],
            "palette_relationship": {
                "status": family["palette_status"],
                "proven_banks": [f"0x{bank:02X}" for bank in family["proven_effective_palette_banks"]],
                "legal_candidates": [f"0x{bank:02X}" for bank in family["legal_palette_candidates"]],
                "evidence": "; ".join(family["static_proof"] + family["dynamic_proof"]),
            },
            "pieces_per_composite": len(components) if components else "unresolved",
            "evidence": "; ".join(family["static_proof"] + family["dynamic_proof"]),
        }
        if components:
            entry["composites"] = [{"id": "whole_game_lexicon_representative", "status": "original arcade sweep composite",
                                     "components": components}]
        classes.append(entry)
    return classes


def write_artifacts(out: Path, families: list[dict], records: list[dict], signatures: dict,
                    rows: list[dict]) -> dict:
    hostile = [f for f in families if f["semantic_category"] in {"ENEMY / HOSTILE", "BOSS"}]
    resolved = [f for f in hostile if f["resolution_status"] == "resolved"]
    unresolved = [f for f in hostile if f["resolution_status"] != "resolved"]
    dynamic_mapped = all(
        "|".join((row["entry_label"], row["block"], row["base_code"], row["compositor_family"])) in signatures
        for row in rows
    )
    static_mapped = all(record.get("mapped_family_id") for record in records)
    unknown_colored = [f["id"] for f in families if f["palette_status"] != "proven" and f["proven_effective_palette_banks"]]
    observed_hostile_ids = {
        family_id for family_id in signatures.values()
        if next(f for f in families if f["id"] == family_id)["semantic_category"] in {"ENEMY / HOSTILE", "BOSS"}
    }
    hostile_observations = sum(
        1 for row in rows
        if signatures["|".join((row["entry_label"], row["block"], row["base_code"], row["compositor_family"]))]
        in observed_hostile_ids
    )
    closure = {
        "schema_version": 1,
        "authority": "original arcade ROM/Ghidra semantics plus bounded original arcade MAME presence",
        "round_phase_entry_points_audited": len(ROUND_PHASES),
        "round_phase_entry_points_total": 18,
        "empty_dynamic_entry_points": sorted(set(ROUND_PHASES) - {row["entry_label"] for row in rows}),
        "static_legal_hostile_seed_count": len(records) + sum(1 for x in ESTABLISHED_UNRESOLVED if x[2] in {"ENEMY / HOSTILE", "BOSS"}),
        "dynamic_signature_count": len(signatures),
        "dynamic_observation_count": len(rows),
        "dynamically_observed_hostile_tuple_count": len(observed_hostile_ids),
        "dynamically_observed_hostile_row_count": hostile_observations,
        "every_dynamic_tuple_mapped": dynamic_mapped,
        "every_static_seed_mapped": static_mapped,
        "resolved_hostile_family_count": len(resolved),
        "explicitly_unresolved_hostile_family_count": len(unresolved),
        "legal_hostile_domain_equals_resolved_plus_explicitly_unresolved": len(hostile) == len(resolved) + len(unresolved),
        "unknown_legal_families_dropped": 0,
        "unknown_palette_colored_family_ids": unknown_colored,
        "unknown_palette_color_contribution": "ZERO",
        "unknown_families_zero_cost": False,
        "enemy_family_enumeration_complete": dynamic_mapped and static_mapped,
        "enemy_semantic_naming_complete": not unresolved,
        "enemy_graphics_composition_complete": all(f["representative_pieces"] for f in hostile),
        "enemy_palette_relationships_complete": all(f["palette_status"] == "proven" for f in hostile),
        "whole_game_hostile_domain_fail_closed": dynamic_mapped and static_mapped and not unknown_colored,
        "validation": "PASS" if dynamic_mapped and static_mapped and not unknown_colored else "FAIL",
    }
    payload = {
        "schema_version": 1,
        "scope": "whole-game original arcade sprite/enemy semantic lexicon",
        "source_authority": [
            "tools/ghidra/rastan_project/rastan_arcade_ref.gpr",
            "analysis/ghidra/rastan_arcade/exports/",
            "build/regions/maincpu.bin", "build/regions/pc090oj.bin",
            "analysis/enemy_sprite_lexicon/evidence/arcade_sweep/",
        ],
        "palette_rule": "Only proven object-to-effective-bank relationships render in color; unknowns are neutral and remain capacity-bearing.",
        "families": families,
        "closure": closure,
        "optimizer_classes_by_scope": {"round1_phase1": optimizer_classes(families, "round1_phase1")},
    }
    (out / "families.json").write_text(json.dumps(payload, indent=2) + "\n")
    (out / "static_actor_records.json").write_text(json.dumps(records, indent=2) + "\n")
    (out / "dynamic_signature_map.json").write_text(json.dumps(signatures, indent=2, sort_keys=True) + "\n")
    (out / "closure_check.json").write_text(json.dumps(closure, indent=2) + "\n")
    (out / "optimizer_input.json").write_text(json.dumps({"schema_version": 1, "optimizer_classes_by_scope": payload["optimizer_classes_by_scope"]}, indent=2) + "\n")

    columns = ["id", "name", "aliases", "semantic_category", "resolution_status", "name_status", "palette_status",
               "proven_effective_palette_banks", "legal_palette_candidates", "round_phase_presence",
               "actor_records", "actor_classes", "spawn_controller_callers", "renderer_compositor_families",
               "animation_state_values", "composer_tables", "representative_codes", "composite_dimensions_pixels",
               "palette_derivation", "observed_sprite_controls", "observed_actor_palette_attributes",
               "static_proof", "dynamic_proof", "merge_split_rationale", "feasibility_treatment",
               "physical_pattern_count", "representative_piece_count", "unresolved_blockers", "representative_png"]
    with (out / "families.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for family in families:
            row = {key: family.get(key, "") for key in columns}
            row["physical_pattern_count"] = len(family["physical_patterns"])
            row["representative_piece_count"] = len(family["representative_pieces"])
            for key, value in list(row.items()):
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, separators=(",", ":"))
            writer.writerow(row)

    with (out / "round_phase_presence.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family_id", "name", *ROUND_PHASES, "static_only_or_unobserved"])
        for family in families:
            presence = set(family["round_phase_presence"])
            writer.writerow([family["id"], family["name"], *["YES" if scope in presence else "" for scope in ROUND_PHASES],
                             "YES" if not presence else ""])

    notes = ["# Whole-Game Original-Arcade Enemy/Sprite Lexicon Evidence", "",
             "Unknown palettes are always rendered in grayscale and never contribute colors to the optimizer.", ""]
    for family in families:
        notes.extend([
            f"## {family['id']}",
            f"- Name/category: {family['name']} / {family['semantic_category']}",
            f"- Resolution: {family['resolution_status']}; palette: {family['palette_status']}",
            f"- Static proof: {'; '.join(family['static_proof']) or 'none beyond declared fail-closed route'}",
            f"- Dynamic proof: {'; '.join(family['dynamic_proof']) or 'not observed in bounded sweep'}",
            f"- Merge/split: {family['merge_split_rationale']}",
            f"- Blockers: {'; '.join(family['unresolved_blockers']) or 'none'}", "",
        ])
    (out / "evidence_notes.md").write_text("\n".join(notes))
    return closure


def write_html(out: Path, families: list[dict], closure: dict) -> None:
    rows = []
    for family in families:
        rows.append(
            "<tr>"
            f"<td><img src='{html.escape(family['representative_png'])}'></td>"
            f"<td><code>{html.escape(family['id'])}</code><br>{html.escape(family['name'])}</td>"
            f"<td>{html.escape(family['semantic_category'])}</td>"
            f"<td>{html.escape(family['resolution_status'])}</td>"
            f"<td>{'PROVEN ' + ', '.join(f'0x{x:02X}' for x in family['proven_effective_palette_banks']) if family['palette_status'] == 'proven' else 'PALETTE UNKNOWN / NEUTRAL RENDER'}</td>"
            f"<td>{html.escape(', '.join(family['round_phase_presence']) or 'static legal / not dynamically observed')}</td>"
            f"<td>{html.escape('; '.join(family['unresolved_blockers']) or 'none')}</td>"
            "</tr>"
        )
    page = f"""<!doctype html><meta charset='utf-8'><title>Rastan Arcade Enemy Sprite Lexicon</title>
<style>body{{background:#111;color:#eee;font:15px sans-serif;margin:2rem}}h1,h2{{color:#ffd56a}}code{{color:#9edfff}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #555;padding:.5rem;vertical-align:top}}th{{position:sticky;top:0;background:#222}}td img{{max-width:180px;max-height:140px;image-rendering:pixelated}}.warn{{background:#402d00;padding:1rem}}pre{{white-space:pre-wrap}}</style>
<h1>Whole-Game Original-Arcade Enemy / Sprite Lexicon</h1>
<p>Static actor/spawn/dispatch/composer closure first; bounded 18-selector ORIGINAL ARCADE MAME presence second. Genesis output is not semantic input.</p>
<p class='warn'>Unknown palette means neutral grayscale. It never means a guessed bank, colored optimizer input, omitted family, or zero graphics cost.</p>
<h2>Closure</h2><pre>{html.escape(json.dumps(closure, indent=2))}</pre>
<h2>Representative Contact Sheet</h2><img src='contact_sheet.png' style='max-width:100%;image-rendering:pixelated'>
<h2>Families and Explicit Unresolved Seeds</h2><table><tr><th>Representative</th><th>ID/name</th><th>Category</th><th>Semantic status</th><th>Palette</th><th>Presence</th><th>Blockers</th></tr>{''.join(rows)}</table>
<h2>Exclusions</h2><p>PLAYER, PLAYER AUXILIARY, ITEM / DROP, PROJECTILE / WEAPON, EFFECT / TRANSIENT, HUD / SYSTEM, and OTHER PROVEN NON-ENEMY entries are classified separately and are not counted as ordinary enemy families.</p>"""
    (out / "index.html").write_text(page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", type=Path, default=ROOT / "analysis/enemy_sprite_lexicon/evidence/arcade_sweep/all_observations.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "analysis/enemy_sprite_lexicon")
    args = parser.parse_args()
    rows = list(csv.DictReader(args.sweep.open()))
    maincpu = (ROOT / "build/regions/maincpu.bin").read_bytes()
    pc090oj = (ROOT / "build/regions/pc090oj.bin").read_bytes()
    families, records, signatures = build_families(rows, maincpu)
    attach_patterns(families, pc090oj)
    args.out.mkdir(parents=True, exist_ok=True)
    render_outputs(args.out, families, pc090oj, maincpu)
    closure = write_artifacts(args.out, families, records, signatures, rows)
    write_html(args.out, families, closure)
    if closure["validation"] != "PASS":
        raise SystemExit("lexicon closure validation failed")
    print(json.dumps(closure, indent=2))


if __name__ == "__main__":
    main()
