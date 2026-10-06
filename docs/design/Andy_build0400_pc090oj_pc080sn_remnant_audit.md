# Build 0400 — PC090OJ / PC080SN Hardware-Emulation Remnant Audit

**Author:** Andy · **Date:** 2026-10-05 · **Branch:** `rastan-direct-proposal` @ `9094d21` ("Pre Buidl 401" = Build 0400 source)
**Type:** AUDIT ONLY. No ROM produced. No gameplay / graphics / scheduling / VBlank / sprite / tilemap / collision / palette / rope / optimization change made. Build 0400 source restored and verified clean at HEAD; Build 0401 preserved under `docs/design/build0401_shelved/`.

---

## 0. Headline Finding (read this first)

**Build 0400 contains ZERO arcade-hardware bus emulation.** There is no live read or write to any
PC090OJ / PC080SN / palette / sprite-control / input-latch / watchdog address anywhere in the
Genesis source. Every former hardware *mirror* has already been retired:

- **No PC090OJ object-RAM mirror.** The D-range (`0x00D00000..0x00D007FF`) is never dereferenced.
- **No PC080SN C-window RAM mirror.** The C-range (`0x00C00000..0x00C10000`) is never dereferenced
  as arcade tilemap RAM. (`0x00C00000` is touched only as the *Genesis VDP data port* in the
  native PIO/DMA plane writers — a legitimate Genesis output, not arcade emulation.)
- **No palette-RAM mirror.** Arcade `0x00200000` is never dereferenced.
- **No sprite-ctrl / scroll / ctrl register emulation.** `0x00380000`, `0xC20000`, `0xC40000`,
  `0xC50000` do not appear as live accesses.

A full-source literal sweep for arcade-hardware addresses returns only **five** hits, and **all
five are either comments or `cmpi`/`cmpa`/`subi` token arithmetic — none is a dereference**:

| Site | Literal | Use |
|---|---|---|
| `pc090oj_hooks.s:971` | `0x00380000` | comment only; hook takes the value in `d0` |
| `palette_hooks.s:304` | `0x00200000` | `cmpa.l` destination-token recognition |
| `palette_hooks.s:387,389,392` | `0x00200000/0x00201000` | token recognition / index math |

**Therefore the project's forbidden shape is already gone.** Build 0400 does **not** run:

> ~~arcade semantic state → emulated PC090OJ/PC080SN record → compatibility RAM → scan/decode/project → Genesis output~~

The last instance of the forbidden "scan/decode/project" stage — the **frontend 256-record
object-RAM scanner** (`.Lnq_frontend_object_scan`) — **has been removed** (`pc090oj_hooks.s:2353-2358`).

What Build 0400 actually runs is the project's *target* shape, with one asterisk:

> arcade semantic decision (arcade worker still executes, writing its own WRAM state)
> → **native hook: WRAM-state read + token decode + mapping/piece expansion**
> → native staged Genesis buffers → `dma_publish_frame` (dma.s) → VDP

So the real subject of this audit is **not** "what hardware emulation is left" (answer: none). It
is: **what still couples the native renderer to the arcade program, and what is dead weight.**
Those fall into three classes, inventoried below:

- **(A) Dead vestige** — clobbered loads, `rts`-stub hook bodies, uncalled arcade routines left as
  dead code. Removable with no behavioral risk.
- **(B) Translation bridge** — native hooks that read arcade WRAM descriptor/actor/palette state
  and arcade-written *destination tokens* (`0xD00460`, `0xC00000/0xC08000`, `0x200000`) as
  recognition/decode keys, then produce native Genesis output. **Correct and load-bearing.** This
  is where the Build-0400 performance cost lives; it is retired only by replacing the arcade
  producer, not by deletion.
- **(D) Diagnostics** — audit-guard traps, DMA self-test, VC_MARK profiling, compiled into the
  production ROM (73 references).

---

## PART A — PC090OJ (sprite) remaining architecture

### A.1 Hardware mirror: fully retired
`PC090OJ_HW_BASE = 0x00D00000` (`pc090oj_hooks.s:113`) appears only in `.equ` definitions,
comments, and token arithmetic. The authoritative comment (`:993-999`):

> "The PC090OJ D-range (`0x00D00000..0x00D007FF`) is fully retired: its only callers were the
> arcade object-RAM clear routines `0x03AD4C / 0x03AD72`, which are now RTS … so no D-range
> address ever reaches this dispatcher. No PC090OJ recognition remains here."

### A.2 Gameplay sprites — native, scene-gated (Category B bridge)
Hook structure (all gate on `genesistan_current_scene_id == 1`):

