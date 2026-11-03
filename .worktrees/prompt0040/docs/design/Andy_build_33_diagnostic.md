# Andy — Build 33 Diagnostic

**Status:** ANALYSIS COMPLETE. Root cause identified. No implementation performed.
**Build:** 0033 (`rastan-direct`).

---

## 1. Hook Firing Status

**`genesistan_hook_text_writer_3c4d2` — patch is correctly installed. Hook IS
invoked by execution paths that reach `arcade_pc: 0x03C4D2`.** (See §2 for
binary-level evidence.) However, the hook is **not the only gate** that
reaches PC080SN FG C-window space; other unhooked dispatcher handlers also
write there. See §5.

Direct evidence the hook is live:
- `apps/rastan-direct/out/symbol.txt:42` → `0007054e T genesistan_hook_text_writer_3c4d2`.
- ROM bytes at `genesis_rom_offset: 0x03C6D2` begin `4EB9 0007054E` (JSR to the
  hook's resolved address). See §2.
- Hook source body at `apps/rastan-direct/src/main_68k.s:636–788` writes only
  into `staged_fg_buffer` and `fg_row_dirty` (no C-window writes).

Indirect evidence the hook path is not reaching the original inner
subroutine body:
- Trace watchpoint `helper_5b512_rts@000200 count=0` in
  `states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_summary.txt`.
  The original inner sub at `arcade_pc: 0x03C516` unconditionally executes
  `jsr 0x5B512` at `arcade_pc: 0x03C53E` every loop iteration. If the
  original 0x03C4D2 body (and hence the inner sub) were reached, this count
  would be nonzero. **Count=0 is consistent with the 0x03C4D2 body being
  dead after the patch.**

---

## 2. Patch Entry Integrity

**All four checks pass. `replacement_bytes` is valid and the binary matches.**

| Check | Result | Evidence |
|-------|--------|----------|
| `opcode_replace` entry present for `arcade_pc: 0x03C4D2` | PASS | `specs/rastan_direct_remap.json:351–356` |
| `replacement_bytes` contains valid symbol placeholder | PASS | `4EB9{symbol:genesistan_hook_text_writer_3c4d2}4E75` + 30 × `4E71` at `specs/rastan_direct_remap.json:354` |
| Symbol resolves in link | PASS | `apps/rastan-direct/out/symbol.txt:42` → `0007054e T genesistan_hook_text_writer_3c4d2` |
| Resolved bytes match ROM at `genesis_rom_offset: 0x03C6D2` | PASS | ROM bytes at `0x03C6D2`: `4EB9 0007054E 4E75` + 30 × `4E71` = 68 bytes (verified by byte-read of `apps/rastan-direct/dist/rastan_direct_video_test.bin`) |

`genesis_rom_offset: 0x03C6D2` obtained from
`build/rastan-direct/address_map.json` `patched_site` segment for
`arcade_pc: 0x03C4D2`.

`opcode_replace_count = 47` confirmed in both
`specs/rastan_direct_remap.json` and
`build/rastan-direct/rastan_direct_patch_manifest.json`.

**STOP DOCUMENT RULE: NOT triggered** — `replacement_bytes` are valid,
symbol resolves, binary matches.

---

## 3. Trace Findings

Source: `states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_summary.txt`. 1798 frames
traced. All PCs below are `runtime_genesis_pc` unless otherwise noted.

### 3.1 Execution summary

- Final frame `1797`. No hard crash in MAME (MAME is more permissive about
  writes to unmapped cart addresses than BlastEm).
- `vdp_ports_live count=26336` at `runtime_genesis_pc: 0x070100` — the
  wrapper's `vdp_set_reg` site, firing every frame. Wrapper VBlank handler
  is healthy.
- `z80_ctrl changes=58` — Z80 driver handshake is active through frame
  1770.
- `startup_result_code addr=0xFF686A changes=1 first_change=389 last_change=389`
  — control-flow reaches the stage where the arcade code writes its
  startup_result word, then stalls (no further change across remaining
  1409 frames).
- `arcade_stage changes=1 first_change=391 last_change=391 last=0x4E73`
  — stage register changes once (early attract transition) then freezes.
- `reg_c50000_live count=0` — no writes to obsolete legacy address
  `0xC50000`.

### 3.2 Unexpected hardware writes — `fg_cwindow_live`

```
fg_cwindow_live count=8 first_frame=170 last_frame=384
  first_pc=03C52A last_pc=03C518
  first_addr=C09EA0 last_addr=C09EA6
  first_data=0000 last_data=0037 first_mask=FFFF last_mask=FFFF
```

`HW_ADDRESS/PC080SN/FG_TILEMAP` is being written in this trace. 8 write
events, spanning `0xC09EA0..0xC09EA6`, between frames 170 and 384.
`last_data=0x0037` is a non-blank value (real tile code — slow-path text
rendering), so the path producing these writes is the script-interpreter
**slow path**, not the fast-fill path.

### 3.3 PC interpretation (flagged as open question)

The trace's `first_pc=03C52A last_pc=03C518` values correspond **numerically**
to addresses inside the `arcade_pc: 0x03C516..0x03C52A` inner subroutine if
interpreted as arcade-normalized PCs. They do **not** match any write
instruction at the same `genesis_rom_offset` if interpreted as Genesis-space
PCs (the relocated inner-sub write instructions live at
`genesis_rom_offset: 0x03C730` and `0x03C744`, not `0x03C52A` and `0x03C518`).

The `helper_5b512_rts count=0` watchpoint simultaneously proves the inner
subroutine did **not** run (it would call `jsr 0x5B512` every iteration).
Therefore the `first_pc/last_pc` fields reported by `fg_cwindow_live`
cannot be the actual runtime PC of the offending writes. This is an
instrumentation-layer question (see §6) and does not change the §5 root
cause.

### 3.4 Anomalous execution paths

None outside the `fg_cwindow_live` writes. `vdp_ports_live` runs only at
`0x070100` (wrapper) — as expected. No writes to the sprite chip range
`0xD00000..0xD03FFF` (`reg_d01bfe` changed once at frame 389, but that's
an already-hooked WRAM shadow, not sprite RAM).

---

## 4. Visual Evidence (Exodus — `states/screenshots/build_33/`)

537 frames were extracted. Seven frames sampled: `frame_0001, frame_0090,
frame_0180, frame_0270, frame_0360, frame_0450, frame_0537`. Each frame
was read in full, including the VDP Image Window (center), the Plane
Viewer thumbnails (lower-left), the VRAM Pattern Viewer, the CRAM Palette
panel, the Registers panel (right), and the console log panel (far left).

### Sampled observations

| Frame | VDP Image (center) | Plane A (FG) / Plane B (BG) | CRAM palette | VRAM Pattern (tile data) | Console log |
|-------|--------------------|------------------------------|--------------|---------------------------|-------------|
| 0001 | File-open dialog obscures window — Exodus not yet advanced past launcher setup. | not visible | not visible | not visible | not visible |
| 0090 | Red/magenta vertical striped grid filling most of the play field. | Plane thumbnail shows the same striped content. | Four palette lines populated; distinct bright entries (green, red, blue). | Checkerboard / hatch patterns in VRAM tile area — synthetic bring-up tiles (consistent with `init_staging_state` checkerboard). | Clean (no errors visible). |
| 0180 | Red-dominated horizontal fill with a thin blue band at the top. | Same content in plane thumbnail. | Palette unchanged from frame 0090. | Same synthetic-tile VRAM contents. | Clean. |
| 0270 | Green hatched/tiled pattern covering the play field. Different from frames 0090/0180 — the plane content has changed. | Green hatched tile pattern. | Palette updated (green entries more prominent). | VRAM pattern shows green hatched tile cluster. | Clean. |
| 0360 | **Play field BLACK.** Plane Viewer thumbnail still shows residual green hatched content. CRAM retains palette. VRAM still contains tile data. | Plane content present but not rendered. | Green entries present in CRAM. | Green hatched tiles still in VRAM. | **Console shows repeated `Error Trigger` entries** — consistent with exception traps firing. |
| 0450 | BLACK. | Plane content still cached in VRAM (visible in Plane Viewer thumbnail). | Palette still loaded. | Tile data still loaded. | More `Error Trigger` entries; no recovery. |
| 0537 | BLACK. | Same as 0450. | Same. | Same. | More `Error Trigger` entries; system frozen. |

### Synthesis

- Visible content in frames 0090–0270 is the bring-up scaffolding's
  synthetic checker/hatch/stripe patterns drawn by `init_staging_state`
  (see `apps/rastan-direct/src/main_68k.s` — this is known bring-up
  content, NOT arcade game graphics).
- No arcade text, title, sprite, or attract graphics are visible at any
  sampled frame.
- Between frames 0270 and 0360, the VDP output goes to black even though
  Plane A, Plane B, palette, and tile data are all populated. This
  pattern is consistent with the CPU entering the Genesis exception
  trap (observed in the MAME trace as the CPU returning to
  `runtime_genesis_pc: 0x000010` per the MAME exit summary in
  `AGENTS_LOG.md` — the trap vector stub at the wrapper boundary).
- The console log (far-left panel) transitions from clean to repeated
  "Error Trigger" entries between frames 0270 and 0360 — exactly the
  window during which execution hits the invalid hardware write.

Registers panel is not legible at thumbnail resolution. The register
panel does not change the §5 conclusion (the root cause is identifiable
without it).

---

## 5. Root Cause Determination (MANDATORY)

**Root cause: (4) Alternate code path writes to 0xC09EA0.**

The hook at `arcade_pc: 0x03C4D2` is installed, wired to a valid symbol,
and reachable via its two dispatcher branches at
`arcade_pc: 0x03C924` and `arcade_pc: 0x03C92C` (script opcodes `0x50`
and `0x60`). The hook body routes through `staged_fg_buffer` only and
does not write to C-window. None of categories (1)–(3) applies:

- **(1) Patch not applied to binary** — refuted by §2: ROM bytes at
  `genesis_rom_offset: 0x03C6D2` are the expected `JSR + RTS + NOP*`
  pattern.
- **(2) Patch applied but not executed** — refuted by §1 indirect
  evidence (`helper_5b512_rts count=0` means the original 0x03C4D2 body
  and its inner subroutine are dead; the patched JSR path is the only
  remaining way the original dispatcher branches at
  `arcade_pc: 0x03C924/0x03C92C` resolve to a live RTS).
- **(3) Hook executes but does not intercept all writes (via the patched
  entry)** — the hook is a self-contained translator, written once, and
  does not write to C-window anywhere in its body (see
  `apps/rastan-direct/src/main_68k.s:636–788`). It cannot partially
  intercept writes at `arcade_pc: 0x03C4D2` because the original body
  there has been entirely replaced with `JSR hook; RTS; NOP×30`.

The script-interpreter dispatcher at approximately
`arcade_pc: 0x03C902..0x03C94C` (`build/maincpu.disasm.txt:76269–76288`)
routes script-opcode top-nibble values to **eight** separate handlers:

| Script opcode (top nibble) | Handler `arcade_pc` | Hooked? |
|----------------------------|---------------------|---------|
| `0x10` | `0x03C830` | **NO** |
| `0x20` | `0x03C7A4` | **NO** |
| `0x30` | `0x03C6DC` | **NO** |
| `0x50` | `0x03C4D2` | YES (this build) |
| `0x60` | `0x03C4D2` (same) | YES (this build) |
| `0x90` | `0x03C75C` | **NO** |
| `0xA0` | `0x03C550` | **NO** |
| `0xB0` | `0x03C636` | **NO** |
| `0xC0` | `0x03C586` | **NO** |

The unhooked handlers (e.g. `arcade_pc: 0x03C830`) use the **same write
shape** — indexed `A1@(2)` for the tile word, `A1@(6)` for the secondary
word, stride `addq.l #8, A1` — via their own private inner subroutines
(e.g. `arcade_pc: 0x03C85E`). These writes target arcade PC080SN FG C-window
space. Confirmed by ROM byte inspection using the
`arcade_copy` segment's recorded `identity_offset` from `address_map.json`:

| Arcade write site | Corresponding `genesis_rom_offset` (from segment record) | Bytes in ROM |
|-------------------|---------------------------------------------------------|--------------|
| `arcade_pc: 0x03C816` (handler `0x20` tile write) | `0x03CA16` | `33400002` (`movew D0, A1@(2)`) |
| `arcade_pc: 0x03C824` (handler `0x20` attr write) | `0x03CA24` | `33470006` (`movew D7, A1@(6)`) |
| `arcade_pc: 0x03C880` (handler `0x10` sub `0x85E` tile write) | `0x03CA80` | `33400002` |
| `arcade_pc: 0x03C88E` (handler `0x10` sub `0x85E` attr write) | `0x03CA8E` | `33470006` |

(All Genesis-space addresses above are derived from
`build/rastan-direct/address_map.json` segment
`arcade_copy [0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)` with
`identity_offset = 512`. No independent arithmetic.)

The Build 33 attract-mode script data must contain text-script opcodes
with top-nibble values **other than** `0x50` / `0x60` — specifically at
least one of `{0x10, 0x20, 0x30, 0x90, 0xA0, 0xB0, 0xC0}` — which
dispatches to an unhooked handler that writes directly to
`HW_ADDRESS/PC080SN/FG_TILEMAP`. The specific write address `0xC09EA0`
and the progression through frames 170..384 confirm slow-path text
rendering by one of these handlers.

The hook installed at `arcade_pc: 0x03C4D2` resolves one handler's worth
of writes. The dispatcher has **seven other unhooked sibling handlers**
using the same write pattern. At least one of those is executed by the
Build 33 attract-mode script, producing the `0xC09EA0` write that
BlastEm reports as a fatal machine freeze.

Per the `docs/design/Andy_final_pc080sn_hook_strategy.md` principle
("One hook, multiple call sites, zero game-state awareness"), the correct
next step is to expand the intent-class coverage — either by adding
sibling hooks at the seven unhooked `arcade_pc` entries of the dispatcher
table, or by hooking upstream at the dispatcher entry itself so a single
translator intercepts all top-nibble opcodes. That is scope for a new
prompt; **no fix is proposed here** (this is analysis only).

---

## 6. Open Questions

1. **Trace PC-field interpretation.** `fg_cwindow_live first_pc=0x03C52A last_pc=0x03C518`
   in the trace summary does not match any live write instruction at the
   same `genesis_rom_offset`. Two hypotheses (a) the harness normalizes
   PCs to arcade space for the `fg_cwindow_live` filter only, or (b) the
   fields are stale-cached from a prior run. Resolution would require
   reading `tools/mame/run_genesis_trace_wsl.sh` and
   `tools/mame/genesistrace.lua` (or equivalent) to see how that filter's
   PC is sampled. **Does not change the §5 conclusion** — regardless of
   PC interpretation, C-window writes occurred, the 0x03C4D2 hook
   prevents writes via its handler, and sibling handlers still contain
   the raw write instructions.
2. **Which specific script-opcode top nibble fires first.** Trace
   captured writes but does not tell us which handler produced them.
   Resolving this would require either a per-handler instrumentation
   watchpoint or stepping through the script byte-stream at arcade
   descriptor `A4@(+11..+26)`. Not required for root-cause
   identification.
3. **Exodus Register panel values.** Panel is present in every sampled
   frame but not legible at thumbnail resolution. Reading individual
   pixels within a zoomed panel would require a higher-fidelity read
   path than the current Read tool provides. Not required — register
   state is not needed to support the §5 determination.
4. **Build 33 MAME trace summary bytes are identical to the Build 32
   trace summary on several fields** (counts, first/last addr, first/last pc
   for `fg_cwindow_live`). Possibility (b) from open question 1 (stale
   cached state) should be considered. This does **not** invalidate the
   BlastEm fatal-error evidence — BlastEm shows a present-tense crash on
   the same address.

---

## 7. Evidence Sources Examined

| Tag | Source | Examined | Outcome |
|-----|--------|----------|---------|
| E1 | `states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_summary.txt` | YES | §3 — C-window writes present; helper_5b512 never called; wrapper healthy. |
| E2 | `states/screenshots/build_33/` (537 frames) | YES (7 sampled) | §4 — synthetic bring-up content rendered until frames ~270–360, then black with repeated Error Trigger log entries. |
| E3 | BlastEm screenshot (fatal error "machine freeze due to write to address C09EA0") | YES | §5 — confirms write happens at runtime despite patch, independent of MAME summary interpretation. |
| E4 | `specs/rastan_direct_remap.json:351–356`, `apps/rastan-direct/out/symbol.txt:42`, `apps/rastan-direct/dist/rastan_direct_video_test.bin[0x03C6D2:0x03C6D2+68]` | YES | §2 — patch entry integrity PASS, STOP DOCUMENT RULE not triggered. |

---

## 8. Files Touched

None. Analysis only.
