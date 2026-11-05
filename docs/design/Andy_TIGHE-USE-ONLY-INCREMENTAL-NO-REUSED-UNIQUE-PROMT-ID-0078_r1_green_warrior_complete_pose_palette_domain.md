# PROMPT-ID-0078 — R1 Green Sword Warrior: complete pose palette domain

**Author:** Andy · **Date:** 2026-11-04 · **Method:** arcade 68000 decompilation/disassembly-first (no ROM
build, no Test.json change, no Cody files touched).

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0078`

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0078 Result

The Palette Composer and the offline reindex generator now cover the **complete same-actor base-`$033E`
animation domain**, resolved from the actor state machine (state dispatcher `0x40BAA`) — 17 programs across
four pose groups. Every pose inherits the **one** authored R1 mapping (single object_id). Tighe's authored
mapping was **not** changed; no ROM was built.

| Pose group | Programs | Source | Note |
|---|---|---|---|
| NORMAL walk/idle | `$93,$94,$95,$96` | ground engine `0x47140` (states 3-0C,12) + state-0x11 `0x4684E` (`+$3E==2`) | upright ~48×64, banks `[3,7]` |
| CROUCH / reaction | `$71,$72,$73` | state-0x0F **alt** path `0x40E0E` (`+$03!=0`, sfx `0x17`, **base-preserving**) | short ~24px poses; **Cody's runtime-observed block (0079 handoff)** |
| AIRBORNE / low | `$20,$21,$22,$23` | airborne engine `0x473B8` (states 0D/0E, fam2) → `$20+tbl[0x47562]` | compact ~32×48; the block that added the genuinely-new codes |
| ROPE / climb | `$4D,$56,$57,$58,$59,$5A` | state-0x11 `0x4684E` rope branch (`+$3E==8` / family 8) over the **shared** `$033E` sheet | Build 0534 coverage preserved + re-verified |

**`$74` is correctly EXCLUDED:** it is the state-0x20 handler `0x40F82`'s torch/light actor (sets base
`0x0DAB`, retarget `'I'`), **not** the knight. Cody's handoff said "`$71-$74`"; the knight's share of that is
`$71-$73` (base-preserving) — `$74` belongs to a different actor and would mis-recolor a torch.

### One premise corrected by the state-machine trace (please read)
The ROM does **not** support "the warrior's own `+$3E` becomes 8 while climbing." `+$3E` (family) is written
only at spawn (`0x4A08A`, from field-schedule byte `e[1]` = **2** here) and to `0x0C` on death-explode
(`0x40D4C`); it is **never** `8`. The rope programs are the `+$3E==8` (family-8) branch of engine `0x4684E`,
rendered from the **shared `$033E` sheet** — i.e. the same *visual* warrior climbing, implemented as a
distinct family. The one-visual-warrior grouping is kept exactly as Build 0534 shipped it; only the
provenance comment is corrected.

## Proven actor identity
Field schedule `0x4A104` (`tools/analysis/decode_field_schedule.py`): for 0x13E in `0x11..0x17`,
`f2/v0/c0 = $033E` — **family 2, variant 0, base graphics `$033E`**. Palette Decision
`PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` preserved. Rejected identities (lizardman `$004B`, flame `$0A73`)
stay rejected.

## Normal animation domain
`0x47140` fam2 → `$93+{0,1,3}` = `$93,$94,$96`; `0x4684E` (`+$3E==2`) → `$93+{1,2,3}` = `$94,$95,$96`.
Union = `$93-$96`. (Already covered; unchanged.)

## Rope / climbing animation domain
`0x4684E` rope branch (`+$3E==8`) → `$4D` + `$56-$5A`. Reached as a **family-8** behavior over the shared
`$033E` sheet. Banks `[0],[4],[9]` (a different palette regime from walk, consistent with a separate family).
`verify_green_knight` test 15 and `verify_reindexed` explicitly re-assert this block so a later refactor
cannot silently drop it (§14). Re-verified: renders from `$033E`; present in the Composer for R1.

## Crouch / duck (reaction) animation domain
State-0x0F `alt` path `0x40E0E` (reached when `+$03 != 0`) **preserves the actor base**, plays sfx `0x17`
on the first frame, and sets `anim = $70 + (++$08)` for `$08 = 1,2,3` → **`$71,$72,$73`**; at `$08 >= 4` it
leaves via `0x40E8E`. These render from the warrior's own `$033E` sheet as short (~24px-tall, 4-piece) low
poses. This is the block Cody observed at runtime for the warrior and handed over (PROMPT-ID-0079). State
dispatcher `0x40BAA` (signed-16 self-relative table at `0x40BC2`). Identified by the state machine, not by
visual frame-picking. (Their cells `0x342-0x34D` were already in the reindex set via the shared walk/rope
codes, so adding this block completes the Composer/audit; the material new-code fix is the AIRBORNE block.)

## Airborne / low-pose animation domain
`0x473B8` (states 0D/0E), fam2 branch at `0x4753C`: `anim = $20 + tbl[0x47562]`, `tbl={00,01,02,03}` →
**`$20,$21,$22,$23`** (states `<0x0D` give the walk set). Compact ~32×48, bank `[7]`. This block contributed
the genuinely-new reindex codes `0x366-0x37E`, which were previously unreindexed — the concrete palette-
fallback fix if the pose Tighe saw is this one. State-machine-derived (not runtime-confirmed as displayed).

## Other discovered same-actor states
`+$3E` is forced to `0x0C` only by `0x40D4C` (state 0x0F ordinary-death → base `0x0A73`/burst `0x9E-$A0`),
a destruction effect, not a browsable warrior pose — intentionally **not** added. `$74` is a torch (above).
No other engine writes a distinct family-2 display program from the `$033E` sheet.

## Complete `(code,effective-bank)` coverage
All 17 programs resolve through the shared compositor VM (`compositor_vm.py`, selector-0 table `0x3D09E`,
`anim_index = actor +$01`). The knight's runtime effective bank is `0x33`
(`gen_reindexed_pc090oj.USAGE_BANK`). Generator run against the **live** Test.json: knight domain **77 codes**,
all covered; `verify_reindexed`'s independent re-derivation reports `expected 77 covered 77 exact=True`.

## Palette Composer preview changes
`green_knight_usages()` (`server.py`) emits the complete domain with a per-frame `anim_state`
(`normal`/`crouch`/`airborne`/`rope`) so the UI shows the pose groups under the **one** `Green Sword Knight`
object per castle section (object_id `object:castle.green_sword_knight.r%d.n%x`). The authored R1 mapping is
applied to every frame (single object_id). Later-round sections remain browse-reference only (no inferred
R2-R6 mapping, §18).

## Offline generator changes
`gen_reindexed_pc090oj.GREEN_KNIGHT_ANIMS` extended to the 17-program domain. The generator reads the authored
`index_map` for `object:castle.green_sword_knight.r1.n3` and bakes the reindexed cells. No ROM was built:
generation was run to a **scratch** output only; the committed `pc090oj_sprite_variants.inc` / region bins were
left for Cody's integration build.

## Shared-code safety
The AIRBORNE block's new codes **`0x366-0x37E` (25 codes) are ALL knight-exclusive** — no sharing, no
divergence, so no per-bank variant is needed and no unrelated sprite is recolored. The CROUCH codes
(`0x342-0x34D`) are the warrior's own, already present via walk/rope — same actor, same map, no conflict.
Independent `verify_reindexed`: `cross-bank divergent 75 (all-distinct 75, bad 0)`, `stray writes = 0`,
`mismatched = 0`, Rastan retention `344 / 0`, all enemy objects unchanged. The two divergent blocks (`0x28E`,
`0xA73`) are unrelated (burst / lizardman·chimera·insect). No global code-based recoloring.

## Verification
- `verify_green_knight.py` (extended): **23/23 PASS** — complete domain, crouch `$71-$73`, airborne `$20-$23`,
  rope preserved, torch `$74` excluded, single-object inheritance, `anim_state` tagging, and an **exact
  source-index → authored-destination-index** transform check from the live Test.json (no color-only PASS,
  §17); Test.json SHA unchanged.
- `verify_reindexed_pc090oj.py` (extended, independent re-derivation): **VERIFY PASS** against a scratch build
  from the live Test.json; knight domain exact=True; Rastan/enemy retention intact; stray=0.
- `verify_r1s2_castle_browser.py`: 15/15 PASS (unchanged behavior).
- Test.json SHA-256 before == after: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`.

