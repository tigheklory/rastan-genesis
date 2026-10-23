# Andy — AUDIO-015: Shared `$25` Restart Correction + GAME OVER Stop

**Task:** AUDIO-015 (continuing Cody's interrupted multi-song work) · **Issue:** OPEN-039 (remains OPEN) ·
**Agent:** Andy (Opus) · **Date:** 2026-10-23 · **Builds:** 0491 (multi-song finish), **0492** (this fix).

## Scope and what was preserved

This task took over Cody's in-flight multi-song audio work and corrected two remaining behaviors.
**Nothing of Cody's implementation was reset, reverted, or rewritten.** Preserved verbatim:

- The permanent Z80 engine `apps/rastan-direct/src/sound/z80_driver.asm` (564 bytes): command ring,
  Timer-B rearm, native song-table scan/dispatch, banking, loop pointers, `$00` all-channel stop.
- The native compiler `tools/audio/compile_genesis_native_music.py` and the 7-song library
  (`out/audio_native/library.json`: 01 Credit, 02 Opening, 03 Aggressive World, 04 Name Regist,
  05 Scene 2, 06 Scene 3 Boss, 09 Ending), FM6/DAC reserved, dispatch `$25`.
- Cody's size-invariant correction `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x30FEB8` (commit
  `ac29264b`), and the death-transition handling lineage in `sound_comm.s`.

The entire fix lives in the **68000→Z80 bridge** `apps/rastan-direct/src/sound/sound_comm.s`
(`z80_write_command`), which already owns the semantic distinction of command `$25`.

## 1. Build 0491 — interrupted multi-song build finished (priority 1)

The multi-song build was completed first, as directed. Canonical ROM:
`dist/rastan-direct/rastan_direct_video_test_build_0491.bin`
(SHA `8051a6ab8c8f9cccc88ca90f55a518f25ddead568b229fd3d4a50a1e7de6e973`), 7 songs, FM6 reserved,
dispatch `$25` → Aggressive World. Static audio gate `AUDIO_NATIVE_STATIC_PASS`.

## 2. Authoritative evidence (ORIGINAL ARCADE MAME)

A no-invincibility deterministic run through full appearance → 3 deaths → GAME OVER was captured with
the established observer (`tools/mame/scripts/audio015_arcade_command_timing.lua`,
`tools/mame/run_audio015_arcade_command_timing.sh`) extended with a durable
`AUDIO015_ARCADE_INVINCIBLE` env toggle. Trace:
`states/traces/audio015_arcade_gameover/arcade_command_timing.tsv`.

Every `$25` and the GAME OVER command, with retained 68000 state (A5 = `0x10C000`):

| frame | cmd | outer (`+0`) | phase (`+2`) | state4 (`+4`) | player_state (`+0x10E8`) | player_x (`+0x10BE`) | meaning |
|---|---|---|---|---|---|---|---|
| 787 | `25` | 2 | 3 | 0 | **3** | 0x20 | first appearance (start music) |
| 1666 | `25` | 2 | 4 | 1 | **8** | 0xA0 | death #1 transition |
| 1798 | `25` | 2 | 3 | 0 | **3** | 0x20 | respawn #1 (restart music) |
| 2677 | `25` | 2 | 4 | 1 | **8** | 0xA0 | death #2 transition |
| 2809 | `25` | 2 | 3 | 0 | **3** | 0x20 | respawn #2 (restart music) |
| 3688 | `25` | 2 | 4 | **2** | **8** | 0xA0 | final death (GAME OVER) |
| 3689 | **`1E`** | 2 | 4 | **2** | 8 | 0xA0 | **GAME OVER music cue** |

Normal-gameplay SFX (`0B,15,28,1A,10,0C,…`) all carry `player_state = 1` (walking) or 2. Command `$00`
appears **only** 16× at frame 4 (boot ring clear) — it is never emitted in gameplay or at GAME OVER.
Command `1E` appears only at the GAME OVER transition. The sound-command table at arcade `0x2300` maps
`1E → descriptor 0x0492` (a short cue that, in the arcade sound CPU, preempts the looping stage song).

**Shared discriminator:** a genuine stage (re)appearance is uniquely `player_state == 3` (at the spawn
column, `player_x = 0x20`); death is `player_state == 8`; a mid-stage scene-segment crossing leaves the
player walking (`player_state == 1`). This is a single command-semantic property, not a per-segment fact.

## 3. Fix — one shared rule in the bridge

