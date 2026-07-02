# Cody - Genesis SAT Link-Chain Termination Audit

**Date:** 2026-07-02
**Type:** Evidence / attribution only
**Build:** rastan-direct Build 0126
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`
**SHA256:** `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`
**Trace directory:** `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/`

## Phase 0

- Classification: **EXTENDING** OPEN-001 / OPEN-024 sprite evidence.
- Mandatory architecture read: `RULES.md` and `ARCHITECTURE.md` read before evidence work.
- Relevant priors loaded: KF-011, KF-032, KF-036, OPEN-001, OPEN-024, Build 0125 temporary SAT suppression context, Build 0126 canonical baseline, and recent PC090OJ/object-RAM/SAT evidence docs.
- Contradiction detected: **NO**.
- Scope compliance: **PASS**. No source, spec, tool, Makefile, ROM, invariant, build, bookmark, or implementation change was made.
- Build 0126 SHA matched the requested canonical ROM.
- Address discipline: runtime addresses in this note are labelled `runtime_genesis_pc`; no arcade-to-Genesis arithmetic mapping was used as proof.

## Objective

Audit whether Build 0126's Genesis Sprite Attribute Table (SAT) construction can explain the black overlay through an invalid/unterminated/stale link chain. The specific question was whether the VDP could be walking into stale reachable SAT entries after the intended sprites.

## Static SAT Audit

### Commit Sequence

`vdp_commit_sprites` in `apps/rastan-direct/src/pc090oj_hooks.s` runs:

```asm
bsr .Lvcs_mirror_scan
bsr .Lvcs_link_chain_build
bsr .Lvcs_tile_dma
bsr .Lvcs_sat_dma
bsr .Lvcs_clear_dirty
```

It is called from `_vblank_service` in `apps/rastan-direct/src/vdp_comm.s` before palette/scroll commit and before handoff to the arcade VBlank handler.

### Clearing

`.Lvcs_clear_generated_sprite_state` clears all generated sprite state at the start of every mirror scan:

- `staged_sprite_sat`: `80 * 8 = 640` bytes cleared.
- `staged_sprite_descriptor_table`: `80 * 12 = 960` bytes cleared.
- `staged_sprite_dirty`: cleared.
- `staged_sprite_active_count`: cleared.

Boot also clears `staged_sprite_sat`, `staged_sprite_descriptor_table`, `staged_sprite_dirty`, `staged_sprite_active_count`, `pc090oj_object_ram`, and PC090OJ counters.

### Link Construction

`.Lvcs_link_chain_build` scans descriptor slots `0..79` and links only descriptors with valid bit 0 set:

- For each current valid slot, the previous valid slot's SAT size/link word is rewritten to `0x0500 | current_slot`.
- The last valid slot is explicitly terminated with `0x0500`, meaning link byte `0`.
- If no valid slot exists, no link write occurs, but all SAT entries are already zero from the per-frame clear.

### DMA

`.Lvcs_sat_dma` programs a DMA of `640` bytes / `320` words from `staged_sprite_sat` to VDP SAT VRAM destination `0x0000F800`.

### Expected Genesis SAT Cases

- `emitted_count = 0`: all SAT entries were cleared; no descriptor is valid; slot 0 remains all zero with link byte `0`. Safe termination.
- `emitted_count = 1`: slot 0 is valid and final; `.Lvcs_link_chain_build` writes slot 0 size/link `0x0500`, link byte `0`. Safe termination.
- Decreasing count frame-to-frame: stale entries are cleared before each scan, not merely unlinked. The full 80-entry SAT is then DMA'd. Safe against stale reachable entries.
- Unused slots: descriptor valid bit is clear, SAT words are zeroed, and they are not linked.

## Runtime Capture Method

Two capture methods were attempted:

1. `capture_build0126_sat_audit.lua` sampled frame-done moments and dumped staged SAT / VDP SAT. This was rejected for final SAT classification because the sampled PC was inside `vdp_commit_sprites` (`runtime_genesis_pc 0x071F5A` clear loop), i.e. after clear but before rebuild/DMA. Those files remain in the trace directory as rejected lifecycle evidence.
2. `mame_postcommit_dump_selected.cmd` used native MAME debugger `go 70100` to stop at the post-commit VBlank handoff boundary, then dumped staged SAT, descriptors, counters, and state at handoff counts 60, 282, 283, 289, and 369. These are the authoritative runtime samples for this audit.

The native debugger could not dump VDP `videoram` space at `0xF800` with the probed syntaxes, so exact post-handoff true VDP SAT readback is not independently captured here. The static DMA path proves the whole staged SAT is the DMA source and `0xF800` is the DMA destination, but the exact post-DMA VRAM bytes are recorded as a measurement limitation.

## Runtime Results

Decoded post-commit analysis:

- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_sat_link_chain_analysis.md`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_sat_link_chain_analysis.json`

All five post-commit samples have identical SAT chain structure:

| Handoff | Label | Decoded | Drawable | Emitted | Active | Valid Slots | Chain | Terminates | Unreachable Nonzero |
|---:|---|---:|---:|---:|---:|---|---|---|---|
| 60 | title_steady | 256 | 4 | 4 | 4 | 0,1,2,3 | 0 -> 1 -> 2 -> 3 -> 0 | YES | none |
| 282 | story_black_cover_nominal | 256 | 4 | 4 | 4 | 0,1,2,3 | 0 -> 1 -> 2 -> 3 -> 0 | YES | none |
| 283 | story_reveal_nominal | 256 | 4 | 4 | 4 | 0,1,2,3 | 0 -> 1 -> 2 -> 3 -> 0 | YES | none |
| 289 | story_reveal_late | 256 | 4 | 4 | 4 | 0,1,2,3 | 0 -> 1 -> 2 -> 3 -> 0 | YES | none |
| 369 | late_story_or_transition | 256 | 4 | 4 | 4 | 0,1,2,3 | 0 -> 1 -> 2 -> 3 -> 0 | YES | none |

Representative decoded chain entries, same across sampled handoffs:

| Slot | Size/Link | Link | Attr | X | Y | Screen Pos | Size | Visible |
|---:|---|---:|---|---|---|---|---|---|
| 0 | `0x0501` | 1 | `0xE400` | `0x0080` | `0x0080` | `(0,0)` | 2x2 cells | YES |
| 1 | `0x0502` | 2 | `0xE404` | `0x00AA` | `0x0080` | `(42,0)` | 2x2 cells | YES |
| 2 | `0x0503` | 3 | `0xE408` | `0x0080` | `0x0100` | `(0,128)` | 2x2 cells | YES |
| 3 | `0x0500` | 0 | `0xE40C` | `0x0081` | `0x0100` | `(1,128)` | 2x2 cells | YES |

No sampled post-commit SAT contains:

- a nonzero slot outside the reachable chain;
- a visible slot outside the reachable chain;
- a link loop;
- an out-of-range link;
- an unterminated final sprite;
- a descriptor-valid/SAT-zero mismatch in the reachable chain.

## Raw Writer / Post-SAT-DMA Check

Static source scan found the production SAT flow in `pc090oj_hooks.s`:

- Generated SAT writes happen through `.Lpc090oj_emit_slot`, `.Lvcs_clear_generated_sprite_state`, and `.Lvcs_link_chain_build`.
- The VDP SAT upload is `.Lvcs_sat_dma`, targeting `VRAM 0xF800` and using `staged_sprite_sat` as the DMA source.
- No alternate source-level SAT DMA path was found in `apps/rastan-direct/src/` for the normal sprite commit. Crash-handler VDP writes are crash-only and not part of this no-crash runtime window.

Runtime post-DMA VDP SAT readback at `VRAM 0xF800` was attempted but not captured at the exact handoff boundary due debugger VDP-space dump limitations. Therefore, the conclusion is strictly: **the staged SAT chain handed to `.Lvcs_sat_dma` is well-formed and fully terminated**. The direct true-VDP SAT bytes are not independently proven in this pass.

## Classification

### Link-chain defect: **NOT SUPPORTED**

The Build 0126 post-commit staged SAT is not stale, unterminated, or over-walking. The reachable chain is exactly four entries long and terminates with link `0` in every sampled title/story/reveal handoff. There are no nonzero unreachable entries for the VDP to accidentally reach through the link chain.

### Remaining interpretation

If the black overlay remains sprite-related, this audit points away from link-chain termination and toward one of these still-open categories:

- the four legitimately reachable sprite entries are semantically wrong;
- their tile data / palette / priority causes unintended cover;
- the cover is not from SAT link traversal at all.

This audit does **not** prove a fix and does **not** resolve the broader black-cover attribution. It only rules out stale/unterminated SAT chain traversal as the proximate mechanism in the sampled Build 0126 post-commit states.

## Artifacts

Authoritative post-commit artifacts:

- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/mame_postcommit_dump_selected.cmd`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_060_title_steady_staged_sprite_sat_ff6104.txt`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_282_story_black_cover_nominal_staged_sprite_sat_ff6104.txt`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_283_story_reveal_nominal_staged_sprite_sat_ff6104.txt`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_289_story_reveal_late_staged_sprite_sat_ff6104.txt`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_369_late_story_or_transition_staged_sprite_sat_ff6104.txt`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_sat_link_chain_analysis.md`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_sat_link_chain_analysis.json`
- `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/postcommit_*_sat_decode.csv`

Rejected / non-authoritative artifacts:

- `capture_build0126_sat_audit.lua` and `frame_*` dumps sampled during `vdp_commit_sprites` and are not used for final chain classification.
- `postcommit_sat_trace.log` is an accidental broad instruction trace from an intermediate debugger attempt and is not used for analysis.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched; rendering/black-cover context only. Not closed.
- OPEN-024: touched; PC090OJ/SAT context only. Not closed.
- OPEN-015: not touched.
- CLOSED issues: none touched.
- New issues opened: none.
- KNOWN_FINDINGS: Option A, no update. This evidence narrows a hypothesis but does not establish a new durable mechanism.

## STOP

STOP triggered: **NO** for the requested staged SAT link-chain attribution. Measurement limitation recorded: exact post-handoff true VDP SAT bytes at `VRAM 0xF800` were not independently dumped; staged SAT link-chain proof and full-SAT-DMA static proof are sufficient to reject stale/unterminated staged-chain traversal as the sampled mechanism.
