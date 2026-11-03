# Cody — Permanent full-HUD parallel build variant

Date: 2026-10-16  
Agent: Cody  
Task: Build-system/configuration variant  
Accepted baseline and source label: **Build 0434**

## Correction after user hardware validation (2026-10-16)

The initial conclusion below that `RASTAN_GAMEPLAY_HUD_SPRITES=1` selected a
usable full gameplay HUD is **REJECTED**. Tighe tested the generated artifact
and observed **no gameplay HUD**. The artifact with SHA-256
`00e90a76f0b13e6c8b089946a6ccc5c003b0873ddcae986dd7ed741e59fbb726`
is invalid as a full-HUD baseline and has never been accepted.

A current-source re-audit found no compile-time value that enables the complete
gameplay HUD:

- mode 2 calls `.Lnq_project_p1_hud`, which clears/rebuilds `native_queue_hud`
  with the current-player score and 1UP label only;
- modes 0 and 1 both omit that call and assemble identical executable bytes in
  `pc090oj_hooks.o` (the object files differ only in the absolute config
  symbol's value);
- the flag-independent native `0x05A098` replacement can publish the eight-piece
  energy/status lane when its retained arcade caller reaches it, but this is not
  a complete gameplay HUD and does not produce 1UP, HIGH SCORE, or 2UP;
- the old complete PC090OJ HUD builders/record scanner were retired
  unconditionally. `native_frontend_hud_emit` remains complete for frontend
  scenes, but gameplay scene 1 branches to `.Lnq_gameplay` and never calls it.

Therefore Tighe's mode-0 hypothesis is **rejected for the current Build-0434
source**: mode 0 is executable-code-identical to the tested no-HUD mode 1. No
truthful configuration-only correction exists. The known-bad `_full_hud`
artifact was not replaced with an equally incorrect mode-0 artifact, no Build
0435 was consumed, and the accepted canonical/five-variant family was not
modified. A real full-HUD variant requires an explicitly authorized gameplay
producer implementation/restoration task, which this task forbids.

The remainder of this document preserves the initial build-system result and
mistaken interpretation as historical evidence; it is superseded by this
correction.

## Result

The normal Rastan Direct build family now permanently includes a sixth ROM:

```text
rastan_direct_video_test_build_NNNN_full_hud.bin
```

The canonical/default ROM remains `RASTAN_GAMEPLAY_HUD_SPRITES=2` (1UP and
current-player score). The new variant uses the already-existing
`RASTAN_GAMEPLAY_HUD_SPRITES=1` full gameplay-HUD implementation. No HUD,
frontend, sprite, player, background, death-effect, or gameplay source was
changed.

Build 0434 remains accepted. This task added a same-source configuration
artifact and did not consume Build 0435:

```text
build counter: 434 -> 434
```

## Why both modes are permanent

Mode 2 remains the accepted presentation, performance comparison, regression
isolation point, and fallback. Mode 1 establishes the unoptimized full-HUD
baseline needed to pursue the long-term target of full gameplay HUD at 60 FPS.
Future HUD work must build and preserve both configurations; passing only mode
2 is insufficient.

## Build-system changes

`apps/rastan-direct/Makefile` now:

- defines a normal rolling full-HUD ROM and `full-hud-variant` target;
- invokes that target automatically from the existing normal family workflow;
- names the numbered artifact with `_full_hud` while retaining the canonical
  build number;
- passes every relevant compile-time flag explicitly for all six family
  members, preventing inheritance from a preceding recursive build;
- copies the actual generated `pc090oj_config.inc` used for each family member
  into `out/variant_configs/` as a verification receipt;
- extends the existing `verify-variant-set` target to require all six artifacts
  and validate every receipt;
- refuses to overwrite an existing numbered diagnostic, score, display-off,
  cheat, or full-HUD artifact;
- uses the existing postpatcher's explicit variant coverage-delta facility for
  mode 1 (`-0x1000`). Mode 1 occupies one fewer aligned helper page; no padding
  or invariant weakening was introduced.

The existing target name `dual-build` remains for compatibility, but its normal
family is now:

```text
.bin
_d.bin
_s.bin
_do.bin
_c.bin
_full_hud.bin
```

## Configuration matrix and isolation

| Artifact | HUD | CPU bar | Score metric | Display off | MODE cheat |
|---|---:|---:|---:|---:|---:|
| canonical | 2 | 0 | 0 | 0 | 0 |
| `_d` | 2 | 1 | 0 | 0 | 0 |
| `_s` | 2 | 0 | 1 | 0 | 0 |
| `_do` | 2 | 0 | 0 | 1 | 0 |
| `_c` | 2 | 0 | 0 | 0 | 1 |
| `_full_hud` | 1 | 0 | 0 | 0 | 0 |

All receipts also prove `PC090OJ_MIRROR_RECORDS=256`. The family verifier
passed. Full-HUD was built, the other configurations were rebuilt, and
full-HUD was rebuilt last; both full-HUD outputs were byte-identical. This
proves the generated configuration is refreshed and build order does not leak
one member's flags into another.

## Accepted-artifact protection

The five existing numbered artifacts were not overwritten. Each was rebuilt to
a rolling or temporary verification output and compared byte-for-byte with the
protected accepted artifact.

| Existing artifact | Recorded SHA-256 | Rebuilt result |
|---|---|---|
| canonical | `178838c4eed65f920a78718c63fe1086e55ab0aeb567177f2918898b0ac1d5ca` | BYTE-IDENTICAL |
| `_d` | `ea5cf2a4af6db675afa25cd33b2f5a20a5794a0dfa5d82cafd146f2f4616eaac` | BYTE-IDENTICAL |
| `_s` | `51f47ff0d6cbb44c8e87d7f8b65a920d08e2311f5f66fdb632b8c4f253f6455c` | BYTE-IDENTICAL |
| `_do` | `fc4e7759147c2ab17e887cc2408ecbdb7a05a9fe87e8f93b7e290fbda6b14d8b` | BYTE-IDENTICAL |
| `_c` | `3ec86db1bb87c76921a9e9e8c7f61b906f69832c1252293fb954ff7ef46b0beb` | BYTE-IDENTICAL |

Canonical Build 0434 is therefore unchanged.

## Full-HUD baseline artifact

```text
path: dist/rastan-direct/rastan_direct_video_test_build_0434_full_hud.bin
size: 2,694,840 bytes
SHA-256: 00e90a76f0b13e6c8b089946a6ccc5c003b0873ddcae986dd7ed741e59fbb726
HUD mode: RASTAN_GAMEPLAY_HUD_SPRITES=1
```

The postpatch invariant passed with 231 opcode-replacement sites and exact
variant coverage `0x291EB8` (canonical mode 2 is `0x292EB8`). Both pre- and
postpatch boot guards passed.

## Validation

### Static/build validation

- complete six-ROM artifact family: **PASS**;
- complete per-variant configuration receipts: **PASS**;
- canonical and existing variants reproduced byte-identically: **PASS**;
- full-HUD rebuild after other variants byte-identical: **PASS**;
- full-HUD postpatch coverage/count invariant: **PASS**;
- full-HUD boot guards: **PASS**.

### Standard fixed validation

Platform: **GENESIS NTSC MAME** (`genesis` driver), existing fixed 30-second
workflow, no new route or harness.

Result: **1,798 frames completed**. Evidence:
`states/traces/build0434_full_hud_mame_30s/`.

### Existing deterministic rope benchmark

Platform: **GENESIS NTSC MAME** (`genesis` driver). Existing runner, Lua route,
and summarizer were reused without modification.

Reduced-HUD canonical Build 0434:

```text
803 / 803 / 803 frames
median 803 frames / 13,400.588 ms
deterministic YES
```

Full-HUD Build 0434:

```text
803 / 803 / 803 frames
median 803 frames / 13,400.588 ms
deterministic YES
```

Measured difference: **0 frames / 0.000 ms / 0.000%**. This frame-count route
shows no global progression regression but does not measure fine-grained
per-frame HUD CPU cost. It must not be interpreted as proving that full HUD has
zero runtime cost.

Evidence:

- `states/traces/build0434_rope_attach_benchmark_reduced_hud/`
- `states/traces/build0434_rope_attach_benchmark_full_hud/`

## Architecture and scope accounting

- Semantic subsystem changed: build configuration/family generation only.
- Native semantic cut changed: **NO**.
- Legacy PC080SN/PC090OJ code removed: **NONE** (not a native-conversion task).
- Legacy code intentionally remaining: all accepted Build-0434 runtime code.
- Production HUD implementation changed: **NO**.
- Frontend/attract HUD implementation changed: **NO**.
- Opcode replacement/spec change: **NO**.
- New tooling created: **NONE**.
- Existing project tools reused: Makefile variant/postpatch/boot-guard machinery,
  fixed Genesis trace, rope benchmark runner, Lua route, and summarizer.
- Why new tooling was necessary: not applicable.
- Gameplay driven manually by Cody: **NO**.
- New gameplay trace or route: **NO**.

## USER MUST VERIFY

On real Genesis or Exodus, test
`rastan_direct_video_test_build_0434_full_hud.bin` and confirm:

1. which full gameplay HUD elements appear beyond 1UP/current score;
2. whether every element is visible, correctly positioned, and not offscreen;
3. whether the known score/1UP vertical relationship matches the existing mode-1
   behavior (this task intentionally did not fix it);
4. frontend/title/attract HUD remains unchanged;
5. normal player, background, sprites, and gameplay remain unchanged;
6. compare `_full_hud` and canonical `_do` black-bar load during the opening
   drop and ordinary gameplay.

Full-HUD presentation acceptance: **USER MUST VERIFY**. Build 0434 canonical
remains accepted regardless of this result.

Unresolved limitation: no real-hardware or Exodus visual evidence was produced
by Cody; visual correctness and actual per-frame full-HUD load are not claimed.

Phase D started: **NO**.  
Phase E started: **NO**.  
STOP status: **TASK COMPLETE; USER HARDWARE ACCEPTANCE PENDING**.
