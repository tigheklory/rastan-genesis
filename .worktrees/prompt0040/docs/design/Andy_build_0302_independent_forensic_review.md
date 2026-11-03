# Andy — Independent Build 0302 Forensic Review

**Type:** independent architecture/runtime forensic review. No production change, no ROM, Build 0303
not consumed. Baseline artifact reviewed: `rastan_direct_video_test_build_0302.bin`
(SHA-256 `990644b2…12768e6`, counter 302).

## Verdict summary
- **Speed architecture (boundary-loaded, no per-frame residency): ACCEPT.** Build 0302's removal of
  the Build-0301 per-frame hash/liveness/eviction is correct and is why gameplay is fast. Do not
  restore per-frame residency.
- **Dominant corruption cause: stale name-table slot ownership — CONFIRMED** by generated data.
- **Black/blank regions: intentional Plane-B package drops — expected behavior**, separate from the
  valid-but-wrong corruption.
- **Castle `0xC0ABE0` crash: untranslated raw PC080SN directional-edge writer — identified statically
  (FUN_00055b3c → FUN_00055c4a).** Not dynamically reproduced.

---

## 1. Stale name-table slot ownership — CONFIRMED (primary corruption)

### Representation proof (why a LUT change cannot repair the screen)
Publication writes the **resolved final Genesis name word** to the staged plane buffer, not the
arcade code. `src/tilemap_hooks.s` Plane-B path:
```
bsr  fg_boundary_resolve_b      ; d3 = slot from active LUT
or.w 12(%sp), %d3               ; merge attribute bits
move.w %d3, 0(%a6,%d0.w)        ; STORE final (slot|attr) into staged buffer
```
Once a cell is staged, its value is a **slot index**; changing the LUT afterwards does nothing to it.

### Install proof (no republish)
`fg_boundary_install` (`src/fg_tile_cache.s`) does exactly: check scene/record → read Plane-B Y →
select variant → **clear+rewrite `fg_boundary_active_lut`** → display off → **DMA new patterns into
slots** → display on. **There is no step that rewrites existing staged Plane-A/Plane-B cells or
re-publishes the visible ring.** Both planes are affected identically (both stage resolved slots).

### Data proof (the slots are massively reshuffled every boundary)
From `boundary_packages.bin` (record index table + 16-byte descriptors + map/upload pairs), the
rec0-var0 → rec1-var0 transition:
- **819 of 820 slots** are reused holding a **different pattern identity** (different upload source
  code). e.g. slot 65: pattern src `0x00bd` → `0x0070`; slot 66: `0x00be` → `0x0071` …
- Of **816 arcade codes present in both packages, 815 map to a *different* slot** (only 1 unchanged).

The allocator packs each package **densely from slot 64 with no cross-package stability**, so nearly
every slot changes meaning at every boundary. A staged cell holding slot `S` (published for code X)
instantly renders package Q's slot-`S` pattern Y → **valid Rastan graphics, wrong for that location**.
As the arcade scrolls new columns in and republishes them through Q's LUT, cells become correct →
**exact match to Tighe's GOOD → boundary → wrong → walk → recovery** report. **CONFIRMED.**

### Why this is the compiler regression
Milestone-1B's allocator retained a code's slot across consecutive epochs (tile lifetimes). The
`--boundary-experiment` path discarded that and repacks each package from scratch, guaranteeing the
stale-slot reshuffle. This is a **compiler allocation** defect, not a runtime install defect per se.

---

## 2. Intentional Plane-B drops — expected, explains SOME black cells

`boundary_report.json`: 22 packages carry deliberate Plane-B drops (largest 315), unmapped code →
slot 0 (blank) + a miss counter, never loaded. These produce **blank/black cells**, which are
distinct from the valid-but-wrong corruption. Tighe's separate "black holes" are consistent with
these drops (and with code-0 defaults). **These are not the reshuffle bug.** Plane A never drops.
A dropped code resolves to slot 0 (blank), so drops cannot themselves create valid-but-wrong tiles.

---

## 3. Record / variant / event-reseed timing — CONTRIBUTING (secondary, at event records)

