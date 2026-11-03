# Andy — Title Render VBlank/VDP Ownership Audit (after OPEN-016 Part 1)

**Author:** Andy
**Date:** 2026-06-19
**ROM under analysis:** OPEN-016 Part 1 patched (SHA `c9fab1b47ccd3dd7dff76dbd4fe8776521287697a9e6824917a1b7a10131b390`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No implementation. No runtime probing. No fix design (bounded recommendation only).

Disassembly from `build/genesis_postpatch.disasm.txt` / `build/maincpu.disasm.txt`. The Start→C→A crash is out of scope (downstream). The old `0x50205741` crash is statically fixed (table relocated) and not treated as active.

---

## 1. Baseline statement

OPEN-016 Part 1 relocated the title descriptor-pointer table at `0x03BD7C` by +0x200, so `table[65]` now points to a valid descriptor at `0x03C446` (`dest = 0x00C0914C`, attr, "OTHERW…"). Zero-input no longer crashes; the title/attract state is stable but visually **garbled** (sparse dots near top), and changes with input. This audit asks: when the renderer writes to `0x00C0914C`, where does that go, and what VBlank/VDP path commits/ignores it?

---

## 2. Title glyph renderer write destination trace

Proven path: `0x3ACC6 moveq #65,%d0` → `0x3ACC8 bsrw 0x3BD48` → `table[65]@0x3BE80 = 0x0003C446` → descriptor `dest = a1 = 0x00C0914C` → loop `0x3BD66/0x3BD68: movew %d2,%a1@+ / movew %d0,%a1@+` (attr/glyph word pairs).

**`0x00C0914C` is PC080SN tilemap hardware.** Per `AGENTS.md:101` the arcade map `0xC00000–0xC0FFFF = PC080SN tilemap → (intended) VDP nametable writes`; `tilemap_hooks.s` defines `ARCADE_PC080SN_CWINDOW_BASE_FG = 0x00C08000`, and `0xC0914C` is in the **FG C-window** (`0xC08000–0xC0FFFF`). **STATICALLY_PROVEN / DOCUMENTED.**

On real Genesis hardware, `0xC00000–0xC0FFFF` **is the VDP I/O region** (data/control ports, mirrored), not RAM and not a staging buffer. So `movew %d2,(a1)+` with `a1 = 0x00C0914C` writes **directly into the Genesis VDP port space**, with no VDP control-port address setup — i.e., uncontrolled data-port writes. **INFERRED (Genesis hardware) + STATICALLY_PROVEN (the renderer writes raw `movew` to `a1`).**

**Is this write path translated?** No. The port translates PC080SN access by **function-level hooks** on specific writer routines (`specs/rastan_direct_remap.json`):
- `genesistan_hook_number_renderer_3c2e2` (arcade `0x03C2E2`) — note: "intercept … ALL sentinel writes that otherwise target PC080SN FG tilemap hardware."
- `genesistan_hook_text_writer_3c4d2 / 3c550 / 3c586 / 3c636 / 3c6dc / 3c75c / 3c7a4 / 3c830 / 3c950` — note: "Route text writer handler … to Genesis FG staging hook and prevent direct C-window FG writes."

These hooks replace whole arcade writer functions (opcode_replace function-body replacement) and redirect their PC080SN writes into Genesis **FG staging** (`staged_fg_buffer`). **The glyph renderer `0x3BD48` is NOT in the hook list.** The only OPEN-016 remap entry touching it (`rastan_direct_remap.json:726`) *relocates its descriptor table* — it does not hook its writes. **STATICALLY_PROVEN / DOCUMENTED.**

The renderer is reached **directly** from the title sub-state handler (`0x3ACC8 bsrw 0x3bd48`) and ~48 other direct `bsrw 0x3bd48` sites — none routed through the hooked `0x3c2e2–0x3c950` functions. So the title handler's calls hit the **unhooked, raw PC080SN-write path.** **STATICALLY_PROVEN.**

---

## 3. VBlank/VDP commit path inventory

`_vblank_service` (`vdp_comm.s:156`, runtime `0x700C2`, Level-6 vector) per frame: display-off → commits → display-on → `jmp 0x3A208` (arcade handler). Ownership:

| Concern | Owner | Source |
|---|---|---|
| Tile pattern upload | `vdp_commit_tiles_if_dirty` | gated `tiles_dirty` |
| Plane B (BG) nametable | `vdp_commit_bg_strips_if_dirty` | reads `staged_bg_buffer`, `bg_row_dirty` |
| Plane A (FG) nametable | `vdp_commit_fg_strips_if_dirty` | reads `staged_fg_buffer`, `fg_row_dirty` |
| Sprites/SAT | `vdp_commit_sprites` | sprite staging |
| CRAM/palette | `vdp_commit_palette` | gated `palette_dirty` |
| Scroll | `vdp_commit_scroll` | scroll WRAM |

**All visible-plane commits read Genesis WRAM staging buffers** (`staged_bg_buffer` / `staged_fg_buffer`) and DMA them to VRAM (Plane B `0xC000`, Plane A `0xE000`). The hooked text/number writers populate `staged_fg_buffer` and set `fg_row_dirty`, so their output is committed. **DOCUMENTED (source).**

---

## 4. Ownership / stomping analysis

This is **not** a two-routine stomp on a shared VDP destination, and **not** a dirty-flag-cleared-before-commit race. It is an **orphaned writer**:

- The committed planes are sourced **only** from `staged_bg_buffer` / `staged_fg_buffer`.
- The title glyph renderer `0x3BD48` writes to **`0xC0914C` (PC080SN FG hardware)** — it populates **no** staging buffer and sets **no** Genesis dirty flag.
- Therefore the VBlank FG commit (`vdp_commit_fg_strips_if_dirty`) never sees the title text; meanwhile the renderer's raw `0xC0xxxx` writes land directly in the VDP port space as uncontrolled data-port writes.

So the renderer is disconnected from the Genesis staging→commit pipeline that every other plane goes through, while its writes simultaneously poke the VDP directly. **STATICALLY_PROVEN (data-flow from source + disasm).**

---

## 5. Explanation of the garbled title output

- The renderer streams `(attr, glyph)` word pairs to `a1 = 0xC0914C+` (and similar dests for `d0 = 17, 63–70, …`). On Genesis these are **direct VDP-port writes without a control-port address setup**, so they scatter data into the VDP at whatever address the VDP register currently holds → **sparse/garbage pixels near the top**, not a coherent nametable. **INFERRED (Genesis VDP behavior) + STATICALLY_PROVEN (raw writes).**
- The coherent FG plane is built only from `staged_fg_buffer`; since the title renderer never stages, the real title text **never forms** on Plane A.
- Pressing Start advances the title sub-state machine → different `d0`/glyph sequences → **different garbage**, with no crash because these dests (`0xC0914C`, etc.) are even. Consistent with the observed "changes with input, still garbled." **INFERRED.**

This is fully explained without invoking the old `0x50205741` crash (fixed) or the downstream Start→C→A crash (out of scope).

---

## 6. Classification

### **R1 — Destination translation missing.**

The title glyph renderer `0x3BD48` writes to arcade-era PC080SN FG-tilemap destinations (`0xC08000–0xC0FFFF`, e.g. `0xC0914C`) that are **not translated** into the Genesis VDP staging/commit system. The port hooks the high-level text/number writers (`0x3c2e2`, `0x3c4d2–0x3c950`) to redirect their PC080SN writes into `staged_fg_buffer`, but the lower-level glyph renderer `0x3BD48` — called directly by the title sub-state handler — is **unhooked**, so its writes hit the VDP raw. OPEN-016 Part 1 fixed the *descriptor data* it reads; the *write destination* is still untranslated.

Not R2 (no competing committer stomps it — it's orphaned from staging). Not R3 (a commit path exists; the renderer just doesn't feed it). R4 (pattern/palette) may be a *secondary* concern but is not the proximate cause — even correct patterns/palette cannot make raw, address-less `0xC0xxxx` port writes form a coherent plane. **STATICALLY_PROVEN / DOCUMENTED** for the destination + hook-coverage facts; **INFERRED** for the VDP-port-write visual mechanism.

---

## 7. Bounded recommendation

**Next bounded task (Cody, investigation→implementation; not designed here):** extend the existing FG text-writer hook pattern to cover the title glyph renderer path. Concretely:
- Hook/redirect the renderer `0x3BD48`'s PC080SN FG C-window writes (`0xC08000–0xC0FFFF`) into Genesis `staged_fg_buffer` + set `fg_row_dirty`, mirroring `genesistan_hook_text_writer_3c4d2`/`…3c950` (which already "prevent direct C-window FG writes" for their functions). Because `0x3BD48` is a shared leaf called from ~48 sites and uses a descriptor-driven `dest`, decide whether to hook at the renderer (covering all callers) or only the title-handler caller; the renderer-level hook is the higher-leverage option and matches the descriptor `dest = 0xC0xxxx` → FG-staging-offset translation the other hooks perform.
- Verify the FG-staging address math: translate descriptor `dest` (`0xC08000`-relative) into the `staged_fg_buffer` offset the commit path expects (same `ARCADE_PC080SN_CWINDOW_BASE_FG` subtraction the BG/FG hooks use).

Keep scope to the title glyph-renderer write path. Do **not** broaden into a graphics rewrite. Do **not** chase the Start→C→A crash or the crash-handler defects in this task.

---

## 8. KNOWN_FINDINGS impact

**Option C — proposed KF-028 refinement** (assess only; do not update `KNOWN_FINDINGS.md`). Proposed addition:

> After OPEN-016 Part 1 relocated the descriptor table, the title glyph renderer `0x03BD48` reads valid descriptors but writes their destinations (PC080SN FG C-window, e.g. `0x00C0914C`) **directly** to Genesis VDP hardware. Unlike the hooked text/number writers (`0x03C2E2`, `0x03C4D2–0x03C950`, routed to `staged_fg_buffer`), `0x03BD48` is unhooked, so its title-text writes bypass the Genesis staging→commit pipeline and scatter into the VDP — producing garbled title output (R1, destination-translation gap). The renderer is reached directly from the title sub-state handler (`0x03ACC8`) and ~48 other sites.

STRONG/CONFIRMED (destination + hook-coverage facts proven from source/spec/disasm). Cross-ref KF-010 (plane mapping), KF-013, KF-028. Possibly merits noting alongside OPEN-001 (rendering). Andy proposes; Cody applies after Tighe ack.

---

## 9. OPEN issue impact

- **OPEN-016** (title text descriptor work): this audit identifies the **next part** — Part 1 relocated the descriptor table; the renderer's write destination still needs translation/hooking into FG staging. **Do NOT close OPEN-016.**
- **OPEN-001** (rendering broken / blank-garbled output): directly relevant context; the title-text garble is one concrete instance of the staging-bypass class. No status change.
- OPEN-004: no longer the active blocker for the title path (watchdog block resolved upstream); context only.
- New issues opened: NONE. Issues closed: NONE.

## 10. STOP triggered

NO.
