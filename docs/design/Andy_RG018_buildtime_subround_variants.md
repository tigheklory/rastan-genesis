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

**Genesis equivalent:** arcade `0x05FF9F` maps through the maintained address map
(`build/rastan-direct/address_map.json`, whole-maincpu copy, +0x200) to **Genesis ROM offset
`0x05FFE5`**. The accepted invincible variant already patches this exact byte (`0xFF → 0xBF`), proving
the Genesis build reads it and that a single-byte patch there is effective and is never overwritten.

## 2. Implementation (smallest build-time semantic override)

`tools/translation/build_subround_variant.py` copies the parent canonical ROM and patches the one
relocated selector byte (looked up via the address map, not hard-coded) with the derived selector. It
refuses to patch a parent whose byte is not the default `0xFF`, and asserts only that byte changes
(Round 1 Outside = `0xFF` = default → a byte-identical variant, which is correct). This patches the
original startup selection mechanism — no new gameplay code, no teleport; the chosen subround
initializes through the game's own stage decode.

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
- Arcade `0x05FF9F` → Genesis `0x05FFE5` resolves via the address map; canonical byte is the default `0xFF`.
- Every variant changes only `0x05FFE5` to the correct value (R1-1 byte-identical to canonical).
- No other byte of the canonical ROM is modified; all 18 generated; correct names + shared build number.
- Invalid round/subround inputs rejected; derivation is deterministic.

Confirmed operationally: parent build number stayed 0494 (no number consumed); canonical SHA unchanged;
`release → dual-build` does not reference the subround targets.

## 6. Stage-init observation (diagnostic, NOT a playability claim)

`tools/mame/scripts/subround_start_probe.lua` boots a variant on **GENESIS NTSC**, runs the normal
coin/start sequence, and samples the decoded round (`a5@0x118`) and stage index (`a5@0x1242`).

**Result: inconclusive by automation.** For every probed variant (S1-1, S3-1, S6-1) the sampled round
read 1 and the stage index read 0 within 300–1500 frames — including the stage index being 0 for R1,
where the decode would yield 23. That means the probe is not sampling the stage-select decode's effect
(wrong location for the Genesis port, or the decode path — gated by `a5@0x104` at `0x45288`/`0x452BA` —
is not exercised on the current start), **not** that the patch is wrong. The selector byte is verified
correct per §1 and the invincible-variant precedent. Per the task, this is an area where automated
Genesis observation is not capable, so **stage playability is deferred to Tighe's BlastEm / real
hardware validation**. These ROMs are a mechanism to expose incomplete later-stage functionality; a
correctly generated ROM and selector value is **not** a claim that the later stage is playable.

Where useful, compare against ORIGINAL ARCADE MAME with the equivalent level-select cheat.

## 7. Scaffolding and scope

- No new gameplay code, no NOP/RTS, no production ROM scaffolding. The variants are single-byte patches
  of the canonical ROM at the original selector location.
- New durable tooling (retain): `build_subround_variant.py`, `verify_subround_variants.py`,
  `subround_start_probe.lua`, and the `test-subround`/`test-subrounds` Makefile targets.
- RG-018 did not attempt to repair later rounds; it only adds the build-time selection infrastructure.
- Preserved: Build 0492 accepted behavior, all native audio and nine Composer arrangements, the
  sound-command mappings, death/respawn/GAME OVER, the seven-ROM release, and native VDP work. The
  variants use the normal gameplay music-selection mechanism (no Z80 engine change, no hardcoded music).

## 8. Open items
- The automated stage-init probe is inconclusive; Tighe's BlastEm/hardware check will confirm whether
  each selected subround actually loads, and will expose which later stages are incomplete.
- Cheat-XML address `0x05FFFD` vs the game's traced read address `0x05FF9F`: the implementation follows
  the game's read address (verified); if `0x05FFFD` turns out to drive selection in some path, that is a
  follow-up, but the invincible variant confirms `0x05FF9F`/`0x05FFE5` is the live, read, patchable byte.
