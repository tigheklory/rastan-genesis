ifndef GDK
$(error GDK is not set. Run "source ../../tools/setup_env.sh" from the repo root first.)
endif

ROOT := $(abspath ../..)
PYTHON ?= python3
VARIANT ?= world_rev1
NOHOOK_FLAGS := -DRASTAN_ENABLE_STARTUP_HOOK=0
RASTAN_EXCEPTION_DUMPER_MODE ?= 0
EXCEPTION_DUMPER_FLAGS := -DRASTAN_EXCEPTION_DUMPER_MODE=$(RASTAN_EXCEPTION_DUMPER_MODE)
RASTAN_BUILD_NUMBER ?= 0
BUILD_INFO_HEADER := $(CURDIR)/inc/build_info.h
MD_LDSCRIPT := $(CURDIR)/linker_rastan.ld

all: release

release:
	@mkdir -p ../../dist
	@count=$$(cat ../../dist/release_counter.txt 2>/dev/null || echo 0); \
	set -e; \
	count=$$((count + 1)); \
	stamp=$$(date +%Y%m%d_%H%M%S); \
	$(PYTHON) "$(ROOT)/tools/translation/write_build_info.py" \
		--header "$(BUILD_INFO_HEADER)" \
		--build-number "$$count" \
		--build-stamp "$$stamp" \
		--variant "$(VARIANT)" \
		--hook-mode "hooked"; \
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"; \
	$(PYTHON) "$(ROOT)/tools/translation/patch_maincpu.py" \
		--variant "$(VARIANT)" \
		--input "$(ROOT)/build/regions/maincpu.bin" \
		--output "$(ROOT)/build/rastan/maincpu_patched.bin" \
		--manifest "$(ROOT)/build/rastan/maincpu_patch_manifest.json" \
		--startup-output "$(ROOT)/build/rastan/startup_common_slice.bin" \
		--startup-manifest "$(ROOT)/build/rastan/startup_common_manifest.json"; \
	$(MAKE) -f $(GDK)/makefile.gen release EXTRA_FLAGS="$(EXCEPTION_DUMPER_FLAGS)" MD_LDSCRIPT="$(MD_LDSCRIPT)"; \
	$(PYTHON) "$(ROOT)/tools/translation/postpatch_startup_rom.py" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$(CURDIR)/out/rom.bin" \
		--symbols "$(CURDIR)/out/symbol.txt" \
		--manifest "$(ROOT)/build/rastan/startup_common_rom_manifest.json"; \
	printf "%s" "$$count" > ../../dist/release_counter.txt; \
	name="Rastan_$${count}.bin"; \
	cp out/rom.bin ../../dist/$$name; \
	printf "%s\n" "$$name" > ../../dist/latest_release_name.txt; \
	echo "Release: ../../dist/$$name"

release-nohook:
	@mkdir -p ../../dist
	@count=$$(cat ../../dist/release_counter.txt 2>/dev/null || echo 0); \
	set -e; \
	count=$$((count + 1)); \
	stamp=$$(date +%Y%m%d_%H%M%S); \
	$(PYTHON) "$(ROOT)/tools/translation/write_build_info.py" \
		--header "$(BUILD_INFO_HEADER)" \
		--build-number "$$count" \
		--build-stamp "$$stamp" \
		--variant "$(VARIANT)" \
		--hook-mode "nohook"; \
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"; \
	$(MAKE) -f $(GDK)/makefile.gen release EXTRA_FLAGS="$(NOHOOK_FLAGS) $(EXCEPTION_DUMPER_FLAGS)" MD_LDSCRIPT="$(MD_LDSCRIPT)"; \
	printf "%s" "$$count" > ../../dist/release_counter.txt; \
	name="Rastan_$${count}.bin"; \
	cp out/rom.bin ../../dist/$$name; \
	printf "%s\n" "$$name" > ../../dist/latest_release_name.txt; \
	echo "Release: ../../dist/$$name"

debug:
	@stamp=$$(date +%Y%m%d_%H%M%S); \
	set -e; \
	$(PYTHON) "$(ROOT)/tools/translation/write_build_info.py" \
		--header "$(BUILD_INFO_HEADER)" \
		--build-number "$(RASTAN_BUILD_NUMBER)" \
		--build-stamp "$$stamp" \
		--variant "$(VARIANT)" \
		--hook-mode "debug-hooked"; \
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"; \
	$(PYTHON) "$(ROOT)/tools/translation/patch_maincpu.py" \
		--variant "$(VARIANT)" \
		--input "$(ROOT)/build/regions/maincpu.bin" \
		--output "$(ROOT)/build/rastan/maincpu_patched.bin" \
		--manifest "$(ROOT)/build/rastan/maincpu_patch_manifest.json" \
		--startup-output "$(ROOT)/build/rastan/startup_common_slice.bin" \
		--startup-manifest "$(ROOT)/build/rastan/startup_common_manifest.json"; \
	$(MAKE) -f $(GDK)/makefile.gen debug EXTRA_FLAGS="$(EXCEPTION_DUMPER_FLAGS)" MD_LDSCRIPT="$(MD_LDSCRIPT)"; \
	$(PYTHON) "$(ROOT)/tools/translation/postpatch_startup_rom.py" \
		--variant "$(VARIANT)" \
		--maincpu "$(ROOT)/build/regions/maincpu.bin" \
		--rom "$(CURDIR)/out/rom.bin" \
		--symbols "$(CURDIR)/out/symbol.txt" \
		--manifest "$(ROOT)/build/rastan/startup_common_rom_manifest.json"

debug-nohook:
	@stamp=$$(date +%Y%m%d_%H%M%S); \
	set -e; \
	$(PYTHON) "$(ROOT)/tools/translation/write_build_info.py" \
		--header "$(BUILD_INFO_HEADER)" \
		--build-number "$(RASTAN_BUILD_NUMBER)" \
		--build-stamp "$$stamp" \
		--variant "$(VARIANT)" \
		--hook-mode "debug-nohook"; \
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"; \
	$(MAKE) -f $(GDK)/makefile.gen debug EXTRA_FLAGS="$(NOHOOK_FLAGS) $(EXCEPTION_DUMPER_FLAGS)" MD_LDSCRIPT="$(MD_LDSCRIPT)"

clean:
	$(MAKE) -f $(GDK)/makefile.gen clean

.PHONY: all release release-nohook debug debug-nohook clean
