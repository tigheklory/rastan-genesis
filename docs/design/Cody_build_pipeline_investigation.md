# Cody — Build Pipeline Investigation (Build 0029, rastan-direct)

## Summary
This investigation audited the existing `rastan-direct` build pipeline, toolchain, and MAME trace infrastructure to determine what already exists versus what must be added for automatic post-patch disassembly generation and automatic trace capture.

## Disassembly Toolchain Findings (Question 1)
- `m68k-elf-objdump` availability: YES.
  - Evidence:
    - `tools/setup_env.sh` exports `M68K_ELF_ROOT` and prepends `$M68K_ELF_ROOT/bin` to `PATH` (`tools/setup_env.sh:10,13`).
    - After sourcing env, `command -v m68k-elf-objdump` resolved to:
      `/home/tighe/projects/rastan-genesis/tools/local/toolchain/m68k-elf/bin/m68k-elf-objdump`.
- Existing disassembly pattern:
  - `tools/disasm_maincpu.sh` uses:
    - `m68k-elf-objdump -D -b binary -m m68k:68000 --adjust-vma=0 <input> > <output>`
    - Evidence: `tools/disasm_maincpu.sh:12-18`.
- Final patched Genesis ROM path from `rastan-direct` build:
  - Relative: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - Variable: `BIN := $(DIST_DIR)/rastan_direct_video_test.bin`
  - Evidence: `apps/rastan-direct/Makefile:41,71-81`.
- Exact disassembly command needed for final patched Genesis ROM:
```bash
source tools/setup_env.sh && \
m68k-elf-objdump -D -b binary -m m68k:68000 --adjust-vma=0 \
  apps/rastan-direct/dist/rastan_direct_video_test.bin \
  > build/genesis_postpatch.disasm.txt
```

## Makefile Insertion Point Findings (Question 2)
- Final target producing patched ROM:
  - `$(BIN)` where `BIN := $(DIST_DIR)/rastan_direct_video_test.bin`
  - Target recipe starts at `apps/rastan-direct/Makefile:71`.
- Current success gating:
  - Standard Make recipe command chaining; any non-zero exit aborts target.
  - Critical patch success points are:
    - postpatch invocation (`Makefile:75-81`)
    - postpatch boot guard validation (`Makefile:82`)
- Correct insertion point for automatic post-patch disassembly so it only runs on success:
  - Immediately after `$(PYTHON) "$(BOOT_GUARD)" --rom "$@"` (line 82), before numbered artifact copy block (line 83 onward).
  - Rationale: guarantees ROM is patched and validated before disassembly runs.

## MAME Trace Infrastructure Findings (Question 3)
- Existing scripts in `tools/` invoking MAME for tracing: YES.

### Script: Genesis trace harness
- Path: `/home/tighe/projects/rastan-genesis/tools/mame/run_genesis_trace_wsl.sh`
- Command it runs:
  - `exec "${MAME_BIN}" "${MACHINE}" -cart "${CART}" ... -autoboot_script "${ROOT}/tools/mame/scripts/genesistrace.lua" "$@"`
  - Evidence: `tools/mame/run_genesis_trace_wsl.sh:59-73`.
- ROM type: **genesis** (uses `MACHINE=genesis` and `-cart`).

### Script: Arcade trace harness
- Path: `/home/tighe/projects/rastan-genesis/tools/mame/run_rastan_trace_wsl.sh`
- Command it runs:
  - `exec "${MAME_BIN}" "${MACHINE}" ... -rompath "${ROOT}/roms" ... -autoboot_script ".../rastantrace.lua" "$@"`
  - Evidence: `tools/mame/run_rastan_trace_wsl.sh:34-45`.
- ROM type: **arcade** (`MACHINE=rastan`, `-rompath` arcade set).

### Script: Arcade trace lite harness
- Path: `/home/tighe/projects/rastan-genesis/tools/mame/run_rastan_trace_lite_wsl.sh`
- Command it runs:
  - `exec "${MAME_BIN}" "${MACHINE}" ... -autoboot_script ".../rastantrace_lite.lua" "$@"`
  - Evidence: `tools/mame/run_rastan_trace_lite_wsl.sh:34-45`.
- ROM type: **arcade**.

### Script: Arcade jump trace harness
- Path: `/home/tighe/projects/rastan-genesis/tools/mame/run_rastan_jumptrace_wsl.sh`
- Command it runs:
  - `exec "${MAME_BIN}" "${MACHINE}" ... -autoboot_script ".../rastanjumptrace.lua" "$@"`
  - Evidence: `tools/mame/run_rastan_jumptrace_wsl.sh:38-49`.
- ROM type: **arcade**.

