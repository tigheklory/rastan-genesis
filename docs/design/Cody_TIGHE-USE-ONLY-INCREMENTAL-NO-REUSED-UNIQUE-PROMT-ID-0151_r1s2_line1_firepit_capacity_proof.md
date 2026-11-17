TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0151

# R1-S2 Line-1 fire-pit capacity proof

**Date:** 2026-11-17

**Scope:** source/static capacity proof only; no runtime implementation

**Result:** `LOSSLESS_FREE_SLOT_LEASE`; independently, `LOSSLESS_REGIONAL_COMPOSITE`

## 1. Starting state

- Branch: `rastan-direct-proposal`.
- HEAD: `275e2e35e65e46dab46ce685c035e554dea4110d`.
- Makefile build counter: `573`.
- Build 0573 canonical ROM remains the protected working baseline. This task neither rebuilt nor changed it.
- PROMT-ID-0149 is still present as uncommitted analyzer/report work; no commit contains either its report or analyzer.
- Analyzer SHA-256 after this task's narrow extension and stale-prose correction: `1911588ccfcfbdb3418fa87c443ac8b81bf4e7c749293de932f7820a2fdfc1fd`.
- Starting `git status` contained pre-existing modified generated `apps/rastan-direct/out/*`, generated build/address-map/disassembly/trace/inventory files, `apps/rastan-direct/src/sound/sound_comm.s`, `tools/mame/cheat/output.json`, and Andy/Antigravity/roadmap documentation. The 0149 report and analyzer/tests were untracked. All were preserved.
- Test 2.0 input SHA-256 remained `4339688ebe07bc121d5108d464f57b320a6628f4c36cdd71a95cfe5ea8c964cf`; the palette registry remained `9fdd8f928b08cffbacb3536495204a761893889cd79ddd4f692a52a44aa8f0e3`.

## 2. Protected baseline and question answered

Build 0573 is authoritative for every already-correct visual. The narrow answer is **yes**: throughout the proven fire visibility envelope, no legal R1-S2 sprite consumes Genesis Line 1. Slots 1–15 are stable under the existing authored-gameplay writer gates. The nine fire colors therefore fit losslessly without moving or recoloring any Build-0573 sprite mapping.

This proves capacity and writer compatibility only. It does not implement residency. The future semantic cut would remain above PC080SN palette/tile publication: precompile final Genesis fire tile indices and install/restore the regional CRAM lease at the existing authored-scene ownership boundary. No PC080SN chip tail or production code was changed here.

## 3. Exact fire-envelope input

PROMT-ID-0149's established input was reused unchanged:

- fire: PC080SN Layer A, record 18, tiles `$093A..$0949`, usages `LA-0479..LA-0494`, arcade bank `$014`, no sprite component;
- fire pixels X: `9280..9663`;
- camera-left X: `8961..9663`;
- 87 tile-aligned critical viewports;
- decoded records 17–19, forward and reverse traversal;
- lifecycle vocabulary and maximum simultaneous demand: nine colors: `006E 008E 00AE 00CE 00EE 08EE 0AEE 0CEE 0EEE`.

The analyzer's earlier prose still described a superseded ten-color hypothesis even though its arrays and counts were nine. That sentence was corrected; the computed vocabulary and result did not change.

## 4. Possible Line-1 consumers

There are **no** `PROVEN_PRESENT_POSSIBLE` Line-1 consumers and no `UNKNOWN` consumer in the fire envelope. Consequently, legal simultaneous Line-1 sprite demand is the empty set.

R1-S2's schedule/roster evidence contains the family-2 Green Sword Knight (`base $033E`) and the marker-M burst path; both use Line 0 in Build 0573. The separate family-8 rope climber (`base $0241`, programs `$56/$59/$5A`) also does not introduce Line 1. The retained R1 sprite-control evidence is high bits `$30`; its relevant program nibbles map outside Line 1. This is sufficient for the Line-1 exclusion and does not claim that unrelated rope-climber pixel-authoring work is complete.

## 5. Excluded authored Line-1 consumers

