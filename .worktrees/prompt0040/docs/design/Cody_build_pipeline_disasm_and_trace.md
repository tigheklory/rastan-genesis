# Cody - Build Pipeline Disassembly and Trace (Build 0029, rastan-direct)

## 1. Summary
Implemented permanent `rastan-direct` build-pipeline automation in `apps/rastan-direct/Makefile` for:
- post-patch Genesis ROM disassembly output
- automatic 30-second Genesis MAME trace capture
- trace artifact archival under `states/traces/`
- hard failure when `genesis_exec_summary.txt` is missing

Scope was limited to `apps/rastan-direct/Makefile` for implementation logic, with this design document and AGENTS log append as required reporting outputs.

## 2. Phase 1 Verification Results (including execution order)
Required files read before implementation:
- `AGENTS_LOG.md` (latest entries first)
- `docs/design/Cody_build_pipeline_investigation.md`
- `apps/rastan-direct/Makefile` (full)
- `tools/mame/run_genesis_trace_wsl.sh` (full)

Phase 1 confirmations:
- Phase 1 complete: YES
- Disassembly command confirmed: YES
- Makefile insertion point for disassembly confirmed: YES - line 85 (post-patch boot guard), disassembly inserted immediately after
- Build counter end line confirmed: YES - line 108 (end of shell block), `tag` defined at line 93
- `tag` available after counter block: YES
- Trace script invocation confirmed: YES
  - full command: `timeout 120s "$(ROOT)/tools/mame/run_genesis_trace_wsl.sh" "$@" -video none -sound none -nothrottle -seconds_to_run 30`
- Trace output location confirmed: YES
  - script native output: `$(ROOT)/build/mame/home/genesistrace/`
  - archival output: `$(ROOT)/states/traces/$(NUMBERED_PREFIX)_${tag}_mame_30s_${trace_ts}/`
- Output copy required: YES
- Execution order confirmed: YES

Confirmed execution order implemented:
1. boot guard (post-patch)
2. disassembly (`build/genesis_postpatch.disasm.txt`)
3. build counter block (defines `tag`)
4. 30s Genesis trace
5. trace confirmation (`genesis_exec_summary.txt` existence)

## 3. Exact Makefile Changes Made (before/after insertion points)
File modified: `apps/rastan-direct/Makefile`

### Insertion point A: tool variable / fallback
Before:
```make
NM := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-nm
```
After:
```make
NM := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-nm
OBJDUMP := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-objdump
```
And fallback block adds:
```make
OBJDUMP := m68k-elf-objdump
```

### Insertion point B: release target
Before:
```make
.PHONY: all clean
all: $(BIN)
```
After:
```make
.PHONY: all clean release
all: $(BIN)
release: $(BIN)
```

### Insertion point C: post-patch disassembly (immediately after boot guard)
Before:
```make
$(PYTHON) "$(BOOT_GUARD)" --rom "$@"
@mkdir -p "$(NUMBERED_DIST_DIR)" "$(dir $(NUMBERED_COUNTER))"
```
After:
```make
$(PYTHON) "$(BOOT_GUARD)" --rom "$@"
@mkdir -p "$(ROOT)/build"
$(OBJDUMP) -D -b binary -m m68k:68000 --adjust-vma=0 "$@" > "$(ROOT)/build/genesis_postpatch.disasm.txt"
@mkdir -p "$(NUMBERED_DIST_DIR)" "$(dir $(NUMBERED_COUNTER))"
```

### Insertion point D: automatic trace + confirmation (after existing counter block)
Extended the existing shell block after numbered artifact copy to:
- create `trace_ts`
- create destination trace directory with build `tag`
- run Genesis trace command (30s)
- copy trace artifacts from script output directory
- verify `genesis_exec_summary.txt` exists in destination

## 4. Disassembly Command Used and Output Path
Command used in pipeline:
```bash
$(OBJDUMP) -D -b binary -m m68k:68000 --adjust-vma=0 "$@" > "$(ROOT)/build/genesis_postpatch.disasm.txt"
```
Observed output path:
- `build/genesis_postpatch.disasm.txt`

## 5. Full Trace Invocation Command (verbatim) and Output Convention
Verbatim trace command used in Makefile:
```bash
timeout 120s "$(ROOT)/tools/mame/run_genesis_trace_wsl.sh" "$@" -video none -sound none -nothrottle -seconds_to_run 30
```

ROM type: genesis (script uses `MACHINE=genesis` + `-cart`).

Output directory convention:
- `states/traces/rastan_direct_video_test_build_<tag>_mame_30s_<YYYYMMDD_HHMMSS>/`

Observed example from validation run:
- `states/traces/rastan_direct_video_test_build_0032_mame_30s_20260415_010931`

## 6. Output Copy/Move Logic
Output copy is required because `run_genesis_trace_wsl.sh` writes to fixed path:
- source: `build/mame/home/genesistrace/`

Copied files into `trace_dir`:
- `genesis_exec_summary.txt` (required)
- `genesis_exec_trace.log` (required)
- `trace_metadata.txt` (optional if present)
- `mame_stdout.txt` (optional if present)

## 7. Trace Confirmation Step Implementation
Implemented hard failure check after copy:
```bash
if [ ! -f "$$trace_dir/genesis_exec_summary.txt" ]; then
  echo "ERROR: Missing genesis_exec_summary.txt in trace output: $$trace_dir"
  exit 1
fi
```
This enforces non-silent trace success.

## 8. Validation Results
### V1. Build verification
Command run:
```bash
source tools/setup_env.sh
make -C apps/rastan-direct clean
make -C apps/rastan-direct release
```
Result: PASS
- disasm produced: `build/genesis_postpatch.disasm.txt`
- trace dir produced: `states/traces/rastan_direct_video_test_build_0032_mame_30s_20260415_010931`
- summary present: `genesis_exec_summary.txt`

### V2. Disassembly content check
PASS
- file exists and non-empty (`14M`)
- header confirms binary source:
  - `dist/rastan_direct_video_test.bin:     file format binary`

### V3. Trace directory check
PASS
- naming convention matches required pattern
- `<tag>` value matches incremented build counter (`0032`)
- required files present:
  - `genesis_exec_summary.txt`
  - `genesis_exec_trace.log`

### V4. Regression check
PASS
Pre/post SHA256 identical:
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - `b0445a2917a07cd094b476c1afb70a987ba4ed2e31f08d8d647bc0ba3d486332`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
  - `a3ead76e46d00c3064b487917d3644a01a7a29d65f1d31fec36a6cea2a9c3995`
- `build/rastan-direct/address_map.json`
  - `d3fdab3345c166821e56568f37e426ff916dfff21fe5efa6de2664697750f9a7`

MAME trace final PC check:
- `0x000010` (from latest recorded MAME exit summary entry in `AGENTS_LOG.md`, 2026-04-15 01:08:17).

## 9. Regression Confirmation
No source/patch/spec behavior changed; automation is build-pipeline orchestration only.
Artifacts controlling patch semantics remained byte-identical after implementation and validation rebuild.

## 10. Next-Step Impact
- Post-patch ROM disassembly is now automatically captured each `rastan-direct` release build.
- Genesis 30-second trace is now automatically archived per build number and timestamp.
- Build now fails fast if trace summary is missing, preventing silent trace regressions.
