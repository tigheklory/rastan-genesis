# Summary
Implemented `bg_dirty` / `fg_dirty` guards in `rastan-direct` so full BG/FG nametable CPU copy loops run only when the corresponding plane is marked dirty.

# Exact File Modified
- `apps/rastan-direct/src/main_68k.s`

# Exact Symbols Added or Changed
- Added `.bss` flags:
  - `bg_dirty`
  - `fg_dirty`
- Updated `init_staging_state`:
  - `move.b #1, bg_dirty`
  - `move.b #1, fg_dirty`
- Updated `vdp_commit_bg`:
  - dirty test/skip guard around existing full-plane commit
  - `bg_dirty` clear after commit
- Updated `vdp_commit_fg`:
  - dirty test/skip guard around existing full-plane commit
  - `fg_dirty` clear after commit

# Classification
- `bg_dirty`: BRINGUP_ONLY
- `fg_dirty`: BRINGUP_ONLY

# Why This Change Is Required
The active VBlank path previously executed unconditional 2048-word BG and 2048-word FG CPU copies every frame, overrunning VBlank timing. Dirty guards align commit behavior with Rainbow Islands discipline by avoiding full-plane commits when no staged plane data changed.

# Why DMA Was NOT Introduced Here
This prompt required only dirty-flag gating as the immediate timing correction. DMA introduction was explicitly out of scope and not implemented.

# Removal / Follow-On Plan
Replace one-time bring-up dirty guards with producer-driven dirty setting once arcade tilemap hooks become active and authoritative staging updates exist per plane.

# Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

# Verification Status
- Build succeeded: YES
- BG commit executes only when dirty: YES
- FG commit executes only when dirty: YES
- Display visible: USER MUST VERIFY
- Checkerboard visible: USER MUST VERIFY