| Arcade PC | Hook | Gameplay action | Frontend action |
|---|---|---|---|
| `0x41DAE` | `genesistan_pc090oj_hook_target_41dae` | `native_stage_dispatch_41dae` → `pc090oj_native_emit_pass` | `rts` |
| `0x41F5E` | `..._41f5e` | `native_sprite_frame_begin` (clears native lane counts) | `rts` |
| `0x45DFA` | `..._45dfa` | `native_stage_dispatch_45dfa` → `pc090oj_native_emit_pass` | `rts` |
| `0x51AB6` | `genesistan_native_contact_coords_51ab6` | token-decode → arcade actor coords (contact list) | — |

`native_stage_dispatch_41dae/45dfa` walk the **arcade actor arrays in A5-WRAM** (`A5+0x508`
player, `A5+0x5C8` middle, `A5+0x2C8` back-enemy) and call `.Lnative_emit_actor_common`, which:
1. reads `a4@0x38` family → indexes relocated arcade family tables (`.Lnea_fam_bases`),
2. reads `a4@1` animation index → self-relative descriptor offset → piece stream,
3. expands the piece stream directly into the native Genesis SAT lanes.

**This is the Build-0400 performance root cause** (HEAVY profiling: `worker ≈ 55,600 + 2,609 ×
emitted_sprites`). The 2,609 cyc/sprite is this per-piece arcade→Genesis expansion plus the
runtime residency resolve — **our implementation cost, not Genesis hardware cost**. It is
Category B (load-bearing), retired only by the resident/transient redesign (the Build 0401
direction), not by deleting scaffolding.

### A.3 The `0xD00xxx` token references — not hardware, two sub-cases
1. **Dead vestigial loads** (`:406 0xD001C8`, `:416 0xD00300`, `:426 0xD00460`, `:518 0xD00170`,
   `:538 0xD00460`, `:552 0xD00170`, `:562 0xD00300`): each `lea 0x00D00xxx, %a1` is **clobbered
   at `:613** (`lea .Lnea_fam_bases, %a1`) before any use. Pure dead weight (Category A).
2. **Live token decode** (`genesistan_native_contact_coords_51ab6`, `:829-836`): the arcade stored
   `0xD00460 + actor_index*0x50` tokens in its own registration list at `A5+0x1282`. The hook reads
   those *arcade-written* tokens from WRAM and does `subi.l #0x00D00460 / divu #0x50` to recover the
   actor index, then indexes `A5+0x2C8`. **No bus access to the D-range occurs** — it is arithmetic
   on a value the arcade wrote. Category B (couples to arcade token layout).

### A.4 Frontend sprites — native, object-RAM scan REMOVED
`pc090oj_native_emit_pass` (`:1522`) branches on scene:
- scene 1 → `.Lnq_gameplay`
- scene 0 stage 0 → `.Lnq_title` (static native HUD table `.Lnq_title_labels` + live score/credit)
- scene 0 stage≠0, scene 2 → `.Lnq_frontend_native`

`.Lnq_frontend_native` (`:2359`) comment is explicit (`:2353-2358`): *"The former
`.Lnq_frontend_object_scan` + its 256-record object-RAM loop, decoder, and residency tail are
REMOVED; every frontend sprite is produced by native Genesis owners."* The remaining
`.Lnq_frontend_object_scan` strings are **comments only** — there is no live label. `native_frontend_hud_emit`
(`:1694`) builds the credit/score/HUD block natively.

**Answer to the task's explicit question:** No frontend scene performs
`arcade object representation → PC090OJ-style RAM/records → scanner/decoder → Genesis SAT`. That
pipeline was retired at the frontend builder boundary (Build 0272/0273: `0x3B8B0` → `rts;nop`,
`0x3B902` body-replaced, `0x3B930` generic copier left uncalled/dead) and the scanner itself was
later deleted. Every frontend sprite is now native.

### A.5 PC090OJ retired-to-`rts` hook bodies (Category A dead vestige)
`genesistan_pc090oj_hook_target_3b902` (`:207` `rts`), `..._3b926` (`:216` `rts`),
`..._59f5e`, `..._5a098` status-sprite, and the `0x3AD4C/0x3AD72` object-RAM clears — all reduced
to register-preserving `rts`. They service nothing; they exist only so the arcade call sites return
cleanly. Removable once the arcade call sites themselves are cut.

---

## PART B — PC080SN (tilemap / scroll / palette) remaining architecture

