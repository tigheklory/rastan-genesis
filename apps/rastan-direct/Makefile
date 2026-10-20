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
R1_SELECTOR_STREAM_VERIFY := $(ROOT)/tools/translation/verify_r1_selector_stream_relocation.py
ATTRACT_PLANE_B_ENTRY_VERIFY := $(ROOT)/tools/translation/verify_attract_demo_plane_b_scene_entry.py
BOOT_GUARD := $(ROOT)/tools/translation/verify_rastan_direct_boot_guard.py
CANONICAL_GATE := $(ROOT)/tools/translation/verify_canonical_rom.py
GAMEPLAY_ENTRY_GATE := $(ROOT)/tools/mame/run_build0309_gameplay_entry_gate.sh
PHASE1_EPOCH_GATE := $(ROOT)/tools/mame/run_build0310_epoch_gate.sh
TRANSITION_RETENTION_GATE := $(ROOT)/tools/translation/verify_build0311_transition_retention.py
BG_A_INCREMENTAL_GATE := $(ROOT)/tools/translation/verify_bg_a_incremental_background.py
PLANE_A_SEL0_SEGMENT_GATE := $(ROOT)/tools/translation/verify_plane_a_selector0_segment_hoist.py
PLANE_A_SEL12_SEGMENT_GATE := $(ROOT)/tools/translation/verify_plane_a_selector12_segment_hoist.py
VDP_DMA_BOUNDARY_GATE := $(ROOT)/tools/translation/verify_vdp_dma_boundary.py
PC080SN_NATIVE_METATILE_GEN := $(ROOT)/tools/translation/gen_pc080sn_native_metatiles.py
PC080SN_NATIVE_METATILE_VERIFY := $(ROOT)/tools/translation/verify_pc080sn_native_metatiles.py
PC080SN_PLANE_B_VISUAL_GEN := $(ROOT)/tools/translation/gen_pc080sn_plane_b_visual_records.py
PC080SN_PLANE_B_VISUAL_VERIFY := $(ROOT)/tools/translation/verify_pc080sn_plane_b_visual_records.py
COLLISION_VISUAL_SEMANTICS_VERIFY := $(ROOT)/tools/translation/verify_collision_visual_semantics.py
NATIVE_TITLE_GEN := $(ROOT)/tools/translation/gen_native_title.py
NATIVE_TITLE_VERIFY := $(ROOT)/tools/translation/verify_native_title.py
NATIVE_HUD_GEN := $(ROOT)/tools/translation/gen_native_hud.py
NATIVE_HUD_VERIFY := $(ROOT)/tools/translation/verify_native_hud.py
NATIVE_ITEM_GEN := $(ROOT)/tools/translation/gen_native_item_description.py
NATIVE_ITEM_VERIFY := $(ROOT)/tools/translation/verify_native_item_description.py
BEST5_TABLE_GEN := $(ROOT)/tools/translation/gen_best5_native_tables.py
BEST5_TABLE_VERIFY := $(ROOT)/tools/translation/verify_best5_native_tables.py
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
# Build 0344: display-off VBlank publication variant. 0 = display stays ON during dma_publish_frame
# (current behaviour); 1 = blank the display for the publication phase (Rainbow model). Emits a "_do" ROM.
RASTAN_VBLANK_DISPLAY_OFF ?= 0
# Build 0360: opt-in controller cheat variant.  When 1, P1 six-button MODE
# invokes the authoritative arcade/MAME "Finish Current Sub-Round Now!"
# semantic on a rising edge.  The normal and diagnostic ROMs compile it out.
RASTAN_MODE_RACK_ADVANCE ?= 0
# Build 0440: permanent benchmark/diagnostic variant. When 1, the postpatcher
# asserts the original arcade A5+0x0040 debug gate at its startup source. The
# standard numbered ROM defaults to 0 and retains normal enemy damage.
RASTAN_INVINCIBLE ?= 0
CRASH_BUILD_USE_CURRENT ?= 0
PC090OJ_CONFIG_INC := $(OUT_DIR)/pc090oj_config.inc
CRASH_BUILD_INC := $(OUT_DIR)/crash_build.inc
# Direct PC090OJ palette-line LUT: current Tool-authored R1/P1 mappings plus
# compatibility-complete fallback rows, selected by scene outside the hot path.
PC090OJ_PALSEL_LUT_INC := $(OUT_DIR)/pc090oj_palsel_lut.inc
PC090OJ_PALSEL_LUT_GEN := $(ROOT)/tools/translation/gen_pc090oj_palsel_lut.py
PC090OJ_PALSEL_EQUIV := $(ROOT)/build/rastan-direct/pc090oj_direct_palette_equivalence.json

