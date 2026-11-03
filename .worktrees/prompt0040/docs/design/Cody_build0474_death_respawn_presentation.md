# Cody Build 0474 — Death/Respawn Presentation (Rejected)

## Verdict

Build 0474 is **REJECTED** and permanently consumed. Its canonical build, seven-ROM family, boot,
R1-S1, production-epoch, generated graphics, native HUD, sprite/frame, and static final-life gates all
pass, but the extended established final-life regression proves that the required post-death `READY!`
presentation remains hidden. No rope benchmark or broader acceptance suite was run after this hard
functional failure.

- exact ROM-producing source: `70622388b1dc21c22aa8c3ccaa194abf4ab9575a`
- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0474.bin`
- SHA-256: `93afbf60dbc4b2423e58296e9925c8143c26e9ab242b505e2682c5f899ae901c`
- size: 2,739,896 bytes
- seven-ROM family: complete and configuration-verified
- accepted tag: **none** (correctly not created)

## What Build 0474 proves

The presentation-only latch is structurally sound for death blanking and the first coherent gameplay
reveal. The existing final-life route naturally traversed two non-final deaths and one final death.
For both non-final restarts:

- the latch entered HOLD at the retained `0x051998` death-terminal event;
- no HOLD generation was classified visible;
- the gameplay fill completion moved the latch to READY;
- the next publication consumed it;
- the first visible gameplay state was identical: player state `3`, X `0x0020`, Y `0x0030`, primary/
  secondary selectors `0x0000/0x000C`, scene `1`, scene-pending `0`, native body count `9`, emitted SAT
  count `11`.

This hides the previously exposed death-location reconstruction and premature wrong-palette/wrong-pose
gameplay frame. It does not add gameplay authority, polling, PC090OJ/PC080SN emulation, shadow RAM,
framebuffer state, or a wait-N delay.

## Why it is rejected

The first static cut incorrectly treated internal `0x055DDC` state 12 / `0x055FD2` as the human
post-death READY completion event. Original disassembly proves the actual human-session branch:

1. `0x055DDC` sees internal state `<9` and nonzero session `A5+0x0034`;
2. it sets `A5+0x1394=0x00FF` and returns;
3. caller `0x03A6B2` then takes the `0x00FF` path;
4. `0x03A6E8..0x03A748` emits PLAYER/READY, ROUND/digit, and remaining presentation consequences;
5. `0x03A74E` enters the visible 112-tick subphase-7 READY dwell;
6. `0x03A75C` ends that dwell and begins the loading transition.

The Build-0474 reveal hook at `0x055FD2` is therefore not reached on this route. Runtime result:

```text
result=FAIL
reason=ready_never_visible
death_entries=3
ready_visible_frames=0
unsafe_visible_frames=0
visible_restarts=2
```

The correct future source change is bounded and proven: move READY reveal ownership from `0x055FD2`
to the retained `0x03A74E` completion event, and mark presentation unsafe again at retained READY-dwell
expiry `0x03A75C`. Build 0474 cannot be overwritten or renamed, and this task did not authorize or
produce Build 0475.

## Semantic cut and removed tail

The semantic cut remains retained arcade death/READY/respawn decisions → Genesis display safety around
final native CRAM/Plane/SAT/scroll publication. The already-retired PC090OJ tuple/SAT and PC080SN chip
write tails remain removed. Build 0474 adds no compatibility layer; it only misplaces one reveal event.

## Validation record

- canonical and boot guards: PASS
- R1-S1 gameplay entry: PASS (569 frames, 240 post-entry frames, no exceptions)
- seven production epochs: PASS
- generated PC090OJ frame/direct-dispatch verifier including RG-014 register preservation: PASS
- native HUD/title/item and palette-family verification: PASS
- seven-ROM configured family: PASS
- established final-life plus RG-015 bounded presentation assertions: **FAIL — READY hidden**
- rope: NOT RUN after hard functional rejection
- writer-event, Continue/re-entry, RG-004 frontend, attract/title acceptance reruns: NOT RUN after hard
  functional rejection

## USER MUST VERIFY

No hardware acceptance is requested for rejected Build 0474. For the next authorized candidate, Tighe
must verify a non-final death through restart: complete disintegration; no Rastan reconstruction at the
death location; visibly stable `READY!`; black native-loading interval after READY; then the correct
spawn position and falling/neutral pose with coherent sky palette, Plane A/B terrain, Rastan sprite
graphics, SAT, HUD, and no one-frame mixed-generation flicker. Continue, GAME OVER, title/attract,
score, 1UP, damage, and rope behavior must remain unchanged.
