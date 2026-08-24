# Andy — Build 0301: Live Plane-A VRAM Owner — STEP 1 instrument ready (capture pending)

**Type:** Targeted runtime proof. Baseline: Build 0300. **No ROM yet — the decisive fix requires the one
interactive capture (STEP 2, Tighe plays); STEP 3 fix+build follows.**

## 1. Ground truth (incorporated)
Cave = segments **1→2→3**, tm0=0, selector=0; page pointer `050F6C→6D→6E`; segment ≠ scene. The 4/5/6
assumption is abandoned. Prior over-claim (sprite DMA definitely overwrites cache B) is **withdrawn**: the
sprite SAT/pattern path is record-based (`record*4+1024`, NATIVE_SAT_MAX=80 → 1024..1343) and the per-frame
tile-DMA worklist is capped at 12 — so sprites reaching cache B (1344+) is **not proven**. The owner must be
observed, not inferred.

## 2. STEP 1 — decisive automatic instrument (built + validated)
`tools/mame/scripts/genesistrace.lua` extended (durable tool, no /tmp):

- **Semantic route** (stable arcade workram, `a5=0x00FF0000`): segment `0xFF013E`, tm0 `0xFF1386`, selector
  `0xFF10A8`, page `0xFF10C6`, strip `0xFF10CA`, group `0xFF10CC`, plus native `tileset_id`/`scene_id`
  (every residency change logged). Compares Genesis route to the arcade 1→2→3 / page 6C/6D/6E ground truth.
- **VDP VRAM access:** `:gen_vdp.spaces["videoram"]` is readable from Lua (confirmed) → the detector polls the
  actual VRAM pattern bytes, catching **both** CPU writes and DMA (a port tap would miss DMA).
- **Decisive detector `sample_plane_a_ownership()`** (every 4 frames, gameplay scene only): scans
  `staged_fg_buffer` (0xFF50E4, 2048 Plane-A name words); for each **already-displayed cell whose name word
  is STABLE** across samples, it fingerprints the referenced VRAM tile slot and fires
  **`LIVE_PLANE_A_PATTERN_OVERWRITE`** when that pattern changes underneath the stable cell — i.e. exactly the
  task's acceptance criterion ("an unrelated writer modified a VRAM pattern slot while a live Plane-A name
  word still references it"). Each event logs slot, cell, name word, old/new fingerprint, seg/page/tileset,
  and an **owner correlation**: `RESIDENCY_RELOAD` (tileset_id just changed), `SPRITE_RANGE` (slot 1024–1535),
  or `OTHER`. Normal scrolling name-word churn is deliberately excluded (it's not the defect).

**Validation (Build 0300, headless):** loads clean (`plane_a_vram ready`, 0 Lua errors); reaches gameplay
(tileset 0→1, segments 0→1→2→3); **0 `LIVE_PLANE_A_PATTERN_OVERWRITE` on correct outdoor gameplay** (no false
positives); 859% speed (smooth for interactive play). The instrument is silent when graphics are correct and
will fire in the cave if/when an already-visible cell's pattern is overwritten.

## 3. STEP 2 — one interactive playthrough (Tighe)
The attract demo only reaches segment-3 outdoor; the cave interior needs real play. Run Build 0300
interactively (window + logger, runs until you quit):

    cd apps/rastan-direct
    ../../tools/mame/run_genesis_trace_wsl.sh ../../dist/rastan-direct/rastan_direct_video_test_build_0300.bin

Then just **play normally into the cave, through it, climb the rope, exit, and quit MAME.** No pausing,
standing still, hotkeys, or scripted moves — the logger captures automatically. Output lands in
`build/mame/home/genesistrace/genesis_exec_{trace.log,summary.txt}`.

## 4. STEP 3 — classify + fix + Build 0301 (after capture)
From the log I read the FIRST `LIVE_PLANE_A_PATTERN_OVERWRITE` (or, if none, a `NAME_WORD` anomaly) and its
`owner`:
- **owner=RESIDENCY_RELOAD → CASE A:** the Build-0299/0300 per-segment residency loader repurposes slots
  while live Plane-A cells still reference them → fix the slot-lifetime/ownership (not another preload).
- **owner=SPRITE_RANGE → CASE B:** measure the real sprite destination span and separate the VRAM ownership
  partition (don't assume all of 1024–1535 is needed).
- **owner=OTHER → CASE C:** identify that exact writer and correct the conflicting ownership.
- **name word itself mutating on a should-be-stable cell → CASE D:** trace the first incorrect native
  producer write.

The smallest correct fix supported by the evidence is applied; streaming is used only if the trace proves the
live working set genuinely needs it. Then Build 0301 via the normal release path (GATE_PASS), with a
re-capture proving the overwrite no longer occurs.

---
**Interactive Build-0300 cave capture completed:** NO — instrument built + validated; awaiting Tighe's one playthrough (STEP 2)
**Genesis route observed:** headless attract reaches seg 0→1→2→3 outdoor; cave needs play
**Expected route:** 1 → 2 → 3
**Route matches arcade:** PENDING capture
**Plane-A name word changed / Referenced VRAM pattern changed / FIRST divergence / Failure classification:** PENDING capture (detector ready)
**Exact VRAM slot / Exact writer / Residency reload involved / Sprite DMA involved / Actual measured sprite destination range / Live Plane-A slot overwritten:** PENDING capture
**Root cause:** to be read from the first `LIVE_PLANE_A_PATTERN_OVERWRITE` owner
**Fix / Streaming cache required:** determined by the proven owner (smallest correct fix)
**Stale/title VRAM cleanup included:** only if part of the proven fix
**Rope restored:** PENDING
**Missing cave block fixed:** NO · **deferred:** YES
**Plane B changed:** NO · **Collision changed:** NO
**Build 0301 produced:** NO (pending capture → classify → fix)
**ROM / SHA-256 / Gate:** none yet
