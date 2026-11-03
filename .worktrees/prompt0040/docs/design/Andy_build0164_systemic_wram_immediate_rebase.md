# Andy — Build 0164: WRAM-Immediate Rebase + 0x041F5E Destination Split

Baseline HEAD `77eb1bd`, counter 163 → **Build 0164 produced**
(`dist/rastan-direct/rastan_direct_video_test_build_0164.bin`,
SHA `76e93b2f66563632216c03377a679e47a7655e17e78731b230e81a6f00435c6a`, 1,581,268 bytes,
counter 164). GATE_PASS.

## Outcome summary
Two changes were designed for this build:

1. **pc090oj 0x041F5E destination-mapping split** — SHIPPED, proven safe + correct.
2. **Systemic WRAM-immediate rebase (KF-044)** — IMPLEMENTED as spec-gated
   infrastructure, but **GATED OFF** in the shipped ROM because enabling it (even the
   minimal player-source-block scope) **regresses gameplay progression**.

The shipped ROM therefore matches Build 0163's WRAM behavior (no regression) plus the
correct destination-record split. The player source block `0xFF11B2` is **not** populated,
because the only mechanism that could populate it (rebasing the writers' raw-WRAM
literals) breaks the pre-spawn transition.

## 1. WRAM-immediate rebase pass (implemented, mechanically verified)
Added `rewrite_wram_immediate_literals_in_scan_windows` +
`build_move_immediate_long_opcode_set` to `postpatch_startup_rom.py`, gated by
`spec.wram_immediate_relocation`. It decodes by instruction class — MOVE.L #imm,Dn
(0x2n3C) and MOVEA.L #imm,An (0x2n7C) — and rebases immediate-long operands whose value
lies in a configured arcade-WRAM value window by `+0x00EE4000`
(`0x0010C000→0x00FF0000`). Delta arithmetic asserted at load
(`0x10D1B2→0xFF11B2`, `0x10D600→0xFF1600`, `0x10DE00→0xFF1E00`). Every rebase/skip is
logged. Value-window guard + the exact 16-opcode set prevent corrupting non-address
literals; the one adjacent constant `movel #0x100010,d1` @0x41880 is correctly skipped
(outside window). Full-window run rebased **55 sites / 28 literals** with **0 anomalies**
(verified against the ROM), confirming the mechanism is correct.

## 2. Why it is gated OFF — progression regression (runtime-proven)
| Build variant | writerExec (0x542–0x54A, gameplay) | producer freeze | progresses? |
|---|---|---|---|
| 0163 (control) | 561, frames[536..718] | no | YES |
| 0164 full systemic (55 sites) | 0 | at F480 | NO (frozen) |
| 0164 narrow (2 player blocks) | 0 | at F480 | NO |
| 0164 block A only (0x10D1B2) | 0 | at F480 | NO |
| 0164 split only, rebase OFF | 626, frames[536..719] | no | YES |

Isolation proved the **pc090oj split is safe** (rebase OFF → progresses) and the **WRAM
rebase is the sole regressor** — and that even rebasing *only* the player source block
`0x10D1B2` freezes gameplay. Cause: the `0x10D1B2` block is accessed pre-spawn by
non-player-cluster routines — reader `0x51E00` (`movea.l #0x0010D1B2,a1; move.w a1@,…`)
and writer/init `0x5288C`/`0x52A6C` (`movea.l #0x0010D1B2,a0; move.w #5,a0@+`). On Genesis
with raw literals these alias ROM (constant reads / dropped writes), and the mis-ported
progression logic only advances in that state. Rebasing to zero-initialised WRAM changes
the transition and it never reaches player spawn (~F536), so the writers never run.

Corollary: there is **no bounded WRAM-rebase scope** that populates the player source
without regressing the game, and there are **no a5-relative gameplay writers** to
`0xFF11B2` (only startup-zeroing `0x03B102`/`0x03A4D4`). The player source cannot be
populated by literal rebasing alone.

