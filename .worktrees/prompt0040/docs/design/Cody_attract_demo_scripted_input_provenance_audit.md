# Cody — Attract Demo Scripted Input Provenance Audit

## Result

Build 0254 does contain and reach the original arcade attract-demo input player, but the translated player terminates immediately instead of consuming its script. The root cause is one two-part translation-family defect inside the retained arcade routine:

1. its stage-derived script selector reads the raw arcade absolute address `0x0010C118` instead of mapped Genesis WRAM `0x00FF0118`; and
2. its nine-entry script-pointer table at arcade `0x052C1C` was copied but its embedded absolute ROM pointers were not relocated.

Both defects predate Build 0254. The D00298/D002B0 writer repair did not create or alter either site. This was an audit-only task: no fix, build, generated artifact, ROM, or counter change was authorized or made.

## Baseline and observation

- Accepted baseline: Build 0254, `dist/rastan-direct/rastan_direct_video_test_build_0254.bin`.
- SHA-256: `53bf25f4f2a090864aaab3fad98ce1646b15226d218f5e907468e52212c0b7e4`.
- Size: `1,592,224` bytes.
- Counter: `254`.
- Rolling ROM has the same SHA-256 and size.
- User-observed behavior: attract gameplay now starts without the former D00298/D002B0 fatal, but Rastan stands still rather than following the arcade demo movement script.
- Accepted Build 0254 visual/runtime status is preserved.

## Scope and prior evidence read