### B.1 Hardware mirror: fully retired
The C-window bases `ARCADE_PC080SN_CWINDOW_BASE_BG = 0x00C00000` / `_FG = 0x00C08000`
(`tilemap_hooks.s:94-95`) appear **only** in `cmpi.l` range checks and `subi.l` offset decodes
(≈20 sites: `:1301, :1307, :1480, :1533, :1785, :1838, :1871, :1924, :2132, :2137, :2225 …`). The
pattern everywhere is identical:

```
cmpi.l #ARCADE_PC080SN_CWINDOW_BASE_BG, %dN     ; is this arcade dest in the BG C-window?
cmpi.l #(..._BASE_BG + ..._BYTES), %dN          ; range check
subi.l #ARCADE_PC080SN_CWINDOW_BASE_BG, %dN     ; -> tile offset, translate to Genesis plane
```

The arcade writes its tilemap *destination address* (a C-window token) into its WRAM descriptors;
the native hook recognizes the range and decodes the offset into a Genesis plane row. **The C-range
is never dereferenced as memory.**

### B.2 Arcade descriptor state lives in A5-WRAM (Category B bridge)
`ARCADE_PC080SN_*_OFFSET` (`:76-93`) are offsets into the arcade's own WRAM PC080SN state
(`A5+0x1000..0x1386`: desc lists, scroll X/Y FG+BG, strip index/group, walker, table index).
`PC080SN_DESC_REBUILD_*` (`:124-132`, `0x00FF1000+`) are the Genesis-side working copies. The native
plane producers read arcade descriptor state and rebuild Genesis plane strips → staged buffers →
`dma_publish_frame`.

### B.3 Scrolling tilemap — native, scene-gated
The BG/FG plane-strip rebuild and directional dispatch gate on `SCENE_GAMEPLAY_ID` (`:1237, :1287,
:1559, :4132`). Hook families (from `rastan_direct_remap.json`):
- `genesistan_hook_tilemap_plane_a` (+ `selector0`/`selector12` native variants),
- `genesistan_plane_a_pan_publish_entering_rows_up/down`,
- `genesistan_pc080sn_directional_dispatch_native`,
- `genesistan_hook_pc080sn_bg_scroll_fill` / `..._fg_scroll_fill`,
- six `genesistan_hook_inline_fg_write_3a5xx..3d04c` inline-write intercepts,
- `genesistan_phase3_fg_anim_native`, `genesistan_collision_surface_mark_visual_native`.

### B.4 Textwriter / glyph / number renderers — native fill, arcade glyph source (Category B)
`genesistan_hook_textwriter_dispatch` (`:3942`) still calls **`jsr 0x000565CE`** (arcade glyph
fetch), then decodes the C-window dest token into BG/FG range and routes to
`genesistan_hook_tilemap_bg_fill` / `_fg_fill`. It has **no scene gate** — it serves any scene that
runs arcade text (HUD scores in gameplay; "PUSH BUTTON", ranking, ROUND/READY, credits in
frontend). Companion hooks: `genesistan_hook_text_writer_3c4d2/3c550/3c586/3c636/3c6dc/3c75c/3c7a4/
3c830/3c950`, `genesistan_hook_number_renderer_3c2e2`, `genesistan_hook_glyph_renderer_3bd48`,
`genesistan_hook_highscore_fg_producer`, `genesistan_hook_cwindow_clear` (`:3625`),
`genesistan_hook_itempage_strip_populate` / `_blit`, `genesistan_hook_pc080sn_descriptor_rebuild`.

This is the **most arcade-coupled** native subsystem remaining: it still re-enters arcade code
(`0x565CE`) for the glyph bitmap and still keys off C-window destination tokens.

### B.5 Transitional dispatcher scheduled for deletion
`genesistan_hook_3ad44_dispatch` (`:989`) recognizes the C-range (`cmpi.l #0x00C00000 / #0x00C10000`,
`:1002-1005`) and routes to BG names / BG scroll / FG. Its own comment (`:997-1000`): *"survives
ONLY for its still-live PC080SN C-range callers (`0x03AE70/80`, `0x03AF38/48`) and is scheduled for
deletion once PC080SN C-range ownership is native (see the PC080SN Final-Retirement Handoff)."*

### B.6 Palette — native staging, arcade token recognition (Category B)
`palette_hooks.s`: `genesistan_palette_hook_45dae` (`:301`) recognizes arcade dest `0x200000`
(`cmpa.l`, `:304`), converts XBGR555→CRAM, writes `staged_palette_words`; it is **skipped for scene 1**
(`:315`, gameplay Lines 0/1/3 are Test-owned). `genesistan_palette_hook_59ad4` is the gameplay
bank-2→Line-2 loader. `..._03ab00`, `..._3ba64` complete the set. The sprite-ctrl colour bank
(`genesistan_pc090oj_sprite_ctrl_write_d0`, `:975`) shadows the arcade value into
`pc090oj_sprite_ctrl_shadow` (WRAM) to drive palette-bank reevaluation — no HW access.

