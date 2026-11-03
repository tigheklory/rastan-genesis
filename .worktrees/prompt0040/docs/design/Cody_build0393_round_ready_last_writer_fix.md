# Cody — Build 0393 ROUND/READY Last-Writer Fix

## Result

Tighe found that Build 0392 shortened, but did not remove, the READY-shaped
terrain interval. The first remaining bad event was Build-0392
`load_scene_tiles` enabling display at canonical Genesis PC `0x0746D2` while
the cleared final Plane-B staging still had an unpublished dirty-row update.
Live Plane-B VRAM therefore still held the earlier READY names when gameplay
patterns reused their slots.

Build 0393 moves the existing dirty Plane-B publication to the already-hidden
scene-ready boundary. No additional clear, delay, READY special case, or
per-frame operation was added. Visual acceptance remains Tighe's.

## Bounded evidence

The established READY producer destination is arcade C-window `0x00C00C48`
(Plane B row 12, column 18), with the second line two rows below. The bounded
Build-0392 probe watched only representative cells from those rows and the
transition display state. Together with the locked Build-0391 name/pattern
proof and Tighe's Build-0392 result, it distinguishes final staging from live
VDP ownership:

- `staged_bg_buffer` after `genesistan_hook_cwindow_clear`: **blank/correct**;
- a post-clear READY-name rewrite into staging: **not observed**;
- live Plane-B immediately before the bad display-enable: **stale READY
  names**, proven by the visible READY geometry drawing replacement terrain
  patterns;
- last staging owner: `genesistan_hook_cwindow_clear` at `0x07232E`, reached
  from translated teardown `0x0564D0 -> 0x073874`;
- last live-name owner: the earlier ordinary
  `vdp_commit_bg_strips_if_dirty` publication at `0x070106`; the Build-0392
  clear only marked its replacement dirty and did not synchronously publish it.

This is **Case A**, a publication/display ordering defect. Runtime probing was
required because static code alone did not distinguish final staging from the
live VDP name table.

## Exact repair

Build 0392 performed:

1. clear final Plane-B staging and mark all rows dirty;
2. replace/reuse gameplay patterns while display is off;
3. call `vdp_set_reg` at `0x0746D2` to enable display;
4. publish the dirty cleared Plane-B rows only in the later normal VBlank.

Build 0393 calls the existing `vdp_commit_bg_strips_if_dirty` at canonical PC
`0x0746CE`, while `load_scene_tiles` still owns display-off, then enables the
display at `0x0746D6`. The publisher consumes and clears the existing dirty
mask, so this is moved work rather than a redundant full-plane DMA. The rule is
generic for scene activation and contains no READY, round, record, or screen
coordinate condition.

Build 0392 shortened the artifact because its restored clear made the next
normal VBlank replace the stale READY names. It did not eliminate the interval
between gameplay pattern replacement/display-enable and that VBlank.

## Native boundary and policy checklist

Semantic cut: retained arcade control decides that the old presentation has
ended; native final Plane-B staging and its existing dirty publisher realize
that decision directly in Genesis VRAM before the scene becomes visible. The
retired PC080SN C-window fill/write tail remains unreachable.

- Semantic boundary rather than chip-write emulation: **YES**.
- Complete retired PC080SN tail remains bypassed: **YES**.
- Input/output are final native name words and dirty ownership: **YES**.
- New shadow RAM, virtual PC080SN, projector, or framebuffer: **NO**.
- New persistent representation or transitional compatibility: **NO**.
- Per-frame work: **NO**.
- Additional blind clear or redundant publication: **NO**.
- Arcade gameplay/state ownership preserved: **YES**.

## Build 0393

| Variant | Bytes | SHA-256 |
|---|---:|---|
| canonical | 1,744,568 | `b089d3f92bce80fcbf4cd705ce7a7cbcfec511d5d8d47db693f8a8b9994eb9a1` |
| `_c` | 1,748,664 | `70732a74faffc017e8bddc1d4bf37a6793b802818399384d27976e2b36d734da` |
| `_d` | 1,744,568 | `a0d6e578137aaaf5a583521709981b1bcc916b070d0485660949e890e371b022` |
| `_do` | 1,744,568 | `50b10a03377708c739220406247de91f857b666c25de208c7c8b9763404506a5` |
| `_s` | 1,744,568 | `baae26f502104dd97462f45fc153b32a074d066dbc41164d77b92fec118bf59c` |

- Counter: `392 -> 393`.
- Canonical gate: **PASS**.
- Gameplay-entry gate: **PASS** (240 post-entry frames; no address, bus,
  illegal-instruction, or crash-handler entry).
- Complete five-ROM verification: **PASS**.
- Transition-retention verifier: **PASS**.
- Mandatory Genesis NTSC MAME smoke: completed; no unmapped-memory report.
- Phase-1 seven-epoch gate: **FAIL/WARNING**, unchanged from Build 0392 and
  preserved as the emitted gate verdict.
- Palette, final Plane-A resolver, collision, waterfall, Phase-2, Flying Demon,
  third-chain, and H25 code: **unchanged**.

## Project ledger

- Classification: **EXTENDING**.
- Open issues touched: **OPEN-001, OPEN-018**.
- Context only: **OPEN-017, CLOSED-020**.
- New or closed issues: **NONE** pending user visual acceptance.
- Tools reused: the established gameplay-entry inputs, final-ROM disassembly,
  existing VDP/staging interfaces, normal Makefile release/gates, and the
  existing dirty Plane-B publisher.
- New bounded tool: `tools/mame/scripts/build0393_ready_last_writer.lua`, used
  only to distinguish staging ownership from live-name ownership.
- **No new finding to index:** this applies the existing direct-native
  publication-order policy and does not establish a new reusable subsystem
  behavior.

## User verification

**USER MUST VERIFY** that READY no longer becomes terrain, the gameplay
transition remains clean, and accepted Build-0392 gameplay behavior remains
intact.
