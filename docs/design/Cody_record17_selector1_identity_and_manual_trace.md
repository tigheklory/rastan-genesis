# Cody — Third-chain record/selector identity and manual-trace decision

**Scope:** Resume the Build-0378 third-chain investigation at the record-identity gate. No ROM
change, no numbered build, and no selector transform patch.

## Result

The automated failing state is **not** the exact `(record 17, selector 1)` state required by the
requested selector-1 transform audit.

Two retained state chains disagree:

| Contract | Live/authoritative value | Meaning |
|---|---:|---|
| Descriptor/content progression | `A5+0x013E = 0x0011` | `0x11` indexes descriptor record 17 |
| Map-stream pointer | Genesis `A5+0x10C6 = 0x00051183` | rebased original `0x00050F83` |
| Stream offset | `0x50F83 - 0x50F6B = 0x18` | LUT `0x50EE0` assigns offset `0x18` to record 22 |
| Selector byte | original `byte[0x50F83] = 0x00`; live `A5+0x10A8 = 0x0000` | selector 0, horizontal |

The original scene-init chain does map progression `0x11` to record 17 and selector 1:

```text
byte[0x50EE0 + 0x11] = 0x12
0x50F6B + 0x12 = 0x50F7D
byte[0x50F7D] = 0x01
```

That proves the static reconstruction label. It does **not** make the current automated route a
live selector-1 oracle, because its retained stream pointer has advanced/been selected to record 22
while its descriptor/content boundary still reports record 17. This is a mixed retained state.

Per the task's first gate, the record-17 selector-1 raw-to-world audit stops here. Applying the
static transpose proof to this selector-0 runtime would be invalid, and no conclusion about a
missing or double selector-1 transpose is drawn.

## Why the current evidence cannot justify a fix

The Build-0378 automated route uses the cheat/MODE path and reaches a state whose content record and
direction stream record do not agree. It is therefore not authoritative for Tighe's naturally
controlled third-chain failure. The static image is useful only as a record-17 visualization; it
cannot resolve which retained record/selector Tighe actually has at the blocked exit.

## Bounded user-controlled Genesis trace

Script:

`tools/mame/scripts/build0379_third_chain_user_genesis0378c.lua`

Output directory:

`states/traces/build0379_third_chain_user_genesis0378c/`

The script supplies no game input and performs no emulated-memory writes. The first `M` key rising
edge records `USER_MARK`, arms only the existing Build-0378 player collision/movement PCs, and keeps
720 frames. It records:

- progression, full map-stream pointer, selector, strip/group;
- player state/substate, position, requested and actual motion;
- ground/contact fields, foreground scroll, and special-solid state;
- actual head/side/feet collision probe events and returned words;
- all 16 retained live source pointers/rebuilt descriptors at the mark and every 30 frames.

The script passed a MAME startup/syntax smoke test with Build `0378_c`. Marker input itself remains
for the required interactive run.

Exact command is preserved in
`states/traces/build0379_third_chain_user_genesis0378c/launch_command.txt`.

## User procedure

1. Launch the preserved command.
2. Start Round 1. To shorten the route in `_c`, press MODE once after gameplay begins to enter
   Phase 2; do not press MODE again.
3. Play normally to the third chain and attach to it.
4. Before the final climb into the upper exit, press `M` once. MAME will report `USER_MARK` and that
   the 720-frame window is armed.
5. Climb and use the controls that should carry Rastan through the intended upper exit. If blocked,
   continue the attempted exit for roughly ten seconds.
6. Wait for MAME to report that the trace is complete, then stop MAME.
7. Return `third_chain_states.tsv`, `third_chain_probe_events.tsv`,
   `third_chain_source_tables.tsv`, and `trace_metadata.txt` from the output directory.

The next comparison will first determine whether Tighe's actual state is coherent record 17 /
selector 1. Only if it is will the raw-to-world selector-1 audit proceed. If it instead reproduces
the mixed record-17/record-22 state, the first divergence is the retained record/stream selection,
not the selector-1 transpose.

## Build status

- Build 0379: **NOT BUILT**
- Runtime counter: unchanged at `378`
- Production source/spec changes: **NONE**
- Build 0378_c SHA-256: `ad67c2bf6922c8f1b602b71b391f574b8c04dbea3ef6b64336827e22e17152c4`
