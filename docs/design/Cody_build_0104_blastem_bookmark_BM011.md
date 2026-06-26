# Cody - Build 0104 BlastEm Bookmark BM-011

**Date:** 2026-06-25
**Type:** Hybrid verification + diagnostic bisection
**Build context:** Build 0102 -> 0103 -> 0104, `rastan-direct`
**Scope:** Revert BM-010, re-audit interval `runtime_genesis_pc 0x70000..0x70C36`, insert one BM-011 bookmark. No HV fix, no sanitizer, no VDP rewrite, no display-origin/title/exception work.

## Phase 0 Baseline

Classification: **EXTENDING** (OPEN-017 diagnostic bisection). Relevant priors: KF-004/KF-006 address discipline as context; OPEN-017 active for BlastEm/Nomad behavior; OPEN-005 HV-counter historical context; OPEN-001 rendering context; OPEN-015 not touched. HIGH-hazard findings touched: none contradicted. Deferred appendix: none directly relevant. Contradiction of CONFIRMED/STRONG finding: **NONE**. STOP triggered in Phase 0: **NO**.

Architecture compliance: **CONFIRMED**. Bookmark activators are Rule 10 diagnostic exceptions only. No production Genesis-owned loop or lifecycle was added; no fix was attempted.

Confirmed user evidence consumed:

- BM-008 at `runtime_genesis_pc 0x00070000`: HIT in BlastEm, parked at helper `0x00071EB4`, no HV fatal first.
- BM-009 at `runtime_genesis_pc 0x0007186C`: MISS in BlastEm, `Illegal write to HV Counter port 8` before bookmark.
- BM-010 at `runtime_genesis_pc 0x00070C36`: MISS in BlastEm, `Illegal write to HV Counter port 8` before bookmark.
- Resulting bracket: `0x00070000 < offending HV access < 0x00070C36`.

## Build 0103 - BM-010 Revert

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release BOOKMARK_REVERT=BM-010
```

Result: **PASS**.

- Build: `0103`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0103.bin`
- SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Canonical Build 0097/0099/0101 SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Byte-identical comparison with Build 0097: PASS (`cmp = 0`)
- Active bookmark state after revert: absent (`build/rastan-direct/active_bookmark_baseline.json` deleted)
- Restored bytes at `0x00070C36`: `2449d4fc0002`
- Helper bytes at `0x00071EB4`: `60fe`

## Re-Focused Static Audit: `0x70000..0x70C36`

Address-map segment for interval targets: `build/rastan-direct/address_map.json` maps `0x070000..0x17CD28` as `genesis_only`, tag `wrapper`. No arcade equivalent is claimed for BM-011.

### Computed/Register-Indirect Candidates To `HW 0x00C00008`

**Strong computed/register-indirect candidate:** NONE FOUND. The bisection remains the oracle.

The narrowed interval was reviewed with special attention to the VDP register/init/commit cluster:

| runtime_genesis_pc | Instruction / path | EA reasoning | Candidate verdict |
|---|---|---|---|
| `0x70088` | `movew %d2,0xc00004` | Absolute VDP control-port register write in `vdp_set_reg`; target is `HW 0xC00004`, not offset 8. | Not HV-offset candidate |
| `0x700AE` | `movel %d1,0xc00004` | Absolute VDP control-port address setup; target is `HW 0xC00004`, not offset 8. | Not HV-offset candidate |
| `0x70122`, `0x70160`, `0x701AE`, `0x701E4` | `movew %a0@+,0xc00000` | Absolute VDP data-port commits from WRAM staging; target is `HW 0xC00000`, not offset 8. | Not HV-offset candidate |
| `0x70204`, `0x70214`, `0x7022C`, `0x7023A` | `movew %d0,0xc00000` | Absolute VDP data-port scroll writes; target is `HW 0xC00000`, not offset 8. | Not HV-offset candidate |
| `0x7021A` | `movel #0x40000010,0xc00004` | Absolute VDP control-port setup for VSRAM/scroll; target is `HW 0xC00004`, not offset 8. | Not HV-offset candidate |
| `0x70242..0x70C36` | BG/FG staging/helper region begins | Subsequent helpers perform PC080SN range checks and WRAM staging writes. This region is after BM-011 target and remains outside the pre-BM-011 cluster if BM-011 MISSes. | Not pre-target candidate |

