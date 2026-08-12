> **COMPLETED in Build 0273** (2026-08-08, after WSL restart restored MAME). The retirement was executed at the
> arcade-code boundary (0x3B8B0 + 0x3B902 → rts; clear workaround deleted; 0x3B930 preserved) and validated
> byte-for-byte on the reachable frontend states. See `Andy_build0273_arcade_hud_pc090oj_tail_retirement.md`.
> One correction to §1 below: the producer is **0x3B8B0 / 0x3B902** (proven by arcade `bsr` caller census); the
> "~0x5007C" address in the earlier trace was a spurious stack word. The §3 Y-convention hazard was **resolved** —
> `.Lnq_title_labels` matches the object-RAM label records exactly (the raw-table byte decode was misaligned).

# HANDOFF — Retire the Frontend HUD PC090OJ Tail at the Original Arcade-Code Boundary

**Agent:** Andy · **Type:** analysis/handoff (NO ROM produced, NO build number consumed, NO source changed this
session) · **Baseline:** Build 0272 (committed `9e61cfc`, tree clean, coverage `0x184AC0`, opcode count 221).

## 0. Why this is a handoff and not a build

The MAME validation environment is **non-functional this session**: every invocation (direct `mame megadriv`,
the `run_genesis_trace_wsl.sh` wrapper, and the previously-working `satdiff`/`reccode` harnesses) hangs in
OSD/SDL init and produces **zero output** even with `-verbose`, and must be hard-killed. This is a WSLg/SDL
wedge (the Build-0272 30 s smoke trace ran fine ~18 h earlier). Consequence: `make release`'s own smoke-trace
step would also hang, so a candidate ROM cannot even be confirmed to boot, and the task's mandatory multi-state
runtime validation (Rule 13 + the prompt's 7-state list) cannot be performed.

Per Tighe's instruction: **do NOT restart WSL from inside the agent session** (it would kill the session). This
document preserves all findings so a post-restart session executes the cut quickly and *validated*. **Chosen
label strategy (Tighe): FULL native labels + retire the builder** (not the digits-only variant).

No source files were edited this session. `git status` is clean at Build 0272.

## 1. The exact arcade HUD producer (proven, static — no MAME needed)

`relocation_delta = 0x200` (direct-execution copy: `runtime_genesis_pc = arcade_pc + 0x200`). The three
sub-producers are additionally **hooked** to native routines at runtime `0x70000+` via `opcode_replace`
(`genesistan_pc090oj_hook_target_3b902/3b926/3b930`, and `..._score_digit_3b802` which is inert since Build 0270).

### 1a. Main template builder — `arcade_pc 0x3B8B0` (runtime copy `0x3BAB0`); sole caller `0x3B06A`
Pure PC090OJ construction (Case A). Body:

| arcade_pc | insn | effect |
|---|---|---|
| 3B8B0 | `lea 0x3B950,a0` | source table (24 recs) |
| 3B8B4 | `lea 0xD00020,a1` | dest = record 4 |
| 3B8BA | `moveq #24,d1` | count 24 → records **4..27** |
| 3B8BC | `bsr 0x3B930` | copy |
| 3B8C2 | `bsr 0x3B802` | HS digit overlay (**inert** since 0270) |
| 3B8C6 | `moveq #9,d1` | |
| 3B8C8 | `lea 0x3B9B0,a0` | source (9 recs) |
| 3B8CC | `lea 0xD000E0,a1` | dest = record 28 |
| 3B8D2 | `bsr 0x3B930` | records **28..36** |
| 3B8D8 | `lea 0x3B9D4,a0` | source (9 recs); `moveq #9,d1` at 3B8D6 |
| 3B8DC | `lea 0xD00128,a1` | dest = record 37 |
| 3B8E2 | `bsr 0x3B930` | records **37..45** |
| 3B8E6 | `moveq #1,d1` | |
| 3B8E8 | `bsr 0x3B902` | records **17..21** (credit) |
| 3B8EC | `rts` | |

### 1b. Credit/digit updater — `arcade_pc 0x3B8EE`; callers `0x3A5EC`, `0x3A652`
`bsr 0x3B902` (records 17..21) + two `bsr 0x3B802` (inert). 

### 1c. Generic copier — `arcade_pc 0x3B930` → `genesistan_pc090oj_hook_target_3b930` (runtime `0x072898`)
Copies `d1` records of `[Ybyte, codebyte, Xword]` from `(a0)` into `(a1)` object-RAM records (word0=0, Y, code,
X-transformed via `jsr 0x5B712`). **GENERIC — DO NOT stub / RTS / teach about HUD.** Live callers: `0x3B8B0`
(3 sites) and `0x3B902` (via `0x3B912`). Stays alive as long as `0x3B902` is live.

### 1d. Shared sub-producers and ALL their callers (Rule-13 consumer surface)
- **`0x3B902`** (credit records 17..21; and via `0x3B912`→`0x3B930`): **8 callers** — `0x3A20E, 0x3A264,
  0x3A640, 0x3A6C4, 0x3A820, 0x3A8E0` (six **state-specific** HUD-setup routines), `0x3B8E8` (in 0x3B8B0),
  `0x3B8F0` (in 0x3B8EE). Hooked body = `genesistan_pc090oj_hook_target_3b902`.
- **`0x3B926`**: callers `0x3A9C6, 0x3A9D4`.
- **`0x3B802`** (digit emitter, **inert**): callers `0x3A66A, 0x3A9C0, 0x3A9CE, 0x3A9DA, 0x3B7A2, 0x3B7B0,
  0x3B7E0, 0x3B8C2, 0x3B8F6, 0x3B8FC`.

**Implication:** the frontend HUD is assembled by MULTIPLE state-specific routines in `0x3A2xx..0x3A9xx`, each
calling the shared sub-producers. A full retirement must enumerate each state caller and prove native ownership
for that state (this is the multi-state validation MAME is required for).

## 2. The template tables (decoded from `build/regions/maincpu.bin`; record = `[Yb, codeb, Xhi, Xlo]`)

Codes `0x2A..0x33` = digit glyphs (`0x2A + BCD`); codes `≥0x34` = label glyphs. **Native owns the digits;
the labels are what must be converted.**

`0x3B950` (recs 4..27): labels `4:3B/5:3A/6:3C/7:3D/8:3E` (Y0, "SCORE" row, X78..B8) · `9:37/10:38` +
`11..16:45` (Y F8, bottom-left row, X08..80) · **digit rec17 (2A,YEC,X0)** · labels `18:34/19:35/20:36`
(Y E8, X100..120) · **digit rec21 (2B,YE8,X128)** · **HS digits 22..27 (2A, Y0, XA8..80)**.
`0x3B9B0` (recs 28..36): **P1 digits 28..33 (2A, Y0, X30..08)** · labels `34:39 (Y10,X40) /35:48 (Y0,X28)
/36:46 (Y0,X38)`.
`0x3B9D4` (recs 37..45): **P2 digits 37..42 (2A, Y0, X110..E8)** · labels `43:39 (Y10,X120) /44:49 (Y0,X108)
/45:47 (Y0,X118)`.
`0x3B984` (recs 17..21, via 0x3B902 clear-path): **digit 17 (2A)** · labels `18:34/19:35/20:36` · **digit 21 (2B)**.

## 3. ⚠️ BLOCKER to resolve DURING implementation: native vs arcade Y-convention

`.Lnq_title_labels` (the existing native labels) is **NOT** a byte-identical transcription of these tables:
table recs 18..20/34/43 use `Y=0xE8/0x10`, while `.Lnq_title_labels` uses `Y=0x01E8` for the same glyphs (a
`0x100` delta). The title values were tuned to look right in the **title** state through `.Lnq_emit_entry`; the
scan renders the arcade records at `Y=0xE8` through `.Lpc090oj_decode_record` (+viewport offset). These two
coordinate conventions currently coincide *visually* only because both are correct in their own state — this
must be **verified in MAME**, per state, before trusting native labels in the scan-rendered states. This is the
precise Build-0267 hazard: do not extend native labels to a state whose on-screen result is unconfirmed.

## 4. Implementation plan (execute AFTER WSL restart restores MAME)

1. **Convert all frontend HUD labels natively.** Build a state-aware `native_frontend_hud_emit` label set from
   the arcade tables' **label** records (codes `≥0x34`; records 4..16,18..20,34..36,43..45) — semantic
   `{glyph, anchor_x, anchor_y}`, expanded to native SAT via `.Lnq_emit_entry`. Resolve §3: choose the Y value
   that reproduces the **scan's** current on-screen position (verify against Genesis-driver MAME AND arcade MAME
   per state). Reuse `.Lnq_title_labels` only after confirming its Y matches in each state; otherwise use the
   table's `Y=0xE8` form fed through the same transform the scan applies.
