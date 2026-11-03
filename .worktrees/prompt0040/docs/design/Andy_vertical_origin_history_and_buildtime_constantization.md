# Vertical −8px Display-Origin History + Build-Time Constantization Audit (Andy)

**Date:** 2026-10-16 · **Type:** READ-ONLY history/source audit + implementation spec. **No**
production/Makefile/ROM/counter change, no runtime/gameplay/trace, Phase D/E not started. Output:
this report + an append-only `AGENTS_LOG` entry.

Evidence tags: **[SRC]** current Build-0435 source · **[DOC]** AGENTS_LOG/design report anchor ·
**[INFER]** reasoned · **[CONFIRM]** needs confirmation before implementation.

---

## 1. Executive conclusion

The vertical 8px adjustment is a **render-origin / viewport** choice, not a gameplay/world value. In
current Build 0435 it is **already expressed through named constants that are logically linked**:
sprite `PC090OJ_TO_GENESIS_Y_OFFSET = -8 (= -VDP_DISPLAY_ORIGIN_Y_BIAS)`, plane
`VDP_DISPLAY_ORIGIN_Y_BIAS = +8`, viewport `GENESIS_VIEWPORT_TOP/BOTTOM = 0/224`. The scattered
magic numbers the user worried about (Build-0179 `RASTAN_VERTICAL_CROP_BIAS`, Build-0282
`BACK_ENEMY −8`) are **already retired**. [SRC] **So constantization is largely done; the real
remaining work is to SPLIT the single shared origin into independent FRONTEND vs GAMEPLAY origins.**
The split is small: one shared sprite-Y transform site (`pc090oj_hooks.s:3050`) and the plane-Y bias
(`vdp_comm.s:366/377`) both reached in both scenes. Collision/hitboxes have **no** dependency on the
origin (Build 0282 proved the Lizardman fix was a collision-source bug, not the −8). Frontend can
keep its current origin while gameplay changes.

## 2. Original arcade Y-origin facts [DOC Build 0096]

Arcade Rastan composes a **240-line** picture; the arcade **visible-area top begins at raster Y=8**
(per `src/mame/taito/rastan.cpp set_visarea 8..247`). The X divergence (+16) is PC080SN
`scrolldx = −16`; the Y divergence (+8) is this display-origin/viewport fact — **not** dynamic
gameplay scroll. Genesis target = **224 lines** (do not pursue 240-line mode). The open question is
only how to frame the 240-line composition in 224 lines.

## 3. Build 0096 attribution history [DOC]

Historical analysis attributed the +16X/+8Y presentation divergence to the two arcade facilities
above (PC080SN scrolldx −16; arcade visible top Y=8). The Y issue was correctly classified as a
display-origin/viewport issue.

## 4. Build 0147 sprite/viewport change [SRC/DOC]

Introduced/generalized `PC090OJ_TO_GENESIS_Y_OFFSET = −8` and the viewport clip
`GENESIS_VIEWPORT 0..223` (`pc090oj_hooks.s:160-191`). Intent: arcade raster Y=8 → Genesis line 0;
title/frontend sprite alignment + natural clipping of the arcade top margin above the Genesis
viewport. **Title/attract result is GOOD — do not change frontend default.** [SRC + user]

## 5. Build 0179 background-bias change [DOC; superseded]

Background scroll replacement used `RASTAN_VERTICAL_CROP_BIAS = 8` for both BG and FG (crop 8 top/8
bottom; arcade 240 → Genesis 224) — the paired BG counterpart to the sprite −8. **Current status:
`RASTAN_VERTICAL_CROP_BIAS` is ABSENT from Build-0435 source** [SRC — grep returns nothing]; its role
is now carried by `VDP_DISPLAY_ORIGIN_Y_BIAS = +8` (the plane Y bias, `vdp_comm.s:78,366,377`).
**Sign relation:** sprite `screen_y = arcade_y + (−8)`; plane `bias = +8`. The plane adds +8 (shift
content down by the cropped top) while the sprite subtracts 8 (place arcade Y=8 at screen 0); the two
are the same positive origin (8) applied with opposite sign so sprite and background stay aligned.
[SRC/INFER]

## 6. Build 0205/0206 Lizardman evidence [DOC]

User observed the Lizardman ~8px low. Evidence centered on `PC090OJ_TO_GENESIS_Y_OFFSET = −8`. This
was the **render-origin suspicion** phase — not the final cause (see §8). Treat as historical
suspicion.

