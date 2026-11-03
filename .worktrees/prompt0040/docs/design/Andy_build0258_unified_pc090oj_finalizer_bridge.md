# Build 0258 — Unified PC090OJ Finalizer Bridge

**Agent:** Andy · **Type:** PC090OJ finalizer architecture bridge · **Build produced: YES (0258).** **STOP: NO.**
User authorization: Tighe approved Andy performing the source-changing build.

## 1. Baseline + prior STOP

Build **0257** current: ROM `dist/rastan-direct/rastan_direct_video_test_build_0257.bin`, SHA-256
`6aa273c9f1337b9d4e16a39a90ae5ee50debbf2eeb475ea3e0d0f92577e79b3e`, size `1591596`, counter `257`. Preserved.
Pre-edit coverage `0x18492C`, opcode-replace `221`. The prior `Andy_build0258_pc090oj_frontend_legacy_retirement.md`
STOP proved: gameplay uses native lanes; frontend/non-gameplay uses `pc090oj_object_ram` scanned by
`pc090oj_legacy_emit_pass` (active every frontend frame); frontend producers write `object_ram`, not lanes; no
PC090OJ component is safe to delete cold; the next safe step is this **finalizer bridge**.

## 2. User priority

Prepare the finalizer so future builds can convert frontend producers to native lanes one family at a time —
without deleting `object_ram`, removing the object scan, or converting producers yet.

## 3. Files/reports read

Governance + Cody 0251/0254/0255 + Andy 0249/0255/0256/0257 + the Build 0258 STOP audit; `pc090oj_hooks.s`,
`tilemap_hooks.s`, `vdp_comm.s`, `boot/boot.s`; `out/symbol.txt`, `address_map.json`, patch manifest, remap spec.

## 4. Current → new finalizer structure

**Before (0257):**
```asm
pc090oj_native_emit_pass:
    cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    beq.s   .Lnq_gameplay
    bra     pc090oj_legacy_emit_pass       ; separate exported (local t) finalizer
.Lnq_gameplay:            ...native semantic lanes... rts
pc090oj_legacy_emit_pass: ...object_ram scan...       rts
```

**After (0258):**
```asm
pc090oj_native_emit_pass:
    cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    beq.s   .Lnq_gameplay
    bra     .Lnq_frontend_object_scan      ; local scene!=1 continuation of THIS function
.Lnq_gameplay:              ...native semantic lanes... rts
.Lnq_frontend_object_scan:  ...object_ram scan (byte-unchanged)... rts
```

`pc090oj_native_emit_pass` now **owns both** finalizer paths; there is no standalone `pc090oj_legacy_emit_pass`
symbol. The object-RAM scan body is moved verbatim under a local label.

## 5. Exact source changes

Only `apps/rastan-direct/src/pc090oj_hooks.s`:
1. `bra pc090oj_legacy_emit_pass` → `bra .Lnq_frontend_object_scan` (scene≠1 branch, line 1560).
2. `pc090oj_legacy_emit_pass:` → `.Lnq_frontend_object_scan:` (label at 1925) + a bridge comment. The scan
   body, record range/order, masks, tile residency, and the `.Lnative_palsel` palette fixup are unchanged.

No other line changed. The two canonical `.py` constants were **not** touched (coverage unchanged, §7).

## 6. Standalone `pc090oj_legacy_emit_pass` symbol: RETIRED (not aliased)

`pc090oj_legacy_emit_pass` was a **local `t` symbol** (no `.global`), referenced only by the intra-file `bra` —
**no** patch-manifest, remap-spec, or other-source xref. Renaming its label to the local `.Lnq_frontend_object_scan`
(an assembler-local `.L` label, not emitted to `out/symbol.txt`) removes the standalone symbol entirely.
Confirmed: `pc090oj_legacy_emit_pass` count in `out/symbol.txt` = **0**. It was retired, not kept as an alias.

## 7. Why the aggressive prologue/finalize merge was deferred (byte-safety)

The task's "desired structure" shows a shared common prologue + common finalize. Inspection shows the two
paths' prologues and epilogues **genuinely differ** and cannot be merged byte-equivalently:
- **Prologue:** gameplay unconditionally `bsr .Lnq_project_p1_hud`; the frontend path deliberately **skips** the
  mode-2 P1-HUD projection (`legacy` guarded it on scene==1, which is never true there).
- **Epilogue:** the frontend path runs a commit-time palette fixup (`.Lnpf_loop`/`.Lnative_palsel`) that the
  gameplay lane epilogue does not.

