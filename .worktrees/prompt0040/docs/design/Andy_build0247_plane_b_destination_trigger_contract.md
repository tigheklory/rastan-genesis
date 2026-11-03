# Build 0247 — Plane B Destination & Trigger Contract (research; no source/build)

**Agent:** Andy. **Type:** focused Plane B destination/trigger proof.
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0247 / counter 247).
**Authority:** `build/rastan-direct/address_map.json` (segment-membership; **no fixed-offset inference**),
`specs/rastan_direct_remap.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`, Build 0247
source/symbols, arcade opcodes. **Evidence:** `states/traces/build0247_plane_b_dest_20260801/`
(`bgdest`, `bgvert`). `0xC00000` used **only as oracle**. **Builds on:**
`Andy_build0247_native_plane_b_semantic_boundary.md` (source proven — not repeated) and
`Cody_build0247_native_plane_a_no_publish_vertical_routing.md` (the Plane A vertical hooks reused here).

## Native-hardware-replacement acknowledgement (policy §10/§12)

- **Semantic cut retained:** the arcade owns the BG producer counters (`a5@0x10F4/0x10F6`), the ROM source
  (`0x3951C`), and the camera/scroll (`a5@0x10B0`→`a5@0x10EE`). The native tail only reads those and emits
  final Plane B words.
- **Chip tail removed:** no `0xC00000` authority, no `a5@0x10F8` destination cursor, no `staged_bg_tall_buffer`,
  no projector. Proven below: destination column comes from producer counters, **not** the chip cursor.
- **Plane A / collision / rope: untouched.**

---

## 1. Result summary

- **Horizontal destination column PROVEN:** `logical_dest_col = ((a5@0x10F4 & 3)*16 + a5@0x10F6) & 63`.
  Matched **23104 / 23104** tilemap0 writes (fill + gameplay), across source-group transitions
  (`a5@0x10FC` `0x3951C→0x03954C`) and **four real 63→0 column wraps** (`colRange=[0..63]`). Uses **producer
  state only** — `C00000 required: NO`, `a5@0x10F8 required: NO`. X-scroll reconstruction is **unnecessary**
  (X-scroll candidates matched only 3072/5568 of 23104).
- **Physical column = logical column** (64-col ring, full match, no fold).
- **Vertical starvation PROVEN (twin of Plane A):** BG Y-scroll `a5@0x10EE` **==** FG Y-scroll `a5@0x10B0`
  (0 mismatches); BG `visible_top` settles **1→23** (22 crossings) with **0 tilemap0 rows published** at
  every crossing. The BG's 64-row window scrolls into the 32-row Genesis ring with no publisher — exactly
  Plane A, currently masked by the tall projector.
- **Vertical entering-row formulas = Plane A's** (because BG visible_top = FG visible_top):
  increasing `(new_visible_top+31)&63`, decreasing `new_visible_top&63`.
- **Hook = Option B, shared with Plane A:** the no-publication Y-scroll paths `0x055790`/`0x055704` (already
  patched for Plane A) — because `a5@0x10EE == a5@0x10B0`, no BG-specific vertical hook is needed.
- **STOP: not triggered.**

## 2. Part 1 — Logical destination column (horizontal)

**Method (`bgdest.txt`):** tap the tilemap0 tile write `0x055C90`; for every write decode the logical
`(row,col)` from the C-window address as **oracle** and test candidate formulas built from producer/scroll
state; walk right for a long run (F260→3200) to force group transitions and ring wraps.

**Result — one exact formula, 100%:**
```
logical_destination_column = ((a5@0x10F4 & 3) * 16 + a5@0x10F6) & 63     [23104/23104 matches]
```
| candidate | matches / 23104 |
|---|---:|
| `((F4&3)*16 + F6) & 63` | **23104 (100%)** |
| `F6 & 63` | 6592 |
| `((BGx>>3)&0x30 + F6) & 63` | 5568 |
| `((BGx>>3) + F6) & 63` | 3072 |

Representative sequence (fill, X=0): `ocol` 0,3,6,9,12,15 (`F4=0`,`F6`=…) → 18,21,25,28,31 (`F4=1`) →
34…46 (`F4=2`) → 50,53,56,59 (`F4=3`), i.e. `col = (F4&3)*16 + F6` sweeping 0..63.
**Group transitions:** `a5@0x10FC` advanced `0x3951C→0x039522→0x039528→0x03952E→…→0x03954C` (per §-source
proof), `F4` cycling 0..3. **True 63→0 wraps:** captured 4× (F=575 `X=0x1B1`, F=1406, F=2417, F=3018) — the
destination sequence itself demonstrates `…63 → 0` (not inferred from an X range).

