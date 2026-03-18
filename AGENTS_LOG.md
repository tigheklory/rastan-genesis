# AGENTS Log

## [2026-03-18] Build 87 - I/O Mapping Phase


### MAME Exit Summary (2026-03-18 11:48:20)
- Final PC: 0x2001CA
- Stack Pointer (SP): 0xE0FFFF40
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031

### MAME Exit Summary (2026-03-18 11:48:38)
- Final PC: 0x2145A0
- Stack Pointer (SP): 0xE0FFFF5C
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031

### MAME Exit Summary (2026-03-18 12:10:22)
- Final PC: 0x214736
- Stack Pointer (SP): 0xE0FFFF5C
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031


## [Supervisor - Tighe]

Visual Result: [Launcher works, In game play shows text from the title screen but it is all at the top few lines and overtop of each other and wrong colors]

Platform: [Tested on MAME and Blastem]

## [Supervisor - Tighe] Manual Evidence Log
- **Visual Evidence (MAME):** Screenshot saved as `B87_mame_launcher_20260318_1215.png` (Stage: Launcher)
- **Visual Evidence (MAME):** Screenshot saved as `B87_mame_ingame_20260318_1216.png` (Stage: In-Game)
- **Visual Evidence (BlastEm):** Screenshot saved as `B87_blastem_launcher_20260318_1220.png` (Stage: Launcher)
- **Visual Evidence (BlastEm):** Screenshot saved as `B87_blastem_ingame_20260318_1221.png` (Stage: In-Game)

## [Architect Review - Build 88 Technical Audit]

### 1. Aliasing Audit
**Confirmed.**
The spec `specs/startup_title_remap.json` currently maps `0xC00000`, `0xC04000`, `0xC08000`, and `0xC0C000` to the single symbol `genesistan_shadow_c_window_words`.
This results in a 4-to-1 aliasing where writes to distinct arcade video pages overwrite the same Genesis shadow buffer index. This explains the garbled title screen text (text overwriting background or vice versa).

### 2. Fault Analysis (0xD000DA)
**Confirmed Unmapped Literal.**
The address `0xD000DA` is missing from the `absolute_rewrite_groups` in the current spec.
Since `allow_in_code` is disabled for safety (Decision 2026-03-17), this absolute address literal in the code is not being rewritten.
Accessing `0xD000DA` on Genesis (unmapped space) causes the observed crash/freeze.

### 3. Mitigation Strategy
1.  **Split C-Window Shadows**: Define four separate 16KB shadow buffers in `apps/rastan/src/main.c`.
2.  **Remap Pages**: Update `specs/startup_title_remap.json` to map each 0xC0xxxx page to its own unique shadow symbol.
3.  **Patch D000DA**: Add `0xD000DA` to the explicit D-window absolute remap group targeting `genesistan_shadow_d00000_words` (offset 218).

## [Implementer Update - Build 88]

### Fixes Implemented
- Confirmed: `specs/startup_title_remap.json` now decouples prior 4-to-1 C-window aliasing with distinct mappings:
  - `0x00C00000 -> genesistan_shadow_c00000_words`
  - `0x00C04000 -> genesistan_shadow_c04000_words`
  - `0x00C08000 -> genesistan_shadow_c08000_words`
  - `0x00C0C000 -> genesistan_shadow_c0c000_words`
- Confirmed: `0x00D000DA` is mapped in D-window group to `genesistan_shadow_d00000_words` with `offset: 218`.

### Build Blocker
- Current state is `LINKER FAILURE` due to WRAM exhaustion.
- Cause: addition of 4 x 16KB volatile C-window shadow buffers (64KB total) pushes `.bss` past Genesis WRAM capacity (`$E00000-$FFFFFF`).
- Reported linker error: `.bss exceeds ram region at 0xE100BECC`.

### Integrity Check
- Confirmed unshifted arcade code offsets in spec:
  - `0x03AE86`
  - `0x039F80`
  - `0x03B098`

### Final Status
- Build 88: `Logic Complete / Memory Blocked`.
