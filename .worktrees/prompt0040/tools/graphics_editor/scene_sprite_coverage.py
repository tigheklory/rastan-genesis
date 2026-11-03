#!/usr/bin/env python3
"""PROMPT-ID-0006 Req 4 / Criterion F — honest per-subround sprite/enemy coverage.

The Composer's Objects tab shows the proven R1/Phase-1 enemy corpus. For any OTHER scene it was
presenting that same corpus with no disclosure — exactly the silent substitution the task forbids.
This tool computes, per scene_key, what sprite/enemy roster is actually KNOWN for that scene and the
honest coverage status, from existing analysis (no new RE, no fabrication):

  - R1-S1 (Round 1, Phase 1): PROVEN_COMPLETE — analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv
    is the authoritative, captured enemy vocabulary already authored in the editor.
  - S2 (castle) scenes: SCHEDULE_ONLY — analysis/actor_subround2/subround2_schedule_rosters.json lists
    the per-round subround-2 family-2 spawner bases; these identify WHICH actors appear, but their
    complete per-scene cell vocabulary is not captured, so they cannot be authored yet.
  - Everything else: PENDING — per-scene markers are not enumerated (h11_phase2_actor_rosters.tsv blocker:
    "A5+0x10D000 collision-record populator"); h13 reachable_rounds is attached where it exists.

The editor consumes this to show a disclosure banner on non-R1-S1 scenes: the R1/P1 graphics are the
only authored sprite vocabulary and are NOT a substitute for this scene's enemies.

Output (deterministic): build/palette_export/scene_sprite_coverage.json   (read-only inputs)
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "specs/palette_subround_map.json"
R1P1 = ROOT / "analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv"
SR2 = ROOT / "analysis/actor_subround2/subround2_schedule_rosters.json"
H13 = ROOT / "analysis/actor_decompilation/h13_phase2_actor_rosters.tsv"
OUT = ROOT / "build/palette_export/scene_sprite_coverage.json"

BLOCKER = ("per-scene spawn markers not enumerated — blocked on the A5+0x10D000 collision-record "
           "populator (column marker source); see analysis/actor_decompilation/h11_phase2_actor_rosters.tsv")


def _r1p1_objects() -> list[str]:
    if not R1P1.is_file():
        return []
    objs, seen = [], set()
    for ln in R1P1.read_text().splitlines()[1:]:
        c = ln.split("\t")
        if c and c[0] and c[0] not in seen:
            seen.add(c[0]); objs.append(c[0])
    return objs


def _sr2_by_round() -> dict:
    return json.loads(SR2.read_text()) if SR2.is_file() else {}


def _h13_reach() -> dict[int, list[str]]:
    """round -> list of actor bases proven reachable in that round (from h13 reachable_rounds)."""
    out: dict[int, list[str]] = {}
    if not H13.is_file():
        return out
    rows = H13.read_text().splitlines()
    hdr = rows[0].split("\t")
    bi, ri = hdr.index("base"), hdr.index("reachable_rounds")
    for ln in rows[1:]:
        c = ln.split("\t")
        if len(c) <= max(bi, ri):
            continue
        rr = c[ri].strip()
        if rr and rr != "-":
            try:
                for r in json.loads(rr):
                    out.setdefault(int(r), []).append(c[bi])
            except Exception:
                pass
    return out


def main() -> int:
    smap = json.loads(MAP.read_text())
    r1p1 = _r1p1_objects()
    sr2 = _sr2_by_round()
    reach = _h13_reach()

    scenes = {}
    for sr in smap.get("subrounds", []):
        rnd, sub = sr["round"], sr["subround"]
        for env in sr.get("environments", []):
            if env.get("family") != "PLANEA":
                continue  # sprite coverage is per subround, keyed on the PLANEA scene
            sk = env["scene_key"]
            if rnd == 1 and sub == 1:
                status, roster, note = ("PROVEN_COMPLETE", r1p1,
                    "Authoritative captured R1/Phase-1 enemy vocabulary (already authored).")
            elif sub == 2:
                rkey = f"round{rnd}"
                bases = (sr2.get(rkey, {}) or {}).get("schedule_family2_spawners", []) \
                        + (sr2.get(rkey, {}) or {}).get("schedule_nonfamily2_bases", [])
                status, roster, note = ("SCHEDULE_ONLY", bases,
                    "Spawner bases from the subround-2 schedule identify WHICH actors appear, but their "
                    "complete per-scene cell vocabulary is not captured — cannot be authored yet.")
            else:
                status, roster, note = ("PENDING", [f"reachable base {b}" for b in reach.get(rnd, [])],
                    BLOCKER)
            scenes[sk] = {
                "scene_key": sk, "round": rnd, "subround": sub, "env": env["env"],
                "coverage_status": status,
                "roster": roster,
                "note": note,
                "authored_vocabulary": "R1/Phase-1 corpus only",
                "substitution_warning": (None if status == "PROVEN_COMPLETE" else
                    "The sprite graphics shown are the proven R1/Phase-1 vocabulary and are NOT a "
                    "substitute for this scene's enemies."),
            }

    manifest = {
        "schema": "rastan-scene-sprite-coverage/v1",
        "prompt": "PROMPT-ID-0006 Req 4 / Criterion F",
        "sources": {
            "proven_r1p1": "analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv",
            "subround2_schedule": "analysis/actor_subround2/subround2_schedule_rosters.json",
            "reachability": "analysis/actor_decompilation/h13_phase2_actor_rosters.tsv",
            "blocker_ref": "analysis/actor_decompilation/h11_phase2_actor_rosters.tsv",
        },
        "legend": {
            "PROVEN_COMPLETE": "captured, authorable now",
            "SCHEDULE_ONLY": "actors identified, cell vocabulary not captured",
            "PENDING": "per-scene roster not enumerated (blocked)",
        },
        "scenes": dict(sorted(scenes.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=1) + "\n")
    by = {}
    for s in scenes.values():
        by[s["coverage_status"]] = by.get(s["coverage_status"], 0) + 1
    print(f"SCENE_SPRITE_COVERAGE_OK scenes={len(scenes)} status={by} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