The boundary hook replaces the `addq.w #1,a5+0x013E` at arcade `0x558FE` and installs immediately.
For ordinary horizontal records this is fine. For **event/reseed records (15→16 event 4, 21→22
event 6/7)** the scene reseed that sets the record's Plane-B Y, descriptor cursor and tm0 runs later
via the outer controller (per `Andy_pc080sn_plane_b_static_decoder.md` §3: event 4 → mode 7 →
`0x3A7DA` copies segment 16 into `a5+0x1242` → scene init reseeds). Installing at the increment moment
can read a **pre-reseed Plane-B Y** and pick the wrong variant for records 16/22. This explains
*extra-sharp* corruption specifically at those progression points, layered on top of the pervasive
stale-slot reshuffle. **CONTRIBUTING**, not primary.

---

## 4. LUT plane-independence — NOT a root cause
`resolve_a` and `resolve_b` both index the single `fg_boundary_active_lut` by `code & 0x3FFF`.
Because PC080SN drives both tile layers from **one shared character ROM**, a given code decodes to the
same 8×8 pattern regardless of plane, so a shared code→slot map is semantically correct; attributes
(palette/flip/priority) are merged separately at publication (`or.w 12(%sp),%d3`). No plane-collision
bug found. **UNPROVEN as a cause; architecture is sound here.**

---

## 5. Package DMA source / indexing — correct
Upload pairs are `(representative_code, slot)`; install does `src = code<<5` into
`genesistan_pc080sn_tile_rom`, `dst = slot<<5`, 16 words. The pattern ROM is the shared decoded
character set indexed by code, so `code<<5` is the correct source for that slot's pattern. Spot-checks
of descriptor offsets/counts are consistent. **No indexing/offset/stride bug found.** The corruption
is not a DMA-source defect.

---

## 6. Castle crash `0x00C0ABE0` — untranslated raw PC080SN writer (identified statically)

### Mechanism
On Genesis, `0xC00000–0xC0001F` are VDP ports; a 68k bus write to `0xC0ABE0` is illegal → BlastEm
"machine freeze." On the arcade, `0xC00000`/`0xC08000` are the two PC080SN name-table bases. So the
crash is a **raw arcade PC080SN name-table write that escaped native replacement.**

### The writer
Cody replaced the **forward horizontal** column publication (arcade `0x55904–0x55ab4`, the
`a5+0x10ca/0x10cc` cascade → staged buffer). He did **not** replace the four **directional scroll-edge
column producers** dispatched by `FUN_00055ad6` on `a5+0x10d0` direction bits:
`FUN_00055b28 / FUN_00055b32 / FUN_00055b3c / FUN_00055bb6`, which call `FUN_00055c4a` to write.

`FUN_00055b3c` (arcade `0x55b3c`, **not in remap replace list**) computes:
```
addr = 0xC00000 + (a5+0x10f6 * 4 + a5+0x10f4 * 0x40)   ; stored to a5+0x10f8, then FUN_00055c4a writes
```
The final ROM still contains this raw computation (disassembler prints it in **decimal**:
`0680 00c0 0000  addil #12582912,%d0` at genesis `0x55c60`; sibling `#12615680 = 0xC08000` writers at
`0x557cc/0x55858/0x558f2/0x55ab8/0x55b2e/0x55b46/0x52a52/0x52a74/0x52b6e/0x576aa/0x5a434`). My initial
hex search missed these purely because of the decimal formatting.

`0xC0ABE0 = 0xC00000 + 0xABE0` matches this writer's address form exactly. It fires on directional
(vertical/edge) scrolling — **the castle climb** — and not during early horizontal Stage-1, which is
why early gameplay runs and the castle freezes. The large `0xABE0` offset is consistent with the
producer reading camera/column state (`a5+0x10f4/0x10f6`) that the native horizontal replacement no
longer maintains, so the offset is not bounded to a normal on-screen cell.

### Status
**Raw PC080SN write escaped translation: YES.** Writer: `FUN_00055b3c` → `FUN_00055c4a` (and its three
siblings) on the `0xC00000`/`0xC08000` name tables. **Not dynamically reproduced** (would require
climbing to the castle in Genesis MAME). Static identification is exact enough to act on; a Genesis
watchpoint on the `0xC0xxxx` write can confirm the precise sibling if desired before the fix.

