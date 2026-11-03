1) Purpose
- Trace the live title/logo sprite path in Build 230 and identify the first concrete breakpoint preventing title/logo sprite data from reaching active renderer-owned descriptor buffers.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest Build 229/230 sections)
- `docs/research/build229_post_seed_trace.md`
- `docs/research/build230_text_dispatch_fix.md`
- `docs/research/build228_visible_output_trace.md`
- `dist/Rastan_230.bin` disassembly (`m68k-elf-objdump`)
- `apps/rastan/src/main.c`
- Runtime probes (started-path, START injected, 20s):
  - `/tmp/build230_sprite_trace_probe.txt`
  - `/tmp/build230_sprite_io_clean.txt`
  - `/tmp/build230_active_consumer_probe.txt`
  - `/tmp/build230_exec_probe.txt`

3) Live Title Sprite Path Trace
- Active title init chain in Build 230:
  - `0x03AADE` init body includes `0x03AAF2: jsr 0x05A174`.
- `0x05A174` behavior (disassembly-proven):
  - clears 64 bytes at `0xE0FF4094` (`movea.l #0xE0FF4094,a0`, looped `move.l d0,(a0)+`)
  - writes 16 words at `0x0010C170` (4 entries x 4 words)
  - returns (`rts`), no downstream helper call.
- Runtime execution proof (started run):
  - `0x03AAF2` hit `1`
  - `0x05A174` hit `1`
  - `0x20060C` (`genesistan_render_sprites_vdp`) hit `294`.
- Active renderer path (`genesistan_render_sprites_vdp` in `main.c`) consumes descriptor blocks from workram offsets:
  - block A: `A5+0x11B2` (`0xFF11B2`)
  - block B: `A5+0x0170` (`0xFF0170`).

4) Legacy vs Active Buffer Ownership
- `0xFF4094`
  - classification: `LEGACY`
  - semantic role: legacy title/front-end sprite staging block (old path)
  - producer(s): `0x05A174` (also related family at `0x05A2C4`/`0x05A402`)
  - consumer(s) in started Build 230 run: none observed (`reads=0`, `writes=32`)
  - final active renderer ownership: NO

- `0x10C170`
  - classification: `LEGACY`
  - semantic role: legacy descriptor/control table for title/front-end helper family
  - producer(s): `0x05A174` and nearby helper variants
  - consumer(s) in started Build 230 run: none observed (`reads=0`, `writes=16`)
  - final active renderer ownership: NO

- `0xFF11B2`
  - classification: `ACTIVE`
  - semantic role: active sprite descriptor block A used by Genesis renderer
  - producer(s) seen in started run: clear/write activity (`0x03AF5A` and memset-like writes at `0x2011AA..0x2011B0`)
  - consumer(s): active renderer (`reads_renderer=19992`, PCs `0x200696/0x20069A/0x2006A4/0x2006AA/...`)
  - final active renderer ownership: YES

- `0xFF0170`
  - classification: `ACTIVE`
  - semantic role: active sprite descriptor block B (secondary block in renderer ownership model)
  - producer(s) seen in started run: minimal writes only (`writes=18`, mostly memset-like PCs)
  - consumer(s): no renderer-window reads observed in this 20s run (`reads_renderer=0`)
  - final active renderer ownership: YES

5) First Sprite Breakpoint
- First concrete breakpoint after title/logo call is at:
  - `PC 0x05A174` (called from `0x03AAF2`).
- Expected output target for live title/logo sprites:
  - active descriptor ownership (`A5+0x11B2` / `A5+0x0170`, i.e. `0xFF11B2` / `0xFF0170`) consumed by `genesistan_render_sprites_vdp`.
- Actual output target from `0x05A174`:
  - legacy buffers `0xFF4094` and `0x10C170`.
- Why renderer never sees meaningful title/logo sprite data:
  - renderer reads active block A heavily, but block A remains zero (`0/144` nonzero in started-run probe),
  - the title/logo producer writes are landing in legacy buffers with no live consumer in this started path.

6) Minimal Next Fix Target
=== BUILD230_SPRITE_LOGO_FIX_TARGET ===
- fix_area: title/logo sprite producer ownership at `0x03AAF2 -> 0x05A174`.
- exact_blocking_path: title init invokes `0x05A174`, which writes sprite setup to `0xFF4094` and `0x10C170` only; active renderer consumes `0xFF11B2`/`0xFF0170`.
- current_wrong_target_or_condition: producer writes to legacy buffers that are not consumed by active renderer.
- correct_expected_target_or_condition: title/logo producer must populate active descriptor buffers (or a directly consumed active-format path) before `genesistan_render_sprites_vdp` runs.
- why_this_blocks_logo/sprite_output: active renderer input remains empty/near-empty while logo producer output is stranded in legacy ownership.
- minimal_correct_change: retarget/replace the `0x05A174` producer output path to active descriptor ownership format/addressing (direct opcode-path correction, no detours).
- what_must_NOT_be_done: no fake sprite injection, no manual unrelated buffer population, no shims/trampolines/bridges, no state-machine bypass.

7) Uncertainties
- This pass proves the first producer ownership break and buffer mismatch, but does not yet finalize the exact descriptor-format transformation needed to preserve full arcade logo semantics when writing into active blocks.
- Block B (`0xFF0170`) did not show renderer-window reads in this 20s sample; whether that is phase-dependent versus structurally unused in this state remains to be confirmed in a longer/state-focused probe.

8) Conclusion
- Build 230 title/logo sprite output is blocked first at `0x05A174`: it still produces legacy-buffer sprite data, while the live Genesis renderer consumes a different active descriptor ownership path (`0xFF11B2`/`0xFF0170`), leaving the visible logo/sprite payload effectively empty.
