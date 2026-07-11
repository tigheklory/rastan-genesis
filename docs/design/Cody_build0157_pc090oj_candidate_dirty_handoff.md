# Cody - Build 0157 PC090OJ Candidate/Dirty Handoff

**Date:** 2026-07-10
**Type:** Analysis documentation only
**Build context:** Build 0156 accepted; Build 0157 sprite-candidate investigation
**Baseline branch / HEAD:** `rastan-direct-proposal` / `5668c6e`
**Accepted ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0156.bin`
**Accepted ROM SHA256:** `03c6e8aa747700235437706adb206968b1f737453ad436959681e19d299fdf01`
**Scope:** No source/spec/tool/Makefile/ROM/build/invariant changes. No new traces. No collision, scroll, continue/game-over, D00298, Exodus, or tilemap work.

## Baseline

The Build 0157 evidence question is narrow: populated PC090OJ mirror/object records exist in Genesis Build 0156 gameplay, but the existing gameplay sprite trace reports no candidates/decodes/drawables/emissions. The handoff question is where the current retained PC090OJ renderer hands mirror writes to candidate processing and SAT/VBlank commit.

Current trace evidence under `states/traces/build_0157_gameplay_sprites/` records:

- Genesis gameplay object RAM has coded records: `objcoded=212` in repeated `2/3/0` samples, and `objcoded=220` in `2/4/1` samples.
- Live object-RAM writes occur at `runtime_genesis_pc 0x071BB8` and `runtime_genesis_pc 0x071A8A`.
- `pc090oj_mirror_dirty` writes occur at `runtime_genesis_pc 0x071BD0` and `runtime_genesis_pc 0x071AA6`.
- `pc090oj_scan_active` runtime value is `0x0001`.
- The diagnostic counters `pc090oj_candidate_count`, `pc090oj_decoded_count`, and `pc090oj_emitted_count` are not reliable as sole evidence: the inspected source declares them, but the currently inspected processing path does not visibly maintain them.

## Phase 0

**Relevant priors from `KNOWN_FINDINGS.md`:**

- `KF-011` - frame progression is owned by the arcade VBlank; Genesis VBlank is servicing-only.
- `KF-016` - title-state VBlank includes PC090OJ/sprite-RAM clear patterns and off-screen marker semantics.
- `KF-026` - PC090OJ runtime write surfaces are not fully statically enumerable; runtime evidence is required for pointer-indexed write surfaces.
- `KF-032` - copied arcade writes into PC080SN/PC090OJ hardware space must route through the translated staging path, not raw Genesis VDP mirror space.

**Rediscovery Hazard HIGH findings touched:**

- `KF-011` and `KF-032` are HIGH-hazard architecture/write-routing priors. This task does not contradict them.

**Deferred-appendix entries relevant:**

- None. The task does not rely on deferred appendix entries.

**Task classification:** EXTENDING. This extends the active `OPEN-024` PC090OJ sprite-subsystem work and the `OPEN-001` graphics bring-up context.

**Open/Closed issues touched:**

- Open: `OPEN-001`, `OPEN-024`; `OPEN-018` context only for raw PC080SN/PC090OJ routing discipline.
- Closed: none touched beyond respecting prior closure boundaries.

**Contradiction of CONFIRMED or STRONG finding detected:** NONE.

## Files / Evidence Inspected

Inspected only the allowed files and directory:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `states/traces/build_0157_gameplay_sprites/`

Baseline verification:

- `git branch --show-current`: `rastan-direct-proposal`
- `git rev-parse --short HEAD`: `5668c6e`
- Build 0156 SHA matches the prompt.

Pre-existing unrelated dirty file observed and not touched:

- `build/mame/home/genesistrace/genesis_exec_trace.log`

## Exact Writer Paths

### `runtime_genesis_pc 0x071A8A`

Attribution: `.Lpc090oj_emit_slot`, the legacy producer bridge in `pc090oj_hooks.s`.

Evidence:

- Runtime trace `gen_prod.txt` records writes at `0x071A8A/0x071A8C/0x071A90/0x071A94`, matching the four-word record write shape.
- Source `.Lpc090oj_emit_slot` writes four words to `pc090oj_object_ram` at `pc090oj_hooks.s:192..204`.
- `.Lpc090oj_emit_slot` then calls `.Lpc090oj_candidate_set_d0` and sets `pc090oj_mirror_dirty`.

Note: `.Lpc090oj_emit_slot` is a local label and is not exported in `symbol.txt`; this attribution is supported by source order plus the four-word write pattern and the observed dirty write.

### `runtime_genesis_pc 0x071BB8`

Attribution: `.Lpc090oj_family_apply_record`, called by exported `pc090oj_workram_block_sprites`.

Evidence:

- `symbol.txt` exports `pc090oj_workram_block_sprites = 0x00071B4A`.
- Runtime trace `gen_prod.txt` records writes at `0x071BB8/0x071BBA/0x071BBE/0x071BC2`, followed by `pc090oj_mirror_dirty` at `0x071BD0`.
- Source `pc090oj_workram_block_sprites` calls `.Lpc090oj_family_apply_record` for block A/B records (`pc090oj_hooks.s:272..299`).
- Source `.Lpc090oj_family_apply_record` writes four words into `pc090oj_object_ram`, sets `pc090oj_mirror_dirty`, calls `.Lpc090oj_sync_record_from_mirror`, then clears the candidate (`pc090oj_hooks.s:307..323`).

## Candidate-Bit Behavior By Writer

### `.Lpc090oj_emit_slot`

`.Lpc090oj_emit_slot` sets candidate state:

- Writes record words to `pc090oj_object_ram`.
- Calls `.Lpc090oj_candidate_set_d0` with `d0 = record`.
- Sets `pc090oj_mirror_dirty` to `1`.

Relevant source:

- `.Lpc090oj_emit_slot`: `pc090oj_hooks.s:192..204`
- `.Lpc090oj_candidate_set_d0`: `pc090oj_hooks.s:147..158`

### `.Lpc090oj_family_apply_record`

`.Lpc090oj_family_apply_record` does not leave a candidate bit set:

- Writes record words to `pc090oj_object_ram`.
- Sets `pc090oj_mirror_dirty` to `1`.
- Calls `.Lpc090oj_sync_record_from_mirror` immediately.
- Calls `.Lpc090oj_candidate_clear_d6` immediately after direct sync.

Relevant source:

- `pc090oj_workram_block_sprites`: `pc090oj_hooks.s:272..299`
- `.Lpc090oj_family_apply_record`: `pc090oj_hooks.s:307..323`
- Comment explicitly states this family does not set a candidate and later unconverted writes re-set candidates: `pc090oj_hooks.s:264..270`.

## `pc090oj_mirror_dirty` Behavior

Observation-only statement:

`pc090oj_mirror_dirty` is written by observed producer paths, but no inspected source path consumes or clears it before `vdp_prepare_sprites` processes candidates.

Writers in inspected source include:

- `.Lpc090oj_emit_slot`: `pc090oj_hooks.s:204`
- `.Lpc090oj_mirror_write_word_a1_d0`: `pc090oj_hooks.s:234`
- `.Lpc090oj_mirror_write_byte_a1_d0`: `pc090oj_hooks.s:256`
- `.Lpc090oj_family_apply_record`: `pc090oj_hooks.s:321`
- `genesistan_hook_3ad44_dispatch` PC090OJ branch: `pc090oj_hooks.s:531`

`vdp_prepare_sprites` does not test or clear `pc090oj_mirror_dirty`.

## Where Candidate Bits Are Consumed

Candidate bits are consumed only by `.Lpc090oj_process_candidates`:

- Enters with `d6 = 0`.
- Checks the candidate byte for each 8-record group.
- If the byte is zero, skips the whole group with no decode/sync.
- If a record bit is set, calls `.Lpc090oj_sync_record_from_mirror`.

Relevant source:

- `.Lpc090oj_process_candidates`: `pc090oj_hooks.s:1070..1105`
- Sync call: `pc090oj_hooks.s:1094`

## Where Candidate Bits Are Cleared

Candidate bits are cleared in two places:

1. After candidate-driven VBlank sync:
   - `.Lpc090oj_process_candidates` clears the processed record bit after `.Lpc090oj_sync_record_from_mirror`.
   - Source: `pc090oj_hooks.s:1094..1100`

2. In the direct semantic family path:
   - `.Lpc090oj_family_apply_record` calls `.Lpc090oj_candidate_clear_d6` immediately after direct sync.
   - Source: `pc090oj_hooks.s:322..323`

The clear helper itself is `.Lpc090oj_candidate_clear_d6` at `pc090oj_hooks.s:171..183`.

## `vdp_prepare_sprites` Behavior When `pc090oj_scan_active == 1`

`_vblank_service` calls `vdp_prepare_sprites` before DISPLAY_OFF:

- `_vblank_service`: `vdp_comm.s:164..176`

When `pc090oj_scan_active == 1`, `vdp_prepare_sprites`:

1. Skips `.Lpc090oj_renderer_init`.
2. Checks `pc090oj_bootstrap_pending`.
3. If bootstrap is pending, clears it and calls `.Lpc090oj_set_all_candidates` once.
4. Calls `.Lpc090oj_process_candidates`.
5. Copies `pc090oj_represented_count` into `staged_sprite_active_count`.
6. Returns.

Relevant source:

- `vdp_prepare_sprites`: `pc090oj_hooks.s:958..974`
- `.Lpc090oj_renderer_init` sets `pc090oj_scan_active = 1`: `pc090oj_hooks.s:999..1030`
- `.Lpc090oj_set_all_candidates`: `pc090oj_hooks.s:1035..1043`

Runtime trace reports `pc090oj_scan_active(0xFF71EA?)=0001` in `gen_counters.txt`.

## First Exact Divergence

Confirmed structural observations:

- Populated `pc090oj_object_ram` records exist in gameplay samples (`objcoded=212` / `220`).
- `pc090oj_mirror_dirty` is written by observed producer paths.
- `pc090oj_mirror_dirty` is not consumed by `vdp_prepare_sprites`.
- Candidate processing is driven only by `pc090oj_candidate_bitset`.
- `.Lpc090oj_family_apply_record` intentionally clears the record candidate after direct sync.

Working hypothesis:

The first handoff divergence is at the mirror-dirty to candidate-processing boundary: mirror records can be updated and marked dirty, but the VBlank prepare path does not use `pc090oj_mirror_dirty` to force or request candidate processing. Therefore, if no candidate bit remains set, `.Lpc090oj_process_candidates` sees zero candidate bytes and skips record groups without consulting the populated mirror.

Important caution:

The existing diagnostic counters are not sufficient as sole root-cause proof. They are useful symptom evidence, but the inspected source does not maintain all of them in the visible processing path. A Build 0157 implementation should validate with direct candidate bitset / represented set / SAT evidence, not only these counters.

## Recommended Smallest Implementation Boundary For Andy

Recommended boundary:

- Keep the work inside `pc090oj_hooks.s`.
- Start at `vdp_prepare_sprites` and the candidate/dirty handoff.
- Do not add a second renderer, second SAT path, Genesis-owned lifecycle, source seeding, or broad sprite/object/collision changes.

Smallest safe candidate:

- Consume `pc090oj_mirror_dirty` in `vdp_prepare_sprites` before `.Lpc090oj_process_candidates`.
- When dirty is set, clear the dirty flag and request reevaluation through the existing candidate mechanism.
- Preserve arcade ownership: arcade producers still write mirror/object intent; Genesis VBlank still only prepares/commits staged sprite state.

This is a boundary recommendation, not an implementation.

## `.Lpc090oj_set_all_candidates` Assessment

`.Lpc090oj_set_all_candidates` is acceptable as a conservative dirty-frame fallback, but it is broad.

Why acceptable:

- It already exists and is used for bootstrap/global reevaluation.
- It stays inside the retained PC090OJ renderer path.
- It does not create a second SAT path or change arcade control flow.
- It is safer than guessing which live writer family failed to leave candidates, especially while the counters are unreliable.

Why broad:

- It marks all 256 records whenever dirty is consumed.
- That may do more scan/decode work than necessary.

Recommendation:

- For a first Build 0157 implementation, `.Lpc090oj_set_all_candidates` is an acceptable conservative boundary if Andy validates timing and final SAT/represented output.
- If cost becomes a problem, narrow later to a dirty-record bitset or ensure each writer leaves precise candidates, but that is a second design step.

## Andy Inspect-First List

Inspect in this order:

1. `pc090oj_hooks.s:958..974` - `vdp_prepare_sprites`.
2. `pc090oj_hooks.s:1070..1105` - `.Lpc090oj_process_candidates`.
3. `pc090oj_hooks.s:147..183` - candidate set/clear helpers.
4. `pc090oj_hooks.s:192..204` - `.Lpc090oj_emit_slot`.
5. `pc090oj_hooks.s:264..323` - `pc090oj_workram_block_sprites` / `.Lpc090oj_family_apply_record`.
6. `pc090oj_hooks.s:220..256` - raw word/byte mirror writers.
7. `pc090oj_hooks.s:486..533` - `genesistan_hook_3ad44_dispatch` PC090OJ branch.
8. `vdp_comm.s:164..176` - VBlank ordering.
9. `apps/rastan-direct/out/symbol.txt` symbols around `vdp_prepare_sprites`, `pc090oj_workram_block_sprites`, `pc090oj_candidate_bitset`, `pc090oj_mirror_dirty`, and `pc090oj_scan_active`.
10. `states/traces/build_0157_gameplay_sprites/gen_prod.txt`, `gen_perframe.txt`, `gen_counters.txt`, and `gen_sprites.txt`.

## Stop Conditions Encountered

None.

No source change, build, ROM artifact, trace rerun, bookmark, or issue-ledger edit was required.

## Architecture Compliance

CONFIRMED.

This analysis keeps arcade code as the program. The recommended implementation boundary preserves Genesis-side code as helper/service code: arcade producers populate PC090OJ mirror/object state; VBlank service prepares/commits staged sprite state; no Genesis-owned gameplay loop or alternate lifecycle is proposed.

## Open / Closed Issues Impact

- Open issues touched: `OPEN-001`, `OPEN-024`.
- Open issues context only: `OPEN-018`.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: collision, scroll, continue/game-over, D00298, Exodus, tilemaps, broader raw-write inventory, broader sprite visual correctness.
- Closed issues touched: NONE.

## KNOWN_FINDINGS Impact

Option A - no new finding to index.

Rationale: this is a handoff/working-hypothesis document for an active implementation boundary. It does not yet establish a durable new system-behavior finding beyond existing PC090OJ/open-issue context.

## STOP

STOP triggered: NO.
