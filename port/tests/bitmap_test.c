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
    uint16_t *vram = VirtualAlloc((void *)0x06000000, 0x18000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    uint16_t *oam = VirtualAlloc((void *)0x07000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(pal && vram && oam);
    for (unsigned i = 0; i < 128; ++i) oam[i * 4] = 0x200;
    pal[0] = 0x03e0;
    pal[1] = 0x001f;
    pal[2] = pal[257] = 0x7c00;
    REG_BG2PA = REG_BG2PD = 256;
    REG_DISPCNT = DISPCNT_MODE_3 | DISPCNT_BG2_ON;
    vram[0] = 0x001f;
    vram[240 * 160 - 1] = 0x7c00;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xffff0000 && pixels[1] == 0xff000000);
    assert(pixels[240 * 160 - 1] == 0xff0000ff);
    REG_DISPCNT |= 0x10; // Mode 3 ignores page selection.
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xffff0000);

    memset(vram, 0, 0x18000);
    ((uint8_t *)vram)[0] = 1;
    ((uint8_t *)vram)[0xa000] = 2;
    ((uint8_t *)vram)[0xa000 + 240 * 160 - 1] = 1;
    REG_DISPCNT = DISPCNT_MODE_4 | DISPCNT_BG2_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xffff0000 && pixels[1] == 0xff00ff00);
    REG_DISPCNT |= 0x10;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff && pixels[240 * 160 - 1] == 0xffff0000);
    REG_BG2X = (uint32_t)-256;
    REG_BG2CNT = BGCNT_WRAP; // Ignored by bitmap: outside remains backdrop.
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff00ff00 && pixels[1] == 0xff0000ff);

    REG_BG2X = 0;
    REG_BG2CNT = 1;
    memset((uint8_t *)vram + 0x14000, 0x11, 32);
    oam[0] = 0;
    oam[1] = 0;
    oam[2] = 512 | (2 << 10); // Behind BG2, above backdrop.
    REG_DISPCNT = DISPCNT_MODE_4 | DISPCNT_BG2_ON | DISPCNT_OBJ_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xffff0000 && pixels[1] == 0xff0000ff);
    oam[2] = 2 << 10; // Forbidden bitmap OBJ tile, even if its bytes exist.
    PortPpu_Render(pixels);
    assert(pixels[1] == 0xff00ff00);
    oam[2] = 512 | (2 << 10);
    REG_DISPCNT = DISPCNT_MODE_3 | DISPCNT_BG2_ON | DISPCNT_OBJ_ON;
    vram[0] = 0x001f;
    vram[1] = 0;
    PortPpu_Render(pixels);
    assert(pixels[1] == 0xff000000); // Direct color zero is opaque.
    REG_WIN0H = 4;
    REG_WIN0V = 8;
    REG_WININ = 0x10; // OBJ only in window.
    REG_WINOUT = 0x24; // BG2 and effects outside.
    REG_DISPCNT |= DISPCNT_WIN0_ON;
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff && pixels[4] == 0xff000000);
    REG_BLDCNT = 0x2044; // BG2 first, backdrop second, alpha.
    REG_BLDALPHA = 0x0808;
    PortPpu_Render(pixels);
    assert(pixels[4] == 0xff007b00); // Black + green, fixed-point truncation.
    return 0;
}
