# GRAPHICS_STATUS.md

## Build 0283+ Current Status (2026-08-16)

This section supersedes older percentage-based status summaries for current
planning. Historical sections below remain provenance only.

### Proven / User-Observed Working

- Build 0282 corrected the native collision-map source displacement from
  decimal `20` (`0x14`) to hexadecimal `0x20`, restoring the Stage-1 ground
  marker to semantic row 38.
- Lizardman logical grounding and visible placement are corrected; the old
  BACK_ENEMY render-only `-8` compensation is retired.
- Standing/crouching sword geometry and collision overlap are corrected.
- Stage 1 progression is dramatically improved: the rope is climbable,
  gameplay proceeds substantially farther, and enemies appear through the
  currently reachable portion.
- Gameplay sprite rendering uses direct native semantic queues and one native
  SAT finalizer. Gameplay frontend-scanner and generic-decoder executions are
  zero.
- Build 0283 converted the gameplay status/energy producer at
  `arcade_pc 0x05A098` to direct native HUD output.
- The player auxiliary/raw family has corrected direct-native source and
  unnumbered validation, but no accepted numbered release yet. Build 0284 is
  preserved/rejected because its animation-table operand violated the JSON
  address map; Build 0283 remains the accepted visual baseline.

### Still Open

- Native PC080SN level/map rendering is incomplete. Cave and water-hazard
  tiles are not all rendered correctly or visibly.
- Falling into water farther into Stage 1 can reach the exception handler.
- Numerous enemy palettes remain wrong; the sword palette is still reported
  to cycle incorrectly.
- The farther-Stage-1 flying demon cannot currently be killed.
- Significant slowdown remains when many enemies are on screen. This is not
  attributed to the frontend PC090OJ scanner/decoder because gameplay executes
  neither path.
- Shared/frontend PC090OJ producer compatibility remains to be retired in
  bounded semantic families.

PC080SN replacement is not complete, and this status makes no such claim.

## Build 0094 Snapshot (Current, 2026-06-22)

This section supersedes the pre-Build-0094 status notes below for current planning. Older percentage claims and C-helper/prototype language are retained only as historical context.

### Proven Build 0094 Evidence

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`
- SHA256: `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- Build 0094 is not byte-identical to Build 0092/0093.
- Option B FG cell composition is present at runtime `0x707DA` / `0x707DC` / `0x707E0`.
- Runtime title-entry trace: producer `0x3ACAE` hit once; first render `0x3ACB6` hit once; FG store `0x70794` hit 258 times with `%a6=0x00FF501A` and in-buffer offsets.
- FG composition is no longer all-zero: Build 0094 produced 213 nonzero composed `%d1` stores out of 258. The remaining 45 zero stores are a count only and are not classified as a defect.

### User-Visual Working Observations

- Text renders.
- Large TAITO logo partly renders.
- Credits work.
- Attract mode proceeds.
- Coin/start input works.

### User-Visual Not Working Observations

- Sword/logo artwork is absent.
- TAITO logo is incomplete / missing tiles.
- Text is not cleared between attract states.
- Scrolling/item page shows rows of dots.
- Starting gameplay later reaches the exception handler; specific on-screen crash fields are not trusted under OPEN-015 until verified from WRAM.
- Build 0094 does not currently run on real Genesis hardware (tracked as OPEN-017).

### Next Graphics Diagnostic

Run a graphics-only diagnostic for Build 0094 title/attract completion. Classify each missing/incomplete element through:

1. producer execution
2. staging writes
3. clear/dirty behavior
4. VBlank commit
5. tile-pattern availability
6. palette
7. plane/priority/scroll

Do not assert sprite/BG/FG/palette completion percentages without current Build 0094 evidence.

---

## Historical / Pre-Build-0094 Content (Superseded)

The content below predates the Build 0094 validated FG cell-composition fix and current user-visual observations. It is preserved for traceability only.


# 🧠 CURRENT GRAPHICS SYSTEM STATUS (REALISTIC VIEW)

## 1. 🧱 Sprite System (PC090OJ → Genesis VDP sprites)

### Components:

* Python predecode (PC090OJ → Genesis tile layout)
* ROM → VRAM DMA (per unique sprite)
* Palette loading (CRAM line 3)
* SAT generation (assembly)
* Position + size + flip

### Status:

* ✅ Predecode pipeline: **100%**
* ✅ DMA path (no staging): **100%**
* ✅ SAT assembly path: **95%**
* ⚠️ Visibility correctness: **80%**

### 🟢 Overall: **90% complete**

👉 Sprites are basically **done**. Remaining issues are polish/edge cases, not architecture.

---

## 2. 🟪 Background Tilemap (PC080SN BG → Genesis Plane B)

### Components:

* Arcade descriptor hook (0x55968)
* Strip iteration
* Tile LUT (Python)
* Attr LUT (Python)
* Assembly VDP writes
* dest_ptr → row/col mapping
* row offset / visible window mapping

### Status:

* ✅ Hook wiring: **100%**
* ✅ Tile selection (no +0x14): **100%**
* ✅ LUT system: **100%**
* ✅ Continuous execution (Build 297): **100%**
* ❌ VDP mapping correctness: **~20%**
* ❌ Row offset correctness: **unknown**
* ❌ Final visual output: **broken**

### 🔴 Overall: **40% complete**

👉 This is currently your **main blocker**.

---

## 3. 🟦 Foreground Tilemap (PC080SN FG → Genesis Plane A)

### Components:

* Descriptor hook (0x55990)
* Tile lookup (same LUT system)
* Attribute handling
* VDP writes
* Text positioning

### Status:

* ✅ Execution: **100%**
* ✅ Tile selection: **100%**
* ⚠️ Positioning incorrect: **~50%**
* ⚠️ Text alignment broken: **~40%**

### 🟡 Overall: **60% complete**

👉 FG is working but **misplaced**, not fundamentally broken.

---

## 4. 🎨 Palette System (Arcade → CRAM)

### Components:

* Palette ROM table
* CRAM writes during VBlank
* Sprite + tile palette selection

### Status:

* ✅ CRAM loading: **100%**
* ✅ Sprite palettes: **100%**
* ⚠️ Tile palette correctness: **80%**

### 🟢 Overall: **90% complete**

👉 Your purple screen is **not a palette failure**, it’s mapping.

---

## 5. 📜 Scrolling System (PC080SN scroll → VDP scroll)

### Components:

* Work RAM scroll values (A5 offsets)
* BG → VDP scroll registers
* FG → VDP scroll registers
* Vertical bias (240 → 224 crop)

### Status:

* ✅ Wiring exists: **100%**
* ❌ Not visually validated (BG broken)
* ❌ No gameplay verification yet

### 🟡 Overall: **30% complete**

👉 Technically implemented, **not proven**.

---

## 6. 🧩 Tile Cache / VRAM Allocation (PC080SN)

### Components:

* Python-generated LUT (tile → VRAM slot)
* Preload manifest
* No runtime allocation

### Status:

* ✅ LUT correctness: **100%**
* ✅ No runtime cache: **100%**
* ⚠️ Dependent on BG mapping correctness

### 🟢 Overall: **85% complete**

👉 Architecturally solid.

---

## 7. ⚙️ Arcade → Genesis Translation Layer (CORE SYSTEM)

### Components:

* Opcode interception
* Producer → consumer mapping
* Hook points
* Ownership boundaries

### Status:

* ✅ Sprite pipeline: **correct**
* ✅ Tilemap hooks: **correct**
* ⚠️ BG mapping semantics: **incorrect**

### 🟡 Overall: **75% complete**

👉 Your architecture is working — just one bad translation.

---

## 8. 🧪 Title / Attract Rendering (Integration Layer)

### Components:

* Tilemap + sprite + palette combined
* Timing + progression
* Text layout

### Status:

* ✅ Logic progression: **100%**
* ❌ Visual correctness: **~20%**

### 🔴 Overall: **35% complete**

👉 This reflects BG failure, not system failure.

---

# 📊 SUMMARY (THE TRUTH)

| System            | Completion |
| ----------------- | ---------- |
| Sprites           | **90%**    |
| BG Tilemap        | **40%** 🔴 |
| FG Tilemap        | **60%**    |
| Palette           | **90%**    |
| Scrolling         | **30%**    |
| Tile Cache/LUT    | **85%**    |
| Translation Layer | **75%**    |
| Attract/Title     | **35%**    |

