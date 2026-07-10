# Andy — Gameplay PC080SN Output Analysis: Stage 1 BG/FG Producer Census (Outcome G, no build)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** evidence-only analysis.
**No source, no JSON, no ROM, no build.**
**Baseline:** `rastan-direct-proposal` @ `9aa1a58` (Build 0153 accepted). Build 0153 ROM
`ee232cbdda4880a56c51f7be26ff6bb07f811dbad8d7987e600e61af33c5707a`, counter 153. Working tree clean.
**Evidence dir:** `states/traces/build_0154_gameplay_pc080sn_output/`.

## Outcome

**Outcome G — larger gameplay PC080SN architecture gap; bounded stop.** The task's working hypothesis
(**Outcome A**, "untranslated gameplay PC080SN bulk-writer family") is **disproven by Genesis runtime
evidence**: the arcade raw column writers do **not execute** on Genesis, the gameplay BG cells **already reach
the existing staging buffer**, and the actual first missing operation is **scene-selection / tile-pattern
residency**, not a raw writer. The correct fix requires a design step plus the still-unproven authoritative
gameplay scene pointer, which the task forbids forcing. No numbered build was produced.

## What was proven

### 1. Arcade: where and how Stage 1 outside BG/FG is painted
Original Rastan in MAME, shortest coin→start route into Stage 1 (`states/traces/.../arc_timeline.txt`,
`arc_regs.txt`, `arc_gp.txt`). The Stage 1 outside BG/FG plane is populated **once, at state `2/2/4`**
(F≈294–351, the last transition before gameplay `2/3/0`), by two raw PC080SN column writers:

| plane | writer PCs (arcade) | producer entry | destination | source (A2) | walker (A4) |
|---|---|---|---|---|---|
| BG | `0x055C80` (code) + `0x055C94` (attr) in loop `0x055C7A` | `0x055C68` | `0xC00000` C-window | `0x00D11C`→`0x00D91C`→`0x00F11C` (step 0x800) | `0x03951C` (+6/desc) |
| FG | `0x0559B8` + `0x055A06` in loop `0x0559B2` | `~0x055980` | `0xC08000` C-window | `0x0020FC`/`0x002048`/… | `0x03951C`/`0x050F6B` |

- Each writer PC fires **4096×** = **64 columns × 64 rows** (the producer paints one 64-cell column per call
  and is called once per column; the m68k prefetch offsets the reported PC by +4 from the store site).
- The BG loop writes a cell pair per row `{word0=(a1)+ (attr), word1=(a2+row*32+col*2) (code)}`, stride `0x100`
  (down one BG row), 64 rows; the FG loop additionally keeps a `0x0010DE00` work-RAM shadow but **also** issues
  two raw C-window stores per row.
- **At steady gameplay `2/3/0` there are ZERO C-window writes** (`arc_gp.txt`: BG=0 FG=0): the plane is painted
  at entry and thereafter moved by hardware scroll. So Stage 1 BG content is established entirely at `2/2/4`.
- The descriptor-source slots `0x10C0A0`/`0x10C0A4` (read by the descriptor-hook scene detector) are **never
  written with a gameplay-range pointer** during the entry (`arc_scene.txt`).

### 2. Genesis Build 0153: the raw writers are DYNAMICALLY DEAD; cells already reach staging
Genesis Build 0153 in MAME (`gen_probe.txt`, `gen_decide.txt`, `gen_final.txt`), same route, state `2/3/0`:

- **No raw-writer PC (`0x055Bxx`–`0x055Fxx`) ever writes the VDP** (`gen_decide.txt`, "RAW-writer PCs …" list
  is empty). All VDP data-port writes originate from genesistan hooks/commit (`0x0701xx`, `0x0702xx`,
  `0x072D4C`). The raw BG producer `0x055E68` never writes its own dest-cursor slot `0xFF10F8` (its store at
  `0x055E74` never fires) — i.e. that producer is **not reached** on Genesis.
- Instead, at `2/2/4` the **already-hooked item-page BG strip-blit** (`genesistan_hook_itempage_strip_blit`,
  runtime `0x716CA`, installed at `0x055E5E`) runs, reading a **relocated** source `A2 = 0x00D31C` (= arcade
  `0xD11C` + 0x200; `@0xD31C = 0x04A6` real data vs `@0xD11C = 0x00AD`), stepping `0xD31C→0xDB1C→0xF31C`, cols
  0–15, and stages BG cells (final dest-cursor reaches `0xC00000+0x4000` = full plane). `genesistan_hook_
  itempage_strip_populate` had already relocated the strip source (Build 0119 / KF-032 path).
- **`staged_bg_buffer` is fully populated** (2048/2048 nonzero) and **committed** to VRAM during gameplay
  (`0x07020E`/`0x070236`/`0x070244` fire ×231 at `2/3/0`), `bg_row_dirty = 0` (already flushed).

### 3. But the staged BG plane is BLANK content, and patterns are absent
- Every `staged_bg_buffer` word is **`0x4000`** (`gen_final.txt`: first row and row 8 all `0x4000`) — Genesis
  cell = tile index **0** with the priority bit. It is a **uniform tile-0 plane**, not the Stage 1 layout.
  `staged_fg_buffer` is almost entirely zero (76/2048 nonzero).
- **`genesistan_current_scene_id = 0`** and **`genesistan_scene_a0_lo = 0x0005A7DA`** (title range) at `2/3/0`.
  `load_scene_tiles(1)` has **never** run, so the **gameplay tile patterns are not resident in VRAM** and the
  arcade→Genesis tile LUT never covers the gameplay tile indices; the code words from source `0xD31C…` collapse
  through `genesistan_pc080sn_tile_vram_lut` to tile 0 → the uniform `0x4000`.