Per the task rule "preserve code-path byte behavior over code-size reduction if in doubt," these were left
per-path. The bridge therefore unifies **ownership** (one finalizer function, standalone symbol retired) while
keeping each path's body byte-for-byte — the safest Step-1.

## 8. Frontend equivalence — proven at the strongest level

Because the change is a pure **local-label rename** (no instruction bytes changed, same target addresses), the
assembled+linked+patched ROM is **byte-identical** to Build 0257:
- Build 0258 SHA-256 `6aa273c9f1337b9d4e16a39a90ae5ee50debbf2eeb475ea3e0d0f92577e79b3e` = Build 0257 SHA-256;
  size `1591596` = `1591596`.
This subsumes any staged-SAT comparison: **every scene** (title/story/high-score/insert-coin/Push-Player-Button/
attract/normal gameplay) produces byte-identical VDP/SAT output because the executable bytes are identical. No
per-frame SAT capture is needed — the identical ROM is the equivalence proof.

## 9. Preservation proofs

- Scene 1 native lane path preserved (`.Lnq_gameplay` unchanged); scene≠1 object-RAM scan preserved
  (`.Lnq_frontend_object_scan`, reachable via the `bra`).
- `pc090oj_object_ram` remains allocated (`0xFF6F92`); `vdp_prepare_sprites` (`0x739DA`) still enters
  `pc090oj_native_emit_pass` (`0x7331C`).
- `native_sprite_emit`/`native_sprite_frame_begin`/`native_stage_player_blocks_41f5e`/PLAYER_BODY lanes present
  and unchanged.
- Build 0254 D00298/D002B0 remaps preserved (symbolic `{symbol:pc090oj_object_ram+0x298/0x2B0}`). Build 0255
  demo-input fix preserved (`0x00FF0118` + `0x052C1C`). Build 0256/0257 PC080SN removals preserved
  (`staged_bg_tall_buffer`/projector symbols still absent).

## 10. Build + validation

- **GATE_PASS.** Counter **257 → 258**. Numbered ROM `dist/rastan-direct/rastan_direct_video_test_build_0258.bin`;
  SHA-256 `6aa273c9f1337b9d4e16a39a90ae5ee50debbf2eeb475ea3e0d0f92577e79b3e` (= 0257, byte-neutral); size
  `1591596`. Rolling = numbered. Build 0257 preserved.
- Opcode-replace **221 → 221**; coverage `0x18492C → 0x18492C`; gaps `[]`; overlaps `[]`.
- `pc090oj_legacy_emit_pass` symbol absent; `.Lnq_frontend_object_scan` present (branch + label).
- MAME smoke `states/traces/rastan_direct_video_test_build_0258_mame_30s_20260804_183313/`: frames `1798`, no
  unmapped/fatal/error.

## 11. User verification required (post-Andy)

Byte-identical ROM ⇒ expected identical to 0257: title/story/high-score good; item screen unchanged; attract
demo scripted action; normal gameplay Rastan/lizards/bats/axe; no frontend sprite loss; no new regression.

## 12. Next PC090OJ step

**Recommended first frontend producer-family conversion: the score-digit hook `0x3B802`** → emit its digits via
`native_sprite_emit` into a native HUD lane, and have `.Lnq_frontend_object_scan` **exclude** that record band
from the object scan (exactly the pattern the gameplay lanes used). Reason: score digits are the most
self-contained frontend family (fixed positions, one arcade hook, small band), giving a low-risk first
conversion that shrinks the frontend object scan while the merged finalizer already owns both paths. Then
`0x5A098` status → `workram_block_sprites` blocks → D00298 family, until the frontend scan is empty and retires.

## 13. Issues / findings

- Open issues touched: OPEN-024-adjacent PC090OJ native migration (frontend). New: none. Closed: none.
- Deferred: the shared prologue/finalize factoring (byte-safety, §7); all frontend producer conversions (§12);
  item-description screen; the four dead aliases; Push-Player-Button residue.
- KNOWN_FINDINGS: Option A — no new finding; **not edited** (Build 0255 sync pending).
- **Andy follow-up recommended: YES** — author the `0x3B802` score-digit → HUD-lane conversion spec next.

## 14. STOP status

**STOP: NO.** The Step-1 unified-finalizer bridge is implemented safely: `pc090oj_native_emit_pass` owns both the
gameplay native-lane path and the frontend object-RAM scan, the standalone `pc090oj_legacy_emit_pass` symbol is
retired, and the ROM is byte-identical to Build 0257 (strongest equivalence). Every do-not-touch path
(object_ram, native lanes, PLAYER_BODY, 0254/0255/0256/0257 fixes) is preserved. The finalizer is now ready for
family-by-family frontend conversion.
