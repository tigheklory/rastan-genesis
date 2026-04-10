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
NUMBERED_DIST_DIR := $(ROOT)/dist/rastan-direct
NUMBERED_COUNTER := $(ROOT)/build/rastan-direct/build_counter.txt
NUMBERED_PREFIX := rastan_direct_video_test_build

AS := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-as
LD := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-ld
OBJCOPY := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-objcopy
NM := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-nm

ifeq ($(wildcard $(AS)),)
AS := m68k-elf-as
LD := m68k-elf-ld
OBJCOPY := m68k-elf-objcopy
NM := m68k-elf-nm
endif

ASFLAGS := --register-prefix-optional
LDFLAGS := -T link.ld -nostdlib

OBJS := \
	$(OUT_DIR)/boot.o \
	$(OUT_DIR)/main_68k.o \
	$(OUT_DIR)/sound_comm.o \
	$(OUT_DIR)/z80_driver.o

ELF := $(OUT_DIR)/rastan_direct_video_test.elf
PREPATCH_BIN := $(OUT_DIR)/rastan_direct_video_test.prepatch.bin
BIN := $(DIST_DIR)/rastan_direct_video_test.bin

.PHONY: all clean

all: $(BIN)

$(OUT_DIR) $(DIST_DIR):
	@mkdir -p $@

$(OUT_DIR)/boot.o: $(SRC_DIR)/boot/boot.s | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/main_68k.o: $(SRC_DIR)/main_68k.s | $(OUT_DIR)
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
	@mkdir -p "$(NUMBERED_DIST_DIR)" "$(dir $(NUMBERED_COUNTER))"
	@counter_file="$(NUMBERED_COUNTER)"; \
	if [ -f "$$counter_file" ]; then n=$$(cat "$$counter_file"); else n=0; fi; \
	n=$$((n + 1)); \
	printf "%d\n" "$$n" > "$$counter_file"; \
	tag=$$(printf "%04d" "$$n"); \
	numbered="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}.bin"; \
	cp "$@" "$$numbered"; \
	echo "numbered build artifact: $$numbered"

clean:
	rm -rf $(OUT_DIR) $(DIST_DIR)
