# Build 0279 — Shift-Aware Genesis-Only → Maincpu Hook Continuations

**Agent:** Andy · **Type:** targeted implementation + one Makefile-owned build · **Baseline:** Build 0273
(good) · **Regressed baselines:** 0274–0278 · **Produced:** Build 0279.

## Root cause (proven, not re-investigated)
Build 0274 introduced variable-length `shift_replacements` that moved the copied maincpu by **−0x4A (−74)**
bytes at the 0x557xx region. The pre-existing Build-0247 Plane-A vertical-scroll hooks jmp back to **hardcoded
runtime continuation addresses** that were only correct *before* the shift:

- `PLANE_A_PAN_UP_CONTINUATION = 0x55998` (arcade 0x55798) — post-shift the real continuation is **0x5594E**.
- `PLANE_A_PAN_DOWN_CONTINUATION = 0x5590C` (arcade 0x5570C) — post-shift the real continuation is **0x558C2**.

Both real continuations are the `move.w a5@(0x10B0),d1` vertical-origin update. The stale jmps landed on the
wrong / a mid-instruction byte, bypassing the `a5@0x10B0` update, so the playfield vertical origin never
progressed, collision sampling stayed on the wrong cell, and the player fell through the floor.

## The systemic fix (not a hardcode, not a trampoline, not a reflow abandonment)
Source now expresses the **arcade** continuation identity; the translation pipeline resolves the runtime address
through the same authoritative shift/relocation mapping used for the maincpu itself.

- **`apps/rastan-direct/src/tilemap_hooks.s`** — the two continuations are declared from arcade addresses:
  ```
  .equ PLANE_A_ARCADE_RELOCATION_BASE, 0x00000200
  .equ PLANE_A_PAN_UP_CONTINUATION,   (0x00055798 + PLANE_A_ARCADE_RELOCATION_BASE)
  .equ PLANE_A_PAN_DOWN_CONTINUATION, (0x0005570C + PLANE_A_ARCADE_RELOCATION_BASE)
  ```
  (byte-neutral emit — still a single `jmp abs.l`.)
- **`tools/translation/postpatch_startup_rom.py`** — new post-shift pass over the genesis-only region: any
  `jmp/jsr abs.l` (0x4EF9/0x4EB9) whose operand falls inside the copied maincpu source range is re-resolved as
  `arcade = operand − relocation_delta; resolved = arcade + relocation_delta + accumulated_shift_before(arcade)`.
  This is the **same** `accumulated_shift_before` mapping the maincpu reflow already uses, so genesis-only
  continuations now track the maincpu automatically on any future shift. An invariant
  `genesis_only_maincpu_ref_count = 5` (declared in `specs/rastan_direct_remap.json`) guards the audit set.
- Coverage constant advanced to `0x1848E0` in `postpatch_startup_rom.py` and `verify_canonical_rom.py`
  (byte-neutral change; the +596 was a stale-constant artifact in the working tree, not new bytes).

## Genesis-only → maincpu target audit (mandatory blast-radius sweep)
Every genesis-only `jmp/jsr` into the copied maincpu was enumerated and classified. Refs whose arcade target is
**before** the first shift point need no adjustment; refs **after** it are shift-resolved.

| # | Site (genesis-only) | Arcade target | Pre-fix runtime | Post-fix runtime | Status |
|---|---|---|---|---|---|
| 1 | Plane-A pan **up** hook `0x706a4` | 0x55798 | 0x55998 (stale, `beq`) | **0x5594E** (`move.w a5@(0x10B0),d1`) | FIXED |
| 2 | Plane-A pan **down** hook `0x706fc` | 0x5570C | 0x5590C (stale, mid-insn) | **0x558C2** (`move.w a5@(0x10B0),d1`) | FIXED |
| 3 | textwriter jsr | 0x56584 | 0x565CE (stale) | **0x56584** | FIXED (latent — same class) |
| 4 | 0x3b930 jsr | 0x5B6E2 | 0x5B712 (stale) | **0x5B6E2** | FIXED (latent — same class) |
| 5 | vblank hook `0x3A208` | before first shift | unchanged | unchanged | already-safe (proven) |

Refs #3/#4 are the "another identical latent bug" the task required be found and fixed, not just the two known
Plane-A continuations. The highscore-LEA (`0x3C654`) and the vblank hook are before the first shift point and are
correct unchanged.

## Static proof (built ROM `build/genesis_postpatch.disasm.txt`)
```
706f6: jmp 0x5594e          # pan-up hook returns to shifted continuation
70746: jmp 0x558c2          # pan-down hook returns to shifted continuation
5594e: movew %a5@(4272),%d1 # arcade 0x55798 continuation, a5@0x10B0
558c2: movew %a5@(4272),%d1 # arcade 0x5570C continuation, a5@0x10B0
55998: beqs 0x559a2         # stale target now decodes as wrong instruction (confirms staleness)
706a4/706fc: moveml ...     # forward hook entries intact
```

## Runtime state comparison — Genesis NTSC (`mame genesis -cart`)
Sampled `a5@0xFF10B0` in gameplay (scene=01), identical harness/timeline for all three builds:

| Build | F2800 10B0 | F3000 10B0 | Verdict |
|---|---|---|---|
| 0273 (good) | **0x0149** | **0x0149** | vertical origin progressed |
| 0278 (regressed) | 0x0000 | 0x0000 | stuck — player falls through floor |
| **0279 (fix)** | **0x0149** | **0x0149** | **restored — matches 0273 exactly** |

0279 reproduces the working baseline's `a5@0x10B0` progression that 0278 lost. The `10B0=0` regression is gone.

## 0275–0278 good fixes retained (not reverted)
- 0275 FRONT/BODY register preservation (D1/D3/D4/D6) — kept.
- 0276 shifted long/immediate reference relocation — kept.
- 0277 branch/reference-to-replacement-start mapping — kept.
- 0278 BODY mode-7 `D2=0` restore — kept.

The 0274 main-loop native PLAYER_BODY/FRONT-staging → VBlank-commit architecture is unchanged and was never the
cause.

## Not included (recorded as separate review debt)
The auxiliary-anchor redesign (`a5+0x129A/0x129C`, `0x0547C0`, `0x051E00`, `0x542E8`) is out of scope for this
fix and remains unverified. It must be validated separately before being trusted; it is not required for, and was
not mixed into, the continuation fix.

## Build identity
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0279.bin`
- SHA-256: `2107c36638ea2994c3ca3f0884f48f3317f52213896747976e7522f4e89f58d0`
- Size: 1591520 bytes · Counter: 278 → **279** · Canonical gate: PASS.

## USER MUST VERIFY
Static proof and the `a5@0x10B0` progression match are confirmed. Please confirm on real/emulated Genesis-NTSC
that the player now lands and moves normally (walk, jump, land on floor) across the intro fall and early gameplay,
matching Build 0273 and unlike 0274–0278.
