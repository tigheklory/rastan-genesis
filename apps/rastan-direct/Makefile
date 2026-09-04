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
GAMEPLAY_ENTRY_GATE := $(ROOT)/tools/mame/run_build0309_gameplay_entry_gate.sh
PHASE1_EPOCH_GATE := $(ROOT)/tools/mame/run_build0310_epoch_gate.sh
TRANSITION_RETENTION_GATE := $(ROOT)/tools/translation/verify_build0311_transition_retention.py
REGION_BUILDER := $(ROOT)/tools/build_rastan_regions.py
NUMBERED_DIST_DIR := $(ROOT)/dist/rastan-direct
NUMBERED_COUNTER := $(ROOT)/build/rastan-direct/build_counter.txt
CONSUMED_BUILD_LEDGER := $(ROOT)/build/rastan-direct/consumed_build_numbers.txt
NUMBERED_PREFIX := rastan_direct_video_test_build
HELPER_CANONICAL_SHA ?= 20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb
BOOKMARK_REVERT ?=
BOOKMARK_STATE_FILE := $(ROOT)/build/rastan-direct/active_bookmark_baseline.json

# PC090OJ helper mirror sizing (durable, Make-overridable).
# Default is the full arcade model of 256 PC090OJ object records.  Override for
# diagnostic/tuning builds, e.g. `make release PC090OJ_MIRROR_RECORDS=128` or
# `make release PC090OJ_MIRROR_RECORDS=80`.  Valid range 1..256.  The value is
# baked into a generated assembly include ($(OUT_DIR)/pc090oj_config.inc) so no
# scattered assembly constants need hand-editing.
PC090OJ_MIRROR_RECORDS ?= 256
# Build 0208/0230: gameplay HUD-sprite representation option (durable,
# Make-overridable).
# 0 (accepted gameplay default) suppresses ONLY the Genesis representation of
# the gameplay HUD sprite records (0..45) during active gameplay -- arcade HUD
# code, score/life/health state, and all non-gameplay scenes are untouched --
# and frees CRAM line 0 so the shared palette route can carry PC090OJ sprite
# bank 0x36 (lizard men) there.
# 1 is diagnostics/comparison mode: preserve the old full Genesis HUD sprite
# representation.
# 2 keeps only the player-one score group (1UP label + 1P score records 28..36)
# while suppressing the rest of the gameplay HUD family; palette routing follows
# mode 0 so the bank-0x36 carrier path remains active.
RASTAN_GAMEPLAY_HUD_SPRITES ?= 2
# Build 0337: diagnostic CPU-load raster bar. When 1, _vblank_service sets the VDP backdrop
# (CRAM entry 0) to a bright color across the Genesis VBlank servicing window (sprite + plane +
# scroll VDP commits/DMA) and clears it when servicing finishes. The colored band on screen shows
# how much of the frame that servicing costs and whether it overruns vblank into active display.
# 0 = off (the numbered release ROM); 1 = on (the "_d" diagnostic ROM). NEVER shipped in the
# numbered artifact -- the dual-build produces both from one `make`.
RASTAN_DIAG_CPU_BAR ?= 0
# Build 0338: diagnostic numeric performance metric. When 1, _vblank_service writes a measured value
# into the P1 score (BCD @ 0xFF011E) so the on-screen 1UP score reads a stable NUMBER instead of the
# game score. Current metric = peak active-display scanlines the Genesis VBlank servicing overran
# (0 = servicing fits entirely in vblank; N = worst-case overran N scanlines into the picture).
# 0 = off (release / _d bar build); 1 = on (the "_s" metric ROM). NEVER shipped; corrupts the score.
RASTAN_DIAG_SCORE_METRIC ?= 0
PC090OJ_CONFIG_INC := $(OUT_DIR)/pc090oj_config.inc
CRASH_BUILD_INC := $(OUT_DIR)/crash_build.inc
# Build 0340 OPT-003: prebaked PC090OJ sprite palette-line LUT (derived from palette_route_table).
PC090OJ_PALSEL_LUT_INC := $(OUT_DIR)/pc090oj_palsel_lut.inc
PC090OJ_PALSEL_LUT_GEN := $(ROOT)/tools/translation/gen_pc090oj_palsel_lut.py

