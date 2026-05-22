SHELL := /bin/bash

ROOT := ../..
OUT_DIR := out
DIST_DIR := dist
SRC_DIR := src
PYTHON ?= python3
VARIANT ?= world_rev1
PATCH_SPEC := $(ROOT)/specs/rastan_direct_remap.json
PATCH_MANIFEST := $(ROOT)/build/rastan-direct/rastan_direct_patch_manifest.json
SYMBOLS := $(OUT_DIR)/symbol.txt
PATCHER := $(ROOT)/tools/translation/postpatch_startup_rom.py
BOOT_GUARD := $(ROOT)/tools/translation/verify_rastan_direct_boot_guard.py
CANONICAL_GATE := $(ROOT)/tools/translation/verify_canonical_rom.py
REGION_BUILDER := $(ROOT)/tools/build_rastan_regions.py
NUMBERED_DIST_DIR := $(ROOT)/dist/rastan-direct
NUMBERED_COUNTER := $(ROOT)/build/rastan-direct/build_counter.txt
NUMBERED_PREFIX := rastan_direct_video_test_build
HELPER_CANONICAL_SHA ?= 20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb
BOOKMARK_REVERT ?=
BOOKMARK_STATE_FILE := $(ROOT)/build/rastan-direct/active_bookmark_baseline.json

PC090OJ_REGION := $(ROOT)/build/regions/pc090oj.bin
PC090OJ_PRECONV := $(ROOT)/build/pc090oj_genesis.bin
PC090OJ_SLOT_LUT := $(ROOT)/build/pc090oj_slot_lut.bin

AS := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-as
LD := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-ld
OBJCOPY := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-objcopy
NM := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-nm
OBJDUMP := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-objdump

ifeq ($(wildcard $(AS)),)
AS := m68k-elf-as
LD := m68k-elf-ld
OBJCOPY := m68k-elf-objcopy
NM := m68k-elf-nm
OBJDUMP := m68k-elf-objdump
endif

ASFLAGS := --register-prefix-optional
LDFLAGS := -T link.ld -nostdlib

OBJS := \
	$(OUT_DIR)/boot.o \
	$(OUT_DIR)/vdp_comm.o \
	$(OUT_DIR)/tilemap_hooks.o \
	$(OUT_DIR)/palette_hooks.o \
	$(OUT_DIR)/pc090oj_hooks.o \
	$(OUT_DIR)/pc090oj_assets.o \
	$(OUT_DIR)/diag_bookmark.o \
	$(OUT_DIR)/scene_load.o \
	$(OUT_DIR)/sound_comm.o \
	$(OUT_DIR)/z80_driver.o

ELF := $(OUT_DIR)/rastan_direct_video_test.elf
PREPATCH_BIN := $(OUT_DIR)/rastan_direct_video_test.prepatch.bin
BIN := $(DIST_DIR)/rastan_direct_video_test.bin

.DELETE_ON_ERROR:
.PHONY: all clean release

all: $(BIN)
release: $(BIN)

$(OUT_DIR) $(DIST_DIR):
	@mkdir -p $@

$(OUT_DIR)/boot.o: $(SRC_DIR)/boot/boot.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/vdp_comm.o: $(SRC_DIR)/vdp_comm.s $(SRC_DIR)/crash_handler.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/tilemap_hooks.o: $(SRC_DIR)/tilemap_hooks.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/palette_hooks.o: $(SRC_DIR)/palette_hooks.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(PC090OJ_REGION): $(REGION_BUILDER)
	$(PYTHON) "$(REGION_BUILDER)" --variant "$(VARIANT)"

$(PC090OJ_PRECONV): $(PC090OJ_REGION) $(ROOT)/tools/translation/preconvert_pc090oj_tiles.py
	$(PYTHON) "$(ROOT)/tools/translation/preconvert_pc090oj_tiles.py" \
		--input "$<" --output "$@"

$(PC090OJ_SLOT_LUT): $(ROOT)/tools/translation/build_pc090oj_slot_lut.py
	$(PYTHON) "$(ROOT)/tools/translation/build_pc090oj_slot_lut.py" --output "$@"

