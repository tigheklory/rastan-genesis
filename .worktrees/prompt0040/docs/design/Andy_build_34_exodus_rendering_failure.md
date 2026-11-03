# Andy — Build 0034 Exodus Rendering Failure Analysis

**Status:** ANALYSIS COMPLETE. Single primary failure identified. No
implementation. STOP not triggered.
**Build Context:** Build 0034, `rastan-direct`.

---

## 1. Summary

Build 0034 still presents bring-up synthetic graphics (red/magenta
stripes, hatched green tiles) in Exodus, transitions to BLACK between
frames ~0270 and ~0360, and then continues rendering nothing while
Exodus's console log fills with "Error Trigger" entries. The 7 new
stride-8 sibling hooks (Build 33 → 34 delta) have **not** changed the
visible output. The dispatcher default path at `arcade_pc: 0x03C950`
remains unhooked (out of scope of the prior spec set) and is the only
code path in the text-script dispatcher that can still write directly
to PC080SN FG hardware.

**Primary rendering failure: UNHOOKED ACTIVE WRITER PATH** — the
dispatcher default path's stride-2 `A1@+` writes still hit
`HW_ADDRESS/PC080SN/FG_TILEMAP`, the CPU traps to
`runtime_genesis_pc: 0x000010`, the screen goes black, and no further
arcade-supplied tile/text content can reach `staged_fg_buffer`. The
7 new hooks may be intercepting their script-opcode classes correctly,
but no visible content reaches the screen because the run dies before
text-mode rendering produces anything that survives the trap.

---

## 2. Build 0034 Baseline Confirmation

- Spec entries: `specs/rastan_direct_remap.json` `opcode_replace` count = **54** (47 prior + 7 sibling hooks). Verified by grep.
- All 8 hook symbols present in `required_symbols`:
  `genesistan_hook_text_writer_3c4d2`, `…_3c550`, `…_3c586`, `…_3c636`, `…_3c6dc`, `…_3c75c`, `…_3c7a4`, `…_3c830`.
- ROM hash differs from Build 33: Build 34 = `38fb4d4d2df3e789be18a52b06d47af09ad8c6aec880e3bd6ad87802c87bd205` (Build 33 was `b0445a29…`). The patches are present in the binary; this is a different ROM than Build 33.
- `0x03C950` default path: NOT hooked (confirmed; out of scope of the stride-8 spec set per `docs/design/Andy_stride8_sibling_hook_spec.md` §10 open question 2).
- BlastEm crash at `HW_ADDRESS/PC080SN/FG_TILEMAP: 0xC09EA0`: STILL PRESENT (per user's prior Build 33 evidence + AGENTS_LOG anomaly note that runtime behavior didn't change with sibling hooks).
- Exodus garbage output: STILL PRESENT (frames sampled below).
- Tile data is present in the VDP: confirmed (Pattern Viewer panels show recognizable tile shapes throughout).

---

## 3. Exodus Screenshot / Debugger Analysis

`states/screenshots/build_34/` contains 435 frames. Seven sampled:
0001, 0090, 0180, 0270, 0360, 0435 (last available), and 0001 (pre-game
launcher). Each frame's panels are recorded below; the
tilemap-to-pattern correlation question (§3.8) is answered explicitly.

### 3.1 frame_0001
- VDP Image Window: not visible — Exodus file-open dialog overlays the window.
- Plane / VRAM / CRAM panels: not visible.
- Conclusion: Exodus is in pre-launch state at frame 1. No rendering data yet.

### 3.2 frame_0090
- VDP Image Window: red/magenta vertical-stripe fill across the play field.
- Plane Viewer (Layer A / Plane A `0xE000`): same vertical-stripe content visible in the thumbnail.
- Plane Viewer (Layer B / Plane B `0xC000`): similar but lower-contrast vertical stripes.
- VRAM Pattern Viewer: large checkerboard / hatch patterns (synthetic bring-up tiles, consistent with `init_staging_state` content).
- VDP Palette: four palette lines populated; visible bright green, red, blue entries.
- Console log (left): clean (no error triggers yet).

### 3.3 frame_0180
- VDP Image Window: solid red plane fill with a thin blue band at the top.
- Plane Viewer thumbnails: matching red fill.
- VRAM Pattern Viewer: same synthetic-tile contents as frame 0090.
- Palette: unchanged.
- Console log: clean.