**Does producer state already supply the logical column directly?** **YES.** `a5@0x10F4` and `a5@0x10F6`
are arcade-owned producer counters (the ring destination), independent of the chip cursor `a5@0x10F8` and of
`0xC00000`. An independent BG-X-scroll reconstruction is therefore **not required** for the destination
column — a cleaner result than Plane A (which reconstructs from FG X-scroll). The **source** column still
tracks the absolute map position via `a5@0x10FC` (proven in the source doc), so destination (ring) and
source (map) are cleanly decoupled — the dual-axis wrapped map.

- **Physical column formula:** `physical_col = logical_dest_col` (0..63, full-match ring; no folding).

## 3. Part 2 — Vertical entering rows

**Method (`bgvert.txt`):** arcade, **no input**, opening settle. Sample `a5@0x10B0` (FG Y), `a5@0x10EE`
(BG Y), compute BG `visible_top`, and count tilemap0 writes per frame across each BG visible-top crossing.

**Results:**
- **`a5@0x10EE == a5@0x10B0` — 0 mismatches (F250–520).** The BG Y-scroll is the FG Y-scroll, mirrored every
  frame at arcade `0x055B28` (`movew a5@0x10B0, a5@0x10EE`). ⇒ **BG visible_top == FG visible_top.**
- BG `visible_top` **1→23** across 22 crossings (F286–342); `finalBGvtop=23`, `finalBGy=0x0149`.
- **`tm0_writes_this_frame = 0` at every one of the 22 crossings** ⇒ the BG publishes **no** rows during the
  vertical settle. **Vertical starvation confirmed — identical to Plane A.** (The horizontal parallax
  producer `0x055B60`→`0x055B8E` is gated `sel==0` and fed by the *horizontal* delta at half-rate — it does
  not fire on vertical-only crossings.)

**Crossing table (excerpt):**

| F | BG vtop | FG y = BG y | tm0 rows published | entering_row=(vtop+31)&63 | phys=row&31 |
|---:|---:|---:|---:|---:|---:|
| 286 | 1→2 | 0x1F6 | 0 | 33 | 1 |
| 302 | 7→8 | 0x1C6 | 0 | 39 | 7 |
| 323 | 15→16 | 0x187 | 0 | 47 | 15 |
| 342 | 22→23 | 0x14E | 0 | 54 | 22 |

**Direction-complete entering-row formulas** (identical to Plane A, since BG vtop = FG vtop):
- **Increasing visible_top:** `entering_row = (new_visible_top + 31) & 63` (enters ring bottom).
- **Decreasing visible_top:** `entering_row = new_visible_top & 63` (enters ring top).
- **Physical row:** `entering_row & 31`. **Max rows per invocation:** settle ≤1/frame (BG Y step = FG Y step,
  `10DA=3`); general bounded loop `= |Δvisible_top|`, `≤ ceil(|Δ10B0|/8)`.

**A/B/C determination:**
- **A. Existing `0x055C5E` producer supplies every required vertical row: NO** — it publishes 0 rows on
  vertical crossings (starvation proven).
- **B. Separate no-publication hook required: YES**, and — because `a5@0x10EE == a5@0x10B0` — it is the
  **same** no-publication Y-scroll boundary already patched for Plane A (`0x055790` up / `0x055704` down). No
  BG-specific vertical hook is needed.
- **C. Opening settle needs a distinct native call boundary: NO** — the settle rides the same `0x055790`
  no-publish up path (`10B0` drives both planes).

## 4. Hook inventory & address-map / remap table