### Script: Arcade monitor harness
- Path: `/home/tighe/projects/rastan-genesis/tools/mame/run_rastan_wsl.sh`
- Command it runs:
  - `exec "${MAME_BIN}" "${MACHINE}" ... -autoboot_script ".../rastanmon.lua" "$@"`
  - Evidence: `tools/mame/run_rastan_wsl.sh:35-46`.
- ROM type: **arcade**.

- Does existing infrastructure distinguish ROM type: YES.
  - Genesis path uses `-cart` + `MACHINE=genesis` (`run_genesis_trace_wsl.sh:5,59-61`).
  - Arcade paths use `MACHINE=rastan` + `-rompath` (`run_rastan*_wsl.sh`).

- Exact command used in previous builds for the **30-second trace** (from AGENTS_LOG):
  - **UNKNOWN**.
  - Reason: AGENTS_LOG records `trace saved to: states/traces/..._mame_30s_...` for build 0027/0028/0029 (`AGENTS_LOG.md:27001,27026`), but does not include the exact full command line for those 30s runs.
  - Last explicit genesis trace command string present in AGENTS_LOG is older and not explicitly a `30s` trace command entry:
    - `timeout 120s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_272.bin -autoboot_script /tmp/phase1_runtime_ordering_genesis_probe.lua -sound none -video none`
    - Evidence: `AGENTS_LOG.md:21575`.

- Trace output path/filename convention from evidence:
  - Directory naming pattern under `states/traces/`:
    - `rastan_direct_video_test_build_<build>_mame_<duration>s_<YYYYMMDD_HHMMSS>/`
    - Evidence examples:
      - `states/traces/rastan_direct_video_test_build_0027_mame_30s_20260412_232548`
      - `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_181500`
      - listed in AGENTS log (`AGENTS_LOG.md:27001,27026`) and filesystem listing.
  - File names within trace directory:
    - `genesis_exec_summary.txt`
    - `genesis_exec_trace.log`
    - sometimes also `mame_stdout.txt`, `trace_metadata.txt` (seen in older trace dirs)
    - Evidence: `find states/traces -maxdepth 2 -type f`.

## Build Number Tracking Findings (Question 4)
- Build number tracking exists in `apps/rastan-direct/Makefile`.
- Storage location:
  - `NUMBERED_COUNTER := $(ROOT)/build/rastan-direct/build_counter.txt`
  - Evidence: `Makefile:15`.
- Increment mechanism:
  - Shell block reads counter, increments, writes back, formats `tag` as 4 digits, and copies numbered artifact.
  - Evidence: `Makefile:84-91`.
- Can build number be read in Makefile for trace filenames: YES.
  - Same shell block currently reads it from `build_counter.txt` and computes `tag` (`Makefile:84-89`).

## states/traces Directory Findings (Question 5)
- `states/traces/` exists: YES.
  - Evidence: directory listing.

Current entries:
- `rastan_direct_bss_relocation_20s_20260412_180111`
- `rastan_direct_video_test_build_0024_mame_20s_20260412_113620`
- `rastan_direct_video_test_build_0025_mame_30s_20260412_181636`
- `rastan_direct_video_test_build_0027_mame_30s_20260412_232548`
- `rastan_direct_video_test_build_0028_mame_30s_20260413_112440`
- `rastan_direct_video_test_build_0028_mame_30s_20260413_113538`
- `rastan_direct_video_test_build_0029_mame_30s_20260413_181500`
- `rastan_direct_video_test_build_0029_mame_30s_20260413_212116`

Naming convention observed:
- Primary: `<rom_id>_build_<build>_mame_<duration>s_<timestamp>`
- Variant older format also present: `rastan_direct_bss_relocation_<duration>s_<timestamp>`

## Recommended Implementation Scope (what to create vs what exists)
Already exists:
- Toolchain binary for post-patch disassembly (`m68k-elf-objdump` in repo toolchain).
- Final patched ROM output target in Makefile (`apps/rastan-direct/dist/rastan_direct_video_test.bin`).
- MAME Genesis trace harness (`tools/mame/run_genesis_trace_wsl.sh`).
- Arcade trace harnesses (separate scripts).
- Build counter storage/increment logic (`build/rastan-direct/build_counter.txt`).
- Historical trace directory naming convention and trace artifact files in `states/traces/`.

Needs to be created for automatic rastan-direct build integration:
1. A Makefile post-patch disassembly command in `$(BIN)` recipe (after boot guard pass).
2. A Makefile post-build trace command for Genesis ROM (rastan-direct target scope is Genesis artifact).
3. Trace archive/copy step from `build/mame/home/genesistrace/*` into a build-numbered `states/traces/...` directory if deterministic per-build trace retention is required.
4. Explicit command logging into AGENTS_LOG or build output if exact command provenance is required for future audits.

Automation scope recommendation based on evidence:
- **Genesis trace automation for rastan-direct build target** should be primary (build artifact is Genesis ROM).
- Arcade trace scripts should remain available as separate/manual cross-reference tools.
