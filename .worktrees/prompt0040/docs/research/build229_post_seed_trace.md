1) Purpose
- Trace the downstream path after the Build 229 state-seed correction and identify exactly why full title producers still do not activate.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections)
- `docs/research/build228_state_machine_trace.md`
- `docs/research/build228_visible_output_trace.md`
- `docs/research/build229_state_seed_fix.md`
- `dist/Rastan_229.bin` disassembly (`m68k-elf-objdump`)
- Runtime probes:
  - `/tmp/build229_state_seed_probe.txt`
  - `/tmp/build229_hook_exec_probe.txt`
  - `/tmp/build229_sprite_buf_window.txt`
  - `/tmp/build229_write_targets_probe.txt`
  - `/tmp/build229_sprite_addr_mismatch_probe.txt`

3) Title Cluster Downstream Trace
- Entry is now correct: `A5+0x0000=1` routes major dispatch to `0x03AAB8`.
- `0x03AAB8` first applies timer gate on `A5+0x002C`:
  - if nonzero: decrement and `rts` (`0x03AABE..0x03AAC2`)
  - when zero: substate dispatch at `0x03AAC4..0x03AAD8`
- Substate 0 (`0x03AADE`) runs title init chain:
  - `0x03AFEA`
  - `0x03AF5E`
  - `0x03B06C` -> `0x03B076`, `0x03B2AA`
  - `0x05A174`
  - `0x03AAFA/0x03AB0A/0x03AB16/0x03AB1C -> 0x03BD5E`
  - then sets `A5+0x0002=1` (`0x03AB20`)
- Substate 1 (`0x03AB28`) is idle/coin loop and mostly returns until coin transition.
- Runtime proof in started path (20s):
  - `0x03AAB8`: 294 hits
  - `0x03AADE`: 1 hit
  - `0x03AF5E`: 5 hits
  - `0x03B06C`: 1 hit
  - `0x03BD5E`: 5 hits

4) Text/Tilemap Producer Block
- `0x03BD5E` is currently:
  - `jsr 0x2027B8`
  - `rts`
- `0x2027B8` is a byte-mirror stub (`move.b d0,0xE0FF4863; rts`), not a tile/text producer.
- The actual 3bb48 writer remains at `0x20034C` and wrapper at `0x2027C0` (`jsr 0x20034C`), but:
  - only call to `0x20034C` in ROM is inside `0x2027C0`
  - no callsite targets `0x2027C0`
- Therefore, title text dispatch executes (`0x03BD5E` hits), but full 3bb48 producer path does not.
- Why hooks stay quiet:
  - `0x20034C`: blocked by wrong call target (`0x03BD5E -> 0x2027B8`)
  - `0x200000`/`0x2001A6`: not on this title init chain; their live callsites are elsewhere (`0x055B86 -> 0x200000`, `0x055BAE -> 0x200292`) and are not reached in the observed title window.

5) Sprite Producer Block
- Title-prep call `0x03AF5E` currently performs clear-only writes (via `0x03AF56`) and does not populate visible sprite descriptors.
- The title logo helper `0x05A174` writes to legacy regions:
  - `0xFF4094`
  - `0x10C170`
  - runtime write proof at frame 667 (`/tmp/build229_write_targets_probe.txt`).
- Active Genesis sprite renderer path in `main.c` consumes descriptor sources anchored at:
  - `A5+0x11B2` (`0xFF11B2`)
  - `A5+0x0170` (`0xFF0170`)
- Observed result:
  - renderer source block A remains zero-valued
  - block B is only minimally populated
  - sprite output path runs (`0x20060C` hits), but payload remains near-empty.

6) First Post-Seed Breakpoint
- First concrete blocker after correct title-state entry is the text dispatch remap at `0x03BD5E`:
  - current: `jsr 0x2027B8` (status mirror stub)
  - expected producer path: `0x2027C0 -> 0x20034C` (or equivalent true text writer path)
- This is the earliest downstream point where title init executes but full text/tile output is suppressed.

7) Minimal Next Fix Target
=== BUILD229_POST_SEED_FIX_TARGET ===
- fix_area: title text dispatch remap in the title init call chain.
- exact_blocking_path: `0x03AAFA/0x03AB0A/0x03AB16/0x03AB1C -> 0x03BD5E -> 0x2027B8 -> rts`.
- current_wrong_condition: title text dispatch calls a non-producer mirror stub, leaving `0x20034C` unreachable from active title path.
- correct_expected_condition: title text dispatch must route into the real text producer path (`0x2027C0 -> 0x20034C`, or equivalent direct producer target).
- why_this_blocks_full_title_output: title text IDs are issued, but producer execution is short-circuited before tile/text writes are generated.
- minimal_correct_change: correct the `0x03BD5E` remap target to the true text-writer producer path without adding detours or fake data.
- what_must_NOT_be_done: no shims/trampolines, no manual producer calls, no fake graphics injection, no forced state writes, no launcher-path changes.

8) Uncertainties
- The `0x200DE2` hit count remains low and appears to be from a separate/indirect path; it is not sufficient to establish full title text ownership.
- Sprite-side legacy-to-final ownership mismatch is proven, but this report prioritizes the first post-seed text breakpoint as the minimum next step.

9) Conclusion
- Build 229 successfully enters title-state control flow, but full title output is still blocked immediately downstream because `0x03BD5E` dispatches into a non-producer stub (`0x2027B8`) and sprite content remains sourced from legacy/clear-only paths rather than fully populated renderer inputs.
