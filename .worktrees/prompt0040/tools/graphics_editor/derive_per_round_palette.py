#!/usr/bin/env python3
"""PROMPT-ID-0006 Req 1 / Criterion E — static derivation of Rastan's per-round palette loading.

WHY THIS EXISTS
  The Composer derived every scene's arcade Plane-A colors from the FIXED startup table
  (0x4EAF6 + bank*32). PROMPT-ID-0006 Req 1 asks whether that is correct for Round 2+, and to
  obtain genuine Round-2 evidence *or*, if a clean R2 state cannot be reproduced, to derive what can
  be derived from the original loading routines and clearly state the remaining uncertainty WITHOUT
  fabricating colors.

  A genuine Round-2 live-palette capture could NOT be produced three ways:
    - forcing the round counter (0x10C118:=2) from boot corrupts the appearance/state machine;
    - the _Sx-y stage-select ROMs set the stage index (0x10D242) but leave the round counter at 1
      (the "RG-019 quirk"), so they never load a per-round R2 palette;
    - poking the subround-complete marker (0x10D243) does not advance the round counter.
  So this file DERIVES from the arcade loader instead, and labels the residual uncertainty.

WHAT IS PROVEN HERE (all from build/regions/maincpu.bin, the authoritative arcade program):
  1. Conversion: arcade ROM 0RGB nibble -> live xBGR-555 is  field = nibble*2, packed
     word = (B2<<10)|(G2<<5)|R2.  Verified: 0x4EAF6+3*32 reproduces the live R1 palette-RAM bank 3
     (states/traces/palram_R1) EXACTLY.
  2. The visible R1 Plane-A background bank 3 is sourced from the FIXED base 0x4EAF6 — NOT from the
     per-round pool 0x4FD02 (whose decode for the same bank differs).
  3. A genuine per-round bank-index table EXISTS at 0x3BA88 (32 pool-indices per round, loaded by the
     routine at 0x3BA20 through 0x4FD02). Round 2's row genuinely differs from Round 1's, so the
     per-round mechanism is real and data-driven.

REMAINING UNCERTAINTY (stated, not papered over):
  Whether any 0x200000-region Plane-A bank is *reloaded* per-round (overwriting the fixed base for
  R2+) is UNCONFIRMED. R1 bank 3 provably comes from the fixed base and the per-round pool feeds a
  separate buffer (a5+0x1600); but an earlier round-forcing test perturbed bank 0x003, which the
  fragile forced state makes unreliable. Confirming/refuting this needs a genuine R2 live capture.

  Consequence for the Composer: it keeps deriving Plane-A colors from the PROVEN fixed base (no
  fabricated R2 colors). The real R2/arcade mismatch Tighe saw is explained by the editor previously
  applying R1's scope/records to R2 (fixed-scope + R1-record-decode bugs), both fixed under
  PROMPT-ID-0006 Req 2/Req 3 so each scene now reads its OWN records and bank set.

Output (deterministic): analysis/graphics_optimizer/per_round_palette_evidence.json
Read-only against the arcade ROM; writes one evidence JSON. No ROM build, no registry mutation.
"""
from __future__ import annotations
import json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "build/regions/maincpu.bin"
R1_DUMP = ROOT / "states/traces/palram_R1/palram.tsv"
OUT = ROOT / "analysis/graphics_optimizer/per_round_palette_evidence.json"

FIXED_BASE = 0x4EAF6     # round-independent startup color table (0RGB nibble), bank*32
POOL_BASE  = 0x4FD02     # per-round color pool, indexed by the 0x3BA88 table (0RGB nibble), idx*32
RTAB_BASE  = 0x3BA88     # per-round bank-index table, round r uses +(r-1)*32, 32 one-byte indices
LOADER_PC  = 0x3BA20     # per-round loader (reads round counter 0x10C118, fills a5+0x1600 buffer)
MAX_ROUNDS = 7


def _mc() -> bytes:
    return MAIN.read_bytes()


def _w(mc: bytes, a: int) -> int:
    return struct.unpack(">H", mc[a:a + 2])[0]


def conv_bank(mc: bytes, addr: int) -> list[int]:
    """16 ROM 0RGB nibble words at addr -> 16 live xBGR-555 words (nibble*2 per channel)."""
    out = []
    for i in range(16):
        s = _w(mc, addr + 2 * i)
        R, G, B = (s >> 8) & 0xF, (s >> 4) & 0xF, s & 0xF
        out.append(((B * 2) << 10) | ((G * 2) << 5) | (R * 2))
    return out