### 3a. Three unwanted restarts (segments 5/8/12 + death) — shared cause

The old bridge published every `$25` except the proven death form, so the death restart was already
suppressed, but any *other* non-appearance `$25` (the mid-stage segment-5/8/12 scene-entry cue) still
published and restarted the song. The shared correction inverts the rule:

> **Publish `$25` only in the genuine-appearance form — gameplay outer (`0xFF0000`) == 2 AND
> player_state (`0xFF10E8`) == 3 — and consume every other `$25`.**

This keeps the authentic first-appearance *and* post-READY respawn restart (both `player_state == 3`),
and removes the death restart (`player_state == 8`) and the segment-5/8/12 restarts
(`player_state == 1`, player walking) with **no per-segment gate**. `player_state == 3` is the fundamental
"appearing" discriminator; it is used rather than `player_x == 0x20` so a deeper checkpoint respawn (not at
the spawn column) still restarts correctly.

### 3b. GAME OVER — music must stop

GAME OVER emits the authentic cue `$1E`, which the native engine's song-table scan does not match, so it
is consumed and the stage loop runs forever. The current library authors no GAME OVER jingle, so the
faithful native realization renders `$1E` as the engine's canonical all-channel stop `$00`:

> **Translate command `$1E` → `$00` in the bridge before publishing.** The driver's existing `$00`
> handler stops playback and silences YM2612 + PSG, so the looping stage song ends at GAME OVER.

If a GAME OVER / Name-Registration track is later authored, map `$1E` to that song in the generated
dispatch table instead of translating to stop — no other change required.

Both rules are a single contiguous edit to `z80_write_command`; the ROM was disassembled to confirm the
emitted opcodes (`cmpi.b #$25`, `cmpi.w #2`/`#3` against `0xFF0000`/`0xFF10E8`, `cmpi.b #$1E`,
`moveq #0,d0`).

## 4. Build 0492 and validation

- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0492.bin`
  (SHA `feb610c0ceef6a25247248733e326fbf4a1cd9fd3cab7cfc478e920fb582f065`), full 7-ROM family.
- All production gates passed: shift-table patch, boot guard, canonical gate, final-life transition,
  R1 selector relocation, invincible-variant verify, and the static audio contract
  `AUDIO_NATIVE_STATIC_PASS driver=564 songs=7 dispatch=1 ticks=17410 events=151408`.
- **GENESIS NTSC MAME** non-regression gate (`run_audio015_native_runtime_gate.sh`,
  `states/traces/build0492_audio015_native_runtime/`): `result=PASS`. Driver goes ACTIVE at frame 381
  (appearance music still starts), `$25` publishes, `banked_mismatches=0`, no invalid PC/SP/access,
  `music_periods=623` (expected 626). The tightened `$25` gate does **not** break the working appearance
  restart.

**Behavioral acceptance boundary:** segments 5/8/12 and the GAME OVER transition are **not reachable in
GENESIS NTSC automation** (the translated 68000 core stalls the player at `player_x = 0xA7`, and the
gameplay route takes no deaths). As with Build 0490, final confirmation that (a) the three mid-stage
restarts are gone and (b) GAME OVER music stops requires Tighe's real-hardware audition. The fix is
grounded in ORIGINAL ARCADE ring evidence (§2), not in a Genesis observation.

## 5. Scaffolding inventory and removal plan

- **No production ROM scaffolding.** No NOP, no RTS stub, no dead-write suppression, no skipped call was
  added. The bridge only adds state-gated command classification and one command→command translation.
- **Tooling:** the only non-ROM change is the durable `AUDIO015_ARCADE_INVINCIBLE` env toggle on the
  existing arcade observer (default `1` preserves prior behavior). This is a reusable extension of a
  project-owned tool, not a disposable script — **retain**, no removal required.
- Legacy-subsystem size: unchanged by this task (the arcade sound-command transport remains intact and
  authoritative; only the native bridge's semantic classification changed).

## 6. Status
- OPEN-039 remains **OPEN** pending Tighe's hardware audition of 0492 (restart suppression + GAME OVER
  stop) and the broader multi-song acceptance.
- Prior superseded hypotheses (`$19` live publisher, YM2151-IRQ owning the 68000 flags) are already
  retracted in `Andy_AUDIO015_68000_audio_call_restoration.md`; the live mechanism is the `$25`
  appearance cue proven here and in Cody's Build 0488 report.
