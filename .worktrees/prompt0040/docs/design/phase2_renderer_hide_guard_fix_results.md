# Phase 2 Renderer Hide Guard Fix Results

## 1. Purpose
Apply the single approved renderer-side fix in `genesistan_render_sprites_vdp` so valid block-A tuples are not hidden solely because `word0 == 0`, while preserving hidden behavior for truly empty tuples and the arcade hidden sentinel (`word1 == 0x0180`).

## 2. Exact Code Change
File changed: `apps/rastan/src/main.c`

Target function: `genesistan_render_sprites_vdp`

Before:
```c
u16 data = (u16)(((u16)entry[0] << 8) | entry[1]);
u16 y_raw = (u16)(((u16)entry[2] << 8) | entry[3]);
const u16 code = (u16)((((u16)entry[4] << 8) | entry[5]) & 0x3FFF);
s16 x = (s16)((((u16)entry[6] << 8) | entry[7]) & 0x01FF);
...
if (data == 0)
    y_raw = 0x0180;
```

After:
```c
u16 data = (u16)(((u16)entry[0] << 8) | entry[1]);
u16 y_raw = (u16)(((u16)entry[2] << 8) | entry[3]);
const u16 code = (u16)((((u16)entry[4] << 8) | entry[5]) & 0x3FFF);
const u16 x_raw = (u16)(((u16)entry[6] << 8) | entry[7]);
s16 x = (s16)(x_raw & 0x01FF);
...
if ((data == 0) && (y_raw == 0) && (code == 0) && (x_raw == 0))
    y_raw = 0x0180;
```

Chosen option: narrow the guard (not full removal).

Reason: this keeps safe suppression for truly empty entries while no longer hiding authentic arcade tuples like `0000/00E8/03CA/0010`.

## 3. Build Performed
Command:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact:
- `dist/Rastan_278.bin`
- Build output line: `Release: ../../dist/Rastan_278.bin`

## 4. Runtime Tuple Verification
Probe run:
```bash
timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_278.bin \
  -autoboot_script /tmp/phase2_guardfix_probe.lua -sound none -video none
```

Probe output: `/tmp/phase2_guardfix_probe.txt`

Required tuple observed at runtime:
- `target_tuple frame=672 w0=0000 w1=00E8 w2=03CA w3=0010`
- same tuple repeats through subsequent renderer passes (38 hits total)

Execution hit counts:
- `HIT 03AAEC 1`
- `HIT 03AAF2 1`
- `HIT 05A174 1`
- `HIT 2005C4 198`
- `HIT 03BD5E 5`
- `HIT 20034C 5`

## 5. Renderer Guard Verification
For the same live tuple (`0000/00E8/03CA/0010`), probe captured old vs new guard evaluation:

- `old_guard = (word0==0)` -> `true`
- `new_guard = (w0==0 && w1==0 && w2==0 && w3==0)` -> `false`

Aggregates from probe:
- `target_tuple_hits=38`
- `old_guard_true=38`
- `new_guard_true=0`

Interpretation: the previous guard would have hidden all 38 valid tuple instances; the new narrowed guard does not hide those instances.

## 6. Visual Verification
Capture run:
```bash
timeout 220s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_278.bin \
  -autoboot_script /tmp/phase2_blocka_restore_probe.lua \
  -aviwrite /tmp/build278_guardfix_logo.avi -sound none
```

Extracted frame:
- `/tmp/build278_guardfix_frame700.png`

Observed result in this capture:
- no visible sprite/logo pixels confirmed.

Visual classification: **FAIL** (no visible sprite/logo pixels confirmed).

## 7. Regression Check
- Renderer still protects truly empty tuples:
  - guard now hides only all-zero tuple (`w0=w1=w2=w3=0`).
- Real text path still executes:
  - `HIT 03BD5E 5`
  - `HIT 20034C 5`
  - selector sample includes `D0_AT_03BD5E 00000002 1` (CREDIT selector dispatch observed)

CREDIT visual appearance was not reconfirmed in this black-frame capture sequence.

## 8. Final Result
- Single-file renderer guard narrowing was applied exactly in `main.c`.
- Runtime tuple evidence confirms authentic block-A tuple instances are no longer auto-hidden by `word0 == 0` alone.
- Visual sprite/logo pixels are still not confirmed in this run, so this pass is not yet a visual title-logo success.

Guard fix applied: narrowed hide guard to all-zero tuple only (`(data==0 && y_raw==0 && code==0 && x_raw==0)`)
Runtime tuple result: valid tuple `0000/00E8/03CA/0010` observed 38 times; old guard true 38/38, new guard true 0/38
Visual result: FAIL (no visible logo sprite pixels confirmed)
Regression result: text producer path still executes (including D0=2 selector dispatch); empty tuple suppression preserved
