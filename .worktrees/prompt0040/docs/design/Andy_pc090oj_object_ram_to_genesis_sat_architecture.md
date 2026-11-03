# Andy — PC090OJ Object RAM → Genesis SAT Architecture Audit (Analysis / Design Only)

**Author:** Andy
**Date:** 2026-07-01
**Baseline:** rastan-direct pure-assembly baseline (Build 0120 tree). rastan-direct.
**Scope:** ANALYSIS / DESIGN only. No implementation; no source/spec/tool/Makefile/ROM/build changes. MAME used **only** as arcade-hardware reference (in-repo `docs/reference/mame/rastan/src/mame/taito/pc090oj.{cpp,h}`, `rastan.cpp`) — no code copied/ported; no C/SGDK. Code correlation via `address_map.json` (no arithmetic mapping). Labels: **[OBS]** verified this task; **[MAME]** from the in-repo MAME reference; **[INT]** interpretation.

> **HEADLINE (answer to the key design question):** The current rastan-direct sprite layer is **hook-slot / event-oriented, NOT object-RAM-mirror-oriented.** It has **no faithful mirror of PC090OJ RAM `0xD00000..0xD03FFF`** and performs **no VBlank scan of the 0x800 active range decoding 256 entries.** Instead, ~15 per-arcade-PC `patched_site` hooks translate specific sprite-producing routines (and arcade **work-RAM** sprite blocks) directly into 80 Genesis SAT slots via a build-baked `pc090oj_slot_lut`. This mismatch is a strong structural explanation for why the sprite layer has never worked: coverage depends on hooking every sprite producer, a fixed entry→slot LUT cannot represent the dynamic 256-entry object RAM, and any unhooked producer yields missing/garbage sprites.

---

## == PHASE 0 ==