MAINCPU_REGION := $(ROOT)/build/regions/maincpu.bin
PC080SN_REGION := $(ROOT)/build/regions/pc080sn.bin
PC080SN_EDITOR_LAYERA := $(ROOT)/build/regions/pc080sn_editor_layera.bin
EDITOR_LAYERA_SNAPSHOT := $(ROOT)/build/rastan-direct/build0314/Test.snapshot.json
# Canonical approved pattern reference-substitution policy (offline only). Consumed automatically by the
# normal build: apply_pattern_reuse.py validates every approved entry against the real plane-A usage
# inventory and fails the build on any unresolved entry. Editing the policy re-triggers validation.
PATTERN_REUSE_POLICY := $(ROOT)/specs/pattern_reuse_policy.json
PATTERN_REUSE_RESOLVED := $(ROOT)/build/regions/pattern_reuse_resolved.json
PLANE_A_USES := $(ROOT)/analysis/graphics_optimizer/round1_phase1/plane_a_uses.json
PC080SN_TILE_LUT := $(ROOT)/build/pc080sn_tile_vram_lut.bin
PC080SN_ATTR_LUT := $(ROOT)/build/pc080sn_attr_lut.bin
PC080SN_SCENE_PRELOAD_TITLE := $(ROOT)/build/pc080sn_scene_preload_title.bin
PC080SN_SCENE_PRELOAD_GAMEPLAY := $(ROOT)/build/pc080sn_scene_preload_gameplay.bin
PC080SN_SCENE_PRELOAD_GAMEPLAY_CAVE := $(ROOT)/build/pc080sn_scene_preload_gameplay_cave.bin
PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S4 := $(ROOT)/build/pc080sn_scene_preload_stage1_cave_s4.bin
PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S5 := $(ROOT)/build/pc080sn_scene_preload_stage1_cave_s5.bin
PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S6 := $(ROOT)/build/pc080sn_scene_preload_stage1_cave_s6.bin
PC080SN_SCENE_PRELOAD_STAGE1_SEG1 := $(ROOT)/build/pc080sn_scene_preload_stage1_seg1.bin
PC080SN_SCENE_PRELOAD_STAGE1_SEG2 := $(ROOT)/build/pc080sn_scene_preload_stage1_seg2.bin
PC080SN_SCENE_PRELOAD_ENDROUND := $(ROOT)/build/pc080sn_scene_preload_endround.bin
PC080SN_SOURCE_SCENE_MAP := $(ROOT)/build/pc080sn_source_scene_map.bin
PC080SN_BOUNDARY_DIR := $(ROOT)/build/pc080sn_boundary
PC080SN_BOUNDARY_PACKAGES := $(PC080SN_BOUNDARY_DIR)/boundary_packages.bin
PC080SN_BOUNDARY_CONSTANTS := $(PC080SN_BOUNDARY_DIR)/boundary_constants.inc
PC080SN_BOUNDARY_REPORT := $(PC080SN_BOUNDARY_DIR)/boundary_report.json
PC080SN_TRANSITION_RETENTION_STAMP := $(OUT_DIR)/build0311_transition_retention_gate.stamp
PC090OJ_REGION := $(ROOT)/build/regions/pc090oj.bin
PC090OJ_PRECONV := $(ROOT)/build/pc090oj_genesis.bin
# Build 0325: offline Palette-Composer-reindexed R1/P1 sprite region (frozen Test index_maps per resolved
# (code,bank)). Consumed by pc090oj_assets.s. Provenance in pc090oj_editor_manifest.json.
PC090OJ_EDITOR := $(ROOT)/build/regions/pc090oj_editor.bin
SPRITE_ENEMIES_CORPUS := $(ROOT)/analysis/graphics_optimizer/round1_phase1_corpus/enemies.json
SPRITE_ENEMY_PATTERNS := $(ROOT)/analysis/graphics_optimizer/round1_phase1_corpus/enemy_patterns.json
SPRITE_FAMILIES := $(ROOT)/analysis/graphics_optimizer/round1_phase1/sprite_families.json
PC090OJ_HUD_WHITE := $(ROOT)/build/pc090oj_hud_white_genesis.bin
PC090OJ_SLOT_LUT := $(ROOT)/build/pc090oj_slot_lut.bin
PC090OJ_BLANK_BITSET := $(ROOT)/build/pc090oj_blank_bitset.bin
PC090OJ_OPAQUE_BBOX := $(ROOT)/build/pc090oj_opaque_bbox.bin

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

