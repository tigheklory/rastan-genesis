# Cody - Selector-0 PC080SN Tail Retirement Audit

**Agent:** Cody  
**Date:** 2026-07-28  
**Type:** Analysis / verification only  
**Build context:** rastan-direct, accepted Build 0235; counter 240  
**Scope:** Selector-0 Plane A / PC080SN chip-tail retirement audit only. No source/spec/tool/Makefile/ROM changes. No build. No runtime trace.

Address labels: `arcade_pc` = original arcade code PC; `runtime_genesis_pc` = Genesis runtime PC from `build/rastan-direct/address_map.json`; `arcade_data` = original arcade data address; `Genesis-WRAM` = Genesis work RAM. All code mappings below are JSON-derived; no arithmetic PC relocation is used as authority.

---

## Phase 0 - Baseline Statement

**Relevant priors:** KF-010 (BG/FG to Genesis plane mapping; FG/tilemap1 -> Plane A), KF-011 (arcade VBlank owns progression), KF-068 native video surface / native replacement direction, KF-071/KF-072 (Build 0226/0227 native plane baseline and rejected ring-buffer direction), KF-073 (Stage 1 progression/collision map hazard context).

**Rediscovery-Hazard HIGH touched:** KF-011, KF-068, KF-071, KF-072, KF-073. The audit respects the current policy: retain arcade semantic decisions, cut before chip-specific PC080SN execution, and do not revive rejected chip-projection architecture as final design.

**Deferred-appendix entries relevant:** none identified for this narrow selector-0 audit.

**Task classification:** EXTENDING (native PC080SN replacement / OPEN-001, OPEN-017 context).

**Open/Closed issues touched:** OPEN-001 and OPEN-017 as graphics/gameplay-video context; OPEN-024 as gameplay hardware context. No closed issue is contradicted or reopened.

**Contradiction of CONFIRMED/STRONG finding detected:** NONE.

**Architecture compliance:** CONFIRMED. This audit preserves arcade-owned state progression and proposes only a future native helper at a chip-tail boundary. No production change is made.

---

## Files And Evidence Inspected

- `RULES.md`
- `ARCHITECTURE.md`
- `PROMPT_TEMPLATE.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
- `docs/design/Andy_plane_a_semantic_cut_contract.md`
- `docs/design/Andy_plane_a_selector0_logical_coordinate_proof.md`
- `docs/arcade_reference/pc080sn/state_fields.md`
- `docs/arcade_reference/pc080sn/core_publishers_assembly.md`
- `docs/arcade_reference/pc080sn/scene_initialization_assembly.md`
- `docs/arcade_reference/pc080sn/gameplay_control_assembly.md`
- `docs/arcade_reference/pc080sn/access_inventory.md`
- `build/maincpu.disasm.txt`
- `build/rastan-direct/address_map.json`
- `apps/rastan-direct/src/tilemap_hooks.s` (comparison only; no edits)
- `apps/rastan-direct/src/vdp_comm.s` (comparison only; no edits)
- latest relevant `AGENTS_LOG.md` entries

---

## JSON-Derived Address Map

| arcade_pc | runtime_genesis_pc | Note |
|---:|---:|---|
| `0x0503DC` | `0x0505DC` | Scene-fill owner entry |
| `0x0503EC` | `0x0505EC` | Selector-fill `a5+0x10A0` seed, patched site |
| `0x050434` | `0x050634` | Scene-fill Plane A publication call |
| `0x050444` | `0x050644` | Scene-fill `a5+0x10A0` back-step, patched site |
| `0x05581E` | `0x055A1E` | Gameplay `a5+0x10A0` materialization |
| `0x055822` | `0x055A22` | Gameplay selector publish call |
| `0x0558A2` | `0x055AA2` | Ring progression helper |
| `0x055904` | `0x055B04` | Descriptor rebuild helper, patched site |
| `0x055948` | `0x055B48` | Plane A selector dispatcher |
| `0x055950` | `0x055B50` | Selector-0 branch call to chip tail |
| `0x055954` | `0x055B54` | Selector-0 return continuation, `10CA++` |
| `0x055962` | `0x055B62` | Post-publication ring helper call |
| `0x055968` | `0x055B68` | Selector-0 column driver, patched site |
| `0x055982` | `0x055B82` | Selector-0 `a5+0x10A0` save, patched site |
| `0x0559B2` | `0x055BB2` | Selector-0 cell producer |
| `0x0559EC` | `0x055BEC` | Collision cell write inside cell producer |
| `0x055A12` | `0x055C12` | Selector-0 cell loop tail |
| `0x055E54` | `0x056054` | Separate tilemap0/state-gated `a5+0x10A0` seed |
| `0x0560DA` | `0x0562DA` | Separate tilemap0/state-gated `a5+0x10A0` read |
| `0x0560EA` | `0x0562EA` | Separate tilemap0/state-gated `a5+0x10A0` read |
| `0x05610E` | `0x05630E` | Separate tilemap0/state-gated `a5+0x10A0` save |

---

## `a5+0x10A0` Consumer Audit

`a5+0x10A0` is absolute arcade work-RAM address `0x10D0A0`. In the selector-0 Plane A path it holds a PC080SN-shaped destination cursor, not a semantic gameplay coordinate.

| Site | Access | Path | Classification |
|---:|---|---|---|
| `arcade_pc 0x0503EC` | write `#0x00C08000` to `a5+0x10A0` | Scene-fill setup | PC080SN-only destination seed for Plane A selector-0 fill. |
| `arcade_pc 0x050416` | write `#0x00C08000` to `a5+0x10A0` | Scene-fill selector-1 setup | PC080SN-only destination seed, but selector-1 is out of this audit. |
| `arcade_pc 0x050444` | subtract `#0x3FFC` from `a5+0x10A0` | Scene-fill loop | PC080SN-only cursor back-step for the old chip tail. |
| `arcade_pc 0x05581E` | write `0x00C08000 + ((10CC << 4) + (10CA << 2))` | Gameplay horizontal strip trigger | PC080SN-only materialized destination. The semantic inputs are `10CA`, `10CC`, direction/tile-cross state, and descriptor/source tables. |
| `arcade_pc 0x055968` | read `a5+0x10A0` into `a0` | Selector-0 column driver | PC080SN-only read. Native selector-0 must not consume it. |
| `arcade_pc 0x055982` | write updated `a0` back to `a5+0x10A0` | Selector-0 column driver | PC080SN-only cursor save. Native selector-0 must not preserve this as an output dependency. |
| `arcade_pc 0x055E54` | write `#0x00C00400` to `a5+0x10A0` | Separate state-gated tilemap0 family | PC080SN-only but outside selector-0 Plane A tail retirement. Prevents global deletion from being claimed here. |
| `arcade_pc 0x0560DA` | read `a5+0x10A0` | Separate state-gated tilemap0 family | Outside selector-0 Plane A tail retirement. |
| `arcade_pc 0x0560EA` | read `a5+0x10A0` | Separate state-gated tilemap0 family | Outside selector-0 Plane A tail retirement. |
| `arcade_pc 0x05610E` | write updated `a0` to `a5+0x10A0` | Separate state-gated tilemap0 family | Outside selector-0 Plane A tail retirement. |