The audit did not identify a visible literal or register-indirect write that proves `HW 0x00C00008`. Because BlastEm reports an HV-port write before BM-010, the next useful evidence is the BM-011 bisection at the boundary after this high-suspicion cluster.

## Build 0104 - BM-011 Insert

BM-011 target:

- `runtime_genesis_pc`: `0x00070244`
- `genesis_rom_offset`: `0x00070244`
- Symbol: `genesistan_hook_tilemap_plane_a`
- JSON segment: `genesis_only`, `0x070000..0x17CD28`, tag `wrapper`
- Arcade equivalent: none; native Genesis helper/wrapper code.
- Original bytes: `48e7fffe4bf900ff0000`
- Original instructions: `movem.l %d0-%fp,-(%sp)`; `lea 0xff0000,%a5`
- Reason: first safe complete-instruction/function boundary after the VDP register/init/commit cluster. The exact `0x70240` post-cluster boundary is only a 2-byte `rts`; it cannot safely host a 6-byte long-jump activator without corrupting the following helper entry.

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build: `0104`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0104.bin`
- SHA256: `109e0af71de8dcd3e2ee391b5da0b7d71824af4089113182b073b1919bd9ab91`
- Helper symbol: `genesistan_diag_bookmark`
- Helper runtime address: `0x00071EB4`
- Helper bytes: `60fe`
- Activator bytes at `0x00070244`: `4ef900071eb44e714e71`
- Active bookmark state: present, cycle `BM-011`, pre-insert counter `103`
- One-bookmark max: honored; BM-010 was reverted before BM-011 was inserted.

Bookmark-stage invariant model:

- `bookmarks_v2` activator applied by bookmark stage, outside opcode_replace segment coverage accounting.
- `opcode_replace` patched-site count: `96` (canonical)
- `total_genesis_bytes_covered`: `0x17CD28` (canonical)
- Patch counts: `{'opcode_replace_and_rom_opcode_replace': 96}`

Note: a padding word at `0x70242` can make linear objdump render the activator bytes oddly if disassembly starts at `0x70242`. Raw ROM bytes confirm the activator starts exactly at `0x70244`.

## User Test Instructions

Run Build 0104 in BlastEm:

```text
b 0x71EB4
c
```

- HIT: breakpoint hits `0x71EB4` / `bra #-2`, no HV fatal first. New interval: `(0x70244, 0x70C36)`.
- MISS: BlastEm emits `Illegal write to HV Counter port 8` before the breakpoint. New interval: `(0x70000, 0x70244)`, pinning the fault inside the VDP register/init/commit cluster.

Do not use `p/x $pc` as the authoritative PC; use the breakpoint/disassembly line if exposed. If MISS, report the exact fatal text.

## Rule 10

Build 0104 is diagnostic-only. The immediate next ROM-producing task must revert BM-011 unless Tighe explicitly directs otherwise.

## Non-Actions

No HV fix, no illegal-port sanitizer, no VDP rewrite, no display-origin/title work, no exception/OPEN-015 work, no red-TAITO/SCORE-HUD/CREDIT work.

## OPEN / KNOWN_FINDINGS Impact

- Open issues touched: OPEN-017 (active), OPEN-005 (context), OPEN-001 (context), OPEN-015 (not touched)
- New issues opened: NONE
- Issues closed: NONE
- KNOWN_FINDINGS impact: Option A - no new finding to index; this is diagnostic bisection and root cause is not proven.

## STOP

STOP triggered: **NO**.