MAINCPU_REGION := $(ROOT)/build/regions/maincpu.bin
PC080SN_REGION := $(ROOT)/build/regions/pc080sn.bin
PC080SN_EDITOR_LAYERA := $(ROOT)/build/regions/pc080sn_editor_layera.bin
EDITOR_LAYERA_SNAPSHOT := $(ROOT)/build/rastan-direct/build0400/Test.snapshot.json
# Canonical approved pattern reference-substitution policy (offline only). Consumed automatically by the
# normal build: apply_pattern_reuse.py validates every approved entry against the real plane-A usage
# inventory and fails the build on any unresolved entry. Editing the policy re-triggers validation.
PATTERN_REUSE_POLICY := $(ROOT)/specs/pattern_reuse_policy.json
PATTERN_REUSE_RESOLVED := $(ROOT)/build/regions/pattern_reuse_resolved.json
PLANE_A_USES := $(ROOT)/analysis/graphics_optimizer/round1_phase1/plane_a_uses.json
PC080SN_TILE_LUT := $(ROOT)/build/pc080sn_tile_vram_lut.bin
PC080SN_ATTR_LUT := $(ROOT)/build/pc080sn_attr_lut.bin
NATIVE_TITLE_BG := $(ROOT)/build/rastan-direct/native_title_bg.bin
NATIVE_TITLE_FG := $(ROOT)/build/rastan-direct/native_title_fg.bin
NATIVE_TITLE_FG_INVINCIBLE := $(ROOT)/build/rastan-direct/native_title_fg_invincible.bin
NATIVE_TITLE_PALETTE := $(ROOT)/build/rastan-direct/native_title_palette.bin
NATIVE_TITLE_PATTERNS := $(ROOT)/build/rastan-direct/native_title_patterns.bin
NATIVE_TITLE_REPORT := $(ROOT)/build/rastan-direct/native_title_report.json
NATIVE_HUD_PATTERNS := $(ROOT)/build/rastan-direct/native_hud_patterns.bin
NATIVE_HUD_STATIC_SAT := $(ROOT)/build/rastan-direct/native_hud_static_sat.bin
NATIVE_HUD_DYNAMIC_RECORDS := $(ROOT)/build/rastan-direct/native_hud_dynamic_records.bin
NATIVE_HUD_REPORT := $(ROOT)/build/rastan-direct/native_hud_report.json
NATIVE_ITEM_LOGICAL_MAP := $(ROOT)/build/rastan-direct/native_item_logical_map.bin
NATIVE_ITEM_INITIAL_ROWS := $(ROOT)/build/rastan-direct/native_item_initial_rows.bin
NATIVE_ITEM_REFERENCE := $(ROOT)/build/rastan-direct/native_item_arcade_reference.json
NATIVE_ITEM_PLANE_PATTERNS := $(ROOT)/build/rastan-direct/native_item_plane_patterns.bin
NATIVE_ITEM_ICON_PATTERNS := $(ROOT)/build/rastan-direct/native_item_icon_patterns.bin
NATIVE_ITEM_ICON_RECORDS := $(ROOT)/build/rastan-direct/native_item_icon_records.bin
NATIVE_ITEM_REPORT := $(ROOT)/build/rastan-direct/native_item_report.json
BEST5_NUMBER_TABLE := $(ROOT)/build/rastan-direct/best5_number_descriptors.bin
BEST5_NAME_TABLE := $(ROOT)/build/rastan-direct/best5_name_descriptors.bin
BEST5_TABLE_REPORT := $(ROOT)/build/rastan-direct/best5_native_tables_report.json
PC080SN_NATIVE_METATILE_INDEX := $(ROOT)/build/pc080sn_native_metatile_index.bin
PC080SN_NATIVE_METATILE_RECORDS := $(ROOT)/build/pc080sn_native_metatile_records.bin
PC080SN_NATIVE_METATILE_REPORT := $(ROOT)/build/rastan-direct/pc080sn_native_metatile_report.json
PC080SN_PLANE_B_VISUAL_RECORDS := $(ROOT)/build/pc080sn_plane_b_visual_records.bin
PC080SN_PLANE_B_VISUAL_REPORT := $(ROOT)/build/rastan-direct/pc080sn_plane_b_visual_report.json
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
# Build 0381: complete R1/P1 semantic corpus + weapon/player cell evidence (replaces the
# representative enemies.json/enemy_patterns.json subset). Drives the complete (code,bank)
# variant reindex. The generated variant index include is consumed by pc090oj_hooks.s.
R1P1_ENEMY_CORPUS := $(ROOT)/analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv
H24_WEAPON_CELLS := $(ROOT)/analysis/actor_decompilation/h24_player_weapon_cells.tsv
H24_PLAYER_CELLS := $(ROOT)/analysis/actor_decompilation/h24_player_frame_cells.tsv
H24_LEG_CELLS := $(ROOT)/analysis/actor_decompilation/h24_player_leg_cells.tsv
H16_BURST_RENDER := $(ROOT)/analysis/actor_decompilation/h16_burst_child_render.tsv
ACTOR_GRAPHICS_MANIFEST := $(ROOT)/docs/design/rastan_actor_graphics_manifest.json
PC090OJ_VARIANTS_INC := $(OUT_DIR)/pc090oj_sprite_variants.inc
PC090OJ_HUD_WHITE := $(ROOT)/build/pc090oj_hud_white_genesis.bin
PC090OJ_SLOT_LUT := $(ROOT)/build/pc090oj_slot_lut.bin
PC090OJ_BLANK_BITSET := $(ROOT)/build/pc090oj_blank_bitset.bin
PC090OJ_OPAQUE_BBOX := $(ROOT)/build/pc090oj_opaque_bbox.bin
PC090OJ_FRAME_GEN := $(ROOT)/tools/translation/precompute_pc090oj_frame_table.py
PC090OJ_FRAME_VERIFY := $(ROOT)/tools/translation/verify_pc090oj_frame_table.py
PC090OJ_DISPATCH_VERIFY := $(ROOT)/tools/translation/verify_pc090oj_direct_dispatch.py
PC090OJ_FRAME_TABLE := $(ROOT)/build/pc090oj_frame_table.bin
PC090OJ_PLAYER_PIECE_TABLE := $(ROOT)/build/pc090oj_player_piece_table.bin
PC090OJ_FRAME_INDEX := $(ROOT)/build/pc090oj_frame_index.bin
PC090OJ_SECONDARY_FRAME_INDEX := $(ROOT)/build/pc090oj_secondary_frame_index.bin
PC090OJ_GENERIC_FRAME_INDEX := $(ROOT)/build/pc090oj_generic_frame_index.bin
PC090OJ_GENERIC_PIECE_TABLE := $(ROOT)/build/pc090oj_generic_piece_table.bin
PC090OJ_UNIVERSAL_FRAME_INDEX := $(ROOT)/build/pc090oj_universal_frame_index.bin
PC090OJ_SPECIAL_FRAME_INDEX := $(ROOT)/build/pc090oj_special_frame_index.bin
PC090OJ_DEATH_FRAME_INDEX := $(ROOT)/build/pc090oj_death_frame_index.bin
PC090OJ_DEATH_PIECE_TABLE := $(ROOT)/build/pc090oj_death_piece_table.bin
PC090OJ_GENERIC_BASE_LUT := $(ROOT)/build/pc090oj_generic_base_lut.bin
PC090OJ_GENERIC_USAGE_TABLE := $(ROOT)/build/pc090oj_generic_usage_table.bin
PC090OJ_FRAME_RESIDENCY := $(ROOT)/build/pc090oj_frame_residency.bin
PC090OJ_FRAME_REPORT := $(ROOT)/build/pc090oj_frame_table.report.txt
PC090OJ_FRAME_COVERAGE := $(ROOT)/build/pc090oj_frame_table.coverage.json
PALETTE_DECISIONS := $(ROOT)/specs/palette_decisions.json
PC090OJ_LAYER1_VERIFY := $(ROOT)/tools/graphics_editor/verify_reindexed_pc090oj.py
PC090OJ_LAYER1_STAMP := $(OUT_DIR)/pc090oj_layer1_verify.stamp

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
	$(OUT_DIR)/dma.o \
	$(OUT_DIR)/tilemap_hooks.o \
	$(OUT_DIR)/fg_tile_cache.o \
	$(OUT_DIR)/palette_hooks.o \
	$(OUT_DIR)/title_native.o \
	$(OUT_DIR)/hud_native.o \
	$(OUT_DIR)/item_native.o \
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
DO_ROM := $(DIST_DIR)/rastan_direct_video_test_do.bin
CHEAT_ROM := $(DIST_DIR)/rastan_direct_video_test_cheat.bin
FULL_HUD_ROM := $(DIST_DIR)/rastan_direct_video_test_full_hud.bin
INVINCIBLE_ROM := $(DIST_DIR)/rastan_direct_video_test_invincible.bin
VARIANT_CONFIG_DIR := $(OUT_DIR)/variant_configs
INVINCIBLE_VARIANT_VERIFY := $(ROOT)/tools/translation/verify_invincible_variant.py

# Every family member declares the complete compile-time configuration.  This
# prevents a recursively built variant from inheriting the preceding member's
# generated pc090oj_config.inc state.  Mode 2 remains the canonical default;
# mode 1 differs only by enabling the existing full gameplay HUD.
CANONICAL_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=0
DIAG_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=1 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=0
SCORE_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=1 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=0
DISPLAY_OFF_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=1 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=0
CHEAT_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=1 RASTAN_INVINCIBLE=0
FULL_HUD_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=1 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=0
INVINCIBLE_BUILD_FLAGS := PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=2 RASTAN_DIAG_CPU_BAR=0 RASTAN_DIAG_SCORE_METRIC=0 RASTAN_VBLANK_DISPLAY_OFF=0 RASTAN_MODE_RACK_ADVANCE=0 RASTAN_INVINCIBLE=1

