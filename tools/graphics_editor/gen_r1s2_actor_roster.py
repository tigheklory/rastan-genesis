#!/usr/bin/env python3
"""PROMPT-ID-0025 — R1-S2 (castle) actor roster from STATIC arcade evidence (NO traces).

Builds the R1-S2 marker-driven actor roster by combining the already-proven static artifacts:
  - analysis/actor_decompilation/h6_marker_materialization_routes.tsv  (marker -> state -> handler -> base_source)
  - analysis/actor_decompilation/h13_phase2_marker_occurrences.tsv     (per-round phase-2 marker occurrences)
  - the maintained decompilation (rastan_actor_behavior.c / _dispatch.c) for the state->base assignments,
and confirms each resolved sprite base DECODES to real pieces via the static compositor VM
(tools/graphics_optimizer/compositor_vm — the Bestiary's render route, NOT a gameplay trace).

Scope note (honest): h13/h6 enumerate markers per ROUND-PHASE. For Round 1, phase-2 = subround S2 (castle)
+ S3 (boss). The S3 boss is RECORD-TYPE driven (table 0x45592, body base 0x061D), not marker driven, so
the phase-2 MARKER actors are attributed to the S2 castle. The exact per-scene S2/S3 marker split is the
documented open blocker (the A5+0x10D000 runtime collision-record populator); this roster is marker-driven
castle actors + the record-type boss listed separately.

Output: analysis/actor_decompilation/r1s2_actor_roster.json (deterministic). Read-only inputs.
"""
from __future__ import annotations
import csv, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H6 = ROOT / "analysis/actor_decompilation/h6_marker_materialization_routes.tsv"
H13 = ROOT / "analysis/actor_decompilation/h13_phase2_marker_occurrences.tsv"
OUT = ROOT / "analysis/actor_decompilation/r1s2_actor_roster.json"

# CORRECTION (PROMPT-ID-0038): the original 0025 roster mapped marker->state->base WITHOUT the handler
# PROGRESS GUARD, which over-attributed bases to R1. Reconciled against the source + Bestiary H14:
# handler 0x44082 (state 0x18) does `if (progress_13e < 0x18) arcade_4092e()` (RETIRE) — R1-S2 progress is
# 0x11..0x16 (< 0x18), so the R1 'E' marker RETIRES and base 0x0224 does NOT materialize in R1. Base
# 0x0224 materializes in R2,R4; base 0x00F4 in R4,R5,R6; marker 'M' burst is the R1 castle actor (children
# PENDING). The authoritative record is docs/design/rastan_actor_graphics_manifest.json (H14) — this file
# is a derived cross-check, NOT a competing roster.
STATE_BASES = {
    0x18: ("0x44082", [0x0224, 0x00F4], "h5_44082: 'E' -> base 0x0224 / retarget 'O' -> 0x00F4 ONLY when "
                                        "progress_13e >= 0x18 (R2+); RETIRES in R1 (guard prog<0x18)"),
    0x1B: ("0x43ECC", [],               "h5_43ecc: 'M' burst spawner (arcade_43f4e_burst, 5 children, anim 0x7A); "
                                        "R1 castle actor (H14 R1 prog 0x11); coordinate-only children, no static base"),
    0x1C: ("0x4415A", [0x0224],         "h5_4415a: 'G' -> base 0x0224 (R2 castle)"),
}
# Rounds where each base actually materializes (Bestiary H14, exact +0x1E write). NOT R1 for 0x0224/0x00F4.
BASE_ROUNDS = {0x0224: [2, 4], 0x00F4: [4, 5, 6]}


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _decode_base(base):
    """Confirm a sprite base decodes to real pieces via the static compositor VM. Returns a small summary
    (anims with >=2 pieces, a representative frame's piece count + tile codes) or None if it never decodes."""
    p = str(ROOT / "tools/graphics_optimizer")
    if p not in sys.path:
        sys.path.insert(0, p)
    try:
        from compositor_vm import ActorRenderState, visible_pieces
    except Exception as e:
        return {"decodable": None, "error": "compositor_vm import failed: %s" % e}
    anims = []
    rep = None
    for anim in range(0x100):
        try:
            sat = visible_pieces(ActorRenderState(base, anim, 0))
        except Exception:
            sat = None
        if sat and len(sat) >= 2:
            anims.append(anim)
            if rep is None:
                rep = {"anim": anim, "pieces": len(sat),
                       "tile_codes": ["0x%X" % (q.tile & 0x1FFF) for q in sat][:10]}
    return {"decodable": bool(anims), "anims_with_pieces": len(anims),
            "anim_ids_sample": ["0x%02X" % a for a in anims[:8]], "representative_frame": rep}


