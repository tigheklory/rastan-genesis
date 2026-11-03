# Andy — Missing "UP" in "2UP" Title Header (Focused Analysis, Outcome A)

**Agent:** Andy (temporary runtime-evidence role). **Type:** evidence-only analysis. **No source, no ROM, no build number.**
**Baseline:** `rastan-direct-proposal` @ `a60d5f5`; accepted ROM
`dist/rastan-direct/rastan_direct_video_test_build_0146.bin` =
`3edcf345d1c6e547b993f72b29ab9d80f7fa58823ad992de962391a5ce8a416b`. Working tree clean apart from env files.
**Evidence dir:** `states/traces/missing_up_2up_header/`.

## Outcome
**Outcome A — missing coordinate/clipping rule proven.** The arcade PC090OJ renders sprites with the game's
**8-pixel top visible-area margin** (`set_visarea(0,319,8,247)`, `m_y_offset = 0`). Leading-zero score digits
(code `0x2A`) are inked **only in cell rows 0–6 (top half)** and are placed at **raw Y = 0**, so their ink lands on
screen rows 0–6 — inside the clipped top margin — and the arcade shows nothing. The Genesis retained decoder maps
raw Y = 0 → SAT screen Y = 0 with **no top-margin clip**, so the digits' top-half ink is fully visible and each
leading-zero record consumes a Genesis SAT slot on scanline 0. That pushes scanline 0 to the Genesis H40 limit
(20 sprites / 320 px), and the VDP drops the last sprite in link order — record 45, the `UP` of `2UP`. A disposable
debugger experiment (removing the six left leading-zero SAT slots at commit) restored `2UP` and cleared the left
`000000`, confirming the line-budget consequence. Mirror state was never modified.

## Settled record/SAT facts (not re-derived)
Record 44 = visible `2` (`0000 0000 0049 0108`); record 45 = missing `UP` (`0000 0000 0047 0118`); Genesis mirror
matches the arcade for both; record 44 → SAT slot 21, record 45 → SAT slot 22 (Y 0x080, link 0, tile 0xC458,
X 0x198, palette line 2); slot 22 resident pattern = `0x0047`. The retained renderer is not limited to five sprites.

## 1. Exact arcade PC090OJ rendering rule (MAME source)
`src/mame/taito/pc090oj.cpp`, `pc090oj_device::draw_sprites()`:
```cpp
int x = m_ram_buffered[offs + 3] & 0x1ff;
int y = m_ram_buffered[offs + 1] & 0x1ff;
if (x > 0x140) x -= 0x200;
if (y > 0x140) y -= 0x200;
if (!(m_ctrl & 1)) { x = 320 - x - 16; y = 256 - y - 16; flipx = !flipx; flipy = !flipy; }
x += m_x_offset;  y += m_y_offset;
gfx(0)->prio_transpen(bitmap, cliprect, code, color, flipx, flipy, x, y, ...);   // clipped to cliprect
```
- Raw Y extraction: `m_ram_buffered[offs+1] & 0x1ff`; sign-wrap `if (y>0x140) y-=0x200`.
- Rastan driver (`src/mame/taito/rastan.cpp`): **no `set_offsets`** ⇒ `m_x_offset = m_y_offset = 0`;
  `spritectrl_w` writes only `sprite_ctrl_w` (colbank/priority + coin lockout), **no flip bit**.
- **Visible area:** `screen.set_visarea(0*8, 40*8-1, 1*8, 31*8-1)` = X 0..319, **Y 8..247** → screen rows **0–7 are a
  non-displayed top margin**; the `transpen` blit clips all sprite pixels to this `cliprect`.
- No per-sprite visibility/disable bit; **no per-scanline sprite limit** in the PC090OJ (it draws all 256 records).
- Runtime evidence shows the **non-inverted path is in effect** (upright display): `1UP` at raw X 0x28 renders on the
  screen **left** (an inversion would put it at 320−0x28−16 = 264, right), and `HIGH SCORE` at raw Y 0 renders at the
  screen **top** (an inversion would put it at 256−0−16 = 240, bottom). So effectively `screen_y = raw_y`,
  `screen_x = raw_x`, with the 8-px top margin clipping rows 0–7.