## 7. Build 0234 coordinate/compensation history [DOC]

Coordinate-model analysis: BG `Y_BIAS = +8`, sprite `Y_OFFSET = −8`; identified fragmented
render-vs-collision handling and object-specific adjustments (e.g. `.Lb2c8_yfix`, a move-up /
Lizardman / standing-sword cluster). **Current status: `.Lb2c8_yfix` and those object-specific −8
render compensations are NOT present in Build-0435 source** [SRC — grep returns nothing] — superseded
by the clean single-origin transform + the Build-0282 collision fix. Do not reintroduce them.

## 8. Build 0282 final Lizardman/collision correction [DOC — the decisive fact]

The final Lizardman grounding/hitbox issue was a **collision-source displacement bug**: GNU
displacement **20 decimal (0x14)** vs the original arcade **0x20**. Build 0282 corrected the
collision readers and **RETIRED an unproven `BACK_ENEMY −8` compensation.** **Therefore the final
proven cause was COLLISION SOURCE, not the −8 render origin.** Not every historical −8 belongs in the
new config: the `BACK_ENEMY −8` is an obsolete compensation that must stay removed. [DOC]

## 9. Complete chronological origin-change table

| Build | File/function | Old → new | Numeric | Reason | FE/GP/both | Domain | Superseded? | 0435 status | Future constant dep |
|---|---|---|---|---|---|---|---|---|---|
| 0096 | (analysis) | attribute +16X/+8Y | +8 Y | arcade visible top Y=8 | both | render origin | — | concept stands | yes (origin) |
| 0147 | `pc090oj_hooks.s` | add `PC090OJ_TO_GENESIS_Y_OFFSET=−8` + viewport 0..223 | −8 | raster Y=8→line0; FE clip | both | render + clip | — | **ACTIVE** (`:180,3050,3066`) | yes |
| 0179 | background commit | `RASTAN_VERTICAL_CROP_BIAS=8` BG/FG | +8 | 240→224 crop | both | render origin (plane) | **YES** → `VDP_DISPLAY_ORIGIN_Y_BIAS` | **RETIRED** (symbol gone) | yes (as plane bias) |
| 0205/06 | (evidence) | Lizardman −8 suspicion | −8 | render-origin suspicion | GP | render (suspected) | **YES** (not the cause) | n/a | no |
| 0234 | render/`.Lb2c8_yfix` | object-specific −8 cluster | −8 | render-vs-collision fragmentation | GP | render compensation | **YES** | **RETIRED** (symbol gone) | **NO (obsolete)** |
| 0282 | collision readers | disp `0x14`→`0x20`; drop `BACK_ENEMY −8` | — | collision-source bug | GP | **collision** | — | **ACTIVE** (collision correct) | **NO (collision, not origin)** |
| ~0250+ | native SAT emit | origin applied in shared native lane transform | −8 | native migration kept the origin | both | render origin | — | **ACTIVE** (`:3050`) | yes |

No rows invented; retired symbols confirmed absent in current source.

## 10. Current Build-0435 literal/symbolic dependency inventory [SRC]

| Site | Expression | Domain | FE/GP/shared |
|---|---|---|---|
| `pc090oj_hooks.s:180` | `.equ PC090OJ_TO_GENESIS_Y_OFFSET, -8` (`= -VDP_DISPLAY_ORIGIN_Y_BIAS`) | render origin (sprite) | shared |
| `pc090oj_hooks.s:3050` | `addi.w #PC090OJ_TO_GENESIS_Y_OFFSET, %d2` (shared SAT emit, after flip) | render (sprite Y) | **shared FE+GP** |
| `pc090oj_hooks.s:3066/3068` | `cmpi.w #GENESIS_VIEWPORT_BOTTOM/TOP` (clip on post-offset Y) | viewport clip | shared |
| `vdp_comm.s:78` | `.equ VDP_DISPLAY_ORIGIN_Y_BIAS, 8` | render origin (plane) | shared |
| `vdp_comm.s:366,377` | `addq.w #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0` (plane/scroll Y bias) | render (plane Y) | shared |
| `pc090oj_hooks.s:187-188` | `GENESIS_VIEWPORT_TOP=0 / BOTTOM=224` | viewport bounds | shared |
| bottom-status HUD raw Y (`#0x00E8`, `#0x00E4`) | raw arcade Y → shared sprite transform | render (follows sprite origin) | GP |