def main() -> int:
    h6 = _rows(H6)
    h13 = _rows(H13)
    # R1 phase-2 marker occurrences = the castle (S2) marker set (boss S3 is record-type driven).
    r1 = [r for r in h13 if r["round"] == "1"]
    # index h6 by state for route notes
    h6_by_state = {}
    for r in h6:
        st = r.get("output_state", "").strip()
        if st:
            h6_by_state.setdefault(st, r)

    actors = []
    for occ in sorted(r1, key=lambda r: r["marker"]):
        marker = occ["marker"]
        state = occ["state_+0x05"]
        handler = occ["handler_0x40BAA"]
        try:
            st_int = int(state, 16)
        except ValueError:
            st_int = None
        hb = STATE_BASES.get(st_int, (handler, [], "state->base not yet pinned in decompilation"))
        bases = []
        for b in hb[1]:
            bases.append({"base": "0x%04X" % b, "materializes_in_rounds": BASE_ROUNDS.get(b, []),
                          "r1_status": "RETIRES in R1 (handler guard prog<0x18) — NOT an R1 actor",
                          "graphics": _decode_base(b)})
        actors.append({
            "marker": marker, "marker_char": occ.get("route_note", ""),
            "occurrences": int(occ["occurrences"]),
            "state": state, "handler": handler,
            "state_handler_note": hb[2],
            "sprite_bases": bases,
            "status": ("MARKER_PRESENT_IN_R1_BUT_BASE_RETIRES" if (bases and st_int == 0x18)
                       else "RESOLVED_MARKER_TO_BASE" if bases else "MARKER_RESOLVED_BASE_UNPINNED"),
        })

    roster = {
        "schema": "rastan-r1s2-actor-roster/v2",
        "prompt": "PROMPT-ID-0025 (corrected under PROMPT-ID-0038)",
        "authority": ("docs/design/rastan_actor_graphics_manifest.json (Bestiary H14) is AUTHORITATIVE for "
                      "round placement; this file is a derived cross-check, not a competing roster."),
        "correction_0038": ("Original v1 over-attributed bases 0x0224/0x00F4 to R1-S2 by mapping "
                            "marker->state->base WITHOUT the handler PROGRESS GUARD. Source: handler 0x44082 "
                            "`if (progress_13e < 0x18) arcade_4092e()`; R1-S2 progress is 0x11..0x16 (<0x18) "
                            "so the R1 'E' marker RETIRES. H14: 0x0224 -> R2,R4; 0x00F4 -> R4,R5,R6. The "
                            "ONLY R1-S2 marker actor is the 'M' burst (children identity PENDING)."),
        "scope_note": ("R1 phase-2 MARKER-driven castle (S2) actors. S3 boss is record-type driven "
                       "(table 0x45592, body base 0x061D) and is listed separately. The exact per-scene "
                       "S2-vs-S3 marker split is the open blocker (A5+0x10D000 runtime populator)."),
        "sources": {
            "marker_routes": "analysis/actor_decompilation/h6_marker_materialization_routes.tsv",
            "marker_occurrences": "analysis/actor_decompilation/h13_phase2_marker_occurrences.tsv",
            "state_handlers": "analysis/decompilation/c/rastan_actor_behavior.c (h5_* handlers)",
            "sprite_decoder": "tools/graphics_optimizer/compositor_vm (static Bestiary route; NOT a trace)",
        },
        "marker_driven_castle_actors": actors,
        "record_type_boss_S3": {"record_type": "0x0E", "body_base": "0x061D",
                                "source": "rastan_actor_tables.c record_type_45592[0x0E]",
                                "note": "R1 boss body; record-type path, not marker driven"},
        "naming_status": ("Tighe's labels 'Armored Men' and 'Wizards' map to the marker-'E' humanoid "
                          "bases (0x0224 primary, 0x00F4 secondary/retarget) and the marker-'M' burst "
                          "spawner respectively — to be CONFIRMED by viewing the decoded graphics in the "
                          "Composer; this roster does not assert the visual label without that view."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(roster, indent=1) + "\n")
    nres = sum(1 for a in actors if a["sprite_bases"])
    print("R1S2_ACTOR_ROSTER_OK markers=%d resolved_to_base=%d -> %s"
          % (len(actors), nres, OUT.relative_to(ROOT)))
    for a in actors:
        bs = ",".join(b["base"] + ("[decodes]" if (b["graphics"] or {}).get("decodable") else "[no-decode]")
                      for b in a["sprite_bases"]) or "(burst/coordinate-only)"
        print("  marker %s (%s x%d) state %s -> %s" % (a["marker"], a["marker_char"], a["occurrences"], a["state"], bs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
