# Andy — RG-018: Build-Time Starting-Subround Test ROM Variants

**Task:** RG-018 · **Agent:** Andy (Opus) · **Date:** 2026-10-24 · **Parent build:** 0494
(`99d2ccd2b3e9dd08d5a7e31c2195a0c8acd58024040702b83965fa58691de677`).

## Objective

Optionally generate 18 test ROMs (6 rounds × 3 subrounds), each with its starting subround fixed at
build time — no in-game menu, controller cheat, or runtime MAME dependency — to test later portions of
the game directly. `make release` is unchanged.

## 1. Arcade stage-select mechanism (traced)

The MAME cheat file `tools/mame/cheat/output.xml` "Select Starting Round/Sub-Round" writes a parameter
to the arcade program. **Address discrepancy:** the task states arcade `0x05FF9F`, but the cheat XML
writes `maincpu.mb@05FFFD`. The authoritative, traced mechanism is `0x05FF9F`:

The original stage decoder reads the config word at `0x05FF9E` (low byte `0x05FF9F`) and decodes the
starting stage from its bits:

```
0x04527E  movew 0x5ff9e,d1 ; notw d1 ; andiw #7,d1 ; addq #1,d1   ; round = (~0x5FF9F & 7) + 1
          -> stored at a5@0x117 / a5@0x118
0x04529C  movew 0x5ff9e,d0 ; notw ; andiw #7 ; mulu #23,d0        ; stage = round*23
          btst #3,0x5ff9f ; bne ; addi #22,d0                     ; bit 3 clear => Boss  (+22)
          btst #5,0x5ff9f ; bne ; addi #16,a5@0x1242              ; bit 5 clear => Castle (+16)
          -> stage index stored at a5@0x1242
```

So the selector byte at arcade `0x05FF9F` is a packed value: bits 0–2 = round (`0xF8 | (8-round)`),
bit 3 = Boss, bit 5 = Castle, bit 6 = invincible (the existing invincible variant uses this). Default
`0xFF` = Round 1 Outside. The selector **values** (0xFF, 0xDF, 0xF7, 0xFE, …) match the cheat items and
the task table exactly; only the cheat's *write address* differs from the game's *read address*.

**Genesis equivalent — important subtlety.** The address map
(`build/rastan-direct/address_map.json`) maps arcade `0x05FF9F` to Genesis ROM offset **`0x05FFE5`**,
and the accepted invincible variant patches exactly that byte (`0xFF → 0xBF`). But `0x05FFE5` is only
read by the *startup* config decoder (translated arcade `0x03AFEE` → Genesis `0x3B21E`:
`movew 0x5ffe4,d0`), whose absolute operand WAS relocated. The **stage decoder** (translated arcade
`0x04527E`/`0x04529C` → Genesis `0x45482`/`0x454A0`) still reads the **unrelocated literal** operand:
`movew 0x5ff9e,d1`, `btst #3,0x5ff9f`, `btst #5,0x5ff9f`. Genesis `0x5FF9E` reverse-maps to arcade
`0x5FF58` (`0xFF` padding), so the stage decoder reads `0xFF` and always computes Round 1 — regardless
of the relocated config byte. **Therefore the byte the stage decoder actually reads is the literal
Genesis offset `0x05FF9F`** (verified empirically: patching it yields the selected round/subround; see
§6). An initial implementation patched the address-map location `0x05FFE5` and all variants still booted
to R1-S1, which exposed this operand-relocation gap. The generator now patches the literal read offset
`0x05FF9F` (detecting the unrelocated `movew 0x5ff9e` read form in the ROM; it falls back to the
address-map location if a future build relocates the operand). That byte is `0xFF` padding on the
canonical ROM, so the single-byte patch is safe.

## 2. Implementation (smallest build-time semantic override)

`tools/translation/build_subround_variant.py` copies the parent canonical ROM and patches the single
byte the stage decoder reads (the literal `0x05FF9F`; see §1), with the derived selector. It refuses to
patch a parent whose byte is not the default `0xFF`, and asserts only that byte changes (Round 1 Outside
= `0xFF` = default → a byte-identical variant, which is correct). This drives the game's own stage-decode
mechanism — no new gameplay code, no teleport; the chosen subround initializes through the original
stage setup. (It is the "smallest equivalent build-time semantic override" the task allows when the
address-map-relocated data location is not what the decoder reads.)

The variants are derived from the current numbered canonical ROM, so they inherit its build number and
embedded crash-handler stamp automatically (only `0x05FFE5` differs).

## 3. Build-system integration (`apps/rastan-direct/Makefile`)

- `make -C apps/rastan-direct release` — unchanged seven-ROM build (never generates the 18).
- `make -C apps/rastan-direct test-subround ROUND=1 SUBROUND=2` — one variant.
- `make -C apps/rastan-direct test-subrounds` — all 18, then runs the verifier.

Targets resolve the parent build number/ROM at use time, require the canonical ROM to already exist
(error directing to `make release` otherwise), **consume no build number**, and never overwrite the
canonical. Each variant uses the standard gameplay configuration — no `_d/_s/_do/_c/_full_hud/
_invincible` per subround.

## 4. Naming and selector table

`rastan_direct_video_test_build_<NNNN>_S<round>-<subround>.bin`, e.g. `..._0494_S1-2.bin`.

