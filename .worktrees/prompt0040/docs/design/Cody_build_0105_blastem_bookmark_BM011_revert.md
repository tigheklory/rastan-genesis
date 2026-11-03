# Cody - Build 0105 BlastEm Bookmark BM-011 Revert

**Date:** 2026-06-25
**Type:** Bookmark revert only
**Build context:** Build 0104 -> 0105, `rastan-direct`
**Scope:** Revert BM-011 only. No new bookmark, no HV fix, no sanitizer, no VDP rewrite, no display-origin/title/exception work.

## Phase 0 Baseline

Classification: **EXTENDING** (OPEN-017 diagnostic bisection cleanup). OPEN-005 and OPEN-001 are context only. OPEN-015 is not touched. Architecture compliance: **CONFIRMED**; this task only removes the sanctioned Rule 10 diagnostic activator and restores a clean canonical ROM.

Confirmed user result consumed: Build 0104 / BM-011 at `runtime_genesis_pc 0x00070244` MISSed in BlastEm. BlastEm emitted `Illegal write to HV Counter port 8` before the bookmark. Current crash interval is `0x00070000 < offending HV access < 0x00070244`, pinning the fault inside the VDP boot/register/init/commit cluster. No fix was authorized.

## Build 0105 - BM-011 Revert

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release BOOKMARK_REVERT=BM-011
```

Result: **PASS**.

- Build: `0105`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0105.bin`
- SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Canonical Build 0097/0099/0101/0103 SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Byte-identical comparison with Build 0097: PASS (`cmp = 0`)
- Active bookmark state after revert: absent (`build/rastan-direct/active_bookmark_baseline.json` deleted)
- `bookmarks_v2` after revert: absent
- Restored bytes at `0x00070244`: `48e7fffe4bf900ff0000`
- Helper bytes at `0x00071EB4`: `60fe`

## Invariants

- `opcode_replace` patched-site count: `96`
- `total_genesis_bytes_covered`: `0x17CD28`
- Patch counts: `{'opcode_replace_and_rom_opcode_replace': 96}`

## Non-Actions

No new bookmark was inserted. No HV fix, sanitizer, VDP rewrite, display-origin/title work, exception work, or OPEN-015 work was performed.

## OPEN / KNOWN_FINDINGS Impact

- Open issues touched: OPEN-017 (active), OPEN-005 (context), OPEN-001 (context), OPEN-015 (not touched)
- New issues opened: NONE
- Issues closed: NONE
- KNOWN_FINDINGS impact: Option A - no new finding to index; this was Rule 10 cleanup only.

## STOP

STOP triggered: **NO**.
