# Cody - Build 0111 High-Score NAME Column Source/Destination Audit

**Date:** 2026-06-28
**Type:** Evidence / analysis only
**Build under audit:** Build 0111, `dist/rastan-direct/rastan_direct_video_test_build_0111.bin`, SHA256 `3e8977513586231bf83636ba9ce9b65852f2fe8f94f8772ad9fa7fa493442e23`
**Arcade baseline:** original `rastan` / Rastan arcade driver under MAME
**Scope:** NAME-column source/destination audit only. No source/spec/tool/Makefile/ROM/build changes. No bookmarks. No diagnostics inserted into ROM. No implementation or fix design.

## Phase 0

Read before work:

- `RULES.md`
- `ARCHITECTURE.md`
- latest `AGENTS_LOG.md` tail
- `docs/design/Andy_03C5FE_highscore_fg_staging_route_design.md`
- `docs/design/Cody_build0111_highscore_fg_producer_staging_route.md`
- `docs/design/Cody_build0109_highscore_03C5FE_raw_write_scope.md`

Classification: **EXTENDING** OPEN-018 / OPEN-001 evidence. OPEN-015 was not touched.

Architecture compliance: PASS. The arcade runtime establishes intent; Build 0111 is checked for whether its Genesis helper reads the mapped equivalent of the arcade source. This task is evidence-only.

Address discipline: code correlations use `build/rastan-direct/address_map.json`. No `+0x200` arithmetic is used as authority.

## Evidence Artifacts

New original-arcade runtime trace:

`states/traces/original_arcade_highscore_name_source_audit_20260628_115007/`

Files:

- `mame_arcade_highscore_name_source.cmd`
- `native_debug_trace.log`
- `mame_stdout.log`
- `mame_stderr.log`

Build 0111 comparison traces:

- `states/traces/build_0111_highscore_fg_producer_staging_route_20260628_105240/events_only.log`
- `states/traces/build_0111_highscore_fg_producer_staging_route_20260628_105240/route_analysis.md`
- `states/traces/build_0111_highscore_fg_producer_staging_cells_20260628_105419/` / `..._110247/` staged-cell confirmations

## JSON / Map Integrity Check

`specs/rastan_direct_remap.json` and `build/rastan-direct/address_map.json` both parse as valid JSON.

`specs/rastan_direct_remap.json` has exactly one `opcode_replace` entry for `arcade_pc 0x03C3FE`:

```json
{
  "arcade_pc": "0x03C3FE",
  "original_bytes": "3E3C000034000240",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_highscore_fg_producer}4E75"
}
```

`required_symbols` includes `genesistan_hook_highscore_fg_producer`. The generated symbol table resolves it at `runtime_genesis_pc 0x000707A0`.

Address map checks:

| Runtime Genesis PC | Kind | Arcade PC | Notes |
|---|---|---|---|
| `0x0003C5FE..0x0003C606` | `patched_site` | `0x0003C3FE..0x0003C406` | high-score producer entry wrapper |
| `0x0003C606..0x0003C6D2` | `arcade_copy` | `0x0003C406..0x0003C4D2` | preserved post-wrapper body/table region |
| `0x0003C654` | `arcade_copy` segment above | `0x0003C454` | descriptor table preserved |
| `0x0003B0EA` | `patched_site` | `0x0003AEEA` | redirects arcade work-RAM A0 base `0x10C000` to Genesis WRAM `0xFF0000` |
| `0x0003B104` | `patched_site` | `0x0003AF04` | redirects arcade A5 work-RAM base `0x10C000` to Genesis WRAM `0xFF0000` |

No malformed or missing mapping was found for the `0x03C5FE` site, preserved `0x03C606+` segment, descriptor table, or work-RAM base remap. The defect identified below is not JSON corruption; it is the helper's literal source base.

Important generated-policy finding: in `rastan-direct`, arcade work-RAM `0x0010C000` is mapped to Genesis WRAM `0x00FF0000` by generated opcode replacements. `apps/rastan-direct/out/symbol.txt` does **not** expose `genesistan_arcade_workram_words`; the direct build uses literal `0x00FF0000` as the mapped work-RAM base.

## Original Arcade NAME Column

The original arcade trace proves the NAME producer is the same producer family as Build 0111's routed helper:

- Producer entry: `arcade_pc 0x0003C3FE`
- Caller: `arcade_pc 0x0003B700`
- Descriptor table: `arcade_pc 0x0003C454`
- Attr writer: `arcade_pc 0x0003C42A`
- Code writer: `arcade_pc 0x0003C446`

