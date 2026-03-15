ROOT := $(CURDIR)
PYTHON ?= python3
VARIANT ?= world_rev1

.PHONY: patch-maincpu startup-rom clean

patch-maincpu:
	$(PYTHON) "$(ROOT)/tools/build_rastan_regions.py" --variant "$(VARIANT)"
	$(PYTHON) tools/translation/patch_maincpu.py \
		--variant "$(VARIANT)" \
		--input "$(ROOT)/build/regions/maincpu.bin" \
		--output "$(ROOT)/build/rastan/maincpu_patched.bin" \
		--manifest "$(ROOT)/build/rastan/maincpu_patch_manifest.json" \
		--startup-output "$(ROOT)/build/rastan/startup_common_slice.bin" \
		--startup-manifest "$(ROOT)/build/rastan/startup_common_manifest.json"

startup-rom:
	$(MAKE) -C attic/startup-common-rom release VARIANT="$(VARIANT)"

clean:
	rm -f "$(ROOT)/build/rastan/maincpu_patched.bin" \
		"$(ROOT)/build/rastan/maincpu_patch_manifest.json" \
		"$(ROOT)/build/rastan/startup_common_slice.bin" \
		"$(ROOT)/build/rastan/startup_common_manifest.json"