| Status | Identity / source | Spawn and lifetime proof | Test 2.0 usage | Code/bank | Actual mapped indexes | Why excluded |
|---|---|---|---|---|---|---|
| `PROVEN_EXCLUDED` | Lizardman, family 0 | R1-S1 field family; absent from R1-S2 schedule/marker roster | `usage:lizardman:bank0x36` | base `$004B`, bank `$36` | 1–12 | Cannot enter R1-S2 across the subround ownership transition. |
| `PROVEN_EXCLUDED` | Flying Demon, family 8/9 component | R1-S1 field family; absent from R1-S2 schedule/marker roster | `usage:flying_demon:bank0x35` | base `$0129+$0275`, bank `$35` | 1–8, 10–15 | No legal R1-S2 spawn/lifetime. |
| `PROVEN_EXCLUDED` | Four-Armed Insect, family 3 | R1-S1 field family; absent from R1-S2 schedule/marker roster | `usage:four_armed_insect:bank0x3A` | base `$02E8`, bank `$3A` | 1–4, 7, 9, 10, 12–14 | No legal R1-S2 spawn/lifetime. |
| `PROVEN_EXCLUDED` | Round-1 boss body, record type `$0E` | R1-S3 record 22 only | `object:boss.r1.body` | base `$061D`, bank `$4F` | 1–15 | Cannot coexist with the R1-S2 records 17–19 envelope. |
| `PROVEN_EXCLUDED` | Boss flying daggers, record type `$0F` | Created only by the R1-S3 boss | `object:boss.r1.flying_daggers` | program `$47E54`, bank `$4F` | 3–6, 8, 10, 11, 13 | Cannot survive backward through a subround boundary. |
| `PROVEN_EXCLUDED` | Gameplay reward kind 01 | Could follow an R1-S2 death, but its authored object mapping is not a Build-0573 production consumer | `object:item.reward.kind01` | base `$0A5A`, selector `$13` | authored 8, 9, 13, 14 | Native death records 26/27 carry embedded Line 0. |
| `PROVEN_EXCLUDED` | Gameplay reward kind 11 | Same production distinction | `object:item.reward.kind11` | base `$0A5A`, selector `$1D` / code `$0A65` | authored 1, 9, 11, 12, 14 | Native death records 46/47 carry embedded Line 0. |

The generated Build-0573 sprite manifest consumes the three `usage:*` mappings above, not the two reward `object:*` mappings. `pc090oj_hooks.s:1211-1245` defines the native death/reward record domain, and the generated death-frame index proves kinds 01 and 11 emit Line 0. This avoids falsely counting editor-authored, production-unconsumed decisions as live Line-1 pixels.

## 6. Unresolved consumers

None for the Line-1 capacity question. Broader PC090OJ completion and rope-climber authoring are separate work and do not create an unknown Line-1 consumer in this envelope.

## 7. Actual sprite pixel-index demand

Because the possible-consumer set is empty, the union of Line-1 indexes referenced by legal visible sprite pixels is exactly `{}`. The table above reports actual generated mapping-index unions for every excluded authored consumer; those unions are not charged to R1-S2 simply because their colors happen to reside in the scene's fixed Line 1.

The worst legal simultaneous Line-1 sprite color set is therefore also `{}`. This conclusion uses schedule, marker, subround, native death-record, and production-manifest proof—not a single observed frame.

## 8. Writer classification by Line-1 index

