# Cody — Build 0369 Auxiliary Retirement Fix

Date: 2026-09-23  
Baseline: Build 0368  
Produced build: Build 0369

## A. Accepted 0366/0367/0368 audit conclusion

The accepted regression audit is not reopened here. Its controlling conclusion is:

- Build 0367's HUD instruction shrink changed the ROM bytes observed through the already-stale
  `0x0010D2C8` item-event pointer, producing repeated false FIRE grants.
- Build 0368 correctly rebased that reader to the real A5-relative event table at
  `0x00FF12C8`, restoring the normal weapon and exposing real type-0 hit events.
- A real type-0 event activates the auxiliary at `A5+0x1296`, but the live primary updater's
  two terminal stores still addressed arcade absolute `0x0010D296`. That address is cartridge
  ROM on Genesis, so the authoritative A5-relative active word was never retired.

Build 0369 changes only those two proven terminal stores. It is a controlled lifecycle fix, not
a conclusion that the user's enemy-obstruction, cave-floating, or cave-hit-feel symptoms are
all resolved.

## B. Four `0x10D296` retirement-store sites

The relationship was verified byte-for-byte before editing against the original arcade region,
the Build 0368 ROM, and the Build 0368 address map:

| Updater | Arcade PC | Build 0368 Genesis PC | Build 0368 bytes | Result |
|---|---:|---:|---|---|
| live primary, subtype 1 | `0x051A8C` | `0x051C98` | `33 FC 00 FF 00 10 D2 96` | stale absolute store |
| live primary, subtype 4 | `0x051AA8` | `0x051CB4` | `33 FC 00 FF 00 10 D2 96` | stale absolute store |
| duplicate, subtype 1 | `0x052B0E` | `0x052C36` | `3B 7C 00 FF 12 96` | already correct |
| duplicate, subtype 4 | `0x052B2A` | `0x052C50` | `3B 7C 00 FF 12 96` | already correct |

The original arcade bytes at all four arcade PCs are
`33 FC 00 FF 00 10 D2 96`, or `move.w #$00FF,$0010D296.l`. The duplicate updater was already
translated to `move.w #$00FF,A5+0x1296`; only the live-primary pair remained stale.

## C. Primary versus duplicate updater

The accepted audit and the reproduced Build 0368 runtime trace identify the `0x051A8C` /
`0x051AA8` family as the live primary path used by the observed auxiliary lifecycle. The
`0x052B0E` / `0x052B2A` duplicate family already had the correct A5-relative retirement stores,
but that did not retire the instance exercised by the real type-0 event. This is why fixing the
duplicate pair earlier did not prevent the Build 0368 phase-`0x14` stick.

## D. Exact two-site patch

Two declarative `shift_replacements` were added to `specs/rastan_direct_remap.json`:

```text
arcade 0x051A8C: 33FC00FF0010D296 -> 3B7C00FF1296
arcade 0x051AA8: 33FC00FF0010D296 -> 3B7C00FF1296
```

This preserves the terminal value and changes only its destination contract:

```text
terminal auxiliary phase
    -> move.w #$00FF,A5+0x1296
    -> auxiliary inactive
```

The replacements are 8-to-6-byte semantic rewrites handled by the established shift/reflow
pipeline. There is no runtime helper, NOP, RTS bypass, shadow, fallback, object test, or added
state.

The Build 0369 address map and final canonical bytes are:

| Arcade PC | Build 0369 Genesis PC | Final bytes |
|---:|---:|---|
| `0x051A8C` | `0x051C98` | `3B 7C 00 FF 12 96` |
| `0x051AA8` | `0x051CB2` | `3B 7C 00 FF 12 96` |
| `0x052B0E` | `0x052C32` | `3B 7C 00 FF 12 96` |
| `0x052B2A` | `0x052C4C` | `3B 7C 00 FF 12 96` |

The two new two-byte contractions account for the four-byte downstream address shift; the
generated address map is authoritative for the new runtime PCs.

## E. Before/after auxiliary lifecycle trace

The existing Genesis NTSC route/input method was run against canonical Builds 0368 and 0369.
Both runs reach the same real type-0 event and the same subtype-4 auxiliary progression.
Selected exact samples follow (`active=A5+0x1296`, `phase=A5+0x1298`,
`subtype=A5+0x129E`):

| Build | Frame | Event record 0 `{active,type,x,y}` | active | phase | subtype | Meaning |
|---:|---:|---|---:|---:|---:|---|
| 0368 | 2979 | `{0001,0000,00B8,0079}` | `00FF` | `0000` | `0000` | real type-0 event present |
| 0368 | 2980 | `{0001,0000,00B8,0079}` | `0001` | `0001` | `0004` | auxiliary activated |
| 0368 | 3003 | inactive | `0001` | `0013` | `0004` | normal progression |
| 0368 | 3004 | inactive | `0001` | `0014` | `0004` | terminal phase reached |
| 0368 | 3060 | inactive | `0001` | `0014` | `0004` | incorrectly remains active |
| 0368 | 3420 | inactive | `0001` | `0014` | `0004` | still stuck |
| 0369 | 2979 | `{0001,0000,00B8,0079}` | `00FF` | `0000` | `0000` | same real type-0 event present |
| 0369 | 2980 | `{0001,0000,00B8,0079}` | `0001` | `0001` | `0004` | same activation |
| 0369 | 3003 | inactive | `0001` | `0013` | `0004` | same progression |
| 0369 | 3004 | inactive | `0001` | `0014` | `0004` | same terminal phase |
| 0369 | 3005 | inactive | `00FF` | `0014` | `0004` | live-primary retirement succeeds |
| 0369 | 3019 | `{0001,0000,00C0,0079}` | `00FF` | `0014` | `0004` | later real event arrives while inactive |
| 0369 | 3020 | inactive | `0001` | `0001` | `0004` | a new bounded lifecycle begins |
| 0369 | 3060 | inactive | `00FF` | `0014` | `0004` | later lifecycle also retired |

