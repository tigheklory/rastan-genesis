# MAME on WSL for Rastan

This directory is the repo-local MAME setup for Rastan analysis.

It is meant to give us:

- one consistent way to launch MAME from this repo
- cheat support through `cheat.7z`
- an automatic `rastanmon` plugin that logs mode changes and palette-shadow
  changes while you play
- a separate `rastantrace` execution tracer for boot/title/attract analysis

## What this setup does

The wrapper script:

- points MAME at the repo `roms/` directory
- keeps MAME state under `build/mame/home/`
- launches MAME in a window by default
- enables the stock MAME `cheat` plugin
- runs a repo-local `rastanmon` Lua monitor automatically after boot

The `rastanmon` Lua monitor:

- watches the main CPU program space
- logs top-level mode words we have already traced
- polls the live palette shadow region at `0x200000`
- writes a log file you can review after a run

The `rastantrace` Lua tracer:

- samples the main CPU `PC`
- labels execution when it enters known startup/title/helper ranges
- tracks touches to the exact arcade address windows we have been remapping
- writes a trace log plus a compact summary

The `rastantrace_lite` Lua tracer:

- keeps the same scene/range intent
- avoids per-access logging on hot regions
- samples window changes in a coarse round-robin scan
- is intended for longer title/attract runs

## 1. Install MAME in WSL

I could not complete this step from here because package install requires root on
your machine.

Run this in WSL:

```bash
sudo apt-get update
sudo apt-get install -y mame mame-data mame-tools p7zip-full
```

You will also need WSLg working if you want the MAME window to display on your
desktop.

## 2. Put `cheat.7z` in the repo-local cheat folder

Put the inner `cheat.7z` file here:

```text
tools/mame/cheat/cheat.7z
```

Do not unpack the `7z`.

If you download the outer archive from Pugsy's site, extract it once and then
place the inner `cheat.7z` in the folder above.

## 3. Launch Rastan

From the repo root:

```bash
tools/mame/run_rastan_wsl.sh
```

To launch a different clone:

```bash
tools/mame/run_rastan_wsl.sh rastanu
```

You can pass extra MAME options after the machine name:

```bash
tools/mame/run_rastan_wsl.sh rastan -window -nomax
```

## 3a. Launch the execution tracer

Use this when you want a boot/title/attract execution trace instead of the
palette/mode monitor:

```bash
tools/mame/run_rastan_trace_wsl.sh
```

It uses the same ROM, cheat, and home paths, but swaps the autoboot script to
`rastantrace.lua`.

## 3b. Launch the lite execution tracer

Use this for longer title/attract observation when the heavy tracer is slowing
MAME down too much:

```bash
tools/mame/run_rastan_trace_lite_wsl.sh
```

## 3c. Launch the Genesis target-ROM tracer

Use this to debug the Genesis output ROM directly (instead of the arcade
`rastan` machine):

```bash
tools/mame/run_genesis_trace_wsl.sh
```

You can pass a specific ROM path as the first argument:

```bash
tools/mame/run_genesis_trace_wsl.sh dist/Rastan_59_20260316_170643.bin
```

You can also switch machine with:

```bash
MAME_GENESIS_MACHINE=megadriv tools/mame/run_genesis_trace_wsl.sh
```

## 4. Cheat usage

This setup enables the stock MAME cheat plugin automatically.

In-game:

1. press `Tab`
2. open `Cheat`
3. enable the cheats you want for the current set

If the desired cheats are not present in the downloaded archive, we can add
repo-local overrides later.

## 5. Automatic monitoring

The monitor writes to:

```text
build/mame/home/rastanmon/rastan_monitor.log
```

The execution tracer writes to:

```text
build/mame/home/rastantrace/rastan_exec_trace.log
build/mame/home/rastantrace/rastan_exec_summary.txt
```

The lite tracer writes to:

```text
build/mame/home/rastantrace_lite/rastan_exec_trace_lite.log
build/mame/home/rastantrace_lite/rastan_exec_summary_lite.txt
```

The Genesis tracer writes to:

```text
build/mame/home/genesistrace/genesis_exec_trace.log
build/mame/home/genesistrace/genesis_exec_summary.txt
```

It currently logs:

- `a5 + 0x00` at `0x10c000`
- `a5 + 0x02` at `0x10c002`
- `a5 + 0x04` at `0x10c004`
- credits at `0x10c012`
- stage id at `0x10c13e`
- `a5 + 0x118` at `0x10c118`
- `a5 + 0x13aa` at `0x10d3aa`
- `a5 + 0x13ac` at `0x10d3ac`
- `a5 + 0x13ae` at `0x10d3ae`
- `a5 + 0x13b0` at `0x10d3b0`
- `a5 + 0x28`, `0x2a`, `0x2c`, `0x34`, `0x46`
- `a5 + 0x1392`, `a5 + 0x1394`

It also polls palette-shadow blocks in:

```text
0x200000 .. 0x2008ff
```

and logs any 16-color block that changes.

It also writes:

- field-change events for important mode words
- scene markers using the current best mode-flow interpretation
- scene palette snapshots under:
  `build/mame/home/rastanmon/snapshots/`

This is deliberately scene-oriented. It is not trying to be a full debugger UI.
It is meant to let you keep playing while still collecting useful palette/mode
evidence.

## 5a. Execution tracing

The execution tracer is aimed at the exact startup/title bring-up problem.

It tracks:

- scene changes based on the same top-level mode words
- sampled `PC` values
- entry into known RE ranges such as:
  - `startup_common`
  - `frontend_title_cluster`
  - `title_init_block`
  - `helper_3f084_reg_write`
- touches to the important arcade-side windows:
  - `0x10c000..0x10ffff`
  - `0x200000..0x203fff`
  - `0xc00000..0xc0ffff`
  - `0xc20000`
  - `0xc40000`
  - `0xc50000`
  - `0xd00000..0xd007ff`
  - `0xd01bfe`
  - `0x350008`
  - `0x380000`
  - `0x390009`
  - `0x39000b`
  - `0x3c0000`
  - `0x3e0001`
  - `0x3e0003`

The summary file is meant to answer:

- which startup/title ranges actually executed
- which remapped windows were really touched
- which addresses were first touched, and from which `PC`

The lite tracer is meant to answer the same questions with much lower overhead,
trading detail for usable runtime speed.

## 5b. Genesis tracing details

The Genesis tracer (`genesistrace.lua`) is aimed at target-ROM bring-up and
tracks:

- sampled Genesis `maincpu` `PC`
- entry into key startup/title ranges at both base and `+0x0200` relocated
  offsets
- coarse signatures over key Genesis windows (WRAM, I/O, VDP ports, Z80 control)
- symbol-backed project state changes loaded from:
  `apps/rastan/out/symbol.txt`

## 6. Notes

- The palette logger is watching the live color shadow region, not just static
  ROM tables.
- Scene names are still best-effort labels based on the current RE docs. The
  raw words are still logged so we do not over-trust an interpretation.
- The next step after using this should be turning the collected logs and
  snapshots into scene-by-scene palette reports.