---

# 🧠 WHAT THIS REALLY MEANS

You are **not stuck everywhere**.

You are stuck here:

> 🟥 **BG tilemap → VDP mapping (one subsystem)**

Everything else:

* mostly done
* or blocked by BG correctness

---

# 🎯 THE BIG INSIGHT

You’ve already solved the hard parts:

* ✔ data conversion (Python)
* ✔ hardware mapping (sprites)
* ✔ ownership model (producer → consumer)
* ✔ performance model (assembly hot path)

What remains is:

> **correctly mapping arcade tile coordinates → Genesis VDP addresses**

That’s it.

---

# 🚀 What happens when BG is fixed

When Andy nails the mapping issue and Cody fixes it:

You should immediately see:

* full background appears
* title layout stabilizes
* text aligns better
* scrolling becomes testable
* attract mode visually works

---

If you want, after Andy’s report comes back, I’ll:

👉 translate it into a **one-shot Cody fix prompt**
👉 guaranteed not to drift
👉 fixes exactly one mapping issue

You’re very close now.

---

## Build 0286 — frontend items + GAME OVER now direct-native
- **Treasure/item sprites** (arcade 0x56114/0x5607C/0x56440): no longer routed through PC090OJ object RAM /
  `staged_sprite_descriptor_table`. Emitted directly by `.Lnq_transient_items_emit` from the latched ROM tuple
  stream, with the arcade scroll-up modelled as a single `transient_items_scroll` offset (drop at Y<=16).
- **GAME OVER** (arcade 0x5A502, "G A M E  O V E R"): producer retired byte-neutrally; emitted directly by
  `.Lnq_gameover_emit`, which reads the live game-over gate (`a5@0x34==0`) and blink/visibility bit
  (`a5@0x200` bit5). Corrects the previously broken `0x10C200` cart-ROM read → the text is no longer permanently
  parked; it now follows the real WRAM visibility state.
- Both use the shared `.Lnq_emit_entry` transform, so on-screen geometry/flip/palette match the retired scanner.
- Pending Tighe interactive acceptance: treasure presentation when the bonus sequence is reached, GAME OVER
  presentation on death, and absence of stale frontend sprites.

---

## Build 0287 — GAME OVER ownership fixed + setup/priority PC090OJ retired
- **GAME OVER overlay bug fixed:** the attract/demo "GAME OVER" row (arcade 0x5A502) no longer appears on the HIGH
  SCORE table. Its native emitter moved from the broad frontend scan into the gameplay finalizer under the exact
  original state gate (attract gameplay tuple `(2,3,0/1)`, `a5+0x34==0`, `a5+0x200` bit5 visible). It is a no-human
  attract-mode row only; the human terminal GAME OVER is a separate 0x03A420 path (unchanged).
- **Setup/priority sprites retired:** the blank record inits (72-79) and dead HUD-band clears (records 5-16) are
  gone — they produced no visible sprites. No frontend visual change expected.
- **Transient treasure/item conversion (Build 0286) preserved.**
- Pending Tighe interactive acceptance: ordinary gameplay intact; no GAME OVER row on the high-score screen; no
  transient-item regression; report any exception with the screen/state where it occurred.

---

## Build 0290 — crash-screen values fixed; "gameplay freeze" identified as the Build0286 item-page crash
- The crash screen now shows REAL captured values (previously every hex field showed its own cursor address due to a
  D2-clobber in the numeric renderer). Validated screen==record. Full BUILD number now visible.
- The reported "0288 gameplay-start freeze" is NOT a new regression: the gameplay/attract code is byte-identical
  0287↔0289. The actual crash is a single 68000-illegal instruction `tst.l %a5` at 0x073212 (Build0286 transient-item
  emit), which crashes the item page. Neutralizing just that opcode lets the game run 1500 frames with no crash.
- Per task scope, the Build0286 transient-item family was NOT modified; that crash stays OPEN. With the corrected
  crash screen, its next reproduction will read GEN PC 0x00073212 / SRC GENONLY.