## Cody Integration Handoff
- Regenerate `apps/rastan-direct/out/pc090oj_sprite_variants.inc` (and region bins) from the updated
  `gen_reindexed_pc090oj.py` against the production profile during the next ROM build; the generator and its
  verifier now expect the 17-program knight domain. I did **not** touch the committed `.inc` (it is modified
  in your working tree by your build).
- Resolved your 0079 handoff: of `$71-$74`, the knight's own block is **`$71-$73`** (state-0x0F alt,
  base-preserving). **`$74` is the state-0x20 torch (base `0x0DAB`)** — do not map it to the warrior.
- Remaining dynamic question for a short **ORIGINAL ARCADE MAME** capture: which of CROUCH `$71-$73` vs
  AIRBORNE `$20-$23` is the pose Tighe calls "crouch/duck" (both are now covered, so no fallback either way —
  the capture only sharpens the UI label). The AIRBORNE block is the one that added previously-missing codes
  `0x366-0x37E`.
- No transition / audio / Plane-A / `tilemap_hooks.s` files were touched.

## Files / Local Commits / Logs
- `tools/graphics_editor/server.py`, `gen_reindexed_pc090oj.py`, `verify_reindexed_pc090oj.py`,
  `verify_green_knight.py`; this report; `AGENTS_LOG.md`. No Test.json / palette_decisions.json / Cody files;
  no ROM/build counter change.

### Explicit report
- current Test.json SHA: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`
- normal programs: `$93,$94,$95,$96`
- **all climbing programs:** `$4D,$56,$57,$58,$59,$5A`
- crouch programs: `$71,$72,$73` (state-0x0F alt; `$74` excluded = torch base `0x0DAB`)
- every newly discovered same-actor program: `$71,$72,$73` (crouch) and `$20,$21,$22,$23` (airborne/low)
- all climbing states represented in Palette Composer: **YES**
- all crouch states represented in Palette Composer: **YES**
- Tighe's authored mapping changed: **NO**
- ROM/build counter changed: **NO**
- Cody files touched: **NO**
- GitHub push: **NO**

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0078`