2. **Prove per-state coverage (Rule 13).** For EACH state caller (`0x3A20E,0x3A264,0x3A640,0x3A6C4,0x3A820,
   0x3A8E0` → 3b902; `0x3A5EC,0x3A652` → 3b8ee; `0x3B06A` → 3b8b0; plus 3b926 callers), identify the screen
   (title / throne-PUSH / story / ranking / ROUND-READY / credit) and confirm native emits its labels+digits.
3. **Retire the arcade builder at the arcade-code boundary** via `opcode_replace` (arcade_pc, so runtime copy
   `+0x200`): RTS/bypass `0x3B8B0` and the `0x3B902`/`0x3B8EE` HUD tails **only once every state consumer is
   proven native**. Because `0x3B902` is shared by 6 state routines, cut at each state's HUD-build boundary or
   at `0x3B902`'s hooked body — NOT by touching generic `0x3B930`.
4. **Delete the Build-0272 workaround:** remove `.Lnq_hud_clear_records`, `.Lnq_hud_owned_records`, the
   `0x2A..0x33` code-gated clear, and its comments (in `apps/rastan-direct/src/pc090oj_hooks.s`; also drop the
   `bsr .Lnq_hud_clear_records` inside `native_frontend_hud_emit`). Keep `native_frontend_hud_emit` itself.
