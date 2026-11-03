# Cody Remove FG Full-Plane Commit

## 1. Summary
Removed the obsolete FG full-plane VBlank publish path from `rastan-direct` to eliminate a bring-up-only Plane A full upload that has no valid use case in the current baseline.

## 2. Root cause reference (Andy report)
Reference: `docs/design/Andy_vblank_efficiency_audit_and_transition_plan.md`.

## 3. Exact file modified
- `apps/rastan-direct/src/main_68k.s`

## 4. Exact symbols removed
- `_VINT_handler` call site: `bsr     vdp_commit_fg`
- Function removed: `vdp_commit_fg`
- `.bss` symbol removed: `fg_dirty`
- `init_staging_state` line removed: `move.b  #1, fg_dirty`

## 5. Classification
- `vdp_commit_fg`: BRINGUP_ONLY / architecturally invalid path removed
- `fg_dirty`: BRINGUP_ONLY removed

## 6. Why FG full-plane commit was wrong
The FG plane is fully transparent in the current baseline, so performing a full 2048-word Plane A upload every VBlank is unnecessary overhead and not aligned with the Rainbow Islands commit discipline.

## 7. Why removal is safe
FG transparency is preserved by the existing FG buffer clear path, and no remaining logic depends on `vdp_commit_fg` or `fg_dirty` for visible output in this baseline.

## 8. What remains for future FG support
`staged_fg_buffer` remains allocated and available for future arcade-driven strip-level FG updates committed through a later correct path.

## 9. Verification expectations
- Checkerboard baseline remains stable.
- Visible output remains unchanged except the obsolete FG publish path is absent.
- Blue top-band artifact does not return.

## 10. Next-step impact toward Rainbow Islands alignment
This removal reduces unnecessary frame-1 VBlank cost and moves `rastan-direct` closer to Rainbow Islands-style commit ownership by removing a non-arcade-equivalent full-plane FG publish stage.
