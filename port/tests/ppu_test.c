#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_ppu.h"

static uint32_t sFrame[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];

static void *Map(uintptr_t address, size_t size)
{
    void *region = VirtualAlloc((void *)address, size,
                                MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(region == (void *)address);
    return region;
}

int main(void)
{
    void *io = Map(0x04000000u, 0x1000);
    uint16_t *palette = Map(0x05000000u, 0x1000);
    uint8_t *vram = Map(0x06000000u, 0x18000);
    uint16_t *oam = Map(0x07000000u, 0x1000);
    for (int i = 0; i < 128; ++i) oam[i * 4] = 0x0200;

    palette[0] = 0;
    palette[1] = 0x001f;
    palette[2] = 0x7c00;
    palette[3] = 0x03e0;
    memset(vram + 0x4000, 0x11, 32);
    REG_BG0CNT = BGCNT_CHARBASE(1) | BGCNT_SCREENBASE(0);
    REG_DISPCNT = DISPCNT_BG0_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);

    memset(vram + 0x4000, 0, 32);
    memset(vram + 0x8000, 2, 64);
    REG_BG1CNT = BGCNT_PRIORITY(1) | BGCNT_CHARBASE(2) |
                 BGCNT_SCREENBASE(1) | BGCNT_256COLOR;
    REG_DISPCNT |= DISPCNT_BG1_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff0000ffu);

    REG_DISPCNT = DISPCNT_BG0_ON;
    REG_BG0CNT = BGCNT_CHARBASE(1) | BGCNT_SCREENBASE(4) | BGCNT_TXT512x512;
    memset(vram + 0x4020, 0x33, 32);
    *(uint16_t *)(vram + 0x2000 + 3 * 0x800) = 1;
    REG_BG0HOFS = 256;
    REG_BG0VOFS = 256;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff00ff00u);

    REG_BG0HOFS = 0;
    REG_BG0VOFS = 0;
    REG_BG0CNT = BGCNT_CHARBASE(1) | BGCNT_SCREENBASE(0);
    memset(vram + 0x4000, 0x33, 32);
    memset(vram + 0x10000, 0x11, 32);
    palette[256 + 1] = 0x7c00;
    oam[0] = 10;
    oam[1] = 10;
    oam[2] = 0;
    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP;
    PortPpu_Render(sFrame);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 10] == 0xff0000ffu);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 20] == 0xff00ff00u);

    oam[2] = 3 << 10;
    PortPpu_Render(sFrame);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 10] == 0xff00ff00u);

    oam[0] = 10 | 0x2000;
    oam[2] = 0;
    memset(vram + 0x10000, 2, 64);
    palette[256 + 2] = 0x001f;
    PortPpu_Render(sFrame);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 10] == 0xffff0000u);

    VirtualFree(oam, 0, MEM_RELEASE);
    VirtualFree(vram, 0, MEM_RELEASE);
    VirtualFree(palette, 0, MEM_RELEASE);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
