# Build 0256 — PC080SN Tall-Projector Consumer Retirement (Slice 1)

**Agent:** Andy · **Type:** dead-code retirement — implementation spec + STOP (delegation) · **Baseline:** Build 0255.
**STOP status: YES — delegation, not a technical blocker.** The retirement is fully proven safe and ready; the
source-changing production build belongs to Cody per the settled delegation model (Andy = read-only analysis /
planning; production implementation + numbered builds = Cody). No production source, spec, ROM, or counter was
changed by this task.

---

## 1. Baseline (verified)

- Build: **0255** (current). ROM `dist/rastan-direct/rastan_direct_video_test_build_0255.bin`; SHA-256
  `edfd03534b1766309de105a1dad00671d0ac73eb3ca0fa5dfe7cc3859b378673`; size `1592224`; counter `255`. **All match.**
- Build 0255 numbered ROM is preserved (untouched).
- `docs/design/Cody_known_findings_sync_build0255.md`: absent (Codex exhausted) — not a STOP; `KNOWN_FINDINGS.md`
  not edited.
- Next source-changing build would be **Build 0256**.

## 2. Retirement-plan summary (from `Andy_pc090oj_pc080sn_legacy_retirement_plan_build0255.md`)

Slice 1 retires the **dead PC080SN tall-projector consumer interface only**: the two no-op projector stubs, their
`_vblank_service` call sites, the redundant Build 0252 scene gate, and the dead `*_tall_project_base` globals +
boot clears. Producers, tall buffers, dirty flags, native Plane A/B, frontend, and PC090OJ are **out of scope**
(Slice 2 / do-not-touch).

## 3. Files read

`RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `AGENTS_LOG.md` (latest), `KNOWN_FINDINGS.md`,
`OPEN_ISSUES.md`, `CLOSED_ISSUES.md`; Cody reports 0251–0255 + the Build 0255 Andy plan;
`apps/rastan-direct/src/vdp_comm.s`, `boot/boot.s`, `tilemap_hooks.s`, `pc090oj_hooks.s`;
`tools/translation/postpatch_startup_rom.py`, `verify_canonical_rom.py`; `out/symbol.txt`, `address_map.json`,
patch manifest.

## 4. Xref proof — projector stubs (PASS)

`vdp_project_bg_tall_if_dirty` (`out/symbol.txt` → `0x00070148`) and `vdp_project_fg_tall_if_dirty` (`0x0007014A`):

- **Body is a pure no-op stub** (`vdp_comm.s:244–254`): a Build 0253 comment + a single `rts` each. No live
  projector body remains.
- **Only call sites** are `vdp_comm.s:198` and `:200`, both inside `_vblank_service` (non-gameplay branch).
- No other source xref; the `out/symbol.txt` entries are the symbol table itself, not usages; no
  `address_map.json` / patch-manifest dependency on the exported names (they are Genesis-internal helpers, not
  `opcode_replace`/`absolute_long_pointer_tables` targets).
- **Removing the symbols will not break linking** (no external referencer).

## 5. Xref proof — project-base globals (PASS)

`bg_tall_project_base` (`0x00FF404C`), `fg_tall_project_base` (`0x00FF4054`):

- **Storage:** `vdp_comm.s:545` / `:552` (`.word 0`).
- **Only writes:** `boot/boot.s:207` `clr.w bg_tall_project_base`, `:210` `clr.w fg_tall_project_base` (boot
  clears, value 0). Plus `.extern` at `boot.s:11/14` and `.global` at `vdp_comm.s:33/36`.
- **Zero reads** anywhere (the only reader was the projector body removed in Build 0253).
- **Deleting the globals + boot clears + their `.extern`/`.global` is safe** (no reader, no external xref).

## 6. `_vblank_service` before/after — commit-order proof

**Before (current Build 0255):**
```asm
    bsr     vdp_commit_tiles_if_dirty
    cmpi.b  #1, genesistan_current_scene_id
    beq.s   .Lvs_skip_gameplay_tall_projectors
    bsr     vdp_project_bg_tall_if_dirty     ; no-op stub
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_project_fg_tall_if_dirty     ; no-op stub
    bra.s   .Lvs_after_tall_projectors
.Lvs_skip_gameplay_tall_projectors:
    bsr     vdp_commit_bg_strips_if_dirty
.Lvs_after_tall_projectors:
    bsr     vdp_commit_fg_narrow_strips
```
Removing the two no-op `bsr vdp_project_*_tall_if_dirty` makes both branches identical
(`bsr vdp_commit_bg_strips_if_dirty`), so the gate is redundant.

**After (Slice 1):**
```asm
    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_narrow_strips
