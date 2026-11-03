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

# State -> visible sprite base(s), read from the maintained decompilation (rastan_actor_behavior.c handlers).
# Each entry: state -> (handler_pc, [bases], note). Bases verified present in rastan_actor_behavior.c.
STATE_BASES = {
    0x18: ("0x44082", [0x0224, 0x00F4], "h5_44082: 'E' chain -> base 0x0224 then retarget 'U'/'O' -> base 0x00F4"),
    0x1B: ("0x43ECC", [],               "h5_43ecc: 'M' burst spawner (arcade_43f4e_burst, 5 children, anim 0x7A); "
                                        "coordinate-only child presentation (seeded SAT), no single static base"),
    0x1C: ("0x4415A", [0x0224],         "h5_4415a: 'G' (R2 castle) -> base 0x0224"),
}


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
            bases.append({"base": "0x%04X" % b, "graphics": _decode_base(b)})
        actors.append({
            "marker": marker, "marker_char": occ.get("route_note", ""),
            "occurrences": int(occ["occurrences"]),
            "state": state, "handler": handler,
            "state_handler_note": hb[2],
            "sprite_bases": bases,
            "status": ("RESOLVED_MARKER_TO_BASE" if bases else "MARKER_RESOLVED_BASE_UNPINNED"),
        })

    roster = {
        "schema": "rastan-r1s2-actor-roster/v1",
        "prompt": "PROMPT-ID-0025",
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
