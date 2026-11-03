#!/usr/bin/env python3
"""Build the fail-closed R1/P1 sprite-palette authority and SAT-word oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "analysis/graphics_optimizer/r1p1_palette_authority_oracle"
UNRESOLVED = "UNRESOLVED"

DECISION_BY_CLASS = {
    "rastan_player_body": "PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001",
    "player_auxiliary": "PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001",
    "stage1_lizardman": "PAL-PC090OJ-STAGE1-LIZARDMAN-001",
    "hostile_base004b_compositor0": "PAL-PC090OJ-STAGE1-LIZARDMAN-001",
}

STATIC_ONLY_CLASSES = {
    "collision_marker40_route",
    "collision_marker41_route",
    "collision_marker49_special_route",
    "collision_marker4f_behavior20_route",
    "record08_family2_class30",
    "record09_family1_class57",
    "record0a_family1_classb6",
    "record0b_family1_classb9",
    "record0c_family1_classbc",
}


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def parse_live_routes(path: Path) -> dict[int, int]:
    routes: dict[int, int] = {}
    row = re.compile(
        r"^\s*\.word\s+1,\s*PROUTE_OWNER_PC090OJ,\s*(0x[0-9A-Fa-f]+|\d+),\s*(\d+),"
    )
    for line in path.read_text().splitlines():
        match = row.match(line)
        if match:
            routes[int(match.group(1), 0)] = int(match.group(2), 0)
    return routes


def effective_bank(family: dict) -> tuple[int | None, int | None, int | None]:
    banks = family["palette_relationship"].get("proven_banks", [])
    if len(banks) != 1:
        return None, None, None
    bank = int(banks[0], 0)
    return bank & 0xF, (bank & 0x70) << 1, bank


def registry_index(registry: dict) -> dict[str, dict]:
    return {entry["id"]: entry for entry in registry["decisions"]}


def classify_reconciliation(entry: dict, live_line: int | None) -> tuple[str, str]:
    registry_line = entry["genesis_realization"].get("palette_line")
    if registry_line is None:
        if live_line is None:
            return "UNRESOLVED", "No accepted Genesis line and no live route."
        return "TEST-ONLY", "Live frozen-Test route is not an accepted registry realization."
    if live_line == registry_line:
        return "ACCEPTED / CANONICAL", "Accepted registry and live route agree."
    return "CONTRADICTED", "Accepted registry and current frozen-Test live route disagree."


def make_reconciliation(registry: dict, live_routes: dict[int, int]) -> dict:
    rows = []
    for entry in registry["decisions"]:
        arcade = entry["arcade_semantics"]
        effective = arcade.get("effective_palette_bank")
        bank = int(effective, 0) if effective else None
        live_line = live_routes.get(bank) if bank is not None else None
        status, reason = classify_reconciliation(entry, live_line)
        rows.append(
            {
                "decision_id": entry["id"],
                "semantic_class": entry["context"]["subsystem"],
                "arcade_sprite_family": entry["context"].get("actor_family"),
                "source_nibble": arcade.get("source_attribute_nibble"),
                "control_state": arcade.get("sprite_control"),
                "effective_bank": effective,
                "registry_status": entry["status"],
                "registry_line": entry["genesis_realization"].get("palette_line"),
                "live_route_line": live_line,
                "runtime_observed_line": live_line,
                "runtime_observation_basis": "static natural-gameplay path through .Lnative_palsel and .Lnative_pal_fixup; not a new runtime capture",
                "decision_status": status,
                "confidence": "HIGH" if entry["status"] in {"proven", "decided"} else "PROVISIONAL" if entry["status"] == "provisional" else "UNKNOWN",
                "reason": reason,
                "provenance": entry.get("evidence", []),
            }
        )
    return {
        "schema_version": 1,
        "scope": "Round 1 Phase 1",
        "authority_rule": "Accepted registry decisions control only where evidence and acceptance support them; live frozen-Test routes are observations, not automatic authority.",
        "rows": rows,
        "counts": {
            status: sum(row["decision_status"] == status for row in rows)
            for status in [
                "ACCEPTED / CANONICAL",
                "PROVISIONAL",
                "TEST-ONLY",
                "CONTRADICTED",
                "UNRESOLVED",
                "NOT REACHABLE IN R1/P1",
            ]
        },
    }


def make_domain(families: list[dict], decisions: dict[str, dict], live_routes: dict[int, int]) -> dict:
    rows = []
    for semantic_id, family in enumerate(families):
        nibble, control, bank = effective_bank(family)
        decision_id = DECISION_BY_CLASS.get(family["id"])
        decision = decisions.get(decision_id) if decision_id else None
        line = decision["genesis_realization"].get("palette_line") if decision else None
        resolved = bool(decision and line is not None and family.get("codes"))
        rows.append(
            {
                "generated_semantic_id": semantic_id,
                "semantic_class": family["id"],
                "graphics_family": family["name"],
                "arcade_codes": [f"0x{code:04X}" for code in family.get("codes", [])],
                "source_attribute_nibble": f"0x{nibble:X}" if nibble is not None else UNRESOLVED,
                "pc090oj_sprite_ctrl_shadow": f"0x{control:04X}" if control is not None else UNRESOLVED,
                "effective_bank": f"0x{bank:02X}" if bank is not None else UNRESOLVED,
                "force_tag": "semantic HUD force-to-line-3" if family["id"] == "gameplay_hud" else "none proven",
                "pixel_reindex_profile": UNRESOLVED,
                "expected_genesis_palette_line": line if resolved else UNRESOLVED,
                "decision_id": decision_id or UNRESOLVED,
                "authority_status": "ACCEPTED / CANONICAL" if resolved else "UNRESOLVED",
                "class_resolution": family["class_resolution"],
                "graphics_resolution": family["graphics_resolution"],
                "arcade_palette_resolution": family["palette_relationship"]["status"],
                "live_route_line": live_routes.get(bank) if bank is not None else None,
                "runtime_observation_status": "not observed in inspected traces; retained from static semantics" if family["id"] in STATIC_ONLY_CLASSES else "observed or observation status not independently closed",
                "fail_closed": not resolved,
                "evidence": family.get("evidence"),
            }
        )
    resolved = [row for row in rows if not row["fail_closed"]]
    unresolved = [row for row in rows if row["fail_closed"]]
    return {
        "schema_version": 1,
        "scope": "Round 1 Phase 1",
        "legal_domain_source": "analysis/graphics_optimizer/round1_phase1_whole_game_lexicon/sprite_class_coverage.json",
        "fail_closed_sentinel": UNRESOLVED,
        "rows": rows,
        "counts": {
            "legal_semantic_cases": len(rows),
            "resolved": len(resolved),
            "unresolved": len(unresolved),
            "statically_legal_not_observed_in_inspected_traces": sum(
                row["semantic_class"] in STATIC_ONLY_CLASSES for row in rows
            ),
        },
    }


def reference_emit_then_fixup(
    pattern: int, line: int, hflip: bool, vflip: bool, priority: bool
) -> int:
    emitted = (
        (int(priority) << 15)
        | (int(vflip) << 12)
        | (int(hflip) << 11)
        | (pattern & 0x07FF)
    )
    return (emitted & 0x9FFF) | ((line & 3) << 13)


def generated_static_then_dynamic(
    pattern: int, static_attribute: int, hflip: bool, vflip: bool
) -> int:
    dynamic = (int(vflip) << 12) | (int(hflip) << 11) | (pattern & 0x07FF)
    return static_attribute | dynamic


def make_parity(domain: dict) -> dict:
    patterns = [0x000, 0x001, 0x3FF, 0x7FF]
    details = []
    tested = 0
    resolved = 0
    mismatches = []
    for row in domain["rows"]:
        if row["fail_closed"]:
            details.append(
                {
                    "semantic_class": row["semantic_class"],
                    "status": UNRESOLVED,
                    "reason": "No accepted complete palette decision and code domain.",
                }
            )
            continue
        line = row["expected_genesis_palette_line"]
        priority = True
        static_attribute = (int(priority) << 15) | ((line & 3) << 13)
        class_tested = 0
        for code in row["arcade_codes"]:
            for pattern in patterns:
                for hflip in (False, True):
                    for vflip in (False, True):
                        tested += 1
                        resolved += 1
                        class_tested += 1
                        reference = reference_emit_then_fixup(
                            pattern, line, hflip, vflip, priority
                        )
                        generated = generated_static_then_dynamic(
                            pattern, static_attribute, hflip, vflip
                        )
                        if reference != generated:
                            mismatches.append(
                                {
                                    "semantic_class": row["semantic_class"],
                                    "arcade_code": code,
                                    "pattern": pattern,
                                    "hflip": hflip,
                                    "vflip": vflip,
                                    "reference": reference,
                                    "generated": generated,
                                }
                            )
        details.append(
            {
                "semantic_class": row["semantic_class"],
                "status": "RESOLVED",
                "tested_combinations": class_tested,
                "palette_line": line,
                "priority": 1,
                "generated_static_attribute": f"0x{static_attribute:04X}",
                "dynamic_pattern_samples": patterns,
            }
        )
    unresolved = sum(row["fail_closed"] for row in domain["rows"])
    return {
        "schema_version": 1,
        "scope": "Round 1 Phase 1",
        "reference": "independent model of native emitted word 2 followed by accepted semantic palette-bit clear/patch; priority fixed to 1",
        "proposed": "independent context-selected generated static attribute OR genuinely dynamic pattern/H/V bits",
        "tested_combinations": tested,
        "resolved_combinations": resolved,
        "unresolved_semantic_cases": unresolved,
        "mismatches": len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "mismatch_details": mismatches,
        "result": "INCOMPLETE" if unresolved else "PASS" if not mismatches else "FAIL",
        "resolved_subset_result": "PASS" if not mismatches else "FAIL",
        "details": details,
    }


def make_lookup_key_analysis(domain: dict) -> dict:
    code_owners: dict[str, list[str]] = {}
    for row in domain["rows"]:
        for code in row["arcade_codes"]:
            code_owners.setdefault(code, []).append(row["semantic_class"])
    collisions = [
        {"arcade_code": code, "semantic_classes": owners}
        for code, owners in sorted(code_owners.items())
        if len(owners) > 1
    ]
    return {
        "schema_version": 1,
        "scope": "Round 1 Phase 1",
        "candidate_keys": {
            "arcade_code": {
                "sufficient": False,
                "reason": "A code can identify pieces from different semantic producers.",
                "collisions": collisions,
            },
            "semantic_piece_id": {
                "sufficient": "FOR_RESOLVED_ROWS_ONLY",
                "reason": "A generated semantic piece ID distinguishes the known code collision, but 23 legal semantic cases remain unresolved.",
            },
            "code_source_bank": {
                "sufficient": "UNPROVEN",
                "reason": "Source-bank identity is unresolved for legal classes and does not encode context-dependent reindex choice.",
            },
            "code_effective_bank": {
                "sufficient": "UNPROVEN",
                "reason": "Effective-bank identity is unresolved for legal classes and code 0x0276 spans two semantic producers.",
            },
            "semantic_piece_effective_bank": {
                "sufficient": "FOR_RESOLVED_ROWS_ONLY",
                "reason": "Representable for resolved rows, but not exhaustive until every legal class and bank is closed.",
            },
            "semantic_piece_context": {
                "sufficient": "RECOMMENDED_REPRESENTATION",
                "reason": "The active context/epoch selects a generated bank; the compact semantic piece ID indexes a pre-resolved record without hot-path semantic reasoning.",
            },
            "semantic_piece_control_state": {
                "sufficient": "UNPROVEN",
                "reason": "Control state contributes to effective-bank derivation but is not a substitute for producer identity or context.",
            },
        },
        "recommended_key": {
            "bank_selector": "active graphics context/epoch",
            "row_index": "compact generated semantic piece ID",
            "static_record_fields": [
                "pixel reindex profile ID",
                "Genesis palette bits",
                "priority when semantically static",
                "Palette Decision ID",
            ],
            "dynamic_emit_fields": ["pattern slot", "H flip", "V flip", "priority when not semantically static"],
        },
        "completeness": "INCOMPLETE",
        "remaining_unresolved_semantic_cases": domain["counts"]["unresolved"],
    }


def make_profile_audit(profile: dict) -> dict:
    signatures: dict[str, dict] = {}
    usages = []
    for usage, mapping in sorted(profile.get("usage_palette_mappings", {}).items()):
        normalized = {
            "line": mapping.get("line"),
            "index_map": mapping.get("index_map", {}),
            "solver": mapping.get("solver", "explicit"),
        }
        encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        signature = hashlib.sha256(encoded.encode()).hexdigest()[:16]
        signatures.setdefault(
            signature,
            {"candidate_profile_id": f"TEST-{signature}", "mapping": normalized, "usages": []},
        )["usages"].append(usage)
        usages.append(
            {
                "usage": usage,
                "candidate_profile_id": f"TEST-{signature}",
                "authority": "frozen Test editor policy only; not canonical palette authority",
            }
        )
    rastan_profiles = sorted(
        {row["candidate_profile_id"] for row in usages if row["usage"].startswith("usage:rastan_")}
    )
    return {
        "schema_version": 1,
        "scope": "Round 1 Phase 1",
        "source_profile": profile.get("profile_id"),
        "source_authority": "diagnostic/frozen Test authoring; candidate evidence only",
        "usage_mapping_count": len(usages),
        "distinct_candidate_profile_count": len(signatures),
        "canonical_distinct_profile_count": UNRESOLVED,
        "candidate_profiles": sorted(signatures.values(), key=lambda row: row["candidate_profile_id"]),
        "usages": usages,
        "same_source_multiple_profiles": {
            "rastan_candidate_profile_ids": rastan_profiles,
            "candidate_observed": len(rastan_profiles) > 1,
            "canonical_r1p1_requirement_proven": False,
            "reason": "The Test editor profile contains multiple Rastan usage profiles, but the canonical registry does not identify accepted reindex profiles.",
        },
        "palette_tool_assessment": "PARTLY",
        "already_supported": [
            "usage-level palette line",
            "usage-level pixel index map",
            "context policy container",
        ],
        "required_explicit_model": [
            "stable reindex profile IDs",
            "context/epoch-selected semantic-piece records",
            "semantic piece to profile and palette-line relation",
            "context-specific transformed asset variants",
            "Palette Decision IDs",
        ],
        "current_limitation": "The generated sprite-asset path collapses each arcade code to one global usage mapping and rejects conflicts, so it cannot yet encode context-dependent variants of the same code.",
        "future_context_flexibility_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    registry = read_json(ROOT / "specs/palette_decisions.json")
    decisions = registry_index(registry)
    families = read_json(
        ROOT / "analysis/graphics_optimizer/round1_phase1_whole_game_lexicon/sprite_families.json"
    )
    coverage = read_json(
        ROOT / "analysis/graphics_optimizer/round1_phase1_whole_game_lexicon/sprite_class_coverage.json"
    )
    if [family["id"] for family in families] != coverage["legal_graphics_bearing_classes"]:
        raise SystemExit("legal sprite-family rows do not match the fail-closed coverage domain")

    live_routes = parse_live_routes(ROOT / "apps/rastan-direct/src/palette_hooks.s")
    reconciliation = make_reconciliation(registry, live_routes)
    domain = make_domain(families, decisions, live_routes)
    parity = make_parity(domain)
    lookup_keys = make_lookup_key_analysis(domain)
    profile_audit = make_profile_audit(
        read_json(ROOT / "analysis/graphics_optimizer/editor_policy/Test.json")
    )
    write_json(out / "palette_authority_reconciliation.json", reconciliation)
    write_json(out / "legal_sprite_palette_domain.json", domain)
    write_json(out / "sat_word2_parity.json", parity)
    write_json(out / "minimum_lookup_key.json", lookup_keys)
    write_json(out / "pixel_reindex_profile_audit.json", profile_audit)
    print(json.dumps({"domain": domain["counts"], "parity": {k: parity[k] for k in ["tested_combinations", "unresolved_semantic_cases", "mismatches", "result"]}}, sort_keys=True))
    return 0 if not parity["mismatches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
