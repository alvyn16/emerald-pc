# Diagnostic host build only. This never writes into ../pokeemerald.
# Match upstream's C pipeline: GCC -E | tools/preproc -i | host GCC.
# scaninc only produces dependency files in upstream's Makefile.
SHELL := bash
.SHELLFLAGS := -o pipefail -c

POKEEMERALD := ../pokeemerald
HOST_CC ?= gcc
HOST_ARCH ?= x86_64
PKG_CONFIG ?= pkg-config

SDL2_CFLAGS := $(shell $(PKG_CONFIG) --cflags sdl2)
SOURCES := $(shell find $(POKEEMERALD)/src -type f -name '*.c' | sort)
CHECKS := $(patsubst $(POKEEMERALD)/src/%.c,check/%,$(SOURCES))
HOST_CPPFLAGS := -std=gnu11 -E -DMODERN=0 -DPORT_PC -include stdlib.h -iquote include -I. $(SDL2_CFLAGS)
HOST_CFLAGS := -std=gnu11 -fsyntax-only -fmax-errors=5 -x c
ifeq ($(HOST_ARCH),i686)
OBJECT_DIR := ../build/host-objects-i686
LINK_OUTPUT := ../build/host-link-probe-i686.exe
PREPROC_PATH_PREFIX := /mingw64/bin:
else
OBJECT_DIR := ../build/host-objects
LINK_OUTPUT := ../build/host-link-probe.exe
PREPROC_PATH_PREFIX :=
endif
OBJECTS := $(patsubst $(POKEEMERALD)/src/%.c,$(OBJECT_DIR)/%.o,$(SOURCES))
HOST_OBJECT_CFLAGS := -std=gnu11 -fmax-errors=5 -x c -c

.PHONY: syntax objects link-probe check-tools
syntax: $(CHECKS)
objects: $(OBJECTS)

$(CHECKS): | check-tools

check-tools:
	@$(PKG_CONFIG) --exists sdl2 || { echo 'SDL2 development files are required'; exit 1; }
	@$(HOST_CC) -dumpmachine | grep -q '$(HOST_ARCH).*mingw' || { echo 'Use $(HOST_ARCH) GCC from the matching MSYS2 MinGW shell'; exit 1; }
	@test -x $(POKEEMERALD)/tools/preproc/preproc.exe || { echo 'Build pokeemerald tools/preproc first'; exit 1; }
	@test -d $(POKEEMERALD)/build/assets || { echo 'Build pokeemerald assets first'; exit 1; }
	@test -f $(POKEEMERALD)/charmap.txt || { echo 'Missing pokeemerald/charmap.txt'; exit 1; }
	@echo "Checking $(words $(SOURCES)) C files with $(HOST_CC) and SDL2 headers"

check/%: $(POKEEMERALD)/src/%.c
	@echo "CHECK $<"
	@cd $(POKEEMERALD) && { \
		$(HOST_CC) $(HOST_CPPFLAGS) "src/$*.c" | \
		PATH="$(PREPROC_PATH_PREFIX)$$PATH" tools/preproc/preproc.exe -i -g build/assets "src/$*.c" charmap.txt | \
		$(HOST_CC) $(HOST_CFLAGS) -; \
	}

$(OBJECT_DIR)/%.o: $(POKEEMERALD)/src/%.c | check-tools
	@mkdir -p $(OBJECT_DIR)
	@echo "OBJECT $<"
	@cd $(POKEEMERALD) && { \
		$(HOST_CC) $(HOST_CPPFLAGS) "src/$*.c" | \
		PATH="$(PREPROC_PATH_PREFIX)$$PATH" tools/preproc/preproc.exe -i -g build/assets "src/$*.c" charmap.txt | \
		$(HOST_CC) $(HOST_OBJECT_CFLAGS) -o "../build/$(notdir $(OBJECT_DIR))/$*.o" -; \
	}

# Run after `make -k objects`; failed object units are deliberately omitted.
link-probe:
	@$(HOST_CC) -nostartfiles -Wl,-e,AgbMain -o $(LINK_OUTPUT) \
		$(OBJECT_DIR)/*.o $(shell $(PKG_CONFIG) --libs sdl2)
