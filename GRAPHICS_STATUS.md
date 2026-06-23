# GRAPHICS_STATUS.md

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
