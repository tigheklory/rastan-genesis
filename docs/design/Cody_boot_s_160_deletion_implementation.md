# Cody — boot.s:160 Deletion Implementation (Build 0052)

Date: 2026-04-22  
Task type: Implementation + verification  
Scope: single-line source deletion in `apps/rastan-direct/src/boot/boot.s`

## Required Reading Confirmation
- `RULES.md`: read
- `ARCHITECTURE.md`: read
- `AGENTS_LOG.md` (latest entries): read
- `docs/design/Andy_interrupt_enable_timing.md`: read
- `docs/design/Andy_boot_s_160_deletion_viability.md`: read
- `docs/design/Cody_a5_2c_seed_check.md`: read
- `docs/design/Cody_seed_clear_ordering_trace.md`: read
- `apps/rastan-direct/src/boot/boot.s`: read

## Phase 1 — Mechanical Edit

Edit applied in `apps/rastan-direct/src/boot/boot.s`:
- Deleted exactly one line: `move.w  #0x2000, %sr` (previously line 160)
- No replacement instruction inserted
- No comment insertion at deleted site
- No formatting changes outside the deleted line

Post-edit `_bootstrap`:
```asm
_bootstrap:
    jsr     vdp_boot_setup
    bsr     _bootstrap_clear_staging
    moveq   #0, %d0
    jsr     load_scene_tiles
    lea     0x00FF0000, %a5
    jmp     (0x00003A200).l
```

Source diff:
```diff
@@ -157,7 +157,6 @@ _bootstrap:
     moveq   #0, %d0
     jsr     load_scene_tiles
     lea     0x00FF0000, %a5
-    move.w  #0x2000, %sr
     jmp     (0x00003A200).l
```

## Phase 2 — Rebuild

Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Build result: PASS  
New ROM path: `dist/rastan-direct/rastan_direct_video_test_build_0052.bin`  
New ROM SHA-256: `935afce5ba3a1ef68e96d3472531d8c00593f478974dd24adbf1e0d397dc6030`  
Prior Build 0051 SHA-256: `f9e1232fc98113a5f2aa106ff07727559d5d096dd7e73cff541c6219aa32ae52`  
New SHA differs from Build 0051: YES

## Phase 3 — Static Post-Build Verification

### 1) Source check
- Deletion confirmed in source:
  - [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s):160 now `jmp (0x00003A200).l`
  - No `move.w #0x2000, %sr` remains in `_bootstrap`

### 2) Binary check in Genesis-side `_bootstrap` region
Checked ROM bytes from offset `0x00000200` through `0x0000025F`:
- Pattern `46 FC 20 00` (`move.w #0x2000, %sr`) present in Genesis-side `_bootstrap` region: NO
- Pattern `4E F9 00 03 A2 00` (`jmp 0x0003A200`) present: YES (at region offset `0x3E`, absolute ROM offset `0x23E`)

Region hexdump excerpt:
```text
00000230: 70 00 4e b9 00 07 11 b0 4b f9 00 ff 00 00 4e f9
00000240: 00 03 a2 00 ...
```

### 3) Handoff check
- `_bootstrap` handoff intact: YES (`jmp (0x00003A200).l` still present)

### 4) File-modification scope
- Source/spec/tool modifications beyond allowed scope: NO
- Only source file changed by this implementation: `apps/rastan-direct/src/boot/boot.s`

## Phase 4 — Runtime Verification A (Arcade Enable Ownership)

ROM: `dist/rastan-direct/rastan_direct_video_test_build_0052.bin`  
Debugger: MAME native internal debugger (`-debug -debugger qt`)  
Lua: NO

Breakpoint:
- `BP_ARCADE_ENABLE` target runtime_genesis_pc `0x0003B27A` (= arcade_pc `0x03B07A`)

Capture result:
- Hit: YES
- Cycle at hit: `3158242`
- Observed runtime_genesis_pc: `0x0003B27C` (prefetch offset)
- SR before instruction: `0x2700`
- A5 at hit: `0x00FF0000`

Trace evidence around hit:
```text
PRE cyc=3158242 pc=03B27C sr=2700 ...
03B27A: andi    #$f0ff, SR
(interrupted at 03B27E, IRQ 6)
```

SR after instruction:
- Runtime first-hit flow takes IRQ6 immediately after `andi.w #0xF0FF,%sr`, so no direct pre-IRQ post-instruction SR sample exists on that exact first hit line.
- Independent direct probe at post-instruction PC (`runtime_genesis_pc 0x0003B27E`) captured `sr=2000`, confirming IMASK clear at arcade site.

## Phase 5 — Runtime Verification B (CLEAR before first SEED)

Breakpoints:
- `BP_SEED`: runtime_genesis_pc `0x0003ADD0` (= arcade_pc `0x03ABD0`)
- `BP_CLEAR`: runtime_genesis_pc `0x0003B0FC` (= arcade_pc `0x03AEFC`)
- Watchpoint: write-watch on `HW_ADDRESS 0x00FF002C` (word)

Results:
- First SEED cycle: `3692403` (BP hit)
- First CLEAR cycle: `1491088` (trace pass at runtime `0x0003B0FC`, arcade `0x03AEFC`)
- First to occur: CLEAR
- `BP_CLEAR` breakpoint event: not emitted (target is prefetch-aligned, not instruction-start), but trace pass is present and used as required by spec (`event or trace pass`).
- Write history for `0x00FF002C` captured: YES

Write-watchpoint note:
- MAME watchpoint fields here report `old=<wpdata>` and `new=<w@addr-before>` (reversed vs semantic names).
- Interpreted write transitions are therefore `before = logged new`, `after = logged old`.

Key writes (interpreted):
1. Cycle `1491642`, writer observed arcade_pc `0x03AF02` (CLEAR loop tail): `0x0000 -> 0x0000`
2. Cycle `3692403`, writer observed arcade_pc `0x03ABD6` (SEED site prefetch): `0x0000 -> 0x0010`
3. Subsequent writes observed at arcade_pc `0x039F8C` decrement countdown (`0x0010 -> 0x000F -> ...`)

Required outcome check:
- CLEAR event/trace pass occurs before first SEED: YES
- Seeded-then-wiped inversion from Build 0051 is no longer present in first-occurrence ordering: YES

## Phase 6 — Basic Boot Sanity

Checks performed with native debugger breakpoints:
- Arcade startup_common entry breakpoint
  - Target runtime_genesis_pc `0x0003B086` (= arcade_pc `0x03AE86`)
  - Hit: YES at cycle `802876` (observed PC `0x0003B088`, prefetch)
- `load_scene_tiles` entry breakpoint
  - Target runtime_genesis_pc `0x000711B0`
  - Hit: YES at cycle `156274` (observed PC `0x000711B2`, prefetch)
- Immediate exception/halt in first 2 seconds:
  - NO fatal exception/halt observed

## Phase 7 — Integrity

- Only `apps/rastan-direct/src/boot/boot.s` changed as source: YES
- Build succeeded: YES
- Static post-build verification complete: YES
- Runtime Verification A complete: YES
- Runtime Verification B complete: YES
- Basic boot sanity complete: YES
- No source/spec/tool modifications beyond allowed scope: YES

## Final Status

- `boot.s:160` deletion implemented: YES
- Genesis-side pre-handoff interrupt-enable instruction removed from `_bootstrap`: YES
- Arcade reaches its own enable site at arcade_pc `0x03B07A`: YES
- CLEAR-before-first-SEED ordering: YES
- Immediate boot regression in first 2 seconds: NO
