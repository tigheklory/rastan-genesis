# Cody Actor Renderer / Tile / Palette Verification

Date: 2026-09-18  
Scope: original arcade static reverse engineering, ORIGINAL ARCADE MAME corroboration, and offline tooling only.  
ROM/build status: no Genesis ROM was built; no Genesis runtime source was changed; build counter remains 360.

## Result

The offline reconstruction failed for two independent reasons:

1. it routed nearly every field family through compositor table 0 even though spawn byte 2 low nibble is copied to actor `+0x38`, and `0x3D054` dispatches selectors 0..4 to five different compositor tables;
2. it commonly rendered the base-loader initialization byte as though it were the current frame. The renderer actually consumes the live actor byte `+0x01`, which update routines continuously rewrite.

The old VM also misread control `0x40` as the displayed horizontal flip, ignored the `D6/+0x20` branch rule, ignored the `0x70` Y adjustment, and did not model the palette attribute substitution at `0x3C9E8`.

The corrected VM and its verifier produce eight exact original-arcade SAT matches. Machine-readable results are in `Cody_actor_render_verified.json`.

## Semantic cut

For this offline audit, the semantic boundary is:

`live 0x40-byte actor state -> 0x3D054 compositor selection -> 0x3C902 PC090OJ SAT descriptor expansion`.

This work models the original chip tail for evidence only. It does not add a production PC090OJ emulation layer, shadow RAM, or Genesis runtime dependency. No native replacement or chip-tail removal was in scope.

## Memory model

### A5

`A5 = 0x10C000` is confirmed by the canonical project/exported addressing and by the live actor addresses in MAME. For example, the ninth ordinary actor is `A5+0x4C8 = 0x10C4C8`; the boss BODY sample is `A5+0x708 = 0x10C708`.

### Actor versus render record

There is no actor-to-separate-render-record copy in the audited routes. `0x41DAE` and `0x45DFA` point `A4` directly into 0x40-byte actor blocks and pass fields from that same slot to `0x3D054`:

| Block | Normal renderer (`0x41DAE`) SAT lane | Boss renderer (`0x45DFA`) SAT lane |
|---|---:|---:|
| `A5+0x508` | `0xD001C8` | not used |
| `A5+0x5C8` | `0xD00300` | `0xD00460` |
| `A5+0x2C8` | `0xD00460` | not used |
| `A5+0x748` | `0xD00170` | `0xD00170` |
| `A5+0x8C8` | not used | `0xD00300` |

The names “source gameplay actor” and “render record” described the same physical record in Andy's handoff for these paths. The distinction is a role, not a copy boundary.

### `+0x752`

The instruction is literally `move.b D6,(0x752,A4)` at `0x4A09C`, not `(0x752,A5)`. Because adjacent actors advance `A4` by 0x40, this is a parallel per-slot byte array 0x752 bytes after each actor slot. It is outside the 0x40-byte actor record.

Spawn decoding at `0x4A086` is:

| Spawn byte | Destination | Meaning |
|---|---|---|
| byte 0 | actor `+0x04` | actor class/update selector |
| byte 1 | actor `+0x3E` | ordinary family |
| byte 2 low nibble | actor `+0x38` | compositor selector |
| byte 2 high nibble | `(0x752,A4)` | parallel base/palette variant selector |
| byte 3 | actor `+0x36` | spawn/state field, not current animation |

`0x4544E`, `0x4545A`, and `0x456C2` consume the parallel variant byte for base and palette selection.

### Proven actor fields

| Base | Offset | Meaning in these actor records |
|---|---:|---|
| `A4` | `+0x01` | current animation/program index consumed by renderer |
| `A4` | `+0x02` | facing (`D7`) |
| `A4` | `+0x03` | state gate used with `D6 bit 0` at `0x3CA26` |
| `A4` | `+0x06` | record type for the `0x4543E` loader path |
| `A4` | `+0x0B` | subframe/index used by coordinate-only special modes |
| `A4` | `+0x16` | X coordinate |
| `A4` | `+0x18` | extra Y term for control `0x70` |
| `A4` | `+0x1A` | Y coordinate |
| `A4` | `+0x1E` | base graphics tile code |
| `A4` | `+0x20` | mirror-control byte passed as `D6` |
| `A4` | `+0x27` | palette/attribute override; bit 6 enables low-byte replacement |
| `A4` | `+0x28` | loader-supplied actor field; not used as the compositor base |
| `A4` | `+0x2C` | loader-supplied actor field; not used as the compositor base |
| `A4` | `+0x38` | compositor selector |
| `A4` | `+0x3E` | ordinary spawn family |
| `A4`-relative parallel area | `+0x752` | variant selector outside the actor record |

