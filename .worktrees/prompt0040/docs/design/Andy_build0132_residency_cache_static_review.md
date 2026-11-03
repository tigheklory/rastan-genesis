# Andy — Build 0132 PC090OJ Residency Cache Static Review (Independent Review Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** Build 0132, `dist/rastan-direct/rastan_direct_video_test_build_0132.bin`, SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`.
**Primary Cody report:** `docs/design/Cody_pc090oj_persistent_sprite_tile_dma_cache_build0132.md`.
**Scope:** Independent STATIC review of the implementation logic only. No implementation/edit/build/runtime trace. Labels **[OBS]** verified from Build 0132 source this task; **[INT]** interpretation.

> **BOTTOM LINE:** All three logic paths are **CORRECT**. Cody's suspicious emit-side snippet is **misleading, not a bug**: it omitted the 2-byte `bra.s .Lpc090oj_store_flags` that sits at `0x00071​8B6` — proven both by the source (pc090oj_hooks.s:159-164) and by the address arithmetic (a 4-byte `move.w #0x8005,%d5` at `0x718B2` ends at `0x718B5`, so `0x718B8` cannot be the next instruction; a 2-byte instruction occupies `0x718B6`). The DMA-side update writes the correct slot's cache only after the DMA command and only inside the changed-gate, and the boot clear zeroes exactly 80 words in a non-overlapping location. **Verdict: cache implementation correct → Branch A (HV/VCounter display-on diagnostic).**

---

## == PHASE 0 ==

- **Relevant priors:** Andy residency-cache design (per-SAT-slot, sentinel 0x0000); Andy PC080SN/PC090OJ VRAM ownership design (1024..1343 reserved; endround relocated to 1344..1406); Andy Build 0130 timing analysis (late-DISPLAY_ON SUPPORTED; churn CONFIRMED); Cody Build 0132 implementation; Exodus Build 132 layer-separated observation (planes/sprites complete, composite shows a moving bottom band).
- **High-rediscovery hazards:** generated-disassembly excerpts can silently drop instructions — the changed-bit "bug" is exactly such an omission; must be checked against source + byte addresses, not the excerpt alone. KF-021 (staged SAT ≠ truth) unaffected.
- **Task classification:** Independent static verification of an OPEN-024 implementation slice.
- **Contradiction detected:** NO — the apparent contradiction (snippet says changed-bit overwritten; runtime shows 44 DMA updates) is resolved: the snippet is incomplete; the source is correct.
- **Build 0132 baseline:** SHA `989b17e8…b611832` (matches task).
- **Cody cache summary:** `sprite_tile_resident_code[80]` @ WRAM 0xFF674A; boot clears 80 words; emit_slot compares `(d3&0x0FFF)` vs cache and sets bit 0x0004 on miss (no cache write); tile_dma writes cache after DMA then clears bit 0x0004; runtime 80 boot + 44 post-DMA writes (frames 33/43) then 0 (frames 44–1800) with active/drawable/emitted=0x20.
- **address_map.json loaded:** YES (all addresses Genesis-native runtime_genesis_pc; no arcade correlation used).
- **arithmetic offset used as proof:** NO (byte-length arithmetic within a single Genesis routine is used to expose the omitted instruction — not an arcade↔genesis offset claim).

---

## == Q1 STATIC CHANGED-BIT LOGIC ==

**source sequence** [OBS pc090oj_hooks.s:149-164]:
```
    move.w  %d3, %d6
    andi.w  #0x0FFF, %d6                 ; d6 = masked emitted code
    move.w  %d0, %d5
    add.w   %d5, %d5                      ; d5 = slot*2
    move.l  %a2, -(%sp)
    lea     sprite_tile_resident_code, %a2
    move.w  0(%a2,%d5.w), %d5             ; d5 = resident[slot]
    move.l  (%sp)+, %a2
    cmp.w   %d6, %d5
    beq.s   .Lpc090oj_no_tile_change      ; HIT
    move.w  #0x8005, %d5                  ; MISS: valid+touched+changed(0x0004)
    bra.s   .Lpc090oj_store_flags         ; <-- the instruction Cody's snippet omitted
.Lpc090oj_no_tile_change:
    move.w  #0x8001, %d5                  ; HIT: valid+touched
.Lpc090oj_store_flags:
    move.w  %d5, (%a0)                    ; store descriptor word0
```

