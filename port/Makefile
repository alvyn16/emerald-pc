# Diagnostic host build only. This never writes into ../pokeemerald.
POKEEMERALD := ../pokeemerald
HOST_CC ?= gcc
PKG_CONFIG ?= pkg-config

SDL2_CFLAGS := $(shell $(PKG_CONFIG) --cflags sdl2)
SOURCES := $(shell find $(POKEEMERALD)/src -type f -name '*.c' | sort)
CHECKS := $(patsubst $(POKEEMERALD)/src/%.c,check/%,$(SOURCES))
HOST_CFLAGS := -std=gnu11 -fsyntax-only -fmax-errors=5 -DMODERN=0 -DPORT_PC \
	-iquote $(POKEEMERALD)/include -I$(POKEEMERALD) $(SDL2_CFLAGS)

.PHONY: syntax check-tools
syntax: check-tools $(CHECKS)

check-tools:
	@$(PKG_CONFIG) --exists sdl2 || { echo 'SDL2 development files are required'; exit 1; }
	@$(HOST_CC) -dumpmachine | grep -q 'x86_64.*mingw' || { echo 'Use x86-64 GCC from MSYS2 MINGW64'; exit 1; }
	@echo "Checking $(words $(SOURCES)) C files with $(HOST_CC) and SDL2 headers"

check/%: $(POKEEMERALD)/src/%.c
	@echo "CHECK $<"
	@$(HOST_CC) $(HOST_CFLAGS) "$<"