```
**Surviving commit order preserved:** `vdp_commit_tiles_if_dirty` → `vdp_commit_bg_strips_if_dirty` →
`vdp_commit_fg_narrow_strips`. Neither surviving commit is removed or moved; `vdp_commit_sprites_vram`, palette,
scroll, and the VBlank tail are unchanged.

## 7. Exact source changes (implementation-ready for Cody)

**`apps/rastan-direct/src/vdp_comm.s`:**
- Delete `.global vdp_project_bg_tall_if_dirty`, `.global vdp_project_fg_tall_if_dirty` (lines 10–11).
- Delete `.global bg_tall_project_base`, `.global fg_tall_project_base` (lines 33, 36).
- In `_vblank_service`: delete the `cmpi.b #1,…` gate + the two `bsr vdp_project_*_tall_if_dirty` + the duplicated
  branch, leaving the single unconditional sequence in §6 "After". (Preserve everything else in the routine.)
- Delete the two stub labels + bodies `vdp_project_bg_tall_if_dirty:` / `vdp_project_fg_tall_if_dirty:` (lines
  244–254).
- Delete the storage `bg_tall_project_base: .word 0` (545) and `fg_tall_project_base: .word 0` (552). Keep the
  neighbouring `bg_tall_dirty` / `fg_tall_dirty` / `fg_row_dirty` / `fg_native_gameplay_owner` — **do not touch.**

**`apps/rastan-direct/src/boot/boot.s`:**
- Delete `clr.w bg_tall_project_base` (207), `clr.w fg_tall_project_base` (210).
- Delete the now-unused `.extern bg_tall_project_base` (11), `.extern fg_tall_project_base` (14).
- Touch nothing else in boot.

**`tools/translation/postpatch_startup_rom.py` + `verify_canonical_rom.py`:**
- Update `CANONICAL_TOTAL_GENESIS_BYTES_COVERED` by the **measured** negative byte delta from the release build
  (dead Genesis code: two `rts` stubs + two `bsr` + gate branch instructions; data: 4 bytes of `.word 0`).
- **Do not** change the opcode-replace count unless the measured build truly changes it (Slice 1 removes no
  `opcode_replace` site — expected unchanged; note the current live count is whatever Build 0255 reports, **not**
  the stale `218`/`221` from prior notes — measure it).

## 8. Untouched confirmation (do-not-touch, verified in scope)

Producers (`genesistan_hook_tilemap_bg_fill_tall` / `fg_fill_tall`), tall buffers (`staged_bg/fg_tall_buffer`),
dirty flags (`bg/fg_tall_dirty`), native Plane A/B producers (incl. the FG loop calling `fg_fill_tall` at
`tilemap_hooks.s:1084`), `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_narrow_strips`, `fg_narrow_desc_*`,
frontend C-window/text, all `pc090oj_*` (object_ram, legacy/native emit, `native_sprite_*`, lanes), Build 0254
D00298/D002B0 remaps, Build 0255 demo-input fix, input, palette/CRAM, collision, rope/reset, audio — **none are
in the Slice 1 change set.**

## 9. STOP status + reason

**STOP: YES — delegation, not a technical blocker.** All Phase-1 baseline capture and Phase-2 xref proofs pass;
the retirement is proven safe and the exact edits are specified (§7). The remaining work is **Phase-3 source
edits + Phase-4 numbered production Build 0256 + gate/MAME validation**, which under this project's settled
delegation model is executed by **Cody** (production implementation and builds), not Andy (read-only analysis /
planning / specs). This is the task's own "needs an implementation-capable agent" path — here that agent is Cody.
The build-time items (measured canonical byte delta, live opcode-replace count, ROM SHA/size, GATE_PASS, MAME
smoke) can only be produced by the release build and are therefore reported by the implementing build, not here.

**No blocking issue found:** no projector-stub is non-no-op; no project-base reader exists; no external xref
requires the symbols; the commit order is preservable. If Cody's build surfaces any of the Phase-2 STOP
conditions (a reader appears, linking breaks, commit order would change, coverage cannot reconcile to a pure
dead-code delta, or opcode count shifts unexpectedly), that is a real STOP for the implementing agent.

## 10. Issues / findings impact

- **Open issues:** OPEN-017 / OPEN-024-adjacent native rendering cleanup context; none opened or closed.
- **KNOWN_FINDINGS:** Option A — no new finding; not edited this task (Build 0255 sync still pending).
- **Andy follow-up recommended after implementation:** YES — a brief Andy review of the built Build 0256 to
  confirm the measured byte delta is pure dead-code/data and to green-light Slice 2 (tall-buffer + producer
  retirement, which needs the native-FG-producer audit).
