# Cody — Enemy Death / Drop Semantic Validation and Build-0428 Mapping

| Category | Observed effect | Arcade owner | Death entry | Effect creation | State | Base | Selectors | Compositor | Bank | Piece counts | Item/drop relationship | Current Build-0428 Genesis route | Proof status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A — Small/Large Bat pop | Tiny, brief pop | The bat actor itself (`rec_type` 10 large, 11 small) | Collision manager `0x449B4` → damage accumulator `0x44804` → `0x448B2`; `0x447F0` is not required by this fatal route | In-place actor state change; no child allocation | `0x0F`, specialized handler `0x42ABC` | `0x0275` | `0xA8`, then retire on the next gated update | 0 | effective bank `0x3E` | 1 displayed piece in the captured bat-death route; original producer ceiling 6 | Bat schedule `+0x36` is zero, so no retained reward | Compact Level-B rejects selector `0xA8`; universal-general generated index → native queue/SAT | PROVEN |
| B — common enemy death | Heavy multipart death used by Lizardman, Valkyrie, Four-Armed Insect, Chimera | The dying enemy actor itself | `0x449B4` → `0x44804` (thresholded damage) or qualifying direct hit reaction → `0x448B2` | In-place transformation; no `0x0275` child is allocated | `0x0F`, default `0x40CCC` branch (`+0x03==0`, `+0x39==0`) | `0x0A73` | `0x0D,0x0C,0x0B,0x0C,0x0D,0x0E,0x0F,0x10,0x11,0x12`; one phase every 3 updates | 2 | `0x40CCC` clears `+0x27` bit 6, so every piece uses embedded line 0; effective bank is the active lane high bits + 0 (R1/P1: `0x30`) | `9,4,4,4,9,9,8,9,4,1` in selector order | At phase 10, `+0x36==0` recycles; nonzero `+0x36` converts the same actor to D | Universal-general generated index → native semantic queue → existing residency/DMA/SAT publication | PROVEN |
| S — special child burst | Expanding four-frame impact/burst | Up to five independent records in A5+`0x03C8..0x04C8`, activated by state-`0x1B` controller `0x43ECC` through `0x43F4E/0x43F52` | `0x447F0` sets component flag `+0x39`, then `0x448B2` enters state `0x0F` | Activates existing pool records; the controller is not the displayed burst and no common-death actor is converted | `0x0F`, `0x40CCC` branch `+0x03==0,+0x39!=0` | `0x0275` | `0x9D,0x9E,0x9F,0xA0`, one phase per update; retire at phase 4 | 0 | `0x30` | `6,8,9,10` | None; each transient record self-retires through `0x4092E` | `0x9E–0xA0` are exact compact Level-B records; `0x9D` uses universal-general closure → queue/SAT | PROVEN |
| C1 — Flying Demon fountain | Large paired death/spray | Hittable A5+`0x0548` member plus fixed A5+`0x0508` partner | Lethal `0x44804`; `rec_type` 8/9 branch `0x44896` also calls `0x448B2` on A5+`0x0508` | Two existing fixed-pool actors enter death; no fountain child allocator | `0x0F`; fixed-pool dispatcher `0x42102` table `0x4213A[state 15]` → `0x42ABC` on both | `0x0275` | `0x9D,0x9E,0x9F,0xA0`, four updates per phase | 0 | retained Demon override/effective bank `0x35` | 6/8/9/10 per actor; simultaneous totals 12/16/18/20 | Each actor self-retires through `0x4092E`; this route does not enter the ordinary `+0x36` reward conversion | Universal-general generated index (compact burst requires embedded bank `0x30`); Build-0386 operand at runtime `0x44A98` preserves partner transition | PROVEN |
| C2 — representative boss (Round 5) | Boss defeat burst/fountain | Five structural segments plus primary A5+`0x0708` (`rec_type` 16) | `0x469E8` waits for five segments inactive, then `0x447F0` → `0x448B2` on primary | Existing primary is activated; no new fountain actor | `0x0F`, specialized death handler `0x42ABC` | `0x0275` | `0x9D,0x9E,0x9F,0xA0` | 0 | retained boss override selects effective bank `0x3F` in Round 5 | `6,8,9,10` | Score awarded at `0x46AAC`; not the ordinary schedule-drop completion | Burst compact Level-B requires embedded attr/bank `0x30`, so boss override rejects it; universal-general → native queue/SAT | PROVEN for Round-5 representative; “blood fountain” is not one universal code path |
| D — enemy-death reward/drop | Item/reward left after eligible ordinary death | Same dying actor, transformed in place | Completion of B at `0x40D32` | No allocator: family becomes 12; `0x40C0E` maps schedule byte `+0x36` | family 12 presentation/collection | `0x0A5A` | `(+0x36-1)+0x13`, range `0x13–0x23` | retained compositor 2 | override remains clear: kinds 1–13 use embedded line 0; kinds 14–17 use embedded line 3; effective bank adds the active lane high bits (R1/P1: `0x30` or `0x33`) | 1 for every selector `0x13–0x23` | `+0x36` is deterministic eligibility/identity; `0x448D8` awards `+0x2C` and recycles on collection; otherwise it persists until generation/bounds rejection | Universal-general generated index → native queue/SAT; gameplay semantics remain translated | PROVEN; separate from timed-weapon event records |

