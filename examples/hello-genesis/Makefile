ifndef GDK
$(error GDK is not set. Run "source ../../tools/setup_env.sh" from the repo root first.)
endif

all: release

release:
	$(MAKE) -f $(GDK)/makefile.gen release

debug:
	$(MAKE) -f $(GDK)/makefile.gen debug

clean:
	$(MAKE) -f $(GDK)/makefile.gen clean

.PHONY: all release debug clean
