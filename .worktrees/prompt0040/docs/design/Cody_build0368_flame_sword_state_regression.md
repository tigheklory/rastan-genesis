# Cody — Build 0368 FIRE SWORD state regression

Date: 2026-09-22  
Baseline: Build 0367  
Artifact under test: Build 0368  
User validation status: **BlastEm validation required**

## A. User-observed Build-0367 symptom

Tighe reported that Build 0367 starts Rastan with the FIRE SWORD (the task used
“flame sword”), that it never clears, and that the cave entrance block remains
solid and destructible but feels unusually position-sensitive to sword hits.
Build 0367's water-death fix was user-confirmed and remains accepted.

## Semantic boundary

The retained arcade gameplay state remains authoritative for weapon selection:

```text
retained arcade item event / timer / A5+0x12FA selector
    -> retained mapping and contact-table selection
    -> native Genesis SAT realization
```

The PC090OJ chip-specific tail stays retired. Build 0368 changes only the
absolute address contract by which the retained item dispatcher reaches its
live event records. It adds no native weapon flag, synthetic pickup, forced
normal state, or cave-block special case.

## B–C. Original arcade weapon-state fields and values

| Field | Proven meaning | Normal SWORD | FIRE SWORD | Writers |
|---|---|---:|---:|---|
| `A5+0x12FA` (arcade `0x10D2FA`, Genesis `0xFF12FA`) | Shared melee-weapon selector | `1` | `4` | init `0x504B6`; expiry `0x54E74`; grants `0x54ED4`, `0x54EEA`, `0x54F00` |
| `A5+0x1326` (arcade `0x10D326`, Genesis `0xFF1326`) | Shared melee-weapon elapsed timer | `0` at init | cleared to `0` when granted, then increments | init `0x504BC`; expiry/update `0x54E70`/`0x54E7C`; grants `0x54ED0`, `0x54EE6`, `0x54EFC` |
| `A5+0x12C8` | Four 8-byte item-event records | no active FIRE record | `{active=1, subtype low byte=1}` grants FIRE | dispatcher scan `0x54B1E..0x54BF4` |

No separate FIRE-SWORD Boolean was found. The selector value is the gameplay
state. The event record's `active` word is a dispatcher input, not a persistent
weapon-power flag. `A5+0x138C` is a separate body-animation selector and
`A5+0x1388` is a separate front/thrown-weapon type; neither replaces
`A5+0x12FA`.

The stage-init master at `0x501EA` calls equipment initialization `0x5049A`
from `0x50242` when its existing mode branch permits it. That routine writes
selector `1` at `0x504B6` and clears the timer at `0x504BC`. An exhaustive
operand audit found no independent death-only writer: all writes to these two
fields are the initializer, timer expiry, and the three weapon-grant leaves.
Consequently, reset/round behavior follows the existing stage-init routing;
Build 0368 does not invent a new death hook.

## D. FIRE SWORD acquisition

The retained dispatcher `0x54A2C` first calls the timer updater and then scans
four item records starting at arcade WRAM `0x10D2C8`. At `0x54B70`, subtype
low byte `1` calls `0x54EF2` only when the record's active word equals `1`.

`0x54EF2` performs the complete grant:

1. sends sound command `0x000E` through `0x3A0EC`;
2. clears `A5+0x1326` at `0x54EFC`;
3. writes FIRE-SWORD selector `4` to `A5+0x12FA` at `0x54F00`.

This original acquisition path is unchanged and therefore remains available
for a real gameplay event.

## E. FIRE SWORD expiration and clearing

The per-frame updater at `0x54DD2`, called by `0x54A2C` at `0x54A3C`, handles
melee expiry at `0x54E58..0x54E80`. It indexes the threshold table at `0x54E96`
with raw field `A5+0x1418`. The five thresholds are:

```text
0x0BB8, 0x0E10, 0x1068, 0x12C0, 0x1518
```

Until the selected threshold is reached, `0x54E7C` increments `A5+0x1326`.
At equality, `0x54E70` clears the timer and `0x54E74` restores selector `1`.
Build 0367 did not have a broken timer or reversed test: its false event record
re-granted state `4` and reset the timer repeatedly, defeating the otherwise
correct expiry path. Build 0368 retains the updater unchanged.

## F. Genesis-native weapon selection

The retained visual producer tests `A5+0x12FA` at `0x54536` and selects these
mapping programs:

| Selector | Mapping program |
|---:|---:|
| `1` | `0x5CD8A` |
| `4` | `0x5D068` |
| `2` | `0x5D346` |
| `3` | `0x5D666` |

The retained gameplay contact producer tests the same selector at `0x548D8`
and selects:

| Selector | Contact table |
|---:|---:|
| `1` | `0x5C9EA` |
| `2` | `0x5CAC6` |
| `3` | `0x5CBA2` |
| `4` | `0x5CC7E` |

The native compositor receives the already-selected mapping pieces and emits
final SAT entries. It does not reinterpret a private native weapon flag. The
Build 0367 failure was therefore **both visual and gameplay-state**, including
contact geometry, rather than a display-only error.

## G. Build 0366 versus 0367 static comparison

The address-map/reflow products were used rather than assuming a constant PC
delta. Direct binary comparisons of the canonical artifacts found zero byte
differences in representative retained weapon/player regions:

| Runtime region | Compared bytes | Differences |
|---:|---:|---:|
| `0x51090` player main | `0x80` | `0` |
| `0x52732` weapon-state path | `0x80` | `0` |
| `0x52AF6` timer-adjacent path | `0x80` | `0` |
| `0x545D0..0x54ACF` visual/contact selection range | `0x500` | `0` |