## 2. Representative zero-record Y-byte semantics (arcade vs Genesis, settled title frame)
Full 8 bytes (`word0 Y code X`); arcade `0xD00000+r*8`, Genesis mirror `0xFF69B0+r*8`:
```
 rec 28 (left leading-zero) : 00 00 00 00 00 2a 00 30   w0=0 Y=0x0000 code=0x2a X=0x030   arcade==genesis
 rec 42 (right leading-zero): 00 00 00 00 00 2a 00 e8   w0=0 Y=0x0000 code=0x2a X=0x0e8   arcade==genesis
 rec 35 (1UP '1')           : 00 00 00 00 00 48 00 28   w0=0 Y=0x0000 code=0x48 X=0x028   arcade==genesis
 rec 45 (2UP 'UP')          : 00 00 00 00 00 47 01 18   w0=0 Y=0x0000 code=0x47 X=0x118   arcade==genesis
```
**Resolution of the flagged inconsistency:** the leading-zero records really are at **raw Y = 0** (the Y-word,
bytes 2–3, is `0x0000`) — the earlier Y=0 dump is correct. There is **no leading-zero visibility flag and no special
Y**; word0 = 0 for both zeros and labels. Arcade and Genesis final bytes are **byte-identical** for every record
(zeros, digits, labels). The suppression is entirely a **pattern-ink + clip geometry** effect, not a record-field
encoding — which is why it is Outcome A (clipping rule), not Outcome B (visibility bit).

## 3. Rendered eligibility per group (screen_y = raw_y; arcade visible top = 8; sprites 16 px tall)
| group | records | raw Y | arcade screen Y (cell) | ink rows | arcade ink screen Y | arcade shows? | Genesis screen Y | Genesis shows? |
|---|---|---|---|---|---|---|---|---|
| left leading zeros | 28–33 | 0 | 0–15 | 0–6 (top) | 0–6 | **NO** (clipped <8) | 0 (cell 0–15) | **YES** (wrong) |
| 1UP label | 35–36 | 0 | 0–15 | 8–14 (bot) | 8–14 | YES | 0 | YES |
| right leading zeros | 37–42 | 0 | 0–15 | 0–6 (top) | 0–6 | **NO** (clipped <8) | 0 | **YES** (wrong) |
| 2UP label | 44–45 | 0 | 0–15 | 8–14 (bot) | 8–14 | YES | 0 | YES for 44, **dropped for 45** |

First divergence appears at the **SAT-representation / top-clip stage**: the arcade yields zero visible pixels for the
raw-Y=0 top-inked digits (they fall in the 8-px margin), whereas the Genesis decoder allocates each a full SAT slot at
screen Y 0. Record 45 (`UP`) itself is correctly represented, but it is the **20th and last** sprite in link order on
scanline 0 (see §Line-budget), so the VDP drops it.

## 4. Pattern-row layout (arcade OBJ ROM `:pc090oj`, 16×16×4 packed-MSB, 128 B/tile)
Ink pixel counts by vertical half:
```
 code 0x2a (leading-zero digit): TOP rows 0-6 inked (24 px)   BOTTOM rows 8-15 = 0
 code 0x39 (score '00' glyph)  : TOP rows 0-6 inked (48 px)   BOTTOM = 0
 code 0x47 (2UP 'UP')          : TOP = 0                      BOTTOM rows 8-14 inked (57 px)
 code 0x49 (2UP '2')           : TOP = 0                      BOTTOM rows 8-14 inked (30 px)
 code 0x48 (1UP '1')           : TOP = 0                      BOTTOM rows 8-14 inked (19 px)
 code 0x46 (1UP 'P')           : TOP = 0                      BOTTOM rows 8-14 inked (57 px)
 code 0x3a (HIGH 'HI')         : TOP = 0                      BOTTOM rows 8-14 inked (53 px)
```
**Digit glyphs are inked only in the top 8 rows; label glyphs only in the bottom 8 rows.** This is the deliberate
arcade mechanism: place both at raw Y = 0 and let the 8-px top margin hide the (top-inked) leading zeros while the
(bottom-inked) labels remain on-screen. The proposed 8-pixel clipping explanation is **confirmed** by the pattern
data.

## 5. Disposable debugger experiment (no source / ROM / mirror change)
Breakpoint at `vdp_commit_sprites` (`runtime_genesis_pc 0x00072098`) with action zeroing the Y-word of the six left
leading-zero staged-SAT slots (records 28–33 = slots 5–10, `staged_sprite_sat 0xFF6188 + slot*8`) **just before the
sprite DMA**, then continue (`states/traces/missing_up_2up_header/dbg.txt`, `snap.lua`). Result
(`snaps/gen146_bp_exp.png`):
- the left `000000` **disappeared**;
- `1UP`, `HIGH SCORE`, and `2UP` remained correctly positioned;
- **`UP` became visible** — the header now reads `2UP` (blue), not `2`;
- the mirror (`pc090oj_object_ram`) and every other record were untouched; only staged-SAT Y at the commit instant
  was overridden for this capture.

Removing the unwanted rendered zeros from scanline 0 restored `UP`. (Earlier attempts that patched the mirror
candidate bitset or the staged SAT at frame boundaries had no effect — the renderer rebuilds those slots each frame
and a WRAM read-tap does not intercept the VDP DMA fetch; the pre-DMA breakpoint is the correct injection point.)