## Andy Claim-by-Claim Validation

- **Bat rec_type-7 speculation — REJECTED.** The large and small bats are `rec_type` 10 and 11. Their templates are bases `0x03F6` and `0x0268`; both have damage threshold `+0x3A=1`. Their fatal damage path calls `0x448B2`, reaches state `0x0F`, and the specialized handler `0x42ABC` gives types 10/11 the short base-`0x0275`, selector-`0xA8`, compositor-0 pop. Its deliberate second phase increment retires the same actor on the next gated update. No effect child is allocated.
- **`0x0275`, selectors `0x9E–0xA0`, is the common ordinary-enemy explosion — REJECTED.** That exact 8/9/10-piece program is selected by the `+0x39!=0` child branch at `0x40DD8`, and by some specialized/boss types at `0x42ABC`. Ordinary Lizardman/Valkyrie/Four-Armed/Chimera deaths have clear `+0x03/+0x39` and take `0x40CCC`'s `0x0A73` default branch.
- **Common deaths use state `0x0F` — CONFIRMED WITH THE POLYMORPHIC QUALIFIER.** State alone is insufficient. The discriminators are `+0x03==0` and `+0x39==0`; the selector table is `0x40DCE`.
- **Special child burst identity — CONFIRMED AND NARROWED.** State-`0x1B` controller `0x43ECC` activates up to five existing pool records through `0x43F4E/0x43F52`; each gets `+0x39=1`, enters state `0x0F`, uses the `0x40DD8` branch, displays the bank-`0x30` `0x9D/0x9E/0x9F/0xA0` 6/8/9/10-piece expansion, and retires independently. Earlier H16 evidence omitted the first `0x9D` phase; `0x448B2` initializes `+0x08=0xFF`, so the first increment selects `0x9D`. This is not the ordinary enemy-death owner.
- **Flying Demon/boss fountain was unresolved — CORRECTED.** Flying Demon death is a paired, simultaneous specialized `0x0275/9D–A0` death. The decisive dispatch is fixed-pool `0x42102` → state table `0x4213A[15]` → `0x42ABC`; the older Build-0386 prose that named `0x40CCC/0x0A73` for the fixed pair is superseded by this exact table decode. The Round-5 boss representative also uses an existing primary and `0x42ABC`, but retains its own palette owner. The appearance is shared; actor ownership and palette context are not.
- **Enemy-death drops are absent — REJECTED.** No child allocator exists because none is needed. At ordinary-death completion the dying actor itself becomes family 12. Schedule entry byte 3, installed at actor `+0x36` by `0x4A086`, is the deterministic eligibility/selection value. `0x40C0E` maps it through `0x40C2E` (identity) and `0x40C40` (reward value), then `0x40D64–0x40DC8` either presents base `0x0A5A` or recycles it.
- **Visible reward is merely unrelated marker placement — REJECTED.** Fixed/map-placed pickups remain a distinct mechanism, but the ordinary-death completion chain itself conditionally preserves the same actor as the visible family-12/base-`0x0A5A` reward.
- **Timed rec_type-12 event path equals the enemy-death reward — REJECTED / KEPT SEPARATE.** `0x4495A` maps a `rec_type`-12 pickup to A5+`0x12C8` event types 1/2/3. The newly proven enemy-death reward becomes **family** 12 (`+0x3E`), not `rec_type` 12 (`+0x06`). It is therefore incorrect to use the absence of a rec_type-12 allocator to deny the family-12 death reward; it is also incorrect to claim from this analysis that every death reward is a timed weapon.
- **Current Genesis fallback/unconverted presentation assumption — CORRECTED.** Build 0428 has no runtime arcade mapping-program fallback for these effects: the exact generated Level-B or universal-general route emits native semantic queue entries and the shared finalizer publishes Genesis SAT.

