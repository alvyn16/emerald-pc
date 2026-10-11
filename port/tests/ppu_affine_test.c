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
    pal[257] = pal[1] = 0x001f;
    pal[258] = pal[2] = 0x7c00;
    for (unsigned y = 0; y < 8; ++y)
        for (unsigned x = 0; x < 8; ++x)
            vram[0x10000 + y * 8 + x] = 1 + ((x + y) & 1);
    oam[0] = 0x3003; // 8bpp mosaic, origin (3,3).
    oam[1] = 3;
    oam[2] = 0;
    REG_DISPCNT = DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP;
    REG_MOSAIC = 0x3300;
    PortPpu_Render(pixels);
    assert(pixels[3 * 240 + 3] == 0xffff0000);
    assert(pixels[3 * 240 + 4] == 0xff0000ff);
    assert(pixels[4 * 240 + 4] == 0xffff0000);
    assert(pixels[3 * 240 + 11] == 0xff0000ff); // Horizontal trailing group.
    oam[0] = 0x3000;
    oam[1] = 509; // x=-3: screen mosaic phase must survive clipping.
    PortPpu_Render(pixels);
    assert(pixels[0] == 0xff0000ff);

    oam[0] = 0x3003;
    oam[1] = 3 | 0x1000; // Flip after applying the screen mosaic phase.
    PortPpu_Render(pixels);
    assert(pixels[3 * 240 + 3] == 0xff0000ff);
    assert(pixels[3 * 240 + 4] == 0xffff0000);
    REG_MOSAIC = 0;
    oam[0] = 0x2100; // Affine 8bpp, negative horizontal scale.
    oam[1] = 20;
    oam[3] = (uint16_t)-256;
    oam[7] = oam[11] = 0;
    oam[15] = 256;
    PortPpu_Render(pixels);
    assert(pixels[20] == 0xff000000 && pixels[21] == 0xff0000ff);
    assert(pixels[22] == 0xffff0000);
    oam[0] |= 0x0200; // Double-size box retains its centre at x=28.
    PortPpu_Render(pixels);
    assert(pixels[4 * 240 + 24] == 0xff000000 && pixels[4 * 240 + 25] == 0xff0000ff);
    assert(pixels[4 * 240 + 28] == 0xffff0000);

    REG_MOSAIC = 0;
    memset(vram + 0x10000, 0x11, 4096);
    oam[0] = 129 | 0x0300; // 64x64 affine, double box wraps vertically.
    oam[1] = 0xc000;
    oam[3] = 256;
    oam[7] = oam[11] = oam[15] = 0;
    PortPpu_Render(pixels);
    assert(pixels[32] == 0xffff0000 && pixels[129 * 240 + 32] == 0xff000000);

    oam[0] = 0x200;
    memset(vram, 0, 0x10000);
    memset(vram + 0x4000, 1, 64);
    memset(vram + 0x4040, 2, 64);
    vram[1] = 1;
    REG_BG2CNT = BGCNT_CHARBASE(1);
    REG_BG2PA = REG_BG2PB = 256;
    REG_BG2PC = REG_BG2PD = 0;
    REG_BG2X = REG_BG2Y = 0;
    REG_DISPCNT = DISPCNT_MODE_1 | DISPCNT_BG2_ON;
    PortPpu_BeginFrame();
    for (unsigned y = 0; y < 9; ++y) PortPpu_RenderLine(y, pixels + 240 * y);
    assert(pixels[8 * 240] == 0xff0000ff);
    REG_BG2X = 0; // Identical external register, different internal reference.
    PortPpu_NotifyWrite(REG_ADDR_BG2X, 4);
    PortPpu_RenderLine(9, pixels + 240 * 9);
    assert(pixels[9 * 240] == 0xffff0000);
    REG_BG2PA = -256;
    REG_BG2X = 8 << 8;
    PortPpu_NotifyWrite(REG_ADDR_BG2X, 4);
    PortPpu_RenderLine(10, pixels + 240 * 10);
    assert(pixels[10 * 240] == 0xff0000ff && pixels[10 * 240 + 1] == 0xffff0000);
    REG_BG2CNT |= BGCNT_WRAP;
    REG_BG2X = (uint32_t)-256;
    PortPpu_NotifyWrite(REG_ADDR_BG2X, 4);
    PortPpu_RenderLine(11, pixels + 240 * 11);
    assert(pixels[11 * 240] == 0xffff0000); // Tile map wraps to x=127.
    return 0;
}
