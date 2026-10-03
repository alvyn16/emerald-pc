# Diagnostic host build only. This never writes into ../pokeemerald.
# Match upstream's C pipeline: GCC -E | tools/preproc -i | host GCC.
# scaninc only produces dependency files in upstream's Makefile.
SHELL := bash
.SHELLFLAGS := -o pipefail -c

POKEEMERALD := ../pokeemerald
HOST_CC ?= gcc
PKG_CONFIG ?= pkg-config

SDL2_CFLAGS := $(shell $(PKG_CONFIG) --cflags sdl2)
SOURCES := $(shell find $(POKEEMERALD)/src -type f -name '*.c' | sort)
CHECKS := $(patsubst $(POKEEMERALD)/src/%.c,check/%,$(SOURCES))
HOST_CPPFLAGS := -std=gnu11 -E -DMODERN=0 -DPORT_PC -iquote include -I. $(SDL2_CFLAGS)
HOST_CFLAGS := -std=gnu11 -fsyntax-only -fmax-errors=5 -x c

.PHONY: syntax check-tools
syntax: $(CHECKS)

$(CHECKS): | check-tools

check-tools:
	@$(PKG_CONFIG) --exists sdl2 || { echo 'SDL2 development files are required'; exit 1; }
	@$(HOST_CC) -dumpmachine | grep -q 'x86_64.*mingw' || { echo 'Use x86-64 GCC from MSYS2 MINGW64'; exit 1; }
	@test -x $(POKEEMERALD)/tools/preproc/preproc.exe || { echo 'Build pokeemerald tools/preproc first'; exit 1; }
	@test -d $(POKEEMERALD)/build/assets || { echo 'Build pokeemerald assets first'; exit 1; }
	@test -f $(POKEEMERALD)/charmap.txt || { echo 'Missing pokeemerald/charmap.txt'; exit 1; }
	@echo "Checking $(words $(SOURCES)) C files with $(HOST_CC) and SDL2 headers"

check/%: $(POKEEMERALD)/src/%.c
	@echo "CHECK $<"
	@cd $(POKEEMERALD) && { \
		$(HOST_CC) $(HOST_CPPFLAGS) "src/$*.c" | \
		tools/preproc/preproc.exe -i -g build/assets "src/$*.c" charmap.txt | \
		$(HOST_CC) $(HOST_CFLAGS) -; \
	}
