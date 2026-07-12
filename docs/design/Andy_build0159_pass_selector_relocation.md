# Andy — Build 0159: Pass-Selector Relocation (0x503CE #0x050F6B → #0x05116B)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `2be3421` (pre-build), clean. Accepted Build 0158 ROM
`2bf5a06f…`, counter 158, opcode_replace 136. Task class: EXTENDING (KF-039/shift-relocation literal class).
KNOWN_FINDINGS touched: KF-039 + the missed data-register pointer-literal relocation class. OPEN issue: OPEN-017.

## 2. Site verification (Phase 1 — all passed)
1. arcade `0x503CE` bytes = `203C00050F6B` (`movel #0x00050F6B,d0`) ✓ (maincpu.disasm).
2. Genesis `0x505CE` (Build 0158) still `203C00050F6B` (un-relocated) ✓.
3. sibling arcade `0x503BC` `moveal #0x00050EE0,a1` → Genesis `0x505BC` `moveal #0x000510E0,a1` (already relocated) ✓.
4. `ROM[0x05116B] = 0x00` (correct relocated target = arcade data) ✓.
5. `ROM[0x050F6B] = 0x80` (wrong un-relocated byte) ✓.
6. Only ONE reference to `#0x00050F6B` in the copied arcade code (0x503CE) — no other un-relocated refs ✓.
7. No existing opcode_replace overlaps 0x503A0–0x503E0 ✓.

## 3. State-causality answers
1. **What state should exist?** `a5@0x10C6` → relocated pass-seq table `0x0005116B + index`; the byte read = 0x00
   for Stage 1; `a5@0x10A8 = 0x0000`; the PC080SN tilemap dispatch (`0x55948`) takes the BG branch (arcade).
2. **Which code creates it?** `0x503BC`/`0x503CE` compute the pass-seq pointer into `a5@0x10C6`; the desc-rebuild
   reads `*(a5@0x10C6)` → `a5@0x10A8`.
3. **Why not now?** `movel #0x00050F6B,d0` is a **data-register immediate**; the postpatch shift-relocation only
   adjusts abs.l control-transfer/LEA operands (`maybe_shift_abs_long_expected_bytes`: opcodes 0x4EB9/0x4EF9/LEA),
   so `#0x00050F6B` was not shifted +0x200 (its abs-reg sibling `#0x00050EE0` was). Genesis read
   `ROM[0x050F6B]=0x80` → `a5@0x10A8=0x0080` (FG) instead of 0x0000 (BG).

## 4. Readiness classification: **A** (single byte-neutral relocation, proven and bounded)
Confirmed A pre-build (site verified, sibling relocated, one reference, no overlap, opcode 0x203C not in the
shift-adjust set → replacement not re-shifted). Implemented.

## 5. Exact opcode/spec change
One `opcode_replace` (spec `rastan_direct_remap.json`, first entry):
`arcade_pc 0x0503CE`, `original_bytes 203C00050F6B`, `replacement_bytes 203C0005116B`
(`movel #0x00050F6B,d0 → movel #0x0005116B,d0`; opcode 0x203C preserved; byte-neutral 6→6). Canonical counts
paired-updated 136→137 in `postpatch_startup_rom.py`, `verify_canonical_rom.py`, and spec
`expectations.opcode_replace_count`. Coverage unchanged (0x182070; byte-neutral). No other change.

## 6. Static validation
GATE_PASS; boot guard PASS (SP=0x00FF0000, RESET=0x00000202, VINT=0x000700C2). Postpatch disasm
`0x505CE = movel #0x0005116B,d0` (`203c 0005 116b`) — relocated, **not** re-shifted. Sibling `0x505BC` remains
`moveal #0x000510E0,a1`. ROM size 1,581,168 = Build 0158 (byte-neutral). opcode_replace=137. address-map
gaps/overlaps clean. ROM bytes `0x505CE = 203c0005116b`. ROM SHA
`14138b825fa0dcbfea52d9a519574b615e11722ad41e73a0b56752d4f75b905a`. counter 159.

## 7. Runtime selector before/after
`states/traces/build_0159_passsel_verify/gen159.txt` (deterministic — two identical runs):
- **Build 0158:** desc-rebuild helper (0x071728) `srcptr=0x050F6B, *ptr=0x80` → `a5@0x10A8 = 0x0080` (FG).
- **Build 0159:** desc-rebuild helper (0x071728) `srcptr=0x05116B, *ptr=0x00` → `a5@0x10A8 = 0x0000` (BG). ✓
- The relocated pointer now reads the correct control byte (0x00). Command source `a5@0x137A=0x00FF` intact.