This proves the requested sequence and isolates the fix: event production and activation are
unchanged; the first divergence is the terminal active-word write. Full traces are preserved at:

- `states/traces/build0369_auxiliary_retirement_20260923_092047/build0368_before.tsv`
- `states/traces/build0369_auxiliary_retirement_20260923_092047/build0369_after.tsv`

The weapon selector is `0001` throughout the cited gameplay samples.

## F. Unchanged special-solid path

No special-solid producer, consumer, registration rule, response, support field, or hitbox was
changed. The Build 0366 relocation remains present in the canonical ROM:

```text
arcade 0x054BF8 -> Genesis 0x054C8E
41 F9 00 FF 02 42    lea 0x00FF0242,a0
```

The trace's `A5+0x0242`, response, and side fields remain inactive on this outdoor route. Build
0369 makes no claim about the cave's user-visible collision behavior.

## G. Unchanged item-event path

The Build 0368 event-table relocation remains present:

```text
arcade 0x054B1E -> Genesis 0x054BB4
41 F9 00 FF 12 C8    lea 0x00FF12C8,a0
```

The real event records in the A/B trace prove that the live table continues to drive the
original dispatcher. `A5+0x12FA` remains `0001` through the first and subsequent type-0 events;
FIRE is not active without a real subtype-1 gameplay event. No weapon state, timer, mapping,
contact table, sword extent, cave hurtbox, or active-frame logic changed.

## H. Unchanged water and rope fixes

The linked native HUD code remains:

```text
0x0007387A  41F9 00FF B800    lea     0x00FFB800,a0
0x00073880  3140 0014         move.w  d0,20(a0)
0x00073884  0C6D 0001 1328    cmpi.w  #1,4904(a5)
```

No production assembly file was changed for Build 0369. In particular, the general compositor,
`genesistan_native_contact_coords_51ab6`, rope registration/contact behavior, and rope mapping
semantics are source-identical to Build 0368. Automated gameplay-entry and standard traces show
zero address, bus, illegal-instruction, or crash-handler events, but the route does not exercise
water death or the rope; those remain explicit user regression tests.

## I. Build artifacts and automated validation

All five same-number artifacts are 1,719,992 bytes:

| Variant | Artifact | SHA-256 |
|---|---|---|
| canonical | `dist/rastan-direct/rastan_direct_video_test_build_0369.bin` | `491c9f35e3149b42c763f8529d1e78a52bad0a1bf82d9a3bdf87b9035c0686b0` |
| `_d` | `dist/rastan-direct/rastan_direct_video_test_build_0369_d.bin` | `790e561afaf4b39395fcbf8ddd17034e646c2686188c0e3b2e7ac53b455727bc` |
| `_s` | `dist/rastan-direct/rastan_direct_video_test_build_0369_s.bin` | `038745b1c7c5d54c1c546c7f3ad485d3fc278995f56efd5fa25bf85b2e7943e5` |
| `_do` | `dist/rastan-direct/rastan_direct_video_test_build_0369_do.bin` | `5d132b6dfdf1ffe98e73ea682bc2523c40f09e85026035da46775fbecaeb0034` |
| `_c` | `dist/rastan-direct/rastan_direct_video_test_build_0369_c.bin` | `3c212a993ad2848eee748b340d1f31415faf57fa9dba2a28ae7b4da28c92dbe1` |

Build counter: `369`. Consumed ledger records Build 0369 as produced.

- Canonical gate: **PASS**.
- Complete canonical/`_d`/`_s`/`_do`/`_c` artifact-set gate: **PASS**.
- Genesis NTSC gameplay-entry gate: **PASS**, including 240 post-entry frames and zero address,
  bus, illegal-instruction, or crash-handler events. Evidence:
  `states/traces/build0369_gameplay_entry_gate_20260923_092042`.
- Standard 30-second Genesis NTSC trace: completed 1,798 frames with no unmapped-memory fault.
  Evidence: `states/traces/rastan_direct_video_test_build_0369_mame_30s_20260923_092047`.
- Controlled event/auxiliary route: normal weapon, real type-0 activation, progression to phase
  `0x14`, and retirement to `0x00FF`: **PASS**.
- The known seven-epoch gate remains a warning/failure and did not suppress publication, matching
  the preceding accepted builds.

## J. User validation boundary

Build 0369 proves the stale live-primary destination and its corrected bounded lifecycle. It does
not prove the complete physical mechanism behind the three reported downstream symptoms.

BlastEm validation is required for:

1. killing the same enemies and checking the former-location obstruction;
2. cave-block hit tolerance, destruction, standing during destruction, and post-destruction
   floating;
3. water death remaining crash-free;
4. normal sword at start and no permanent FIRE;
5. rope rendering, grabbing, carrying, and release remaining correct.

Until Tighe reports those results, enemy ghost obstruction, cave floating, and cave hit
difficulty remain **USER TEST REQUIRED**, not fixed claims. No further fix is started from this
build.