| Suffix | Location | Value | | Suffix | Location | Value |
|---|---|---|---|---|---|---|
| `_S1-1` | R1 Outside | `0xFF` | | `_S4-1` | R4 Outside | `0xFC` |
| `_S1-2` | R1 Castle | `0xDF` | | `_S4-2` | R4 Castle | `0xDC` |
| `_S1-3` | R1 Boss | `0xF7` | | `_S4-3` | R4 Boss | `0xF4` |
| `_S2-1` | R2 Outside | `0xFE` | | `_S5-1` | R5 Outside | `0xFB` |
| `_S2-2` | R2 Castle | `0xDE` | | `_S5-2` | R5 Castle | `0xDB` |
| `_S2-3` | R2 Boss | `0xF6` | | `_S5-3` | R5 Boss | `0xF3` |
| `_S3-1` | R3 Outside | `0xFD` | | `_S6-1` | R6 Outside | `0xFA` |
| `_S3-2` | R3 Castle | `0xDD` | | `_S6-2` | R6 Castle | `0xDA` |
| `_S3-3` | R3 Boss | `0xF5` | | `_S6-3` | R6 Boss | `0xF2` |

## 5. Validation

`tools/translation/verify_subround_variants.py` (run by `test-subrounds`): **ALL CHECKS PASS**.
- Selector values match the MAME cheat items exactly (all 18) and the pure derivation.
- The stage decoder's read offset (literal `0x05FF9F`) is detected in the ROM; canonical byte is `0xFF`.
- Every variant changes only `0x05FF9F` to the correct value (R1-1 byte-identical to canonical).
- No other byte of the canonical ROM is modified; all 18 generated; correct names + shared build number.
- Invalid round/subround inputs rejected; derivation is deterministic.

Confirmed operationally: parent build number stayed 0494 (no number consumed); canonical SHA unchanged;
`release → dual-build` does not reference the subround targets.

## 6. Stage-init observation (diagnostic, NOT a playability claim)

`tools/mame/scripts/subround_start_probe.lua` boots a variant on **GENESIS NTSC**, runs the normal
coin/start sequence, and samples the decoded round (`a5@0x118`) and stage index (`a5@0x1242`).

**Result: CONFIRMED.** After patching the correct read offset (`0x05FF9F`, §1), the probe observes the
game's own stage decoder selecting the chosen round and subround:

| Variant | observed round | stage index `a5@0x1242` | meaning |
|---|---|---|---|
| S1-1 | 1 | `0x00` | R1 Outside (round*23 = 0) |
| S3-1 | 3 | `0x2E` (46) | R3 Outside |
| S3-2 | 3 | `0x3E` (62 = 46 + 16) | R3 **Castle** |
| S2-3 | 2 | `0x2D` (45 = 23 + 22) | R2 **Boss** |
| S6-1 | 6 | `0x73` (115) | R6 Outside |

The stage index matches `round_bits*23 + 22·boss + 16·castle` exactly, so both the round and the
subround are selected through the original decode. This confirms the selector reaches the game's stage
setup (not a teleport).

**Scope caveat preserved:** confirming the decoder selects the stage is NOT a claim that each later
stage is fully playable — later-stage graphics/enemies/scrolling may still be incomplete. **Tighe
performs gameplay validation in BlastEm and on real Genesis hardware.** Compare against ORIGINAL ARCADE
MAME with the equivalent level-select cheat where useful.

## 7. Scaffolding and scope

- No new gameplay code, no NOP/RTS, no production ROM scaffolding. The variants are single-byte patches
  of the canonical ROM at the original selector location.
- New durable tooling (retain): `build_subround_variant.py`, `verify_subround_variants.py`,
  `subround_start_probe.lua`, and the `test-subround`/`test-subrounds` Makefile targets.
- RG-018 did not attempt to repair later rounds; it only adds the build-time selection infrastructure.
- Preserved: Build 0492 accepted behavior, all native audio and nine Composer arrangements, the
  sound-command mappings, death/respawn/GAME OVER, the seven-ROM release, and native VDP work. The
  variants use the normal gameplay music-selection mechanism (no Z80 engine change, no hardcoded music).

## 8. Open items and findings
- **Stage selection confirmed in MAME (§6).** Remaining validation is Tighe's BlastEm/hardware play
  test, which will expose which later stages are graphically/behaviorally incomplete.
- **Operand-relocation gap (finding).** The stage decoder (`0x45482`/`0x454A0`) reads its config operand
  as the unrelocated literal `0x5FF9E`/`0x5FF9F`, while the startup decoder's operand WAS relocated to
  `0x5FFE4`. The config word therefore effectively lives at two Genesis locations, and the stage decoder
  reads `0xFF` padding on the stock canonical — which is why the port always started at R1 before these
  ROMs. RG-018 drives the decoder's actual read byte (`0x5FF9F`); the proper long-term fix is to declare
  that operand for relocation so the decoder reads the same config the startup does (a semantic-remapper
  change, out of RG-018 scope). The generator auto-falls back to the address-map location if that fix
  lands.
- Cheat-XML address `0x05FFFD` vs the game's traced read address `0x05FF9F`: the implementation follows
  the game's traced stage-decode read (verified in §6). `0x05FFFD` appears to be a cheat-file anomaly.