---

## Decision tree

| # | Category | Verdict |
|---|---|---|
| 1 | Stale name-table slot references across package transition | **CONFIRMED (primary)** |
| 2 | Intentional missing Plane-B package codes | CONFIRMED as *expected* blank behavior (not the wrong-tile bug) |
| 3 | Wrong record timing (event reseed 16/22) | CONTRIBUTING |
| 4 | Wrong Y-variant timing (event reseed) | CONTRIBUTING |
| 5 | LUT/code identity flaw | REJECTED |
| 6 | Package binary/DMA indexing bug | REJECTED |
| 7 | Overflow/drop bookkeeping bug | REJECTED (drops resolve to slot 0, cannot make wrong tiles) |
| 8 | Staged-buffer/hardware commit ordering | REJECTED as a cause of the wrong-tile corruption (ordering is fine; the defect is that staged cells are never re-resolved) |
| 9 | Other: untranslated raw PC080SN directional-edge writer | **CONFIRMED (crash only)** |

---

## Build 0303 minimum implementation

**A. Kill the stale-slot reshuffle (primary, compiler-side).** Replace the boundary allocator's
per-package dense repack with **cross-package stable slot assignment**: give each arcade code a slot
that is **retained across every package in which it stays live** (the Milestone-1B tile-lifetime
allocator applied over the package sequence), reassigning a slot only after its code leaves the live
window. Then a staged cell keeps rendering the correct pattern after a boundary because its slot still
holds the same code's pattern, and pattern DMA at each boundary drops to only the genuinely-changed
slots. This preserves boundary-only performance (and reduces DMA). No runtime republish needed if slot
stability is high enough; if residual reshuffle remains for codes that must be evicted, add a
**boundary-only** staged-buffer remap (offline-generated `old_slot→new_slot` per transition) — not a
per-frame pass.
   - Applies to **both** Plane A and Plane B (both stage resolved slots).
   - Pattern-index field mask: `& 0x3FFF` for the code; preserve attribute bits (palette/flip/pri)
     already merged separately — the remap must touch only the slot bits, never the attribute bits.
   - old→new slot mapping is fully offline-derivable (both packages known at compile time).

**B. Fix event-reseed variant timing (secondary).** Install the package for records 16/22 **after**
the scene reseed sets the post-event Plane-B Y / descriptor cursor / tm0, not at the raw increment.
Hook the post-reseed point (outer-controller scene-init completion) for event records, or re-install
once after reseed.

**C. Natively realize the directional-edge producers (crash fix).** Convert `FUN_00055b28 /
FUN_00055b32 / FUN_00055b3c / FUN_00055bb6` (via `FUN_00055c4a`) to the **same native staged-buffer +
LUT publication** used for the horizontal path — arcade semantic decision → native Plane-A/B name
word into the staged buffer, never a raw `0xC0xxxx` write. **No NOP/RTS suppression** (that would
delete the castle's vertical column fills). This is a real ownership extension of the already-native
publication, not a new architecture.

**No per-frame residency. No new tile cache. No sprite/PC090OJ work. No new broad RE.**

---

## BUILD 0303 SHOULD FIX
1. Compiler: cross-package **stable slot allocation** (retention) replacing per-package dense repack — kills the valid-but-wrong reshuffle on both planes.
2. Runtime (only if residual eviction remains): **boundary-only** staged-buffer `old_slot→new_slot` remap, attribute bits preserved.
3. Event-reseed **variant/record timing** for records 16 and 22 (install after reseed).
4. Native realization of the **directional-edge column producers** (`FUN_00055b3c` + siblings via `FUN_00055c4a`) → fixes the `0xC0ABE0` castle crash.

## BUILD 0303 SHOULD NOT TOUCH
1. The boundary-loaded, no-per-frame-residency performance architecture (keep it).
2. PC090OJ sprites, sprite palette banks 49–127, SAT.
3. The shared single-LUT / resolver design (it is correct).
4. Package DMA source/indexing and overflow bookkeeping (correct).
5. Broad Plane-B reachability / terrain-exact / whole-game compiler scope.