| Line-1 index | Build-0573 value | Classification during fire visibility | Proof |
|---:|---:|---|---|
| 0 | backdrop/transparent | `USED_STATIC` | Reserved transparent/backdrop entry; never leased. |
| 1 | `08CC` | `UNUSED_STABLE` | No legal visible consumer; same authored asset; retained writers gated. |
| 2 | `0242` | `UNUSED_STABLE` | Same. |
| 3 | `0486` | `UNUSED_STABLE` | Same. |
| 4 | `0064` | `UNUSED_STABLE` | Same. |
| 5 | `04A6` | `UNUSED_STABLE` | Same. |
| 6 | `04A0` | `UNUSED_STABLE` | Same. |
| 7 | `0662` | `UNUSED_STABLE` | Same. |
| 8 | `0CCA` | `UNUSED_STABLE` | Same. |
| 9 | `0CCC` | `UNUSED_STABLE` | Same. |
| 10 | `0028` | `UNUSED_STABLE` | Same. |
| 11 | `024C` | `UNUSED_STABLE` | Same. |
| 12 | `0422` | `UNUSED_STABLE` | Same. |
| 13 | `0AA6` | `UNUSED_STABLE` | Same. |
| 14 | `0640` | `UNUSED_STABLE` | Same. |
| 15 | `0AC4` | `UNUSED_STABLE` | Same. |

`vdp_install_test_lines` installs the complete fixed authored Lines 0/1/3 when gameplay palette ownership is acquired (`vdp_comm.s:444-492`). Its refresh path changes them only when the finite authored asset changes (`vdp_comm.s:498-524`), which records 17–19 do not do. While that owner is active, retained `$059AD4`, `$045DAE`, and `$03BA64` paths are gated away from Lines 0/1/3 (`palette_hooks.s:257-270`, `399-406`, `509-520`). Thus no Line-1 index is `USED_DYNAMIC`, `UNUSED_DYNAMIC`, or `UNKNOWN` during the envelope.

## 9. Exact overlap and worst legal set

- Required host Line-1 sprite colors: `{}`.
- Required host Line-1 sprite indexes: `{}`.
- Fire colors: `{006E,008E,00AE,00CE,00EE,08EE,0AEE,0CEE,0EEE}`.
- Exact value overlap: `{}`; count `0`.
- Lossless union size: `9`.
- Capacity: `15` nontransparent slots.
- Over capacity: `0`; artistic merges required: `0`.

## 10. Free-slot lease result

Result: **`LOSSLESS_FREE_SLOT_LEASE`**.

All indices `1..15` are proven `UNUSED_STABLE`; nine are needed. One deterministic assignment is:

| Index | Fire color |
|---:|---:|
| 1 | `006E` |
| 2 | `008E` |
| 3 | `00AE` |
| 4 | `00CE` |
| 5 | `00EE` |
| 6 | `08EE` |
| 7 | `0AEE` |
| 8 | `0CEE` |
| 9 | `0EEE` |

Indices 10–15 remain spare. No existing sprite index mapping moves. The word "lease" is essential: existing fixed Line-1 contents must be restored before any later Line-1 consumer becomes present.

## 11. Independent regional-composite result

Result: **`LOSSLESS_REGIONAL_COMPOSITE`** / `LOSSLESS_REGIONAL_COMPOSITE_POSSIBLE`.

The exact composite set is the same nine fire colors because the legal host-sprite set is empty. The allocation above is deterministic. No PC090OJ sprite usage requires a regional variant. Only PC080SN usages `LA-0479..LA-0494` require offline regional reindexing.

The existing PC080SN per-context compiler can emit these final indexed tiles offline; runtime pixel conversion is unnecessary. PC090OJ `(code,bank)` dedup/variant machinery is capable of regional sprite variants but is not needed here. At most 16 distinct 8×8 fire patterns × 32 bytes = **512 bytes** of generated pattern data before normal deduplication. CRAM/residency control cost is not estimated because this prompt does not design or implement it.

## 12. Build-0573 behavior preservation

| Behavior | Line-1 impact |
|---|---|
| Rastan | Line 0; outside blast radius. |
| Sword/axe/hammer/fire sword | Line 0 with Rastan; outside blast radius. |
| R1-S2 Green Sword Knight and rope climber | Not Line 1; unchanged. |
| Other enemies | The only authored Line-1 enemy families are proven absent during the envelope. |
| Traps, falling water, moving gate, spikes | Plane/tile or non-Line-1 paths; unchanged. |
| Pickups/effects | Current native reward records use Line 0 or Line 3, including kinds 01 and 11; unchanged. |
| HUD/sprite consumers | Not a fire-envelope Line-1 consumer; unchanged. |
| Death presentation | May own other presentation state only while gameplay/fire is not visible. |
| READY | Occurs outside gameplay/fire presentation. |
| Respawn | Gameplay ownership must reinstall the exact Build-0573 state before visibility, then evaluate the lease. |
| Current R1-S2 Line-1 animation | None exists; no animation is displaced. |

