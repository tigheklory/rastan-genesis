1) Purpose
- Trace the live title-screen output path forward (no rollback) and isolate the first concrete path that still prevents visible title output.
- Enforce and report the custom text-exception-handler requirement status for this pass.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections)
- `docs/research/build228_visible_output_trace.md`
- `docs/research/build229_post_seed_trace.md`
- `docs/research/build230_text_dispatch_fix.md`
- `docs/research/build231_descriptor_content_trace.md`
- `docs/research/build232_descriptor_content_fix.md`
- Runtime probes:
  - `/tmp/title_forward_probe.txt` (started-path, `dist/Rastan_232.bin`, 20s, START injected)
  - `/tmp/title_forward_probe_232.mame.log`
- Static ROM checks:
  - `dist/Rastan_232.bin` (hexdump + callsite/target decode)
  - `apps/rastan/out/symbol.txt`, `apps/rastan/out/rom.bin` (mode-1 clean-build exception-handler sanity)

3) Title Screen Live Path Checklist
- 1) title state entered: PASS
  - Evidence: started-path reached (`current_screen=0x00000004`), state sampled as `A5+0x0000/+0x0002/+0x0004 = 0001/0000/0000`, `0x03AAB8` hit count `161`.
- 2) title init path executes: PARTIAL
  - Evidence: `0x03AADE` hit count `1`.
  - Limitation: no confirmed full progression through the expected downstream logo/text producer calls in this run (`0x03AAF2` hit `0` by tap).
- 3) text producer path executes: PARTIAL
  - Evidence: dispatch path executes (`0x03BD5E` hit `1`, `0x2027C0` hit `1`).
  - Failure inside path: `0x20034C` hit `0`.
- 4) text becomes visible on active plane output: FAIL
  - Evidence: no `0x20034C` execution; tile hooks `0x200000=0`, `0x2001A6=0`; text-shadow window is mostly space/clear content (`glyph=0x0020` in sampled cells).
- 5) logo/title sprite producer executes: PARTIAL
  - Evidence: active callsite tap for `0x03AAF2` and helper `0x05A174` both `0` in this run; sprite renderer still executes (`0x20060C` hit `160`).
- 6) logo/title sprite descriptors become drawable: FAIL
  - Evidence: block A remains empty (`0/144` nonzero bytes); block B remains non-drawable residue (`3/32` nonzero bytes; only one entry with partial words).
- 7) logo/title sprite graphics/data reach VRAM: PARTIAL
  - Evidence: heavy VDP data/control writes continue (data `23487`, control `13575`), but descriptor content is empty/non-drawable, so no meaningful logo payload is proven.
- 8) title-specific tilemap/background path executes if required: FAIL
  - Evidence: no activity at `0x200000`/`0x2001A6`; no proof of title tilemap population from live title path in this window.

- Mandatory custom text exception-handler rule status for this pass: FAIL on `dist/Rastan_232.bin`
  - Vectors in `dist/Rastan_232.bin` point to SGDK defaults (`bus=0x217DF2`, `addr=0x217E06`, `ill=0x217E1E`, `zdiv=0x217E3C`).
  - Text dumper strings are absent in `dist/Rastan_232.bin`.
  - Therefore runtime traces on that artifact are not mode-1-handler compliant.

4) First Still-Broken Title Output Path
- First still-broken path: `0x03BD5E` text dispatch remap target is stale/wrong.
- Proven current path:
  - `0x03BD5E` contains `JSR 0x2027C0`.
  - `0x2027C0` bytes are not the text wrapper (`32DA 7200 7000 ...`), i.e. wrong-function/inside-body target.
- Proven expected producer wrapper location in current image:
  - wrapper signature `2F0D 4EB9 0020034C 2A5F 4E75` is at `0x202A4C`.
- Impact:
  - Dispatch reaches `0x2027C0`, but `0x20034C` is never reached (`hit=0`), so visible title text generation is blocked at the first producer handoff.

5) Text Visibility Audit
- Active title text dispatch executes (`0x03BD5E` hit `1`), but visible producer execution fails.
- Producer chain result in this run:
  - `0x03BD5E -> 0x2027C0` executes.
  - `0x20034C` does not execute (`hit=0`).
  - `0x200000` / `0x2001A6` do not execute.
- Data evidence:
  - text-shadow writes do occur (`writes=2045`), but top writer PCs are clear/maintenance paths (`0x03AF5A`, `0x20161E`), and sampled cells are space-filled (`glyph=0x0020`).
- Conclusion:
  - producer dispatch executes, but visible text producer write path to active plane output is not reached correctly due stale remap target.

6) Sprite/Logo Visibility Audit
- Renderer path is active (`0x20060C` hit `160`), but descriptor payload is not drawable:
  - block A: `0/144` nonzero bytes
  - block B: `3/32` nonzero bytes (single partial entry; no stable drawable tuples)
- Descriptor write ownership in this run is dominated by clear/setup paths (`0x03AF5A`, `0x20143x` family), not proven logo tuple generation.
- VDP writes continue at high volume, but without meaningful descriptor content they do not establish visible title/logo sprite composition.
- Result classification: active buffers remain empty/near-empty for drawable title/logo output.

7) Shift/Relocation Sanity On Live Title Path
- PASS: major-state dispatch table integrity (base `0x03A26C`)
  - state1 target resolves to `0x03AAB8`.
- PASS: title substate table integrity (base `0x03AADA`)
  - sub0 -> `0x03AADE`, sub1 -> `0x03AB28`.
- PASS (static): title logo callsite target form
  - `0x03AAF2` opcode `4EB9`, target `0x05A174`.
- FAIL: title text dispatch remap semantic correctness
  - `0x03BD5E` target `0x2027C0` no longer matches the real wrapper location (`0x202A4C`), producing WRONG_FUNCTION/STALE_TARGET behavior.

8) Title Screen Forward Fix Target
=== TITLE_SCREEN_FORWARD_FIX_TARGET ===
- fix_area: title text dispatch remap target in the live title init chain.
- exact_live_path: `0x03AAFA/0x03AB0A/0x03AB16/0x03AB1C -> 0x03BD5E -> (currently 0x2027C0)`.
- current_failure: remap lands on stale/wrong function body; real wrapper moved to `0x202A4C`, so `0x20034C` is not reached.
- correct_expected_behavior: dispatch must land on the real text wrapper (`0x202A4C -> 0x20034C`) or equivalent direct producer endpoint.
- why_this_is_the_next_forward_step: this is the earliest proven post-entry output handoff failure in the live title path and it blocks visible text production before later sprite-side issues.
- what_must_NOT_be_done: no rollback, no shims/trampolines/bridges, no fake data injection, no forced state writes, no broad speculative rewrite.

9) Uncertainties
- The mode-1 custom-handler-compliant ROM from this pass (`apps/rastan/out/rom.bin` after clean mode-1 build) failed release postpatch validation, so the started-path runtime evidence above uses `dist/Rastan_232.bin` (non-compliant with the mandatory exception-handler rule).
- Address-read taps count memory reads, not a strict execute-trace primitive; callsite execution certainty is based on combined taps plus static opcode/target decode.

10) Conclusion
- Forward-path blocker #1 is a stale title text remap target (`0x03BD5E -> 0x2027C0`) that no longer lands on the real text wrapper (`0x202A4C -> 0x20034C`), preventing visible title text production while renderer-side sprite output remains descriptor-empty.