The intended Build-0367 HUD instruction shrink/reflow did not alter these
branches, pointers, loads, selectors, timer operands, or mapping/contact
tables. The defect was a pre-existing unrebased absolute arcade-WRAM operand
which became visible during Build-0367 testing, not a semantic mutation caused
by the HUD store.

## H. First divergence and root cause

The original instruction at arcade `0x54B1E` is:

```asm
lea 0x0010D2C8.l,a0
```

Build 0367 copied it unchanged. On Genesis, `0x0010D2C8` is cartridge ROM, not
the mapped retained work RAM. The 32 ROM bytes interpreted as four event
records were:

```text
0300 0300 0F0C 0F0C
0000 0000 0F0F 0F0F
0001 0001 0E0F 0E0F
0202 0000 0F0F 0D0D
```

The third false record at `0x10D2D8` is exactly `{active=1, subtype=1}`. Thus
the unchanged original dispatcher legitimately called `0x54EF2` on bogus ROM
data after the correct initializer had established state `1`.

The Build 0367 Genesis NTSC trace records selector `0 -> 1` at frame 407, then
`1 -> 4` at frame 409. This is the first runtime divergence. The timer remains
near zero because the false record repeatedly re-grants FIRE SWORD.

Evidence:

- `states/traces/build0368_weapon_state_build0367_genesis_20260922/weapon_state_trace.csv`
- original static listing and Ghidra exports for `0x5049A`, `0x54A2C`,
  `0x54DD2`, and `0x54EF2`

## I. Normal versus FIRE attack/contact geometry

The selector changes both mapping pieces and attack extents. Decoding all 55
four-byte entries of the normal table at `0x5C9EA` and FIRE table at `0x5CC7E`
shows distinct extents for every nonzero representative attack frame. Examples
below retain the table's signed four-value order:

| Frame | Normal (`state 1`) | FIRE (`state 4`) |
|---:|---|---|
| `00` | `{7, 10, -40, -16}` | `{6, 11, -41, -15}` |
| `01` | `{16, 30, -24, -21}` | `{15, 31, -25, -20}` |
| `02` | `{16, 32, -9, -7}` | `{15, 33, -10, -6}` |
| `03` | `{0, 9, -5, 0}` | `{-1, 10, -6, 1}` |
| `04` | `{-19, -8, -8, 3}` | `{-20, -7, -9, 4}` |
| `05` | `{-56, -24, -10, -8}` | `{-57, -23, -11, -7}` |

Therefore the user's cave-block hit observation can plausibly be a secondary
effect of being in the wrong weapon state. It is not evidence that the solid
block rectangle should be enlarged.

## J. Cave-block relationship

The Build 0366 cave block's destruction and player-solidity routes are
unchanged. Build 0368 does not alter `0x449B4`, `0x44548`, `0x444F8`,
`0x54BF8`, or the special-solid record at `A5+0x0242`. The block should be
retested with the restored normal SWORD before any independent hit-geometry
work is considered.

## K. Exact fix

The authoritative remap spec adds one byte-neutral address-contract repair:

```text
arcade PC:          0x054B1E
original:           41F90010D2C8
replacement:        41F900FF12C8
final Genesis PC:   0x054BB8
```

The final address map records a six-byte `patched_site` at `0x54BB8..0x54BBE`
with zero shift delta. This redirects the retained dispatcher to the real
Genesis work-RAM counterpart of `A5+0x12C8`. No control flow, timer logic,
weapon grant, renderer, contact producer, cave logic, water logic, or rope code
was changed.

Fresh Build 0368 Genesis NTSC trace proof:

- frame 407: selector becomes normal state `1`, timer `0`;
- frame 409 onward: timer advances normally;
- through frame 800: selector remains `1`, no state `4` appears;
- final frame 800: selector `1`, timer `0x0140`.

Evidence:
`states/traces/build0368_weapon_state_build0368_genesis_20260922/weapon_state_trace.csv`.

The canonical gameplay-entry gate also passed with `address_errors=0`,
`bus_errors=0`, `illegal_instructions=0`, and `crash_handler_entries=0`. The
standard seven-epoch evaluation emitted its pre-existing non-blocking warning;
the numbered artifacts were deliberately preserved for user evaluation.

Decompilation deliverables added for the formerly missing functions:

- raw: `0005049a.c`, `00054a2c.c`, `00054dd2.c`, `00054ec6.c`;
- semantic: `rastan_player_weapon_state.c`;
- coverage/audit inventories and canonical Ghidra labels/exports updated.

Both decompilation coverage and fidelity guards pass; the new C also passes
`gcc -std=c11 -fsyntax-only`.

## L. Build 0368 artifacts

All artifacts are 1,719,992 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `c031aa60867801db3733e06486feb2c87e5842a46c7bc9f441b80cc2a527beb4` |
| `_d` | `6f9985319e528f709a4315bf3a9ccbdddf47b5e52b8fbeb570db9fd8de187699` |
| `_s` | `ddbe6cddce55f8c963a9ca4f25e99914052668bb140cdeee7d61829fe0546932` |
| `_do` | `a1d4df528074f0ffe68a201693068eb0a340b577d25da2711e6f6e7610b3cef7` |
| `_c` | `b627cc0e04bf1d89dbb1767c691b7e6a8a8724265f889183b203f0c5e38fe307` |

Counter after publication: `368`.

## M. Required BlastEm validation

Build 0368 is testable, but the defect is not user-accepted until Tighe checks:

1. a new game starts with the normal SWORD, not FIRE SWORD;
2. normal sword visuals and contact feel normal;
3. a legitimate FIRE-SWORD pickup still grants state `4`;
4. FIRE SWORD expires back to the normal SWORD;
5. the cave block remains solid and destructible, and hit ease is retested with
   the normal SWORD;
6. water death/respawn still does not crash;
7. the rope remains visible, grabbable, rideable, and releasable.

