# Cody - Build 0120 Title Composite Stripe Runtime Evidence

**Date:** 2026-06-30
**Type:** Runtime evidence / verification only
**Build:** 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**ROM SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No implementation. No fix design. No bookmark. No diagnostic ROM. No memory seeding or state forcing.

Address labels: `runtime_genesis_pc` = Genesis runtime/file-offset code address. `Genesis-WRAM` = Genesis work RAM. `HW_ADDRESS` = Genesis hardware-visible address. Arcade-to-Genesis mapping, when needed, must come from `build/rastan-direct/address_map.json`; this task did not use arithmetic mapping as proof.

## Phase 0

Classification: **EXTENDING** OPEN-001, with OPEN-023 and OPEN-024 as direct context. OPEN-006, OPEN-015, and OPEN-021 are guardrail/context only.

Relevant priors loaded from the project corpus:

- KF-010: BG maps to Genesis Plane B, FG maps to Plane A, PC090OJ sprites map to Genesis SAT.
- KF-016: title sprite-RAM clear behavior is an established prior for title/sprite interpretation.
- KF-021 and KF-026: sprite/SAT behavior must not be assumed from static enumeration alone; runtime sprite surface can be non-enumerable.
- KF-032: raw PC080SN/PC090OJ hardware writes must be routed into Genesis staging rather than allowed to hit VDP ports directly.
- KF-036: mapped work-RAM discipline applies if RAM-base helpers are involved.
- KF-038: item-description BG row aliasing is not the same mechanism as this title composite stripe symptom.

High-rediscovery-hazard findings touched: KF-026, KF-032, KF-036. No contradiction detected.

Deferred context: no deferred appendix entry is used as a prior. The known MAME/Exodus divergence concern remains a caution for interpreting emulator-specific VDP views, but no conclusion below depends on MAME VDP readback as authoritative.

## Evidence Artifacts

Visual evidence inspected:

- `states/screenshots/build_120/Exodus_build_120_title_screen_window_boundaries_on.png`
- `states/screenshots/build_120/Exodus_build_120_story_screen_window_boundaries_off.png`

Runtime/evidence directories produced during this task:

- `states/traces/build_0120_title_composite_stripe_evidence_20260630_204509/`
- `states/traces/build_0120_title_composite_stripe_evidence_20260630_204613/`
- `states/traces/build_0120_title_composite_stripe_evidence_20260630_204742/`
- `states/traces/build_0120_title_composite_stripe_evidence_20260630_204857_sanity/`

The useful runtime artifact is the sanity capture in `build_0120_title_composite_stripe_evidence_20260630_204857_sanity/`. It proves the MAME debugger dump method can stop at `vdp_commit_sprites`, but it captured an early state, not the steady title state.

## Visual Evidence

The Exodus title screenshot shows:

- Plane A viewer: the TAITO/copyright/credit text is present. It does not contain the RASTAN logo/sword art.
- Plane B viewer: the RASTAN logo and sword title art appear coherent and clean in the Plane B-only view.
- Window viewer: patterned green/purple/white garbage is visible in the VDP tool's Window view.
- Sprite viewer: a small outlined sprite-boundary box is visible.

The Exodus story screenshot shows:

- Plane A viewer: story text and credit text are present.
- Plane B viewer: king/figure artwork is present.
- Window viewer: patterned garbage is visible.
- Sprite viewer: a small outlined sprite-boundary box is visible.

No local final-composite screenshot of the title stripe artifact was found under `states/screenshots/build_120/`. Therefore the reported composite stripe remains a user/runtime observation, while the local image evidence proves only that Plane B alone is not obviously corrupted in the VDP viewer.

## Static VDP Setup

Static source review of `apps/rastan-direct/src/vdp_comm.s` shows the boot VDP setup uses:

| Register | Value | Meaning |
|---|---:|---|
| MODE1 | `0x04` | normal display setup |
| MODE2 off | `0x34` | display disabled during commit |
| MODE2 on | `0x74` | display enabled after commit |
| Plane A base | `0x38` | VRAM `0xE000` |
| Window base | `0x3C` | VRAM `0xF000` |
| Plane B base | `0x06` | VRAM `0xC000` |
| SAT base | `0x7C` | VRAM `0xF800` |
| BG color | `0x00` | palette index 0 |
| MODE3 | `0x00` | full-plane horizontal scroll mode, not line/cell hscroll |
| HScroll base | `0x3F` | VRAM `0xFC00` |
| Plane size | `0x01` | project-interpreted 64x32 planes |
| Window X | `0x00` | boot value |
| Window Y | `0x00` | boot value |

Source search found the Window X/Y register writes only in boot setup, not in a later per-frame path. This is static evidence only; a synchronized title-frame VDP register dump was not captured.

`_vblank_service` performs the expected sequence: save registers, update inputs, display off, commit tiles, commit BG, commit FG, commit sprites, optionally commit palette, commit scroll, display on, restore registers, then hand off to the arcade VBlank handler.

`vdp_commit_scroll` writes only the first two HScroll table words and two VSRAM words:

- `staged_scroll_x_fg - 16`
- `staged_scroll_x_bg - 16`
- `staged_scroll_y_fg + 8`
- `staged_scroll_y_bg + 8`

