# Build 329 Force Plane A Only Display Proof

## 1. Executive Summary
Build 329 applies one temporary proof-only suppression to remove non-Plane-A sprite visibility so we can verify whether Plane A content is the correct final visible render path.

## 2. Method Used to Suppress Non-Plane-A Output
Method: early return in the sprite renderer entrypoint `genesistan_render_sprites_vdp_asm` in `apps/rastan/src/startup_trampoline.s`.

Change applied:

```asm
genesistan_render_sprites_vdp_asm:
    /* Build 329 proof-only: suppress sprite-layer output to isolate Plane A visibility. */
    rts
```

This suppresses sprite SAT/tile submission by exiting before sprite pass execution.

## 3. What Was Intentionally Left Unchanged
- `genesistan_debug_fg_proof()` unchanged
- `genesistan_pc080sn_commit_planes` Plane A path unchanged
- FG buffer generation unchanged
- tile lookup/sanitizer/dereference instrumentation unchanged
- window/palette/scroll logic unchanged

## 4. Why This Is Proof-Only
The change is intentionally narrow and temporary. It does not attempt to fix sprite logic or crash/root-cause paths. It isolates visible output ownership by removing sprite-layer contribution only.

## 5. Build Verification
Build command:

```bash
source tools/setup_env.sh
make -C apps/rastan release
```

Build output:
- Build succeeded
- Artifact: `dist/Rastan_329.bin`
- No new errors
- No new warnings (same 5 pre-existing warnings)

## 6. Expected Runtime Result
- rolling dots suppressed (expected)
- Plane A debug text visible on actual screen (expected)
- crash may still occur (possible)

## 7. Final Verdict
Build 329 now provides a Plane-A-only visibility proof condition by suppressing sprite output via a single renderer entrypoint change, with Plane A and debug paths left intact.