At high-score screen entry, the original arcade work-RAM source bytes are:

| Row | Name | Arcade-RAM source | Bytes |
|---:|---|---|---|
| 0 | `COB` | `0x0010C157..0x0010C159` | `43 4F 42` |
| 1 | `THS` | `0x0010C15A..0x0010C15C` | `54 48 53` |
| 2 | `YAG` | `0x0010C15D..0x0010C15F` | `59 41 47` |
| 3 | `TKG` | `0x0010C160..0x0010C162` | `54 4B 47` |
| 4 | `YTN` | `0x0010C163..0x0010C165` | `59 54 4E` |

Trace anchor:

```text
EVENT CALL_03C3FE ... src0=434F42 src1=544853 src2=594147 src3=544B47 src4=59544E
```

The 15 emitted NAME code cells are:

| Row | Char | Arcade source | Code write HW_ADDRESS | Code |
|---:|---:|---|---|---:|
| 0 | 0 | `0x0010C157` | `0x00C09376` | `0x0043` (`C`) |
| 0 | 1 | `0x0010C158` | `0x00C0937A` | `0x004F` (`O`) |
| 0 | 2 | `0x0010C159` | `0x00C0937E` | `0x0042` (`B`) |
| 1 | 0 | `0x0010C15A` | `0x00C09576` | `0x0054` (`T`) |
| 1 | 1 | `0x0010C15B` | `0x00C0957A` | `0x0048` (`H`) |
| 1 | 2 | `0x0010C15C` | `0x00C0957E` | `0x0053` (`S`) |
| 2 | 0 | `0x0010C15D` | `0x00C09776` | `0x0059` (`Y`) |
| 2 | 1 | `0x0010C15E` | `0x00C0977A` | `0x0041` (`A`) |
| 2 | 2 | `0x0010C15F` | `0x00C0977E` | `0x0047` (`G`) |
| 3 | 0 | `0x0010C160` | `0x00C09976` | `0x0054` (`T`) |
| 3 | 1 | `0x0010C161` | `0x00C0997A` | `0x004B` (`K`) |
| 3 | 2 | `0x0010C162` | `0x00C0997E` | `0x0047` (`G`) |
| 4 | 0 | `0x0010C163` | `0x00C09B76` | `0x0059` (`Y`) |
| 4 | 1 | `0x0010C164` | `0x00C09B7A` | `0x0054` (`T`) |
| 4 | 2 | `0x0010C165` | `0x00C09B7E` | `0x004E` (`N`) |

Each row also writes attr word `0x0000` at `HW_ADDRESS` `0x00C09374/78/7C`, `0x00C09574/78/7C`, etc.

Destination cell decode for the attr/code pairs (`cell = (dest - 0x00C08000) >> 2`, 64 columns):

| Row | Dest attr base | FG row | FG columns |
|---:|---|---:|---|
| 0 | `0x00C09374` | `19` | `29..31` |
| 1 | `0x00C09574` | `21` | `29..31` |
| 2 | `0x00C09774` | `23` | `29..31` |
| 3 | `0x00C09974` | `25` | `29..31` |
| 4 | `0x00C09B74` | `27` | `29..31` |

Conclusion: the 15-cell equivalence gate covers the NAME cells, not SCORE or ROUND. The original arcade names are seeded and nonzero.

## Correct Mapped Genesis Equivalent

The NAME source is arcade work-RAM, not ROM data.

Source window:

- Arcade-RAM base: `0x0010C000`
- NAME source offsets: `0x0157..0x0165`
- Arcade-RAM source addresses: `0x0010C157..0x0010C165`

Direct-build mapping basis:

- `address_map.json` / spec entries at `arcade_pc 0x03AEEA` and `0x03AF04` redirect the arcade work-RAM base from `0x0010C000` to Genesis WRAM `0x00FF0000`.
- Therefore the correct Genesis mapped equivalent for the NAME source is `Genesis-WRAM 0x00FF0157..0x00FF0165`.

This is a stable mapped RAM window. It must not move because genesis-only helper code grew elsewhere.

## Build 0111 Actual Behavior

Build 0111's helper constant is:

```asm
.equ ARCADE_HIGHSCORE_SOURCE_BASE, 0x0010C068
...
adda.l #0x0010C068,%a2
```

