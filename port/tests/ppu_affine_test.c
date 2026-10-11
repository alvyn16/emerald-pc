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
    return 0;
}
