ifndef GDK
$(error GDK is not set. Run "source /home/tighe/projects/rastan-genesis/tools/setup_env.sh" first.)
endif

ROOT := $(abspath ../..)
PYTHON ?= python3
VARIANT ?= world_rev1
RELEASES_DIR := $(ROOT)/dist
BUILD_COUNTER := $(ROOT)/dist/attic_build_counter.txt

all: release

release:
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) "$(ROOT)/tools/translation/patch_maincpu.py" \
		--variant "$(VARIANT)" \
		--input "$(ROOT)/build/regions/maincpu.bin" \
		--output "$(ROOT)/build/rastan/maincpu_patched.bin" \
		--manifest "$(ROOT)/build/rastan/maincpu_patch_manifest.json" \
		--startup-output "$(ROOT)/build/rastan/startup_common_slice.bin" \
		--startup-manifest "$(ROOT)/build/rastan/startup_common_manifest.json"
	$(MAKE) -f $(GDK)/makefile.gen release
	$(PYTHON) "$(ROOT)/tools/translation/postpatch_startup_rom.py" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "out/rom.bin" \
		--symbols "out/symbol.txt" \
		--manifest "$(ROOT)/build/rastan/startup_common_rom_manifest.json"
	@mkdir -p "$(RELEASES_DIR)"
	@count=$$(cat "$(BUILD_COUNTER)" 2>/dev/null || echo 0); \
	count=$$((count + 1)); \
	printf "%s" "$$count" > "$(BUILD_COUNTER)"; \
	stamp=$$(date +%Y%m%d_%H%M%S); \
	name="Rastan_attic_$${count}_$${stamp}.bin"; \
	cp "out/rom.bin" "$(RELEASES_DIR)/$$name"; \
	printf "%s\n" "$$name" > "$(ROOT)/dist/latest_attic_release_name.txt"; \
	echo "Wrote $(RELEASES_DIR)/$$name"

debug:
	$(MAKE) -f $(GDK)/makefile.gen debug

clean:
	$(MAKE) -f $(GDK)/makefile.gen clean

.PHONY: all release debug clean
