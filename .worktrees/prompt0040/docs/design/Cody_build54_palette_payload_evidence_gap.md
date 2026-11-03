# [Cody — Build 54/55 Palette Payload Artifact Generation]

Type: Phase A evidence gate (read-only)  
Outcome: STOP (Phase A gate FAIL)  
Scope: palette payload source + scene mapping authority for Build 55 producer work

## Phase A

### §A.1 Real palette source data

Evidence that non-placeholder palette source data exists in current project artifacts:

- Title path call chain:
  - `build/maincpu.disasm.txt` shows `0x03AA54: jsr 0x5a356` ([build/maincpu.disasm.txt:73679](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73679))
  - `0x5A356` loads `%a0 = 0x5A6FA`, `%d0 = 1`, `%d1 = 0`, then `jsr 0x59AD4` ([build/maincpu.disasm.txt:113661](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113661))

- Converter routine:
  - `0x59AD4` writes converted words to `0x200000 + (d0<<5)` via `%a1` ([build/maincpu.disasm.txt:112973](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112973))

- Gameplay path call chains (project artifacts classify these as gameplay palette callsites):
  - `0x55F60 -> bsrw 0x56128`, then `0x56128/0x56176/0x5618C` call `0x59AD4` using source tables `0x5649E`, `0x564FE`, `0x5651E` ([build/maincpu.disasm.txt:107790](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107790), [build/maincpu.disasm.txt:107906](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107906))
  - Additional gameplay palette callsites at `0x575FE`, `0x57610`, `0x57816`, `0x5782A`, `0x5783E`, `0x57850`, `0x598C2`, `0x598F0`, `0x5999A`, `0x599F0`, `0x59A20`, `0x59A50`, `0x59A80` (all `jsr/bsr 0x59AD4`) ([build/maincpu.disasm.txt:109681](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109681), [build/maincpu.disasm.txt:112815](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112815))

- Raw data samples from `build/regions/maincpu.bin` (non-zero, varied `0x0xxx` values):
  - `0x5A6FA`: `0000 0ff8 0ec0 0c90 0a70 0850 0740 0530 ...`
  - `0x5649E`: `0000 0233 0455 0566 0788 09aa 0a87 0044 ...`
  - `0x564FE`: `0000 0000 0fb9 0f97 0b65 0740 0420 0890 ...`
  - `0x5651E`: `0000 0111 0eee 0fa8 0a54 0643 0900 0600 ...`
  - `0x59910`: `ffff ffff ffff 00df ...`

### §A.2 Per-scene mapping evidence (scene 0/1/2)

Confirmed scene IDs in current direct path:

- `apps/rastan-direct/src/scene_load.s` maps scene IDs:
  - `0 = title` (default path)
  - `1 = gameplay`
  - `2 = endround`
  ([scene_load.s:33-44](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/scene_load.s:33))

Confirmed gap for palette payload authority:

- Current direct source has tile preload manifests only; no scene palette manifests (`pc050cm_palette_*`) and no palette producer code in `load_scene_tiles` ([scene_load.s:112-124](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/scene_load.s:112), [scene_load.s:27-94](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/scene_load.s:27))
- `tools/build_rastan_regions.py` emits no scene palette payload files ([build_rastan_regions.py:175-215](/home/tighe/projects/rastan-genesis/tools/build_rastan_regions.py:175))
- Andy’s root-cause document explicitly leaves “identify arcade ROM palette table address(es) for each scene (title/gameplay/endround)” as a pending step ([Andy_build54_palette_root_cause.md:169-170](/home/tighe/projects/rastan-genesis/docs/design/Andy_build54_palette_root_cause.md:169))
- Project strategy doc still marks scene-level palette ownership and per-stage active palette state as unproven ([rastan_palette_port_strategy.md:495-500](/home/tighe/projects/rastan-genesis/docs/project/rastan_palette_port_strategy.md:495))

### §A.3 Phase A gate decision

- §A.1 real palette source data located: **YES**
- §A.2 definitive per-scene mapping (title/gameplay/endround) for Build 55 payload files: **NO**
- Phase A gate: **FAIL**

## Specific evidence gap (blocking Phase B)

Missing artifact authority required before Phase B:

1. A project-cited mapping from scene IDs `0/1/2` to concrete palette payload source table(s) and selection rule(s), including how gameplay/endround choose among the multiple observed `0x59AD4` callsite/table networks.
2. Build-time authoritative selection that yields one 64-word payload per direct-rastan scene preload (`title`, `gameplay`, `endround`) without guessing.

Until that authority exists, generating `pc050cm_palette_title.bin`, `pc050cm_palette_gameplay.bin`, and `pc050cm_palette_endround.bin` for Build 55 would require unverified selection.

## Integrity

- §A.1 real palette source data located: YES
- §A.2 per-scene mapping determined: NO
- §A.3 Phase A gate: FAIL
- Conversion invented or extrapolated: NO
- Diagnostic placeholders used as payload: NO
- Phase B implementation attempted: NO
- STOP triggered: YES (Rule 21 / Phase A fail)
