# Andy — RG-019: Subround Selection Correction (why RG-018 failed, and the real mechanism)

**Task:** RG-019 · **Agent:** Andy (Opus) · **Date:** 2026-10-24 · **New numbered build:** 0495
(`55b1cae50e685211…`). Supersedes the broken RG-018 selection.

## 1. What RG-018 got wrong

RG-018 (as tested by Tighe in BlastEm) patched the **relocated config byte** at Genesis `0x05FFE5`
(the address-map translation of arcade `0x05FF9F`, and the byte the invincible variant patches). All
variants still booted to Round 1, Subround 1.

**Root cause — inconsistent operand relocation.** Two different original instructions read the config
word at arcade `0x05FF9E`:
- The **startup/invincible** decoder (arcade `0x03AFEE`) — its absolute operand WAS relocated by the
  postpatcher, so on Genesis it reads `0x05FFE4` (where the config physically lives). That is why
  patching `0x05FFE5` affects the invincible bit.
- The **stage** decoder (arcade `0x04527E`/`0x04529C`) — its operand was **NOT** relocated. On Genesis
  (`0x45482`/`0x454A0`) it still reads the literal `0x05FF9E`/`0x05FF9F`, which reverse-maps to arcade
  `0x05FF58` — `0xFF` padding. So the stage decoder reads `0xFF` → Round 1, **ignoring** the `0x05FFE5`
  patch entirely.

So RG-018 patched a byte the stage decoder never reads. (RG-018's own MAME probe even reported Round 1
for `_S1-1`/`_S3-1`/`_S6-1`, which was the warning; it was wrongly deferred as "inconclusive.")

## 2. The MAME cheat's `0x05FFFD` is a red herring (proven on the arcade)

`tools/mame/cheat/output.xml` "Select Starting Round/Sub-Round" writes `maincpu.mb@05FFFD`. But
`0x05FFFD` is a byte **inside the difficulty-config lookup table** (`0x5FFCE–0x5FFFD`, indexed by the
config decoder at `0x5FFA2`/`0x5FFB2`), not a stage selector. ORIGINAL ARCADE MAME, patching the ROM
region and latching at first appearance (`state2==3`, `player_x==0x20`):

| Patch | round `0x10C118` | **stage index `0x10D242`** | result |
|---|---|---|---|
| none (baseline) | 01 | `0x0000` | R1 Outside |
| `0x05FFFD = 0xFA` (R6) | 01 | `0x0000` | **no change** — not the selector |
| `0x05FF9F = 0xFA` (R6) | 01 | `0x0073` | **R6** — this IS the selector |

So the cheat's address does nothing for stage selection; the real selector is arcade `0x05FF9F`. (The
round counter `0x10C118` stays `01` even on the arcade; the **stage index `0x10D242`** is the
authoritative result — RG-018's probe watched the wrong variable.)

## 3. The real mechanism

The original stage decoder (`0x04527E`/`0x04529C`) reads the packed selector byte at arcade `0x05FF9F`:

```
round      = (~byte & 7) + 1
stage index = (round-1)*23  + 22 if (bit 3 == 0, Boss)  + 16 if (bit 5 == 0, Castle)
```

stored at `a5@0x1242` (arcade `0x10D242`, Genesis `0x00FF1242`). Selector values (0xFF…0xF2) match the
MAME cheat items. On Genesis the decoder reads the **unrelocated literal `0x05FF9F`** (§1), which is
`0xFF` padding on the canonical ROM — so patching that exact byte feeds the decoder the selector.

## 4. The correction

`tools/translation/build_subround_variant.py` patches the byte the stage decoder actually reads — the
literal Genesis `0x05FF9F` — detecting the unrelocated `movew 0x5ff9e` read form in the ROM (with
fallback to the address-map location if a future build relocates the operand). One `0xFF`-padding byte
changes; canonical start is untouched; no teleport, no menu, no controller input, no runtime cheat. The
build commands and `_S<r>-<s>` naming are unchanged; variants share the parent build number.

This is the smallest permanent semantic override compatible with the architecture. The *proper*
long-term fix is to declare the stage decoder's operand for relocation in the semantic remapper so it
reads the same config (`0x05FFE4`) the startup does — a canonical-pipeline change out of RG-019 scope;
the generator auto-adapts if that lands.

## 5. Proof of actual selection (Genesis MAME, Build 0495)

`tools/mame/run_subround_functional_verify.sh` boots each variant, runs the normal credit/start, latches
the live **stage index `0x00FF1242`** at first appearance, and checks it equals the arcade-derived
expected index. **All 18 + canonical PASS**, each a distinct correct state (not all R1-S1):

| | S-1 Outside | S-2 Castle | S-3 Boss | | | S-1 | S-2 | S-3 |
|---|---|---|---|---|---|---|---|---|
| R1 | `0x00` | `0x10` | `0x16` | | R4 | `0x45` | `0x55` | `0x5B` |
| R2 | `0x17` | `0x27` | `0x2D` | | R5 | `0x5C` | `0x6C` | `0x72` |
| R3 | `0x2E` | `0x3E` | `0x44` | | R6 | `0x73` | `0x83` | `0x89` |

Canonical ROM = `0x00` (R1-S1, unchanged). Spawn `player_x` also varies by stage (e.g. R1 Boss `0x120`,
R6 Boss `0x58`), further confirming genuinely different stage initialization. MAME agreed with BlastEm
on the failing RG-018 build (both R1), so its agreement here that selection now works is credible.

**Scope caveat (unchanged):** this proves the correct subround is *selected and initialized*; it is NOT
a claim that every later stage is fully playable — later-stage graphics/enemies/scrolling may still be
incomplete. That is a separate gameplay limitation these ROMs exist to expose. **Tighe performs final
gameplay validation in BlastEm and on real Genesis hardware.**

## 6. Tooling and validation
- `build_subround_variant.py` / `verify_subround_variants.py` — generate + static-check (byte-level).
- `run_subround_functional_verify.sh` + `subround_start_probe.lua` — **functional** gameplay-init check
  (stage index at appearance); this is the gate that proves selection, replacing RG-018's misleading
  round-counter probe.
- `arcade_subround_cheat_probe.lua` — ORIGINAL ARCADE ground-truth probe used to establish §2–§3.
- `make -C apps/rastan-direct test-subround ROUND=r SUBROUND=s` / `test-subrounds` unchanged.

## 7. Preserved
Build 0492 accepted behavior, the seven-ROM release family, the native Z80 music system and all nine
Audio Composer arrangements, sound-command mappings, translated 68000 gameplay, and native graphics are
untouched. The canonical ROM still starts R1-S1 (verified §5). RG-019 only corrects the optional
subround-variant tooling.
