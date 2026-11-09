#!/usr/bin/env python3
"""PROMPT-ID-0092 — generated-artifact stale-claim verifier for the Bestiary.

PROMPT-ID-0091's verifier checked implementation constants/oracle objects while the GENERATED
Bestiary still carried contradictory prose. This closes that gap: it reads the actual regenerated
HTML artifact that a human reads (docs/design/rastan_actor_bestiary.html) and fails if any prohibited
CURRENT claim is present, and also fails if the positive replacement claims are absent. It does NOT
inspect Python/server objects — the artifact itself is the acceptance test.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0092
"""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "docs/design/rastan_actor_bestiary.html"

# Prohibited CURRENT claims — obsolete reward three-bank model, obsolete Green Knight domain,
# and the disproven Round-1-boss field-pool-RGB wording. These are the user-facing claims; the
# removal/history SENTENCES (which contain "29/109 ... removed", "false three-bank ... removed")
# deliberately do NOT match these needles.
FORBIDDEN = [
    "banks 0x30/0x31/0x37",
    "banks 0x30 (1-4)",
    "0x30 (kinds 1-4)",
    "banks 0x30 (kinds",
    "29 programs",
    "109 codes",
    "line F = 0x3BA88",
    "boss line F = 0x3BA88",
    "colours per pool",
    "MAME-verified body frame+palette",
    "Render/palette Cody-verified",
    # the removed Composer reward objects (false three-bank model)
    "gameplay_reward_b31",
    "gameplay_reward_b37",
    "object:effect.item_drop_death",
]

# Positive replacement claims that MUST be present in the artifact.
REQUIRED = [
    # Green Knight corrected domain
    "23 programs / 97 pattern codes",
    # Rope climber as a separate family-8 base-$0241 object (rope-specific markup, distinct from the
    # pre-existing Valkyrie field enemy that happens to share base graphics 0x0241)
    "object:castle.rope_climber.family8.r1",
    "0x0241</span>, state $11",
    "$56,$59,$5A",
    # Rewards: compositor 2, 17 kinds/children, embedded lines 0/3
    "compositor 2",
    "17 reward kinds",
    "object:item.reward.kind01",
    "line 0 (kinds 1-13)",
    "line 3 (kinds 14-17)",
    # Round 1 boss: body program + honest line-vs-RGB provenance
    "0x47908",
    "LINE-F SELECT PROVEN · RGB PENDING",
    "staged boss RGB PENDING",
    # R1-S2 traps: now PROVEN + authorable (spikes $09EA + fire/water palette animation $59AD4)
    "R1-S2 traps now PROVEN + AUTHORABLE",
]


def main() -> int:
    if not HTML.is_file():
        print("FAIL artifact missing: regenerate with tools/graphics_optimizer/build_bestiary.py")
        return 1
    txt = HTML.read_text(encoding="utf-8")
    P = F = 0

    print("----- FORBIDDEN current-claim scan (each count must be 0) -----")
    for needle in FORBIDDEN:
        n = txt.count(needle)
        ok = n == 0
        P += ok; F += (not ok)
        print(("PASS " if ok else "FAIL ") + f"[{n}] {needle!r}")

    print("\n----- REQUIRED replacement-claim scan (each must appear) -----")
    for needle in REQUIRED:
        n = txt.count(needle)
        ok = n >= 1
        P += ok; F += (not ok)
        print(("PASS " if ok else "FAIL ") + f"[{n}] {needle!r}")

    # Boss honesty must hold per card: the field-pool rule must never be generalized as authoritative
    # boss RGB. Each boss card carries EITHER the R1 proven badge (RGB PROVEN · ROM 0x4708C — Cody
    # PROMT-ID-0095, integrated under PROMT-ID-0098) OR the "LINE-F SELECT PROVEN · RGB PENDING" badge
    # (R2-R6, still pending). No card may carry both the pending badge AND a field-pool RGB claim.
    pend_badges = txt.count("LINE-F SELECT PROVEN · RGB PENDING")
    r1_proven = txt.count('<span class="b ok">RGB PROVEN · ROM 0x4708C</span>')
    boss_cards = txt.count('class="card boss"')
    ok = boss_cards >= 6 and r1_proven >= 1 and (pend_badges + r1_proven) == boss_cards
    P += ok; F += (not ok)
    print("\n----- Per-boss-card honest line-vs-RGB provenance -----")
    print(("PASS " if ok else "FAIL ") +
          f"[proven R1={r1_proven} + pending={pend_badges} == cards={boss_cards}] every boss card is either "
          f"R1 'RGB PROVEN · ROM 0x4708C' or 'LINE-F SELECT PROVEN · RGB PENDING' (cards>=6, >=1 proven)")

    print(f"\n{'BESTIARY ARTIFACT 0092 PASS' if not F else str(F)+' FAILED'}  (pass={P})")
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