**Result:** `a5+0x10A0` has no retained semantic consumer inside the selector-0 Plane A publication tail. It is fully retireable for selector-0 native Plane A publication. It is **not** globally deleteable from all arcade work-RAM semantics in this audit because separate tilemap0/state-gated users remain outside scope.

---

## Selector-0 Current Arcade Tail

The dispatcher at `arcade_pc 0x055948` selects the Plane A publishing tail:

```asm
055948  cmpi.w #0,(4264,a5)      ; selector a5+0x10A8
05594e  bne    0x05595a          ; non-selector-0 path out of this audit
055950  bsr    0x055968          ; selector-0 column driver
055954  addq.w #1,(4298,a5)      ; a5+0x10CA progression remains arcade-owned
055958  bra    0x055962
055962  bsr    0x0558a2          ; ring/descriptor progression remains arcade-owned
055966  rts
```

The selector-0 driver at `arcade_pc 0x055968` reads `a5+0x10A0` as `a0`, then walks 16 segment descriptors from `0x10D040` and 16 source words from `0x10D080`. It calls `arcade_pc 0x0559B2` for each segment and stores the resulting advanced PC080SN cursor back to `a5+0x10A0`.

The cell producer at `arcade_pc 0x0559B2` emits four cells per segment. It writes PC080SN tilemap words through `a0`, writes collision cells through the `0x10DE00` collision map, and uses `a0 - 0xC08000` to derive the old PC080SN destination index.

---

## Retained Semantic Effects

A future native selector-0 replacement must preserve these arcade-owned effects:

- The selector decision at `a5+0x10A8 == 0`.
- Scene-fill/gameplay caller timing and call count.
- The 16 segment loop and four cells per segment.
- Source descriptor pointer reads from `0x10D040`.
- Source word reads from `0x10D080`.
- Tile/cell selection from the source block chosen by the descriptor.
- Collision publication into the `0x10DE00` collision map.
- `10CA` and `10CC` progression, which remain owned by the original dispatcher and `0x0558A2` path after return.
- Any descriptor rebuild or ring maintenance in `0x0558A2` / `0x055904` reached after the selector-0 tail returns.

Andy’s selector-0 logical-coordinate proof established the replacement collision coordinate without PC080SN destination arithmetic:

```text
logical_column = ((a5+0x10CC) * 4 + (a5+0x10CA)) & 63
logical_row    = segment * 4 + cell
collision_addr = 0x10DE00 + ((logical_row * 64 + logical_column) * 2)
```

That proof removes the former dependency on `a0 - 0xC08000` for selector-0 collision placement.

---

## Removed PC080SN-Specific Tail

For selector-0 only, the following are chip-specific tail behavior and need not survive in the final native implementation:

- Materializing a destination as `0x00C08000 + ring_offset` at `arcade_pc 0x05581E`.
- Reading `a5+0x10A0` into `a0` at `arcade_pc 0x055968`.
- Writing PC080SN C-window tilemap words through `a0` at `arcade_pc 0x0559B4` and `0x055A02`.
- Deriving collision coordinates from `a0 - 0xC08000` inside `arcade_pc 0x0559B2`.
- Advancing `a0` by PC080SN C-window row stride.
- Saving the advanced PC080SN cursor back to `a5+0x10A0` at `arcade_pc 0x055982`.
- Scene-fill `a5+0x10A0` seed/back-step bookkeeping as an input to selector-0 Plane A output.

Leaving old `a5+0x10A0` writes temporarily in unconverted callers is harmless only if the native selector-0 path does not read them and no transitional projector is allowed to overwrite native Plane A output.

---

## Native Invocation And Return Contract

**Semantic cut retained:** The original arcade dispatcher chooses selector-0 at `arcade_pc 0x055948`, after the caller has established the current `10CA/10CC`, descriptor tables, source-word tables, scroll/camera state, and scene-fill/gameplay timing.

**Native invocation point:** `arcade_pc 0x055950` (`runtime_genesis_pc 0x055B50`), the selector-0 arm’s `bsr 0x055968` instruction.

**Native return point:** `arcade_pc 0x055954` (`runtime_genesis_pc 0x055B54`), so the original `addq.w #1,(a5+0x10CA)`, `0x0558A2` progression helper, and caller return flow remain arcade-owned.

**Bypassed selector-0 arcade tail:** `arcade_pc 0x055968..0x05598E` plus the repeated selector-0 calls into `arcade_pc 0x0559B2..0x055A12`.

**Selector-1/2 isolation:** The nonzero-selector branch at `arcade_pc 0x05594E -> 0x05595A` remains unchanged by a replacement scoped to `arcade_pc 0x055950`.

---

## Scene-Fill And Gameplay Bookkeeping Disposition

**Scene-fill:** The 64-iteration scene-fill schedule and its Plane A publication calls remain semantic. The `a5+0x10A0` C-window seed/back-step is only old PC080SN destination bookkeeping for selector-0 Plane A output and should not feed the native helper. It can remain temporarily as inert compatibility state, but the final selector-0 native output must not depend on it.

**Gameplay:** The horizontal tile-cross/ring logic before `arcade_pc 0x05581E` remains semantic. The materialized `0xC08000` cursor written at `0x05581E` is not semantic for native selector-0. Native placement should use `10CA/10CC` and segment/cell logical coordinates instead.

**Current transitional source comparison:** Current `genesistan_stage_fg_src_column` still consumes `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` / `a5+0x10A0` and derives placement from C-window geometry. That is transitional compatibility, not the final architecture required by Rule 11.

---

## Register And Condition-Code Contract

The original selector-0 tail uses `d0-d2`, `d7`, `a0-a3`, and `fp/a6` internally. Build 0240 evidence showed that helper register clobbering is a real hazard. A future native helper should therefore preserve all caller-visible data and address registers unless the replacement contract proves a narrower original clobber set safe.

The return continuation at `arcade_pc 0x055954` immediately executes `addq.w #1,(a5+0x10CA)`, which sets CCR before the following branch and before `0x0558A2` begins with its own comparison. Therefore no incoming CCR value from the replaced tail is live at the post-return decision point. Still, preserving CCR/SR where practical is safer and simpler to audit.

---

## Transitional Compatibility And Removal Boundary

No transitional compatibility structure is required by the final selector-0 native contract. The final helper should consume original arcade semantic/source state, not PC080SN-shaped destination state.

Transitional structures currently present in production source include:

- `genesistan_stage_fg_src_column`, which consumes PC080SN-shaped destination state.
- Tall-buffer / projector ownership gates in `vdp_comm.s` used by prior native experiments.

These must be isolated from selector-0 native output and assigned a future removal boundary. They should not be used as proof of final architecture compliance.

---

## Verdict

**0x10A0 semantic consumers:** None inside selector-0 Plane A publication. Separate tilemap0/state-gated users exist outside this audit.

**0x10A0 fully retireable for selector-0:** YES.

**Complete selector-0 PC080SN tail retireable:** YES, if the replacement is scoped to the selector-0 arm and preserves the semantic source walk, collision publication, and return to `0x055954`.

**Implementation ready:** YES for selector-0 tail retirement at `arcade_pc 0x055950` / `runtime_genesis_pc 0x055B50`. NO for global deletion of `a5+0x10A0` or selector-1/2 retirement.

**Remaining blockers:** none for selector-0 tail retirement. Out-of-scope work remains for selector-1/2, global `a5+0x10A0` retirement, final VRAM residency/asset loading, and removal of transitional projection helpers.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-017, OPEN-024 as graphics/gameplay hardware context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: selector-1/2 rows, Plane B, PC090OJ, palettes, graphics ROM conversion, Genesis VRAM asset loading, production implementation.

---

## KNOWN_FINDINGS Impact

**Option A - No new finding to index.** This audit extends KF-068/KF-072 and records a narrow selector-0 implementation boundary. It does not add a new whole-system behavior finding until a production implementation and validation run confirm the replacement in ROM.

---

## STOP Status

STOP triggered: NO.