## Line-budget consequence (from settled + this analysis)
Scanline 0 carries **20 represented sprites** (records 4–8 HIGH SCORE, 35–36 1UP, 44–45 2UP, and the twelve code-0x2A
zeros 28–33/37–42), all at SAT Y 0x080 — exactly the Genesis H40 per-line limit (20 sprites / 320 px = 20×16). In
link order record 45 (`UP`) is the **20th/last** covering line 0, so the VDP drops it. The twelve leading-zero sprites,
which the arcade never displays, are what push the line to the limit.

## First exact arcade-vs-Genesis divergence
The Genesis PC090OJ decode (`.Lpc090oj_decode_record`) **does not reproduce the arcade visible-area top clip
(Y ≥ 8)**. Consequently every raw-Y=0 top-inked leading-zero record — which produces **zero** visible arcade pixels —
is given a full Genesis SAT slot at screen Y 0. This is the first divergence; its downstream effect is the scanline-0
sprite-budget overflow that drops record 45 (`UP`).

## Smallest faithful implementation boundary (do not implement here)
`.Lpc090oj_decode_record` (`apps/rastan-direct/src/pc090oj_hooks.s`) must reproduce the arcade screen geometry:
1. apply the arcade top-of-screen origin (net **−8** in Y, so arcade visible top raw/screen Y = 8 → Genesis
   display line 0); and
2. **gate SAT representation on the arcade `cliprect`** — a record whose inked rows map entirely above the arcade
   visible top (Genesis Y < 0) yields no arcade-visible pixels and must **not** be allocated a Genesis SAT slot.

Because the discriminator is the glyph's vertical ink extent relative to the clip line (top-half vs bottom-half at
raw Y = 0), the decoder needs each code's first-inked row, derivable at pattern-residency time (when the sprite tile
is loaded). This is a **general PC090OJ coordinate + clip visibility rule** — it must not special-case code `0x2A`,
record numbers 28–33/37–42, the text `UP`, the title screen, or the final SAT slot, and it must leave all mirror
records intact. A bare −8 origin **alone is insufficient**: it hides the zeros visually but their (blank) 16-px cells
still cover scanlines 0–7 and still consume the per-line budget, so `UP` would remain dropped; the representation
gate (culling the zero-visible-pixel records) is the part that frees the budget.

Note: this same rule also removes the **extra rendered score-zero rows** (the `000000` that the arcade shows as `00`),
so the missing `UP` and the extra-zeros defect share **one** root cause.

## Confirmation that mirror records remain preserved
All leading-zero and label records remain byte-identical in `pc090oj_object_ram` (arcade == Genesis, §2). The proposed
fix culls only **SAT representation**; the authoritative arcade mirror is never modified. The disposable experiment
touched only the staged SAT at the commit instant and never wrote the mirror.

## Files changed
None (analysis only). Documentation: this report; `AGENTS_LOG.md`; `OPEN_ISSUES.md`. Evidence:
`states/traces/missing_up_2up_header/` (`dbg.txt`, `snap.lua`, `diag.lua/.txt`, `dumpgfx.lua`, `regions.txt`,
`res.lua`, `resident.txt`, `exp*.lua`, `snaps/gen146_bp_exp.png` = UP restored, plus the null-result attempts).
**Build produced: NO. ROM produced: NO. Build number consumed: NO.**

## OPEN_ISSUES impact
- **OPEN-001 (title/attract graphics incomplete):** materially advanced — the missing `UP` in `2UP` is root-caused:
  the arcade 8-px top-margin clip (`set_visarea` Y=8..247) is not reproduced by the Genesis PC090OJ decode, so
  leading-zero digit records (top-inked, raw Y=0) that the arcade hides are over-represented in the Genesis SAT,
  overflowing scanline 0 and causing the VDP to drop the last chain sprite (`UP`). Same root cause explains the extra
  visible score zeros (`000000` vs arcade `00`). Documented next action: add the visible-area top-clip / vertical-ink
  representation gate to the decoder. Not closed.
- **OPEN-024 (PC090OJ subsystem incomplete):** advanced — identifies a general missing decoder rule (arcade
  visible-area top clip + vertical-ink visibility gate), distinct from the record-range and palette fixes. Not closed.
- No issue closed; no duplicate opened.

## Architecture-compliance statement
CONFIRMED. Evidence gathered only via MAME source citation, arcade/Genesis memory dumps, arcade OBJ-ROM pattern
decode, and one disposable runtime debugger breakpoint that made **no** source, ROM, build-number, or mirror change
(it overrode staged-SAT Y at the commit instant for a single capture, then the run exited). Arcade code remained the
execution owner throughout. No production change of any kind.

## Scope statement
HIGH SCORE (Build 0146), palette work (Builds 0143–0145), the extra score-zero rows as a separate deliverable, score
values, `1UP`, colours/palettes, the RASTAN logo, the item screen, Plane A/B, gameplay, scrolling, audio, and
real-hardware behaviour were not investigated. The fix itself was not implemented (analysis only).