**disassembly sequence** [OBS Cody report + address arithmetic]:
```
0x718AE: cmp.w %d6,%d5
0x718B0: beq 0x718B8                      ; HIT → 0x718B8
0x718B2: move.w #0x8005,%d5               ; 4 bytes → ends 0x718B5, next = 0x718B6
0x718B6: bra.s 0x718BC                    ; *** 2-byte instr OMITTED from Cody's excerpt ***
0x718B8: move.w #0x8001,%d5               ; HIT body
0x718BC: move.w %d5,(%a0)                 ; store
```
The excerpt jumps from `0x718B2` straight to `0x718B8`, but a 4-byte `move.w #imm,%d5` at `0x718B2` occupies `0x718B2..0x718B5`; the next instruction is at `0x718B6`, not `0x718B8`. The 2-byte hole at `0x718B6` is the `bra.s .Lpc090oj_store_flags` (target `0x718BC`).

- **cache-hit word0:** `0x8001` (valid bit0 + touched bit15; changed bit2 clear) → `.Lvcs_tile_dma` skips DMA.
- **cache-miss word0:** `0x8005` (valid + touched + **changed 0x0004**) → `.Lvcs_tile_dma` issues DMA.
- **changed-bit preserved (miss):** **YES** — the `bra.s` skips the `0x8001` body; `0x8005` reaches the store intact.
- **Q1.4 snippet accurate:** NO — it dropped the 2-byte `bra.s` at `0x718B6`.
- **Q1.5 real bug:** NO.
- **Q1.6 actual flow:** `beq` → hit → `0x8001`; miss → `0x8005` → `bra.s` → store (skipping the hit body). Both paths converge at `.Lpc090oj_store_flags`.
- **Q1.7 runtime needed:** NO — statically proven.

**classification: changed-bit logic correct.**

---

## == Q2 DMA-SIDE CACHE UPDATE ==

[OBS pc090oj_hooks.s:1130-1217]

- **DMA gate:** `btst #0` (valid) then `btst #2` (tile-code-changed) at 1142-1145; both must be set or `beq .Lvcs_tile_next` skips the whole body.
- **cache update timing:** the cache write (1204-1207) is **after** the DMA trigger `move.l %d1,(%a3)` (1202) and inside the gated body → updated only after a DMA is actually issued.
- **cache slot index:** `d0 = d7*2` (1204-1205, d7 = slot), `move.w %d6, 0(%a1,%d0.w)` (1207); the DMA dest uses the same `d7` (`(SPRITE_TILE_BASE+slot*4)*32`, 1185-1189) → correct slot's entry.
- **code mask consistency:** compare uses `(d3 & 0x0FFF)` (149-150); tile_dma reads `8(a0) & 0x0FFF` → `d6` (1147-1149) and writes `d6` to the cache (1207). Descriptor offset 8 = `d3` (written at emit_slot:131). Same 12-bit masked code both sides. Consistent.
- **changed-bit clear:** `andi.w #0xFFFB, (%a0)` (1210) **after** the cache write (1207). Correct order: DMA cmd → cache write → clear changed bit.
- **Q2.5 cache updated without DMA:** NO static path — 1207 is only reachable after 1202.
- **Q2.6 DMA without cache update:** NO static path — execution falls straight through 1202 → 1207 with no intervening branch.

**classification: DMA-side cache update correct.**

---

## == Q3 BOOT / INIT ==

[OBS boot/boot.s:178,185,236-240; pc090oj_hooks.s:1385-1397; Cody symbol.txt]

- **clear location:** inside `_bootstrap_clear_staging` (called from boot at boot.s:178), between the `staged_sprite_active_count` clear (234) and the `pc090oj_object_ram` clear (242) — matching the BSS declaration order. Runs once at boot before the first frame (runtime frame-0 confirmation: 80 writes at pc 0x304).
- **clear count:** `move.w #(80-1),%d7 … clr.w (%a0)+ … dbra` = **exactly 80 words (160 bytes)**.
- **cache address:** `sprite_tile_resident_code = 0xFF674A`; 80 words span `0xFF674A..0xFF67E9`.
- **neighbor layout:** `staged_sprite_active_count = 0xFF6748` (word, ends 0xFF6749) immediately precedes the cache; `pc090oj_object_ram = 0xFF67EA` immediately follows (`0xFF674A + 0xA0 = 0xFF67EA`). No overlap on either side; the clear touches neither neighbor (object_ram is zeroed separately at 242-246). BSS order (`…active_count, sprite_tile_resident_code, pc090oj_object_ram…`) matches the symbol addresses.
- **Q3 reported layout safe:** YES — `0xFF674A + 160 = 0xFF67EA` is exactly the object_ram base, so the cache abuts it with zero gap and zero overlap.

**classification: cache init correct.**

---

## == Q4 NEXT BRANCH ==

**selected branch:** **Branch A** — static review says the cache implementation is correct; next task is a Cody HV/VCounter display-on diagnostic for Build 0132.

