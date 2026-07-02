# Cody - Build 0120 Title Pommel Sprite/SAT Evidence Capture

**Date:** 2026-07-01
**Type:** Runtime evidence / sprite-SAT attribution only
**Build:** Build 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Scope:** Evidence capture and decoding only. No source/spec/tool/Makefile/ROM/build/invariant changes. No implementation, fix design, bookmark, diagnostic ROM, memory seeding, or state forcing.

Address labels: `runtime_genesis_pc` / `genesis_rom_offset` for Genesis executable PCs and ROM offsets, `Genesis-WRAM` for WRAM addresses, `VRAM` for VDP VRAM addresses.

## Phase 0

Classification: **EXTENDING** OPEN-001 / OPEN-024. OPEN-023 is context only and was already refuted as the visible pommel source by `docs/design/Andy_build0120_window_plane_coverage_design.md`; OPEN-006, OPEN-015, and OPEN-021 are guardrail/context only.

Relevant priors loaded:

- `RULES.md` and `ARCHITECTURE.md`.
- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, and latest `AGENTS_LOG.md` tail.
- `docs/design/Andy_build0120_window_plane_coverage_design.md`.
- `docs/design/Cody_build0120_title_pommel_composite_attribution.md`.
- `docs/design/Cody_build0120_sprite_sat_window_garbage_evidence.md`.
- `docs/design/Cody_sprite_window_buildstate_inventory.md`.
- `docs/design/Cody_build0120_title_composite_stripe_runtime_evidence.md`.
- `docs/design/Cody_build0120_D00298_post_2_2_5_path_analysis.md`.

Relevant findings respected: KF-010, KF-016, KF-021, KF-026, KF-032, KF-036, KF-038. HIGH-hazard priors touched: KF-021, KF-032, KF-036, KF-038. No contradiction detected.

Andy window result applied as prior: Build 0120 Window is OFF (`reg17=0x00`, `reg18=0x00`, zero-size), so Window garbage in a viewer is inert and cannot be used as the player-visible pommel source.

## Evidence Artifacts

Primary successful capture directory:

- `states/traces/build_0120_title_pommel_sprite_sat_evidence_20260701_101003/`

Files of interest:

- `title_sat_capture_frame90.lua` - read-only MAME Lua frame capture.
- `title_sat_capture_frame90_log.tsv` - state/timing log.
- `frame90_staged_sprite_sat_ff6104.bin` - 640-byte `staged_sprite_sat` dump from `Genesis-WRAM 0x00FF6104`.
- `frame90_staged_sprite_descriptor_table_ff6384.bin` - 960-byte descriptor dump from `Genesis-WRAM 0x00FF6384`.
- `frame90_sprite_dirty_active_ff6744.bin` - dirty/active dump from `Genesis-WRAM 0x00FF6744`.
- `frame90_state_ff0000_0080.bin` - title/work state header dump from `Genesis-WRAM 0x00FF0000`.
- `decode_frame90_sat.py` - throwaway decoder script under `states/`.
- `frame90_sat_decode.json` and `frame90_sat_decode.md` - decoded SAT/descriptor output.

Negative/limited VDP introspection attempt:

- `states/traces/build_0120_title_pommel_sprite_sat_evidence_20260701_100652/`
- The attempt did not produce a usable VDP VRAM/SAT dump. Therefore this report decodes production WRAM staging and descriptor state, not true `VRAM 0xF800` contents.

## Title State

The successful capture stopped at MAME frame 90, with no input and no D00298 path reached:

```text
CAPTURE_FRAME90 frame=90 pc=071F62 a5=00FF0000 s0=0000 s2=0001 s4=0000 credits=0000 timer2c=00A2 dirty=00000000 active=0000
```

Interpretation: the captured run is in the no-input title/attract state `0/1/0`, with the attract timer active (`Genesis-WRAM 0xFF002C = 0x00A2`). This is title/attract evidence, but it is not a synchronized visual screenshot of the final composite frame.

