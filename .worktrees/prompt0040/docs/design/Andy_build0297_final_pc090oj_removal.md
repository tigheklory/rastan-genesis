# Andy — Build 0297 Final PC090OJ Removal

**Type:** Implementation / numbered release. **Baseline:** Build 0296. **Produced:** Build 0297 via the
normal sequential numbered pipeline (`make release`, GATE_PASS).
**Artifact:** `dist/rastan-direct/rastan_direct_video_test_build_0297.bin`
**SHA-256:** `4fad1555c7ddf61ed92a779bc09a4561a55e96e1b60422cd49fac3ff929ce441` · **size:** 1,597,112 ·
**counter:** 296→297 · **opcode_replace:** 227 · **genesis-only→maincpu refs:** 7.

## 1. Phase 0 statement
- **Relevant priors:** KF-025 (raw D-range writes render blank / can fault on Genesis), KF-026 (PC090OJ
  write surface not fully static), KF-016 (title VBlank sprite-RAM clear uses Y=0x100 park), KF-011
  (arcade Level-5 VBlank owns progression — unchanged), OPEN-024 (PC090OJ sprite subsystem), CLOSED-019.
- **Rediscovery-Hazard HIGH acknowledged:** KF-011, KF-025, KF-026.
- **Task classification:** EXTENDING.
- **Open/Closed issues touched:** OPEN-024 (narrowed, not closed — see §21).
- **CONFIRMED/STRONG contradiction:** NONE.

## 2. Build 0296 baseline
Accepted numbered baseline; the water-fall ADDRESS ERROR later in attract is a pre-existing OPEN issue.

## 3. Rule-conflict correction from the prior unnumbered attempt
The previous teardown was built/tested as an unnumbered scratch ROM (`build/rastan-direct/UNNUMBERED_
teardown.bin`) — a violation of the sequential-numbering rule. That scratch is **preserved as evidence,
not promoted**. Build 0297 is generated fresh from the corrected source tree through the canonical
numbered pipeline. The prior analysis (census/teardown reports) is used only as evidence.

Two rule-sensitive teardown changes were also corrected per Tighe's explicit direction:
- **3b930** is no longer an RTS shell — the Genesis compatibility hook and its remap/`required_symbols`
  ownership are **removed entirely** (see §6).
- The **0x03AD44 D-range no-op** is gone — the D-range callers are retired at their arcade semantic
  boundary and PC090OJ recognition is removed from the dispatcher (see §7–8).

## 4. Prior census result (re-used)
`Remaining live PC090OJ semantic producers: NONE`; the object-RAM scan/decoder path was proven dead
output (runtime backstop `GLOBAL_MAX_DRAWABLE_CANDIDATE_CODES=0` over 14,382 frames). Re-verified below.

## 5. Current-tree revalidation
Confirmed in the Build 0297 link/disasm: `pc090oj_object_ram`, `.Lnq_frontend_object_scan`,
`.Lpc090oj_decode_record`, `.Lpc090oj_emit_slot`/`clear_slot`/`mirror_write_word/byte`,
`.Lpc090oj_mode2_project_p1_hud`, `genesistan_pc090oj_hook_target_3b930`, and the dead alias stubs are
**absent from the link**; no executable reference to any remains (comment mentions only).

## 6. Handling of 3b930
`genesistan_pc090oj_hook_target_3b930` (Genesis hook) and its remap entry at `arcade_pc 0x03B930` are
**deleted**; the symbol is removed from `required_symbols`. Arcade 0x3B930's original copier bytes remain
as **dead, unreachable arcade code** (its only callers — 0x3B902 body-replaced inert, 0x3B8B0 `rts;nop` —
never reach it). No RTS shell; no raw D-range write is restored to a reachable path.

## 7. Semantic retirement of each D-range caller (Tighe-authorized, narrowly scoped)
The PC090OJ D-range users are two arcade routines whose **entire body is obsolete PC090OJ object-RAM
clearing/parking** (fill value 0x100 = off-screen Y park, KF-016) with no other arcade state/control work,
and no native Genesis effect (the native SAT is rebuilt every frame):
- **arcade 0x03AD4C** — fills 0xD00000 (8 longs) + 0xD00170 (386 longs) via `bsr 0x03AD44`, then `rts`.
  Reached from 6 caller sites: 0x3A242, 0x3A2DC, 0x3A5A4, 0x3A8D6, 0x3AA44, 0x3AA9E.
