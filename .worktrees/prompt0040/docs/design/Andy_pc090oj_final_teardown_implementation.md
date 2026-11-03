# Andy — Final PC090OJ Compatibility Teardown (UNNUMBERED implementation)

**Task type:** Implementation / verification. **UNNUMBERED only — Build 0297 NOT produced, number NOT consumed.**
**Baseline:** Build 0296. **Contract:** `docs/design/Andy_pc090oj_final_retirement_census.md` (Answer A: the
PC090OJ object-RAM path is dead output; remaining live PC090OJ producers: NONE).
**Unnumbered artifact:** `build/rastan-direct/UNNUMBERED_teardown.bin`, size **1,597,112** (unchanged),
boot-guard PASS, postpatch PASS.

---

## 1. Phase 0 statement

- **Relevant priors:** KF-025 (raw D-range writes render blank / can fault on Genesis), KF-026 (PC090OJ write
  surface not fully static → runtime backstop used), KF-011 (arcade Level-5 VBlank owns frame progression —
  unchanged), OPEN-024 (gameplay native; remaining debt frontend/shared), CLOSED-019.
- **Rediscovery-Hazard HIGH acknowledged:** KF-011, KF-025, KF-026.
- **Task classification:** EXTENDING (final teardown of proven-dead infrastructure).
- **Open/Closed issues touched:** OPEN-024 (advanced; NOT closed — closure waits for the numbered Build 0297
  release/regression gate).
- **CONFIRMED/STRONG contradiction:** NONE.

## 2. Prompt-1 census used as prior

The census proved every former PC090OJ producer is native/`rts`/deleted, no reachable writer stores a nonzero
code into `pc090oj_object_ram`, and the frontend scan/decoder emit zero object-RAM sprites (runtime backstop
`GLOBAL_MAX_DRAWABLE_CANDIDATE_CODES=0` over 14,382 frames incl. 2,207 scan-path + 2,002 item-page frames).
This task removes the empty shell.

## 3. Exact source changes (`apps/rastan-direct/src/pc090oj_hooks.s`, `boot/boot.s`)

**Phase 1 — native-only frontend route.** `pc090oj_native_emit_pass` retargets both former
`.Lnq_frontend_object_scan` branches (scene 0 stage≠0, and scene 2) to a new `.Lnq_frontend_native`, which
mirrors `.Lnq_title`'s SAT/residency/cell-used setup, calls `native_frontend_hud_emit` + `.Lnq_transient_items_emit`,
then hands off to the shared finalizer `.Lnq_done_scan`. This reproduces exactly what the old scan did for
frontend scenes *before* its (dead) object-RAM loop.

**Phase 2 — deletions:**
- `.Lnq_frontend_object_scan` entire body incl. the 256-record object-RAM loop and its residency helpers
  (`.Lnep_*`).
- `.Lpc090oj_decode_record` (virtual-record decode/clip/flip/colbank).
- `.Lpc090oj_emit_slot`, `.Lpc090oj_clear_slot`, `.Lpc090oj_mirror_write_word_a1_d0`,
  `.Lpc090oj_mirror_write_byte_a1_d0`.
- `.Lpc090oj_mode2_project_p1_hud` (unreachable gameplay object-RAM HUD projection).
- `genesistan_pc090oj_hook_target_3b930` retired to bare `rts` (uncalled copier; removed its `mirror_write`
  calls and the `jsr (0x0005B712).l` maincpu ref).
- BSS: `pc090oj_object_ram` (256×8) and the dead scan diagnostics `pc090oj_mirror_dirty`,
  `candidate/decoded/code_zero_skipped/blank_skipped/unmapped_skipped/offscreen_skipped/hud_suppressed/
  drawable/represented_count`, `scan_colbank`, `scan_active`, `producer_write_count`, `producer_oob_count`,
  `bootstrap_pending`, `.Lscratch_rec`, `.Lrecord46_*`, and their `.global` decls.
- Dead exported-alias stubs `staged_sprite_descriptor_table`, `pc090oj_candidate_bitset`, `record_to_slot`,
  `represented_records`, `waiting_records`, `used_sat_slots`, `staged_sprite_dirty`, `staged_sprite_active_count`
  (0 functional consumers) + their `.global`/boot `.extern` decls.