The audit read `AGENTS.md`, the latest relevant `AGENTS_LOG.md` entries, `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, the canonical PC080SN/PC090OJ replacement policy, current issue/finding ledgers, the current remap spec/address map/symbols/generated disassembly, original `build/regions/maincpu.bin`, and current input/render source.

The closest prior reports were the Build 0249 audit, Build 0251/0252/0253 reports, Build 0254 attract reachability audit, Build 0254 D00298 fix report, and Builds 0249–0254 KNOWN_FINDINGS synchronization. This is a new behavior audit, not a revisit of the accepted D00298 repair. Relevant prior finding families are KF-022, KF-028, KF-057, KF-058, KF-074, and KF-075.

## Arcade owner and execution order

The existing read-only Ghidra project `tools/ghidra/rastan_project/rastan_arcade_ref.gpr` was used without saving changes. Ghidra resolved these arcade functions:

| Ghidra function | Arcade PC | Role |
|---|---:|---|
| `FUN_0005100a` | `0x05100A` | master per-tick update and direct demo-player caller |
| `FUN_0005126e` | `0x05126E` | selects/activates the attract demo |
| `FUN_00052b38` | `0x052B38` | resets the script run state while inactive |
| `FUN_00052b4a` | `0x052B4A` | owns scripted input playback |

Within `FUN_0005100a`, the relevant original order is:

1. `0x05102E`: read the normal input latch at `A5+0x16`.
2. `0x051034`: write the normal per-frame copy at `A5+0x137A`.
3. `0x051066`: call `FUN_0005126e`.
4. `0x051070`: call `FUN_00052b38`.
5. `0x051076`: call `FUN_00052b4a`.
6. `0x051086`: call downstream player/action logic `FUN_0005132a`.

Therefore, when demo playback is active, `FUN_00052b4a` intentionally overwrites `A5+0x137A` after the ordinary input copy and before player action logic consumes it. Genesis controller polling is not a later competing owner.

`FUN_0005126e` writes demo-active value `1` at `0x051296` or `0x0512B2` and selects script family `1` or `2` at `0x05129C` or `0x0512B8`. Gameplay initialization also marks demo mode when `A5+0x34 == 0`; the retained state timeline, rather than a manually seeded substitute, is responsible for activation.

## Script format, table, and state

`FUN_00052b4a` treats its data as two-byte `{duration,input}` pairs. If the remaining-duration byte is zero, it loads a script pointer, reads the next pair, and advances the word cursor. A zero duration terminates the demo by writing `0x00FF` to the demo-status word. Otherwise, every active frame writes `0xFF00 | input_byte` to the per-frame input copy and decrements duration.

The original nine-entry longword table occupies arcade ROM `0x052C1C..0x052C3F`; data begins immediately at `0x052C40`. Nine entries are required because direct selector values are `1`/`2`, while the stage-derived selector covers `stage+2` for stages 1–6, or indices 3–8.

| Index | Original table value |
|---:|---:|
| 0 | `0x0005354E` |
| 1 | `0x00052C40` |
| 2 | `0x00052C44` |
| 3 | `0x0005354E` |
| 4 | `0x00052F4A` |
| 5 | `0x0005324C` |
| 6 | `0x00052C48` |
| 7 | `0x00052C48` |
| 8 | `0x00052C48` |

The first script bytes are `FF F7 00 00 FF FB 00 00 46 FF 51 F7 ...`. With active-low controls, `FF F7` requests Right for 255 frames and `FF FB` requests Left for 255 frames; the zero-duration pairs terminate their short alternatives.

| Arcade state | Genesis WRAM | Meaning |
|---|---:|---|
| `A5+0x16` | `0x00FF0016` | ordinary input latch |
| `A5+0x34` | `0x00FF0034` | normal-play/demo gate |
| `A5+0x118` | `0x00FF0118` | stage byte used to derive a script selector |
| `A5+0x1372` | `0x00FF1372` | remaining duration byte |
| `A5+0x1373` | `0x00FF1373` | current scripted input byte |
| `A5+0x1374` | `0x00FF1374` | pair cursor word |
| `A5+0x1376` | `0x00FF1376` | demo status: `1` active, `0x00FF` finished |
| `A5+0x137A` | `0x00FF137A` | per-frame input consumed downstream |
| `A5+0x1384` | `0x00FF1384` | explicit selector override |

The ordinary Genesis controller producer remains `rastan_direct_update_inputs` in `apps/rastan-direct/src/tilemap_hooks.s`. `_vblank_service` calls it before returning to the copied arcade VBlank/update flow. Current input shadows are `genesistan_shadow_input_390001=0x00FFA1CC` and `genesistan_shadow_input_390003=0x00FFA1CD`; remap sites redirect arcade hardware input reads to them. KF-057/KF-058 and the 29 existing `A5+0x137A` consumer rebases establish that the normal input pipeline and downstream consumers are already live.

## Authoritative address-map proof

The mappings below were read from `build/rastan-direct/address_map.json`; they are not inferred by applying a blanket offset.

| Arcade PC/data | Runtime Genesis PC/data | Kind / purpose |
|---:|---:|---|
| `0x03A4A2`, `0x03A4A8` | `0x03A6A2`, `0x03A6A8` | `patched_site`, normal input reads |
| `0x03A778`, `0x03A77E` | `0x03A978`, `0x03A97E` | `patched_site`, P1/P2 reads |
| `0x03A796` | `0x03A996` | `arcade_copy`, normal latch write |
| `0x05100A` | `0x05120A` | `arcade_copy`, master update |
| `0x05102E` | `0x05122E` | `patched_site`, mapped latch read |
| `0x051034` | `0x051234` | `arcade_copy`, normal `A5+0x137A` write |
| `0x051066`, `0x051070`, `0x051076` | `0x051266`, `0x051270`, `0x051276` | `arcade_copy`, demo call sequence |
| `0x05126E` | `0x05146E` | `arcade_copy`, selector/activation owner |
| `0x052B38` | `0x052D38` | `arcade_copy`, inactive reset |
| `0x052B4A` | `0x052D4A` | `arcade_copy`, script player |
| `0x052B66` | `0x052D66` | `arcade_copy`, bad raw stage-byte read |
| `0x052B70` | `0x052D70` | `arcade_copy`, table-base load |
| `0x052BA4` | `0x052DA4` | `arcade_copy`, scripted-input output write |
| `0x052BAE` | `0x052DAE` | `arcade_copy`, finished-status write |
| `0x052C1C` | `0x052E1C` | `arcade_copy`, pointer table |
| `0x052C40`, `0x052C44`, `0x052C48` | `0x052E40`, `0x052E44`, `0x052E48` | `arcade_copy`, script data |
| `0x052F4A`, `0x05324C`, `0x05354E` | `0x05314A`, `0x05344C`, `0x05374E` | `arcade_copy`, other script targets |

The script function and its data are copied and reachable; they are not NOPed, bypassed, or removed. The failure is address provenance inside that retained function.

## Defect A: raw WRAM selector read

At arcade `0x052B66`, the original instruction is `move.b 0x0010C118,d0`. Build 0254 retains the exact bytes at runtime `0x052D66`:

```text
1039 0010 c118
```

The intended field is the stage byte at `A5+0x118`, whose mapped Genesis address is `0x00FF0118`. During the focused trace, mapped `0x00FF0118` held `0x01`, while Build 0254 ROM byte `0x0010C118` was `0xFF`. With selector override zero, the retained arithmetic therefore derives `0xFF - 1 + 3 = 0x101` instead of index `3`.

This is a raw absolute arcade-WRAM literal rebase defect in the OPEN-017 family.

## Defect B: copied but unrelocated pointer table

The instruction operand at runtime `0x052D70` was correctly relocated and loads table base `0x00052E1C`. The table bytes at `0x052E1C`, however, remain byte-identical to the arcade table and still contain arcade addresses such as `0x00052C40` and `0x0005354E`, rather than their authoritative Genesis copies `0x00052E40` and `0x0005374E`.

`specs/rastan_direct_remap.json` currently lists absolute-long pointer tables only at arcade `0x03BB7C`, `0x059EC8`, `0x059C9A`, and `0x059F1E`. The demo table at `0x052C1C` is absent. This is the durable embedded-data relocation class recorded by KF-028 and OPEN-016.

The first defect currently indexes `0x052E1C + 0x101*4 = 0x053220`. Bytes there begin `2E F7 03 E7`, so the retained code deterministically interprets `0x2EF703E7` as a pointer and obtains no valid duration. This address/value is a static derivation from the emitted instruction and ROM bytes, not a claimed dynamic pointer capture.

Both defects must be repaired together. Rebasing only the stage read exposes stale table entries; relocating only the table leaves the out-of-range selector.

## Focused runtime evidence

A bounded, no-input audit ran the accepted Build 0254 ROM with:

```bash
TRACE_DIR=/tmp/attract_demo_input_audit MAX_FRAMES=3100 timeout 180s mame genesis \
  -cart dist/rastan-direct/rastan_direct_video_test_build_0254.bin \
  -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script /tmp/attract_demo_input_audit.lua
