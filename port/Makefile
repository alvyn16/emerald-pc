# Diagnostic host build only. This never writes into ../pokeemerald.
# Match upstream's C pipeline: GCC -E | tools/preproc -i | host GCC.
# scaninc only produces dependency files in upstream's Makefile.
SHELL := bash
.SHELLFLAGS := -o pipefail -c

POKEEMERALD := ../pokeemerald
HOST_CC ?= gcc
HOST_ARCH ?= i686
PKG_CONFIG ?= pkg-config

SDL2_CFLAGS := $(shell $(PKG_CONFIG) --cflags sdl2)
SDL2_DLL := $(shell $(PKG_CONFIG) --variable=prefix sdl2)/bin/SDL2.dll
RUNTIME_DLL := ../build/SDL2.dll
SOURCES := $(shell find $(POKEEMERALD)/src -type f -name '*.c' | sort)
CHECKS := $(patsubst $(POKEEMERALD)/src/%.c,check/%,$(SOURCES))
HOST_CPPFLAGS := -std=gnu11 -E -DMODERN=0 -DPORT_PC -include stdlib.h -iquote include -I. -I../port $(SDL2_CFLAGS)
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
DATA_SOURCES := $(sort $(wildcard $(POKEEMERALD)/data/*.s))
DATA_OBJECT_DIR := ../build/host-data-i686
DATA_RAW_OBJECT_DIR := ../build/host-data-i686-raw
DATA_OBJECTS := $(patsubst $(POKEEMERALD)/data/%.s,$(DATA_OBJECT_DIR)/%.o,$(DATA_SOURCES))
DATA_CPPFLAGS := -iquote include -Wno-trigraphs -DMODERN=0 -I tools/agbcc/include -I tools/agbcc -nostdinc -undef -std=gnu89
SONG_SOURCES := $(sort $(wildcard $(POKEEMERALD)/sound/songs/midi/*.s))
SONG_OBJECT_DIR := ../build/host-songs-i686
SONG_RAW_OBJECT_DIR := ../build/host-songs-i686-raw
SONG_INCLUDE_DIR := ../build/host-song-includes
SONG_OBJECTS := $(patsubst $(POKEEMERALD)/sound/songs/midi/%.s,$(SONG_OBJECT_DIR)/%.o,$(SONG_SOURCES))
HOST_EXE_SOURCES := $(filter-out $(addprefix $(POKEEMERALD)/src/,librfu_intr.c m4a.c multiboot.c),$(SOURCES))
HOST_EXE_OBJECTS := $(patsubst $(POKEEMERALD)/src/%.c,$(OBJECT_DIR)/%.o,$(HOST_EXE_SOURCES))
PORT_EXE_SOURCES := main.c gba_memory.c bios.c frame.c speed_menu.c port_timer.c sdl_loader.c audio_silent.c arm_stubs.c host_flash.c port_dma.c port_ppu.c
EXE := ../build/emerald-pc.exe

ifeq ($(DIAGNOSTIC),1)
PORT_EXE_SOURCES += input_script.c
EXE := ../build/emerald-pc-diagnostic.exe
PORT_CPPFLAGS := -DPORT_DIAGNOSTIC -g
endif

.PHONY: syntax objects data-objects song-objects exe diagnostic-exe link-probe check-tools test

# Host-only unit tests. Keep each binary's dependencies explicit so changes
# to a port module rebuild the test that exercises it.
TEST_DIR := ../build/tests
TEST_NAMES := bios dma frame gba_memory host_flash input_script ppu speed_menu timer
TEST_bios_SOURCES := bios.c tests/bios_test.c
TEST_dma_SOURCES := port_dma.c tests/dma_test.c
TEST_frame_SOURCES := frame.c speed_menu.c port_timer.c tests/frame_test.c
TEST_gba_memory_SOURCES := gba_memory.c tests/gba_memory_test.c
TEST_host_flash_SOURCES := host_flash.c tests/host_flash_test.c
TEST_input_script_SOURCES := input_script.c tests/input_script_test.c
TEST_ppu_SOURCES := port_ppu.c tests/ppu_test.c
TEST_speed_menu_SOURCES := speed_menu.c tests/speed_menu_test.c
TEST_timer_SOURCES := port_timer.c tests/timer_test.c
TEST_bios_LIBS := -lm
TEST_gba_memory_LIBS := -lpsapi
TEST_CFLAGS := -std=gnu11 -Wall -Wextra -Werror -DMODERN=0 -DPORT_PC \
	-I. -iquote $(POKEEMERALD)/include $(SDL2_CFLAGS) -Umain \
	-Wl,--image-base=0x10000000 -Wl,--disable-dynamicbase

define BUILD_TEST
$(TEST_DIR)/$(1).exe: $$(TEST_$(1)_SOURCES) Makefile | check-tools
	@mkdir -p $(TEST_DIR)
	@$$(HOST_CC) $$(TEST_CFLAGS) $$(TEST_$(1)_SOURCES) -o $$@ $$(TEST_$(1)_LIBS)
endef
$(foreach name,$(TEST_NAMES),$(eval $(call BUILD_TEST,$(name))))

test: $(addprefix $(TEST_DIR)/,$(addsuffix .exe,$(TEST_NAMES)))
	@set -e; for name in $(TEST_NAMES); do \
		cd .. && build/tests/$$name.exe && cd port && echo "PASS $$name"; \
	done
syntax: $(CHECKS)
objects: $(OBJECTS)
data-objects: $(DATA_OBJECTS)
song-objects: $(SONG_OBJECTS)
exe: $(EXE) $(RUNTIME_DLL)
diagnostic-exe:
	@$(MAKE) DIAGNOSTIC=1 exe

$(RUNTIME_DLL): $(SDL2_DLL) | check-tools
	@cp "$<" "$@"

$(EXE): $(HOST_EXE_OBJECTS) $(DATA_OBJECTS) $(SONG_OBJECTS) $(addprefix ./,$(PORT_EXE_SOURCES)) host_flash.h Makefile
	@find $(OBJECT_DIR) $(DATA_OBJECT_DIR) $(SONG_OBJECT_DIR) -name '*.o' > ../build/host-exe-objects.rsp
	@$(HOST_CC) -std=gnu11 -DMODERN=0 -DPORT_PC $(PORT_CPPFLAGS) -iquote $(POKEEMERALD)/include -I. \
		-Wl,--image-base=0x10000000 -Wl,--disable-dynamicbase \
		-o $(EXE) @../build/host-exe-objects.rsp $(PORT_EXE_SOURCES) \
		$(SDL2_CFLAGS) -lm -lpsapi

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

$(OBJECT_DIR)/agb_flash.o $(OBJECT_DIR)/agb_flash_1m.o: host_flash.h
$(OBJECTS): $(POKEEMERALD)/include/gba/macro.h $(POKEEMERALD)/include/global.h

$(DATA_OBJECT_DIR)/%.o: $(POKEEMERALD)/data/%.s | check-tools
	@mkdir -p $(DATA_OBJECT_DIR) $(DATA_RAW_OBJECT_DIR)
	@echo "DATA $<"
	@cd $(POKEEMERALD) && { \
		PATH="$(PREPROC_PATH_PREFIX)$$PATH" tools/preproc/preproc.exe "data/$*.s" charmap.txt | \
		$(HOST_CC) -E $(DATA_CPPFLAGS) - | \
		PATH="$(PREPROC_PATH_PREFIX)$$PATH" tools/preproc/preproc.exe -ie "data/$*.s" charmap.txt | \
		sed -E -f ../port/asm_compat.sed | \
		$(HOST_CC) -c -x assembler -I. -Wa,--defsym,MODERN=0 -o "../build/host-data-i686-raw/$*.o" -; \
	}
	@objcopy --prefix-symbols=_ $(DATA_RAW_OBJECT_DIR)/$*.o $(DATA_OBJECT_DIR)/$*.o

$(SONG_INCLUDE_DIR)/MPlayDef.s: $(POKEEMERALD)/sound/MPlayDef.s ../port/song_compat.sed
	@mkdir -p $(SONG_INCLUDE_DIR)
	@sed -E -f ../port/song_compat.sed $< > $@

$(SONG_OBJECT_DIR)/%.o: $(POKEEMERALD)/sound/songs/midi/%.s $(SONG_INCLUDE_DIR)/MPlayDef.s ../port/song_compat.sed | check-tools
	@mkdir -p $(SONG_OBJECT_DIR) $(SONG_RAW_OBJECT_DIR)
	@sed -E -f ../port/song_compat.sed $< | $(HOST_CC) -c -x assembler -I$(SONG_INCLUDE_DIR) -o $(SONG_RAW_OBJECT_DIR)/$*.o -
	@objcopy --prefix-symbols=_ $(SONG_RAW_OBJECT_DIR)/$*.o $@

# Run after `make -k objects`; failed object units are deliberately omitted.
link-probe:
	@$(HOST_CC) -nostartfiles -Wl,-e,AgbMain -o $(LINK_OUTPUT) \
		$(OBJECT_DIR)/*.o $(shell $(PKG_CONFIG) --libs sdl2)