## VDP / SAT Baseline

Static/source baseline:

- `staged_sprite_sat = Genesis-WRAM 0x00FF6104`.
- `staged_sprite_descriptor_table = Genesis-WRAM 0x00FF6384`.
- `staged_sprite_dirty = Genesis-WRAM 0x00FF6744`.
- `staged_sprite_active_count = Genesis-WRAM 0x00FF6748`.
- `vdp_commit_sprites` is at `runtime_genesis_pc 0x00071ECC`.
- Per `apps/rastan-direct/src/pc090oj_hooks.s`, `vdp_commit_sprites` rebuilds the SAT link chain from valid descriptors, DMAs sprite tiles, DMAs the full 640-byte `staged_sprite_sat` to `VRAM 0xF800`, then clears dirty state.
- Per `docs/design/Andy_pc090oj_implementation_spec.md`, `staged_sprite_sat` is raw Genesis SAT format and descriptor slot validity is the commit-time truth source.

Capture limitation:

- True VDP `VRAM 0xF800` SAT contents were **not captured**. The MAME/Lua introspection attempt did not expose a safe VDP VRAM read path in this run.
- The decoded evidence below is therefore WRAM staging and descriptor evidence. Because `vdp_commit_sprites` DMAs this buffer to SAT every VBlank, this is still the production-side source for SAT, but it is not a direct hardware VRAM dump.

## SAT Capture

Frame 90 raw summary from `frame90_sat_decode.json`:

- Dirty/active words from `Genesis-WRAM 0x00FF6744..0x00FF674B`: `[0, 0, 0, 0]`.
- `staged_sprite_active_count`: `0`.
- Nonzero staged SAT slots: `45`.
- Valid descriptor slots: `8`.
- Nonzero descriptor slots: `45`.
- Hardware link chain from slot 0: `[0]`.

Important distinction:

- Many SAT slots are mechanically nonzero because word1 contains the constant size field `0x0500`; this does not mean they are active or visible.
- Descriptor-valid slots are the commit-time active candidates. Only 8 descriptor slots have valid bit set at frame 90.
- The link chain from slot 0 terminates immediately (`slot0.link = 0`), so even among stale/nonzero SAT memory, the reachable Genesis hardware chain is not a chain of pommel-area sprites.

## Decoded SAT Entries

Pommel test region from prior visual attribution:

- Approximate screen box: `X=150..185`, `Y=20..70`.

Standard decode used:

- SAT word0: raw Genesis Y, screen `Y = (word0 & 0x01FF) - 0x80`.
- SAT word1: `0x0500` means 2x2 Genesis tiles = `16x16` pixels per project PC090OJ spec; low 7 bits are link.
- SAT word2: priority bit 15, palette bits 14..13, V/H flip bits, tile index bits 10..0.
- SAT word3: raw Genesis X, screen `X = (word3 & 0x01FF) - 0x80`.

Descriptor-valid slots:

| Slot | SAT words | Screen rect | Link | Tile | Palette | Descriptor source |
|---:|---|---|---:|---:|---:|---|
| 0 | `0081 0500 E400 0080` | `x=0..15`, `y=1..16` | 0 | `0x0400` | 3 | slot range `0..4`, target helper family |
| 1 | `0080 0500 E404 0080` | `x=0..15`, `y=0..15` | 0 | `0x0404` | 3 | slot range `0..4`, target helper family |
| 2 | `0080 0500 E408 0080` | `x=0..15`, `y=0..15` | 0 | `0x0408` | 3 | slot range `0..4`, target helper family |
| 3 | `0080 0500 E40C 0080` | `x=0..15`, `y=0..15` | 0 | `0x040C` | 3 | slot range `0..4`, target helper family |
| 4 | `0080 0500 E410 0080` | `x=0..15`, `y=0..15` | 0 | `0x0410` | 3 | slot range `0..4`, target helper family |
| 14 | `0080 0500 E438 00AA` | `x=42..57`, `y=0..15` | 0 | `0x0438` | 3 | slot range `14..17`, helper family |
| 16 | `0100 0500 E440 0080` | `x=0..15`, `y=128..143` | 0 | `0x0440` | 3 | slot range `14..17`, helper family |
| 17 | `0100 0500 E444 0101` | `x=129..144`, `y=128..143` | 0 | `0x0444` | 3 | slot range `14..17`, helper family |