## Compositor dispatch

The exact `0x3D054` mapping is:

| actor `+0x38` | wrapper | pointer table |
|---:|---:|---:|
| 0 or other | inline at `0x3D08E` | `0x3D09E` |
| 1 | `0x4770E` | `0x4771C` |
| 2 | `0x3F0BC` | `0x3F0CE` |
| 3 | `0x3FFDC` | `0x40004` |
| 4 | `0x3FFF0` | `0x4002C` |

The field base table at `0x45502` and spawn schedules prove compositor 0 for families 0..6 and compositor 1 for families 7..11. Valkyrie (family 8) and Serpent (family 11) were therefore decoded through the wrong table in the old bestiary.

## Current-frame bug

`0x4544E` and `0x4543E` initialize actor `+0x01`, but gameplay writers later replace it. The verification uses legal values observed in original MAME:

| Actor | Old bestiary frame | Live verified `+0x01` |
|---|---:|---:|
| Lizardman | `0x17` | `0x17` |
| Chimera | `0x23` | `0x52` |
| Four-Armed | `0x5F` | `0x62` |
| Valkyrie | `0x4D` | `0x4F` |
| Serpent/base `0x0400` | `0xB5` | `0xB6` |
| base `0x01CB` | `0xD0` | `0xD0` |

The failure was not only a bad frame number: for families 8 and 11 the frame was also looked up in the wrong table.

## `0x3C902` general program

The corrected record format is four bytes:

`control, signed Y delta, unsigned tile delta, signed X delta`.

- `0x40` negates the tile delta. It is not by itself the final displayed flip.
- `0x70` adds actor `+0x18` to Y.
- `0x80` sets PC090OJ HFLIP on the `0x3C960` branch.
- actor `+0x27` bit 6 replaces the low byte of word 0.
- facing and the `D6 bit0 / actor+0x03` rule choose `0x3C960` versus `0x3C9A6`.
- `0x3C9A6` sets HFLIP and computes `X = actorX - delta - 16`.
- `0x3C960` computes `X = actorX + delta`.
- tile code is masked by PC090OJ at draw time to 13 bits.
- `0xFF` parks the remainder of the caller's fixed SAT budget at Y `0x180`.
- the general path does not emit VFLIP.

The audited legal frames use the general path and exercise control families `0x00`, `0x40`, `0x70`, and `0x80`. The special dispatcher remains explicitly recognized at `0x10/20/30/50/60/90/A0/B0/C0`; the VM refuses those coordinate-only programs without seeded SAT data rather than fabricating tile words.

## Tile decoder

MAME's PC090OJ device declares `gfx_16x16x4_packed_msb`, uses `(word2 & 0x1FFF)` as the code, and draws transparent pen 0. The verified decoder is therefore:

- 128 bytes per code;
- 16 x 16 pixels;
- 8 packed bytes per row;
- high nibble first;
- low nibble second;
- pen 0 transparent;
- effective code masked to 13 bits.

No pixel-decoder defect was found. Wrong effective tile numbers came from the bad compositor/table/frame model.

## Coordinates and flips

Both directions are covered. Lizardman/Four-Armed/Valkyrie/Serpent and the boss samples exercise the HFLIP branch; Chimera and `0x01CB` exercise the opposite facing branch with clear word0 and reversed X placement. All eight cases match exact word0, tile, order, piece count, and relative coordinates.

The durable MAME frame captures occur after the game's update/render sequence, so an actor that moves in the same frame can differ by one translation pixel from the already-written SAT. Translation is intentionally removed for the equality check; every within-composite coordinate delta remains exact. The enhanced trace records the raw actor, resolved program pointer, and SAT lane together to make this phase ordering explicit.

## Palette path

For all eight verified occurrences, including both boss records, the formula is confirmed:

