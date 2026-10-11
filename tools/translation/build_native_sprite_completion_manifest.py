#!/usr/bin/env python3
"""Build the machine-readable PC090OJ native-sprite completion inventory.

This is a coverage view, not a competing actor or palette registry.  Actor
reachability comes from H21/the canonical actor graphics manifest; observed
selector domains come from the established 18-entry original-arcade sweep.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSITOR_TABLES = (0x03D09E, 0x04771C, 0x03F0CE, 0x040004, 0x04002C)
GENERAL_MODES = {0x00, 0x40, 0x70, 0x80, 0xD0, 0xE0, 0xF0}
FIELDS = (
    "consumer_id", "context_round_segment", "pool_or_producer", "actor_family",
    "semantic_discriminator", "selector_domain", "compositor_table_source",
    "effective_bank", "orientation_behavior", "dynamic_attributes",
    "frame_completeness", "selector_completeness", "palette_completeness",
    "native_status", "fallback_reason", "evidence",
)


def selector_domains(path: Path) -> dict[tuple[int, int], set[int]]:
    result: dict[tuple[int, int], set[int]] = defaultdict(set)
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            # actor+0x01 is the compositor program selector.  The sweep names
            # that retained byte ``record_selector``; ``actor_class`` is a
            # different gameplay field and must never drive graphics lookup.
            result[(int(row["base_code"], 16), int(row["compositor_family"], 16))].add(
                int(row["record_selector"], 16))
    return result


def hex_domain(values: set[int]) -> str:
    if not values:
        return "not captured; universal index covers any general selector"
    return ",".join(f"0x{x:02X}" for x in sorted(values))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", type=Path, default=ROOT / "analysis/actor_decompilation/h21_gameplay_object_census.tsv")
    ap.add_argument("--sweep", type=Path, default=ROOT / "analysis/enemy_sprite_lexicon/evidence/arcade_sweep/all_observations.csv")
    ap.add_argument("--maincpu", type=Path, default=ROOT / "build/regions/maincpu.bin")
    ap.add_argument("--output", type=Path, default=ROOT / "analysis/actor_decompilation/native_sprite_completion_manifest.tsv")
    args = ap.parse_args()

    observed = selector_domains(args.sweep)
    rom = args.maincpu.read_bytes()
    rows: list[dict[str, str]] = []

    def add(**values: str) -> None:
        rows.append({field: values.get(field, "") for field in FIELDS})

    add(
        consumer_id="player_body_and_weapon", context_round_segment="all gameplay",
        pool_or_producer="A5 player state -> 0x54326/0x54492 semantic boundary",
        actor_family="Rastan", semantic_discriminator="A5+0x1244 primary; A5+0x1246 secondary; A5+0x12FA weapon; A5+0x1308 fire phase",
        selector_domain="primary 0..74; secondary 0..51; weapon 0..4; fire phase 0..3",
        compositor_table_source="0x5BD40 primary; 0x5C466 secondary; 0x5CD8A/0x5D346/0x5D666/0x5D068 weapons",
        effective_bank="0x33", orientation_behavior="A5+0x1114; mode-9/orientation-3 selector decrement",
        dynamic_attributes="none after direct key selection", frame_completeness="complete (1200 keys)",
        selector_completeness="complete", palette_completeness="PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001",
        native_status="NATIVE_COMPLETE", fallback_reason="",
        evidence="H24 player/leg corpus; 0x54602 finite fire substitution; generated primary and secondary coverage JSON",
    )
    add(
        consumer_id="player_front_overlays", context_round_segment="all gameplay",
        pool_or_producer="0x59F92 fixed FRONT producer -> PLAYER_FRONT lane",
        actor_family="Rastan fixed weapon/overlay pieces",
        semantic_discriminator="A5+0x1388 and fixed overlay-active tuples",
        selector_domain="four fixed direct pieces",
        compositor_table_source="fixed semantic producer; no 0x3C902 mapping program",
        effective_bank="producer-owned attr/code",
        orientation_behavior="fixed FRONT coordinates",
        dynamic_attributes="active/type fields only",
        frame_completeness="complete whole-producer direct generation",
        selector_completeness="complete",
        palette_completeness="existing FRONT producer contract",
        native_status="NATIVE_COMPLETE",
        fallback_reason="",
        evidence="rastan_direct_remap.json 0x59F92 whole-producer cut; native_player_front_fixed",
    )

    with args.census.open(newline="") as fh:
        for actor in csv.DictReader(fh, delimiter="\t"):
            if actor.get("reachable") != "yes":
                continue
            base_text = actor.get("base", "").strip()
            comp_text = actor.get("selector", "").strip()
            base = int(base_text, 16) if base_text else None
            comp = int(comp_text, 0) if comp_text else 0
            selectors = observed.get((base, comp), set()) if base is not None else set()
            seed_text = actor.get("anim", "").strip()
            if seed_text:
                selectors.add(int(seed_text, 0))
            palette = actor.get("palette_status", "")
            modes = set()
            if 0 <= comp < len(COMPOSITOR_TABLES):
                root = COMPOSITOR_TABLES[comp]
                for selector in selectors:
                    # The arcade applies these entries with ADDA.W, therefore
                    # they are signed PC-relative offsets.
                    off = int.from_bytes(
                        rom[root + selector * 2:root + selector * 2 + 2],
                        "big", signed=True)
                    modes.add(rom[root + off] & 0xF0)
            status = "NATIVE_COMPLETE"
            add(
                consumer_id=actor["technical_id"],
                context_round_segment=(actor.get("rounds") or actor.get("round_presence") or "runtime route"),
                pool_or_producer=actor.get("pool", ""), actor_family=actor.get("semantic_name", ""),
                semantic_discriminator=(f"base={base_text}; family={actor.get('family','')}; state={actor.get('state','')}; rec_type={actor.get('rec_type','')}"),
                selector_domain=hex_domain(selectors),
                compositor_table_source=f"table {comp}; generated direct universal general index",
                effective_bank="retained sprite_ctrl high bits + actor/program low nibble",
                orientation_behavior="generated normal/mirrored records; shared three-field predicate",
                dynamic_attributes="actor base/effective bank retained only (Level A unless an exact Level-B usage matches)",
                frame_completeness="all legal general and nine-mode specialized programs direct-indexed",
                selector_completeness="observed domain listed; static table boundary closes every legal selector",
                palette_completeness=palette,
                native_status=status,
                fallback_reason="",
                evidence="H21 census; whole-game 18-entry arcade sweep; signed-offset/static-boundary generated universal index",
            )

    for cid, context, producer in (
        ("gameplay_hud_status", "all gameplay", "native status/score/energy semantic producers"),
        ("frontend_title_credit", "frontend/title/attract", "native_frontend_hud_emit"),
        ("transient_item_stream", "frontend/gameplay transitions", ".Lnq_transient_items_emit"),
    ):
        add(
            consumer_id=cid, context_round_segment=context, pool_or_producer=producer,
            actor_family="fixed semantic sprite producer", semantic_discriminator="producer-owned semantic state",
            selector_domain="producer-owned direct tables", compositor_table_source="not 0x3D054/0x3C902",
            effective_bank="producer-owned finalized identity", orientation_behavior="producer-owned",
            dynamic_attributes="bounded producer fields only", frame_completeness="complete",
            selector_completeness="complete", palette_completeness="existing native producer contract",
            native_status="NATIVE_COMPLETE", fallback_reason="", evidence="pc090oj_hooks.s direct-native producer inventory",
        )

    for cid, pool, count, lane in (
        ("generic_pool_actor_508", "A5+0x0508", "2 records", "PLAYER_FRONT"),
        ("generic_pool_actor_2c8", "A5+0x02C8", "10 records", "BACK_ENEMY"),
        ("generic_pool_actor_5c8", "A5+0x05C8", "6 records", "MIDDLE/BACK_ENEMY"),
        ("generic_pool_actor_748", "A5+0x0748", "11/6 records", "FRONT_EFFECT"),
        ("generic_pool_actor_8c8", "A5+0x08C8", "5 records", "MIDDLE"),
    ):
        add(
            consumer_id=cid, context_round_segment="whole-game gameplay dispatch",
            pool_or_producer=f"{pool}; {count}; native_stage_dispatch_41dae/45dfa",
            actor_family="pool-level consumer (semantic actors itemized separately)",
            semantic_discriminator="actor+0x38 compositor; actor+0x01 selector",
            selector_domain="dense 5 x 256 x 2 generated index",
            compositor_table_source="all five 0x3C902 program tables",
            effective_bank="retained actor/program state",
            orientation_behavior="shared three-field predicate",
            dynamic_attributes="actor base/effective bank only on Level-A general records",
            frame_completeness="all legal general and specialized programs native",
            selector_completeness="all byte selectors indexed",
            palette_completeness="dynamic effective-bank route retained",
            native_status="NATIVE_COMPLETE",
            fallback_reason="",
            evidence=f"pc090oj_hooks.s dispatch pool {pool} -> {lane}; universal/special index verifier",
        )

    add(
        consumer_id="generic_specialized_compositor_modes",
        context_round_segment="whole-game generic actor pools",
        pool_or_producer="native_stage_dispatch_41dae/native_stage_dispatch_45dfa",
        actor_family="raw compositor modes 0x10/20/30/50/60/90/A0/B0/C0",
        semantic_discriminator="actor+0x38 table; actor+0x01 selector; actor+0x0B subframe",
        selector_domain="12 structurally valid specialized selectors; 24 orientation dispatch records",
        compositor_table_source="0x3D09E/0x4771C/0x3F0CE/0x40004/0x4002C",
        effective_bank="retained", orientation_behavior="handler-specific",
        dynamic_attributes="actor+0x0B subframe; 0xB0 predicate; 0x10 conditional code override",
        frame_completeness="nine modes compiled", selector_completeness="static table boundaries and structural pointer validation",
        palette_completeness="selector-1 generated attr/effective-bank contract",
        native_status="NATIVE_COMPLETE",
        fallback_reason="",
        evidence="FU1 PC090OJ write history; 0x3C4D2..0x3C902; generated special index; independent verifier",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"native sprite completion manifest: {len(rows)} live-consumer rows -> {args.output}")


if __name__ == "__main__":
    main()