| Purpose | Arcade PC | Genesis PC | Kind / current treatment |
|---|---:|---:|---|
| **Horizontal/init BG producer** | `0x055C5E` | `0x055E5E` | patched → `genesistan_hook_itempage_strip_blit`→`bg_fill`/`_tall` |
| tilemap0 cell producer | `0x055C7A` | `0x055E7A` | arcade_copy (dest col = `(F4&3)*16+F6`) |
| tilemap0 rebuild / src-advance | `0x055C2E` / `0x055C14` | `0x055E2E` / `0x055E14` | patched (WRAM rebase) |
| BG Y = FG Y mirror | `0x055B28` | `0x055D28` | arcade_copy (`10EE = 10B0`) |
| **Vertical up no-publish (shared)** | `0x055790` | `0x055990` | **patched (Plane A)** → `jmp 0x00070762`; cont. `0x055998` |
| **Vertical down no-publish (shared)** | `0x055704` | `0x055904` | **patched (Plane A)** → `jmp 0x000707B2`; cont. `0x05590C` |
| Plane A up helper | — | `0x00070762` | `genesistan_plane_a_pan_publish_entering_rows_up` |
| Plane A down helper | — | `0x000707B2` | `genesistan_plane_a_pan_publish_entering_rows_down` |
| Transitional tall writer | — | `0x00070F7C` | `genesistan_hook_tilemap_bg_fill_tall` — RETIRE |
| Transitional projector | — | `0x00070138` | `vdp_project_bg_tall_if_dirty` — RETIRE |

Displaced instructions at the shared hooks (already handled by Plane A): up `0x055790: 322d 10da 936d 10ba`
→ helper reproduces `10BA -= 10DA`, `jmp 0x055998`; down `0x055704: 322d 10da d36d 10ba` → `10BA += 10DA`,
`jmp 0x05590C`. Register ownership: full `movem.l %d0-%d7/%a0-%a6` (as the Plane A helpers already do). Adding
a Plane B publication inside these helpers requires no new hook, no new displaced bytes, no new continuation.

## 5. Native Plane B contracts

- **Initialization + horizontal edge (Option A, producer-driven):** at the existing `0x055C5E` producer
  (runtime `0x055E5E`), for each produced strip write final Plane B words **directly** to
  `staged_bg_buffer[(row & 31)][ ((a5@0x10F4&3)*16 + a5@0x10F6) & 63 ]`, tile from the proven `0x3951C`
  source, existing BG attr LUT, set `bg_row_dirty` for the physical row — **bypassing `bg_fill_tall` and the
  tall buffer**. `physical_col = (F4&3)*16 + F6`; no chip decode; no `a5@0x10F8`.
- **Vertical entering edge (Option B, shared hook):** extend the existing Plane A no-publish helpers
  (`0x00070762` up / `0x000707B2` down) to **also** publish the Plane B entering row: same crossed
  `visible_top`, `entering_row = up ? (vt+31)&63 : vt&63`, `physical_row = entering_row & 31`; for each of the
  64 resident destination columns emit the final Plane B word from the `0x3951C` source at the BG column base
  into `staged_bg_buffer`, set `bg_row_dirty`. Because the helper already owns the crossing and full register
  save, this is a bounded addition, not a new hook.
- **Native scroll relationship:** Plane B VSCROLL = FG Y (`staged_scroll_y_bg` follows `a5@0x10B0`); Plane B
  HSCROLL = half-rate parallax from `a5@0x10EC`. Committed by the existing arcade-owned VBlank path.
- **Column source for the vertical row:** the one detail to pin at implementation (the BG analog of Plane A's
  `source_col_base = (((-a5@0x10AE)&0x1FF)>>3)&0x3F`): derive the resident BG source-column base from the BG
  X-scroll `a5@0x10EC` (half-rate) and walk the `0x3951C` descriptors per column — exactly Plane A's proven
  pattern. The destination column is already exact (§2); only the per-column *source* base mirrors Plane A.

## 6. Transitional gameplay paths made unreachable

Once §5 lands: `genesistan_hook_tilemap_bg_fill_tall` (`0x00070F7C`), `vdp_project_bg_tall_if_dirty`
(`0x00070138`), `staged_bg_tall_buffer` (`0xFF50EC`), `bg_tall_dirty` (`0xFF404A`), `bg_tall_project_base`
(`0xFF404C`). Keep `genesistan_hook_tilemap_bg_fill` (direct 32-row staging), `staged_bg_buffer`, the BG LUTs,
and the **frontend** item-page/block-copy/text routes (gated by scene id + source-pointer range — unchanged).

## 7. Architecture conclusion

`Rastan semantic BG producer/camera decision (F4/F6 dest col, 0x3951C source, 10B0 Y) → bounded native
Plane B row/column → final staged_bg_buffer words → bg_row_dirty → existing arcade-owned VBlank commit`.
No `C00000` authority, no chip-destination decode, no tall buffer, no projector, no Genesis watcher/scheduler.
The exact twin of the accepted Plane A architecture, sharing its vertical hook.

## 8. Smallest safe Cody implementation task