**Relevant priors:**
- **KF-032** — applies as context (raw PC080SN/PC090OJ writes must route through staging, not raw HW; the sprite path is the PC090OJ analog).
- **KF-036 / KF-028** — apply as context (arcade work-RAM is mapped to `0x00FF0000`; the sprite hooks read work-RAM sprite blocks `a5@(…)`, so the same mapping discipline governs them).
- **Andy Build 0120 Window finding** — applies: the Window was refuted as the pommel source, elevating sprite/SAT (this audit's subject) as the leading candidate.

**High-rediscovery hazards:**
- No single KF is HIGH-hazard here, but the **inverted-semantics class** (recently seen with the Window prior) is a caution: treat translation-layer inventions (slot LUT, active_count, descriptor-valid/touched) as **derived**, not arcade-native.

**Task classification:** **INFRASTRUCTURE** (architecture audit) + EXTENDING (OPEN-024). Not a pommel-only task.

**Contradiction check:**
- **CONTRADICTION DETECTED: YES (architectural).** The current implementation models sprites as **write-event/slot descriptors** (`staged_sprite_descriptor_table`, `staged_sprite_active_count`, `descriptor-valid/touched`, `pc090oj_slot_lut`), whereas the arcade hardware model (MAME) is a **256-entry object RAM** where the drawable state is the first `0x800` bytes, decoded uniformly each frame. The translation-layer inventions are being used as if arcade-native truth rather than derived from a faithful object-RAM mirror.
- **Does it affect current implementation assumptions?** YES — it is the root architectural concern. But it does **not** force a STOP: the audit's job is precisely to surface and re-direct this. No design here requires C/SGDK/MAME-copy/emulator-lifecycle, so I proceed to design direction (Part D). (STOP would apply only if a faithful design were impossible in pure assembly — it is not.)

---

## == MAME PC090OJ MODEL == [MAME — verified in-repo]

- **address range (Rastan):** `map(0xd00000, 0xd03fff) rw pc090oj word_r/word_w` (`rastan.cpp:322`). PC090OJ owns sprite/object RAM; PC080SN owns tilemap (`0xC00000…`). ✔ matches the prompt.
- **active drawable range:** `PC090OJ_RAM_SIZE = 0x4000`; `PC090OJ_ACTIVE_RAM_SIZE = 0x800` (`pc090oj.cpp:66-67`). Only the first `0x800` bytes are drawable. ✔
- **entry format:** 8 bytes / 4 words, 256 entries (`0x800/8`), **first sprite = highest priority** (`pc090oj.cpp:12-14`). Decode (`pc090oj.cpp:187-193`): `word0` = flipY(bit15)/flipX(bit14)/color(low nibble); `word1` = Y (`&0x1ff`); `word2` = code (`&0x1fff`); `word3` = X (`&0x1ff`). ✔ matches the prompt.
- **coordinate model:** signed-style — `if (x > 0x140) x -= 0x200; if (y > 0x140) y -= 0x200;` (`pc090oj.cpp:196-197`). Then `x += m_x_offset; y += m_y_offset;` (Rastan does not call `set_offsets` → offsets 0). ✔
- **global flip:** `if (offset == 0xdff)` → `m_ctrl` bit0 = flip control (`pc090oj.cpp:152-154`); in draw, `if (!(m_ctrl & 1))` → flipscreen: `x = 320 - x - 16; y = 256 - y - 16; flipx=!flipx; flipy=!flipy` (`pc090oj.cpp:199-205`). ✔ **CORRECTION to the prompt's wording:** the transform fires when `m_ctrl & 1 == 0` (bit 0 **clear** = flipscreen). Note it well.
- **palette bank:** `color = (data & 0x000f) | sprite_colbank` (`pc090oj.cpp:189`), where `sprite_colbank = (sprite_ctrl & 0xe0) >> 1` (`rastan.cpp:230` `colpri_cb`). `sprite_ctrl` set by `spritectrl_w` at `map(0x380000,…)` (`rastan.cpp:236, 307`). ✔
- **priority/draw order:** `screen_update` (`rastan.cpp:255-258`): PC080SN layer0 (opaque), layer1, **then** PC090OJ `draw_sprites` → **sprites over both tilemap layers**. With `colpri_cb` set (`rastan.cpp:461`), draw iterates forward (`offs 0→end, inc +4`, `pc090oj.cpp:181`) using `prio_transpen`; **entry 0 = highest priority.** ✔ (Genesis SAT: entry 0 first = on top.)
- **buffering:** Rastan does **not** call `set_usebuffer(true)`; `word_w` writes straight through (`m_ram_buffered[offset]=m_ram[offset]`, `pc090oj.cpp:149-150`) → **write-through, no double-buffer.** ✔

*(All prompt facts verified; the only correction is the flip-condition polarity: flipscreen when `m_ctrl & 1 == 0`.)*

---

## == CURRENT RASTAN-DIRECT MODEL == [OBS]

Source: `apps/rastan-direct/src/pc090oj_hooks.s` (hooks + `vdp_commit_sprites`), `pc090oj_assets.s` (`rastan_pc090oj` = `build/pc090oj_genesis.bin` tiles; `pc090oj_slot_lut` = `build/pc090oj_slot_lut.bin`). All hook sites are `patched_site` at their named arcade PCs (JSON-verified):

| hook (symbol) | arcade_pc | runtime_genesis_pc | map kind |
|---|---|---|---|
| `..._hook_target_3b902` | 0x03B902 | 0x03BB02 | patched_site |
| `..._hook_score_digit_3b802` | 0x03B802 | 0x03BA02 | patched_site |
| `..._hook_sprite_update_54810` | 0x054810 | 0x054A10 | patched_site |
| `..._hook_copy_56114` | 0x056114 | 0x056314 | patched_site |
| `..._hook_status_sprite_5a098` | 0x05A098 | 0x05A298 | patched_site |
| `genesistan_hook_3ad44_dispatch` (D00000 branch) | 0x03AD44 | 0x03AF44 | patched_site |
| `vdp_commit_sprites` | — | genesis_only helper | (VBlank) |

- **write hooks:** ~15 named per-arcade-PC hooks (targets `3b902/3b926/3b930/41dae/41f5e/45dfa/59f5e`, plus feature hooks `init_priority_3ad84`, `score_digit_3b802`, `slot_init_54052`, `sprite_update_54810`, `sprite_decay_5607c`, `copy_56114`, `zero_fill_56440`, `status_sprite_5a098`). Each translates one arcade sprite-producing routine.
- **object RAM mirror:** **NONE.** No BSS buffer mirrors `0xD00000..0xD03FFF` (BSS holds only `staged_sprite_sat` (80×8), `staged_sprite_descriptor_table` (80×12), `staged_sprite_dirty`, `staged_sprite_active_count`, small aux). No `0x4000` or `0x800` mirror exists.
- **active range handling:** the `0x3AD44` dispatch's PC090OJ branch computes `idx = (A0−0xD00000)>>3` (0..255 = the 8-byte-entry index over the `0x800` active range) and looks up `pc090oj_slot_lut[idx]` → a Genesis SAT slot, then **clears** that slot. So the `0x800`/256-entry indexing exists only as a **build-baked entry→slot LUT for the clear path**, not a runtime decode of the 256 entries.
- **sprite_ctrl handling:** hooks derive colbank as `(a5@(20) & 0x00E0) >> 1` (e.g. `pc090oj_hooks.s:192-195`) — **matches MAME's `(sprite_ctrl & 0xe0)>>1`**, BUT sourced from **arcade work-RAM shadow `a5@(20)`**, not from a captured `0x380000` write (no `0x380000` hook exists). Faithful **iff** the arcade keeps `a5@(20)=sprite_ctrl`.
- **flip control handling:** **NONE.** No reference to offset `0x0DFF`/global `m_ctrl`/flipscreen transform (`320-x-16`, `256-y-16`) anywhere. **MISSING.**
- **coordinate conversion:** hooks apply `andi.w #0x01FF` to X/Y (matches `&0x1ff`), but **no signed-style wrap** (`if x>0x140: x-=0x200`) found in the emit path. Likely **MISSING/PARTIAL** (masks to 0x1FF but does not sign-fold — offscreen/wrapped sprites mis-placed).
- **palette conversion:** `(colbank & 0xE0) >> 1` per MAME; color = `word0.low_nibble | colbank` composed into the Genesis SAT color field. PARTIAL-MATCH (derivation correct; source is the work-RAM shadow).
- **priority conversion:** SAT emitted with `#0x8000` priority bit (`pc090oj_hooks.s:129`) → sprites high-priority. Roughly matches "sprites over everything," but ordering is **slot-LUT-driven**, not PC090OJ entry-0-first priority order.
- **SAT generation:** `vdp_commit_sprites` = `link_chain_build → tile_dma → sat_dma → clear_dirty` — it assembles the Genesis SAT link chain and DMAs it from the **hook-staged** `staged_sprite_sat`/descriptors, **not** from a scan of an object-RAM mirror.
- **SAT link/termination:** a Genesis link chain **is** built (`.Lvcs_link_chain_build`) over the 80-entry `staged_sprite_sat` — a Genesis-layer invention (correct as an output step), but fed by partial hook data.

---

## == GAP ANALYSIS ==

- **MATCH:**
  - PC090OJ address range concept `[0xD00000,0xD00800)` recognized (dispatch branch).
  - Entry decode fields where used: X/Y `&0x1FF`, flip `&0x8000/&0x4000`, tile `word2`, colbank `(…&0xE0)>>1`, color `low nibble | colbank`.
  - Genesis SAT link-chain generation exists as the output step (correct Genesis-side invention).
  - 80-entry Genesis SAT sizing (`staged_sprite_sat = 80×8`).
- **PARTIAL:**
  - `sprite_ctrl` colbank (derivation matches MAME but sourced from work-RAM `a5@(20)` shadow, not a captured `0x380000` write; faithful only if the shadow is maintained).
  - Priority (`#0x8000` sprites-high present, but ordering is slot-LUT-driven, not entry-0-first).
  - Active `0x800`/256-entry indexing (present only in the clear path via `pc090oj_slot_lut`, not a full runtime decode).
- **MISSING:**
  - **Faithful PC090OJ object-RAM mirror** of `0xD00000..0xD03FFF` (or the `0x800` active range).
  - **VBlank scan** of the `0x800` active range decoding all 256 entries uniformly.
  - **Global flip control** (offset `0x0DFF` / `m_ctrl` / flipscreen transform).
  - **Signed-style coordinate wrap** (`x>0x140 → x-=0x200`, same for Y).
- **UNKNOWN:**
  - Whether `a5@(20)` reliably equals arcade `sprite_ctrl` at all sprite-emit times (needs runtime confirmation).
  - Whether the hooked producers cover **all** sprite sources (enemies/objects/player), or only the hooked features (score, status, a few blocks).
- **INVALID MODEL:**
  - **The overall sprite model is invalid as a faithful translation:** it is **hook-slot/event-oriented** (per-PC hooks + build-baked entry→slot LUT + descriptor-valid/touched/active_count) rather than **object-RAM-mirror-oriented**. `staged_sprite_descriptor_table`, `staged_sprite_active_count`, `descriptor-valid/touched`, and the fixed `pc090oj_slot_lut` are translation inventions treated as truth, not derived from a mirror. This is the structural root of the never-working sprite layer.

---

## == DESIGN DIRECTION == (design only — pure assembly, translation layer, not an emulator)

**Recommended architecture — object-RAM-mirror + VBlank scan (the prompt's preferred shape, confirmed correct):**
1. **PC090OJ object-RAM mirror** in Genesis WRAM: mirror at least the active `0x800` bytes (256 × 8-byte entries) of `0xD00000` (full `0x4000` optional; only `0x800` is drawable). A new BSS buffer `pc090oj_object_ram` (0x800).
2. **On every translated PC090OJ write** (`0xD00000..0xD007FF`): update the mirror word. Route via the existing `genesistan_hook_3ad44_dispatch` PC090OJ branch — but change it from "clear a slot" to "write the word into the mirror at `(A0−0xD00000)`". Also capture `0x380000 sprite_ctrl` (add a small hook or read the confirmed `a5@(20)` shadow) and offset `0x0DFF` global flip into the mirror/state.
3. **Dirty flags for performance only** (not truth): mark the mirror dirty on any active-range write so VBlank can skip when unchanged.
4. **VBlank scan** (`vdp_commit_sprites`): iterate the 256 entries in priority order (entry 0 first).
5. **Decode each 8-byte entry per MAME:** flipY=word0.b15, flipX=word0.b14, color=word0.low4 | ((sprite_ctrl&0xE0)>>1); Y=word1&0x1FF; code=word2&0x1FFF; X=word3&0x1FF; then signed-wrap (`>0x140 → −0x200`); apply global flip if `m_ctrl&1==0` (`x=320−x−16`, `y=256−y−16`, toggle flips); apply arcade Y=8 / X display-origin bias consistent with the PC080SN work (KF-015/Build 0096) so sprites align with the tilemaps.
6. **Determine drawable entries:** skip transparent/empty (code 0 or offscreen after wrap) so they don't consume Genesis SAT slots.
7. **Convert each drawable entry → Genesis SAT** (Y, size=16×16→SAT size bits, tile = code→VRAM-slot via a PC090OJ code→slot LUT + preload [reuse `pc090oj_genesis.bin`/preconvert infra], link, X, priority high, palette line from colbank).
8. **Build the Genesis SAT link chain** as the final output step (already present).
9. **Hide/terminate unused SAT entries** (link=0 after the last used, or park at Y=off-screen).
10. **Use current `sprite_ctrl` palette bank** (`(…&0xE0)>>1`) — already correct.
11. **Apply PC090OJ global flip** (the currently-MISSING `0x0DFF` transform).
12. **Preserve sprites-over-everything** priority (high-priority SAT) unless evidence shows a case needing per-sprite priority vs Plane A.

**Minimal future implementation step (for Cody, later — NOT now):** (a) add the `pc090oj_object_ram` 0x800 mirror + repoint the `0x3AD44` dispatch PC090OJ branch to write the mirror instead of clearing a slot; (b) replace `vdp_commit_sprites`'s hook-fed staging with a **scan-decode-emit** of the mirror's 256 entries → `staged_sprite_sat` (first ≤80 drawable, priority order) → existing link-chain/DMA. Validate on a single title/attract frame before removing the legacy per-site hooks.

**Files/labels likely involved (future):** `apps/rastan-direct/src/pc090oj_hooks.s` (`genesistan_hook_3ad44_dispatch` PC090OJ branch, `vdp_commit_sprites`, the per-site hooks → deprecate once the mirror covers them), `pc090oj_assets.s` (`rastan_pc090oj` tiles reused; `pc090oj_slot_lut` → replaced by a code→VRAM-slot LUT), a new BSS `pc090oj_object_ram`, and a tile code→slot LUT generator under `tools/translation/` (reuse `preconvert_pc090oj_tiles.py`). Sprite_ctrl (`0x380000`) capture + `0x0DFF` flip state.

**What's wrong/incomplete now:** no object-RAM mirror; no 256-entry VBlank scan; missing `0x0DFF` global flip and signed-coordinate wrap; SAT built from partial per-site hooks + fixed slot LUT (cannot represent dynamic object RAM); coverage limited to hooked producers.

**What NOT to do:** no C/SGDK/MAME-copy; no emulator-style PC090OJ device model (the scan is a per-VBlank translation, not a cycle model); no Genesis-owned sprite lifecycle beyond the VBlank commit; no scaffolding/fake sprite data/seeding; no arithmetic address mapping (use JSON for any code-site work); do not change arcade game flow (the arcade still writes `0xD00000`; we mirror + translate).

**Validation plan (future):** capture (1) the **PC090OJ object-RAM** (`0xD00000` mirror, first `0x800`) at a title/attract frame, (2) the **true Genesis VDP SAT** at `0xF800` that frame, (3) the composite. Prove the scan-emit reproduces the arcade's drawable entries (decode matches MAME per-entry), sprites appear at correct positions/palette, and `≤80` cap doesn't drop a needed title sprite. No regression to tilemap/text paths.

---

## == GENESIS LIMITS ==

- **80-entry SAT handling:** Genesis has 80 hardware sprites; PC090OJ has 256 active entries. Emit the **first ≤80 drawable** entries in PC090OJ **priority order (entry 0 first)** — the simplest faithful-enough policy; do **not** build a complex allocator.
- **priority preservation:** by scanning entry-0-first and filling Genesis SAT in that order, arcade priority (first = highest) is preserved; the link chain keeps SAT order = priority.
- **offscreen/empty handling:** entries that are transparent (code 0) or fully offscreen (after signed-wrap + flip) must **not** consume a Genesis SAT slot — skip them, so the 80-slot budget goes to visible sprites (this is what makes ≤80 faithful-enough in practice).
- **termination:** terminate the Genesis SAT link chain after the last emitted entry (link→0 or park remaining at off-screen Y) so stale entries don't render.
- **proving dropped entries aren't relevant:** title/attract almost certainly uses far fewer than 80 visible sprites; validate by counting **visible** (drawable) entries in the captured object-RAM frame — if ≤80, nothing is dropped. Flag (via `log`/report, not silent) if a frame ever exceeds 80 visible.

---

## == POMMEL CONTEXT == (Part F — do not force a pommel fix)

1. **Does Cody's negative staged-SAT capture still matter?** Partially — it shows the *current* `staged_sprite_sat` has no pommel entry, i.e. the current **hooks** produced none. It matters as evidence about the current pipeline's output.
2. **Does it become weaker given no faithful mirror?** **YES** — because the staged SAT is built from **partial per-site hooks**, its *absence* of a pommel entry does **not** prove the arcade PC090OJ object RAM has no sprite there; it only proves the hooked producers didn't emit one. So the negative capture cannot exonerate PC090OJ for the pommel.
3. **Does true VDP SAT (`0xF800`) capture still matter?** **YES, more than ever** — it shows what is actually composited on screen. If a real (possibly garbage) SAT entry sits over the pommel, that's the artifact; if not, the pommel isn't a Genesis sprite.
4. **Could the pommel be unrelated to PC090OJ?** **YES, possibly** — with Plane B clean, Plane A = lower text, Window OFF (refuted), the pommel stripe could be (a) a mis-emitted/garbage sprite from the current incomplete hooks, or (b) something else. It is not proven to be PC090OJ.
5. **Next evidence/step:** capture the **true VDP SAT at `0xF800`** + the **PC090OJ object-RAM state** at the title frame; compare. Then either the pommel is a sprite (resolved/exonerated by the object-RAM-mirror redesign) or it isn't. **The strategic fix is the architecture redesign (object-RAM mirror), which repairs the whole sprite layer; the pommel is one symptom, not the driver — do not scope the redesign to the pommel.**

---

## Open / Closed Issues Impact

- **Open issues touched:**
  - **OPEN-024** (PC090OJ sprite subsystem incomplete/garbage): this audit provides the **root architectural cause** (hook-slot vs object-RAM mirror) and the design direction. Not closed; substantially advanced.
  - **OPEN-001** (title/attract graphics incomplete): context — the sprite layer is a major missing piece; the pommel is one symptom.
  - **OPEN-006** (sprite palette/high-bank): context — the colbank `(sprite_ctrl&0xE0)>>1` path is verified-correct in derivation; the redesign carries it forward.
  - **OPEN-023** (Window): contrast only — Window refuted for the pommel; sprite/SAT is the live candidate.
  - OPEN-015 / OPEN-021: not touched (no crash-numeric-field or title/high-score-text reliance).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend re-scoping OPEN-024 around "object-RAM-mirror architecture" per this audit, if Tighe agrees).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** implementation (mirror + VBlank scan-emit); the `0x0DFF` global flip + signed-coordinate wrap (part of the redesign); the true-VDP-SAT / object-RAM capture (evidence for validation and the pommel question); the code→VRAM-slot tile LUT for sprites.

## files changed
NONE (analysis/design only).

## AGENTS_LOG updated
YES (analysis-doc log entry per standing process).

## STOP status
**NO** — audit complete. The current model is INVALID as a faithful translation (hook-slot/event-oriented, no object-RAM mirror); a faithful object-RAM-mirror + VBlank-scan design is feasible in pure assembly (no C/SGDK/MAME-copy/emulator-lifecycle) and is specified as design direction. No implementation performed.
