# MAME rope-attach performance benchmark

This benchmark measures emulated gameplay time, not host wall-clock time.

- Tool: `tools/mame/run_rope_attach_performance_benchmark.sh`
- Input route: established COIN, START, then hold P1 Right continuously.
- Start: first frame with global state `A5+0/2/4 = 2/3/0`, scene byte 1,
  player X `A5+0x10BE = 0x0020`, and player state
  `A5+0x10E8` in the active states 1–3.
- Stop: first `A5+0x10E8 = 4` after progression `A5+0x013E >= 2`. With no
  jump/attack input, this is the retained arcade first-rope attachment state.
- Time source: MAME emulated attotime; rendered frame count is also recorded.

Build 0419 baseline, three trials:

| trial | elapsed frames | emulated ms |
|---:|---:|---:|
| 1 | 878 | 14652.200 |
| 2 | 878 | 14652.200 |
| 3 | 878 | 14652.200 |

Median is 878 frames / 14652.200 ms; min=max and the route is deterministic.
Build 0422, three trials:

| trial | elapsed frames | emulated ms |
|---:|---:|---:|
| 1 | 879 | 14668.888 |
| 2 | 879 | 14668.888 |
| 3 | 879 | 14668.888 |

Median is 879 frames / 14668.888 ms; min=max and the route is deterministic.
Relative to 0419 this is one frame / 16.688 ms slower, or `+0.114%` elapsed
time. No optimization was added in response; the benchmark is an end-to-end
gameplay metric and the Build 0422 task is correctness-only.

