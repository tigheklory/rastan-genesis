# Pre-Coin Flickering Garbage Visual Trace (Build 218)

## Purpose
Trace the active pre-coin (attract/front-end/config) visual update path and identify the most likely source of flickering garbage before coin input, without applying any fixes.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant entries)
- `README.md`
- `dist/Rastan_218.bin`
- `apps/rastan/src/main.c`
- `build/maincpu.disasm.txt` (arcade context)
- Local disassembly generated via `m68k-elf-objdump`

## Address Mapping Note
All addresses below are Build 218 Genesis ROM/runtime addresses unless explicitly noted as arcade context. This pass keeps pre-coin analysis separate from the post-coin `0x03AAAC` crash chain.

## 1) Pre-Coin Visual Path

### Active pre-coin state/step path (proven)
- Front-end dispatcher returns through `0x03A274` each tick.
- Pre-coin waiting path is in the `0x03AAB8` cluster:
  - setup branch calls at `0x03AADE/0x03AAE2/0x03AAE6`, text ids at `0x03AAFA..0x03AB1C`, then `A5+0x0002 = 1` at `0x03AB20`.
  - coin-gate loop at `0x03AB28` (`move.b 0xE0FF4870,d0`) stays active before coin.
  - coin transition occurs only on `0x03AB50` branch and later sets `A5+0x0000 = 2` at `0x03ABF0`.
- Therefore before coin, execution remains in the pre-coin front-end branch (major state not yet transitioned to `2` by coin handler).

### Pre-coin helper branch where flicker-relevant conversion is active
- In the same pre-coin phase family, `0x03A8B8`/`0x03A9A4` substep flow calls:
  - `0x03A8D6: jsr 0x059F36` (pre-coin callsite)
  - `0x03A944: jsr 0x059F36` (pre-coin callsite)
- These callsites are reached before coin transition (`0x03AB28` path), so `0x059F36` is active in pre-coin display updates.

### Render/update responsibilities in this phase
- Tile/text updates:
  - `0x03BD5E -> jsr 0x2027B8` (patched text writer bridge).
  - `0x059CEA` invoked by `0x05A56C/0x05A626/0x05A658` helper family for table-driven converted writes.
- Sprite updates:
  - Main loop always runs `render_frontend_sprite_layer()` in `SCREEN_FRONTEND_LIVE`.
  - This calls `genesistan_render_sprites_vdp()` (workram descriptor blocks).
- Scroll updates:
  - Main loop runs `sync_arcade_scroll_to_vdp()` -> `genesistan_scroll_from_workram_vdp()` each frame.
- Palette updates:
  - Main loop runs `load_arcade_palette()` each frame (CLCS scan + ROM fallback path).

## 2) Active Display Helpers Involved

### High-signal helper in pre-coin path
- `0x059F36`:
  - prologue: `lea 0x10D600,a1`
  - selector read: `move.b A5+0x0118,d0; subq #1; lsl #2`
  - table base immediate: `movea.l #0x059E9A,a3`
  - table deref and conversion loop writes through `a1`.

### Absolute-long table/data-base immediates observed in this pre-coin helper family
- `0x059F46: movea.l #0x059E9A,a3`
- `0x059E7A: movea.l #0x059E9A,a3`
- `0x059EE4: movea.l #0x059E9A,a3`

### Dependency observations relevant to visual corruption risk
- Remaining C-window/text semantics in live path:
  - `genesistan_hook_text_writer_3bb48_impl()` still computes C-window/shadow address forms and writes a shadow cell side effect (`TEXT_WRITER_SHADOW_PAGE2_OFFSET` path) before VDP draw.
- Staging/deferred format assumptions remain in several helpers:
  - helper families write converted/staged data to workram windows (not all direct one-shot VDP writes).
- Sprite path is still descriptor-staged from workram blocks (frontend-limited SAT builder), so malformed source descriptors can visibly flicker.

## 3) Visual Corruption Source Classification

Primary classification: **stale table/data-base reference**

Why this is primary in pre-coin phase:
- Pre-coin callsites (`0x03A8D6`, `0x03A944`) actively execute `0x059F36` before coin.
- `0x059F36` relies on absolute-long table base immediates (`0x059E9A`) in the same helper family already proven sensitive to shift correctness.
- Malformed table dereference/conversion in this path is consistent with flickering/garbage output before coin, without requiring the post-coin crash path to be active.

Secondary contributors (not primary in this pass):
- residual C-window/text staging assumptions in text writer hook side effects.
- partial architecture state where some frontend data producers still assume staged arcade-like backing layout.

## 4) Minimal Next Target (Design Only)

=== MINIMAL_VISUAL_FIX_TARGET ===
- fix_area: pre-coin helper-family absolute-long table-base relocation correctness in the `0x059E6A/0x059EE4/0x059F36` conversion routines.
- exact path/helper/state involved: pre-coin front-end substep path (`0x03A8D6` and `0x03A944`) calling `0x059F36` during attract/config display updates before coin transition at `0x03AB28`.
- why this is the minimum next visual-output step: these are active pre-coin callsites and the corruption-risk source is pointer/table-base correctness inside the called helper, so this targets the earliest proven visual producer without reopening startup redesign.
- what must NOT be changed: no startup/launcher/gameplay redesign, no manual callsite retargeting, no opcode/spec bypasses, no shadow-RAM reintroduction.

## Uncertainties
- Exact frame-by-frame visual artifact provenance (which converted buffer line corresponds to each flicker tile) was not observed with per-frame emulator capture in this pass.
- This pass did not prove whether text-writer shadow side effects amplify the same flicker symptom; they remain a known secondary risk.

## Conclusion
The pre-coin flickering garbage is best explained by an early active front-end conversion path (`0x03A8D6/0x03A944 -> 0x059F36`) using shift-sensitive absolute table-base immediates; this is a separate earlier visual-output problem from the later post-coin crash trigger.
