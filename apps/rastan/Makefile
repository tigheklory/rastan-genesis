ifndef GDK
$(error GDK is not set. Run "source ../../tools/setup_env.sh" from the repo root first.)
endif

all: release

release:
	$(MAKE) -f $(GDK)/makefile.gen release
	@mkdir -p ../../dist
	@count=$$(cat ../../dist/release_counter.txt 2>/dev/null || echo 0); \
	count=$$((count + 1)); \
	printf "%s" "$$count" > ../../dist/release_counter.txt; \
	stamp=$$(date +%Y%m%d_%H%M%S); \
	name="Rastan_$${count}_$${stamp}.bin"; \
	cp out/rom.bin ../../dist/$$name; \
	printf "%s\n" "$$name" > ../../dist/latest_release_name.txt; \
	echo "Release: ../../dist/$$name"

debug:
	$(MAKE) -f $(GDK)/makefile.gen debug

clean:
	$(MAKE) -f $(GDK)/makefile.gen clean

.PHONY: all release debug clean
