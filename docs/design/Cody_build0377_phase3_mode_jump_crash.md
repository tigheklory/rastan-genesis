# Cody Build 0377 — Phase-3 MODE jump crash

## A. Resume state and scope

Build 0376 is the baseline. Its accepted `0x05A334` collision-surface publication and
`0x05109C` directional producer redirect remain unchanged. This task does not revisit the
second-rope `C0ABE0` fault or the third-rope blockage.

The resumed proof began with the user-observed Build-0376 Phase-3 failure: the copied routine
at final `0x059784` consumed cartridge ROM through the stale arcade-WRAM address
`0x0010C118`, obtained selector 8, and constructed `A0=0x1AC41AD0`.

## B. Current routine and caller

- Original function: `FUN_000596f4` / Phase-3 foreground animation producer.
- Build-0377 entry: `0x059784`.
- Caller: `player_main_update_51090`, original call `0x0510B2`, Build-0377 call
  `0x0512BE`.
- Gate: `cmpi.w #1,A5+0x1360`; a nonmatching value returns through the shared RTS.
- Selector read: original `0x059704`, `move.b 0x0010C118,D0` (byte width); Build-0376
  final `0x059794` retained that stale address.

The original arithmetic is `D0=(selector-1)*6`. The table at original `0x05976E` contains
six records, so the legal one-based selector domain is `1..6`.

## C. Existing OPEN-017 address meaning

`Cody_attract_demo_scripted_input_provenance_audit.md` previously proved that arcade
`0x0010C118` is the stage byte at `A5+0x0118`, retained on Genesis at `0x00FF0118`.
The focused Build-0376 `_c` trace confirms that field is `1` before, during, and after both
MODE jumps. It remains `1` when progression changes to `0x0016/0x0017` and the animation gate
`A5+0x1360` becomes `1`. Thus the legal offset is zero, not `0x42`.

This is the same raw-absolute-WRAM address-contract family as OPEN-017, but a different
consumer and table. The Build-0255 fix was an explicit replacement only at `0x052B66`; it did
not cover `0x059704`. Later shift/reflow did not create this omission.

## D. Table contract and malformed A0 proof

Each six-byte record is:

| Selector | Original stream pointer | Fixed attribute |
|---:|---:|---:|
| 1 | `0x059792` | `0x001E` |
| 2 | `0x0597F6` | `0x0012` |
| 3 | `0x05983A` | `0x0019` |
| 4 | `0x059792` | `0x0007` |
| 5 | `0x05987E` | `0x0000` |
| 6 | `0x059880` | `0x0000` |

The longword is a copied-ROM animation-stream pointer. The word is the common PC080SN
attribute written for each cell. A nonzero stream begins with `{phase_count.w,
group_count.w}`. Each group then contains two raw Layer-A destination longwords followed by
one code word per phase. `A5+0x1362` selects a code at quarter-speed and wraps against the
phase count.

Build 0376 selector 8 gives `(8-1)*6 = 0x42`. Its final table base is `0x0597FE`, so the
out-of-range record begins at `0x059840`. The exact six bytes are:

```text
1A C4 1A D0 1A C4
```

`move.w 4(A0),D6` independently loads `D6=0x1AC4`; `movea.l (A0),A0` independently loads
`A0=0x1AC41AD0`. D6 is not combined into A0. The next instruction, final Build-0376
`0x0597AA: move.w (A0),D4`, addresses low-24-bit `0xC41AD0`, exactly explaining BlastEm.
An emulator that continues then consumes additional malformed stream data, explaining the
later reported write-side failure without a second root cause.

## E. Embedded-pointer audit

The table itself was not correct on Genesis: all six longwords still contained original ROM
addresses. Build 0377 extends the declarative absolute-long table schema with independent
record stride and pointer offset, then declares `0x05976E` as six records of stride 6 with a
four-byte pointer at offset zero. The generated manifest reports six fixes.

Build-0377 final records at `0x0597CE` are:

```text
000597F2 001E
00059856 0012
0005989A 0019
000597F2 0007
000598DE 0000
000598E0 0000
```

For live Stage 1, selector 1 therefore chooses offset zero and stream `0x0597F2`; its header
is `0004 0006` (four phases, six groups). The attribute remains `0x001E`.

## F. Native semantic cut

Correcting the selector and pointer table would expose the retained stream's raw PC080SN
writes. The semantic cut is original `0x059736..0x05976C`: selection, stream decoding,
destination identity, code selection, and timing remain arcade-owned; only the chip-specific
two-destination write loop is retired. `genesistan_phase3_fg_anim_native` publishes the same
attribute/code pair to both retained Layer-A cells through the existing final Plane-A staging
and dirty-row path, and preserves the original `A5+0x1362` cadence.

The original shared RTS at `0x05976C` remains in copied code. The canonical linear objdump
misses the preceding `0x0596F4` boundary, so it also omitted the `0x0596FA -> 0x05976C`
short branch from automatic reflow. Build 0377 adds a validated declarative relative-branch
record; final `0x05978A` is `BNE.S 0x0597CC`. An unnumbered candidate caught this boundary
before release; no extra build number was consumed.

## G. Bounded sibling `0x0010C118` audit

- `0x052B66`: **REBASED** by Build 0255; attract-demo family.
- `0x059704`: **STALE AND LIVE** in the reported Phase-3 player path; fixed in Build 0377.
- `0x055F42`, `0x0561D8`, `0x056200`, `0x05632C`: stale sites in the separate
  `0x055DDC` transition-presentation state machine. None executed during the measured `_c`
  MODE×2 immediate route, so they are classified **STALE BUT UNREACHED IN THIS ROUTE**, not
  silently claimed globally unreachable and not speculatively changed here.
- `0x04CC2C`: **OTHER**; per-round actor dispatch outside the bounded Phase-3 animation
  consumer.

The trace used a read tap on raw `0x0010C118`; it recorded no raw read on the fixed numbered
route.

## H. MODE versus natural entry

Classification: **production defect, not a MODE initialization defect**. MODE does not own or
change `A5+0x0118`; the live value was already the legal Stage-1 value `1` and stayed `1`.
Natural R1 boss-room entry uses the same Stage-1 field and copied player update. MODE merely
made the stale absolute consumer readily reachable in the user's strict-emulator route.

## I. Validation

- Canonical gate: PASS.
- Genesis NTSC MAME gameplay-entry gate: PASS; player control observed; zero address errors,
  bus errors, illegal instructions, or crash-handler entries.
- Build-0377 `_c`, MODE×2: progression reached `0x0016`, then boss-room state `0x0017`;
  `A5+0x0118=1`, `A5+0x1360=1`, and the crash record remained inactive.
- Third MODE: round-phase state advanced from `0x16` to `0x17`, providing the requested Round-2
  debug access path.
- The known superseded seven-epoch diagnostic gate retains its existing FAIL label; the build
  policy preserved the artifact.
- Boss-room visual completeness, player control in that exact room, and the user's original
  BlastEm reproduction remain user acceptance checks.

## J. Build and preservation

Build 0377 is the only numbered build produced; counter `376 -> 377`. All five variants exist.

- Canonical: `dist/rastan-direct/rastan_direct_video_test_build_0377.bin`
  - SHA-256: `4b43a28e6667759e412e9fb5e1d95f18024e8b3df4cfc94497031f4270203080`
  - size: 1,719,992 bytes
- `_c`: `dist/rastan-direct/rastan_direct_video_test_build_0377_c.bin`
  - SHA-256: `68727544ef3e9cd450a7ea873b38c3db16056028a05d25b156fca4961dcb5799`
  - size: 1,724,088 bytes

Build 0376's `0x05A334` native surface publication and `0x05109C` directional redirect remain
present. Rejected Build-0375 residency-preinstall behavior was not restored. The third-rope
issue was not touched.