---

## PART C — VBlank / frame-worker legacy call tree

Frame structure (established in prior tasks, unchanged in this audit):

```
IRQ6 _vblank_service (0x700C2)
  -> input shadow (genesistan_shadow_input_390001/3/5/7)
  -> sprite guard (vdp_prepare_sprites)
  -> dma_publish_frame (dma.s)            ; publishes frame N-1: palette, tiles, BG strips,
  |                                        ;   FG strips, sprites (pattern+SAT), scroll
  -> tail-JMP arcade worker 0x3A208 (raises IPL7)
       |
       +-- arcade frame worker executes (semantic owner — CORRECT per CLAUDE.md)
       |     ... writes its own A5-WRAM PC080SN descriptors + actor arrays ...
       |     ... hits 64 intercepted sites in 0x03A0xx-0x03AFxx ...
       |         each redirects PC080SN plane/scroll/text production to a native hook
       |         (B.3/B.4) which stages Genesis plane/SAT state
       |     ... hits 0x41DAE/0x45DFA sprite dispatch -> native sprite staging (A.2) ...
       |
  -> restore IPL (0x3A27A) -> RTE (0x3A27E)
  -> mainline spin (0x3B0B6 / 0x3B0FE)
```

**64 hook sites** live in the `0x03A0xx-0x03AFxx` worker region (count from
`rastan_direct_remap.json`). The arcade worker **still runs** and is the authoritative semantic
owner — this is correct and must stay. What is intercepted is every *graphics-production* point: the
worker computes WRAM descriptor/actor state, and the native hooks decode that state into staged
Genesis output. The structural cost is that the arcade worker produces into WRAM in its arcade
layout and we **re-decode** it every frame (the Category-B bridge), rather than the worker producing
native-shaped state directly. `dma_publish_frame` is the single VDP publication point; no other
runtime site issues a VDP DMA (crash handlers are error-path only).

---

## PART D — Scene-by-scene runtime matrix

Derived from the static scene gates (deterministic and complete — every hook's scene branch is in
source). **Gameplay row confirmed at runtime** by the prior HEAVY profiling run (native worker, VDP
ownership gate PASSED — no non-publication VDP writes). Frontend rows are static-derived; a single
GENESIS NTSC MAME frontend trace is the one open runtime confirmation (see §F).

| Subsystem | Scene 1 (gameplay: outdoor/cave/boss) | Scene 0 stage 0 (title) | Scene 0 stage≠0 / Scene 2 (end-round, ranking, throne/PUSH-BUTTON) |
|---|---|---|---|
| **Sprite dispatch** | native `41dae/45dfa → emit_pass → .Lnq_gameplay` | `.Lnq_title` native HUD | `.Lnq_frontend_native` native |
| **Object-RAM scan** | none | none | **none (scanner removed)** |
| **Frontend HUD emit** | n/a (gameplay HUD via `.Lnq_gameplay`) | `native_frontend_hud_emit` | `native_frontend_hud_emit` |
| **Plane strips (BG/FG)** | native, scene-gated | native | native |
| **Textwriter (text→plane)** | active (HUD scores) — arcade `jsr 0x565CE` glyph + native fill | active (title/credits) | active (ranking/ROUND-READY/PUSH-BUTTON) |
| **Palette 45dae (`0x200000`)** | **skipped** (Lines Test-owned) | active | active |
| **Palette 59ad4 (bank2→Line2)** | active (sky) | per-scene | per-scene |
| **Sprite-ctrl shadow** | active (colour bank) | active | active |
| **Arcade HW bus access** | **none** | **none** | **none** |
| **Publication** | `dma_publish_frame` | `dma_publish_frame` | `dma_publish_frame` |

Observation: **the frontend and gameplay paths now share the same native producers.** The only
scene-conditional differences are the palette-line ownership gate (45dae skip in scene 1) and the
sprite emit entry (`.Lnq_gameplay` vs `.Lnq_title`/`.Lnq_frontend_native`). There is no
scene-specific legacy renderer — the project's anti-goal (a hybrid chosen by increasingly specific
scene conditions) is **not** present.

---

## PART E — "Nasty bits" ranking (most load-bearing / most coupling / most risk, first)