.DELETE_ON_ERROR:
.PHONY: all clean release FORCE_ASM_REBUILD dual-build diag-variant score-variant do-variant cheat-variant full-hud-variant invincible-variant verify-variant-set

# Every build produces SEVEN ROMs sharing one build number:
#   ..._NNNN.bin     release (all diag/variant flags off) -- owns the counter/gates/ledger
#   ..._NNNN_d.bin   diagnostic CPU-load raster bar (RASTAN_DIAG_CPU_BAR=1)
#   ..._NNNN_s.bin   diagnostic numeric score metric (RASTAN_DIAG_SCORE_METRIC=1)
#   ..._NNNN_do.bin  display-off VBlank publication phase (RASTAN_VBLANK_DISPLAY_OFF=1)
#   ..._NNNN_c.bin   P1 six-button MODE rack-advance cheat (RASTAN_MODE_RACK_ADVANCE=1)
#   ..._NNNN_full_hud.bin existing full gameplay HUD (RASTAN_GAMEPLAY_HUD_SPRITES=1)
#   ..._NNNN_invincible.bin normal display with the arcade A5+0x0040 gate asserted
# The suffixed builds are postpatch-only copies that reuse the release's number and are never
# numbered/ledgered themselves.
all: dual-build
release: dual-build

dual-build:
	$(MAKE) $(BIN) $(CANONICAL_BUILD_FLAGS)
	$(MAKE) diag-variant $(DIAG_BUILD_FLAGS)
	$(MAKE) score-variant $(SCORE_BUILD_FLAGS)
	$(MAKE) do-variant $(DISPLAY_OFF_BUILD_FLAGS)
	$(MAKE) cheat-variant $(CHEAT_BUILD_FLAGS) CRASH_BUILD_USE_CURRENT=1
	$(MAKE) full-hud-variant $(FULL_HUD_BUILD_FLAGS) CRASH_BUILD_USE_CURRENT=1
	$(MAKE) invincible-variant $(INVINCIBLE_BUILD_FLAGS) CRASH_BUILD_USE_CURRENT=1
	$(MAKE) verify-variant-set

