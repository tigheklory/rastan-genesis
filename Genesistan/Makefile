ROOT := $(abspath ..)
PYTHON ?= python3

.PHONY: patch-maincpu clean

patch-maincpu:
	$(PYTHON) tools/patch_maincpu.py \
		--input "$(ROOT)/build/regions/maincpu.bin" \
		--output "$(ROOT)/build/genesistan/maincpu_patched.bin" \
		--manifest "$(ROOT)/build/genesistan/maincpu_patch_manifest.json"

clean:
	rm -f "$(ROOT)/build/genesistan/maincpu_patched.bin" \
		"$(ROOT)/build/genesistan/maincpu_patch_manifest.json"