def _live_r1_bank(n: int) -> list[int] | None:
    if not R1_DUMP.is_file():
        return None
    tag = f"bank 0x{n:03X}:"
    for line in R1_DUMP.read_text().splitlines():
        if line.startswith(tag):
            return [int(x, 16) for x in line.split(":", 1)[1].split()]
    return None


def round_table(mc: bytes, rnd: int) -> list[int]:
    base = RTAB_BASE + (rnd - 1) * 32
    return list(mc[base:base + 32])


def main() -> int:
    mc = _mc()

    # (1)+(2) Prove the fixed base reproduces live R1 bank 3, and the per-round pool does not.
    fixed_b3 = conv_bank(mc, FIXED_BASE + 3 * 32)
    live_b3 = _live_r1_bank(3)
    r1tab = round_table(mc, 1)
    pool_for_b3 = conv_bank(mc, POOL_BASE + r1tab[3] * 32)
    fixed_matches_live = (live_b3 is not None and fixed_b3 == live_b3)
    pool_matches_live = (live_b3 is not None and pool_for_b3 == live_b3)

    # (3) Per-round tables, and how many banks differ from round 1.
    tables = {r: round_table(mc, r) for r in range(1, MAX_ROUNDS + 1)}
    diffs_vs_r1 = {r: [k for k in range(32) if tables[r][k] != tables[1][k]]
                   for r in range(2, MAX_ROUNDS + 1)}

    evidence = {
        "schema": "rastan-per-round-palette-evidence/v1",
        "prompt": "PROMPT-ID-0006 Req 1 / Criterion E",
        "source_rom": "build/regions/maincpu.bin",
        "conversion": "live_xBGR555 = (B*2)<<10 | (G*2)<<5 | (R*2); R,G,B are the arcade 0RGB nibbles",
        "addresses": {
            "fixed_startup_base": f"0x{FIXED_BASE:05X}",
            "per_round_pool_base": f"0x{POOL_BASE:05X}",
            "per_round_index_table": f"0x{RTAB_BASE:05X}",
            "per_round_loader_pc": f"0x{LOADER_PC:05X}",
            "round_counter_ram": "0x10C118",
        },
        "proofs": {
            "fixed_base_reproduces_live_R1_bank3": fixed_matches_live,
            "per_round_pool_reproduces_live_R1_bank3": pool_matches_live,
            "fixed_bank3_words": [f"{x:04X}" for x in fixed_b3],
            "live_R1_bank3_words": ([f"{x:04X}" for x in live_b3] if live_b3 else None),
            "conclusion": ("R1 Plane-A bank 3 is sourced from the FIXED base 0x4EAF6, NOT the "
                           "per-round pool 0x4FD02." if (fixed_matches_live and not pool_matches_live)
                          else "INCONCLUSIVE — re-run with a valid states/traces/palram_R1 dump."),
        },
        "per_round_index_tables": {f"round{r}": [f"{b:02X}" for b in tables[r]]
                                    for r in range(1, MAX_ROUNDS + 1)},
        "per_round_differs_from_round1": {f"round{r}": diffs_vs_r1[r] for r in diffs_vs_r1},
        "genuine_R2_capture": {
            "status": "NOT_REPRODUCED",
            "attempts": [
                "force round counter 0x10C118:=2 from boot -> corrupts appearance/state machine",
                "stage-select _Sx-y ROMs set stage 0x10D242 but leave round counter at 1 (RG-019 quirk)",
                "poke subround-complete marker 0x10D243 -> round counter did not advance",
            ],
        },
        "remaining_uncertainty": (
            "Whether any 0x200000-region Plane-A bank is RELOADED per-round (overwriting the fixed "
            "base for R2+) is UNCONFIRMED. R1 bank 3 provably uses the fixed base and the per-round "
            "pool fills a separate buffer (a5+0x1600); an earlier round-forcing test perturbed bank "
            "0x003 but under a fragile forced state. A genuine R2 live capture is required to settle "
            "it. Until then the Composer keeps the PROVEN fixed-base colors and fabricates nothing."
        ),
        "composer_action": (
            "Keep deriving Plane-A colors from the fixed base 0x4EAF6 (proven). Each scene now reads "
            "its OWN segment records/bank set (Req 2 scope fix + Req 3 selector-aware decode), which "
            "is what actually corrects the R2 appearance the fixed-scope/R1-record bugs caused."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=1) + "\n")
    print(f"PER_ROUND_PALETTE_EVIDENCE_OK fixed_matches_live={fixed_matches_live} "
          f"pool_matches_live={pool_matches_live} "
          f"rounds_differing={ {r: len(v) for r, v in diffs_vs_r1.items()} } -> {OUT.relative_to(ROOT)}")
    return 0 if fixed_matches_live else 1


if __name__ == "__main__":
    raise SystemExit(main())
