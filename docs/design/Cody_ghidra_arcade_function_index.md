# Cody Ghidra Arcade Function Index

| arcade_pc | Ghidra function name | Purpose summary | Confidence |
|---|---|---|---|
| `0x03A000` | `startup_common` | Startup entry thunk branching into full startup body at `0x03AE86` | HIGH |
| `0x03A008` | `level5_vblank_handler` | Arcade L5/VBlank handler using A5-relative state and indirect dispatch | HIGH |
| `0x039F80` (`site: 0x039F9E`) | `warm_restart_watchdog_gate` | Countdown gate (`A5+0x2C`) and warm-restart trampoline via vectors 0/4 | HIGH |
| `0x03AE86` | `FUN_0003ae86` | Core startup body: hardware clears/probes/delays and state seeding | HIGH |
| `0x03AF04` | `<no_function> (site export)` | First explicit A5 base init site (`lea (0x10c000).l,A5`) | HIGH |
| `0x03AB7C` (`site: 0x03AB84`) | `warm_restart_gate_caller_a` | Caller-chain logic around credit/state checks and reset gate call | MEDIUM |
| `0x03B084` (`site: 0x03B092`) | `warm_restart_gate_caller_b` | Alternate loop/caller chain feeding warm-restart gate call | MEDIUM |
| `0x03AB22` | `<no_function> (site export)` | Work RAM default seeding (`A5+0x2C`, `A5+0x100`, `A5+0x00`, `A5+0x02`) | MEDIUM |
| `0x03A0EC` | `FUN_0003a0ec` | Coin/credit queue insertion region gated by A5-relative state | MEDIUM |

Inspected export files live under `docs/design/ghidra_exports/`.