- **arcade 0x03AD72** — fills 0xD00000 (480 longs) via `bsr 0x03AD44`, then falls into the already-`rts`-
  hooked 0x03AD84 (records 76..79). Reached from 2 caller sites: 0x3ABB6, 0x3AF28 (0x03AD84 has no other
  caller).

**Reconfirmed before applying** (arcade Ghidra disasm): every instruction in both routines is fill-setup
(`d1`=count, `a0`=D-range dest, `d0`=fill) / `bsr 0x03AD44` / `rts` — nothing else. The 8 callers read no
return value and continue to unrelated work (e.g. 0x3ABBA `clr.l 0xC20000` PC080SN scroll). No caller
needs a semantic replacement.

**Replacement (byte-neutral opcode_replace, the established `4E75 4E71` retirement form):**
`0x03AD4C`: `323C0008` → `4E754E71`; `0x03AD72`: `323C01E0` → `4E754E71`. Each routine returns
immediately; its D-range `bsr` sites (0x3AD5C/6E/82) and 0x3AD72's fall-through into the dead 0x03AD84 init
become unreachable dead bytes. This RTS was applied **only** with Tighe's explicit, narrowly-scoped
permission for these two proven-obsolete routines — not as a general NOP/RTS licence.

## 8. 0x03AD44 before/after ownership
- **Before:** polymorphic dispatcher — D-range [0xD00000,0xD00800) → PC090OJ object-RAM fill; C-range
  [0xC00000,0xC10000) → PC080SN tilemap/scroll fills.
- **After (Build 0297):** `genesistan_hook_3ad44_dispatch` recognizes **only** the C-range; A0 outside
  [0xC00000,0xC10000) → audit-guard. No D-range compare/branch remains (verified in the final disasm at
  runtime 0x072b9a). Because the two D-range callers are RTS-retired, no D-range address ever reaches it.

## 9. Proof C-range PC080SN behavior is unchanged
The C-range branches (0xC04000/0xC08000/0xC0C000 → `genesistan_hook_tilemap_bg_fill` /
`genesistan_hook_pc080sn_bg_scroll_fill` / `genesistan_hook_tilemap_fg_fill` /
`genesistan_hook_pc080sn_fg_scroll_fill`) are **unchanged**; the four live C-range callers (arcade
0x3AE70, 0x3AE80, 0x3AF38, 0x3AF48) still route through them. No PC080SN source/spec change.