## Newly Decompiled Arcade Functions

### `0x44804` — enemy damage accumulator / lethal transition

Prior status and reports mislabeled it as a death-animation completion stepper. The complete reconstruction is now `analysis/decompilation/c/raw/00044804.c`.

- Callers: the three-pass player/actor collision manager `0x449B4` at `0x44B14` and `0x44C26`.
- Callees: sound `0x3A0EC`, score `0x3B726`, death initializer `0x448B2`.
- Fields: damage accumulator `+0x3C`, threshold `+0x3A`, hit flash `+0x3D`, record type `+0x06`, score `+0x2C`, Y `+0x1A`.
- Semantics: damage is 1/2/3 from A5+`0x1310`; only threshold completion enters state `0x0F`. Types 8/9 additionally start the fixed paired body at A5+`0x0508` immediately.

### `0x40CCC` / `0x40C0E` — ordinary-death completion and reward conversion

The existing raw reconstruction was completed and corrected. It now includes the actual default-death identity, the deterministic reward tables, and the nonzero/zero `+0x36` split.

- Caller: main actor state dispatcher `0x40BAA` for state `0x0F`.
- Callees: candidate helper `0x40C62`, reward mapping `0x40C0E`, schedule-preserving recycle `0x40A1E`, hard retire `0x4092E` for the separate child branch.
- Tables: selector sequence `0x40DCE`; reward identity bytes `0x40C2E`; reward values `0x40C40`.
- Relevant fields: `+0x03`, `+0x39`, `+0x08/+0x09`, `+0x01`, `+0x1E`, `+0x38`, `+0x36`, `+0x29`, `+0x2C`, `+0x3E`, `+0x754`.

### `0x42ABC` — specialized record-type state-0x0F death handler

Static disassembly closes the bat and representative-boss identity:

- fixed-pool state dispatch `0x42102` uses signed table `0x4213A`; state `0x0F` resolves exactly to `0x42ABC`;
- Flying Demon types 8/9 take base `0x0275`, selectors `0x9D–0xA0`, four ticks per phase, then retire; lethal `0x44804/0x44896` starts both A5+`0x0548` and A5+`0x0508`;
- types 10–13 use base `0x0275`; the second phase increment makes a lethal-initialized type 10/11 bat display selector `0xA8` and retire on the next four-tick gate;
- general supported types including Round-5 primary type 16 use base `0x0275` and the visible selector sequence `0x9D/0x9E/0x9F/0xA0` (6/8/9/10 pieces), four ticks per phase, then retire at phase 4;
- retirement is `0x4092E`.

## Arcade → Genesis Address Translation

Genesis ROM offsets below equal the runtime PCs for these low-ROM sites. They were resolved from the current `address_map.json`, not by assuming `+0x200`.

