# Andy — Gameplay Sprite Path Ownership (title vs gameplay PC090OJ/SAT) — STOP (C), NO BUILD

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `ed2bc6f`, clean. Working candidate Build 0162 (`7bcb3179…`, counter 162,
opcode_replace 137, coverage 0x1820AC). Repo policy: accepted build still Build 0160 pending Tighe visual
acceptance; analysis uses Build 0162 (palette lines 0-3 populated). **No source/spec/tool/ROM edit, no build.**
OPEN issue: OPEN-017.

## 2. User visual observation
Title/frontend + HUD sprites visible; gameplay Rastan/enemy sprites absent; gameplay shows flickering dot
garbage (like the old title-sprite issue). User suspects a raw arcade sprite path bypassing Genesis staging.

## 3. Working title/frontend sprite path
Title F=100: `represented=15`, `staged_sprite_active=15`, `sat_dirty=0`, `scan_active=1`. staged_sprite_sat holds
15 valid entries (tiles 0x400-0x42C, pal 2, pri 1) with a **clean link chain** (01→02→…→0C, terminating). This
is the known-good PC090OJ staging path: arcade object writes → hooks → mirror/object_ram → candidate →
represent → staged_sprite_sat → `vdp_commit_sprites_vram` (VBlank).

## 4. Gameplay player/enemy sprite path
Gameplay F=560: `represented=6`, `staged_active=6`. **object_ram HAS 24 drawable gameplay records** (codes 0x2A,
0x2B, 0x2C, 0x2D, 0x31, 0x39, 0x46, 0x48, and 0x3E8-0x3EF at gameplay positions Y=0x10/0xE8/0x110, X=0x08-0x110
— real Rastan/enemy/HUD objects), written by the Genesis hooks (0x071Axx/0x071Bxx). So the gameplay objects DO
reach the hooked object_ram. But only **6 of 24** drawable records are represented into the SAT.

## 5. Raw-write / bypass audit — user hypothesis REFUTED
During gameplay (F≥500): **ZERO raw arcade PC090OJ writes to 0x00D00000..0x00D01FFF** (`NONE`). object_ram
(0xFF69B0) is written only by the Genesis PC090OJ hooks (writer PCs 0x071AC6/AC8/ACC/AD0/B28/B6C/BF4/BF6/BFA/BFE
= the emit_slot / family_apply / mirror paths, 484 writes/frame). So gameplay sprites are NOT written through a
raw arcade path — they go through the hooked staging path. **The bypass hypothesis is refuted.**

## 6. Candidate/SAT comparison (Build 0162)
| | title F=100 | gameplay F=560 |
|---|---|---|
| represented / staged_active | 15 / 15 | **6 / 6** |
| object_ram drawable-code records | (title set) | **24** |
| candidate_bitset nz | 0/32 | 0/32 (post-process) |
| SAT link chain | clean 01→02→…→0C | **CORRUPT: 06 06 03 04 05 06 07 08 0D 0A 0B 0C 0D 0E 00 00** |
The gameplay SAT link chain has duplicate links (06 ×3, 0D ×2) and skips (entry 0 → 6), so the VDP follows an
invalid chain → flickering garbage. Between F=533 (represented=10, links `…0A…`) and F=560 (represented=6, links
`…0D…`) the represented set and link chain CHANGE frame-to-frame → the flicker.

## 7. VRAM tile graphics proof
Not the primary break (the SAT/link corruption precedes it). Gameplay sprite tile codes (0x2A, 0x3E8-0x3EF)
would need VRAM pattern verification in a follow-up, but even valid tiles render as garbage through the corrupt
SAT link chain. Deferred (secondary to §10).

## 8. Palette-line proof
Title + gameplay SAT entries reference palette line 2 (pal2). Line 2 is populated (Build 0161/0162). So palette
is NOT the sprite-invisibility cause here.

## 9. Flickering dot ownership
The flickering dots are the **corrupt SAT link chain** (§6): duplicate/skipping links produce an invalid sprite
list that the VDP renders as garbage, and it changes each frame (represented 10→6) → flicker. Not stale-only:
the represent/SAT engine actively re-derives an incomplete + mis-linked set every frame.

## 10. First proven break in the sprite chain
**The PC090OJ represent → staged-SAT stage.** Gameplay objects reach object_ram (24 drawable records, via
hooks, no bypass), but the incremental SAT engine (`.Lpc090oj_sync_record_from_mirror` / `.Lpc090oj_set_link` /
head-insert at slot 0 / `represented_count`) (a) represents only 6-10 of the 24 drawable records and (b) builds
a **corrupted link chain** (duplicate links). The SAT is a linked-list with incremental insert/remove/relink;
for gameplay's churning object set the link management breaks. This is the first break — upstream object_ram is
correct.

## 11. State-causality answers
1. **What should exist?** The 24 drawable gameplay object_ram records should be represented into staged_sprite_sat
   with a valid link chain (like the title's 15).
2. **Which code?** The existing PC090OJ represent/SAT engine (`sync_record_from_mirror`, `set_link`,
   `process_candidates`) — already the owner; no bypass needed.
3. **Why not?** The incremental linked-list SAT management produces an incomplete represented set (6-10 of 24)
   and a corrupt link chain (duplicate/skipping links) for the gameplay object churn.

## 12. Readiness classification: **C** (object exists + reaches staging, but the represent/SAT-link defect is not trivially bounded) — STOP
Not A (no raw bypass to route — refuted). Not B (the defect is not a single bounded SAT field; it is the
incremental link-chain + represent-count management across a churning object set — a deep engine defect). Not D
(the SAT corruption precedes any tile-graphics question and is the proven cause of the garbage). More analysis
of `sync_record_from_mirror` / `set_link` / the head-insert linked-list is required before a bounded fix. Per
"Build-If-Trivially-Bounded", **STOP without build.**

## 13-18. (no build)
Exact source change: NONE. No candidate produced; nothing to preserve/reject. Regression/collision unchanged
(collision WRAM 0xFF1E00 empty, deferred).

## 19. Open/Closed Issues Impact
OPEN-017 advanced: gameplay sprite invisibility is NOT a raw-write bypass (refuted: no 0xD00000 writes;
object_ram populated by hooks with 24 drawable gameplay records). The break is the PC090OJ represent → SAT-link
engine: only 6-10 of 24 drawable records are represented, and the staged-SAT link chain is corrupt
(06 06 … 0D … duplicate/skipping links, changing frame-to-frame) → the flickering-dot garbage. Fix requires a
dedicated analysis of the incremental linked-list SAT management (sync_record_from_mirror / set_link /
represented_count), not a bounded routing/field change. Not closed.

## 20. KNOWN_FINDINGS impact
Option A — no new finding indexed (owner not yet build-verified). Candidate: "gameplay PC090OJ objects reach
object_ram (no raw bypass) but the incremental staged-SAT link engine emits an incomplete/corrupt link chain,
producing flicker garbage instead of Rastan/enemy sprites."

## 21. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (Build 0162) +
static source; arcade is the reference. Did not touch collision, selector, FG_SRC, palette, PC080SN, player/
camera/scroll, D00298, Exodus, audio; no forced/hardcoded sprites or tiles; no second renderer.