**Count:** ~**4 named origin constants** at ~**5 live code sites**, all already symbolic; **0 stray
origin magic-number literals remain** (the `#8` at `:372/419/510/802/899/1237/1323/1557/1626` are
loop/stride/BCD/count math, **not** origin — excluded with semantic proof). The viewport clip tracks
the origin automatically because it tests the post-offset Y. [SRC]

## 11. Obsolete compensations that must NOT become constants

- Build-0234 object-specific `−8` render cluster / `.Lb2c8_yfix` — **retired**, keep removed.
- Build-0282 `BACK_ENEMY −8` — **retired** (the real fix was collision-source `0x14`→`0x20`), keep
  removed. Do not parameterize either; they were bugs/divergence, not features.

## 12. Frontend current-origin contract [SRC/user]

Frontend/title/attract uses the shared origin = **8** (sprite −8, plane +8, clip 0..223). Title and
attract presentation is **GOOD and must not change**. This is the `RASTAN_FRONTEND_Y_ORIGIN = 8`
default.

## 13. Gameplay current-origin contract [SRC]

Gameplay currently uses the **same** shared origin = **8** (identical transform/clip/plane bias — the
native migration kept one origin for both scenes). This is the `RASTAN_GAMEPLAY_Y_ORIGIN = 8` default.
**The only reason gameplay can't be changed independently today is that the sprite transform
(`:3050`) and plane bias (`vdp_comm.s`) are a single shared value, not scene-selected.**

## 14. HUD coordinate relationship [SRC/DOC]

- **Top HUD** (`.Lnq_project_p1_hud` gameplay, `.Lnq_title_emit_scores` frontend): **screen-fixed
  native coordinates** (e.g. digit X=0x08..0x30, small fixed Y). It is placed directly in Genesis
  screen space, so it does **NOT** go through the arcade→Genesis −8 transform and should **NOT**
  inherit the gameplay origin. **Do not move the accepted top HUD.** [SRC/INFER]
- **Bottom/status HUD** (newly decompiled: reserve-lives raw Y `0xE4`; energy/pickup/persistent-ROUND
  raw Y `0xE8`): these are **raw arcade Y** that flow through the shared sprite transform, so they
  **would inherit the gameplay origin** (`screen_y = rawY − GAMEPLAY_Y_ORIGIN`, then viewport-clip).
  e.g. energy `0xE8(232) − 8 = 224` → at the viewport bottom edge; a different gameplay origin moves
  the whole bottom HUD coherently with the gameplay sprites. **[CONFIRM]** the exact bottom-HUD Y
  sites belong to the status producer before relying on this mapping; do not implement/move now.

## 15. Proposed build-time constant model

**Two user-facing positive logical origins, one per presentation domain:**
- `RASTAN_FRONTEND_Y_ORIGIN` (default **8**)
- `RASTAN_GAMEPLAY_Y_ORIGIN` (default **8**)

One logical origin per domain; derive every subsystem sign from it (no per-subsystem configurable
values — that recreates the divergence we removed). Keep `VDP_DISPLAY_ORIGIN_X_BIAS=16` and the
viewport bounds as-is (X and the 224 viewport are not the experiment). Names provisional; adopt only
if they remain the best fit after Cody's source pass.

## 16. Exact derived expressions by subsystem

Let `O` = the **active** domain origin (frontend producers use `RASTAN_FRONTEND_Y_ORIGIN`, gameplay
producers use `RASTAN_GAMEPLAY_Y_ORIGIN`):
- **Sprite (native SAT, `pc090oj_hooks.s:3050`):** `screen_y = arcade_y − O` (replace the literal
  `PC090OJ_TO_GENESIS_Y_OFFSET` with `−O_active`).
- **Plane A / Plane B / scroll (`vdp_comm.s:366/377`):** `bias = +O` (replace
  `VDP_DISPLAY_ORIGIN_Y_BIAS` with `O_active`). Plane and sprite MUST use the same domain `O` so BG
  and sprites stay aligned.
- **Viewport clip (`:3066/3068`):** unchanged bounds `0..224`; the test on post-offset Y tracks `O`
  automatically — no separate clip constant needed.
- **Bottom-status HUD (raw arcade Y):** inherits `screen_y = rawY − GAMEPLAY_Y_ORIGIN` via the sprite
  transform (no new code).