## 8. BG/FG dispatch before/after
Dispatch selector histogram at `0xFF10CA` strip-write:
- **Build 0158:** `a5@0x10A8=0x0080 ×80` (FG), `0x0000 ×3` (BG).
- **Build 0159:** `a5@0x10A8=0x0000 ×83` (BG) only — **100% BG, arcade-equivalent** (arcade is always 0x0000). ✓
`genesistan_hook_tilemap_plane_a` (BG) now runs the Stage-1 pass; `genesistan_hook_tilemap_fg` no longer
dominates it.

## 9. Collision observation (not fixed in this build — expected)
Collision WRAM `0xFF1E00` still empty (nonzero=0). Reader still uses raw `0x0010DE00` (ROM garbage). Early
`mode=0x0008` still fires (F=679, rel≈165 after 2/3/0 at F=514) — unchanged from Build 0158. This build is the
selector prerequisite; collision emission + 9-site rebase remain deferred, as intended.

## 10. Rendering validation
- **BG staging intact:** gameplay `staged_bg nonzero=2048` (= Build 0158). Frontend `staged_bg=560`.
- **Frontend fully intact:** title (s=0/1/0, F=140) IDENTICAL to Build 0158 — `represented_count=15`,
  `staged_sprite_active=15`, `staged_bg=560`, `staged_fg=66`. Title/story/BEST5/item-page paths unaffected (the
  fix only changes the gameplay pass selector).
- **Gameplay FG staging REGRESSED (expected pass-selection impact):** gameplay `staged_fg` dropped **2020 → 12**.
  Build 0155's FG staging (`genesistan_hook_tilemap_fg` gameplay path) was reached via the **FG branch** of the
  dispatch, which fired only because of the (now-fixed) `a5@0x10A8=0x80` bug. With the correct BG selector, that
  hook no longer runs, so the Stage-1 FG plane is no longer staged. This does **not** break frontend paths →
  classified as **expected pass-selection impact**, requiring a follow-up to re-anchor the FG_SRC staging to the
  correct pass. No new strict-target fatal address. (scrY_bg=0x0000 at F=560 now — the vertical-pan behavior
  also changed with the corrected pass.)

## 11. Regression validation
- Build 0158 command-source rebase intact: `0x5122E = movew 0xff0016,d0`; runtime `a5@0x137A=0x00FF`.
- Build 0157 PC090OJ SAT handoff intact: title `represented_count=15`.
- Build 0156 C08C66 route intact: `0x3D24C = jsr 0x708C8`.
- Build 0152 C08C62 route intact: `0x3A92A = jsr 0x70894`.
- Build 0155 FG plane route **accounted for**: FG staging now bypassed by the correct selector (expected impact;
  re-anchor follow-up). Build 0154 BG plane **accounted for**: BG staging intact (2048).
- Canonical gate PASS; boot guard PASS; 30s trace clean; **two deterministic MAME runs identical**.

## 12. Open/Closed Issues Impact
OPEN-017 advanced (build-verified): the Stage-1 tilemap **pass selector** `a5@0x10A8` is now `0x0000` (BG,
arcade-equivalent) on Genesis after relocating the pass-seq table base literal `0x00050F6B → 0x0005116B` at
arcade `0x503CE`. Dispatch is 100% BG; frontend/BG/command/sprites intact. **New follow-up surfaced:** Build
0155's gameplay FG staging (`genesistan_hook_tilemap_fg`) was triggered by the FG branch (the bug) and is now
bypassed → gameplay FG plane must be re-anchored to the correct pass. Collision remains unfixed (empty WRAM,
early type-8) — the next collision build still applies. Not closed.

## 13. KNOWN_FINDINGS impact
**New: KF-042** (build-verified) — the pass-seq table base literal at arcade `0x503CE` (`movel #imm,Dn`) is not
shifted by the postpatch relocation (data-register immediate), so Stage-1 tilemap pass selector `a5@0x10A8`
became 0x80 (FG) instead of 0x00 (BG); fixed by opcode_replace `0x00050F6B → 0x0005116B` in Build 0159. Also a
reinforced instance of KF-039 (missed data-register pointer literal, cf. Build 0158 command source).

## 14. Architecture compliance
CONFIRMED. Byte-neutral operand relocation through the declarative spec `opcode_replace` pipeline
(original-bytes validated); arcade program stays the source of truth; no NOP/RTS, no destination patch, no
forced value, no collision emission, no `0x0010DE00` rebase, no reader patch, no tilemap-hook edit, no
mode/stage-controller/player/camera/scroll/sprite/frontend change. Exactly one opcode_replace added. Builds
0152/0154/0155/0156/0157/0158 accounted for (frontend + routes intact; Build 0155 gameplay-FG impact documented).