| Semantic role | Arcade PC / function | Status | Runtime Genesis PC / ROM offset | Native replacement/hook | Evidence |
|---|---|---|---|---|---|
| main state-0F ordinary death/drop | `0x40CCC` `arcade_40ccc` | RETAINED | `0x40ECC` | presentation only is native later | address map; postpatch disassembly |
| reward identity/value mapper | `0x40C0E` | RETAINED | `0x40E0E` | none | address map; original/postpatch disassembly |
| schedule-preserving recycle | `0x40A1E` | RETAINED | `0x40C1E` | none | address map |
| hard actor retirement | `0x4092E` | RETAINED | `0x40B2E` | none | address map |
| specialized bat/boss death | `0x42ABC` | RETAINED | `0x42CBC` | presentation only is native later | address map; postpatch disassembly |
| fixed-pool state dispatcher/table | `0x42102` / `0x4213A` | RETAINED | `0x42302` / `0x4233A` | gameplay dispatch retained | address map; decoded signed table (`state 15 -> 0x42ABC`) |
| state-1B burst controller | `0x43ECC` | RETAINED | `0x440CC` | presentation only is native later | address map; H16 static chain |
| burst pool activation loop | `0x43F4E` / `0x43F52` | RETAINED | `0x4414E` / `0x44152` | none | address map; reconstructed C |
| direct hit reaction | `0x447CE` | RETAINED | `0x449CE` | none | address map |
| component activation | `0x447F0` | RETAINED | `0x449F0` | none | address map |
| damage/lethal transition | `0x44804` | RETAINED | `0x44A04` | none | address map; postpatch disassembly |
| Flying-Demon pair transition | `0x44896` | PARTIALLY_REPLACED | `0x44A96`; operand site `0x44A98` | Build-0386 opcode replacement rebases `0x10C508` to `0xFF0508` | spec; patch manifest; address map; postpatch disassembly |
| state-0F initializer | `0x448B2` | RETAINED | `0x44AB2` | none | address map |
| family-12 collection | `0x448D8` | RETAINED | `0x44AD8` | none | address map |
| pickup-event mapper (separate path) | `0x4495A` | RETAINED | `0x44B5A` | none | address map |
| collision manager | `0x449B4` | RETAINED | `0x44BB4` | native contact geometry is consumed where declared, gameplay decisions remain retained | address map; source |
| schedule `+0x36` installer | `0x4A086` | RETAINED | `0x4A286` | none | address map; postpatch disassembly |
| large/small bat creators | `0x45B4A` / `0x45B72` | RETAINED | `0x45D4A` / `0x45D72` | none | address map |
| Round-5/6 boss defeat gate | `0x469E8` / score `0x46AAC` | RETAINED | `0x46BE8` / `0x46CAC` | none | address map; postpatch disassembly |
| original gameplay sprite block producer | `0x41DAE` | FULLY_REPLACED | no active arcade body; replacement site `0x41FAE` | `genesistan_pc090oj_hook_target_41dae` `0x73824` | opcode-replace spec/manifest; symbol table |
| secondary gameplay frame boundary | `0x41F5E` | FULLY_REPLACED | replacement site `0x4215E` | `genesistan_pc090oj_hook_target_41f5e` `0x7384A` | spec/manifest; symbols |
| mode-2 gameplay producer | `0x45DFA` | FULLY_REPLACED | replacement site `0x45FFA` | `genesistan_pc090oj_hook_target_45dfa` `0x7385C` | spec/manifest; symbols |
| arcade compositor/mapping tail | `0x3C902` / `0x3D054` | DEAD/UNREACHABLE in normal gameplay presentation | mapped bytes `0x3CB02` / `0x3D254` exist but are not the active gameplay path | generated Level-B/universal paths | source comments; Build-0260/0406 closure; current hook source |

## Current Build-0428 Execution / Presentation Path

Gameplay state, damage, score, drop selection and animation selectors remain arcade-translated. The chip-specific PC090OJ expansion does not. At the replaced producer boundary:

`genesistan_pc090oj_hook_target_41dae (0x73824)` → `native_stage_dispatch_41dae (0x73D82)` or `native_stage_dispatch_45dfa (0x73F2C)` → exact compact Level-B lookup (`0x73FDA`) → exact universal-general/specialized lookup (`0x74132`) → `native_sprite_emit_fast (0x73D48)` → native semantic queues → `pc090oj_native_emit_pass (0x748EC)` → Genesis SAT.

- A (`0x0275/A8`), B (`0x0A73`) and D (`0x0A5A`) use the generated universal-general index because no compact Level-B record owns those exact keys.
- S's `0x0275/9E–A0`, state-`0x0F`, compositor-0, embedded-attribute keys match the six generated compact Level-B orientation records exactly (bank `0x30`, 8/9/10 pieces); its `0x9D` first frame uses universal-general. C1 retains Demon override/effective bank `0x35` and C2 retains boss override/effective bank `0x3F`, so the compact burst attr/bank predicate rejects both and universal-general owns their four-frame sequences. There is no live gameplay PC090OJ bus/device emulator and no runtime arcade mapping-program fallback.
- `effect_0x0275_burst` in the generated manifest is a graphics-key label, not proof that every `0x0275` display has the same gameplay owner.

No first Genesis semantic divergence was found in these mechanisms. The only known historical divergence in scope—the Flying-Demon paired-body absolute WRAM operand—was corrected at Build 0386 and remains present in 0428.

## Existing Reproducible Future Test Points

