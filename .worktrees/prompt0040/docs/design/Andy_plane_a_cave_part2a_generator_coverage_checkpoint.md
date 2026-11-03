# Andy — Plane-A Cave Part-2A: Generator Coverage — SESSION-LIMIT CHECKPOINT

**Type:** Documentation checkpoint only. **No production changes. No ROM. Build counter 297 unchanged.**
Baseline: accepted Build 0297.

> **Purpose.** A session limit was hit mid-investigation (Plane-A Cave Part-2A: Genesis generator +
> Build-0297 asset integrity). This file preserves ALL evidence already obtained so none is lost. It does
> NOT restart or extend the investigation. Interpretation items are explicitly flagged as NOT-yet-confirmed.

---

## 1. Current production generator

**File:** `tools/translation/precompute_pc080sn_tile_lut.py`
**Relevant function:** `collect_runtime_gameplay_fg_tiles()` (defined at line 294; docstring "Structurally
derive the Stage 1 FG plane tile codes (Build 0155)").

**Current constants observed (lines 101–106):**

```
FG_SRC_BASE     = 0x0001691C      # line 101
FG_SRC_STRIDE   = 0x000022C0      # line 102
FG_SEG_COUNT    = 16              # line 103
FG_GROUP_COUNT  = 16              # line 104
FG_ROW_COUNT    = 4               # line 105
FG_COLIDX_COUNT = 4               # line 106
```

**Current collector formula (source excerpt, lines ~298–310):**

```python
SRC = FG_SRC_BASE + seg*FG_SRC_STRIDE + group*4; code = ROM_word(block + colidx*2 + row*8).
...
for seg in range(FG_SEG_COUNT):            # line 301
    for group in range(FG_GROUP_COUNT):    # line 302
        src = FG_SRC_BASE + seg * FG_SRC_STRIDE + group * 4
        block = read_u16_be(maincpu, src + 2)          # metatile pointer = entry word1
        for colidx in range(FG_COLIDX_COUNT):
            for row in range(FG_ROW_COUNT):
                addr = block + colidx * 2 + row * 8
                codes.add(read_u16_be(maincpu, addr) & 0x3FFF)
```

So the collector enumerates `seg ∈ [0,16)` (stride `0x22C0`) × `group ∈ [0,16)` (×4), reading each entry's
`word1` as the metatile pointer and expanding tile words from it.

The generator also has a **separate** attr-based path: `RUNTIME_GAMEPLAY_DESC_TABLE = 0x3951C` (line 85),
`ATTR→SCENE` map with `0x0003 → SCENE_GAMEPLAY_CAVE` (line 89), and `collect_runtime_gameplay_sources()`
(line 249) walking `0x3951C → source blocks 0xD11C..0xF91C` (outdoor) / `0xF91C/0x1011C` (attr-0x0003 cave).
Part 1 (corrected) proved the attr-0x0003 model is a DIFFERENT/later cave, NOT the Stage-1 demo cave.

---

## 2. Dimensional interpretation (working root-cause hypothesis — NOT yet fully confirmed)

Part 1 / 1B proved the original arcade Plane-A source address has THREE independent dimensions:

```
source = 0x1691C
       + strip_table    * 0x22C0
       + level_segment  * 0x40
       + group          * 4
```

The current collector's `seg * 0x22C0` loop enumerates the **16 STRIP TABLES** despite the variable being
named `seg`. The independent **`level_segment * 0x40`** dimension **does not appear** in the observed
collector formula — it is effectively pinned at `level_segment = 0`.

**Consequence (hypothesis, pending final source audit):** the collector captures Stage-1 **segment-0** FG
tiles across all 16 strips, and later segments' tiles only where they coincide with segment-0 data.

---

## 3. Current LUT observations

**File:** `build/pc080sn_tile_vram_lut.bin` — 32768 bytes = 16384 big-endian u16 entries, indexed by arcade
tile code (domain `0x0000..0x3FFF`); value = assigned Genesis VRAM tile slot; `0` = absent/no pattern.

**Observed representative mappings (present):**

```
0x0070 -> 0x0077
0x00BD -> 0x003C
0x00C2 -> 0x0041
0x010B -> 0x0054
0x0411 -> 0x00DC
0x040E -> 0x00D9
0x041B -> 0x00E6
```

**Observed ABSENT (LUT = 0):**

```
0x07FC -> 0x0000
0x0800 -> 0x0000
0x0806 -> 0x0000
0x0020 -> 0x0000   (0x20 is the blank/space tile; its 0 is expected, not a defect)
```

---

## 4. Proven cave metatile coverage result

**Metatile 0x243C** (Part-1B arcade oracle; deeper-cave/floor; collision classification `0x0001`), 16
graphics words at `+0x00..0x1E`:

```
0x07FC 0x0091 0x0092 0x0093
0x07FD 0x0095 0x07FE 0x0097
0x07FF 0x0800 0x0801 0x0802
0x0803 0x0804 0x0805 0x0806
```

**Observed missing-from-current-LUT for metatile 0x243C (complete session set):**

```
0x07FC 0x07FD 0x07FE 0x07FF 0x0800 0x0801 0x0802 0x0803 0x0804 0x0806
```

(The remaining words `0x0091 0x0092 0x0093 0x0095 0x0097` were present — they coincide with segment-0
graphics; `0x0805` was present.)

**Candidate rope / deeper-cave metatile observations (recorded WITHOUT claiming rope ownership):**

- `0x2B08`, `0x2B48`, `0x2B88`: all 16 tile words = `0x0020` (blank/space) in the ROM. These metatiles are
  therefore currently blank-filled; no distinctive rope graphics tile identities were proven from them. Rope
  single-cell ownership remains NOT PROVEN (the Stage-1 demo GAME-OVERs at ~segment 6 before the rope).
- Reference locations (generator-walk coordinates, `strip,group`): `0x2B08` at seg 5 (site 6,83);
  `0x2B48` at seg 5/6 (6,84 / 7,109 / 12,88); `0x2B88` at seg 5/6 (9,110 / 12,87 / 14,89).

---

## 5. Correct per-segment audit already performed

Using the **full** arcade addressing `0x1691C + strip*0x22C0 + level_segment*0x40 + group*4`, expanding each
entry's `word1` metatile pointer to its 16 tile words, and counting nonblank tiles with `LUT == 0`
(excluding the `0x20` blank tile):

| level_segment | unique tiles | missing (LUT=0, excl 0x20) |
|---|---|---|
| 0 | 49  | 0   |
| 1 | 125 | 18  |
| 2 | 237 | 124 |
| 3 | 333 | 291 |
| 4 | 210 | 121 |
| 5 | 89  | 21  |
| 6 | 240 | 133 |

**524** distinct later-segment-only (segments ≥1) nonblank tile codes were found **missing** from the
current LUT. The generator's current segment-0-equivalent walk (`level_segment` pinned at 0) reaches
**NONE** of that later-segment-only missing set (verified: intersection = empty).

Sample of segment-5 missing set (includes the metatile-0x243C floor family): `0x7FC 0x7FD 0x7FE 0x7FF 0x800
0x801 0x802 0x803 0x804 0x806 0x807 0x808 0x809 0x80A 0x80B 0x80C …`.

The complete 524-code missing list was produced in-session from `build/regions/maincpu.bin` +
`build/pc080sn_tile_vram_lut.bin`; it is reproducible from those two inputs with the addressing above (no
separate evidence file was written — this checkpoint records the method and the aggregate counts so it can
be regenerated exactly).

---

## 6. Current interpretation (NOT proven fact — flagged as interpretation)

The evidence **strongly suggests** `collect_runtime_gameplay_fg_tiles()` models the correct strip-source
FAMILY (`FG_SRC_BASE = 0x1691C`, stride `0x22C0`) but **omits the independent `level_segment * 0x40`
dimension**, pinning it at segment 0.

If confirmed, this causes later Stage-1 FG graphics to be absent from the generated LUT except where tiles
are shared with segment-0 data. This is consistent with the observed symptoms:

- correct map geometry;
- correct collision (collision comes from metatile `+0x22`, produced natively at runtime — independent of
  the tile-pattern LUT);
- **some** cave tiles displaying (the segment-0-shared ones);
- deeper/later cave graphics being wrong/blank.

**This root cause is NOT yet marked fully confirmed.** Final confirmation requires the remaining
production-source audit in §7.

---

## 7. Remaining proof before any implementation / build decision

1. **Verify no other current generator path supplies the omitted later-segment FG tile codes** — audit
   `collect_runtime_gameplay_sources()` (0x3951C attr path), `collect_block_write_sources()`, the
   `SCENE_GAMEPLAY_CAVE` tile-set merge (lines ~711–725), text tiles, and any preload/residency manifest, to
   prove the 524 codes are truly absent from ALL generated tile sets (not just the FG collector's output).
2. **Prove the native Plane-A consequence of `LUT = 0`** — confirm what the native producer emits for a tile
   whose LUT entry is 0 (blank slot vs. fallback), i.e. that LUT=0 actually manifests as wrong/blank cave
   graphics at runtime.
3. **Compute the corrected semantic tile set and the VRAM/residency budget/partition required** — the 524
   additional codes (plus existing) must fit the Genesis VRAM tile budget; determine residency
   partition/scene-set changes needed before proposing a fix.

These are the remaining implementation-boundary checks. **No implementation is authorized by this
checkpoint.**

---

## 8. Deferred / frozen items

- **Plane B:** out of scope.
- **Collision:** currently accepted correct and frozen (out of scope; produced natively from metatile +0x22,
  not from the tile LUT).
- **Missing destructible cave-entrance block:** STILL DEFERRED and recorded (OPEN-001/017).
- **Rope single-cell ownership:** NOT PROVEN (candidate metatiles 0x2B08/0x2B48/0x2B88 are blank-filled).
- **No production fix attempted.**

---

## 9. Provisional first-divergence (for the resumed task, not a final verdict)

Leaning toward **Part-2A verdict B** — "generator models the right source family but omits cave tile codes"
— specifically the omission of the `level_segment * 0x40` dimension, making segments 1–6 FG tiles absent
from the LUT except where shared with segment 0. This remains provisional pending §7.1's full-generator
audit (to rule out A/D and confirm no other path supplies the codes).

**Open/Closed Issues impact:** touches OPEN-001/018 (native FG/map completeness) and OPEN-017 (FG source
divergence). No issue opened or closed by this checkpoint. **KNOWN_FINDINGS:** no change written; a
prospective finding (generator omits the Stage-1 `level_segment` dimension) is a candidate pending §7.

---

**Evidence preserved:** YES. **Production source changed:** NO. **ROM produced:** NO. **Build counter:** 297
unchanged. **Missing cave block deferred:** YES. **STOP triggered:** NO.
