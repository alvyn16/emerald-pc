#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_ppu.h"

static uint32_t pixels[240 * 160];

int main(void)
{
    assert(VirtualAlloc((void *)0x04000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    uint16_t *pal = VirtualAlloc((void *)0x05000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    uint8_t *vram = VirtualAlloc((void *)0x06000000, 0x18000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    uint16_t *oam = VirtualAlloc((void *)0x07000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(pal && vram && oam);
    for (unsigned i = 0; i < 128; ++i) oam[i * 4] = 0x200;
    pal[0] = 0;
    pal[1] = 0x03e0;
    pal[2] = 0x001f;
    pal[257] = 0x7c00;
    pal[258] = 0x001f;
    memset(vram + 0x4000, 0x11, 32);
    memset(vram + 0x8000, 0x22, 32);
    memset(vram + 0x10000, 0x11, 32);
    memset(vram + 0x10020, 0x22, 32);
    REG_BG0CNT = BGCNT_CHARBASE(1) | 1;
    REG_BG1CNT = BGCNT_CHARBASE(2) | BGCNT_SCREENBASE(1) | 2;
    oam[0] = oam[1] = oam[4] = oam[5] = 0;
    oam[2] = 3 << 10;
    oam[6] = 1; // OBJ1 has higher BG priority but lower OAM priority.
    REG_DISPCNT = DISPCNT_OBJ_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff); // OBJ0 wins before BG comparison.
    REG_DISPCNT |= DISPCNT_BG0_ON | DISPCNT_BG1_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff00ff00); // BG0 hides OBJ0; OBJ1 remains hidden.

    oam[0] = 0x400; // Semitransparent OBJ0.
    oam[2] = 0;
    REG_BLDALPHA = 0x0808;
    REG_BLDCNT = 0x0100; // BG0 second target even with effect mode none.
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff007b7b);
    REG_BLDCNT = 0x0200; // BG1 is third; cannot skip non-target BG0.
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff);
    // Equal BG priority chooses BG0; equal OBJ/BG priority chooses OBJ.
    oam[0] = 0x200;
    oam[4] = 0x200;
    REG_BG0CNT &= ~3;
    REG_BG1CNT &= ~3;
    REG_BLDCNT = 0;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff00ff00);
    oam[0] = 0;
    oam[1] = 0x4000; // Uniform 16x16 OBJ for window overlap fixtures.
    memset(vram + 0x10000, 0x11, 128);
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff);

    REG_WIN0H = (236 << 8) | 4;
    REG_WIN0V = (156 << 8) | 4;
    REG_WIN1H = 8;
    REG_WIN1V = 8;
    REG_WININ = 0x0201; // WIN0 BG0, WIN1 BG1.
    REG_WINOUT = 0x10; // OBJ outside, effects disabled.
    REG_DISPCNT |= DISPCNT_WIN0_ON | DISPCNT_WIN1_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff00ff00 && pixels[4] == 0xffff0000);
    assert(pixels[8] == 0xff0000ff);
    oam[8] = 0x0800; // OBJ2 is a window, not a color layer.
    oam[9] = 6;
    oam[10] = 0;
    REG_WINOUT |= 0x2100; // OBJWIN BG0 and effects.
    REG_DISPCNT |= DISPCNT_OBJWIN_ON;
    REG_BLDCNT = 0x81; // Brighten BG0 in OBJWIN only.
    REG_BLDY = 16;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff00ff00); // WIN0 effects are disabled.
    assert(pixels[6] == 0xffff0000); // WIN1 overrides OBJWIN.
    assert(pixels[10] == 0xffffffff && pixels[14] == 0xff0000ff);
    REG_DISPCNT |= DISPCNT_FORCED_BLANK;
    PortPpu_Render(pixels);
    for (unsigned i = 0; i < 240 * 160; ++i) assert(pixels[i] == 0xffffffff);
    return 0;
}