$(OUT_DIR)/pc090oj_hooks.o: $(SRC_DIR)/pc090oj_hooks.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/pc090oj_assets.o: $(SRC_DIR)/pc090oj_assets.s $(PC090OJ_PRECONV) $(PC090OJ_SLOT_LUT) | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/diag_bookmark.o: $(SRC_DIR)/diag_bookmark.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/scene_load.o: \
	$(SRC_DIR)/scene_load.s \
	$(ROOT)/build/pc080sn_tile_vram_lut.bin \
	$(ROOT)/build/pc080sn_attr_lut.bin \
	$(ROOT)/build/regions/pc080sn.bin \
	$(ROOT)/build/pc080sn_scene_preload_title.bin \
	$(ROOT)/build/pc080sn_scene_preload_gameplay.bin \
	$(ROOT)/build/pc080sn_scene_preload_endround.bin \
	| $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/sound_comm.o: $(SRC_DIR)/sound/sound_comm.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/z80_driver.o: $(SRC_DIR)/sound/z80_driver.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(ELF): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $(OBJS)

$(SYMBOLS): $(ELF) | $(OUT_DIR)
	$(NM) -n $< > $@

$(PREPATCH_BIN): $(ELF) | $(OUT_DIR)
	$(OBJCOPY) -O binary $< $@

$(BIN): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(BOOT_GUARD) | $(DIST_DIR)
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(PATCH_MANIFEST)" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"
	@mkdir -p "$(ROOT)/build"
	$(OBJDUMP) -D -b binary -m m68k:68000 --adjust-vma=0 "$@" > "$(ROOT)/build/genesis_postpatch.disasm.txt"
	@mkdir -p "$(NUMBERED_DIST_DIR)" "$(dir $(NUMBERED_COUNTER))"
	@counter_file="$(NUMBERED_COUNTER)"; \
	if [ -f "$$counter_file" ]; then n=$$(cat "$$counter_file"); else n=0; fi; \
	next=$$((n + 1)); \
	tag=$$(printf "%04d" "$$next"); \
	numbered_name="$(NUMBERED_PREFIX)_$${tag}.bin"; \
	"$(PYTHON)" "$(CANONICAL_GATE)" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--spec "$(PATCH_SPEC)" \
		--src-dir "$(SRC_DIR)" \
		--makefile "$(CURDIR)/Makefile" \
		--postpatch-script "$(PATCHER)" \
		--patch-manifest "$(PATCH_MANIFEST)" \
		--helper-symbol genesistan_diag_bookmark \
		--helper-canonical-sha "$(HELPER_CANONICAL_SHA)" \
		--numbered-counter "$$counter_file" \
		--numbered-name "$$numbered_name" \
		--bookmark-revert "$(BOOKMARK_REVERT)" \
		--state-file "$(BOOKMARK_STATE_FILE)" || exit $$?; \
	printf "%d\n" "$$next" > "$$counter_file"; \
	numbered="$(NUMBERED_DIST_DIR)/$$numbered_name"; \
	cp "$@" "$$numbered"; \
	echo "numbered build artifact: $$numbered"; \
	trace_ts=$$(date +%Y%m%d_%H%M%S); \
	trace_dir="$(ROOT)/states/traces/$(NUMBERED_PREFIX)_$${tag}_mame_30s_$${trace_ts}"; \
	mkdir -p "$$trace_dir" || exit 1; \
	trace_cmd='timeout 120s "$(ROOT)/tools/mame/run_genesis_trace_wsl.sh" "$@" -video none -sound none -nothrottle -seconds_to_run 30'; \
	echo "trace command: $$trace_cmd"; \
	if ! eval "$$trace_cmd"; then echo "ERROR: Genesis trace command failed"; exit 1; fi; \
	cp "$(ROOT)/build/mame/home/genesistrace/genesis_exec_summary.txt" "$$trace_dir/" || exit 1; \
	cp "$(ROOT)/build/mame/home/genesistrace/genesis_exec_trace.log" "$$trace_dir/" || exit 1; \
	if [ -f "$(ROOT)/build/mame/home/genesistrace/trace_metadata.txt" ]; then cp "$(ROOT)/build/mame/home/genesistrace/trace_metadata.txt" "$$trace_dir/"; fi; \
	if [ -f "$(ROOT)/build/mame/home/genesistrace/mame_stdout.txt" ]; then cp "$(ROOT)/build/mame/home/genesistrace/mame_stdout.txt" "$$trace_dir/"; fi; \
	if [ ! -f "$$trace_dir/genesis_exec_summary.txt" ]; then echo "ERROR: Missing genesis_exec_summary.txt in trace output: $$trace_dir"; exit 1; fi; \
	echo "trace saved to: $$trace_dir"

clean:
	rm -rf $(OUT_DIR) $(DIST_DIR)