**why:** Q1/Q2/Q3 all pass on source inspection; the "changed-bit bug" was a disassembly-excerpt omission. The runtime evidence is consistent with correct behavior — cache warms (80 boot + 44 post-DMA writes across frames 33/43) then suppresses all further redundant tile DMA (0 writes, frames 44–1800) while 32 sprites stay emitted. The churn is fixed. The **residual moving band** (Exodus Build 132: planes/sprites complete, composite shows a bottom band) is the still-open **late-DISPLAY_ON** mechanism from the Build 0130 Q1 analysis — reduced by the smaller commit window but not eliminated. Quantifying exactly which scanline DISPLAY_ON now lands on requires the HV/VCounter field that Build 0129 deliberately omitted. No cache fix is needed; no inconclusive-trace is needed for the cache itself.

**next Cody prompt (copy-ready):**

---
**Cody — Build 0132 HV/VCounter Display-On Timing Diagnostic (temporary, revert-verified)**

**Type:** Temporary diagnostic build + runtime evidence + mandatory revert to byte-identical. No production logic change.
**Baseline:** Build 0132, SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`.
**Goal:** Measure, in scanlines, how late `_vblank_service` restores DISPLAY_ON relative to VBlank end — the residual "moving band" after the residency-cache fix. Andy's Build 0130 analysis found DISPLAY_ON (checkpoint 0x0B) landing after VBlank bit-3 clears in 15/17 frames but could not quantify lateness because the Build 0129 ring did not sample the HV counter.

**Instrumentation (temporary, every block labeled `TEMP DIAGNOSTIC ONLY - REMOVE BEFORE NEXT CANONICAL BUILD`):**
- Re-add the Build 0129-style VBlank status ring in `apps/rastan-direct/src/vdp_comm.s` with the same 12 checkpoints (0x01..0x0C).
- **Add one field: the VCounter**, read from `HW 0x00C00008` (the HV counter; V is the high byte of the word read), sampled at checkpoints **0x03 (after DISPLAY_OFF), 0x0A (after scroll), and 0x0B (after DISPLAY_ON)**. Store VCounter alongside the existing per-entry data (extend the ring entry; keep the ring in the same Genesis-WRAM diagnostic region).
- Do NOT change any PC090OJ/PC080SN/residency-cache/display logic. Read 0x00C00008 only; do not add other HW reads.
- Update only the diagnostic invariant (`total_genesis_bytes_covered`) in the two canonical tools for the diagnostic build, exactly as in Build 0129; keep `opcode_replace` count unchanged.

**Runs:** no-input and coin/start, same anchors/labels as Build 0129 (title, black-cover/story anchor, coin-accept, ROUND). Capture the ring + screenshots.

**Report (`docs/design/Cody_build0133_hv_vcounter_display_on_diagnostic.md`):** per sampled frame, VCounter at 0x03 / 0x0A / 0x0B and VDP status bit3 at each; classify DISPLAY_ON as inside-VBlank vs N scanlines into active display (`N = VCounter(0x0B) − active_display_start`); compare against Build 0130's pre-cache 15/17-after-VBlank baseline to show whether the residency cache pulled 0x0B earlier; note the min/typical/max lateness and whether any single commit stage (BG/FG strips, mirror scan) dominates the residual. Include the residency-cache counters (emitted, cache writes) to confirm 0 steady-state tile DMA during the measured frames.

**Mandatory revert:** remove all temporary code/data/symbols/comments and the diagnostic invariant; produce a revert build; prove it byte-identical to Build 0132 (`cmp -s` = 0; SHA `989b17e8…b611832`); preserve all three ROMs (0132 baseline, 0133 diagnostic, 0134 revert) with sequential names.

**STOP if:** reading `0x00C00008` triggers a strict-port/HV fault on BlastEm/Nomad (fall back to Exodus-only capture and report the limitation); or the revert is not byte-identical.

**Open/Closed Issues Impact:** OPEN-001 (title display timing — quantify residual), OPEN-024 (sprite subsystem context); none closed; temporary diagnostic, no KNOWN_FINDINGS change unless a durable timing root cause is established.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-024 (residency-cache logic verified correct — churn fix stands; not closed), OPEN-001 (residual moving band re-attributed to late-DISPLAY_ON; not closed).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend, when convenient, a KNOWN_FINDINGS note that generated-disassembly excerpts in reports must include branch instructions or be cross-checked against source + byte addresses — this excerpt's dropped `bra.s` nearly read as a bug).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** HV/VCounter lateness quantification (Branch A diagnostic); `.Lpc090oj_emit_slot` producer/render split (OPEN-024 structural debt); any DISPLAY_ON-timing fix (awaits the diagnostic magnitude).

AGENTS_LOG updated: YES
STOP status: NO — static review complete; cache implementation verified correct (Q1/Q2/Q3 all correct); next step is the Branch-A HV/VCounter diagnostic (Cody), not a code fix.