This matches the project's existing precedent: safe WRAM-literal rebases are done as
**targeted per-site `opcode_replace`** (KF-036 item-page block `0x558C8…0x55C68`;
KF-042/Build 0158 `0x10C016`), never as a blanket pass. The 7 already-`0xFF`-form WRAM
immediates in the ROM are those KF-036 opcode_replace sites (identical in 0163).

## 3. 0x041F5E destination-mapping split (shipped)
Original arcade `0x041F5E`: `lea 0x11B2(a5),a0; moveq #18; lea 0xD003C0,a1` (record 120)
and `lea 0x0170(a5),a0; moveq #4; lea 0xD002E0,a1` (record 92) → block A copies to
records **120..137**, block B to **92..95**. The translation collapsed both to **0..17 /
18..21**. Refactored `pc090oj_workram_block_sprites` into a parameterized core with two
entry points: `pc090oj_workram_block_sprites_41f5e` (base records 120/92, called by
`genesistan_pc090oj_hook_target_41f5e`) and the original (0/18, still used by
`genesistan_pc090oj_hook_target_45dfa`). The shared helper was **not** globally changed:
arcade `0x045DFA` is a distinct routine (sources A5+0x5C8/0x748/0x8C8, dests records
140/46/96 via `0x3D054`) whose destination is out of proven scope; `0x041DAE` (source
A5+0x508, dest 57/96) has no hook target at all. `pc090oj_object_ram` is 256 records
(0x800 bytes), so records 120..137/92..95 are in range. Coverage grew +0x1C
(`0x1820B8→0x1820D4`), invariant paired-updated in both gate scripts. opcode_replace count
unchanged (137).

The split is correct but **inert at runtime** until the source populates: with the source
empty, records 120..137 receive zeros (verified nonempty=0 at gameplay).

## 4. Runtime result (shipped 0164)
Progression identical to 0163 (writerExec=626, producer growing, represented reaches 6 at
gameplay). Palette lines all populated (L0=15,L1=14,L2=15,L3=15 — 0161/0162 preserved).
Source `0xFF11B2` empty; records 120..137 empty; player/Rastan unchanged. No new fatal
address; boot guard PASS.

## 5. Build 0163 forced-refresh status
Build 0163's forced gameplay tile-DMA requeue gate in `pc090oj_hooks.s` is **retained
unchanged** in Build 0164 (not removed — the file was edited only for the 0x041F5E split).

## 6. Decision + recommendation
Shipping the WRAM rebase enabled would deliver a ROM strictly worse than 0163 (whole game
frozen). The responsible deliverable is the safe subset (split shipped, rebase gated off)
with the full finding disclosed. Rejected regression artifacts preserved under
`dist/rastan-direct/rejected/` (`…_full_systemic_REGRESSION.bin`,
`…_blockA_rebase_REGRESSION.bin`).

Next investigation (separate task): resolve why the pre-spawn transition depends on
reading `0x10D1B2` as ROM — trace readers `0x51E00`/writers `0x5288C`/`0x52A6C` and the
a5-base during the F480–F536 window. Only once the block can be zero-initialised WRAM
without hanging the transition can the player source be populated (then the shipped
0x041F5E split becomes live and records 120..137 receive the player cluster).

## 7. Open/Closed + KF
- OPEN-017: touched; player-source population proven un-fixable by literal rebase
  (regression). No closure.
- KNOWN_FINDINGS: **KF-044 updated** — blanket WRAM-immediate rebase is unsafe; player
  source block `0x10D1B2` has a pre-spawn ROM-alias dependency.
- Architecture: CONFIRMED — no NOPs/RTS, no hardcoded records/codes/SAT, no broad PC090OJ
  rewrite, palette/VINT/vector/SR/VDP-reg ownership untouched; `0x045DFA` caller left
  intact.