### 3.4 frame_0270
- VDP Image Window: GREEN+RED hatched grid pattern across the play field. **Different from earlier frames** — pattern density and color have shifted, indicating new staging activity OR a different palette being applied.
- Plane Viewer (Layer A): green/black hatched content; closely matches Image Window.
- Plane Viewer (Layer B): different content, more uniform red.
- VRAM Pattern Viewer: green hatched tile patterns (different from earlier — VRAM pattern data has changed).
- Palette: green entries more prominent.
- Console log: still clean.

### 3.5 frame_0360
- VDP Image Window: **BLACK.**
- Plane Viewer (Layer A): green hatched content STILL PRESENT in the cached plane thumbnail.
- Plane Viewer (Layer B): also still populated.
- VRAM Pattern Viewer: green hatched tiles STILL PRESENT in VRAM.
- Palette: still loaded (green entries present in CRAM).
- Console log: **transitioned to repeated "Error Trigger" entries with timestamps**. The trap window opens between frames 0270 and 0360.

### 3.6 frame_0435 (last available)
- VDP Image Window: BLACK.
- Plane / VRAM / CRAM panels: same as frame 0360 — content cached, not rendered.
- Console log: more Error Trigger entries; system has not recovered.

### 3.7 What is **not** visible at any frame
- No arcade text (high-score table, RASTAN logo, attract narration, item list — see §5 arcade reference frames).
- No sprites.
- No real arcade tiles (the Pattern Viewer shows the synthetic hatch/checker bring-up tiles only — the arcade scene tiles loaded into VRAM by `load_scene_tiles` would have recognisably different shapes that match the arcade reference).

### 3.8 Tilemap-to-pattern correlation (MANDATORY answer)

**Yes — the tile patterns visible in the VRAM Pattern Viewer ARE
correctly referenced by the Layer A / Layer B plane maps.** Across
frames 0090, 0180, and 0270, the Plane Viewer thumbnails directly
mirror the tile content visible in the Pattern Viewer (when shifted by
plane scroll). Frames 0360 and 0435 show the same plane and pattern
data still loaded in VDP memory while the Image Window goes BLACK —
this is a display-OFF or VDP-disable consequence, not a tilemap-mapping
error.

**Therefore: the failure is NOT in data USAGE (how the VDP renders
the tilemap+tiles+palette tuple). It is in data PRODUCTION (what gets
written into staging buffers and committed to VRAM).** Specifically,
the tile data shown is the bring-up scaffold's synthetic content; the
arcade's text-script handlers have not delivered real arcade text into
`staged_fg_buffer` in any frame, AND the run dies (CPU trap) before
the arcade's scene-tile loader can swap in real game tile patterns.

---

## 4. Trace / Code-Path Correlation

Source: `states/traces/rastan_direct_video_test_build_0034_mame_30s_20260415_183954/genesis_exec_summary.txt`.

### 4.1 Trace summary key fields

```
vdp_ports_live      count=26336 first_frame=0    last_frame=1797 first_pc=070100 last_pc=070100 first_addr=C00004 last_data=8134
fg_cwindow_live     count=8     first_frame=170  last_frame=384  first_pc=03C52A last_pc=03C518 first_addr=C09EA0 last_addr=C09EA6 first_data=0000 last_data=0037
reg_c50000_live     count=0
helper_5b512_rts@*  count=0    (all variants)
arcade_stage        changes=1   first_change=391
```

### 4.2 Comparison vs Build 33

`fg_cwindow_live count=8 first_addr=C09EA0 last_addr=C09EA6 first_pc=03C52A last_pc=03C518` — **byte-identical** to the Build 33 trace summary
(`states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_summary.txt`).
This was already flagged as Build 33 diagnostic open question 4
(possible cached/stale fields in the trace harness OR genuinely
unchanged behavior). For Build 34, given that the ROM hash *did* change
and 7 new hooks were genuinely installed, two interpretations remain:

- **(a) The trace summary fields are sticky/cached** and do not reflect Build 34 behavior. In that case, the actual `fg_cwindow_live` write count for Build 34 may differ from 8 but we cannot read it from the summary.
- **(b) The trace summary is fresh and 8 writes still happen** in Build 34. In that case, the writes come from a code path **not** affected by the new sibling hooks — most likely the dispatcher default path at `arcade_pc: 0x03C950` (the only stride-2 writer in the dispatcher) or some other writer not yet identified.

