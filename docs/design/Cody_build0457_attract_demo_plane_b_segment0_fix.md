# Build 0457 — Attract-Demo Plane-B Segment-0 Scene-Entry Fix

**Date:** 2026-10-19

**Status:** CANDIDATE — PENDING TIGHE REAL-GENESIS ACCEPTANCE

**Issue:** OPEN-031
**Accepted baseline:** Build 0456
**ROM-producing source:** `fab0325eeb5b6cd0773391dba191cb14b2c1b22d`

## Result

Build 0457 corrects one ownership error at the first native Plane-B scene population. The retained
arcade initial-fill countdown `A5+0x10AA` is now tested before the native tileset cache-hit branch.
Every real `0x0503DC` initial 64-publication fill therefore re-establishes the complete native
scene-entry contract, even when gameplay tileset ID 1 remains resident from an earlier attract-demo
cycle. Ordinary steady-state strips (`A5+0x10AA == 0`) retain the existing cache fast path.

No palette decision, PC090OJ family, ordinary map renderer, Build-0456 selector relocation, or
Build-0455 item-screen behavior was intentionally changed. Tighe must verify the attract demo and
ordinary gameplay on real hardware before this candidate can be accepted or OPEN-031 closed.

## Static provenance and first divergence

Normal play and attract-demo play share the retained arcade R1 setup chain:

```text
0x03A64C -> 0x04529C -> 0x0501E2 -> 0x0503DC
```

`0x04529C` preserves the stage selector at `A5+0x1242`. `0x0501E2` derives the stage/segment at
`A5+0x013E`, Plane-B descriptor-table index at `A5+0x1386`, zeroes the scroll/ring counters
`A5+0x10CC/0x10F4/0x10CA/0x10F6`, installs the descriptor walker at `A5+0x10FC`, installs the map
stream at `A5+0x10C6`, and calls `0x0503DC`. The attract demo differs downstream by recorded input;
it does not own a different R1 map table. Generated Plane-B records are identical for both entries.

Current Build-0457 `address_map.json` correlations are:

| Arcade PC | Runtime Genesis PC | Role |
|---:|---:|---|
| `0x04529C` | `0x045480` | shared stage initialization |
| `0x0501E2` | `0x0503C6` | shared map/ring initialization |
| `0x0503DC` | `0x0505C0` | initial 64-publication fill |
| `0x050482` | `0x050666` | completed-fill publication boundary |

The first incorrect semantic state was inside `genesistan_hook_itempage_strip_blit`. Before Build
0457 it compared the desired gameplay tileset with `genesistan_current_pc080sn_tileset_id` before
testing the retained initial-fill owner. Frontend/attract screens do not reset that ID. A later demo
entry could therefore hit `desired == current == 1` and skip all scene-entry work while the retained
arcade state correctly began a fresh Segment-0 fill.

The cache hit skipped:

- `genesistan_scene_present_pending` arm and display blanking;
- `load_scene_tiles(1)` and `fg_cache_reset`;
- fixed Plane-B LUT/package installation;
- the coherent full-plane publication at the `0x050482` completed-fill boundary.

Fresh Segment-0 rows were consequently built while the native ring/package still represented the
later state of a previous demo cycle. Normal first gameplay normally entered with a different native
identity and took the full load path, explaining why its Plane B was correct.

## Exact correction

At `.Litempage_blit_tileset_selected`:

1. test `A5+0x10AA` first;
2. if nonzero, arm `genesistan_scene_present_pending` and force `load_scene_tiles`;
3. only when the countdown is zero, use the tileset cache-hit fast path.

The logical ring origin and source state remain the retained arcade values initialized by
`0x0501E2`; Build 0457 does not invent attract-specific coordinates or map data.

## Native-replacement boundary

The semantic cut remains the retained arcade decision to initialize R1 map/scroll state and perform
the initial scene fill, followed by direct Genesis Plane-B staging/publication. Build 0457 corrects
the native resource/publication lifecycle at that decision. The removed tail remains PC080SN
descriptor execution, C-window/name-RAM writes, and chip-specific publication. No chip shadow,
tall-buffer projection, per-write translation, fallback, or runtime interception was added.

## Durable verifier

`tools/translation/verify_attract_demo_plane_b_scene_entry.py` is invoked by the canonical build.
It proves the initial-fill countdown test and presentation arm precede the tileset comparison, the
initial fill branches to `load_scene_tiles`, and only zero-count steady-state strips can cache-skip.

```text
ATTRACT_DEMO_PLANE_B_SCENE_ENTRY_PASS
scene_fill_owner=a5+0x10AA
cache_hit_cannot_skip=present_arm,scene_reload,cache_reset,package_install
```

## Validation

| Check | Result |
|---|---|
| Root scene-entry verifier | PASS |
| Assembly/link and shift reflow (76 sites) | PASS |
| Canonical gate | PASS |
| Gameplay-entry gate | FAIL — legacy post-entry assertions incomplete; 563 frames, gameplay reached, no address/bus/illegal/crash-handler fault |
| Seven-epoch gate | PASS |
| Build-0456 selector relocation verifier | PASS — operand/map `0x051155`, 157 bytes |
| Build-0455 native item-screen verifier | PASS |
| Native title verifier | PASS |
| Shared HUD verifier | PASS |
| BEST-5 verifier | PASS |
| Fixed 30-second Genesis NTSC validation | PASS — 1,798 frames |
| Complete seven-ROM family | PASS |
| `_invincible` verifier | PASS — 66/66 damage table, zero unrelated differences |
| Deterministic rope | PASS — `799/799/799`, `13,333.835 ms`, YES |

The rope result is one frame / 16.688 ms slower than accepted Build 0456 (`798`, `13,317.147 ms`).
No new gameplay trace, Lua route, save state, attract diagnostic harness, or manual navigation was
created or run. The fixed30 validation and established rope benchmark were the only MAME workflows.

## Artifacts

- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0457.bin`
- Canonical SHA-256: `6edfa58f5ea773a200bd8e92d379ba5019cb772e0e6ce3bb009398f2fb457515`
- `_invincible` SHA-256: `1ac8c65a3027284c74c3b57c3b0509af1d5201c15d276893d9e6eb286aca1ea5`
- Size: 2,739,896 bytes each
- Counter: 457
- Fixed30 evidence: `states/traces/rastan_direct_video_test_build_0457_mame_30s_20261019_223909/`
- Rope evidence: `states/traces/build0457_rope_attach_benchmark_invincible/`
- Gameplay-entry evidence: `states/traces/build0457_gameplay_entry_gate_20261019_223859/`

## Acceptance boundary

Required real-hardware proof is attract-demo Segment-0 Plane B correct with subsequent scrolling
correct; ordinary Plane B and Build-0456 R1 progression unchanged; Subround 2 reachable; accepted
item/title/story/BEST-5 screens unchanged. Palette findings are not Build-0457 acceptance criteria.
Phase D and Phase E were not started.
