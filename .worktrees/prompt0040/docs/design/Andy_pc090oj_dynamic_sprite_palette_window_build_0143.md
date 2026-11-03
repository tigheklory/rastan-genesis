# Andy — Build 0143 PC090OJ Dynamic Sprite Palette Window (Outcome C, STOP)

**Agent:** Andy (temporarily filling Cody's implementation/runtime-evidence role; exception ends Thursday evening).
**Type:** Implementation + verification. **Result: Outcome C — coordinated mapping fails on a proven existing-system dependency; production source reverted, not committed.**
**Branch:** `rastan-direct-proposal` (head `96b2acc`). Baseline Build 0142 preserved.

## 1. Phase 0 baseline statement
```
Relevant priors from KNOWN_FINDINGS:
  - KF-011 (Frame ownership: arcade Level-5 VBlank owns progression) — CONFIRMED/STRONG;
    applies because both changes must stay inside arcade-called helpers with no Genesis loop/lifecycle.
  - KF-032 (Raw copied PC080SN/PC090OJ writes must route through Genesis staging) — CONFIRMED;
    applies because the palette change must keep routing through staged_palette_words + palette_dirty + VBlank commit.
  - KF-026 (PC090OJ runtime write surface not fully statically enumerable) — STRONG; context only (OPEN-006).
  - KF-010 (BG→Plane B, FG→Plane A) — STRONG; applies to the shared-CRAM regression check.
  - KF-021 (sprite early-return + SAT-DMA suppression masks sprites) — STRONG/CONTAMINATED; caution: no suppression added.
  - CLOSED-004 (palette xBGR-555 at 0x200000) — context: producer conversion format unchanged.
Rediscovery Hazard HIGH findings touched: KF-011, KF-032, KF-021 — all RESPECTED.
Deferred-appendix relevant: DEF-004 (palette precomputed offline / direct CRAM DMA) — not treated as canonical prior.
Task classification: NEW — implements + measures arcade-sprite-bank → Genesis-CRAM-line mapping and producer/colbank timing, not currently indexed in a KF.
Open/Closed issues touched: OPEN-006 (primary), OPEN-024 (context), OPEN-001 (context), OPEN-002 (naming), CLOSED-004 (context).
Contradiction of CONFIRMED or STRONG finding detected during Phase 0 read: NONE.
```

## 2. Accepted audit findings used as priors (from `docs/implementation/Andy_frontend_header_palette_build0143.md`)
Arcade `color = (word0 & 0x000F) | sprite_colbank`; `sprite_colbank = (sprite_ctrl & 0x00E0) >> 1`. Frontend `sprite_ctrl = 0x60` → colbank 48. Header records 28–45 (word0 low nibble 0) → arcade bank 48; item-icon records 64–67 (word0 low nibble 3) → arcade bank 51. Genesis mirror word0 and `pc090oj_sprite_ctrl_shadow` match the arcade. Build 0142 renderer computed line `(bank>>4)&3`, aliasing 48 and 51 both to line 3; producer `genesistan_palette_hook_3ba64` loaded fixed banks 0–3 into lines 0–3.

## 3. Exact source changes (implemented, validated, then REVERTED — not committed)
- **Change 1 — renderer palette line** (`apps/rastan-direct/src/pc090oj_hooks.s`, `.Lpc090oj_place_record_in_slot`): removed `lsr.w #4,%d0`, changing `line = ((word0&0x0f)|colbank) >> 4 & 3` → `line = ((word0&0x0f)|colbank) & 3`. Only the palette-line bits of staged SAT word2 change; slot/link/tile/X/Y/flip/priority untouched.
- **Change 2 — producer window** (`apps/rastan-direct/src/palette_hooks.s`, `genesistan_palette_hook_3ba64`): added `.extern pc090oj_sprite_ctrl_shadow`; replaced the fixed `bank<4` filter with `line = arcade_bank - ((pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1)`, staged only if `line` in `[0,3]` (`cmpi.l #4; bhs skip`). Kept `staged_palette_words` + `palette_dirty` path; no direct CRAM; no new colbank variable; no hardcoded 48; no screen-identity check; no state machine.
- Predictable paired canonical bump (authorized): `CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x17DCC4 → 0x17DCD0` (net +12 B helper growth), `opcode_replace` unchanged 133.

## 4. Static disassembly proof (of the built, now-rejected Build 0143)
- Renderer: `lsr.w #4,%d0` removed (grep = 0 occurrences); SAT word2 build now `andi #0x0f | or colbank | andi #3 | <<13`.
- Producer (`0x718ac–0x718c2`): `moveq #0,%d1; movew 0xff71d2,%d1; andi #0xe0; lsr #1; sub.l %d1,%d6; cmpi.l #4,%d6; bhs skip` → line = bank − colbank, staged to `staged_palette_words` (`0xff609e`). No direct-CRAM instruction added; `palette_dirty` path preserved.

## 5. Address-map and manifest results (rejected Build 0143)
`opcode_replace = 133` (unchanged); `total_genesis_bytes_covered = 1563856` = 0x17DCD0; `segment_coverage.gaps = []`, `overlaps = []`. No patched-site/wrapper byte change (count unchanged, gaps/overlaps 0). GATE_PASS, boot guard PASS, 30 s trace clean.

## 6. SAT palette-line evidence — Change 1 SUCCEEDED
GENESIS MAME, item screen (state 2/2/6, `sprite_ctrl_shadow=0x0060`, colbank 48). SAT palette-line bits per represented record: header records 28–45 (bank 48) → **Genesis line 0** (18 sprites); item-icon records 64–67 (bank 51) → **Genesis line 3** (4 sprites). Histogram `(bank,line)`: `{(48,0):18, (51,3):4}`. The renderer now selects distinct lines for banks 48 and 51.

## 7. Staged CRAM bank evidence — Change 2 DID NOT deliver the window
Item-screen `staged_palette_words`: line 0 = arcade **bank 0** (`#000000 #ffffff #ff0000 #916d48 …`), line 3 = arcade **bank 3** (`#916d91 …` purple) — **unchanged from Build 0142**, NOT banks 48/51. Required: line 0 = arcade bank 48 (`#000000 #000000 #830000 #f65200 #f69400 #f6f600 #f6f694 #f6f6f6`), line 3 = bank 51. CRAM values do not result.

## 8. Title/story/item colbank transition evidence (GENESIS MAME producer trace, to frame 1320)
- `pc090oj_sprite_ctrl_shadow = 0x0060` (colbank 48) throughout the sampled frontend states (0/1/0, 0/1/2, 2/0/0, 2/2/6).
- **P3BA64 fires exactly twice, both at `sctrl=0x0000` (colbank 0):** `a0=0x00200000 d3=0x300` (banks 0–47) and `a0=0x00200600 d3=0x10` (**bank 48**). It NEVER fires at `sctrl=0x0060`. At its run time the active window is `[0,3]`, so `line = 48 − 0 = 48 ≥ 4` correctly rejects bank 48.
- **P59AD4** (a *different* producer, `genesistan_palette_hook_59ad4`) fires at `sctrl=0x0060` with `d0=0x0001` and `d0=0x0033 (51)`; its own `cmpi #4; bcc` gate rejects `d0=51`. This is the live sprite-bank load at colbank 48, flowing through a producer outside the authorized `3ba64` boundary.

## 9. Exact before/after header colours
| element | arcade intent | Build 0142 | Build 0143 (rejected) |
|---|---|---|---|
| 1UP | `#f7f700` yellow | ~`#f75200` (line3=bank3) | still wrong (line 0 = bank 0) |
| HIGH SCORE | `#f75200` orange | ~`#745774` purple | still wrong (line 0 = bank 0) |
| 2UP | `#f75200` orange | ~`#745774` purple | still wrong |
| scores | white | ~`#340034` | still wrong |

The SAT-line change routes the header to line 0, but line 0 holds arcade bank 0, so the colours remain non-arcade. No acceptance.

## 10. Bank-51 item result
Item icons (records 64–67) → Genesis line 3; line 3 CRAM = arcade bank 3 (purple), not bank 51. Not corrected.

## 11. Non-sprite shared-CRAM regression result
Not reached / N/A. The producer change never populated lines 0–3 with the sprite window, so the decisive shared-CRAM plane-recolour test could not be exercised as an acceptance gate. The change was reverted; no residual plane recolour is introduced (tree restored to Build 0142).

## 12. Retained-renderer (Build 0142) invariant result
Not applicable as an acceptance gate (fix reverted). Build 0142's retained renderer is preserved byte-for-byte; the reverted Change 1 touched only the palette-line bits and no geometry/identity/worklist/DMA behavior.

## 13. DISPLAY_OFF timing comparison
N/A — production change reverted; Build 0142's 994-cycle stable DISPLAY_OFF is unchanged (the palette-line edit is a few instructions in the same helper and does not alter commit/DMA timing).

## 14. Files changed
**Production source: NONE committed** (Change 1/Change 2 and the paired canonical bump were implemented, built, validated as failing, and reverted). **Committed (documentation only):** this design doc, `AGENTS_LOG.md`, `OPEN_ISSUES.md`.

## 15. ROM path, size, SHA256 (rejected Build 0143 evidence — retained, not the branch head)
`dist/rastan-direct/rastan_direct_video_test_build_0143.bin`, size 1,563,856 B, SHA256 `4518bd0bfd19ce4e014a9d13b17eedafae03aac8afe6d354e4baef2227136bec`. Build counter left at 143 (rejected 0143 consumed); the next ROM-producing task uses **Build 0144**.

## 16. Commit SHA (if Outcome A)
N/A — Outcome C. Only a documentation commit is made; no production/ROM commit.

## 17. STOP evidence (Outcome C — exact conflict)
The arcade writes the header's sprite palette **bank 48** into palette RAM through `genesistan_palette_hook_3ba64` (`a0=0x00200600`) **while `pc090oj_sprite_ctrl_shadow = 0x0000` (colbank 0)** — i.e. before it sets `sprite_ctrl = 0x60`. Keying the authorized producer's window off the current shadow at run time therefore evaluates window `[0,3]` and correctly rejects bank 48. The producer is **not re-invoked after the colbank transition to 48** (P3BA64 fires only at `sctrl=0x0000` across the whole sampled frontend). The live sprite-bank update at colbank 48 arrives through a **different producer** (`genesistan_palette_hook_59ad4`, `d0=51`), which its own `<4` gate rejects and which lies **outside the authorized `3ba64` boundary**. Consequently the required CRAM values (bank 48 in line 0, bank 51 in line 3) do not result; the item-screen CRAM line 0 stays arcade bank 0. Two Outcome-C triggers are met simultaneously: "the palette producer is not invoked after a colbank transition" and "expected CRAM values do not result" / "another exact existing-system dependency prevents the authorized mapping." Correcting this would require inventing a new re-load trigger after the colbank transition (explicitly forbidden by this task) or modifying `0x059AD4`/`0x045DAE` (beyond the authorized renderer + `3ba64` boundary → STOP). Per Outcome C: reported and STOPPED; not redesigned.

## 18. Explicitly deferred defects (out of scope, untouched)
Score values `00`, missing `UP`/`GH`/incomplete `HIGH SCORE`, extra zeros, far-left vertical sprite, sprite positions, missing/extra sprites, item-screen completeness, gameplay-start exception, gameplay sprites, decay `0x05607C`, PC080SN, text clearing, title-logo completeness, scroll, audio, real-hardware, broader palette allocation, generic all-banks solution.

## 19. Open/Closed Issues Impact
- **OPEN-006 (sprite/high-bank palette mapping deferred):** NOT closed. New proven limitation recorded: the sprite palette bank for a screen (e.g. header bank 48) is loaded into palette RAM through `0x03BA64` while `sprite_ctrl_shadow` is still 0 (before the colbank control write), and is not re-loaded after the colbank transition; the live per-colbank update flows through `0x059AD4` (`d0`=effective bank, gated `<4`). A current-shadow-keyed single-producer window cannot align. Any real fix must reconcile producer invocation timing with the colbank control write (and likely span `0x059AD4`/`0x045DAE`), which is beyond a bounded single-producer change.
- **OPEN-024 (PC090OJ subsystem incomplete):** unchanged; renderer geometry/identity remains correct (Build 0142). Not closed.
- **OPEN-001 (title/attract graphics):** context only; header colour remains a known open defect.
- **OPEN-002 (sequential build naming):** Build 0143 used strictly sequential numbering, no letter suffix; rejected 0143 is consumed and the next ROM-producing task uses 0144. Not closed (needs its own 3-consecutive-build closure evidence).
- No issue closed. No new issue opened (this is a facet of OPEN-006).

## 20. KNOWN_FINDINGS impact — Option B (proposed new entry)
Proposed new entry (conservative rating; Tighe/Chad Sr. may adjust):
```
KF-039 — Sprite palette bank is loaded before the sprite-colbank control write, via a different producer than the per-colbank update
Status: ACTIVE | Confidence: CONFIRMED (native producer trace + CRAM dump) | Applicability: BUILD_SPECIFIC (Build 0143 rejected; frontend states 0/1/0,0/1/2,2/0/0,2/2/6) | Rediscovery Hazard: HIGH
Addresses: producer genesistan_palette_hook_3ba64 runtime 0x07186C (arcade_pc 0x03BA64); genesistan_palette_hook_59ad4 runtime 0x0717AE (arcade_pc 0x059AD4); pc090oj_sprite_ctrl_shadow WRAM 0xFF71D2; arcade palette RAM 0x200000 (bank 48 at 0x200600); staged_palette_words 0xFF609E
Finding: In the sampled frontend, 0x03BA64 loads arcade palette banks 0-47 and bank 48 while pc090oj_sprite_ctrl_shadow=0x0000, and is not re-invoked after the shadow becomes 0x0060 (colbank 48). The per-colbank sprite palette update at colbank 48 arrives through 0x059AD4 with d0 = effective arcade bank (e.g. 0x33=51), gated to lines <4. Genesis CRAM lines 0-3 at the item screen therefore hold arcade banks 0-3.
Use as prior: A sprite-palette-line fix cannot be delivered by a single current-shadow-keyed producer (0x03BA64); producer invocation timing is decoupled from the sprite_ctrl colbank write, and the live per-colbank load flows through 0x059AD4. Reconcile producer/colbank timing across producers before attempting a colbank-window CRAM mapping.
Related Issues: OPEN-006, OPEN-024, OPEN-001
```

## Architecture compliance
CONFIRMED. Both changes were pure helper-body arithmetic in arcade-called helpers returning via RTS (no Genesis loop, lifecycle, second VBlank, boot re-entry, scaffolding, or control-flow ownership). No test/diagnostic path was added. The changes were reverted on the Outcome C STOP.

## Statement
No out-of-scope defect was changed. The only target attempted was PC090OJ sprite palette-bank selection; on the proven producer/colbank timing conflict the work STOPPED per Outcome C, and the production source was reverted to preserve accepted Build 0142.