ASFLAGS := --register-prefix-optional -I $(OUT_DIR)
LDFLAGS := -T link.ld -nostdlib

OBJS := \
	$(OUT_DIR)/boot.o \
	$(OUT_DIR)/vdp_comm.o \
	$(OUT_DIR)/tilemap_hooks.o \
	$(OUT_DIR)/fg_tile_cache.o \
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
DIAG_ROM := $(DIST_DIR)/rastan_direct_video_test_diag.bin
SCORE_ROM := $(DIST_DIR)/rastan_direct_video_test_score.bin

.DELETE_ON_ERROR:
.PHONY: all clean release FORCE_ASM_REBUILD dual-build diag-variant score-variant

# Build 0337/0338: every build produces THREE ROMs sharing one build number:
#   ..._NNNN.bin    release (both diag flags off) -- owns the counter/gates/ledger
#   ..._NNNN_d.bin  diagnostic CPU-load raster bar (RASTAN_DIAG_CPU_BAR=1)
#   ..._NNNN_s.bin  diagnostic numeric score metric (RASTAN_DIAG_SCORE_METRIC=1)
# The _d and _s builds are postpatch-only copies that reuse the release's number and are never
# numbered/ledgered themselves.
all: dual-build
release: dual-build

dual-build:
	$(MAKE) $(BIN)
	$(MAKE) diag-variant RASTAN_DIAG_CPU_BAR=1
	$(MAKE) score-variant RASTAN_DIAG_SCORE_METRIC=1

$(OUT_DIR) $(DIST_DIR):
	@mkdir -p $@

