# Cody Build 0477 — READY / Continue Visibility Candidate

## Result

Build 0477 is the first passing RG-016 candidate and is **AWAITING TIGHE HARDWARE ACCEPTANCE**.
Accepted Build 0473 remains the immutable baseline. Builds 0474 and 0476 are rejected/consumed;
Build 0475 failed before numbered publication and is consumed without an artifact. No acceptance
tag was created for any RG-016 build.

## Artifact record

- exact ROM-producing source: `a3f1361bd2f583c2d991b04393650d9d208bdcc7`
- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0477.bin`
- normal SHA-256: `a5f9adfc33f44eae8479617d9cc56c4021fe16661fde0572956a44c69ef86eaf`
- size: 2,739,896 bytes
- counter: 477
- complete normal, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible` family: PASS
- canonical inventory: 228 byte-neutral sites, 86 shift replacements, 7,202 relative branches,
  two declared branches, 628 absolute-long references and 29 jump-table entries repaired

The exact source includes the proven `0x03A5D2` READY dispatcher declaration. Later commits
`5586def5` and `3d5127c9` change regression assertions only; `apps/rastan-direct/`, the remap spec
and every ROM-producing input are unchanged from `a3f1361b`.

## Ownership correction

The terminal-death HOLD at arcade `0x051998` remains intact. Human-session READY becomes safe only
after retained construction completes at `0x03A74E`, and becomes unsafe again at READY exit
`0x03A75C`. Coherent gameplay remains publication-gated by the existing `0x050482` producer
completion and fixed-order DMA completion.

Final-death frontend ownership is independent of gameplay readiness. Retained Continue construction
`0x03A31C..0x03A36E` becomes safe at `0x03A374`; complete terminal GAME OVER becomes safe at
`0x03A448`. Continue acceptance stays visible until `load_scene_tiles(1)`, the first actual native
resource turnover, performs the existing blank. No speculative exit hook, state machine, polling or
delay was added.

Each hook preserves its original six-byte state write, then calls a helper that preserves its used
registers and SR/CCR. JSR/RTS is balanced. Canonical variable-length reflow and the declared READY
dispatch table repair all crossing references. No NOP, RTS bypass, chip emulation, shadow rendering,
framebuffer or gameplay authority was added.

## Validation

- canonical and pre/post boot guards: PASS
- Genesis NTSC R1-S1 entry: PASS, gameplay reached with 240 post-entry frames
- all seven production epochs and Plane-A/fixed-Plane-B LUT checks: PASS
- generated PC090OJ frame, direct-dispatch and RG-014 preservation checks: PASS
- native HUD/title/item and configured seven-ROM family: PASS
- fixed30: PASS, 1,798 frames, zero live FG C-window writes
- extended final-life: PASS at frame 3,576; three deaths; 220 READY-visible frames across two
  non-final deaths; 140 post-READY blank frames; two coherent restarts; 966 Continue-visible frames;
  zero unsafe visible frames and zero unsafe display-on writes
- first visible restart, both deaths: state 3, X/Y `0x0020/0x0030`, selectors `0x0000/0x000C`,
  scene 1, pending 0, body count 9, emitted count 11
- writer-event/Continue re-entry: PASS at frame 4,429; 25 Continue-visible frames, 71 re-entry
  loading-blank frames, coherent visible re-entry; both SAT banks and score `001234` preserved
- RG-004 Continue: PASS at frame 2,728; 120 visible frames; 83/83 distinct staged/VDP names;
  zero name mismatches and zero nonblank outside-panel cells; staged palette equals CRAM
- RG-004 attract/title: PASS at frame 7,216; natural demo and death reached; first title, second
  title and terminal CRAM lines match
- `_invincible` rope: PASS, `795/795/795`, median `13,267.083 ms`, deterministic YES; identical to
  accepted Build 0473, so no regression on this established route

The initial final-life invocation reported READY absent only because the newly added assertion used
`A5+0x13AA == 13`. The saved trace itself showed each visible 110-frame `2/2/7` dwell. Correcting the
validator to the statically proven retained subphase and rerunning the unchanged ROM produced the
passing result above; this did not consume another build.

## USER MUST VERIFY

On real Genesis hardware verify both non-final sequences show READY stably, remain blank during the
following load, and reveal only coherent respawn Rastan. Verify final death shows GAME OVER/Continue,
Continue remains usable, and accepted Continue re-entry returns to coherent gameplay. Build 0477 is
not accepted until Tighe reports that result.

Deferred and untouched: reverse-residency optimization, Bat fast path, actor-family optimization,
general PC080SN cleanup and the known absent/deferred full gameplay HUD.