5. **Keep `0x3B930` intact** for whatever remains live (it survives only while `0x3B902` has live non-HUD use;
   if all consumers retire, document it as now-dead rather than deleting mid-task).

Static completion proof to produce: arcade HUD tail no longer executed; no PC090OJ HUD records created; clear
routines deleted; `0x3B930` unmodified; scanner services only independent legacy families (0x5A098,
workram_block_sprites, D00298/D002B0).

## 5. Post-restart runbook (exact steps)

```
# 1. Confirm MAME works again (should print "Average speed" quickly):
pkill -9 -f mame
TRACE_DIR=<scratch> TAG=probe timeout -s KILL 60 mame megadriv \
  -cart dist/rastan-direct/rastan_direct_video_test_build_0272.bin \
  -video none -sound none -skip_gameinfo -nothrottle -seconds_to_run 6 \
  -autoboot_script <scratch>/satdiff.lua </dev/null
#    (satdiff.lua/reccode.lua harnesses are in the session scratchpad: .../scratchpad/hud/)
#    P1-Start driver = field ":ctrl1:mdpad:PAD|P1 Start"; credit reg 0xFF0117; object RAM 0xFF6F92.
# 2. Implement §4. 3. Build:
source tools/setup_env.sh && RASTAN_GAMEPLAY_HUD_SPRITES=2 make -C apps/rastan-direct release
#    (update CANONICAL_TOTAL_GENESIS_BYTES_COVERED in BOTH postpatch_startup_rom.py and
#     verify_canonical_rom.py to the value the build's invariant-failure message prints.)
# 4. Validate ALL states listed in §6 on Genesis-driver MAME vs Build 0272 (SAT byte-diff at 0xFF61CC),
#    and against original arcade MAME (roms/rastan.zip) for label ground truth.
```

## 6. Validation matrix to fill (per prompt)

MAIN TITLE (1UP/2UP, HIGH SCORE, live HS value, PUSH) · THRONE/PUSH (score/HS, labels, throne art) · STORY
(top HUD, INSERT COIN(S), story art) · RANKING (top HUD/HS, ranking list) · ROUND/READY (top score, ROUND 1,
READY!, no stale fragments) · CREDIT STATE (count + visibility) · GAMEPLAY (unchanged) · REMAINING LEGACY
(0x5A098, workram_block_sprites, D00298/D002B0 still render). Digit output is byte-identical-by-construction to
Build 0272 (records stay 0 → native draws); **labels are the validation risk** (§3).

## 7. State at handoff
- No ROM produced; build counter stays **272**; no source/spec/tool change this session; tree clean.
- Durable findings above (producer map, tables, Y-convention hazard) are the reusable result.
- Session scratchpad harnesses: `/tmp/claude-1000/.../scratchpad/hud/` (`satdiff.lua`, `reccode.lua`,
  `caller.lua`, `hcaller.lua`, etc.) — reuse post-restart; they are proven when MAME is healthy.

**It is safe to restart WSL now.**
