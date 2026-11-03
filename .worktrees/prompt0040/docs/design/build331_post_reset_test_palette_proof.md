# Build 331 Post-Reset Test Palette Proof

## 1. Executive Summary
Build 331 injects a fixed, known-visible test palette immediately after `force_clean_vram_init()` in the launcher-to-game handoff path. This is a proof-only change to verify whether early post-reset black output is primarily due to CRAM being left black at reset.

## 2. Exact Post-Reset Injection Site
File: `apps/rastan/src/main.c`  
Function/path: `request_start_rastan()` immediately after:

```c
force_clean_vram_init();
```

Injected call:

```c
apply_post_reset_test_palette();
```

## 3. Test Palette Used
A static 16-color line of distinct visible colors is written and repeated across all 4 CRAM lines.

Write behavior:
- CRAM base command at `0xC0000000`
- auto-increment = 2
- 4 lines x 16 entries = 64 entries total

## 4. What Was Intentionally Left Unchanged
- `_VINT_arcade_mode` palette flow unchanged
- `genesistan_palette_commit_asm` unchanged
- CLCS capture logic unchanged
- bulk tilemap/scroll/sprite/text/sanitizer/input-debug logic unchanged

## 5. Why This Is Proof-Only
The test palette is a temporary visibility probe that runs once at handoff and is allowed to be overwritten later by normal runtime palette commits. It does not alter later runtime ownership or palette logic.

## 6. Build Verification
Build command:

```bash
source tools/setup_env.sh
make -C apps/rastan release
```

Result:
- Build succeeded
- Artifact: `dist/Rastan_331.bin`
- No new errors
- No new warnings (same 5 pre-existing warnings)

## 7. Expected Runtime Result
- Early post-reset period should show visible colors instead of pure black.
- Plane A/debug text may become visible earlier depending on tile content timing.
- Later runtime palette commits may overwrite the test palette.
- Later rolling/items presentation issue may still remain.

## 8. Final Verdict
Build 331 adds a single narrow post-reset CRAM proof injection to test early-black causality directly, while preserving all later arcade-owned palette behavior.
