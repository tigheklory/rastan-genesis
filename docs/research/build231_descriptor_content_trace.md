1) Purpose
- Trace Build 231 live title/logo descriptor content generation after ownership retarget, and identify the first exact point where meaningful active descriptor content fails.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest Build 230/231 sections)
- `docs/research/build230_sprite_logo_trace.md`
- `docs/research/build231_sprite_logo_fix.md`
- `apps/rastan/src/main.c` (`genesistan_render_sprites_vdp` descriptor interpretation)
- `dist/Rastan_231.bin` disassembly (`m68k-elf-objdump`)
- Started-path probe (START injected, 20s): `/tmp/build231_descriptor_content_probe.txt`

3) Live Descriptor Content Trace
- Active path execution is present:
  - `0x03AAF2` hit `1`
  - `0x05A174` hit `1`
  - `0x03AF5E` hit `5`
  - `0x20060C` hit `294`
- Active descriptor writes/readbacks:
  - block A (`0xFF11B2..0xFF1241`): `writes=138`, `reads=41088`, `nonzero_writes=0`
  - block B (`0xFF0170..0xFF018F`): `writes=34`, `reads=4704`, `nonzero_writes=6`
- Write sequence highlights:
  - pre-title/frame-21..22 clears at `0x2011A6..0x2011B4` write zeros into both blocks.
  - title clear pass at frame 665: `0x03AF5A` writes zeros across block A.
  - title/logo producer call at frame 667 (`0x05A174`):
    - block A writes from `0x05A184/0x05A186`: all zeros.
    - block B writes from `0x05A198/0x05A19C/0x05A1A0/0x05A1A4`: repeated `{w0=0x0080, w1=0x0000, w2=0x0000, w3=0x0000}`.
  - block B had earlier unrelated nonzero words at `0xFF018C/0xFF018E` from `0x2149AA` (frame 22), then `0x05A1A0` zeroed them at frame 667.
- End-of-window snapshots:
  - block A: `0/18` nonzero entries, `0/144` nonzero bytes.
  - block B: `4/4` nonzero entries, but only `word0` is nonzero; `4/32` nonzero bytes total.

4) Descriptor Format Analysis
- Renderer-required layout (`genesistan_render_sprites_vdp`):
  - word0: attr/flags (`data`)
  - word1: y position (`y_raw`)
  - word2: tile code (`code & 0x3FFF`)
  - word3: x position
- Required content for visible title/logo sprites:
  - nonzero `word0` (if `word0==0`, renderer forces hidden sentinel behavior)
  - valid `word2` tile code for logo cells (not empty/default code-only stream)
  - valid `word1`/`word3` on-screen coordinates
- Build 231 field-level content:
  - block A (`18` entries):
    - word0 nonzero: `0`
    - word1 nonzero: `0`
    - word2 nonzero: `0`
    - word3 nonzero: `0`
    - renderer interpretation: all hidden/empty.
  - block B (`4` entries):
    - word0 nonzero: `4` (`0x0080`)
    - word1/word2/word3 nonzero: `0/0/0`
    - renderer interpretation: template-like placeholders with no tile code and no positioned logo geometry.

5) First Content Breakpoint
- First exact content failure point: `0x05A174` body (write loop at `0x05A184..0x05A1A4`).
- Expected content:
  - active descriptor entries containing real logo sprite fields (attr + y + tile code + x) for renderer-owned blocks.
- Actual content:
  - block A: clear-only zeros.
  - block B: repeated template-only records (`0x0080,0,0,0`), with no tile-code/position population.
- Why renderer sees no meaningful logo data:
  - block A (primary consumed block) remains entirely zero.
  - block B has attr-only placeholders but missing tile/position fields needed for visible composed logo sprites.
  - therefore ownership is correct, but descriptor content generation is still absent/malformed.

6) Minimal Next Fix Target
=== BUILD231_DESCRIPTOR_CONTENT_FIX_TARGET ===
- fix_area: title/logo descriptor content generation in the live `0x03AAF2 -> 0x05A174` producer path.
- exact_blocking_path: `0x05A174` writes clear/template records only (`blockA all zero`, `blockB attr-only`), never producing full descriptor tuples.
- current_wrong_content_or_format: active buffers receive zeroed or partial records (`w0-only`), with `w2(tile code)=0` and `w1/w3(position)=0` for all block-B entries.
- correct_expected_content_or_format: producer must emit fully populated active-format entries (`word0 attr`, `word1 y`, `word2 nonzero logo tile code`, `word3 x`) for title/logo sprites.
- why_this_blocks_logo_visibility: renderer consumes active buffers, but current records are hidden/empty placeholders rather than drawable logo descriptors.
- minimal_correct_change: replace the `0x05A174` template/clear write logic with the real descriptor-content population logic on the same direct opcode path (no detours), preserving active buffer ownership.
- what_must_NOT_be_done: no hardcoded/fake sprite injection, no manual unrelated buffer writes, no shims/trampolines/bridges, no state-machine bypass.

7) Uncertainties
- This pass proves the first content loss point and field-level absence, but does not yet resolve which exact upstream source table/set should feed nonzero logo `word2/word1/word3` in final form.
- Block B renderer usage may be phase-dependent; this 20s sample confirms reads, but not full intended composition ordering for all title phases.

8) Conclusion
- In Build 231, ownership routing is fixed, but the live title/logo producer still emits clear/template descriptor content at `0x05A174`; the active renderer reads these buffers but receives no full sprite descriptor payload, so title/logo sprites remain invisible.