$(OUT_DIR)/boot.o: $(SRC_DIR)/boot/boot.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/vdp_comm.o: $(SRC_DIR)/vdp_comm.s $(SRC_DIR)/crash_handler.s $(PC090OJ_CONFIG_INC) $(CRASH_BUILD_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

# Generate the crash-screen build number from the SAME counter the numbering
# stage uses (next = last-consumed + 1), so the on-screen BUILD matches the
# numbered ROM. Minimal Phase-2 support required by the transplanted handler.
$(CRASH_BUILD_INC): FORCE_ASM_REBUILD | $(OUT_DIR)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$((n + 1))"); \
	printf '/* GENERATED build number by apps/rastan-direct/Makefile -- do not hand-edit. */\ncrash_build_number_str: .asciz "%s"\n' "$$tag" > $@; \
	echo "crash build number -> $$tag ($@)"

$(OUT_DIR)/tilemap_hooks.o: $(SRC_DIR)/tilemap_hooks.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/palette_hooks.o: $(SRC_DIR)/palette_hooks.s $(PC090OJ_CONFIG_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

# Validated pattern-reuse resolution: canonical policy -> resolved (code,bank) substitutions. Hard gate:
# 0 unresolved approved entries or the build stops here. This artifact + its recorded policy_sha256 are the
# provenance the faithful (code,bank) target-pattern compiler consumes.
$(PATTERN_REUSE_RESOLVED): $(PATTERN_REUSE_POLICY) $(PLANE_A_USES) $(ROOT)/tools/translation/apply_pattern_reuse.py
	$(PYTHON) "$(ROOT)/tools/translation/apply_pattern_reuse.py" \
		--policy "$(PATTERN_REUSE_POLICY)" \
		--uses "$(PLANE_A_USES)" \
		--out "$@"

$(PC080SN_EDITOR_LAYERA): $(PC080SN_REGION) $(EDITOR_LAYERA_SNAPSHOT) $(PATTERN_REUSE_RESOLVED) $(ROOT)/analysis/graphics_optimizer/round1_phase1/plane_a_uses.json $(ROOT)/tools/graphics_editor/gen_reindexed_region.py
	$(PYTHON) "$(ROOT)/tools/graphics_editor/gen_reindexed_region.py" \
		--profile "$(EDITOR_LAYERA_SNAPSHOT)" \
		--pc080sn "$(PC080SN_REGION)" \
		--out "$@"

$(MAINCPU_REGION) $(PC080SN_REGION) $(PC090OJ_REGION): $(REGION_BUILDER)
	$(PYTHON) "$(REGION_BUILDER)" --variant "$(VARIANT)"

$(PC080SN_TILE_LUT) $(PC080SN_SCENE_PRELOAD_TITLE) $(PC080SN_SCENE_PRELOAD_GAMEPLAY) $(PC080SN_SCENE_PRELOAD_GAMEPLAY_CAVE) $(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S4) $(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S5) $(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S6) $(PC080SN_SCENE_PRELOAD_STAGE1_SEG1) $(PC080SN_SCENE_PRELOAD_STAGE1_SEG2) $(PC080SN_SCENE_PRELOAD_ENDROUND) $(PC080SN_SOURCE_SCENE_MAP): $(MAINCPU_REGION) $(PC080SN_REGION) $(ROOT)/tools/translation/precompute_pc080sn_tile_lut.py
	$(PYTHON) "$(ROOT)/tools/translation/precompute_pc080sn_tile_lut.py" \
		--maincpu "$(MAINCPU_REGION)" \
		--pc080sn "$(PC080SN_REGION)" \
		--lut-output "$(PC080SN_TILE_LUT)" \
		--preload-output "$(ROOT)/build/pc080sn_vram_preload.bin" \
		--count-output "$(ROOT)/build/pc080sn_unique_tile_count.txt" \
		--lut-include "$(ROOT)/build/pc080sn_tile_vram_lut_words.inc" \
		--preload-include "$(ROOT)/build/pc080sn_vram_preload_words.inc" \
		--scene-title-output "$(PC080SN_SCENE_PRELOAD_TITLE)" \
		--scene-gameplay-output "$(PC080SN_SCENE_PRELOAD_GAMEPLAY)" \
		--scene-gameplay-cave-output "$(PC080SN_SCENE_PRELOAD_GAMEPLAY_CAVE)" \
		--scene-stage1-cave-s4-output "$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S4)" \
		--scene-stage1-cave-s5-output "$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S5)" \
		--scene-stage1-cave-s6-output "$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S6)" \
		--scene-stage1-seg1-output "$(PC080SN_SCENE_PRELOAD_STAGE1_SEG1)" \
		--scene-stage1-seg2-output "$(PC080SN_SCENE_PRELOAD_STAGE1_SEG2)" \
		--scene-endround-output "$(PC080SN_SCENE_PRELOAD_ENDROUND)" \
		--source-scene-map-output "$(PC080SN_SOURCE_SCENE_MAP)"

$(PC080SN_ATTR_LUT): $(ROOT)/tools/translation/precompute_pc080sn_attr_lut.py
	$(PYTHON) "$(ROOT)/tools/translation/precompute_pc080sn_attr_lut.py" \
		--output "$(PC080SN_ATTR_LUT)" \
		--include "$(ROOT)/build/pc080sn_attr_lut_words.inc"

$(PC090OJ_PRECONV): $(PC090OJ_REGION) $(ROOT)/tools/translation/preconvert_pc090oj_tiles.py
	$(PYTHON) "$(ROOT)/tools/translation/preconvert_pc090oj_tiles.py" \
		--input "$<" --output "$@"

$(PC090OJ_EDITOR): $(PC090OJ_PRECONV) $(EDITOR_LAYERA_SNAPSHOT) $(SPRITE_ENEMIES_CORPUS) $(SPRITE_ENEMY_PATTERNS) $(SPRITE_FAMILIES) $(ROOT)/tools/graphics_editor/gen_reindexed_pc090oj.py
	$(PYTHON) "$(ROOT)/tools/graphics_editor/gen_reindexed_pc090oj.py" \
		--profile "$(EDITOR_LAYERA_SNAPSHOT)" --pc090oj "$(PC090OJ_PRECONV)" \
		--enemies "$(SPRITE_ENEMIES_CORPUS)" --enemy-patterns "$(SPRITE_ENEMY_PATTERNS)" \
		--families "$(SPRITE_FAMILIES)" --out "$@"

$(PC090OJ_HUD_WHITE): $(PC090OJ_PRECONV) $(ROOT)/tools/translation/build_pc090oj_hud_white.py
	$(PYTHON) "$(ROOT)/tools/translation/build_pc090oj_hud_white.py" \
		--input "$<" --output "$@"

$(PC090OJ_SLOT_LUT): $(ROOT)/tools/translation/build_pc090oj_slot_lut.py
	$(PYTHON) "$(ROOT)/tools/translation/build_pc090oj_slot_lut.py" --output "$@"

$(PC090OJ_BLANK_BITSET): $(PC090OJ_PRECONV) $(ROOT)/tools/translation/build_pc090oj_blank_bitset.py
	$(PYTHON) "$(ROOT)/tools/translation/build_pc090oj_blank_bitset.py" \
		--input "$<" --output "$@"

$(PC090OJ_OPAQUE_BBOX): $(PC090OJ_REGION) $(ROOT)/tools/translation/build_pc090oj_opaque_bbox.py
	$(PYTHON) "$(ROOT)/tools/translation/build_pc090oj_opaque_bbox.py" \
		--input "$<" --output "$@"

# Generate the PC090OJ helper sizing include from the Make variable each build so
# an override (PC090OJ_MIRROR_RECORDS=N) is always applied without hand-editing.
$(PC090OJ_CONFIG_INC): FORCE_ASM_REBUILD | $(OUT_DIR)
	@printf '/* GENERATED from PC090OJ_MIRROR_RECORDS=%s RASTAN_GAMEPLAY_HUD_SPRITES=%s RASTAN_DIAG_CPU_BAR=%s RASTAN_DIAG_SCORE_METRIC=%s by apps/rastan-direct/Makefile -- do not hand-edit. */\n.equ PC090OJ_MIRROR_RECORDS, %s\n.equ PC090OJ_MIRROR_BYTES, (PC090OJ_MIRROR_RECORDS * 8)\n.equ PC090OJ_BITSET_BYTES, ((PC090OJ_MIRROR_RECORDS + 7) / 8)\n.equ RASTAN_GAMEPLAY_HUD_SPRITES, %s\n.equ RASTAN_DIAG_CPU_BAR, %s\n.equ RASTAN_DIAG_SCORE_METRIC, %s\n' '$(PC090OJ_MIRROR_RECORDS)' '$(RASTAN_GAMEPLAY_HUD_SPRITES)' '$(RASTAN_DIAG_CPU_BAR)' '$(RASTAN_DIAG_SCORE_METRIC)' '$(PC090OJ_MIRROR_RECORDS)' '$(RASTAN_GAMEPLAY_HUD_SPRITES)' '$(RASTAN_DIAG_CPU_BAR)' '$(RASTAN_DIAG_SCORE_METRIC)' > $@
	@echo "PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=$(RASTAN_GAMEPLAY_HUD_SPRITES) RASTAN_DIAG_CPU_BAR=$(RASTAN_DIAG_CPU_BAR) RASTAN_DIAG_SCORE_METRIC=$(RASTAN_DIAG_SCORE_METRIC) -> $@"

# Build 0340 OPT-003: generate the prebaked (scene,effective_bank)->palette-line LUT from the authored
# palette_route_table + the 0x30->line2 special case + (eb>>4)&3 fallback, and PROVE equivalence
# (--verify: 0 mismatches + hand-anchored spot checks) on every build.  Regenerates when either the
# route source or the generator changes; a mismatch fails the build.
$(PC090OJ_PALSEL_LUT_INC): $(SRC_DIR)/palette_hooks.s $(PC090OJ_PALSEL_LUT_GEN) | $(OUT_DIR)
	$(PYTHON) $(PC090OJ_PALSEL_LUT_GEN) --route-src $(SRC_DIR)/palette_hooks.s --out $@ --verify

$(OUT_DIR)/pc090oj_hooks.o: $(SRC_DIR)/pc090oj_hooks.s $(PC090OJ_CONFIG_INC) $(PC090OJ_PALSEL_LUT_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/pc090oj_assets.o: $(SRC_DIR)/pc090oj_assets.s $(PC090OJ_EDITOR) $(PC090OJ_HUD_WHITE) $(PC090OJ_SLOT_LUT) $(PC090OJ_BLANK_BITSET) $(PC090OJ_OPAQUE_BBOX) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/diag_bookmark.o: $(SRC_DIR)/diag_bookmark.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/scene_load.o: \
	$(SRC_DIR)/scene_load.s \
	$(PC080SN_TILE_LUT) \
	$(PC080SN_ATTR_LUT) \
	$(PC080SN_REGION) \
	$(PC080SN_EDITOR_LAYERA) \
	$(PC080SN_SCENE_PRELOAD_TITLE) \
	$(PC080SN_SCENE_PRELOAD_GAMEPLAY) \
	$(PC080SN_SCENE_PRELOAD_GAMEPLAY_CAVE) \
	$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S4) \
	$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S5) \
	$(PC080SN_SCENE_PRELOAD_STAGE1_CAVE_S6) \
	$(PC080SN_SCENE_PRELOAD_STAGE1_SEG1) \
	$(PC080SN_SCENE_PRELOAD_STAGE1_SEG2) \
	$(PC080SN_SCENE_PRELOAD_ENDROUND) \
		FORCE_ASM_REBUILD \
		| $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/sound_comm.o: $(SRC_DIR)/sound/sound_comm.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/z80_driver.o: $(SRC_DIR)/sound/z80_driver.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(ELF): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $(OBJS)

$(SYMBOLS): $(ELF) | $(OUT_DIR)
	$(NM) -n $< > $@

$(PREPATCH_BIN): $(ELF) | $(OUT_DIR)
	$(OBJCOPY) -O binary $< $@

$(BIN): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(BOOT_GUARD) $(GAMEPLAY_ENTRY_GATE) $(PHASE1_EPOCH_GATE) | $(DIST_DIR)
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
	max_seen=$$( { \
		find "$(NUMBERED_DIST_DIR)" -maxdepth 1 -type f -name "$(NUMBERED_PREFIX)_*.bin" -printf "%f\n" | \
			sed -n 's/^$(NUMBERED_PREFIX)_\([0-9][0-9][0-9][0-9]\)\.bin$$/\1/p'; \
		if [ -f "$(CONSUMED_BUILD_LEDGER)" ]; then \
			awk 'substr($$0,1,4) ~ /^[0-9][0-9][0-9][0-9]$$/ { print substr($$0,1,4) }' "$(CONSUMED_BUILD_LEDGER)"; \
		fi; \
	} | sort -n | tail -n 1 ); \
	if [ -n "$$max_seen" ] && [ "$$n" -lt "$$((10#$$max_seen))" ]; then \
		echo "ERROR: numbered build counter $$n is behind consumed build $$max_seen"; \
		exit 1; \
	fi; \
	next=$$((n + 1)); \
	tag=$$(printf "%04d" "$$next"); \
	numbered_name="$(NUMBERED_PREFIX)_$${tag}.bin"; \
	numbered="$(NUMBERED_DIST_DIR)/$$numbered_name"; \
	if [ -e "$$numbered" ]; then \
		echo "ERROR: refusing to overwrite existing numbered build artifact: $$numbered"; \
		exit 1; \
	fi; \
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
	if ! "$(GAMEPLAY_ENTRY_GATE)" "$@" "$(SYMBOLS)" "$$tag"; then \
		echo "ERROR: Start-to-gameplay package gate failed; numbered artifact not published"; \
		exit 1; \
	fi; \
	if ! "$(PHASE1_EPOCH_GATE)" "$@" "$(SYMBOLS)" "$$tag"; then \
		echo "ERROR: Phase-1 seven-epoch gate failed; numbered artifact not published"; \
		exit 1; \
	fi; \
	cp "$@" "$$numbered"; \
	if [ ! -s "$$numbered" ]; then echo "ERROR: numbered build artifact missing/empty after copy: $$numbered"; exit 1; fi; \
	printf "%d\n" "$$next" > "$$counter_file"; \
	printf "%s PRODUCED %s auto-recorded-by-release\n" "$$tag" "$$(date +%Y-%m-%d)" >> "$(CONSUMED_BUILD_LEDGER)"; \
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

# Build 0337: diagnostic ROM = the same postpatch pipeline as $(BIN) but WITHOUT the numbered
# release/counter/gates (those belong to the normal build).  Built with RASTAN_DIAG_CPU_BAR=1 via
# the recursive `diag-variant` invocation, so config.inc regenerates and every object re-assembles
# with the bar enabled.  Uses a separate manifest so the normal build's manifest is untouched.
$(DIAG_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(BOOT_GUARD) | $(DIST_DIR)
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/diag_patch_manifest.json" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

# Copy the diagnostic ROM to the SAME build number as the just-produced numbered release, with a
# "_d" suffix.  Does not touch the counter or ledger (the normal build already advanced them).
diag-variant: $(DIAG_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_d.bin"; \
	cp "$(DIAG_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: diagnostic build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "diagnostic build artifact (CPU-load bar): $$dest"

# Build 0338: score-metric ROM = same postpatch-only pipeline as $(DIAG_ROM) but built with
# RASTAN_DIAG_SCORE_METRIC=1 (via the recursive `score-variant` invocation).  Separate manifest.
$(SCORE_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(BOOT_GUARD) | $(DIST_DIR)
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/score_patch_manifest.json" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

# Copy the score-metric ROM to the SAME build number as the numbered release, with a "_s" suffix.
# Does not touch the counter or ledger.
score-variant: $(SCORE_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_s.bin"; \
	cp "$(SCORE_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: score-metric build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "diagnostic build artifact (score metric): $$dest"

clean:
	rm -rf $(OUT_DIR) $(DIST_DIR)

$(OUT_DIR)/fg_tile_cache.o: $(SRC_DIR)/fg_tile_cache.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -m68000 -o $@ $<

$(PC080SN_BOUNDARY_PACKAGES) $(PC080SN_BOUNDARY_CONSTANTS) $(PC080SN_BOUNDARY_REPORT): \
		$(MAINCPU_REGION) $(PC080SN_REGION) $(PC080SN_EDITOR_LAYERA) $(PATTERN_REUSE_RESOLVED) $(ROOT)/tools/translation/compile_pc080sn_genesis.py
	$(PYTHON) "$(ROOT)/tools/translation/compile_pc080sn_genesis.py" \
		--maincpu "$(MAINCPU_REGION)" --pc080sn "$(PC080SN_EDITOR_LAYERA)" \
		--pattern-reuse "$(PATTERN_REUSE_RESOLVED)" \
		--out "$(PC080SN_BOUNDARY_DIR)" --boundary-experiment

$(PC080SN_TRANSITION_RETENTION_STAMP): $(PC080SN_BOUNDARY_PACKAGES) \
		$(PC080SN_BOUNDARY_CONSTANTS) $(PC080SN_BOUNDARY_REPORT) \
		$(PC080SN_REGION) $(TRANSITION_RETENTION_GATE) | $(OUT_DIR)
	LAYERA_EDITOR_CANDIDATE=1 $(PYTHON) "$(TRANSITION_RETENTION_GATE)" \
		--report "$(PC080SN_BOUNDARY_REPORT)" \
		--packages "$(PC080SN_BOUNDARY_PACKAGES)" \
		--constants "$(PC080SN_BOUNDARY_CONSTANTS)" \
		--patterns "$(PC080SN_REGION)"
	touch "$@"

$(OUT_DIR)/fg_tile_cache.o: $(PC080SN_BOUNDARY_PACKAGES) \
		$(PC080SN_BOUNDARY_CONSTANTS) $(PC080SN_TRANSITION_RETENTION_STAMP)

.PHONY: pc080sn-compile
pc080sn-compile: $(MAINCPU_REGION) $(PC080SN_REGION)
	$(PYTHON) "$(ROOT)/tools/translation/compile_pc080sn_genesis.py"
