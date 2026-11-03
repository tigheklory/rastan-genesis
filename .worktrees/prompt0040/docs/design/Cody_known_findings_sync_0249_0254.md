# Cody KNOWN_FINDINGS Sync 0249–0254

## 1. Baseline

- Accepted build: Build 0254
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0254.bin`
- SHA-256: `53bf25f4f2a090864aaab3fad98ce1646b15226d218f5e907468e52212c0b7e4`
- Size: `1592224` bytes
- Counter: `254`
- Canonical gate: `GATE_PASS`
- Build produced by this synchronization: NO
- Counter changed by this synchronization: NO
- Source/spec/build/generated artifacts changed by this synchronization: NO

## 2. Build 0254 User Verification

User verification is accepted as PASS:

- BlastEm attract gameplay now starts.
- The former fatal at raw PC090OJ destinations `0x00D00298` / `0x00D002B0` no longer occurs.
- Frontend/title/story/high-score screens still render.
- Normal gameplay still renders Rastan, lizard men, bats, and the axe item.
- No new visual issue was observed.
- No scripted/demo character input was observed after attract gameplay began. This is recorded separately from the destination fix; no evidence attributes it to Build 0254.

## 3. Files Read

Policy and curated baseline:

- `RULES.md`
- `ARCHITECTURE.md`
- `PROMPT_TEMPLATE.md`
- `KNOWN_FINDINGS.md` in full, including the deferred appendix
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest relevant `AGENTS_LOG.md` entries for Builds 0249–0254

Required design evidence:

- `docs/design/Andy_build0249_shared_native_sprite_emitter_contract.md`
- `docs/design/Cody_build0251_rastan_player_body_visibility_fix.md`
- `docs/design/Cody_build0252_runtime_legacy_hotpath_retirement.md`
- `docs/design/Cody_build0253_dead_pc080sn_projector_retirement.md`
- `docs/design/Cody_build0254_attract_mode_legacy_reachability_audit.md`
- `docs/design/Cody_build0254_d00298_raw_pc090oj_writer_fix.md`

Supporting current-state evidence:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/boot/boot.s`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/address_map.json`
- `apps/rastan-direct/out/symbol.txt`

## 4. Architecture Classification

PC090OJ semantic cut:

- Retained above the cut: arcade actor/object initialization, actor state, traversal, mapping/piece expansion, lifecycle, position, visibility, priority, palette route, and mode selection.
- Current gameplay realization: converted producers call `native_sprite_emit`, queue final semantic pieces by priority lane, and `pc090oj_native_emit_pass` constructs the final Genesis SAT chain.
- Retired gameplay chip tail: using the PC090OJ object-table scanner/decoder as the final renderer for converted gameplay paths.
- Transitional compatibility retained: frontend/non-gameplay and unconverted raw producers may still write `pc090oj_object_ram` and use `pc090oj_legacy_emit_pass`. This compatibility is not final architecture and cannot be deleted until native frontend/unconverted-producer conversion is proven.

PC080SN semantic cut:

- Gameplay Plane A/B native producers and the BG/FG strip commits remain the output path.
- Build 0252 skipped the legacy tall projector calls in gameplay while preserving the active strip commits.
- Build 0253 removed only unreachable projector bodies and retained exported stubs plus still-referenced tall buffers/dirty/project-base globals.
- Frontend text/C-window/staging compatibility remains and was not converted by these builds.

Architecture compliance: CONFIRMED. No Genesis-owned loop, scheduler, new mirror, fallback renderer, state seed, bypass, or source change was introduced by this documentation task.

## 5. Findings Already Present And Left Unchanged

- KF-032 remains the general canonical rule for raw copied PC080SN/PC090OJ hardware writes. The Build 0254 family is a concrete new instance, so KF-032 itself was not rewritten.
- KF-068 remains the Ghidra-measured native video replacement design basis.
- KF-070 remains the residency/cache guardrail; Builds 0249–0254 do not contradict it.
- KF-071 remains the historical Build 0226 ring-pipeline record. Its ring guidance is already superseded by KF-072, so it was not expanded with later cleanup details.
- KF-073 remains the Stage 1 progression/collision finding and is unrelated to this documentation sync.

## 6. Findings Updated

### KF-069

KF-069 was changed from current gameplay ownership to a historically bounded Build 0221–0249 finding. It is marked `SUPERSEDED` for gameplay by KF-074 while retaining its still-current frontend compatibility object-store facts. A supersession note prevents future agents from reviving the object-table scan as the gameplay renderer or deleting frontend compatibility prematurely.

### KF-072

KF-072 now includes the Build 0252–0253 projector-retirement sequence:

- scene-1 VBlank skips legacy tall-projector calls;
- BG strip and FG narrow-strip commits remain active;
- old BG/FG projector bodies were unreachable and were removed;
- exported no-op stubs remain;
- tall buffers, dirty flags, and project-base globals remain because xrefs still exist;
- canonical coverage changed `0x184C9C -> 0x184BA0`, while opcode replacement count stayed `218`;
- Build 0253 user verification passed and Build 0254 retained the plane behavior.

## 7. New Findings Added

### KF-074 — native gameplay PC090OJ ownership and PLAYER_BODY lifecycle

KF-074 records the current gameplay/frontend split and Build 0251 ordering guardrail:

- gameplay scene `1` uses semantic priority lanes and final SAT merge;
- frontend/non-gameplay still uses transitional object-store/legacy-emitter compatibility;
- Build 0250 Rastan absence was a queue-lifetime defect, not palette, CRAM, or tile-art failure;
- `native_sprite_frame_begin` must run before `PLAYER_BODY` staging, and the queued body must survive until the single finalizer;
- future changes must not move reset/staging/finalizer timing without a complete producer-order proof.

### KF-075 — paired D00298/D002B0 writer family

KF-075 records the Ghidra-proven durable provenance:

- `FUN_0005a502` constructs eight complete contiguous records 83–90;
- raw destinations `0x00D00298` and `0x00D002B0` are one writer family and must move together;
- Build 0254 redirects both to `pc090oj_object_ram + 0x298/+0x2B0` without changing record contents or flow;
- user BlastEm verification confirms the prior fatal no longer occurs;
- the change is transitional compatibility, not final native SAT ownership.

## 8. Findings Intentionally Not Added

- No standalone causal finding was added for missing attract-demo scripted input. The only proven observation is that attract gameplay begins after Build 0254 but no scripted character movement is seen. No writer, disable site, NOP, input table, or lifecycle owner has been audited, so blaming Build 0254 or naming a cause would be speculation.
- No standalone entry was added for Build 0252 alone. Its safe call-site skip and Build 0253 body deletion are one coherent evolution of KF-072.
- No separate entry was added for the frontend compatibility boundary because it is inseparable from current gameplay ownership and is captured in KF-074.
- No finding claims all PC090OJ or PC080SN compatibility code is gone, that frontend rendering is native, or that `pc090oj_object_ram`/tall storage can be deleted.

## 9. Unresolved Evidence Gaps

- Attract-demo scripted input ownership is unproven and requires a dedicated audit before any fix.
- Frontend PC090OJ and PC080SN semantic conversion is not complete.
- Remaining unconverted/raw PC090OJ producers may still require compatibility destination routing until converted at a proven semantic boundary.
- Tall-buffer/dirty/project-base retirement requires a new xref plus producer/consumer proof; Build 0253 proved only projector-body reachability.

## 10. Open / Closed Issues Impact

- Open issues touched: `OPEN-024`.
- Context only: `OPEN-001`, `OPEN-015`, `OPEN-017`.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: attract-demo scripted input provenance; frontend native PC090OJ/PC080SN conversion; compatibility table/global retirement.

## 11. STOP Status

STOP triggered: NO.

All required evidence was available and mutually consistent. The synchronization required documentation changes only; no source, spec, generated artifact, ROM, or counter change was needed.
