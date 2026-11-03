ifndef GDK
$(error GDK is not set. Run "source ../../tools/setup_env.sh" from the repo root first.)
endif

all: release

regions:
	python3 ../../tools/build_rastan_regions.py

release: regions
	$(MAKE) -f $(GDK)/makefile.gen release

debug: regions
	$(MAKE) -f $(GDK)/makefile.gen debug

clean:
	$(MAKE) -f $(GDK)/makefile.gen clean

.PHONY: all regions release debug clean