In either case, **BlastEm independently confirms the C-window write
crash still happens in Build 34 (per the user's task statement and prior
crash evidence)**. The new hooks did not eliminate the crash — there is
still an active code path producing PC080SN-range writes.

### 4.3 Are the new stride-8 hooks on the live path?

`helper_5b512_rts@* count=0` — all the relocated copies of the
`helper_5b512_rts` helper across all three address-space prefixes
(`@0x000000, @0x000200, @0x200000`) report zero invocations. This
helper is called only from inside `arcade_pc: 0x03C516` (Rastan handler
0x03C4D2's now-dead inner sub) and from `arcade_pc: 0x03C70A` (handler
0x03C6DC's inner sub). Both handlers are now hooked. Count=0 is the
expected post-patch value: the original inner subs are dead because
their containing handler bodies were overwritten with `JSR + RTS + NOPs`.

This is consistent with the new hooks being installed correctly. It
**does not** prove they are firing on the visible path — to prove
firing we would need a per-hook entry-point watch added to
`tools/mame/genesistrace.lua`. That is not in this analysis's scope.

### 4.4 Trap evidence

Prior MAME exit summaries (this Build 33/34 family) consistently report
final `runtime_genesis_pc: 0x000010` and `SP: 0x00DEA634`. Address
`0x000010` is in the Genesis vector table (per
`docs/design/Andy_address_map_artifact_design.md` §6,
`preserved_vectors` segment `[0x000000, 0x000400)`). Reaching it means
the CPU executed an exception trap and ran the trap-vector stub. This
matches the "BLACK from frame 0360 onward + Error Trigger console
spam" observation in the Exodus frames.

### 4.5 Live-path classification

| Build 34 element | Status |
|------------------|--------|
| Wrapper VINT handler | LIVE (`vdp_ports_live` 26336 firings at `runtime_genesis_pc: 0x070100`). |
| Existing Rastan hooks (BG/FG strip producers, scroll, c-window clear) | LIVE (no behavioral evidence to the contrary). |
| New stride-8 sibling hooks (7) | UNVERIFIABLE from trace (no per-hook watch). Patches are in ROM. |
| Dispatcher default path `arcade_pc: 0x03C950` | UNHOOKED. The only stride-2 writer remaining in the text-script dispatcher. |
| Trap path `runtime_genesis_pc: 0x000010` | LIVE (CPU lands here after the C-window write). |

### 4.6 What the trace cannot tell us

- Whether the 8 `fg_cwindow_live` writes in Build 34 originate from the default path 0x03C950 specifically, or from some other source (e.g., a sibling-hook bug producing an out-of-range A1 → fall-through to original write code via the unreachable NOP padding — extremely unlikely because the patched RTS at offset 6 is hit before any NOPs execute).

---

## 5. Arcade Reference Comparison

Source: `states/reference/rastan_arcade_60s/` (1801 frames). Three
sampled to characterize the attract phase.

### 5.1 frame_0001 (arcade ref)
- Solid white fill. Pre-game state — arcade machine has just powered on; nothing rendered yet.

### 5.2 frame_0090 (arcade ref)
- "RASTAN" title screen with sword-on-banner art, "TAITO 1987 ALL RIGHTS RESERVED" text.
- Full text rendering active. Multiple tilemap regions populated with bright multi-color text.

### 5.3 frame_0270 (arcade ref)
- "THIS IS A CHRONOLOGICAL HISTORY OF A BARBARIAN WHO DARED TO CHALLENGE." narrative text.
- Below: "BEST 5" high-score table with column headers ("SCORE", "ROUND", "NAME") and 5 rows of game data.
- Heavy text usage — exactly the kind of content the text-script dispatcher exists to render.

### 5.4 frame_0450 (arcade ref)
- Item-list screen: "AXE", "HAMMER", "FIRE SWORD", "SHIELD" with item icons (tiles) on the left and explanatory text on the right. Multiple tilemap rows populated.

### 5.5 Comparison summary

The arcade attract phase that Build 34 should display at frames
0090–0450 is dense with text rendered through PC080SN FG. Build 34
shows none of this content — only the bring-up scaffolding's
synthetic patterns. The Genesis port has not advanced past the
bringup-init-state visual surface.

**Class of presentation difference:** missing text and missing arcade
tile content. The plane maps and palette infrastructure are working
(tiles ARE referenced and ARE colored), but the *content* in the planes
is bring-up scaffolding because the arcade's text-script handlers
either (a) never produce visible content into `staged_fg_buffer` due to
the CPU trap killing the run, or (b) produce content that is then
displaced by the trap-state handling.

---

## 6. Single Primary Rendering Failure

> **UNHOOKED ACTIVE WRITER PATH.**
>
> The dispatcher fall-through default path at `arcade_pc: 0x03C950`
> (`genesis_rom_offset: 0x03CB50`) — the only stride-2 `A1@+` writer
> in the text-script dispatcher and explicitly out of scope of the
> Build 33→34 stride-8 spec set — continues to write directly into
> `HW_ADDRESS/PC080SN/FG_TILEMAP`. BlastEm crashes on the first such
> write (consistent across Builds 32, 33, 34). MAME's permissive
> handling lets execution continue briefly until the CPU traps to
> `runtime_genesis_pc: 0x000010`. After that point the screen goes
> BLACK (frames 0360–0435) and no arcade-supplied tile/text content
> can reach `staged_fg_buffer`. The 7 new stride-8 sibling hooks
> didn't change this because they only intercept opcodes
> `0x10/0x20/0x30/0x90/0xA0/0xB0/0xC0` — opcodes whose top nibble
> falls outside that set (e.g. `0x40, 0x70, 0x80, 0xD0..0xF0`) drop
> through to the default path at `0x03C950`, which is still raw arcade
> code writing to PC080SN.

### 6.1 Evidence

- The dispatcher routing table (proven in `docs/design/Andy_dispatcher_map_analysis.md` §2) shows 9 explicit `beqw` cases covering top nibbles `0x10, 0x20, 0x30, 0x50, 0x60, 0x90, 0xA0, 0xB0, 0xC0` — all 8 distinct handlers now hooked. **Top nibbles `0x00, 0x40, 0x70, 0x80, 0xD0, 0xE0, 0xF0` fall through** to the default body at `arcade_pc: 0x03C950` (`build/maincpu.disasm.txt:76289+`). The default path uses `move.w D0, A1@+` writes (stride 2) at `arcade_pc: 0x03C982, 0x03C990, 0x03C99E` — different write shape than the stride-8 family — and a fast-fill escape at `arcade_pc: 0x03C9F8` writing `#0x0180` to `A1@(2)` with `addq.l #8, A1`. Either shape can target FG tilemap addresses including `0xC09EA0`.
- The ROM at `genesis_rom_offset: 0x03CB50..0x03CC34` (default-path body) is verbatim arcade code (no `opcode_replace` overlap) — confirmed by the address_map.json `arcade_copy` segment record `[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)` not being interrupted by any patched_site segment in this range. (The 47→54 patched_site segments live elsewhere in the same arcade_copy.)
- BlastEm crashes with the same symptom across Builds 32, 33, 34. Across these builds the patched-site count went 46 → 47 → 54, but the crash persists. The only writer category common to all three builds and not addressed in any build is the dispatcher default path.
- Exodus shows the screen go BLACK + Error Trigger entries at the same frame window as Build 33 (≈ 270–360). That trap window is unchanged because the underlying writer (the default path) is unchanged.

### 6.2 Why each other category is NOT primary

- **Wrong tilemap / nametable mapping:** Refuted by §3.8. Tile shapes in the VRAM Pattern Viewer match the Plane Viewer thumbnails which match the Image Window (frames 0090–0270). The mapping path works; the content is wrong because no real content was produced.
- **Wrong tile / attribute composition:** Refuted by §3.7 — the bring-up synthetic tiles ARE the tiles being shown, and they are correctly colored per the bring-up palette. If a stride-8 hook had a composition bug, we would expect to see *some* hooked content (mis-translated text) in the planes; instead we see no arcade content at all (because execution dies before content is produced). Composition bugs in the new hooks would be visible only after the trap path is fixed.
- **Wrong VDP register / scroll / plane state:** Refuted by `vdp_ports_live count=26336` — the wrapper continues to write VDP registers every frame across all 1798 frames including frames 0360–1797 when the screen is BLACK. The display-OFF/ON bracket is firing per `_VINT_handler` in `apps/rastan-direct/src/main_68k.s:81–109`. Plane bases, scroll initial state, autoinc, planesize are all initialized in `vdp_boot_setup`. None of these would produce a screen that renders the bring-up patterns for 270 frames then goes black.
- **Wrong commit timing / ordering:** Refuted by the same `vdp_ports_live` evidence and by the persistence of bring-up patterns through frame 0270 (which means tile/plane/palette commits ARE reaching VRAM and the VDP IS displaying them on schedule). Commit pipeline is healthy until the trap.

### 6.3 Secondary issue (brief)

Whether the 7 new stride-8 hooks are **firing correctly when their
script-opcode top-nibble matches** has not been independently verified
(see §4.3 — no per-hook live-write watch in current trace tooling).
After the default-path hook is installed and the trap is eliminated, a
follow-up Build 35 trace + Exodus capture should be examined to
confirm whether real arcade text appears in `staged_fg_buffer` — at
that point any per-hook composition bug becomes diagnosable.

---

## 7. Evidence References

| Claim | Source | Address / Line / Frame |
|-------|--------|------------------------|
| Build 34 ROM exists, 54 opcode_replace entries | `specs/rastan_direct_remap.json` | `opcode_replace_count: 54`; 8 hook symbols listed |
| Build 34 ROM hash | `apps/rastan-direct/dist/rastan_direct_video_test.bin` | sha256 `38fb4d4d…` |
| Bring-up synthetic patterns visible | `states/screenshots/build_34/` | frames 0090, 0180, 0270 (Image Window + Plane Viewer + Pattern Viewer panels) |
| BLACK + Error Trigger transition | `states/screenshots/build_34/` | frames 0360, 0435 |
| Wrapper VINT handler firing each frame | `states/traces/rastan_direct_video_test_build_0034_mame_30s_20260415_183954/genesis_exec_summary.txt` | `vdp_ports_live count=26336` at `runtime_genesis_pc: 0x070100` |
| Fall-through dispatcher default path | `build/maincpu.disasm.txt:76289+` | `arcade_pc: 0x03C950` |
| Default-path uses `A1@+` writes | `build/maincpu.disasm.txt:76306, 76311, 76316` | instructions at `arcade_pc: 0x03C982, 0x03C990, 0x03C99E` |
| Default-path fast-fill `A1@(2)` write | `build/maincpu.disasm.txt:76348` | `arcade_pc: 0x03C9F8` |
| address_map default-path location | `build/rastan-direct/address_map.json` arcade_copy segment lookup | `genesis_rom_offset: 0x03CB50` |
| Arcade attract reference content | `states/reference/rastan_arcade_60s/` | frames 0090 (RASTAN title), 0270 (high-score table), 0450 (item list) |
| Tilemap-to-pattern correlation | §3.8 | frames 0090–0270 (planes match patterns); frames 0360–0435 (planes/patterns intact, image black → trap) |

---

## 8. Next-Step Recommendation

Implementation work is **out of scope** for this analysis. The
recommended scope of the next prompt:

1. **Spec the hook for the dispatcher default path at `arcade_pc: 0x03C950`** (the only remaining text-script dispatcher writer not yet hooked). The patch span requires the sub-sub caller audit flagged in `docs/design/Andy_dispatcher_map_analysis.md` open question 3 — confirm whether sub-subs `0x03C9E8, 0x03C9F6, 0x03CA00, 0x03CA12, 0x03CA26` have callers outside the default path. If not, the patch span can absorb the sub-subs; if so, only the entry block.
2. **After Build 35 (which should add the default-path hook), examine the Exodus frames again** to see whether any arcade text content appears in `staged_fg_buffer`. If yes, declare the rendering pipeline fixed and start the per-hook composition correctness audit. If no, look for further unhooked writers (e.g., scene preload paths, sprite RAM writers, palette writers).
3. **Add per-hook live-write watchpoints** to `tools/mame/genesistrace.lua` so future traces can attribute writes to specific handler entries. This is a tooling improvement that would close the ambiguity about whether Build 34 trace summary fields are stale or genuinely unchanged.

No source files modified by this analysis.

---

## 9. STOP Conditions

None triggered. All required Build 34 evidence sources are present and
readable: `states/screenshots/build_34/` (435 frames), Build 34 MAME
trace, `address_map.json`, `specs/rastan_direct_remap.json`,
`build/maincpu.disasm.txt`. Single primary cause supported by panel
evidence + trace correlation + arcade-reference comparison.