- `boot/boot.s`: removed the object-RAM boot clear loop and the dead-diagnostic clears (kept `pc090oj_ctrl_shadow`,
  `pc090oj_sprite_ctrl_shadow`, `pc090oj_emitted_count`, `pc090oj_dropped_count`).

**Phase 3 — 0x03AD44 D-range.** In `genesistan_hook_3ad44_dispatch`, the PC090OJ D-range branch
(`0x00D00000..0x00D00800`) now does `bra .Lhook_3ad44_finish` (bounded no-op return) instead of the object-RAM
long-fill. Confirmed in the final disasm at runtime `0x072b9c`: D-range → `bra 0x72c34` (finish); the C-range
PC080SN branches (0xC04000/0xC08000/0xC0C000 → `genesistan_hook_tilemap_*`/`pc080sn_*_scroll_fill`) are
**byte-for-byte unchanged**.

**Phase 4 — object-RAM init/clear.** No separate edit needed: the arcade clear routines (`0x03AF4C`/`0x03AF72`
→ thunk `0x03AF44` → `genesistan_hook_3ad44_dispatch`) now hit the D-range no-op. The native group builder
(`0x72978`/`0x728A0`, writing native buffers `0xFF68CA..0xFF6C82`; its `lea 0xd0xxxx` A1 loads are vestigial,
overwritten before store) is **separate and untouched** — reconfirmed.

## 4. Exact remap changes (`specs/rastan_direct_remap.json`)

- Removed the two dead GAME OVER object-RAM destination redirects (`0x05A51E` → `pc090oj_object_ram+0x298`,
  `0x05A554` → `+0x2B0`). `0x05A502` is already `clr.l d0; rts` (Build 0288), so its body is unreachable; the
  original `movea.l #0xD00298/#0xD002B0` literals remain in that dead body (category B, see §11) — no raw
  D-range write executes.
- `required_symbols`: removed `pc090oj_object_ram`, `staged_sprite_descriptor_table`, `staged_sprite_dirty`,
  `staged_sprite_active_count` (deleted symbols).
