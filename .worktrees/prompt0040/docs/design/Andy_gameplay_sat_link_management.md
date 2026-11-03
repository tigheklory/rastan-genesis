# Andy — Gameplay PC090OJ SAT-Link / Represent Management — STOP (D: wrong boundary), NO BUILD

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `03507f4`, clean. Working candidate Build 0162 (`7bcb3179…`, counter 162,
opcode_replace 137, coverage 0x1820AC). Accepted build still Build 0160 pending Tighe visual acceptance. **No
source/spec/tool/ROM edit, no build.** OPEN issue: OPEN-017.

## 2. Prior sprite-path ownership summary
No raw arcade PC090OJ bypass (0xD00000 writes = 0); object_ram has 24 drawable gameplay records via hooks;
represented=6 (F560)/10 (F533); prior pass reported a "corrupt SAT link chain" as the flicker cause.

## 3. Title known-good SAT path
Title F=100: reachable chain (follow links from slot 0) = **15 entries, slots 0..14, clean ascending chain
01→02→…→0E→00**, tiles 0x400-0x438 (title logo), pal2 pri1. Valid.

## 4. Gameplay object_ram/candidate state
object_ram has 24 drawable-code records (codes 0x2A/0x2B/0x2C/0x2D/0x31/0x39/0x46/0x48, 0x3E8-0x3EF) at gameplay
positions. These are the real gameplay objects and reach object_ram via the hooks.

## 5-6. Link-chain invariants — the chain is VALID (prior "corrupt" claim corrected)
Following links from slot 0 at gameplay F=560: **slot0→6→7→8→13→14→00 = a VALID 6-entry chain** (no cycle, clean
terminator, 6 reachable = represented_count 6). The "duplicate links" seen before (s1:06, s5:06, s12:0D) are
**UNREACHABLE stale slots** the VDP never renders. So invariants 1-4,9 PASS for the reachable list. The failing
invariant is **#5/#7: reachable entries are stale, not the current drawable records** (see §7).

## 7. First bad "write"/failed invariant — NOT a link write; the represent TRANSITION
The 6 reachable gameplay SAT entries are **STALE TITLE-LOGO sprites** (tiles 0x400, 0x418, 0x41C, 0x420, 0x434,
0x438 at Y=0x78/0x88, X=0x110-0x198) — a decayed subset of the title's 15 — **NOT** the 24 gameplay object_ram
records (codes 0x2A/0x3E8…). So the represent engine **never activated the gameplay records** and never fully
deactivated the title records. First failed invariant: "each reachable/represented SAT entry corresponds to a
current drawable object record" — the represented set is stale title sprites.

## 8. Represented-count analysis — vdp_prepare_sprites runs sporadically at gameplay
`vdp_prepare_sprites` writes `staged_sprite_active_count` every call; runtime tap: it runs on only **~11 of ~60
gameplay frames** (F540=NO, F550=NO, F559=YES). So the represent/SAT engine (`process_candidates` → sync →
activate/deactivate) is **not invoked every VBlank during gameplay** — the SAT is largely frozen at the title
bootstrap set and only sporadically/partially updated (represented_count written 7× over F530-560). That
sporadic partial maintenance of a stale set is the flicker, not link corruption.

## 9. Slot reuse / unlink analysis
The reachable chain is internally consistent (valid unlink/relink for the operations that DO run). The stale
unreachable slots (s1-5,s9-12) retain leftover link bytes but are not rendered. No unlink bug proven in the
reachable list.

## 10. Head/terminator analysis
Head=slot 0, terminator=link 0. Both correct in title and gameplay reachable chains. No head/terminator bug.

## 11. State-causality answers
1. **What should exist?** Every VBlank, the represent engine should run and the reachable SAT should hold the
   current drawable gameplay records (Rastan/enemies), not stale title sprites.
2. **Which code?** `vdp_prepare_sprites`/`process_candidates`/`sync_record_from_mirror` — but they must be
   CALLED every gameplay VBlank, and must transition off the title set onto the gameplay records.
3. **Why not?** (a) `vdp_prepare_sprites` runs only ~18% of gameplay frames (a VBlank/prepare-scheduling gap),
   and (b) even when it runs the reachable SAT stays on stale title records — the gameplay records (22-37) are
   not activated. The SAT LINK chain itself is valid, so link management is the WRONG boundary.

## 12. Readiness classification: **D** (wrong boundary — SAT link chain is valid) — STOP
The staged-SAT link chain is valid (reachable list is a clean chain in both title and gameplay). The sprite
invisibility/flicker is NOT a link-management bug; it is caused by (1) `vdp_prepare_sprites` not running every
gameplay VBlank and (2) the represent transition never activating the gameplay object records (the reachable SAT
holds stale title sprites). Neither is a bounded SAT-link-write fix; both are upstream (VBlank/prepare
scheduling + represent-transition), and pursuing them touches the rendering loop / prepare invocation, out of
this task's SAT-link-management scope. Not A/B (no bounded link bug — the chain is valid). **STOP, no build.**

## 13-19. (no build)
Exact source change: NONE. No candidate produced. Collision unchanged (WRAM 0xFF1E00 empty). No regression run.

## 20. Open/Closed Issues Impact
OPEN-017 advanced + prior conclusion CORRECTED: the gameplay staged-SAT link chain is **valid** (reachable
slot0→6→7→8→13→14→term); the earlier "corrupt link chain" bytes are unreachable stale slots. The real defect is
two-fold and upstream of link management: (a) `vdp_prepare_sprites` runs only ~11/60 gameplay frames (VBlank/
prepare-scheduling gap), and (b) the represent engine never activates the 24 gameplay object_ram records — the
reachable SAT holds stale TITLE sprites (tiles 0x400+). Next: analyze WHY `vdp_prepare_sprites` isn't called
each gameplay VBlank and why the gameplay records don't activate (process_candidates/sync path), NOT the SAT-link
writer. Not closed.

## 21. KNOWN_FINDINGS impact
Option A — no new finding indexed. Candidate: "gameplay PC090OJ SAT reachable chain is valid but holds stale
title sprites; vdp_prepare_sprites runs only ~18% of gameplay VBlanks and the gameplay object records are never
activated."

## 22. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (Build 0162) +
static source. Did not touch collision, selector, FG_SRC, palette, PC080SN, player/camera/scroll, D00298,
Exodus, audio; no forced sprites/tiles; no second renderer. Arcade is the reference.
