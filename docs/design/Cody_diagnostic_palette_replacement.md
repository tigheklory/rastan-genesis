# Summary
Replaced the bring-up palette table in `rastan-direct` with a fully diagnostic, high-contrast palette to make CRAM visibility falsifiable on-screen.

# Exact File Modified
- `apps/rastan-direct/src/main_68k.s`

# Exact Palette Entries Changed
- `palette_init_words` replaced.
- Palette 0 entry 0 kept as `0x0000`.
- Palette 0 entry 7 changed from `0x0EEE` to `0x020C`.
- Entries 8–15 of palette 0 replaced with distinct, non-zero, non-white values.
- Entries 8–15 of palette lines 1–3 replaced with distinct, non-zero, non-white values.
- Zero-filled diagnostic-hostile entries previously present in entries 8–15 across all four lines were removed.

# Classification
- DIAGNOSTIC

# Why the Old Palette Was Non-Falsifiable
The prior table contained `0x0EEE` at palette 0 entry 7 (matching common white power-on appearance) and large zero-filled ranges in entries 8–15, making white/blank-looking output ambiguous and weak for CRAM visibility diagnosis.

# Why the New Palette Is Diagnostic-Friendly
The new table uses high-contrast non-white values across all lines, with explicit non-zero replacements for previously zero-filled ranges, so white-dominant output becomes a strong negative signal and colored output becomes a strong positive CRAM-visibility signal.

# Scaffolding Inventory
1. DIAGNOSTIC
- exact file: `apps/rastan-direct/src/main_68k.s`
- exact symbol/function/label: `palette_init_words`
- purpose: maximize palette observability for CRAM/path validation
- why it exists: reduce ambiguity in palette bring-up diagnostics
- how it is triggered: loaded in `init_staging_state`, committed when `palette_dirty` is set
- future condition allows removal: real arcade-authored palette pipeline replaces bring-up diagnostic palette
- exact removal method: replace `palette_init_words` with production-intent palette source values

# Removal / Revert Plan
- Replace diagnostic `palette_init_words` contents with production-intent palette data when palette pipeline validation is complete.
- Revert method: restore previous palette table values from git history if needed for comparison testing.

# Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

# Verification Status
- Build produced: YES
- Palette 0 entry 7 replaced with `0x020C`: YES
- Zero-filled diagnostic-hostile entries replaced: YES
- Display no longer all-white: USER MUST VERIFY
- Colored output visible: USER MUST VERIFY