1. **The Category-B sprite bridge in `.Lnative_emit_actor_common` (performance root cause).**
   `worker ≈ 55,600 + 2,609×emitted_sprites`; median 208K cyc > 128K frame budget → the slowdown.
   Not scaffolding — it is the live renderer. Retired only by the resident/transient redesign
   (baked mappings + resident art, Sonic model), i.e. the Build-0401 direction. **This is the one
   that actually matters for the game running at full speed.**

2. **Textwriter re-entry into arcade code (`jsr 0x565CE`) + C-window token keying (B.4).** The most
   arcade-coupled native subsystem; ungated by scene; blocks full arcade-text-code removal. Many
   hook sites (`3c2e2..3c950`, dispatch, cwindow_clear, itempage).

3. **Arcade-token coupling as recognition keys** (`0xD00460`, `0xC00000/0xC08000`, `0x200000`).
   Correct but fragile — couples native code to the arcade memory map. Blocks eventual deletion of
   the arcade worker's graphics production entirely.

4. **The 64-site `0x3A0xx` worker interception surface + `genesistan_hook_3ad44_dispatch`.** Large,
   transitional; `3ad44` is self-documented as "scheduled for deletion once PC080SN C-range
   ownership is native." High count = high maintenance surface, low individual risk.

5. **Live diagnostics compiled into the production ROM (Category D, 73 refs).** `audit_guard_*` trap
   in the textwriter fail path (`tilemap_hooks.s:3999`, spins on an out-of-range C-window token),
   `genesistan_pc090oj_dma_self_test` (`:2509`), `pc090oj_dma_test_*`, `VC_MARK`/`vblank_vc`
   publication-cost profiling (`dma.s:64-102`). These are not hardware emulation but should not ship
   in a release ROM.

6. **Dead vestige (Category A, zero-risk removal):** clobbered `lea 0x00D00xxx` loads
   (`pc090oj_hooks.s:406-562`), `rts`-stub hook bodies (`3b902`, `3b926`, `41f5e`-frontend, `59f5e`,
   `5a098`, `3ad4c/3ad72`), uncalled dead arcade routines (`0x3B930`, `0x3B8B0`, templates
   `0x3B950/0x3B9B0/0x3B9D4`).

---

## PART F — Recommended cleanup sequence (NOT to be implemented in this task)

Ordered to make the legacy subsystem *materially smaller* at each step, highest-value first, each a
coherent ownership boundary (not a screen-specific gate):

1. **Sprite producer rewrite (biggest win, separate build).** Replace the runtime arcade→Genesis
   piece expansion in `.Lnative_emit_actor_common` with resident art + baked mappings keyed on spawn
   pattern (resident for persistent actors like the player/continuous lizard-men spawns; transient
   for one-shot spawns). This is the only change that fixes the speed; it supersedes Build 0401's
   ownership-isolation-only approach by attacking the 2,609 cyc/sprite directly. Needs its own
   numbered build and the frame-ownership work as a companion, not a prerequisite.

2. **Textwriter native glyph source.** Replace `jsr 0x565CE` with a native glyph→plane producer so
   the text subsystem no longer re-enters arcade code; keep the C-window decode only until step 4.

3. **Diagnostic strip for release.** Gate `audit_guard_*`, `dma_self_test`, `pc090oj_dma_test_*`,
   `VC_MARK`/`vblank_vc` behind a build flag (default off for release) or remove. Per
   `feedback_no_nops_rts` / scaffolding-audit rules, disclose and get sign-off; do not silently
   `rts` live code.

4. **PC080SN C-range token retirement (the "Final-Retirement Handoff").** Once the arcade worker's
   tilemap production is fully owned natively, delete `genesistan_hook_3ad44_dispatch` and the
   C-window token recognition; the worker then stages native plane state directly.

5. **Dead-vestige sweep (zero-risk, do anytime).** Remove clobbered `lea 0x00D00xxx` loads, the
   `rts`-stub hook bodies, and the dead arcade routines — **after** confirming every arcade call site
   that targets them is itself cut (per "never delete a producer before replacing every live
   consumer"; the Build 0267 regression is the cautionary precedent).

**One cheap optional confirmation before step 1:** a single GENESIS NTSC MAME frontend trace
(title + end-round/ranking) to runtime-confirm the Part D frontend rows (which hooks fire, VDP gate
clean). Static gates already prove the dispatch; this only closes the empirical loop. Not run here to
respect the no-ROM / efficiency constraints.

---

## Diagnostics touched during this audit

None introduced. This was a static read-only audit over source + `specs/rastan_direct_remap.json` +
the existing Ghidra/arcade references. No temporary instrumentation was added, so none needs removal.
