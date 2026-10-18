# Cody Build 0444 — Native One-Shot Genesis Title Screen

Status: **FAILED CANDIDATE — NOT ACCEPTED**  
Accepted baseline: Build 0442 (`c7ca1439e5cad8028043e8b3ff56fe7282addb1d`)  
Accepted ref: `accepted/build-0442`

## Scope and architecture

The retained semantic cut is arcade `0x03AA54`, the title-entry presentation
state. The native helper installs build-generated final Genesis Plane B,
Plane A, palette, and semantic SAT presentation data. Arcade code continues to
own title/attract timing, input, credits, scores, sound, and progression.

The replacement is a proper size-changing shift replacement:

- original entry bytes at arcade `0x03AA54`: `4EB90005A356`;
- Build 0444 runtime entry: `0x03AC54`;
- replacement bytes: `4EB9000736584E75` (`JSR
  genesistan_title_present_once; RTS`);
- original presentation routine logically ends at arcade `0x03AA8E`;
- the old presentation body after the replacement is unreachable from the
  entry; there is no fall-through continuation;
- the helper balances its own save/restore and JSR frame, then its terminal
  RTS returns through the dispatch caller's existing frame;
- A5 is preserved and the original state writes remain: `A5+0x0004 = 0`,
  `A5+0x0002 = 1`, and `A5+0x002C = 0x00D0`.

Generated-title equivalence passes. The three generated 4-KiB maps account
for the exact `+0x3000` deterministic coverage increase. No repeated PC080SN
title draw, full-title comparison, or Genesis-owned attract state machine was
introduced.

## Build 0443 first failure

Build 0443 was produced and preserved as the first native-title candidate. Its
normal gate entered the address-error handler around frame 31. The gate stored
the vector target, not the stacked fault PC, so `0x29500C` is the Build-0443
address-error handler and must not be reported as the faulting instruction.

Static reflow audit found one real defect: the `+2` insertion at arcade
`0x03AA54` crossed the outer title/attract word-displacement dispatch table at
arcade `0x03AA20`, but the table was not declared to the reflow engine. Its
post-insertion entries remained `0x0070` and `0x0138`, targeting two bytes
before the relocated handlers at arcade `0x03AA90` and `0x03AB58`.

## Build 0444 repair and result

Build 0444 declares the exact three-entry `0x03AA20` table through
`jump_table_word_displacements`. Postpatch reports three table fixes and the
final words are `0x0006, 0x0072, 0x013A`, restoring the original dispatch
destinations. The native-title verifier now requires that declaration.

Two already-exposed mechanical expectations were also synchronized:

- canonical Genesis coverage is `0x295EB8`;
- the obsolete full-HUD `-0x1000` coverage delta was removed because its
  generated image now has the same covered extent.

Build 0444 results:

- generated-title equivalence: PASS;
- assembly/link: PASS;
- shift/postpatch: PASS (`72` replacements, `3` jump-table fixes);
- canonical coverage/gate: PASS;
- boot guards: PASS;
- seven-ROM family/configuration verification: PASS;
- fixed 30-second run: completed, `1798` frames;
- gameplay-entry gate: FAIL, address error at external frame 32;
- epoch gate: FAIL for the same exception.

The dispatch-table defect was therefore real and required, but it was not the
complete cause of the early exception.

## Exact remaining evidence gap

The preserved Build 0444 gate evidence contains:

- address-error event at frame `31`;
- handler/vector target `0x29500C`;
- last periodic sample at frame `30`: Genesis PC `0x071866`, inside
  `genesistan_hook_tilemap_fg_fill` (`move.l d0,0x00FF4006`).

It does **not** contain the stacked group-0 exception PC, fault address,
instruction register, or access word. The periodic `0x071866` sample is not
proof that this even-address long store faulted. Consequently the exact fault
PC, instruction, register state, and subsystem cannot be stated from the
allowed artifacts without guessing.

No second speculative patch and no Build 0445 were produced. The single fact
needed next is the already-supported crash record's stacked fault PC (ideally
with fault address/access word) from this failed title candidate.

## Artifacts

- Build 0444 canonical SHA-256:
  `0705b91980acf6cbbdc6eb330a641abbfa9cd0cdf88f143e15061769798f9b97`
- `_d`: `5bd74a181e682cacdbdeae8ecb2114d25e1896acfd9b91208e301d1bae78795f`
- `_s`: `5c7040c8de02edc6ff8d970b8809f56827c77a9bd455c6b1636e9b669d8ef243`
- `_do`: `a5d21cd787dff144e9176d8b98075686153d8b237bfaf0da17063801b6e2533d`
- `_c`: `a440ed6d3518376be55eecebc4ba5079c69150c5d221350fe6fb0c46e1bcd299`
- `_full_hud`: `0c55760f7ffedf508c6b3214e1d8f75ea189e554e2ece810205d531bdcfcfcb1`
- `_invincible`: `00c2e7ef264bfa77e19122dd1545ec3a0991b7231f3203827571715e1c7691e4`

No source commit was created because the candidate did not pass the normal
runtime gates. Real-hardware acceptance remains pending a passing candidate.
