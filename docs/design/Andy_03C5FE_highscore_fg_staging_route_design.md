# Andy — Route the 0x03C5FE High-Score FG Producer Loop Through FG Staging (Design Only)

**Author:** Andy
**Date:** 2026-06-28
**Baseline:** Build 0109 (`dist/rastan-direct/rastan_direct_video_test_build_0109.bin`, SHA256 `a9905cd73837099f6ed548dda5b4ff66a1bb6be0911730e1bf9204472e934bc9`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation. Static from existing evidence. Output: this doc + one AGENTS_LOG entry. Address-PC correlation via `address_map.json` (no ±0x200 as authority). Labels: **[OBS]** verified this task; **[CODY]** Cody binding scope; **[INT]** interpretation.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (KF-032 raw-PC080SN-write class; high-score producer). **Contradiction:** NONE. **Root + scope (Cody, re-verified statically):** the high-score FG producer at `runtime_genesis_pc 0x03C5FE` (`arcade_pc 0x03C3FE`) emits attr/code cell pairs via **raw PC080SN FG writes** (VDP-mirror HW space) that freeze BlastEm/real Genesis. Three raw writers in the loop; spans `HW_ADDRESS 0x00C09374..0x00C09B7E` (all FG C-window). One caller: `runtime_genesis_pc 0x03B900 bsr.w 0x03C5FE`, reached 5× (once per row, `d0`=descriptor index). **Out of scope (do not fix):** the zero/blank table (separate upstream source-data issue), sprites/window/HUD, the already-routed neighbors `0x03C4E2` (number renderer) / `0x03BD48` (glyph renderer), the 0x03AD06 fall-through fix.

**JSON mapping (exact)** [OBS]: producer `0x03C5FE`=`arc 0x03C3FE`; stores `0x03C62A`=`arc 0x03C42A`, `0x03C646`=`arc 0x03C446`, `0x03C64A`=`arc 0x03C44A`; descriptor table `0x03C654`=`arc 0x03C454`; all `arcade_copy`.

---

## 1. The producer, decoded [OBS]

```
3C5FE move.w #0,d7              ; attr value = 0 (intentional)
3C602 move.w d0,d2             ; d2 = mode (sign → space-mode)
3C604 andi.w #127,d0           ; d0 = descriptor index & 0x7F
3C608 mulu.w #6,d0             ; ×6 (6-byte descriptors)
3C60C lea (pc,0x3C654),a0      ; descriptor table base
3C610 adda.w d0,a0             ; &descriptor[index]
3C612 move.w (a0),d0           ; d0 = count (cells)
3C614 movea.w 2(a0),a1 ; 3C618 adda.l #0x00C08000,a1   ; a1 = FG dest = 0xC08000 + dest-offset
3C61E movea.w 4(a0),a2 ; 3C622 adda.l #0x0010C000,a2   ; a2 = source = 0x0010C000 + src-offset
3C628 clr.w d1                 ; (loop top)
3C62A move.w d7,(a1)+          ; *** RAW STORE 1: ATTR word (d7=0), a1+=2
3C62C move.b (a2)+,d1          ; d1 = source byte
3C62E cmpi.b #0x3F,d1 ; bne ; move.w #0x274B,d1   ; '?' → 0x274B
3C638 cmpi.b #0x21,d1 ; bne ; move.w #0x2744,d1   ; '!' → 0x2744
3C642 tst.b d2 ; bmi 3C64A     ; mode negative → space
3C646 move.w d1,(a1)+          ; *** RAW STORE 2: CODE word, a1+=2
3C648 bra 3C64E
3C64A move.w #0x0020,(a1)+     ; *** RAW STORE 3: SPACE code 0x0020, a1+=2
3C64E subq.w #1,d0 ; bne 3C628 ; loop count cells
3C652 rts
3C654 descriptor table: [count.w][dest.w][src.w] × N  (e.g. 0003 1374 0157 | 0003 1574 015A | …)
```
**Per cell = 2 PC080SN words** (attr at even addr, code at +2); a1 advances 4 bytes/cell. Each call processes one descriptor (count cells; observed count=3). [OBS]

---

## 2. Recommended approach — **FUNCTION-LEVEL replacement (approach 2)**; route-3-stores (approach 1) is INFEASIBLE

**Route-3-stores in-place (approach 1) — REJECTED for two independent reasons** [OBS+INT]:
1. **Byte budget:** the attr store `0x03C62A` (`32c7`) and code store `0x03C646` (`32c1`) are **2 bytes each**. No call fits in 2 bytes (`bsr.w`=4, `jsr abs.l`=6). Only the 4-byte space store `0x03C64A` (`32fc 0020`) could hold a `bsr.w`, but genesis_only helpers are >32 KB away (out of `bsr.w` range), and routing 1 of 3 leaves the other two raw → still freezes.
2. **Compose-model mismatch:** Genesis FG staging is **per-cell composed** (one `staged_fg_buffer` word = `tile_vram_lut[code] | attr_lut[attr]`), not separate raw attr/code words. The producer writes attr and code as **two separate PC080SN words**; a per-raw-word route can't produce the composed cell the commit expects. Routing must happen at **cell granularity**, not per raw word.

**Function-level replacement (approach 2) — RECOMMENDED** [INT]: patch the producer **entry** at `0x03C5FE` to `jsr genesistan_hook_highscore_fg_producer` + `rts` (8 bytes), and let a genesis_only hook faithfully reimplement the producer, staging each cell via the existing `genesistan_hook_tilemap_fg_fill`. This eliminates all three raw writers (no in-place per-store patch), routes at cell granularity (matching the staging model), and preserves every producer detail in the hook. The single caller `0x03B900` is unaffected (it still `bsr`s `0x03C5FE`, which now jsr's the hook and rts's).

*(Considered and rejected — scratch-redirect: patch `0x03C618 adda.l #0x00C08000,a1` to a WRAM scratch base so the raw stores hit safe scratch, then a post-pass composes scratch→staging. Rejected: needs a ~0x1C00-byte scratch, a separate post-pass helper, dest-offset tracking, and a post-pass invocation point — more complex and fragile than the clean reimplementation, for no intent-fidelity gain.)*

---

## 3. Raw writers routed (all subsumed by the function-level hook)

| Raw writer | Route |
|---|---|
| `0x03C62A` attr (`move.w d7,(a1)+`) | **Eliminated.** The hook folds attr (`d7=0`) into the per-cell `fg_fill` call as `D0` high word; no raw attr write. |
| `0x03C646` code (`move.w d1,(a1)+`) | **Eliminated.** The hook passes the post-substitution code (`d1`) as `fg_fill` `D0` low word; no raw code write. |
| `0x03C64A` space-mode (`move.w #0x0020,(a1)+`) | **Eliminated and handled** even though not hit this pass: the hook's space branch sets code `0x0020` and stages via `fg_fill`; no raw write. |

---

## 4. %a1 → staging-offset translation

- **Existing staging store accepts an FG C-window HW address? YES** [OBS]. `genesistan_hook_tilemap_fg_fill` (`runtime_genesis_pc 0x0007065E`) takes `A0` = FG HW address and internally computes the staged offset.
- **Formula (HW FG addr → staged_fg_buffer offset)** [OBS]: `cell = ((A0 & 0x00FFFFFF) − 0x00C08000) >> 2`; `col = cell & 0x3F`; `row = (cell >> 6) & 0x1F`; `staged-WRAM-offset = staged_fg_buffer(0x00FF501A) + row*128 + col*2`. (`>>2` truncates the +2 of the code word, so attr-addr and code-addr resolve to the same cell.)
- **Wrapper needed? NO separate translator** — `fg_fill` is the translator. The hook calls `fg_fill(A0 = a1, D0 = (attr<<16)|code, D1 = 1)` per cell, then advances its own `a1` by 4 (preserving the producer's 4-bytes-per-cell stepping). `fg_fill` does not modify the caller's `a1` (movem-preserves a0-a6).
- **attr/code pairing preserved in staging** [OBS+INT]: instead of two raw words, the hook composes one cell per `fg_fill` call (`D0` high word = attr `d7`, low word = code `d1`). `fg_fill` composes `tile_vram_lut[code & 0x3FFF] | attr_lut[attr-bits]` and writes one `staged_fg_buffer` cell at the correct row/col. Attr `0x0000` → `attr_lut[0] = 0x0000` (palette line 0) → composed cell = bare slot (matches the producer's attr-0 intent).
- **Dirty/commit ensured** [OBS]: `fg_fill` sets `bset #row, fg_row_dirty` per staged cell; the VBlank FG commit reads `staged_fg_buffer` for dirty rows → the cells actually commit.

---

## 5. Producer intent preserved (in the hook)

The hook reimplements the producer 1:1 (read `d0` input):
- **Descriptor table `0x03C654`** [OBS]: `d0 &= 0x7F; d0 *= 6; a0 = 0x0003C654 + d0; count = (a0).w; dest = 2(a0).w; src = 4(a0).w`.
- **FG destination:** `a1 = 0x00C08000 + dest`.
- **Source walk `0x0010C157+`** [OBS]: `a2 = 0x0010C000 + src`; `code-byte = (a2)+`. **Read from the exact same address the arcade producer reads** (write-path-only change; the zero-table source question is separate/out of scope).
- **`!`/`?` substitutions** [OBS]: `if byte==0x3F → code=0x274B`; `if byte==0x21 → code=0x2744`; else `code = byte`.
- **Space-mode branch** [OBS]: `mode = d2` (from the input `d0` before masking); `if d2 < 0 → code = 0x0020`.
- **attr/code pairing + loop/return** [OBS]: `attr = d7 = 0`; per cell `fg_fill(A0=a1, D0=(0<<16)|code, D1=1)`; `a1 += 4`; `count -= 1; loop`; `rts`.

Loop-state registers (count, `a1` dest, `a2` source, mode) must be held in registers **outside** the `fg_fill` argument set or relied upon via fg_fill's full-register preservation — see §6.

---

## 6. Register / flag / byte mechanics

- **`fg_fill` preservation** [OBS]: `genesistan_hook_tilemap_fg_fill` does `movem.l %d0-%d7/%a0-%a6` save/restore — it preserves **every** register for its caller, restoring each to its value at the `fg_fill` call. It uses `a4/a2/a3/a6` and d-regs internally; it does **not** read the caller's `a1`.
- **Registers the hook must preserve across each `fg_fill` call** [INT]: the hook keeps loop state (count, dest `a1`, source `a2`, mode) in registers and sets only `A0/D0/D1` as `fg_fill` args. Because `fg_fill` restores all registers to their pre-call values, the hook must keep the loop count in a register it does **not** repurpose as an `fg_fill` arg (e.g. keep count in `d3`, not `d0`, since the hook sets `d0`=composed code for the call). `a1`/`a2` survive (fg_fill preserves a1/a2; fg_fill doesn't touch a1, and restores a2). The hook then advances `a1 += 4` after the call.
- **Caller dependency** [OBS]: the original producer clobbers `d0/d1/d2/d7/a0/a1/a2` (it returns only via `rts`); the caller `0x03B900` re-establishes `d0` each of the 5 calls and relies on no producer-output register. The hook may clobber the same set; it should `movem`-save/restore conservatively and leave the caller's outer-loop register intact (the caller does not depend on `d0` surviving — it re-sets the descriptor index each call). **Flags:** the producer returns via `rts`; the caller does not consume producer-set CCR. No flag dependency.
- **Per-site patch shape + byte budget** [OBS+INT]: **one** patch — the producer entry. Original first 8 bytes at `0x03C5FE` = `3E3C 0000 3400 0240` (`move.w #0,d7` + `move.w d0,d2` + first 2 bytes of `andi.w #127,d0`). Designed 8 bytes = `4EB9 <hook-addr.L> 4E75` (`jsr genesistan_hook_highscore_fg_producer` + `rts`). The hook redoes `d2=d0; d0&=0x7F; …` internally, so overwriting these entry ops is safe. The remaining producer body (`0x03C606..0x03C652`) becomes **dead code** (never executed; harmless); the descriptor table at `0x03C654` stays and is read by the hook. **No trampoline needed** (the entry patch is the single redirect; the 2-byte-store byte problem is sidestepped entirely by not patching the stores).
- **Invariant impact** [INT]: `opcode_replace` **+1** (new patched_site at `0x03C5FE` / `arc 0x03C3FE`); `total_genesis_bytes_covered` **+ hook size** (genesis_only growth, est. ~70–100 bytes for the reimplemented loop; relocation is genesis_only-internal, arcade space unchanged except the 8-byte entry which is byte-neutral 8→8). Pre-authorize: site byte-neutral; +1 opcode_replace; genesis_only grows by exactly the hook. Any other delta = STOP.

---

## 7. Why this matches arcade intent (not literal opcodes)

The producer's **intent** is to emit the high-score table's attr/code cells onto the PC080SN FG plane. The arcade does it with raw PC080SN word writes to FG RAM — correct on arcade hardware, but on Genesis those addresses are VDP-mirror space (raw writes freeze strict targets; cf. KF-032). The hook reproduces the **intent** — same descriptor decode, same source walk, same `!`/`?` substitutions, same space-mode, same cells, same attr-0 — but delivers them through the **Genesis FG staging path** (`fg_fill` → `staged_fg_buffer` → `fg_row_dirty` → VBlank commit), exactly as the comma/sibling Class A fixes did. Reproduce intent, not opcodes. The table **content** is unchanged (the hook reads the same source bytes); only the **write path** changes — so the separate zero-table data issue is neither fixed nor worsened. [INT]

---

## 8. Validation plan for Cody (after implementation)

- Build ROM; canonical gate passes; new build/SHA.
- **Byte-neutral entry confirmed:** only `0x03C5FE` 8-byte entry changed to `jsr hook + rts`; `opcode_replace` +1; `total_genesis_bytes_covered` grows by exactly the hook; arcade space otherwise unchanged. Any other delta = STOP.
- No-input attract reaches the high-score screen; **BlastEm/strict target does NOT freeze** — **zero raw writes to `0x00C08000..0x00C0BFFF` from this producer** (watchpoint the FG C-window range; expect no producer HW writes).
- All 30 FG cells this pass (5 rows × 3 cells × attr+code → 15 composed staged cells) route through `fg_fill` and **commit at VBlank**; the high-score table renders the **same visible cells as Build 0109 (MAME/Exodus)**, now via staging.
- **Space-mode (`0x03C64A`) and `!`/`?` substitutions:** if exercised by data, also staged (no raw write). If not exercisable in no-input attract, flag for later (the hook handles them structurally regardless).
- **No regression:** title, TAITO, story, parens (Class B), OPEN-018 comma/siblings, the already-routed `0x03C4E2`/`0x03BD48` neighbors, and the `0x03AD06` fall-through fix.
- **Zero/blank table content UNCHANGED** by this fix (separate issue) — confirm the routing changes only the write path, not the source-read or the values composed (same `tile_vram_lut`/`attr_lut` outputs as a raw cell would have produced).

---

## 9. Risks / STOP

| Risk | Mitigation |
|---|---|
| Reimplementation drops a producer detail (substitution / space-mode / descriptor / source) | §5 specifies the 1:1 logic; validation checks the rendered cells match Build 0109 and that space-mode/substitution paths exist. |
| Loop count clobbered by `fg_fill` arg setup | §6: keep count in a non-arg register (e.g. `d3`); `fg_fill` preserves it. |
| `a1` stepping wrong | Hook advances `a1 += 4` per cell (attr+code), matching the producer; `fg_fill` derives row/col from `a1`. |
| Source read changed (would alter table) | Hook reads `0x0010C000 + src` byte-for-byte as the arcade producer; write-path-only change; zero-table untouched. |
| Dead producer body / dangling bytes after entry patch | Body `0x03C606..0x03C652` is unreachable (entry rts's); harmless; descriptor table `0x03C654` preserved and read by the hook. |
| Strict-target still freezes from another high-score raw writer | Cody's scope says this producer is the surface; validation watchpoints the whole FG C-window — if another raw writer appears, it's a separate KF-032 site (capture + new follow-up). |

## Open / Closed Issues Impact

- Open issues touched: KF-032 class (high-score FG producer raw writes — design to route; not closed pending implementation), OPEN-001 (context — high-score visual completeness). OPEN-018 (sibling raw-write arc; this is the same class, distinct site). OPEN-015 not touched.
- New issues opened: NONE (recommend tracking the high-score producer routing under the KF-032 / OPEN-018 raw-write umbrella or a dedicated id if Tighe prefers).
- Issues closed: NONE.
- Intentionally deferred: implementation; the zero/blank high-score table source-data issue (separate); any additional raw writers outside this producer.

## STOP triggered

NO (the design routes ALL three raw writers while preserving the producer's full intent, within byte/register constraints).