- Screen at `2/3/0`: black except stale frontend PC090OJ sprites `2731`/`2UP` (`snaps/gen0153_gameplay_600.png`).

## First exact divergence
Not a raw C-window write. The first meaningful arcade PC080SN output that Genesis does **not** faithfully
reproduce is the **content** of the Stage 1 BG plane: the arcade paints real layout cells (from descriptor
`0x03951C` + tile sources `0xD11C`-family) via producers `0x055C5E`/`0x055C68`, whereas on Genesis (a) only the
item-page strip-blit branch runs and it stages a **uniform tile-0 plane**, and (b) **scene selection never
fires**, so the gameplay tile patterns are absent and any staged code word maps to tile 0. The visible blank is
downstream of **scene-selection + pattern-residency + real-content staging**, not of an un-hooked raw writer.

## Why this is Outcome G, not a bounded A–F fix
- **Outcome A is disproven:** the raw writers (`0x055C7A`, `0x0559B2`) do not execute on Genesis; "routing them
  through staging" would be a no-op. `gen_decide.txt` shows zero raw-writer VDP activity.
- **Not a simple helper reroute (B/C):** BG cells already reach `staged_bg_buffer` via `0x716CA`; adding another
  producer wrapper would double-stage or fight the existing hook.
- **Not scene-range editing (D) yet:** the item-page/column path carries source pointers `0xD31C`-family, none in
  the gameplay `scene_a0` range `0x00056A22..0x000570C2`; the descriptor slots that the current detector watches
  (`0x10A0`/`0x10A4`) never hold a gameplay-range pointer. The **authoritative gameplay scene pointer is not yet
  proven**, and the task forbids changing scene ranges or forcing scene ID 1 / `load_scene_tiles(1)` until it is.
- **Not a missing commit (E):** staging **is** committed (`bg_row_dirty=0`, commit PCs fire); the committed cells
  are simply blank because patterns are absent.
- The remaining work — prove the gameplay scene-setup flow, decide why the Genesis item-page branch stages a
  uniform plane while the arcade column producer is bypassed, and wire natural scene selection + real-content
  staging — is a **design step** spanning multiple routines/tables, i.e. Outcome G.

## Writer-family inventory (this exact gameplay bulk-output path)
| routine (arcade) | Genesis mapping | status on Genesis | role |
|---|---|---|---|
| `0x055C5E` item-page BG strip producer | `0x055E5E → jmp 0x716CA` | **hooked**, stages BG (blank content) | 64-cell BG column via `bg_fill` |
| `0x055C68 → 0x055C7A` raw BG column writer | `0x055E68 → 0x055E7A` (live `arcade_copy`) | **never reached** (dynamically dead) | 64-row BG column, raw C-window |
| `0x0559B2` raw FG column writer | `0x055BB2` (live `arcade_copy`) | **never reached**; FG shadow `0x10DE00` unused | FG column, raw C-window + shadow |
| descriptor walker `0x03951C`; tile sources `0xD11C`-family | copied `+0x200` (`0x03971C`/`0xD31C`) | source relocated for the item-page branch only | Stage 1 layout descriptors |
| scene detector in `genesistan_hook_tilemap_plane_a`/`_fg` (`0x70248`/`0x703EA`) | active, keyed on `a5@0x10A0/0x10A4` | **not exercised** by this path | scene selection / `load_scene_tiles` |

Not part of this family (correctly untouched): the raw writer `arcade 0x03D04C → 0x03D24C` (`0xC08C66`) — it does
not appear in this Stage 1 output path.

## Smallest next design task (bounded capture + design, not a one-producer patch)
1. Prove the arcade Stage 1 scene-setup flow end-to-end at `2/2/4`: the relationship between the item-page
   producer `0x055C5E`, the raw column producer `0x055C68`, the descriptor walker `0x03951C`, and the tile
   sources `0xD11C`-family — specifically which cells each contributes and which one carries the **authoritative
   scene identity** that should drive `load_scene_tiles`.
2. Determine on Genesis **why the item-page strip-blit branch stages a uniform tile-0 plane** (LUT collapse from
   absent gameplay patterns vs. a genuine clear pass) and **why the column producer `0x055C68` is bypassed**
   (which caller diverges vs. the arcade).
3. Establish the authoritative gameplay scene pointer and, reusing the **existing** scene-detection primitive,
   design its invocation from the gameplay producer so that `genesistan_current_scene_id → 1`, the gameplay
   `scene_a0` range activates, and `load_scene_tiles(1)` loads the Stage 1 patterns **naturally** — then confirm
   whether the item-page-staged cells become correct once patterns/LUT are resident, or whether the column
   producer's contribution must additionally be routed to `bg_fill`.

Only after (1)–(3) can a bounded, faithful Build 0154 be written without forcing scene ID, hardcoding cells, or
adding a second renderer/commit path.

## Confirmation (no forcing, no changes)
No source, JSON, ROM, or build was produced. `load_scene_tiles(1)` was **not** called, scene ID was **not**
forced, no cells/patterns/scroll/palette were hardcoded, no state was advanced, no scene range changed, the
raw writer `0x03D04C` was untouched, and no emulator-specific behavior was added. Build 0153 pointer relocations
and Build 0152 `0xC08C62` routing remain intact and were not modified.

## Open issue impact
- **OPEN-017 (ROM does not run on real hardware / gameplay):** advanced — the gameplay BG boundary is
  re-characterised with runtime proof: the hypothesised raw-writer gap does **not** exist on Genesis (the writers
  are dynamically dead and BG cells already stage+commit); the real boundary is **scene selection + tile-pattern
  residency + real-content staging** for the item-page/column gameplay BG path (`scene_id` stays 0, staged BG is a
  uniform tile-0 plane). Bounded next design task defined. Not closed; no duplicate opened.