`pool = maincpu[0x3BA88 + (round-1)*32 + line]`

`source = maincpu[0x4FD02 + pool*32 : +32]`

The 16 source words are nibble-packed `0RGB`. `0x3BA64` doubles each nibble and rearranges it into arcade `xBGR-555`. PC090OJ contributes color-bank base `0x30`, so the effective palette-RAM bank is `0x30 | (SAT word0 & 0x0F)`. The reduced MAME evidence captures those live 16 `xBGR-555` words, and all eight banks exactly equal the transformed ROM source. The report's RGB conversion expands the three 5-bit runtime channels.

Both boss BODY samples emit palette line `0xF`: Round 1 selects pool 11 and Round 5 selects pool 3. Their live effective bank `0x3F` exactly matches the respective transformed round/line pool. The earlier apparent mismatch was an evidence-address error—reading bank `0x0F` instead of PC090OJ bank `0x3F`—and is not preserved in the final evidence.

No palette decision in `specs/palette_decisions.json` was changed. The registry entries covering Stage-1 Lizardman, Chimera, Valkyrie, Four-Armed, Flying Demon, and bats remain authoritative for their scoped Genesis realization; this audit only corrects the offline arcade compositor and does not create a competing palette-decision registry.

## Regression results

| Case | Result | Correction |
|---|---|---|
| Lizardman | PASS | control; compositor 0, live `0x17` |
| Four-Armed | PASS | compositor 0, live `0x62` |
| Chimera | PASS | live `0x52`; opposite-facing branch |
| Valkyrie | PASS | compositor 1, live `0x4F` |
| Serpent/base `0x0400` | PASS | compositor 1, live `0xB6` |
| `0x01CB` | PASS render; identity UNKNOWN | family 5/base association is correct; “Small Crawler” is unsupported and removed. The wizard-like composite is real arcade output, not a base/table mix-up. |
| `0x061D` | PASS | record types 14/15, Round-1 boss BODY/component family. “Centaur” rejected. Type 15 components are created at `0x457D0`. |
| `0x0988` | PASS | record types 16/17, Round-5 boss BODY/child family. Type 16 creates five type-17 children at `0x423B2`. Visual dragon resemblance is not treated as a semantic name. |
| one real boss | PASS | Round-1 type-14 BODY, 17 exact pieces, program `0x47908`, compositor 1, live palette line 15 captured |

The boss relationship is code-proven as BODY plus child/component records. It is not a field-family mapping. Weapon/projectile/effect semantic names were not assigned where code did not prove them.

## Original-MAME evidence

- Existing broad corroboration: `analysis/enemy_sprite_lexicon/evidence/arcade_sweep/all_observations.csv`.
- Existing Valkyrie provenance: `analysis/graphics_optimizer/round1_phase1_corpus/full_capture/full_observations.csv` and `owners.csv`.
- New same-frame actor/SAT/palette evidence for all eight cases: `analysis/actor_render_verification/original_arcade_actor_samples.csv`.
- Reproducible capture: `tools/mame/scripts/arcade_actor_renderer_verify.lua`.
- Exact reducer/check: `tools/graphics_optimizer/verify_actor_compositor.py`.

The Round-5 boss capture uses the established level-selector route plus an explicit `A5+0x118=5` round setup. It changes progression setup only; it never writes actor records, compositor programs, SAT, or palette RAM. The sample is labelled selector-assisted in the JSON/report.

## Tool changes

`compositor_vm.py` now centralizes table dispatch, program address selection, exact general-path SAT semantics, tile decoding, and explicit rejection of unseeded coordinate-only special handlers.

`build_bestiary.py` imports that implementation instead of maintaining a divergent private VM. The manifest now uses verified live frames for the regression cards, compositor 1 for families 7/8/9/11, removes the unsupported `0x01CB` and `0x061D` names, and records the `0x061D`/`0x0988` boss ownership.

## Limitations

- The live Ghidra project was not mutated. The concrete rename/type/comment change-list is in `Cody_actor_render_ghidra_changes.md`.
- Special coordinate-only modes are statically dispatched and documented, but none was required by the eight legal regression frames. They still require seeded SAT tile/attribute records for faithful offline execution.
- Semantic boss names remain UNKNOWN; BODY/component ownership is proven without naming from appearance.