1. **Horizontal/init:** in the gameplay path of `genesistan_hook_itempage_strip_blit`/`bg_fill`
   (`scene_id==1`), write final Plane B words directly to `staged_bg_buffer[(row&31)][((F4&3)*16+F6)&63]`
   from the `0x3951C` source; set `bg_row_dirty`; stop writing `staged_bg_tall_buffer`/`bg_tall_dirty`.
2. **Vertical:** extend `genesistan_plane_a_pan_publish_entering_rows_up/down` (`0x00070762`/`0x000707B2`) to
   also publish the Plane B entering row (`(vt+31)&63` / `vt&63`) into `staged_bg_buffer[row&31]`, BG column
   base from `a5@0x10EC`, set `bg_row_dirty` — no new hook, no new displaced bytes.
3. **Gate off** `vdp_project_bg_tall_if_dirty` for scene 1, then delete the tall path (§6) after validation.
4. **Validate:** re-run the C00000 oracle (`misTile=0`) and a Genesis visual check; keep the frontend
   item-page path; do **not** touch Plane A, collision, or rope. Pin only the BG column-source base (§5).

## 9. STOP status

**STOP not triggered.** Logical destination columns are proven from producer state (23104/23104), **not**
`C00000`/`a5@0x10F8`; a true 63→0 wrap is captured (4×); BG vertical crossings are aligned to publications
(0 publications ⇒ starvation, cleanly requiring the shared no-publish hook); exactly one hook architecture is
supported (Option B, shared with Plane A, because `10EE==10B0`); and frontend vs gameplay ownership is cleanly
separated (scene id + source-pointer range). The only implementation-scoping detail — the vertical row's
per-column source base — is the proven Plane A pattern applied to BG X-scroll.

---

# ADDENDUM (2026-08-01) — Completed vertical-row source-column mapping + restart check

Evidence added: `states/traces/build0247_plane_b_dest_20260801/` (`bgsrccol`, `bgrestart`, `bgrespawn`).
This addendum supersedes §5's "pin at implementation" note for the source-column base — it is now **proven exact**.

## 10. Exact 64-column source formula (PROVEN — producer state only)

For a native Plane B row, each ring destination column `C` (0..63) maps to its semantic source as:

```
tm0idx = a5@0x1386                       ( = byte[0x507C5 + seg_index] )
base   = 0x3951C + tm0idx*0x0C
G_r    = (a5@0x10FC - base) / 6          ; absolute source group of the most-recent BG publication
AR     = G_r*16 + a5@0x10F6              ; absolute map column at the ring's RIGHT edge
absC   = AR - ((AR - C) & 63)            ; absolute map column currently resident at ring col C
source_group  = absC >> 4
source_subcol = C & 15                   ; ( == absC & 15 )
descriptor    = *(u32)(base + source_group*6 + 2)      ; Genesis: via +0x200 ROM copy
tile(row, C)  = *(u16)(descriptor + row*32 + source_subcol*2)
```

**Authoritative semantic fields:** `a5@0x10FC` (current absolute source group, via `G_r`), `a5@0x10F6`
(right-edge sub-column), `a5@0x1386`/`tm0idx` (table base). **BG X-scroll reconstruction is NOT required**
(the earlier "derive from `a5@0x10EC`" note is withdrawn — `a5@0x10EC` is presentation scroll; the producer
state is authoritative and cleaner). No `C00000`, no `a5@0x10F8`.

**`10FC` relationship:** `G_r = (a5@0x10FC − (0x3951C + tm0idx*0x0C)) / 6`. The ring→map mapping
`absC = AR − ((AR−C)&63)` places every ring column in the 64-wide window `(AR−63 .. AR]` ending at the most
recent publication — the dual-axis wrapped map, keyed on the producer's own right-edge cursor.

### Per-state 64-cell oracle results (`bgsrccol.txt`)

Generated a full logical row set (rows 0,20,40,63 × all 64 columns = 256 cells) at each state and compared to
`C00000`:

| State F | BG X | F4 | F6 | 10FC | seg | G_r | AR | source groups spanned | match |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 400 | 0x0000 | 0 | 0 | 0x039534 | 1 | 4 | 64 | {0,1,2,3,4} | **256/256** |
| 560 | 0x01C0 | 0 | 0 | 0x039534 | 1 | 4 | 64 | {0,1,2,3,4} | **256/256** |
| 600 | 0x01A8 | 0 | 2 | 0x039534 | 1 | 4 | 66 | {0,1,2,3,4} | **256/256** |
| 1000 | 0x0078 | 2 | 8 | 0x039540 | 2 | 6 | 104 | {2,3,4,5,6} | **256/256** |
| 1600 | 0x013A | 0 | 15 | 0x039534 | 1 | 4 | 79 | {1,2,3,4} | **256/256** |
| 2400 | 0x01C2 | 0 | 0 | 0x039534 | 1 | 4 | 64 | {0,1,2,3,4} | **256/256** |

- **Nonzero BG X:** proven (0x78, 0x13A, 0x1A8, 0x1C0, 0x1C2).
- **Source-group transition:** proven (`G_r` 4→6, `10FC` 0x039534→0x039540, `seg` 1→2, multiple groups/row).
- **Destination wrap:** proven — each state spans a full 64-col ring whose `absC = AR−((AR−C)&63)` wraps
  through multiple source groups (e.g. AR=104 → groups {2..6}); combined with §2's 4 real 63→0 destination
  wraps. **Total mismatches: 0.**

## 11. Restart-state check (INCONCLUSIVE from automation — static risk flagged)

**Goal:** at a genuine restart-to-level-beginning gameplay state, verify the source counters are coherent
for §10.

**What was reachable (`bgrestart.txt`, `bgrespawn.txt`):** automated death-inducing input (run right, no jump)
drove the player to **game-over → attract**, where the source state is **zeroed** (`10FC=0x000000`,
`FGy=BGy=0`, `div6ok=false`) — this is *not* a gameplay restart, and re-coining would re-run full scene-init
(coherent). The genuine **checkpoint-respawn** path — the death-restore writers `0x055F26`/`0x056014`
(`a5@0x13E = a5@0x13B8` / `a5@0x13B8−1`) — **never executed** in 6000 frames (lives were exhausted straight to
game-over). So a real respawn state could not be captured by automated input.

**Static risk (matches the user's observed restart vertical-scroll defect):** the death-restore restores
`a5@0x13E` from the checkpoint `a5@0x13B8` and branches to `0x05602a`; scene-init `0x0501E2` (the only routine
that **re-seeds `a5@0x10FC` and `a5@0x1386` from `a5@0x13E`**, at `0x0502CC`/`0x0502A6`) is reached **only**
via `0x045316`. Whether the respawn path routes through `0x045316` before gameplay resumes is **UNPROVEN**
(the same downgraded event→scene-init route as `map_stream_format.md §6`). If the respawn restores `a5@0x13E`
but does **not** re-seed `a5@0x10FC`/`a5@0x1386`, then §10's `G_r`/`base` are **stale** relative to the
restored segment → the source formula would read the wrong descriptor group → wrong BG tiles after restart.

**First exact field at risk:** `a5@0x10FC` (absolute source-group cursor), and `a5@0x1386` (table base), if not
re-seeded from the restored `a5@0x13E` on the respawn path.

**Restart source state coherent: UNVERIFIED** (genuine respawn not reachable via automation; game-over/attract
state is zeroed, not a gameplay restart).

## 12. STOP + corrected Cody task

- **Source formula (the single goal): PROVEN** — §10, 256/256 across nonzero X, group transitions, and wraps;
  no `C00000`/`a5@0x10F8`/tall-buffer dependency. The normal-gameplay native Plane B (init + horizontal +
  vertical, §5–§8) is fully specified and cleared to implement.
- **SCOPED STOP on the restart path only.** Before relying on `a5@0x10FC`/`a5@0x1386` across a Stage-1
  restart, capture a **genuine checkpoint-respawn** state (controlled replay / savestate, since automated
  input reaches only game-over) and verify §10 coherence. If stale, the fix belongs in the **arcade-owned
  respawn re-seed** (route the respawn through scene-init so `10FC`/`1386` track the restored `13E`), **not**
  a special-case Genesis reset or a revived tall projector. **Do not** paper over it.
- **Corrected Cody task:** implement §8 (steps 1–3) for normal gameplay using the §10 exact source formula
  (drop the "pin `a5@0x10EC` base" note — use `G_r`/`AR` from `10FC`/`10F6`). **Gate on a coherent source
  base** (`(a5@0x10FC − base) divisible by 6 and in the `0x3951C` table range`); if incoherent (restart
  edge case), skip the native BG publish for that frame rather than emitting garbage — and log it — until the
  respawn re-seed is validated. Do not touch Plane A, collision, or rope.