# A default/release build is incomplete unless the canonical ROM and every
# same-number variant, including the full-HUD comparison ROM, are present.
verify-variant-set:
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	for suffix in "" _d _s _do _c _full_hud _invincible; do \
		artifact="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}$${suffix}.bin"; \
		if [ ! -s "$$artifact" ]; then echo "ERROR: required build artifact missing/empty: $$artifact"; exit 1; fi; \
	done; \
	check_config() { \
		file="$$1"; hud="$$2"; bar="$$3"; score="$$4"; display_off="$$5"; mode="$$6"; invincible="$$7"; \
		if [ ! -s "$$file" ]; then echo "ERROR: missing variant configuration receipt: $$file"; exit 1; fi; \
		grep -qx ".equ PC090OJ_MIRROR_RECORDS, $(PC090OJ_MIRROR_RECORDS)" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_GAMEPLAY_HUD_SPRITES, $$hud" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_DIAG_CPU_BAR, $$bar" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_DIAG_SCORE_METRIC, $$score" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_VBLANK_DISPLAY_OFF, $$display_off" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_MODE_RACK_ADVANCE, $$mode" "$$file" || exit 1; \
		grep -qx ".equ RASTAN_INVINCIBLE, $$invincible" "$$file" || exit 1; \
	}; \
	check_config "$(VARIANT_CONFIG_DIR)/canonical.inc" 2 0 0 0 0 0; \
	check_config "$(VARIANT_CONFIG_DIR)/diag.inc" 2 1 0 0 0 0; \
	check_config "$(VARIANT_CONFIG_DIR)/score.inc" 2 0 1 0 0 0; \
	check_config "$(VARIANT_CONFIG_DIR)/display_off.inc" 2 0 0 1 0 0; \
	check_config "$(VARIANT_CONFIG_DIR)/cheat.inc" 2 0 0 0 1 0; \
	check_config "$(VARIANT_CONFIG_DIR)/full_hud.inc" 1 0 0 0 0 0; \
	check_config "$(VARIANT_CONFIG_DIR)/invincible.inc" 2 0 0 0 0 1; \
	$(PYTHON) "$(INVINCIBLE_VARIANT_VERIFY)" \
		--standard "$(BIN)" --invincible "$(INVINCIBLE_ROM)" \
		--standard-manifest "$(PATCH_MANIFEST)" \
		--invincible-manifest "$(OUT_DIR)/invincible_patch_manifest.json" \
		--address-map "$(OUT_DIR)/address_map.json" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin"; \
	echo "complete build artifact/configuration set verified for $$tag (canonical, _d, _s, _do, _c, _full_hud, _invincible)"

$(OUT_DIR) $(DIST_DIR) $(VARIANT_CONFIG_DIR):
	@mkdir -p $@

$(OUT_DIR)/boot.o: $(SRC_DIR)/boot/boot.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/vdp_comm.o: $(SRC_DIR)/vdp_comm.s $(SRC_DIR)/crash_handler.s $(PC090OJ_CONFIG_INC) $(CRASH_BUILD_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/dma.o: $(SRC_DIR)/dma.s $(PC090OJ_CONFIG_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

# Generate the crash-screen build number from the SAME counter the numbering
# stage uses (next = last-consumed + 1), so the on-screen BUILD matches the
# numbered ROM. Minimal Phase-2 support required by the transplanted handler.
$(CRASH_BUILD_INC): FORCE_ASM_REBUILD | $(OUT_DIR)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	if [ "$(CRASH_BUILD_USE_CURRENT)" = "1" ]; then build_n=$$n; else build_n=$$((n + 1)); fi; \
	tag=$$(printf "%04d" "$$build_n"); \
	printf '/* GENERATED build number by apps/rastan-direct/Makefile -- do not hand-edit. */\ncrash_build_number_str: .asciz "%s"\n' "$$tag" > $@; \
	echo "crash build number -> $$tag ($@)"

$(OUT_DIR)/tilemap_hooks.o: $(SRC_DIR)/tilemap_hooks.s $(PC090OJ_CONFIG_INC) $(PC080SN_BOUNDARY_CONSTANTS) $(BEST5_NUMBER_TABLE) $(BEST5_NAME_TABLE) FORCE_ASM_REBUILD | $(OUT_DIR)
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

$(NATIVE_TITLE_BG): $(MAINCPU_REGION) $(PC080SN_REGION) $(PC080SN_SCENE_PRELOAD_TITLE) $(PC080SN_ATTR_LUT) $(NATIVE_TITLE_GEN)
	$(PYTHON) "$(NATIVE_TITLE_GEN)" --maincpu "$(MAINCPU_REGION)" \
		--pc080sn "$(PC080SN_REGION)" \
		--title-preload "$(PC080SN_SCENE_PRELOAD_TITLE)" --attr-lut "$(PC080SN_ATTR_LUT)" \
		--bg-output "$(NATIVE_TITLE_BG)" --fg-output "$(NATIVE_TITLE_FG)" \
		--fg-invincible-output "$(NATIVE_TITLE_FG_INVINCIBLE)" \
		--palette-output "$(NATIVE_TITLE_PALETTE)" --pattern-output "$(NATIVE_TITLE_PATTERNS)" \
		--report "$(NATIVE_TITLE_REPORT)"

$(NATIVE_TITLE_FG) $(NATIVE_TITLE_FG_INVINCIBLE) $(NATIVE_TITLE_PALETTE) $(NATIVE_TITLE_PATTERNS) $(NATIVE_TITLE_REPORT): $(NATIVE_TITLE_BG)
	@test -f "$@"

$(NATIVE_HUD_PATTERNS): $(MAINCPU_REGION) $(PC090OJ_PRECONV) $(NATIVE_HUD_GEN)
	$(PYTHON) "$(NATIVE_HUD_GEN)" --maincpu "$(MAINCPU_REGION)" --pc090oj "$(PC090OJ_PRECONV)" \
		--patterns-output "$(NATIVE_HUD_PATTERNS)" --sat-output "$(NATIVE_HUD_STATIC_SAT)" \
		--dynamic-output "$(NATIVE_HUD_DYNAMIC_RECORDS)" --report "$(NATIVE_HUD_REPORT)"

$(NATIVE_HUD_STATIC_SAT) $(NATIVE_HUD_DYNAMIC_RECORDS) $(NATIVE_HUD_REPORT): $(NATIVE_HUD_PATTERNS)
	@test -f "$@"

$(NATIVE_ITEM_LOGICAL_MAP): $(MAINCPU_REGION) $(PC080SN_REGION) $(PC090OJ_PRECONV) $(NATIVE_HUD_REPORT) $(SRC_DIR)/pc090oj_hooks.s $(PC090OJ_PALSEL_LUT_INC) $(NATIVE_ITEM_GEN)
	$(PYTHON) "$(NATIVE_ITEM_GEN)" --maincpu "$(MAINCPU_REGION)" \
		--pc080sn "$(PC080SN_REGION)" --pc090oj "$(PC090OJ_PRECONV)" \
		--hud-report "$(NATIVE_HUD_REPORT)" --sprite-source "$(SRC_DIR)/pc090oj_hooks.s" \
		--palette-lut "$(PC090OJ_PALSEL_LUT_INC)" \
		--map-output "$(NATIVE_ITEM_LOGICAL_MAP)" \
		--initial-rows-output "$(NATIVE_ITEM_INITIAL_ROWS)" \
		--plane-pattern-output "$(NATIVE_ITEM_PLANE_PATTERNS)" \
		--icon-pattern-output "$(NATIVE_ITEM_ICON_PATTERNS)" \
		--icon-record-output "$(NATIVE_ITEM_ICON_RECORDS)" \
		--reference-output "$(NATIVE_ITEM_REFERENCE)" \
		--report "$(NATIVE_ITEM_REPORT)"

$(NATIVE_ITEM_INITIAL_ROWS) $(NATIVE_ITEM_REFERENCE) $(NATIVE_ITEM_PLANE_PATTERNS) $(NATIVE_ITEM_ICON_PATTERNS) $(NATIVE_ITEM_ICON_RECORDS) $(NATIVE_ITEM_REPORT): $(NATIVE_ITEM_LOGICAL_MAP)
	@test -f "$@"

$(BEST5_NUMBER_TABLE): $(MAINCPU_REGION) $(BEST5_TABLE_GEN)
	$(PYTHON) "$(BEST5_TABLE_GEN)" --maincpu "$(MAINCPU_REGION)" \
		--number-output "$(BEST5_NUMBER_TABLE)" --name-output "$(BEST5_NAME_TABLE)" \
		--report "$(BEST5_TABLE_REPORT)"

$(BEST5_NAME_TABLE) $(BEST5_TABLE_REPORT): $(BEST5_NUMBER_TABLE)
	@test -f "$@"

$(PC080SN_NATIVE_METATILE_INDEX): $(MAINCPU_REGION) $(PC080SN_NATIVE_METATILE_GEN)
	$(PYTHON) "$(PC080SN_NATIVE_METATILE_GEN)" \
		--maincpu "$(MAINCPU_REGION)" \
		--index-output "$(PC080SN_NATIVE_METATILE_INDEX)" \
		--records-output "$(PC080SN_NATIVE_METATILE_RECORDS)" \
		--report-output "$(PC080SN_NATIVE_METATILE_REPORT)"

# Side effects of the single authoritative generator invocation above.
$(PC080SN_NATIVE_METATILE_RECORDS) $(PC080SN_NATIVE_METATILE_REPORT): $(PC080SN_NATIVE_METATILE_INDEX)
	@test -f "$@"

$(PC080SN_PLANE_B_VISUAL_RECORDS): $(MAINCPU_REGION) $(PC080SN_ATTR_LUT) $(PC080SN_PLANE_B_VISUAL_GEN)
	$(PYTHON) "$(PC080SN_PLANE_B_VISUAL_GEN)" \
		--maincpu "$(MAINCPU_REGION)" --attr-lut "$(PC080SN_ATTR_LUT)" \
		--output "$(PC080SN_PLANE_B_VISUAL_RECORDS)" \
		--report "$(PC080SN_PLANE_B_VISUAL_REPORT)"

$(PC080SN_PLANE_B_VISUAL_REPORT): $(PC080SN_PLANE_B_VISUAL_RECORDS)
	@test -f "$@"

$(PC090OJ_PRECONV): $(PC090OJ_REGION) $(ROOT)/tools/translation/preconvert_pc090oj_tiles.py
	$(PYTHON) "$(ROOT)/tools/translation/preconvert_pc090oj_tiles.py" \
		--input "$<" --output "$@"

$(PC090OJ_EDITOR): $(PC090OJ_PRECONV) $(EDITOR_LAYERA_SNAPSHOT) $(R1P1_ENEMY_CORPUS) $(H24_WEAPON_CELLS) $(H24_PLAYER_CELLS) $(H24_LEG_CELLS) $(ROOT)/tools/graphics_editor/gen_reindexed_pc090oj.py | $(OUT_DIR)
	$(PYTHON) "$(ROOT)/tools/graphics_editor/gen_reindexed_pc090oj.py" \
		--profile "$(EDITOR_LAYERA_SNAPSHOT)" --pc090oj "$(PC090OJ_PRECONV)" \
		--corpus "$(R1P1_ENEMY_CORPUS)" --out "$(PC090OJ_EDITOR)" \
		--variants-inc "$(PC090OJ_VARIANTS_INC)"

$(PC090OJ_LAYER1_STAMP): $(PC090OJ_EDITOR) $(PC090OJ_PRECONV) $(EDITOR_LAYERA_SNAPSHOT) $(R1P1_ENEMY_CORPUS) $(PC090OJ_LAYER1_VERIFY) | $(OUT_DIR)
	$(PYTHON) "$(PC090OJ_LAYER1_VERIFY)" --profile "$(EDITOR_LAYERA_SNAPSHOT)" \
		--corpus "$(R1P1_ENEMY_CORPUS)" --raw "$(PC090OJ_PRECONV)" --editor "$(PC090OJ_EDITOR)"
	@touch "$@"

# The variant index include is produced as a side-effect of the pc090oj_editor.bin recipe.
$(PC090OJ_VARIANTS_INC): $(PC090OJ_EDITOR)
	@test -f "$@"

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

$(PC090OJ_FRAME_TABLE) $(PC090OJ_PLAYER_PIECE_TABLE) $(PC090OJ_FRAME_INDEX) $(PC090OJ_SECONDARY_FRAME_INDEX) $(PC090OJ_GENERIC_FRAME_INDEX) $(PC090OJ_GENERIC_PIECE_TABLE) $(PC090OJ_UNIVERSAL_FRAME_INDEX) $(PC090OJ_SPECIAL_FRAME_INDEX) $(PC090OJ_DEATH_FRAME_INDEX) $(PC090OJ_DEATH_PIECE_TABLE) $(PC090OJ_GENERIC_BASE_LUT) $(PC090OJ_GENERIC_USAGE_TABLE) $(PC090OJ_FRAME_RESIDENCY) $(PC090OJ_FRAME_REPORT) $(PC090OJ_FRAME_COVERAGE): $(MAINCPU_REGION) $(PC090OJ_EDITOR) $(EDITOR_LAYERA_SNAPSHOT) $(PALETTE_DECISIONS) $(H24_WEAPON_CELLS) $(H24_PLAYER_CELLS) $(H24_LEG_CELLS) $(H16_BURST_RENDER) $(ACTOR_GRAPHICS_MANIFEST) $(R1P1_ENEMY_CORPUS) $(PC090OJ_FRAME_GEN) $(PC090OJ_FRAME_VERIFY) $(PC090OJ_DISPATCH_VERIFY)
	$(PYTHON) "$(PC090OJ_FRAME_GEN)" \
		--maincpu "$(MAINCPU_REGION)" --variant-index "$(ROOT)/build/regions/pc090oj_variant_index.json" \
		--body-evidence "$(H24_PLAYER_CELLS)" --weapon-evidence "$(H24_WEAPON_CELLS)" \
		--leg-evidence "$(H24_LEG_CELLS)" \
		--profile "$(EDITOR_LAYERA_SNAPSHOT)" --palette-decisions "$(PALETTE_DECISIONS)" \
		--burst-evidence "$(H16_BURST_RENDER)" --actor-manifest "$(ACTOR_GRAPHICS_MANIFEST)" \
		--enemy-corpus "$(R1P1_ENEMY_CORPUS)" \
		--table-output "$(PC090OJ_FRAME_TABLE)" --player-table-output "$(PC090OJ_PLAYER_PIECE_TABLE)" \
		--index-output "$(PC090OJ_FRAME_INDEX)" \
		--secondary-index-output "$(PC090OJ_SECONDARY_FRAME_INDEX)" \
		--generic-index-output "$(PC090OJ_GENERIC_FRAME_INDEX)" \
		--generic-table-output "$(PC090OJ_GENERIC_PIECE_TABLE)" \
		--universal-index-output "$(PC090OJ_UNIVERSAL_FRAME_INDEX)" \
		--special-index-output "$(PC090OJ_SPECIAL_FRAME_INDEX)" \
		--death-index-output "$(PC090OJ_DEATH_FRAME_INDEX)" \
		--death-table-output "$(PC090OJ_DEATH_PIECE_TABLE)" \
		--generic-base-lut-output "$(PC090OJ_GENERIC_BASE_LUT)" \
		--generic-usage-output "$(PC090OJ_GENERIC_USAGE_TABLE)" \
		--residency-output "$(PC090OJ_FRAME_RESIDENCY)" --report-output "$(PC090OJ_FRAME_REPORT)" \
		--coverage-output "$(PC090OJ_FRAME_COVERAGE)"
	$(PYTHON) "$(PC090OJ_FRAME_VERIFY)" --maincpu "$(MAINCPU_REGION)" \
		--variant-index "$(ROOT)/build/regions/pc090oj_variant_index.json" \
		--table "$(PC090OJ_FRAME_TABLE)" --player-table "$(PC090OJ_PLAYER_PIECE_TABLE)" \
		--index "$(PC090OJ_FRAME_INDEX)" \
		--secondary-index "$(PC090OJ_SECONDARY_FRAME_INDEX)" \
		--generic-index "$(PC090OJ_GENERIC_FRAME_INDEX)" \
		--generic-table "$(PC090OJ_GENERIC_PIECE_TABLE)" \
		--universal-index "$(PC090OJ_UNIVERSAL_FRAME_INDEX)" \
		--special-index "$(PC090OJ_SPECIAL_FRAME_INDEX)" \
		--death-index "$(PC090OJ_DEATH_FRAME_INDEX)" \
		--death-table "$(PC090OJ_DEATH_PIECE_TABLE)" \
		--generic-base-lut "$(PC090OJ_GENERIC_BASE_LUT)" \
		--generic-usage "$(PC090OJ_GENERIC_USAGE_TABLE)" \
		--residency "$(PC090OJ_FRAME_RESIDENCY)" --coverage "$(PC090OJ_FRAME_COVERAGE)"
	$(PYTHON) "$(PC090OJ_DISPATCH_VERIFY)" --base-lut "$(PC090OJ_GENERIC_BASE_LUT)" \
		--usage "$(PC090OJ_GENERIC_USAGE_TABLE)" --index "$(PC090OJ_GENERIC_FRAME_INDEX)" \
		--death-index "$(PC090OJ_DEATH_FRAME_INDEX)" \
		--assembly "$(SRC_DIR)/pc090oj_hooks.s"

# Generate the PC090OJ helper sizing include from the Make variable each build so
# an override (PC090OJ_MIRROR_RECORDS=N) is always applied without hand-editing.
$(PC090OJ_CONFIG_INC): FORCE_ASM_REBUILD | $(OUT_DIR)
	@printf '/* GENERATED from PC090OJ_MIRROR_RECORDS=%s RASTAN_GAMEPLAY_HUD_SPRITES=%s RASTAN_DIAG_CPU_BAR=%s RASTAN_DIAG_SCORE_METRIC=%s RASTAN_VBLANK_DISPLAY_OFF=%s RASTAN_MODE_RACK_ADVANCE=%s RASTAN_INVINCIBLE=%s by apps/rastan-direct/Makefile -- do not hand-edit. */\n.equ PC090OJ_MIRROR_RECORDS, %s\n.equ PC090OJ_MIRROR_BYTES, (PC090OJ_MIRROR_RECORDS * 8)\n.equ PC090OJ_BITSET_BYTES, ((PC090OJ_MIRROR_RECORDS + 7) / 8)\n.equ RASTAN_GAMEPLAY_HUD_SPRITES, %s\n.equ RASTAN_DIAG_CPU_BAR, %s\n.equ RASTAN_DIAG_SCORE_METRIC, %s\n.equ RASTAN_VBLANK_DISPLAY_OFF, %s\n.equ RASTAN_MODE_RACK_ADVANCE, %s\n.equ RASTAN_INVINCIBLE, %s\n' '$(PC090OJ_MIRROR_RECORDS)' '$(RASTAN_GAMEPLAY_HUD_SPRITES)' '$(RASTAN_DIAG_CPU_BAR)' '$(RASTAN_DIAG_SCORE_METRIC)' '$(RASTAN_VBLANK_DISPLAY_OFF)' '$(RASTAN_MODE_RACK_ADVANCE)' '$(RASTAN_INVINCIBLE)' '$(PC090OJ_MIRROR_RECORDS)' '$(RASTAN_GAMEPLAY_HUD_SPRITES)' '$(RASTAN_DIAG_CPU_BAR)' '$(RASTAN_DIAG_SCORE_METRIC)' '$(RASTAN_VBLANK_DISPLAY_OFF)' '$(RASTAN_MODE_RACK_ADVANCE)' '$(RASTAN_INVINCIBLE)' > $@
	@echo "PC090OJ_MIRROR_RECORDS=$(PC090OJ_MIRROR_RECORDS) RASTAN_GAMEPLAY_HUD_SPRITES=$(RASTAN_GAMEPLAY_HUD_SPRITES) RASTAN_DIAG_CPU_BAR=$(RASTAN_DIAG_CPU_BAR) RASTAN_DIAG_SCORE_METRIC=$(RASTAN_DIAG_SCORE_METRIC) RASTAN_VBLANK_DISPLAY_OFF=$(RASTAN_VBLANK_DISPLAY_OFF) RASTAN_MODE_RACK_ADVANCE=$(RASTAN_MODE_RACK_ADVANCE) RASTAN_INVINCIBLE=$(RASTAN_INVINCIBLE) -> $@"

# Build 0340 OPT-003: generate the prebaked (scene,effective_bank)->palette-line LUT from the authored
# The current Palette Editing Tool snapshot authors R1/P1 mappings. The live route
# table is retained only as the pre-migration oracle for unauthored inputs. Every
# build proves direct-map and exhaustive SAT word-2 equivalence.
$(PC090OJ_PALSEL_LUT_INC): $(SRC_DIR)/palette_hooks.s $(EDITOR_LAYERA_SNAPSHOT) $(PC090OJ_PALSEL_LUT_GEN) | $(OUT_DIR)
	$(PYTHON) $(PC090OJ_PALSEL_LUT_GEN) --route-src $(SRC_DIR)/palette_hooks.s \
		--profile $(EDITOR_LAYERA_SNAPSHOT) --out $@ --report $(PC090OJ_PALSEL_EQUIV) --verify

$(OUT_DIR)/title_native.o: $(SRC_DIR)/title_native.s $(PC090OJ_CONFIG_INC) $(NATIVE_TITLE_BG) $(NATIVE_TITLE_FG) $(NATIVE_TITLE_FG_INVINCIBLE) $(NATIVE_TITLE_PALETTE) $(NATIVE_TITLE_PATTERNS) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/hud_native.o: $(SRC_DIR)/hud_native.s $(NATIVE_HUD_PATTERNS) $(NATIVE_HUD_STATIC_SAT) $(NATIVE_HUD_DYNAMIC_RECORDS) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/item_native.o: $(SRC_DIR)/item_native.s $(NATIVE_ITEM_LOGICAL_MAP) $(NATIVE_ITEM_INITIAL_ROWS) $(NATIVE_ITEM_PLANE_PATTERNS) $(NATIVE_ITEM_ICON_PATTERNS) $(NATIVE_ITEM_ICON_RECORDS) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/pc090oj_hooks.o: $(SRC_DIR)/pc090oj_hooks.s $(PC090OJ_CONFIG_INC) $(PC090OJ_PALSEL_LUT_INC) $(PC090OJ_VARIANTS_INC) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/pc090oj_assets.o: $(SRC_DIR)/pc090oj_assets.s $(PC090OJ_EDITOR) $(PC090OJ_LAYER1_STAMP) $(PC090OJ_HUD_WHITE) $(PC090OJ_SLOT_LUT) $(PC090OJ_BLANK_BITSET) $(PC090OJ_OPAQUE_BBOX) $(PC090OJ_FRAME_TABLE) $(PC090OJ_PLAYER_PIECE_TABLE) $(PC090OJ_FRAME_INDEX) $(PC090OJ_SECONDARY_FRAME_INDEX) $(PC090OJ_GENERIC_FRAME_INDEX) $(PC090OJ_GENERIC_PIECE_TABLE) $(PC090OJ_UNIVERSAL_FRAME_INDEX) $(PC090OJ_SPECIAL_FRAME_INDEX) $(PC090OJ_DEATH_FRAME_INDEX) $(PC090OJ_DEATH_PIECE_TABLE) $(PC090OJ_GENERIC_BASE_LUT) $(PC090OJ_GENERIC_USAGE_TABLE) $(PC090OJ_FRAME_RESIDENCY) FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/diag_bookmark.o: $(SRC_DIR)/diag_bookmark.s FORCE_ASM_REBUILD | $(OUT_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

$(OUT_DIR)/scene_load.o: \
	$(SRC_DIR)/scene_load.s \
	$(PC080SN_TILE_LUT) \
	$(PC080SN_ATTR_LUT) \
	$(PC080SN_NATIVE_METATILE_INDEX) \
	$(PC080SN_NATIVE_METATILE_RECORDS) \
	$(PC080SN_PLANE_B_VISUAL_RECORDS) \
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

$(BIN): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(ATTRACT_PLANE_B_ENTRY_VERIFY) $(BOOT_GUARD) $(GAMEPLAY_ENTRY_GATE) $(PHASE1_EPOCH_GATE) $(BG_A_INCREMENTAL_GATE) $(PLANE_A_SEL0_SEGMENT_GATE) $(PLANE_A_SEL12_SEGMENT_GATE) $(VDP_DMA_BOUNDARY_GATE) $(PC080SN_NATIVE_METATILE_VERIFY) $(PC080SN_PLANE_B_VISUAL_VERIFY) $(PC080SN_PLANE_B_VISUAL_REPORT) $(COLLISION_VISUAL_SEMANTICS_VERIFY) $(NATIVE_TITLE_VERIFY) $(NATIVE_TITLE_REPORT) $(NATIVE_HUD_VERIFY) $(NATIVE_HUD_REPORT) $(NATIVE_ITEM_VERIFY) $(NATIVE_ITEM_REPORT) $(BEST5_TABLE_VERIFY) $(BEST5_TABLE_REPORT) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/canonical.inc"
	$(PYTHON) "$(PC080SN_NATIVE_METATILE_VERIFY)" --maincpu "$(MAINCPU_REGION)" \
		--index "$(PC080SN_NATIVE_METATILE_INDEX)" --records "$(PC080SN_NATIVE_METATILE_RECORDS)" \
		--report "$(PC080SN_NATIVE_METATILE_REPORT)"
	$(PYTHON) "$(PC080SN_PLANE_B_VISUAL_VERIFY)" --maincpu "$(MAINCPU_REGION)" \
		--attr-lut "$(PC080SN_ATTR_LUT)" --records "$(PC080SN_PLANE_B_VISUAL_RECORDS)" \
		--report "$(PC080SN_PLANE_B_VISUAL_REPORT)"
	$(PYTHON) "$(BG_A_INCREMENTAL_GATE)"
	$(PYTHON) "$(PLANE_A_SEL0_SEGMENT_GATE)" --maincpu "$(MAINCPU_REGION)" \
		--index "$(PC080SN_NATIVE_METATILE_INDEX)" --records "$(PC080SN_NATIVE_METATILE_RECORDS)"
	$(PYTHON) "$(PLANE_A_SEL12_SEGMENT_GATE)" --maincpu "$(MAINCPU_REGION)" \
		--index "$(PC080SN_NATIVE_METATILE_INDEX)" --records "$(PC080SN_NATIVE_METATILE_RECORDS)"
	$(PYTHON) "$(COLLISION_VISUAL_SEMANTICS_VERIFY)"
	$(PYTHON) "$(NATIVE_TITLE_VERIFY)" --generator "$(NATIVE_TITLE_GEN)" \
		--maincpu "$(MAINCPU_REGION)" --pc080sn "$(PC080SN_REGION)" \
		--title-preload "$(PC080SN_SCENE_PRELOAD_TITLE)" --attr-lut "$(PC080SN_ATTR_LUT)" \
		--bg "$(NATIVE_TITLE_BG)" --fg "$(NATIVE_TITLE_FG)" \
		--fg-invincible "$(NATIVE_TITLE_FG_INVINCIBLE)" --palette "$(NATIVE_TITLE_PALETTE)" \
		--patterns "$(NATIVE_TITLE_PATTERNS)" --report "$(NATIVE_TITLE_REPORT)" \
		--spec "$(PATCH_SPEC)" --title-source "$(SRC_DIR)/title_native.s"
	$(PYTHON) "$(NATIVE_HUD_VERIFY)" --generator "$(NATIVE_HUD_GEN)" \
		--maincpu "$(MAINCPU_REGION)" --pc090oj "$(PC090OJ_PRECONV)" \
		--patterns "$(NATIVE_HUD_PATTERNS)" --static-sat "$(NATIVE_HUD_STATIC_SAT)" \
		--dynamic-records "$(NATIVE_HUD_DYNAMIC_RECORDS)" --report "$(NATIVE_HUD_REPORT)" \
		--hud-source "$(SRC_DIR)/hud_native.s" --sprite-source "$(SRC_DIR)/pc090oj_hooks.s" \
		--title-source "$(SRC_DIR)/title_native.s"
	$(PYTHON) "$(NATIVE_ITEM_VERIFY)" --maincpu "$(MAINCPU_REGION)" \
		--pc080sn "$(PC080SN_REGION)" --pc090oj "$(PC090OJ_PRECONV)" \
		--hud-report "$(NATIVE_HUD_REPORT)" \
		--logical-map "$(NATIVE_ITEM_LOGICAL_MAP)" \
		--initial-rows "$(NATIVE_ITEM_INITIAL_ROWS)" --reference "$(NATIVE_ITEM_REFERENCE)" \
		--plane-patterns "$(NATIVE_ITEM_PLANE_PATTERNS)" \
		--icon-patterns "$(NATIVE_ITEM_ICON_PATTERNS)" \
		--icon-records "$(NATIVE_ITEM_ICON_RECORDS)" --report "$(NATIVE_ITEM_REPORT)" \
		--assembly "$(SRC_DIR)/item_native.s" --sprite-source "$(SRC_DIR)/pc090oj_hooks.s" \
		--palette-lut "$(PC090OJ_PALSEL_LUT_INC)" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(VDP_DMA_BOUNDARY_GATE)" --symbols "$(SYMBOLS)" --patterns "$(PC080SN_EDITOR_LAYERA)"
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
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(ATTRACT_PLANE_B_ENTRY_VERIFY)" \
		--tilemap-source "$(SRC_DIR)/tilemap_hooks.s" \
		--sprite-source "$(SRC_DIR)/pc090oj_hooks.s"
	$(PYTHON) "$(BEST5_TABLE_VERIFY)" --maincpu "$(MAINCPU_REGION)" --rom "$@" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" \
		--symbols "$(SYMBOLS)" \
		--number-table "$(BEST5_NUMBER_TABLE)" --name-table "$(BEST5_NAME_TABLE)" \
		--tilemap-source "$(SRC_DIR)/tilemap_hooks.s"
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
	: '=== Tighe imperative 2026-09-08: gates are LABELS, not blockers. The gates below are'; \
	: 'run for their verdict, but NEVER delete, withhold, or un-number a built ROM. Every ROM'; \
	: 'that reaches this point is numbered and preserved regardless of gate outcome, so Tighe'; \
	: 'can evaluate any and all builds. Validation describes the build; it does not grant it'; \
	: 'permission to exist. See RULES.md / CLAUDE.md.'; \
	gate_status=""; \
	if "$(PYTHON)" "$(CANONICAL_GATE)" \
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
		--state-file "$(BOOKMARK_STATE_FILE)"; then \
		gate_status="canonical=PASS"; \
	else \
		gate_status="canonical=FAIL"; \
		echo "WARNING: canonical gate FAILED -- ROM still numbered+preserved for evaluation"; \
	fi; \
	if "$(GAMEPLAY_ENTRY_GATE)" "$@" "$(SYMBOLS)" "$$tag"; then \
		gate_status="$$gate_status entry=PASS"; \
	else \
		gate_status="$$gate_status entry=FAIL"; \
		echo "WARNING: start-to-gameplay gate FAILED -- ROM still numbered+preserved for evaluation"; \
	fi; \
	if "$(PHASE1_EPOCH_GATE)" "$@" "$(SYMBOLS)" "$$tag"; then \
		gate_status="$$gate_status epoch=PASS"; \
	else \
		gate_status="$$gate_status epoch=FAIL"; \
		echo "WARNING: phase1 seven-epoch gate FAILED -- ROM still numbered+preserved for evaluation"; \
	fi; \
	cp "$@" "$$numbered"; \
	if [ ! -s "$$numbered" ]; then echo "ERROR: numbered build artifact missing/empty after copy: $$numbered"; exit 1; fi; \
	printf "%d\n" "$$next" > "$$counter_file"; \
	printf "%s PRODUCED %s auto-recorded-by-release [%s]\n" "$$tag" "$$(date +%Y-%m-%d)" "$$gate_status" >> "$(CONSUMED_BUILD_LEDGER)"; \
	echo "numbered build artifact: $$numbered [$$gate_status]"; \
	trace_ts=$$(date +%Y%m%d_%H%M%S); \
	trace_dir="$(ROOT)/states/traces/$(NUMBERED_PREFIX)_$${tag}_mame_30s_$${trace_ts}"; \
	mkdir -p "$$trace_dir" || true; \
	trace_cmd='timeout 120s "$(ROOT)/tools/mame/run_genesis_trace_wsl.sh" "$@" -video none -sound none -nothrottle -seconds_to_run 30'; \
	echo "trace command: $$trace_cmd"; \
	if ! eval "$$trace_cmd"; then echo "WARNING: Genesis trace command failed -- ROM $$numbered still preserved"; fi; \
	cp "$(ROOT)/build/mame/home/genesistrace/genesis_exec_summary.txt" "$$trace_dir/" 2>/dev/null || true; \
	cp "$(ROOT)/build/mame/home/genesistrace/genesis_exec_trace.log" "$$trace_dir/" 2>/dev/null || true; \
	if [ -f "$(ROOT)/build/mame/home/genesistrace/trace_metadata.txt" ]; then cp "$(ROOT)/build/mame/home/genesistrace/trace_metadata.txt" "$$trace_dir/"; fi; \
	if [ -f "$(ROOT)/build/mame/home/genesistrace/mame_stdout.txt" ]; then cp "$(ROOT)/build/mame/home/genesistrace/mame_stdout.txt" "$$trace_dir/"; fi; \
	echo "trace saved to: $$trace_dir"

# Build 0337: diagnostic ROM = the same postpatch pipeline as $(BIN) but WITHOUT the numbered
# release/counter/gates (those belong to the normal build).  Built with RASTAN_DIAG_CPU_BAR=1 via
# the recursive `diag-variant` invocation, so config.inc regenerates and every object re-assembles
# with the bar enabled.  Uses a separate manifest so the normal build's manifest is untouched.
$(DIAG_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/diag.inc"
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
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

# Copy the diagnostic ROM to the SAME build number as the just-produced numbered release, with a
# "_d" suffix.  Does not touch the counter or ledger (the normal build already advanced them).
diag-variant: $(DIAG_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_d.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing diagnostic build: $$dest"; exit 1; fi; \
	cp "$(DIAG_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: diagnostic build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "diagnostic build artifact (CPU-load bar): $$dest"

# Build 0338: score-metric ROM = same postpatch-only pipeline as $(DIAG_ROM) but built with
# RASTAN_DIAG_SCORE_METRIC=1 (via the recursive `score-variant` invocation). Separate manifest.
# Build 0396: the third generated Plane-A overlap package grows canonical coverage onto the
# formerly score-only aligned page, so this variant no longer adds a coverage page.
$(SCORE_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/score.inc"
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
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

# Copy the score-metric ROM to the SAME build number as the numbered release, with a "_s" suffix.
# Does not touch the counter or ledger.
score-variant: $(SCORE_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_s.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing score-metric build: $$dest"; exit 1; fi; \
	cp "$(SCORE_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: score-metric build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "diagnostic build artifact (score metric): $$dest"

# Build 0344: display-off ROM = same postpatch-only pipeline as $(DIAG_ROM) but built with
# RASTAN_VBLANK_DISPLAY_OFF=1 (via the recursive `do-variant` invocation).  Separate manifest.
# This is the Rainbow-model publication-phase forced-blank variant; NOT a diagnostic overlay.
$(DO_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/display_off.inc"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/do_patch_manifest.json" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

# Copy the display-off ROM to the SAME build number as the numbered release, with a "_do" suffix.
# Does not touch the counter or ledger.
do-variant: $(DO_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_do.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing display-off build: $$dest"; exit 1; fi; \
	cp "$(DO_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: display-off build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "display-off build artifact (RASTAN_VBLANK_DISPLAY_OFF=1): $$dest"

# Build 0360: MODE rack-advance ROM.  This uses the normal postpatch pipeline,
# but the compile-time feature and its two state bytes exist only in the _c ROM.
# Build 0378: canonical helper growth reached the formerly MODE-only aligned page,
# so this variant needed no additional coverage delta.
# Build 0396: the third generated Plane-A overlap package grows canonical coverage onto the
# formerly MODE-only aligned page, so this variant again needs no additional coverage delta.
$(CHEAT_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/cheat.inc"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/cheat_patch_manifest.json" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

cheat-variant: $(CHEAT_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_c.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing cheat build: $$dest"; exit 1; fi; \
	cp "$(CHEAT_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: cheat build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "cheat build artifact (RASTAN_MODE_RACK_ADVANCE=1): $$dest"

# Permanent full-gameplay-HUD comparison ROM. It uses the canonical release
# configuration except for RASTAN_GAMEPLAY_HUD_SPRITES=1 and shares the already
# consumed canonical build number exactly like the diagnostic variants.
$(FULL_HUD_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/full_hud.inc"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/full_hud_patch_manifest.json" \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

full-hud-variant: $(FULL_HUD_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_full_hud.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing full-HUD build: $$dest"; exit 1; fi; \
	cp "$(FULL_HUD_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: full-HUD build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "full-HUD build artifact (RASTAN_GAMEPLAY_HUD_SPRITES=1): $$dest"

# Permanent normal-display invincibility ROM for deterministic benchmarks. The
# normal code image is built with the canonical flags; only the postpatcher's
# spec-declared source-data patch makes the arcade startup initializer assert
# A5+0x0040. It shares the canonical build number and never enters the ledger.
$(INVINCIBLE_ROM): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(R1_SELECTOR_STREAM_VERIFY) $(BOOT_GUARD) $(INVINCIBLE_VARIANT_VERIFY) | $(DIST_DIR) $(VARIANT_CONFIG_DIR)
	cp "$(PC090OJ_CONFIG_INC)" "$(VARIANT_CONFIG_DIR)/invincible.inc"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$(PREPATCH_BIN)"
	cp "$(PREPATCH_BIN)" "$@"
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(PATCHER)" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$@" \
		--symbols "$(SYMBOLS)" \
		--manifest "$(OUT_DIR)/invincible_patch_manifest.json" \
		--invincible \
		--spec "$(PATCH_SPEC)"
	$(PYTHON) "$(R1_SELECTOR_STREAM_VERIFY)" --rom "$@" --maincpu "$(MAINCPU_REGION)" \
		--address-map "$(ROOT)/build/rastan-direct/address_map.json" --spec "$(PATCH_SPEC)"
	$(PYTHON) "$(BOOT_GUARD)" --rom "$@"

invincible-variant: $(INVINCIBLE_ROM)
	@n=$$(if [ -f "$(NUMBERED_COUNTER)" ]; then cat "$(NUMBERED_COUNTER)"; else echo 0; fi); \
	tag=$$(printf "%04d" "$$n"); \
	dest="$(NUMBERED_DIST_DIR)/$(NUMBERED_PREFIX)_$${tag}_invincible.bin"; \
	if [ -e "$$dest" ]; then echo "ERROR: refusing to overwrite existing invincible build: $$dest"; exit 1; fi; \
	cp "$(INVINCIBLE_ROM)" "$$dest"; \
	if [ ! -s "$$dest" ]; then echo "ERROR: invincible build artifact missing/empty: $$dest"; exit 1; fi; \
	echo "invincible build artifact (RASTAN_INVINCIBLE=1): $$dest"

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