With MODE3 set to `0x00`, the static configuration does not indicate per-line or per-cell hscroll stripes.

## Runtime Capture Result

The requested steady title-frame VDP/SAT/Window/VRAM snapshots were **not** captured. The MAME debugger/title-state condition attempts did not produce title-state dumps. This is an evidence limitation, not a gameplay conclusion.

The successful sanity capture stopped at the first observed `vdp_commit_sprites` call and recorded:

```text
EVENT FIRST_BEFORE_VDP_COMMIT_SPRITES cyc=4110101 pc=071ECE sr=2614 s0=0000 s2=0000 s4=0000 cnt=0000 dirty=000FF81B active=0000
EVENT FIRST_AFTER_VDP_COMMIT_SPRITES cyc=4135096 pc=071EE2 sr=2610 s0=0000 s2=0000 s4=0000 cnt=0000 dirty=00000000 active=0000
```

This is an early `0/0/0` state, not the title `0/1/2` state.

Sanity dump observations:

- `staged_sprite_sat` before commit: 320 words, 78 nonzero.
- `staged_sprite_sat` after commit: 320 words, 78 nonzero.
- Sprite descriptor table before commit: touched/valid descriptor bits are present in early slots.
- Sprite descriptor table after commit: touched bits are cleared while valid bits remain where present.
- `staged_sprite_dirty` changes from `0x000FF81B` before the commit to `0x00000000` after the commit.
- `staged_sprite_active_count` is `0` in the event lines.

Interpretation: the sprite commit path can clear dirty/touched state while SAT/staged descriptor contents remain resident. Because this capture is not from the title state, it is **not proof** that sprites cause the title composite stripe. It only preserves sprite/SAT as a plausible class until a title-frame SAT/VRAM dump is captured.

## Classification Matrix

| Candidate | Current Evidence Classification | Rationale |
|---|---|---|
| Plane B corruption | **Not supported by available visual evidence** | Plane B-only Exodus view shows coherent RASTAN/sword art. This is not a synchronized VRAM dump, but it argues against Plane B itself being the stripe source. |
| Plane A overlay | **Possible / unproven** | Plane A contains text layers. No final-composite stripe screenshot was available locally, so a Plane A overlay at the stripe location was not proven. |
| Sprite/SAT | **Unresolved** | Sprite viewer shows a small box and the early sanity capture proves stale SAT-like state can persist through commit mechanics, but no title-frame SAT/VRAM capture was acquired. |
| SAT link/termination | **Unresolved** | Early descriptor behavior shows touched bits clear while valid/SAT state can remain, but the title-frame SAT chain was not captured. |
| H-scroll | **Weak / not supported statically** | Static VDP config uses full-plane hscroll mode and only two HScroll words are committed. No per-line hscroll evidence was found. Runtime HScroll table was not captured. |
| Window visibility/overlap | **Possible / unproven** | Window viewer shows garbage. Static Window X/Y writes are boot-only, but synchronized runtime VDP register and final composite evidence were not captured. |
| Timing/partial commit | **Unresolved** | No before/after title-frame VBlank VRAM snapshots were captured. |
| Emulator-specific | **Unresolved** | The available evidence does not compare the same title composite state across emulators. |

## Narrow Finding

The evidence supports this narrow statement only:

**Plane B-only title art is not sufficient to explain the reported final-composite stripe; the stripe, if present in final composite output, is more likely introduced by another composited source or by runtime VDP state outside the clean Plane B tilemap view.**

The evidence does **not** safely identify the responsible source as sprite/SAT, Window, Plane A, HScroll, or timing.

## D00298 / Exception Boundary

This task did not reproduce or analyze the `HW_ADDRESS 0x00D00298` fatal. No input was applied, and no dangerous stepping path was used. The D00298 path remains out of scope for this evidence note.

## Recommended Next Evidence Step

Recommended evidence-only follow-up: capture a synchronized steady-title frame with:

- VDP registers, especially Window X/Y, MODE3, Plane A/B/Window/SAT bases.
- VRAM Plane A/B/Window/SAT/HScroll table snapshots at VBlank exit.
- `staged_sprite_sat`, `staged_sprite_descriptor_table`, `staged_sprite_dirty`, and `staged_sprite_active_count` at the same frame.
- A final-composite screenshot from the same frame.

This should classify whether the stripe is sprite/SAT, Window, Plane A overlay, scroll/HScroll, or a timing artifact. No fix is justified from the current evidence alone.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched; remains open.
- OPEN-023: context; remains open.
- OPEN-024: context; remains open.
- OPEN-006: guardrail context only.
- OPEN-015: not touched beyond crash-screen caution.
- OPEN-021: context only.

Issues opened: none. Issues closed: none.

KNOWN_FINDINGS impact: **Option A - no update.** The task did not establish a durable mechanism-level finding.

## STOP

STOP triggered: **YES (evidence-limited, not architecture violation).** The task could not safely pin the composite stripe source because the required synchronized title-frame VDP/SAT/Window/VRAM capture was not acquired. No source/spec/tool/ROM/build/invariant changes were made.
