# Original Arcade Init Responsibility Map

## Purpose
Map original arcade startup/frontend-init responsibilities to determine which effects must be preserved for runtime correctness versus which are intentionally excluded in Genesis launcher flow.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (Build 96 skip-startup history, Startup Initialization Forensics, Post-Init WRAM Profiling)
- `README.md`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `build/rastan/startup_common_relocations.json`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin` (cross-check from existing research traces)
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin` (cross-check from existing research traces)
- MAME reference source: `src/mame/taito/rastan.cpp`, `src/mame/taito/taitoipt.h`

## Address Mapping Note
`genesis_rom_addr` uses shifted relocation:
- `patched_maincpu_addr = arcade_addr + cumulative_shift_delta` from `shift_replacements`
- `genesis_rom_addr = patched_maincpu_addr + 0x200`

For startup/common addresses in this pass, current cumulative delta is `+0x12`.

## Findings

| arcade_addr | genesis_rom_addr | Exact write / clear / copy action | State created | Category | Why |
|---|---|---|---|---|---|
| `0x03AE86` | `0x03B098` | `move.w #0, 0xC50000` | Orientation/control hardware register reset | SKIP_EFFECT | Arcade hardware register side effect; not required as Genesis startup state mechanism.
| `0x03AE8E` | `0x03B0A0` | `move.w #0, 0xD01BFE` | Sprite hardware control reset | SKIP_EFFECT | Raw PC090OJ hardware reset path.
| `0x03AE96` | `0x03B0A8` | `clr.w 0x350008`; also `clr.w 0x380000` at `0x03AE9C` | Arcade MMIO latch resets | SKIP_EFFECT | Board-specific MMIO behavior.
| `0x03AEB2..0x03AEE8` | `0x03B0C4..0x03B0FA` | 0x200000 CLCS read/write loops | Palette RAM refresh side effects | MIXED_EFFECT | Historically palette-path prep; raw arcade CLCS mechanism should be replaced by Genesis-native palette flow.
| `0x03AEEA..0x03AF02` | `0x03B0FC..0x03B114` | WRAM clear/copy over `0x10C000` | Deterministic game-owned runtime baseline | KEEP_EFFECT | Required non-video state foundation.
| `0x03AF04` | `0x03B116` | `lea 0x10C000, A5` | Canonical A5 base for game state | KEEP_EFFECT | Required execution contract for all later `A5+offset` logic.
| `0x03AF2C..0x03AF72` | `0x03B13E..0x03B184` | Fills/clears `0xC00000/0xC08000/0xC04000/0xC0C000` | C-window tilemap init | SKIP_EFFECT | Explicitly excluded C-window init path.
| `0x03AF7A..0x03AF8E` | `0x03B18C..0x03B1A0` | Read/invert DIP bytes from `0x390009/0x39000B` into `A5+0x18/+0x1C` | DIP mirror fields | KEEP_EFFECT | Required non-video config sources.
| `0x03AF96..0x03AFEA` | `0x03B1A8..0x03B1FC` | Derive `A5+0x38/+0x36/+0x30/+0x32/+0x2E` from DIP mirrors | Difficulty/bonus/cabinet/flip/mode fields | MIXED_EFFECT | Needed for game logic; cabinet/flip hardware side effects must remain decoupled.
| `0x03AFEE..0x03B00A` | `0x03B200..0x03B21C` | Load debug bits into `A5+0x40/+0x44` from `0x05FF9E` | Competition/invulnerability-related flags | KEEP_EFFECT | Runtime branch-affecting flags.
| `0x03B020..0x03B044` | `0x03B232..0x03B256` | Set init flag and call coinage helpers `0x5FFA2/0x5FFB2` | Coinage/config fields (`A5+0x08..0x10`) | KEEP_EFFECT | Required non-video economic settings.
| `0x03B04A` | `0x03B25C` | `bsr 0x03B0C2` config table copy | Seeds `A5+0x140` (39-byte block) | KEEP_EFFECT | Required table/config bytes used later.
| `0x03B056` | `0x03B268` | `jmp 0x100` when service/test condition set | Branch to test program | MIXED_EFFECT | Startup-mode routing logic is relevant; raw test path itself is not required for normal frontend.
| `0x03B05C` | `0x03B26E` | Send sound command `0x00EF` via `0x03F084` | Audio-side startup synchronization | MIXED_EFFECT | Not part of selector crash root cause, but can affect subsystem expectations.
| `0x03B064..0x03B076` | `0x03B276..0x03B288` | Set marker `A5+0x4A=0x00AA`; call `0x03B8B0`, `0x03B098`, `0x03ADD8`, `0x03AE28` | Composite startup handoff effects | MIXED_EFFECT | Contains both useful game-state transitions and direct arcade hardware writes.
| `0x03B098` | `0x03B2AA` | Legacy scroll clear (`0xC20000/0xC40000`) + text/init subcalls | Scroll+frontend staging | MIXED_EFFECT | Not safe to treat as pure MMIO clear; includes broader startup behavior.
| `0x03ADD8` | `0x03AFEA` | Display-control routine keyed by `A5+0x30/+0x32` | Orientation/control propagation | MIXED_EFFECT | Uses gameplay state fields but writes board-specific control regs.
| `0x03AE28` | `0x03B03A` | Writes from `A5+0x14` to display control MMIO | Display-control update | SKIP_EFFECT | Raw arcade register mechanism should remain excluded.
| `0x04527E` | `0x04549A` | Selector seed from `0x05FF9E` gated by `tst.b A5+0x0104` | Writes `A5+0x0118` and `A5+0x0117` | KEEP_EFFECT | Critical required runtime state for table index validity.

## Uncertainties
- Some `MIXED_EFFECT` routines (`0x03B098`, `0x03ADD8`) blend game-state setup and raw hardware side effects; they cannot be safely retained or removed wholesale without preserving required non-video effects elsewhere.
- Current spec patch state may alter reachability of some startup helper behavior; this report maps original responsibility, not implementation validity.

## Conclusion
- Required runtime correctness depends on preserving WRAM clear/baseline, DIP/config derivation, config copy, and natural selector seed ownership.
- Raw C-window/D-window/orientation MMIO writes are intentionally excluded as mechanisms.
- The safe path is selective reproduction of required non-video effects, not full `startup_common` replay.