## 10. Deleted PC090OJ infrastructure
`pc090oj_object_ram`; frontend 256-record scan `.Lnq_frontend_object_scan`; decoder
`.Lpc090oj_decode_record`; `.Lpc090oj_emit_slot`/`clear_slot`/`mirror_write_word/byte`;
`.Lpc090oj_mode2_project_p1_hud`; the 3b930 hook + remap; the D-range dispatch branch + object-RAM
boot clear (via the RTS'd clear routines); dead scan diagnostics; dead exported-alias stubs; the dead
0x05A51E/0x05A554 GAME OVER object-RAM redirects.

## 11. Retained native sprite infrastructure (Category C — historical name, native behavior)
`staged_sprite_sat`/`_b`, SAT bank/front/frame-ready, `sprite_tile_resident_code`,
`pc090oj_tile_dma_worklist`/`_count`, `pc090oj_cell_used`, `pc090oj_sat_nibble`/`_force_line`,
`worklist_entry_for_slot`, `.Lnative_pal_fixup`/`.Lnative_palsel`, `.Lnq_emit_entry`, `.Lnq_gameplay`,
`.Lnq_project_p1_hud`, `native_frontend_hud_emit`, `.Lnq_title`, `.Lnq_frontend_native`,
`.Lnq_transient_items_emit`, `.Lnq_gameover_emit`, `vdp_prepare_sprites`/`vdp_commit_sprites`,
`pc090oj_emitted_count`/`pc090oj_dropped_count`/`pc090oj_sat_dirty`, `genesistan_pc090oj_dma_self_test`.

## 12. ctrl-shadow findings
`pc090oj_ctrl_shadow` — **retained**; read by the live gameplay flip path (not decoder-only, correcting
the earlier assumption). `pc090oj_sprite_ctrl_shadow` — retained; read by `.Lnative_pal_fixup` (colbank).
Both are native semantic latches with historical names. Their `ctrl_set_0/1` and `sprite_ctrl_write/clear`
capture hooks (which also suppress the raw 0xD01BFE / 0x380000 hardware writes) are unchanged.

## 13. Final D-range operand classification
45 `0x00D0xxxx` executable operands. **Category C (reachable PC090OJ compatibility dependency) = 0.**
- **A (dead/unreachable arcade code):** the fill-setup literals inside the RTS-retired 0x03AD4C/0x03AD72
  bodies (0xD00000/0xD00170) and the 0x03AD84 init (0xD00778), all after an entry `rts`; the unreachable
  0x3B930 copier and 0x5A502 (`rts` body) literals.
- **B (constant/compare/vestigial load, no effect):** the native group-builder `lea 0xd0xxxx,%a1` loads
  (A1 overwritten before store); hardware range-classifier `cmpi.l #0xD00000/#0xD00800` compares.

## 14. Zero-debt ten-question gate — all NO
1 record construct: NO · 2 object RAM: NO · 3 scan virtual records: NO · 4 decode: NO ·
5 D-range→software-RAM translate: NO · 6 helper receiving a PC090OJ op to ignore: NO (no D-range case) ·
7 clear/park virtual records: NO (clear routines RTS'd) · 8 frontend depends on PC090OJ: NO ·
9 gameplay depends on PC090OJ: NO · 10 PC090OJ-only remap/helper necessary: NO.

## 15. Remap changes
Removed: 0x03B930 entry, 0x05A51E/0x05A554 entries (prior), `pc090oj_object_ram` +
`staged_sprite_descriptor_table`/`staged_sprite_dirty`/`staged_sprite_active_count` +
`genesistan_pc090oj_hook_target_3b930` from `required_symbols`. Added: 0x03AD4C, 0x03AD72 RTS entries.
`opcode_replace_count` 226→227; `genesis_only_maincpu_ref_count` = 7. Tool constants
`CANONICAL_OPCODE_REPLACE_COUNT` = 227 (postpatcher + gate).

## 16. Shift / reflow / address-map
shift_table: 67 replacements, 7,213 branch fixes, 630 abs-long fixes. arcade_copy splice unchanged at
0x117E; coverage 0x185EB8 unchanged; `.crash` at 0x185000. address_map regenerated; boot-guard PASS
(pre+post).

## 17. Canonical gate result
**GATE_PASS.** Numbered name verified `rastan_direct_video_test_build_0297.bin`; 30s Genesis-NTSC release
trace clean (970% avg, no crash) — `states/traces/rastan_direct_video_test_build_0297_mame_30s_*`.

## 18. Build 0297 artifact
Path/SHA/size/counter/opcode_replace as in the header. All prior numbered ROMs (0280–0296) preserved;
scratch `UNNUMBERED_teardown.bin` preserved as evidence (not promoted, not deleted).

## 19. GENESIS NTSC MAME results
90s (pre-water-fall): `crash_seen=false`; frontend scene (title + substages incl. item page)
`sat_nonzero_words_max=101`; gameplay demo `sat_nonzero_words_max=289`; **NO_CRASH** — sprites render
natively. Tool: `tools/mame/scripts/teardown_validate.lua`.

## 20. Known water-fall crash status
Full 150s run: crash handler at `0x1853a0` / frame 5589. Build 0296 hits the **identical** crash at
`0x18539c` / frame 5590. Matched by address/interval → the pre-existing water-fall ADDRESS ERROR
(separate OPEN issue), **not** a Build-0297 regression. Not fixed here.

## 21. Open/Closed issue impact
**OPEN-024** — the PC090OJ compatibility subsystem it tracks is now fully removed; sprite ownership is
100% native. Its closure condition requires *correct visual tile/palette/position behavior* (Tighe
acceptance) with remaining sprite defects split out. Build 0297 proves the architecture and that sprites
render (no crash, SAT 101/289), but headless validation cannot confirm full visual correctness, and known
sprite-visual defects remain under OPEN-006 (palette) / OPEN-017 (positions/enemies). **Narrowed, not
closed** — recommended for closure pending Tighe's visual acceptance. No other issue altered.

## 22. KNOWN_FINDINGS impact
Recommend **Option A (new finding)**, ACTIVE/STRONG/GLOBAL: the software PC090OJ object-RAM/scanner/
decoder architecture is removed as of Build 0297; all production sprite output is native Genesis
semantic-lane/SAT; no D-range PC090OJ compatibility remains; `0x03AD44` survives only for PC080SN C-range
ownership and is deleted by the PC080SN retirement task. (Not written unilaterally — proposed for your ok.)

## 23. PC080SN Final-Retirement Handoff
Reconnaissance for the NEXT task (do **not** implement here).

1. **Remaining live callers of 0x03AD44** (all PC080SN C-range fills, arcade_pc): **0x3AE70, 0x3AE80,
   0x3AF38, 0x3AF48** (`bsr 0x03AD44`, A0 ∈ [0xC00000,0xC10000)).
2. All four are **PC080SN C-range** operations (0xC0xxxx name-table / scroll fills).
3. **C-range families still handled** by the dispatcher: BG names [0xC00000,0xC04000) →
   `genesistan_hook_tilemap_bg_fill`; BG scroll [0xC04000,0xC08000) →
   `genesistan_hook_pc080sn_bg_scroll_fill`; FG names [0xC08000,0xC0C000) →
   `genesistan_hook_tilemap_fg_fill`; FG scroll [0xC0C000,0xC10000) →
   `genesistan_hook_pc080sn_fg_scroll_fill`.
4. **Generic PC080SN hardware-address translation helpers:** `genesistan_hook_3ad44_dispatch` (C-range
   only), plus the tilemap/scroll fill helpers above and the broader tilemap dispatch family in
   `tilemap_hooks.s` (e.g. `genesistan_hook_tilemap_plane_a`, descriptor-rebuild, item-page strip
   populate/blit) — full enumeration is the next task's Phase-0 census.
5. **PC080SN virtual/shadow/staging compatibility structures NOT already final Plane/scroll format:**
   the staged BG/FG buffers and C-window shadow paths, per-line scroll fill stubs
   (`genesistan_hook_pc080sn_bg/fg_scroll_fill`, currently no-ops), and the item-page text row-streaming
   path — to be inventoried and classified (final-Genesis vs compatibility) in the next task.
6. **Upstream semantic owners** of each remaining PC080SN hardware op: the arcade tilemap/scroll
   producers (name-table writers, scroll-register writers a5@0x10AE/0x10B0/0x10EC/0x10EE, item-page text
   writer 0x563A6/dispatch) — to be traced to their highest semantic boundary.
7. **Native replacement status (current):** Plane A (FG) partial; Plane B (BG) partial; row/column
   publication partial; H-scroll native (`vdp_commit_scroll`); V-scroll native; **item-page text
   NOT native (known defect)**; gameplay BG partial; gameplay FG partial; scene transitions partial.
8. **Known Build 0296/0297 PC080SN defects (unchanged, out of scope):** item-page text wrap/bleed;
   missing native row-stream semantics; item-page Plane-B state; item-page→attract FG/BG mismatch.
9. **Final Genesis plane/scroll staging that must survive:** `staged_bg_buffer`/`staged_fg_buffer`,
   `staged_scroll_x/y_bg/fg`, `vdp_commit_scroll`, the PC080SN tile-LUT (KF-014), the plane-commit path.
10. **Condition to delete 0x03AD44 entirely:** when the four C-range callers (0x3AE70/80, 0x3AF38/48) and
    all other live PC080SN C-range name-table/scroll producers have native Genesis owners so no A0 ∈
    [0xC00000,0xC10000) reaches the dispatcher — then `genesistan_hook_3ad44_dispatch` and its remap can
    be removed.

**Handoff statement:** *0x03AD44 is now PC080SN-only temporary infrastructure and will be deleted when the
remaining PC080SN C-range semantic owners (arcade 0x3AE70/0x3AE80/0x3AF38/0x3AF48 and peers) have native
Genesis replacements.*

## 24. Final statement
**Remaining PC090OJ compatibility debt: NONE.**

## 25. Final statement
**0x03AD44 is now PC080SN-only temporary infrastructure.**

## USER MUST VERIFY (BlastEm / hardware / Exodus)
- Title/TAITO/RASTAN/sword sprites; frontend HUD (1UP/HIGH SCORE/2UP/credit); throne/story; ranking;
  Scrolling Items sprites (item art — the PC080SN *text* wrap is a known separate defect); ROUND/READY;
  attract-demo + ordinary gameplay player/enemy/effect sprites; GAME OVER — all should match Build 0296
  (no new missing/stale sprites, no SAT corruption). The later water-fall ADDRESS ERROR is pre-existing.