No descriptor-valid slot intersects `X=150..185`, `Y=20..70`.

Nonzero staged SAT slots also have zero intersections with the pommel box; see `frame90_sat_decode.md` for the full slot table.

## Pommel Intersection Test

Result:

- Nonzero staged SAT entries intersecting pommel box: `0`.
- Descriptor-valid SAT entries intersecting pommel box: `0`.
- Hardware link-chain entries intersecting pommel box: `0`.

Therefore, the captured Build 0120 title/attract WRAM sprite staging does **not** support the pommel/sword-hilt composite artifact being caused by a staged PC090OJ sprite over that region.

## Producer Attribution

Runtime descriptor records at frame 90 have source-id word `0x0000`, so exact producer-PC attribution is not present in the descriptor data.

Static slot ownership narrows the candidate families:

- Slots `0..4` are owned by `genesistan_pc090oj_hook_target_3b902`-family output.
- Slots `14..17` are owned by `genesistan_pc090oj_hook_target_3b930`-family output.

However, at capture time:

- `staged_sprite_dirty = 0`.
- `staged_sprite_active_count = 0`.
- Descriptor touched bits are not set for those entries.

So frame 90 does not show a current-frame pommel producer; it shows stale/retained descriptor/SAT state that is outside the pommel region and not linked into a visible pommel-area chain.

## Classification

**Sprite/SAT as the pommel source: NOT SUPPORTED by this capture.**

Evidence basis:

- Captured no-input title/attract state `0/1/0` at frame 90.
- Production WRAM `staged_sprite_sat` and `staged_sprite_descriptor_table` decoded.
- No nonzero staged SAT rectangle intersects the pommel box.
- No descriptor-valid SAT rectangle intersects the pommel box.
- The slot-0 hardware link chain terminates immediately.

Residual limitation:

- True VDP `VRAM 0xF800` SAT was not directly dumped. If the hardware SAT somehow diverged from `staged_sprite_sat`, this capture would not prove that divergence. Static `vdp_commit_sprites` says the staging buffer is DMA-published to SAT every VBlank, so divergence would require a separate commit/VRAM problem not proven here.

Remaining candidate after this capture:

- Window is refuted by Andy's Window-off proof.
- Plane B pommel art is clean in the Exodus Plane B viewer.
- Captured staged SAT does not explain the artifact.
- The remaining explanation is unresolved and should be chased with a synchronized final-composite / VDP-register / Plane-A / true-VRAM capture, or a Plane A/final-composite residue check. Do not implement a sprite/SAT fix for the pommel based on this evidence.

## D00298 Safety

No manual stepping was performed. The run did not target or reach the known D00298-danger path. The task did not step over `runtime_genesis_pc 0x0005A724`, did not step over `runtime_genesis_pc 0x0003B292`, and did not run BlastEm.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched; remains open.
- OPEN-024: touched; current pommel artifact attribution to staged sprite/SAT is not supported by this capture, but OPEN-024 remains open for broader sprite/SAT completeness and known raw PC090OJ paths.
- OPEN-023: context only; Window has been refuted for this visible artifact, but issue remains open for Window implementation/layout concerns.
- OPEN-006, OPEN-015, OPEN-021: context/guardrail only.
- New issues opened: none.
- Issues closed: none.
- `KNOWN_FINDINGS.md`: no update. This is negative/narrow evidence, not a durable new mechanism.

## STOP

STOP triggered: **NO**.

Evidence limitation recorded: true VDP `VRAM 0xF800` SAT was not directly captured; report conclusions are based on production WRAM staging and descriptor state.
