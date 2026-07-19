# Cody — First Lizard-Man Record Ownership and True-VRAM Trace

**Date:** 2026-07-18
**Type:** Analysis / verification only. **No ROM, no source/spec/tool/Makefile/gate change.**
**Trace dir:** `states/traces/first_lizard_record_ownership_true_vram_20260718_170426/`
**Decision-matrix outcome:** **A — record 46 is NOT the (visible) first lizard man.**

## Phase 0 baseline
Relevant priors from KNOWN_FINDINGS:
- KF-060 — enemy PC090OJ records 46/57/96/140 never staged (arcade 0x41DAE/0x45DFA NOPped); applicability: staging-gap root.
- KF-061 — engine 0x3D254 unsafe when called on INVALID (code-0) actors; superseded scope: unsafe only for invalid actors (per KF-063).
- KF-062 — Genesis DOES populate enemy actor blocks (camera/scroll spawn works); applicability: population is not the blocker.
- KF-063 — engine safe on VALIDATED actors; Build 0204 fixed record-46 empty output via the shared 0x3C950 PC080SN/PC090OJ collision; record 46 reaches SAT slot 16.
Rediscovery Hazard HIGH findings touched: KF-060, KF-061, KF-062, KF-063.
Task classification: EXTENDING — tests/narrows the record-46 lizard attribution assumed by Build 0204/0205.
Open/Closed issues touched: OPEN-017, OPEN-024, OPEN-001 (graphics context).
Contradiction of CONFIRMED/STRONG finding: NONE. (KF-063's technical claims remain valid; only the record-46→lizard ATTRIBUTION in the Build 0204/0205 narrative is corrected.)

## Recovered repository state (verified, matches authoritative)
counter 204; rolling Build 0204/256 SHA `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083` size 1583248; Makefile default 256; config 256; opcode_replace 214; coverage 0x182890; Build 0203 preserved (rejected diagnostic); Build 0202 consumed/deleted; Build 0205/0206 absent. No discrepancy. No changes made by this task.

## Phase 1 — Arcade lizard-man owner PROVEN (record 46 is NOT it)
Arcade Rastan run with `-rompath roms`. At F660/F750 the green **lizard men** are on-screen (snapshots arc46/rastan/0001.png, arc/rastan/0002.png).

Full PC090OJ dump at F750 (lizards visible):
- **Composite record groups 190..227** — 4 groups of 8 records, word0=`0x4046` (size/attr bits), sprite codes **0x004B..0x0069**. On-screen X≈0x8C..0xA7 matching the visible lizard positions; smooth leftward walking motion (rec190 X 0xE6→0xD4 over F600..F670). **These are the visible lizard men.**
- **Record 46** = `[0000 0180 0277 0029]` — single record (word0=0), code **0x0277**, **Y=0x0180 (OFF-SCREEN)** while lizards are visible. It flickers on/off near Rastan (X≈0x28, code toggling 0x0276/0x0277, Y 0x61↔0x180 every frame). A single 8×8 sprite at Rastan's position — **not a lizard-man body.**

Owner correlation (arcade, block 0x2C8 vs composite records 140..229):
```
F450 blk0x2C8 act=6 codes=[00,17,17,17,18,18]  composite(140..229) code!=0 = 16
F600 blk0x2C8 act=6 codes=[00,17,17,1D,17,17]  composite = 38
F750 blk0x2C8 act=6 codes=[00,18,1C,18,17,17]  composite = 48
F900 blk0x2C8 act=6 codes=[70,17,17,17,17,17]  composite = 52
```
Composite record population tracks block **A5+0x2C8** activity (6 actors → ~52 records = ~6-7 groups of 8). No `lea 0xD005xx` writes records 190+; they fall in block-0x2C8's engine expansion range (base record 140, 9 entries × d2≈10 → records 140..230). **Proven owner: actor block A5+0x2C8 → composite PC090OJ records ~140..229 (output codes 0x004B..0x0069).**

Phase 1 decision: record 46 / code 0x0275-0x0277 is **NOT** the visible lizard man → proceed with the corrected owner (block 0x2C8 / records 140..229).

## Phase 2 — Genesis Build 0204 matched state
Block A5+0x2C8 (Genesis, camera scrolled, F900/F1100):
```
e0: fl=01 code1=00 f3=01   (INVALID: code-0 + a4@(3)=1 — the Build 0202 corruptor)
e1-e3: inactive
e4-e8: fl=01 code1=17/18   (VALID lizard actors, codes match arcade)
```
Genesis mirror at the matched frame:
- record 46 = `[0000 0069 0277 006B]` — nonzero, on-screen (the Build 0204 record-46 fix working; SAT slot 16, tile 0x0440, palette line 2).
- **records 190..229 = `[0000 0100 0000 0100]` (BLANK, code 0); nonzero-code count = 0.**
- represented count = 17. Screenshot gen_snap/genesis/0000.png: Rastan present, **no lizard men** on the right.

The current staging helper (pc090oj_hooks.s:533) processes **only block A5+0x748** (→ record 46). Block A5+0x2C8 (the lizard men) is **never staged**, so its composite records 140..229 stay blank. The valid lizard actors (e4-e8, codes 0x17/0x18) exist on Genesis but produce no PC090OJ output.

## Actor-to-record chain (corrected)
| | Arcade | Genesis Build 0204 |
|---|---|---|
| Lizard actors | block A5+0x2C8, codes 0x17/0x18/0x1C-0x1F/0x70 | block A5+0x2C8 present, valid codes 0x17/0x18 (e4-e8) |
| Lizard PC090OJ records | composite 140..229, codes 0x004B-0x0069 | **BLANK (never staged)** |
| Record 46 (NON-lizard) | block A5+0x748, code 0x0277, single sprite | staged nonzero (Build 0204 fix) — a secondary sprite |

## Phases 3-5 (record-46 true VRAM) — NOT PERFORMED (wrong target)
Record 46 is not the lizard man, so its true-VRAM trace is irrelevant to lizard visibility. The actual lizard records (140..229) are **blank in the Genesis mirror** — there is no SAT/tile-DMA/VRAM to trace for the lizard until block A5+0x2C8 is staged. The lizard chain therefore breaks at the **object-source/staging layer** (analogous to KF-060, for block 0x2C8), proven by reliable WRAM/mirror sampling — no VDP-VRAM Lua reads were relied upon. No "USER MUST VERIFY" true-VRAM item is warranted at this stage; the blocker is upstream of VRAM.

## Bat evidence constraints
- Timed surface swarm: comparison only; not investigated; recognizable bat artwork with wrong palette (per Tighe). Not combat-tested (Tighe captured a screenshot; swarm collision/death UNKNOWN).
- Underground cave bat: separate observation; spawned, rendered, and was killed (per Tighe) — a distinct working route.
- Bat palette defect: intentionally deferred (out of scope).
- Record 46 (block 0x748, single flickering sprite that Build 0204 made reach SAT) is a DISTINCT small non-lizard actor. Its Build-0204 fix is consistent with a small enemy now reaching output, but this document does **not** assert record 46 = bat without direct visual proof, and does **not** combine the bat and lizard cases.

## First proven divergence
The visible first lizard men are produced by expanding actor block A5+0x2C8 into composite PC090OJ records ~140..229 (codes 0x004B-0x0069). On Genesis these records are blank because the staging helper stages only block A5+0x748 (record 46, a non-lizard sprite). The lizard actors are present and valid on Genesis; the divergence is at the staging/expansion layer for block A5+0x2C8.

## Decision-matrix outcome: A
Record 46 is not the lizard man. Actual owner identified: block A5+0x2C8 → records ~140..229. Do NOT patch/trace record 46 for the lizard. STOP with the next bounded task below.

## Recommended next bounded task
Extend the proven narrow staging (KF-063 non-zero-code guard — which safely skips code-0 entries like block-0x2C8 e0 and processes valid actors) to **block A5+0x2C8 → records 140+** (composite lizard bodies), reproducing arcade 0x41DAE's block-3 iteration (9 entries, d2=10/19, a4@(5)/a4@(3) gates) into the fixed scratch, engine-expanded, flushed to the mirror. The valid lizard actors (e4-e8, codes 0x17/0x18) match arcade and the guard makes engine calls safe (proven for record 46 in Build 0203/0204). Then re-run the true-VRAM trace on the ACTUAL lizard records (140..229 / their SAT slots).

## Open/Closed Issues Impact
Open touched: OPEN-017 (lizard owner corrected to block 0x2C8/records 140-229; record 46 is a non-lizard secondary sprite), OPEN-024. New: NONE. Closed: NONE (no closure condition met). Deferred: block-0x2C8 staging (next task), bat palette, true VRAM (after correct records exist).

## KNOWN_FINDINGS impact
Option A — add a new finding (KF-064) recording the corrected lizard ownership (block A5+0x2C8 → composite records 140..229, codes 0x004B-0x0069) and that record 46 (block 0x748, code 0x0277) is a distinct non-lizard sprite. KF-063 is NOT weakened: its claims (engine safe on validated actors, 0x3C950 fix, record 46 reaches SAT) remain valid; only the record-46→lizard attribution is corrected.

## STOP status
STOP triggered: YES (Outcome A — corrected owner identified; no fix in this task).
