# Summary
Applied the single-line Plane B base register correction in `rastan-direct` so Plane B points to VRAM `0xC000` instead of `0xE000`.

# Exact Files Modified
- `apps/rastan-direct/src/main_68k.s`
- `docs/design/Cody_plane_b_base_fix.md`
- `AGENTS_LOG.md`

# Exact Symbols / Functions / Labels Added or Changed
- `vdp_boot_setup`
  - changed Plane B register value write from `0x07` to `0x06`

# Permanent vs Temporary Classification
- PERMANENT:
  - Plane B base register correction in `vdp_boot_setup` (`0x07` -> `0x06`)
- TEMPORARY:
  - none
- DIAGNOSTIC:
  - none
- BRINGUP_ONLY:
  - none

# Why This Change Was Made
Andy’s audit identified a direct mismatch: Plane B commit writes were targeting VRAM `0xC000`, while VDP register 4 configured Plane B display base as `0xE000`. This one-line correction aligns displayed Plane B base with the active BG commit destination.

# Scaffolding Inventory
- No new scaffolding added.

# Removal / Revert Plan
- No planned removal; this is a permanent correction.
- Revert method if needed: restore `moveq #0x07, %d1` in `vdp_boot_setup`.

# Build Artifact Path
- Build produced: YES
- Artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`

# Verification Status
- Source change applied: YES
- Build succeeded: YES
- BG visible: USER MUST VERIFY
- Palette still correct: USER MUST VERIFY

# Risks / Known Limitations
- Verification in this environment is build/headless only; on-screen visual confirmation remains user-side.
