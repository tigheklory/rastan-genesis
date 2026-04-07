SHELL := /bin/bash

ROOT := ../..
OUT_DIR := out
DIST_DIR := dist
SRC_DIR := src

AS := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-as
LD := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-ld
OBJCOPY := ../../tools/local/toolchain/m68k-elf/bin/m68k-elf-objcopy

ifeq ($(wildcard $(AS)),)
AS := m68k-elf-as
LD := m68k-elf-ld
OBJCOPY := m68k-elf-objcopy
endif

ASFLAGS := --register-prefix-optional
LDFLAGS := -T link.ld -nostdlib

OBJS := \
	$(OUT_DIR)/boot.o \
	$(OUT_DIR)/main_68k.o \
	$(OUT_DIR)/sound_comm.o \
	$(OUT_DIR)/z80_driver.o

ELF := $(OUT_DIR)/rastan_direct_video_test.elf
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

$(BIN): $(ELF) | $(DIST_DIR)
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf $(OUT_DIR) $(DIST_DIR)
