# Andy — Player Source-Block Population Fix Attempt (A5+0x11B2)

Baseline HEAD `77eb1bd`, counter `163`. Candidate cart
`dist/rastan-direct/rastan_direct_video_test_build_0163.bin`
(SHA `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`).
Result: **Build 0164 NOT produced — implementation STOP.** First proven blocker is a
multi-site raw-WRAM-literal family, not a bounded single fix.

## 1. Baseline
No source/spec/tool/Makefile/invariant/ROM changes. Evidence-only. Arcade code remains
the program; only the Genesis helper / opcode-replace path was inspected.

## 2. Arcade source writers (0x10D1B2)
Arcade populates the player PC090OJ source block `0x0010D1B2..0x0010D241` (A5+0x11B2,
18 words) during active gameplay. Writer PCs cluster in `0x0544xx..0x0547xx`
(0x05471E×1012, 0x054724, 0x054746, 0x0545D6×506, 0x0544DE×253, 0x054530×759, plus the
0x054062..0x0540AA init cluster). Final arcade block:
`4003 0049 009E 0010 4003 0059 009F 0010 0003 0000 0000 0000 0003 0000 0000 0000 4003 0051`
— player codes `0x009E`, `0x009F` present.

Disassembly shows the writers read control fields via A5-relative (correct:
`addw %a5@(4288),%d0` @0x54710, `cmpiw #2,%a5@(4372)` @0x54728) but load the
**destination base via a raw arcade-WRAM literal**:
`movea.l #0x0010D1B2, An` (opcodes 0x207C / 0x227C). Eight sites load exactly
`0x0010D1B2`: `0x51E00, 0x5288C, 0x52A6C, 0x54074, 0x5430C, 0x5457A, 0x545BA, 0x547C8`.
Record offsets into the same array are loaded the same way
(`0x10D1D2, 0x10D1F2, 0x10D212, 0x10D2A8, 0x10D2C8, 0x10D338, 0x10D420`).

## 3. Genesis mapped writers + result
Genesis (Build 0163) write-tap over the active window:
- Writes to **mapped `0x00FF11B2..0x00FF1241`: NONE.**
- Writes to **raw `0x0010D1B2..0x0010D241`: MANY**, from PCs
  `0x54946, 0x5484E, 0x5490C, 0x0547D2, 0x5498E, 0x05491E, 0x54924, 0x546DE, 0x54730,
  0x547D6, 0x54708, ...` plus helper `0x071F70..0x071FB8`.
- Genesis `0x00FF11B2` block after the window: all 18 words `0000` (empty).

The Genesis writer PCs are exactly the arcade writers +0x200 (relocation_delta):
`0x5471E→0x5491E, 0x544DE→0x546DE, 0x545D6→0x547D6, 0x54530→0x54730, 0x54724→0x54924`.
They **execute**, but their destination `An` still holds the raw literal `0x0010D1B2`,
which on Genesis is ROM (unmapped for writes) → every store is dropped. The A5-relative
control reads work because a5 = 0xFF0000; only the raw absolute destination base is wrong.

## 4. First proven source-state blocker
**KF-044.** The player source block is never populated on Genesis because the writers
address the destination through un-rebased raw arcade-WRAM immediates
(`movea.l #0x0010D1B2,An`, opcodes 0x207C/0x227C). The postpatch relocation only shifts
code-region absolute operands (0x4EB9/0x4EF9/LEA abs.l in [0,0x60000)); it does **not**
rebase WRAM immediates (0x10C000..0x10FFFF → 0xFF0000..). Same defect class as the
pass-selector `movel #imm,Dn` (KF-042) and the raw-WRAM producers KF-039. Genesis
`0x00FF11B2` therefore stays empty, and the downstream copy has nothing to copy.

## 5. Destination mapping (0x041F5E)
Secondary, real, but non-gating: original arcade `0x041F5E` = `lea %a5@(4530),%a0`
(a5+0x11B2, A5-relative — correct on Genesis). Its Genesis replacement
`genesistan_pc090oj_hook_target_41f5e` → `pc090oj_workram_block_sprites` copies
A5+0x11B2 into records `0..17` (and A5+0x0170 into `18..21`) instead of the arcade
destination records `120..137` (and `92..95`). Correcting this alone is unsafe while the
A5+0x11B2 source is empty (§4): it would copy zeros into remapped records.

## 6. State-causality + classification
Classification: **first-broken-state = SOURCE (A5+0x11B2 empty)**, caused by the raw-WRAM
destination-literal defect (§4). Destination-record remap (§5) is downstream and must not
be built first — matches the task rule "Do not build a destination-only fix while the
source block remains empty."

## 7. Why not a bounded Build 0164
The source fix is **not** one literal. It is a family: 8 base-literal sites + ≥7
record-offset literals for this array, and it is part of a systemic residue of **61
un-rebased raw arcade-WRAM immediates** across [0x10C000,0x110000) (e.g. palette
`0x10D600`×6, collision `0x10DE00`, `0x10D338`×3, `0x10C170`×3 …). Build 0158 rebased
exactly one such literal (`0x10C016→0xFF0016`) by hand via `opcode_replace`. Rebasing the
whole player family plus pairing the §5 remap is a multi-site, two-part change with
per-site safety proof required (some base-loaders `0x51E00/0x5288C/0x52A6C` live in
different routines). That exceeds a bounded candidate.

Recommended proper fix (separate systemic build, not this task): extend the postpatch to
rebase raw-WRAM immediate operands in [0x10C000,0x110000) for `movel #imm,Dn` (0x203C),
`movea.l #imm,An` (0x207C/0x227C) and siblings → +0xEF4000, with a guard list against
false-positive non-address literals. That single pass closes the player, palette, and
collision raw-literal residue at once; only then does the §5 record remap become
meaningful.

## 8. Exact change if built / validation
Not built. If/when the systemic rebase lands, validation = re-run §3 taps and require
mapped `0xFF11B2` writes present + block non-zero with player codes `0x009E/0x009F`, then
Tighe visual verify. Build 0163's forced gameplay tile-DMA requeue gate remains in
`pc090oj_hooks.s` unchanged; **no Build 0164 exists, so it does not carry (or drop) that
experimental source** — the working tree and counter (163) are unchanged.

## 9. Open/Closed + KF + Architecture
- OPEN-017 (gameplay render/run): touched; player-invisibility source root cause proven
  (KF-044). No closure — fix deferred to systemic WRAM-literal rebase build.
- KNOWN_FINDINGS: **KF-044 added** (raw-WRAM immediate destination literals not rebased →
  Genesis WRAM producers write ROM / dropped).
- Architecture: CONFIRMED evidence-only; no NOPs/RTS, no hardcoded records/codes/SAT, no
  broad PC090OJ rewrite, palette/VINT/vector/SR/VDP-reg ownership untouched.
