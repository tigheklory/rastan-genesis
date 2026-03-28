# Phase 1 Runtime Ordering Proof

## 1) Method Used
- Harness: `tools/mame/run_genesis_trace_wsl.sh`
- ROM: `dist/Rastan_272.bin`
- Autoboot script used for this verification run: `/tmp/phase1_runtime_ordering_genesis_probe.lua`
- Command executed:
```bash
timeout 120s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_272.bin \
  -autoboot_script /tmp/phase1_runtime_ordering_genesis_probe.lua \
  -sound none -video none
```
- Trace output captured from runtime taps:
  - producer tap: `PC=0x059F5E`
  - renderer bridge tap: `PC=0x202B80` (`genesistan_render_sprites_vdp_bridge`)
- Raw log file: `/tmp/phase1_runtime_ordering_genesis_probe.txt`

## 2) Title-State Proof
Runtime event context from raw trace:
- `tag=renderer pc=202B80 A5=E0FF004C state=0001/0000/0000 mode4=0000 credits=0000`
- This is the game work-RAM state tuple used in prior title-path tracing (`state=major/sub/step`).
- Event is in the real game producer/renderer path (`0x202B80`), not launcher UI text, not exception handler text, and not debug overlay text.

## 3) Raw Trace Output (Required)
From `/tmp/phase1_runtime_ordering_genesis_probe.txt`:

```text
seq=001 frame=000671 tag=renderer pc=202B80 A5=E0FF004C state=0001/0000/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=002 frame=000672 tag=renderer pc=202B80 A5=E0FF004B state=5000/0100/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0080 0000 0000 0000
seq=003 frame=000672 tag=renderer pc=202B80 A5=E0FF004B state=5000/0100/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0080 0000 0000 0000
STOP frame=000900 seq=3
```

Also from same raw file:

```text
probe_start start_field=true
heartbeat frame=000660 screen=0000 mode4=0000 credits=0000
```

Producer tap result in this run:
- `0x059F5E` hit count: `0`

Renderer tap result in this run:
- `0x202B80` hit count: `3`

## 4) Frame-by-Frame Ordering (3 Observations)
Observation 1:
- Frame `671`
- Producer (`0x059F5E`) hit: `NO`
- Renderer (`0x202B80`) hit: `YES` (seq=001)
- Ordering: renderer executed without producer hit in this title-init state pass.

Observation 2:
- Frame `672`
- Producer (`0x059F5E`) hit: `NO`
- Renderer (`0x202B80`) hit: `YES` (seq=002)
- Ordering: renderer again executed without producer hit.

Observation 3:
- Frame `672`
- Producer (`0x059F5E`) hit: `NO`
- Renderer (`0x202B80`) hit: `YES` (seq=003)
- Ordering: renderer executed again; producer still not observed.

## 5) Descriptor State (at renderer entry)
At `seq=001` (`frame=671`, first renderer entry):
- Block-A (`FF11FE..FF1204`): `0000 0000 0000 0000` (zero)
- Block-B (`FF01BC..FF01C2`): `0000 0000 0000 0000` (zero)

At `seq=002/003` (`frame=672`, renderer entries):
- Block-A: `0000 0000 0000 0000` (still zero)
- Block-B: `0080 0000 0000 0000` (partially non-zero)
- Unexpected state note: `A5=E0FF004B` and sampled `state=5000/0100/0000` at these two entries.

## 6) Final Conclusion (Required)
Runtime proof shows that the ordering is incorrect during the real title-init path.