- `expectations.opcode_replace_count` 228 → **226** (−2 removed byte-neutral entries).
- `expectations.genesis_only_maincpu_ref_count` 8 → **7** (removed `3b930`'s `jsr 0x5B712`).
- Tool constants: `CANONICAL_OPCODE_REPLACE_COUNT` 228 → 226 in `postpatch_startup_rom.py` and
  `verify_canonical_rom.py`.

## 5. Frontend native-only routing change

`scene 0 stage≠0` and `scene 2` → `.Lnq_frontend_native` → `native_frontend_hud_emit` +
`.Lnq_transient_items_emit` → `.Lnq_done_scan`. No object-RAM scan, no second renderer, no new SAT path.

## 6–8. Deleted infrastructure

Object-RAM store/scan/decode/adapters (§3 Phase 2), the D-range compatibility fill (§3 Phase 3), and the
object-RAM boot clear (§3 Phase 4) — all removed. `pc090oj_object_ram` no longer linked.

## 9. Native sprite infrastructure retained (Category C)

`staged_sprite_sat`/`_b`, `pc090oj_sat_bank`/`_front`/`_frame_ready`, `sprite_tile_resident_code`,
`pc090oj_tile_dma_worklist`/`_count`, `pc090oj_cell_used`, `pc090oj_sat_nibble`/`_force_line`,
`worklist_entry_for_slot` (live at the tile-DMA commit), `.Lnative_pal_fixup`/`.Lnative_palsel`,
`.Lnq_emit_entry`, `.Lnq_gameplay`/`.Lnq_project_p1_hud`, `native_frontend_hud_emit`, `.Lnq_title`,
`.Lnq_transient_items_emit`, `.Lnq_gameover_emit`, `vdp_prepare_sprites`/`vdp_commit_sprites`,
`genesistan_pc090oj_dma_self_test`, `pc090oj_emitted_count`/`pc090oj_dropped_count`/`pc090oj_sat_dirty`.

## 10. `pc090oj_ctrl_shadow` vs retained sprite-control state

`pc090oj_ctrl_shadow` was expected (Prompt 1 Phase 6) to become dead when the decoder was removed. **Verified
false — RETAINED:** it is read by the live **gameplay** flip path (`pc090oj_hooks.s`, the `.Lnq_gameplay`
emit at the former line 1966). `pc090oj_sprite_ctrl_shadow` is read by the shared `.Lnative_pal_fixup`
(colbank). Both are live native latches with historical names; kept. Their `ctrl_set_0/1` and
`sprite_ctrl_write/clear` capture hooks (which also suppress the raw `0xD01BFE`/`0x380000` hardware writes)
are unchanged.

## 11. Final D-range operand classification (`build/genesis_postpatch.disasm.txt`)

46 `0x00D0xxxx` executable operands. **Category C (reachable PC090OJ compatibility dependency): 0.**
- **A (dead/unreachable original arcade code):** the `0x05A51E`/`0x05A554` `movea.l #0xD00298/#0xD002B0`
  literals inside the unreachable `0x5A502` (`rts`) body; other retired-producer literals in dead bodies.
- **B (harmless constant/compare/vestigial load):** the dispatch's own `cmpil #0xD00000/#0xD00800` range
  checks; the native group-builder `lea 0xd0xxxx,%a1` vestigial loads (A1 overwritten before store); hardware
  range-classifier compares. None store to a virtual object RAM (which no longer exists).

## 12. address_map / reflow

Regenerated by the postpatcher. `arcade_copy` splice unchanged at `0x117E`; shift table applied (7,213 branch
fixes, 630 abs-long fixes); genesis-only→maincpu continuation refs = 7 (all shift-audited). ROM size unchanged
(1,597,112); `total_genesis_bytes_covered=0x185EB8` unchanged (`.crash` ALIGN(0x1000) padding absorbed the
genesis-only shrink; `.crash` remains at 0x185000, `_crash_common` 0x185144).

## 13. Unnumbered structural gate

- `pc090oj_object_ram` linked: **NO**. Generic 256-record scanner: **NO**. `.Lpc090oj_decode_record`: **NO**.
  emit/clear/mirror adapters: **NO**. 0x03AD44 D-range virtual-object support: **NO** (no-op). Object-RAM boot
  clear: **NO**. Reachable helper building an 8-byte PC090OJ record: **NO**. Reachable D-range→software-RAM
  translator: **NO**.
- Boot-guard PASS (pre + post): SP=0x00FF0000, RESET=0x00000202, VINT=0x000700C2.
- Canonical release gate (`verify_canonical_rom.py`) intentionally NOT run — it consumes the build number;
  deferred to the numbered Build 0297 release/regression task. Its `CANONICAL_OPCODE_REPLACE_COUNT` was
  updated to 226 for that task.

## 14. PC080SN unchanged

No PC080SN source/spec change. The 0x03AD44 C-range branches are byte-identical. Known Build-0296 PC080SN
defects (item-page text wrap/bleed, item-page→attract FG/BG mismatch) are untouched and remain OPEN.

## 15. GENESIS NTSC MAME result (`tools/mame/scripts/teardown_validate.lua`)

USA/NTSC `genesis`, unnumbered ROM, 90s headless (stops just before the pre-existing water-fall crash):
`crash_seen=false`; scene 0 (title + frontend substages incl. item page) `sat_nonzero_words_max=101`;
scene 1 (attract gameplay demo) `sat_nonzero_words_max=289`; **VERDICT=NO_CRASH**. Sprites render natively in
frontend and gameplay.

**Pre-existing crash confirmation:** a full 150s run hits the crash handler at `0x1853a0`/frame 5589; the
**identical** crash occurs in Build 0296 (`0x18539c`/frame 5590). This is the known water-fall ADDRESS ERROR
(separate OPEN issue), **not** a teardown regression — the teardown ROM is clean through the same frames as
0296.

## 16. Remaining PC090OJ compatibility debt

**NONE.** No `arcade → PC090OJ record → virtual object RAM → scanner/decoder → SAT` path exists for gameplay
or frontend. Remaining `0x00D0xxxx` operands are all category A/B (dead/vestigial); category C = 0.

---

**Ready for the numbered Build 0297 release/regression gate:** YES (pending Tighe's visual acceptance and the
canonical-gate release run). No numbered build produced here; no numbered artifact created or overwritten.