The Build 0111 runtime trace confirms the helper reads from `0x0010C068 + src_off`, i.e. `0x0010C1BF..0x0010C1CD`, not the mapped work-RAM equivalent `0x00FF0157..0x00FF0165`.

Build 0111 actual source bytes read:

| Row | Build 0111 source addresses | Bytes read | Intended arcade bytes |
|---:|---|---|---|
| 0 | `0x0010C1BF..0x0010C1C1` | `18 01 34` | `43 4F 42` (`COB`) |
| 1 | `0x0010C1C2..0x0010C1C4` | `66 84 00` | `54 48 53` (`THS`) |
| 2 | `0x0010C1C5..0x0010C1C7` | `13 18 46` | `59 41 47` (`YAG`) |
| 3 | `0x0010C1C8..0x0010C1CA` | `00 01 34` | `54 4B 47` (`TKG`) |
| 4 | `0x0010C1CB..0x0010C1CD` | `14 00 00` | `59 54 4E` (`YTN`) |

Trace anchors:

```text
EVENT HOOK_STAGE_CALL_707F8 ... dest_a1=00C09374 src_next_a2=0010C1C0 src_byte=18 code_d0=0018
EVENT HOOK_STAGE_CALL_707F8 ... dest_a1=00C09574 src_next_a2=0010C1C3 src_byte=66 code_d0=0066
EVENT HOOK_STAGE_CALL_707F8 ... dest_a1=00C09B7C src_next_a2=0010C1CE src_byte=00 code_d0=0000
```

`src_next_a2` is logged after the byte read, so the first read address is one less (`0x0010C1BF`).

Build 0111 does **not** read the mapped Genesis equivalent. It reads the literal `0x0010C068 + src_off`.

## Assessment of `0x0010C068`

`0x0010C068` is not a real mapped relocation for the high-score NAME source in Build 0111.

Evidence:

- The original arcade producer adds `0x0010C000` because that is arcade work-RAM.
- The direct Genesis build remaps that arcade work-RAM base to Genesis WRAM `0x00FF0000`.
- `0x0010C068` is neither the arcade work-RAM base nor the generated Genesis work-RAM mapped base.
- The `+0x68` matches the helper-growth compensation described in the Build 0111 implementation note, not an address-map segment or symbol.
- The helper reads from a stable data/RAM source as if it were a shifting code/ROM-layout source.

Therefore the `+0x68` correction was a Genesis-to-Genesis output-matching workaround, not arcade-fidelity mapping. It explains why NAME tiles are unstable between Build 0110 and Build 0111: the bytes are being read from a layout-sensitive literal region instead of stable mapped work-RAM.

## Classification

**A - 0x03C5FE HOOK SOURCE-BASE WRONG.**

The NAME cells are produced by the same `0x03C3FE` / `0x03C5FE` producer, and the 15-cell gate does cover the NAME cells. The source is arcade work-RAM. Build 0111 reads from a layout-shifted literal (`0x0010C068 + src_off`) instead of the correct mapped Genesis work-RAM equivalent (`0x00FF0000 + src_off`).

Not B: not a different producer; original arcade runtime proves the producer is `arcade_pc 0x03C3FE`.

Not C: not stale/uncleared cells for the captured NAME writes; Build 0111 actively writes the NAME destinations from wrong bytes.

Not D: not primarily LUT/tile interpretation; the source codes entering staging differ from original arcade before LUT mapping.

Not E: not genuinely unseeded for original arcade intent; original arcade has seeded names `COB/THS/YAG/TKG/YTN` at the source addresses.

## Recommendation (Scoping Only)

Future fix scope should change only the source-base used by `genesistan_hook_highscore_fg_producer` to the mapped work-RAM base for this direct build (`Genesis-WRAM 0x00FF0000`, or a project-approved work-RAM symbol if one is introduced for `rastan-direct`). The source expression should be mapped/symbolic, not a literal `0x0010C000` or `0x0010C068` that can drift with code layout.

Do not seed high-score defaults in this task. Do not change score/round zero handling in this task. Do not touch the write-routing logic unless the source-base fix is explicitly authorized later.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018: touched/extended. Build 0111's write routing works structurally but reads the wrong NAME source base.
- OPEN-001: context; high-score NAME corruption source is now classified.
- OPEN-015: not touched.
- Issues opened/closed: none.
- `KNOWN_FINDINGS.md`: no update in this evidence-only task. A future canonical update may be warranted after the source-base fix is implemented/verified.

## STOP

STOP triggered: NO. The classification is resolved without code changes.