```

The run completed successfully through external frame 3100. End-of-frame samples show:

| Frame | Relevant state |
|---:|---|
| 2643 | scene becomes `1`; copied state `2/2/4` |
| 2689 | state `2/2/5`; demo status `0001`; duration `01`; cursor `0`; selector `0`; mapped stage `01` |
| 2690 | state `2/3/0`; demo status remains `0001` |
| 2691 | input copy `FF00`; demo status `0001`; duration reaches `00` |
| 2692 | input copy returns to `FFFF`; demo status becomes `00FF`; cursor remains `0`; selector remains `0` |
| 2693–3100 | input remains `FFFF`; demo remains finished |

This proves that the correct attract/demo state is created in order, but playback terminates before advancing the pair cursor or producing meaningful scripted input. MAME write taps did not provide trustworthy PC attribution after boot, so the trace is used only for frame-state evidence; function ownership and failure mechanics come from Ghidra, the address map, generated disassembly, and ROM bytes.

## State causality answers

1. **What state should exist at this PC?** At `FUN_00052b4a`, demo status should be active, the selector should identify one of nine valid scripts, the cursor should address a duration/input pair, and `A5+0x137A` should receive that pair's active-low input before player action logic.
2. **Which earlier code creates it?** Initialization establishes demo mode and initial run/cursor/selector state; `FUN_0005126e` activates/selects the demo; the original table/data supplies the pair stream; `FUN_00052b4a` owns per-frame advancement/output.
3. **Why was it not created correctly?** Activation is created correctly, but a retained raw WRAM literal derives an invalid selector and the copied table independently retains stale arcade pointers. The player therefore reaches its zero-duration finish path without a valid pair.

No state is skipped, duplicated, reordered, or manually seeded by this audit. The observed `FFFF` is not caused by normal controller polling overwriting demo output; the demo owner is ordered later and simply terminates.

## Preexisting status and Build 0254 separation

A byte comparison of Builds 0253 and 0254 found changes only in the ROM checksum field and the two D00298/D002B0 replacement operands. The bytes at the demo selector read, table-base instruction, table, and script data are unchanged. Therefore:

- defect preexisting: **YES**, present unchanged in at least Builds 0253 and 0254;
- Build 0254 D00298 fix implicated: **NO**;
- original arcade scripted path present: **YES**;
- current function reached/activated: **YES**;
- current function bypassed or NOPed: **NO**;
- normal-controller ownership conflict: **NO**.

## Narrow future implementation candidate — not implemented

The smallest correct future repair is one indivisible spec/tool translation correction:

1. Add a byte-neutral `opcode_replace` at arcade `0x052B66`:
   `10390010C118 -> 103900FF0118`.
2. Add the arcade `0x052C1C` table to `absolute_long_pointer_tables` with `entry_count: 9` and `entry_size_bytes: 4`, relocating every in-window longword through the authoritative address map.

A later implementation must prove that the emitted table targets the mapped script addresses, demo status stays active, the cursor advances, and `0x00FF137A` receives the same scripted sequence before player action logic as the arcade reference. It must also preserve normal controller input, Build 0254's D00298/D002B0 repair, frontend behavior, and current native rendering.

An Andy architecture review is **not recommended as a prerequisite**: this is a bounded recurrence of the existing raw-WRAM and embedded-pointer relocation mechanisms and does not alter the native PC080SN/PC090OJ architecture. Normal implementation review and a matched arcade/Genesis validation trace are still required before any Cody build.

## Architecture and issue impact

Semantic rendering cut remains `actor/object semantic state -> native Genesis SAT`; the retired chip-specific gameplay scan/decode/render tail remains removed. This audit adds no shadow, mirror, scanner, fallback, runtime patch, NOP, RTS bypass, or equal-length workaround. Transitional frontend `pc090oj_object_ram` and all native Plane A/B/SAT paths are unchanged.

- OPEN-016: directly touched by the missing embedded absolute pointer-table relocation.
- OPEN-017: directly touched by the raw arcade-WRAM literal and input behavior.
- OPEN-024: context only because the observation followed the accepted Build 0254 attract repair; it is not causal.
- New issues opened: **NONE**.
- Issues closed: **NONE**.
- Deferred: implementation/build, matched post-fix arcade/Genesis trace, frontend-native PC090OJ/PC080SN conversion, and compatibility retirement.
- KNOWN_FINDINGS: no index change in this audit; the result applies existing KF-028/KF-057/KF-058 translation and input provenance and remains separate from KF-075.

## Stop status

STOP triggered: **NO**. The requested provenance audit is complete. Implementation was intentionally not authorized, so no fix or numbered build was attempted.