- **Top HUD (screen-fixed):** independent of `O` (do not derive).
- **Collision / hitbox / actor Y / ground / sword overlap / collision-map row:** **independent of `O`
  — NO dependency** (world/semantic domain; Build 0282). Must not move when `O` changes.

**Selection mechanism (no runtime scheduler):** the frontend vs gameplay scene split already exists
in `pc090oj_native_emit_pass` (scene 1 → `.Lnq_gameplay`; scene 0/2 → `.Lnq_title`/`.Lnq_frontend_native`)
and in the plane/scroll commit. Set a small resident word `native_active_y_origin` (and the plane
equivalent) to the correct **compile-time constant** at each scene branch entry; the shared sprite
transform and plane bias read it. This is a finite compile-time-driven selection inside existing
presentation code — no runtime ownership change. If both origins are equal (the default), behavior is
byte-identical to Build 0435.

## 17. Makefile/config integration plan

Add `RASTAN_FRONTEND_Y_ORIGIN ?= 8` and `RASTAN_GAMEPLAY_Y_ORIGIN ?= 8` beside the existing flags
(`Makefile:50-75`), emit both into the generated `out/pc090oj_config.inc` receipt (extend the
`.equ`-generating printf at `Makefile:391` and the echo at `:392`). Requirements: command-line
override (`make … RASTAN_GAMEPLAY_Y_ORIGIN=4`); deterministic defaults (both 8 = current accepted
behavior); values recorded in the config receipt; **canonical/default unchanged** until Tighe decides;
**`_full_hud` inherits the same GAMEPLAY origin as canonical** unless explicitly overridden for a
controlled experiment; **`_d/_s/_do/_c` meanings unchanged**; **no new automatic variant
cross-products**.

## 18. Cody implementation checklist (do NOT implement in this task)

1. Add the two `.equ`/Makefile constants + config-receipt wiring (§17).
2. Define `native_active_y_origin` (and plane-Y-origin equivalent); set it from the compile-time
   constant at the frontend vs gameplay scene branches (`pc090oj_native_emit_pass`; plane/scroll
   commit path).
3. Replace the literal in the shared sprite transform (`pc090oj_hooks.s:3050`) with `−O_active`;
   replace `VDP_DISPLAY_ORIGIN_Y_BIAS` uses (`vdp_comm.s:366/377`) with `O_active`. Keep
   `PC090OJ_TO_GENESIS_Y_OFFSET` / `VDP_DISPLAY_ORIGIN_Y_BIAS` as the FRONTEND default values.
4. Leave the top HUD, viewport bounds, X bias, and all collision/actor/hitbox code untouched.
5. **[CONFIRM]** the bottom-status HUD raw-Y sites so their origin inheritance is intentional.
6. Keep default = both 8 → byte-identical to 0435.

## 19. Static verification requirements

- **Default equivalence:** with both origins = 8, the assembled sprite Y transform, plane bias, clip,
  HUD, and SAT output are **byte-identical** to accepted Build 0435.
- **Independence:** changing `RASTAN_GAMEPLAY_Y_ORIGIN` alone leaves **all frontend producer output
  unchanged** (prove the frontend path reads only the frontend origin).
- **Domain isolation:** prove collision/actor-Y/hitbox/sword/collision-map code contains **no**
  reference to either origin constant (grep + call-path) — render-only coupling.
- **Single-origin-per-domain:** prove no subsystem reads a different origin than its domain's (no
  sprite=−8 / plane=+9 drift possible).
- **HUD:** top HUD coordinates unchanged under any origin; bottom-status HUD moves coherently with
  gameplay sprites only.

## 20. Remaining blockers / [CONFIRM]

1. **Bottom-status HUD raw-Y site ownership** — confirm the `0x00E8`/`0x00E4` sites are the status
   producer and flow through the shared sprite transform (so their origin inheritance is intended).
2. **Exact set of frontend vs gameplay emit entry points** where `native_active_y_origin` must be set
   — confirm `pc090oj_native_emit_pass` scene branches + the plane/scroll commit are the only two
   places, so no producer bypasses the selection.
3. No PC090OJ/collision restoration is involved; all blockers are static source confirmations.

---

**Production modified: NO. ROM built: NO. Gameplay driven: NO. New traces: NO. Build number consumed:
NO. Phase D/E: NO.**