| Category | Existing point | Artifact | What it exercises |
|---|---|---|---|
| A | YES | `states/traces/build0234_bat_stale_20260723_161930/` (`arc_bat.txt`, `bat_capture.txt`, `verify0234.txt`) | Natural Small/Hurry-up bat kill, code `0x0276`, short visible pop and retirement |
| B | YES, capture corpus rather than a one-command benchmark | `analysis/graphics_optimizer/round1_phase1_corpus/flying_demon_trace/observations.csv` and the Lizardman/Four-Armed/Chimera contact sheets | Exact `0x0A73` state-0F frames and multipart output across representative ordinary main-pool actors (the directory name does not make these rows the fixed Demon pair) |
| S | Natural scripted location identified; no new fixture created | Round-1 Phase-2 marker `0x4D`; durable chain in `analysis/actor_decompilation/h16_burst_child_structure.json` | Up to five independent `+0x39` burst records and the `0x9D–0xA0` sequence |
| C — Flying Demon | Static repaired-link test point exists; old capture is not authoritative for fixed-pool presentation | `docs/design/Andy_build0386_flying_demon_decompilation_ownership_palette.md`, `0x4213A` state table, and Build-0386 operand site | A5+`0x0548` lethal path, repaired A5+`0x0508` partner transition, and exact fixed-pool state-15 handler |
| C — boss | NO convenient deterministic player-ready fixture identified | Static Round-5 component tables and `0x469E8` chain are durable evidence | Future hardware play should kill a representative boss under `_do` observation |
| D | NO dedicated fixture identified | Static schedule/reward tables and family-12 collection chain are durable evidence | Future play should kill an actor whose schedule byte 3 is nonzero, then collect the resulting reward |

No new trace, route, save state or benchmark framework was created in this task.

## Optimization Readiness

| Presentation | Build-time constant | Frame-level runtime | Genuine per-piece runtime | Generalized work potentially compilable offline |
|---|---|---|---|---|
| A bat pop | exact selector, compositor program, normal/mirror geometry, finalized pattern identity | actor active/base/selector/orientation, queue capacity | clipping, coordinate add, queue append | already generated; remaining gains require measurement |
| B common death | all selector programs and family/context pattern identities | arcade phase/selector and actor position/context | coordinate add, clipping, residency/append | exact death-family fast classification or a dedicated generated frame dispatch could remove generalized lookup, if measured worthwhile |
| C paired/boss | component membership and every exact frame program | which components are alive, selector phase, positions | each visible piece's position/clip/residency/append | component-level batching/pre-resolved frame records may be possible; gameplay linkage must stay retained |
| D reward | `+0x36` identity/value tables and exact frame programs | eligibility, bounds/generation check, movement, collection | visible piece emission | graphics representation is already generated; gameplay selection is genuinely dynamic and should not be replaced |

The largest plausible next target is B/C dense multipart death presentation because it can make several generated frames/components visible together. The safe semantic cut is:

`retained arcade damage/death/drop state` → `exact generated Genesis frame/component representation` → `only dynamic position/orientation/visibility work` → `existing residency worklist, semantic queue and SAT publication`.

That is an optimization hypothesis, not a measured cost conclusion. Piece count, lookup cost, residency installs, DMA and queue/SAT work must be measured during the actual effects before selecting an implementation.

The standard rope race remains the global performance/regression benchmark. A future death-only optimization is expected to have **little or no rope-race effect** because the rope race does not exercise this workload. The practical effect test is the normal `_do` hardware ROM while deliberately triggering A/B/C and observing black-bar magnitude and duration.

## Project-status impact

- Build 0428 remains the user-accepted baseline; no ROM was built.
- OPEN/CLOSED issue status: no issue file status change is justified by this analysis-only task. The report corrects the semantic record for future work.
- Known-findings impact: KF-074/KF-077/KF-089 remain supported (native semantic lanes/final SAT; no gameplay chip emulation). The newly closed death/drop semantics should be promoted in a later governance update if Tighe requests registry edits.
- Phase D: NO. Phase E: NO. Production source modified: NO.

## Final static closeout audit

The original analysis/decompilation/mapping requirements have no remaining
static TODO.  Categories A/B/S/C1/C2/D are closed above; every significant
arcade routine is classified against Build 0428 as retained, partially
replaced, fully replaced, or dead/unreachable.  The report explicitly grades
the disputed taxonomy claims and keeps family `+0x3E == 0x0C` separate from
`rec_type +0x06 == 12`.

Static validation at closeout:

- actor decompilation coverage guard: PASS (126 rows; 109 COMPLETE, 12 PARTIAL,
  5 STUB_ONLY; all 10 H5 handler PCs covered);
- fidelity guard: PASS (126 coverage rows, 72 historical-audit rows);
- game-wide coverage guard: PASS (334 functions / 40,392 bytes; 17.9% fully
  decompiled, 25.4% touched; unrelated undecompiled inventory remains visible);
- complete semantic + raw C-tree `gcc -std=c11 -fsyntax-only`: PASS.

No additional gameplay evidence is required to close the semantic taxonomy or
Build-0428 mapping.  Future visual/hardware acceptance of any later optimization
is a separate, Tighe-driven task.