This is a capacity proof, not permission to leave Line 1 altered outside the proven envelope.

## 13. Runtime-writer compatibility

- **Scene installer:** writes the entire fixed authored Line 1. A future implementation must apply the lease after/with this ownership acquisition, not fight it.
- **Same-stage record movement:** no authored-asset refresh, so there is no hidden full-line overwrite in records 17–19.
- **Retained palette loaders/cyclers:** existing ownership gates permit only Line 2 while Test 2.0 gameplay ownership is active; compatible without runtime translation.
- **Death/READY/intermission owners:** may replace Line 1 only when fire gameplay is not presented. They remain untouched.
- **Resume/respawn:** the exact fixed authored line must be restored first, then the regional fire state installed if the proven envelope is active.
- **Arbitrary write interception:** not required and not recommended. A solution requiring runtime color translation would violate this proof's architecture.

## 14. Death and respawn implications

An R1-S2 enemy/reward may exist immediately before death, but none is a Line-1 consumer. The retained record can remain 18 on same-stage respawn, so fire may be visible as soon as gameplay returns. The later residency mechanism must re-evaluate retained camera/record state and publish the correct initial/current fire phase before display; on leaving the envelope it must restore exact Build-0573 Line 1. This report does not redesign respawn.

## 15. Analyzer integration and deterministic verification

The generic 0149 analyzer was narrowly extended to emit a `line1_question` section and classify Line 1 through the existing result vocabulary. It validates the current Test 2.0 authored Line-1 mapping set, generated production sprite manifest, R1-S2 roster evidence, native death/reward line attributes, writer safety, both capacity tests, deterministic allocation, and source hashes. Tests were extended rather than creating a disconnected helper.

One genuine documentation bug was corrected: stale text said ten fire colors while the already-computed arrays/counts correctly contained nine.

Verification:

- `python3 -m py_compile tools/graphics_editor/analyze_palette_residency.py tools/graphics_editor/test_analyze_palette_residency.py` — PASS.
- `python3 -m unittest tools.graphics_editor.test_analyze_palette_residency` — PASS, 13 tests. Existing `server.py` unclosed-file `ResourceWarning`s remain non-failing and were not changed.
- Analyzer execution — `PALETTE_RESIDENCY_OK`.

Generated evidence:

- `build/analysis/palette_residency/r1s2_firepit_line1_capacity.json`
- SHA-256: `676f9af42c8336a252ed9a29a249fc4276cbcba8e72fee21a54e7da1dec0d885`
- Analyzer SHA-256: `1911588ccfcfbdb3418fa87c443ac8b81bf4e7c749293de932f7820a2fdfc1fd`
- Test SHA-256: `33be712dec1cd6e960381e60167643e5e3736684327902b9377cef8085cdd8d0`

No new trace or diagnostic ROM was necessary.

## 16. Recommendation and explicit non-changes

Recommend **Genesis Line 1 as the candidate host for a later Palette Residency implementation**, using the free-slot lease as the smaller solution. The next task should design the exact camera-envelope activation/release and death/respawn restoration contract at the existing authored-scene ownership boundary, then generate the fire's offline PC080SN reindex. It must retain Build 0573 as the comparison baseline and must not reinterpret this capacity proof as an implemented feature.

1. Production source changed: **NONE**.
2. Test 2.0 changed: **NONE**.
3. Palette registry changed: **NONE**.
4. Current authored mappings changed: **NONE**.
5. Production generated graphics changed: **NONE**.
6. ROM produced: **NONE**.
7. Production build number consumed: **NONE**; counter remains `573`.
8. Push: **NONE**.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0151
