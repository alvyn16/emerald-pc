#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_ppu.h"

static uint32_t sFrame[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];
static uint32_t sLineFrame[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];

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

    memset(vram, 0, 0x18000);
    for (int i = 0; i < 128; ++i) oam[i * 4] = 0x0200;
    memset(vram + 0x4000, 1, 64);
    memset(vram + 0x4040, 2, 64);
    memset(vram + 0x4080, 3, 64);
    vram[1] = 1;
    vram[15] = 2;
    REG_BG2CNT = BGCNT_CHARBASE(1) | BGCNT_SCREENBASE(0) | BGCNT_AFF128x128;
    REG_BG2PA = 256;
    REG_BG2PB = 0;
    REG_BG2PC = 0;
    REG_BG2PD = 256;
    REG_BG2X = 0;
    REG_BG2Y = 0;
    REG_DISPCNT = DISPCNT_MODE_1 | DISPCNT_BG2_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);

    REG_BG2X = 8 << 8;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff0000ffu);

    vram[0x4000 + 7] = 3;
    REG_BG2PA = 0;
    REG_BG2PB = (uint16_t)-256;
    REG_BG2PC = 256;
    REG_BG2PD = 0;
    PortPpu_Render(sFrame);
    assert(sFrame[PORT_SCREEN_WIDTH] == 0xff00ff00u);
    REG_BG2PA = 256;
    REG_BG2PB = 0;
    REG_BG2PC = 0;
    REG_BG2PD = 256;

    REG_BG2X = (uint32_t)(-8 * 256) & 0x0fffffff;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff000000u);
    REG_BG2CNT |= BGCNT_WRAP;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff00ff00u);

    REG_BG2CNT = BGCNT_CHARBASE(1) | BGCNT_AFF1024x1024 | BGCNT_WRAP;
    vram[127] = 2;
    REG_BG2X = 1023 << 8;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff00ff00u);

    REG_BG2CNT = BGCNT_PRIORITY(1) | BGCNT_CHARBASE(1);
    REG_BG2X = 0;
    REG_BG3CNT = BGCNT_PRIORITY(0) | BGCNT_CHARBASE(2) | BGCNT_SCREENBASE(3);
    memset(vram + 0x8000, 2, 64);
    REG_BG3PA = 256;
    REG_BG3PB = 0;
    REG_BG3PC = 0;
    REG_BG3PD = 256;
    REG_BG3X = 0;
    REG_BG3Y = 0;
    REG_DISPCNT = DISPCNT_MODE_2 | DISPCNT_BG2_ON | DISPCNT_BG3_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff0000ffu);

    REG_DISPCNT = DISPCNT_MODE_0 | DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP;
    memset(vram + 0x10000, 0x11, 32);
    palette[256 + 1] = 0x001f;
    oam[0] = 0x0100 | 10;
    oam[1] = 10;
    oam[2] = 0;
    oam[3] = 256;
    oam[7] = 0;
    oam[11] = 0;
    oam[15] = 256;
    PortPpu_Render(sFrame);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 10] == 0xffff0000u);

    oam[0] |= 0x0200;
    oam[3] = 128;
    oam[15] = 128;
    PortPpu_Render(sFrame);
    assert(sFrame[10 * PORT_SCREEN_WIDTH + 10] == 0xffff0000u);
    assert(sFrame[9 * PORT_SCREEN_WIDTH + 9] == 0xff000000u);

    oam[0] &= ~0x0200;
    memset(vram + 0x10000, 0, 32);
    vram[0x10000 + 2] = 0x01;
    oam[3] = 0;
    oam[7] = (uint16_t)-256;
    oam[11] = 256;
    oam[15] = 0;
    PortPpu_Render(sFrame);
    assert(sFrame[14 * PORT_SCREEN_WIDTH + 10] == 0xffff0000u);

    memset(vram, 0, 0x18000);
    for (int i = 0; i < 128; ++i) oam[i * 4] = 0x0200;
    memset(vram + 0x4000, 0x11, 32);
    memset(vram + 0x8000, 0x22, 32);
    REG_BG0CNT = BGCNT_PRIORITY(1) | BGCNT_CHARBASE(1);
    REG_BG1CNT = BGCNT_PRIORITY(0) | BGCNT_CHARBASE(2) | BGCNT_SCREENBASE(1);
    REG_WIN0H = (10 << 8) | 20;
    REG_WIN0V = (10 << 8) | 20;
    REG_WIN1H = (15 << 8) | 25;
    REG_WIN1V = (10 << 8) | 20;
    REG_WININ = WININ_WIN0_BG0 | WININ_WIN1_BG1;
    REG_WINOUT = 0;
    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_BG1_ON |
                   DISPCNT_WIN0_ON | DISPCNT_WIN1_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 12] == 0xffff0000u);
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 16] == 0xffff0000u); // WIN0 wins overlap.
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 22] == 0xff0000ffu);
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 25] == 0xff000000u);
    assert(sFrame[20 * PORT_SCREEN_WIDTH + 12] == 0xff000000u);
    REG_WINOUT = WINOUT_WIN01_BG1;
    PortPpu_Render(sFrame);
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 30] == 0xff0000ffu);
    assert(sFrame[15 * PORT_SCREEN_WIDTH + 16] == 0xffff0000u);

    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_WIN0_ON;
    REG_WININ = WININ_WIN0_BG0;
    REG_WINOUT = 0;
    REG_WIN0H = (220 << 8) | 20;
    REG_WIN0V = 160;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    assert(sFrame[19] == 0xffff0000u);
    assert(sFrame[20] == 0xff000000u);
    assert(sFrame[100] == 0xff000000u);
    assert(sFrame[220] == 0xffff0000u);
    assert(sFrame[239] == 0xffff0000u);

    REG_WIN0H = 240;
    REG_WIN0V = (150 << 8) | 10;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    assert(sFrame[9 * PORT_SCREEN_WIDTH] == 0xffff0000u);
    assert(sFrame[10 * PORT_SCREEN_WIDTH] == 0xff000000u);
    assert(sFrame[150 * PORT_SCREEN_WIDTH] == 0xffff0000u);

    REG_WIN0H = (10 << 8) | 10;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff000000u); // Equal bounds make an empty window.
    REG_DISPCNT = DISPCNT_BG0_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u); // Disabled windows do not mask layers.

    memset(vram + 0x10000, 0x11, 32);
    palette[257] = 0x03e0;
    oam[0] = 5;
    oam[1] = 5;
    oam[2] = 0;
    REG_WIN0H = 10;
    REG_WIN0V = 10;
    REG_WININ = WININ_WIN0_OBJ;
    REG_WINOUT = 0;
    REG_DISPCNT = DISPCNT_OBJ_ON | DISPCNT_WIN0_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff00ff00u);
    REG_WININ = WININ_WIN0_BG0;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff000000u);
    REG_WIN0H = (20 << 8) | 30;
    REG_WINOUT = WINOUT_WIN01_OBJ;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff00ff00u);

    memset(vram + 0x4000, 3, 64);
    REG_BG2CNT = BGCNT_CHARBASE(1);
    REG_BG2PA = REG_BG2PD = 256;
    REG_BG2PB = REG_BG2PC = 0;
    REG_BG2X = REG_BG2Y = 0;
    REG_WIN0H = 10;
    REG_WININ = WININ_WIN0_BG2;
    REG_WINOUT = 0;
    REG_DISPCNT = DISPCNT_MODE_1 | DISPCNT_BG2_ON | DISPCNT_WIN0_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff00ff00u);
    assert(sFrame[20 * PORT_SCREEN_WIDTH + 20] == 0xff000000u);

    memset(io, 0, 0x1000);
    memset(vram, 0, 0x18000);
    for (int i = 0; i < 128; ++i) oam[i * 4] = 0x0200;
    palette[0] = 0;
    palette[1] = 0x001f;
    palette[2] = 0x7c00;
    palette[257] = 0x03e0;
    memset(vram + 0x4000, 0x11, 32);
    memset(vram + 0x8000, 0x22, 32);
    memset(vram + 0x10000, 0x11, 32);
    REG_BG0CNT = BGCNT_PRIORITY(0) | BGCNT_CHARBASE(1);
    REG_BG1CNT = BGCNT_PRIORITY(1) | BGCNT_CHARBASE(2) | BGCNT_SCREENBASE(1);
    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_BG1_ON;
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BG1;
    REG_BLDALPHA = BLDALPHA_BLEND(8, 8);
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff7b007bu); // Red and blue at half intensity.
    REG_BLDALPHA = BLDALPHA_BLEND(16, 0);
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    REG_BLDALPHA = BLDALPHA_BLEND(0, 16);
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff0000ffu);
    REG_BLDALPHA = BLDALPHA_BLEND(31, 31);
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff00ffu); // Coefficients clamp to 16.
    palette[2] = 0x001f;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u); // Channel sum saturates at 31.
    palette[2] = 0x7c00;

    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_LIGHTEN;
    REG_BLDY = 0;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    REG_BLDY = 8;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff7b7bu);
    REG_BLDY = 16;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffffffffu);
    REG_BLDY = 31;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffffffffu); // BLDY clamps to 16.
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_DARKEN;
    REG_BLDY = 0;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    REG_BLDY = 8;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff840000u);
    REG_BLDY = 16;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff000000u);
    REG_BLDY = 31;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff000000u);

    REG_DISPCNT = DISPCNT_BG0_ON;
    palette[0] = 0x7c00;
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BD;
    REG_BLDALPHA = BLDALPHA_BLEND(8, 8);
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff7b007bu); // Backdrop is the second layer.
    REG_DISPCNT = 0;
    REG_BLDCNT = BLDCNT_TGT1_BD | BLDCNT_EFFECT_LIGHTEN;
    REG_BLDY = 16;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffffffffu); // Backdrop can be first target.
    palette[0] = 0;

    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_BG1_ON | DISPCNT_WIN0_ON;
    REG_WIN0H = 8;
    REG_WIN0V = 8;
    REG_WININ = WININ_WIN0_BG0 | WININ_WIN0_BG1 | WININ_WIN0_CLR;
    REG_WINOUT = WINOUT_WIN01_BG0 | WINOUT_WIN01_BG1;
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BG1;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff7b007bu);
    assert(sFrame[10] == 0xffff0000u); // Outside: effects disabled.
    REG_WININ &= ~WININ_WIN0_CLR;
    REG_WINOUT |= WINOUT_WIN01_CLR;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u);
    assert(sFrame[10] == 0xff7b007bu);

    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_OBJ_ON;
    REG_BLDCNT = BLDCNT_TGT2_BG0; // No global alpha or OBJ first-target bit.
    oam[0] = 0x0400 | 5; // OAM mode 1: semi-transparent OBJ.
    oam[1] = 5;
    oam[2] = 0;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff7b7b00u);
    REG_DISPCNT |= DISPCNT_WIN0_ON;
    REG_WININ = WININ_WIN0_BG0 | WININ_WIN0_OBJ;
    REG_WINOUT = WINOUT_WIN01_BG0 | WINOUT_WIN01_OBJ | WINOUT_WIN01_CLR;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff00ff00u);
    REG_WININ |= WININ_WIN0_CLR;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff7b7b00u);

    oam[0] = 5; // Ordinary OBJ selected as first target.
    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_OBJ_ON;
    REG_BLDCNT = BLDCNT_TGT1_OBJ | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BG0;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff7b7b00u);
    oam[2] = 1 << 10; // OBJ behind BG0, selected as second target.
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_OBJ;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff7b7b00u);

    oam[0] = 0x0200;
    memset(vram + 0xc000, 0x33, 32);
    REG_BG2CNT = BGCNT_PRIORITY(2) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(2);
    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_BG2_ON;
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BG2;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff7b7b00u); // BG2 can be second target.
    REG_DISPCNT |= DISPCNT_BG1_ON;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xffff0000u); // Visible BG1 blocks the selected BG2.
    REG_BG3CNT = BGCNT_CHARBASE(1);
    REG_DISPCNT = DISPCNT_BG3_ON;
    REG_BLDCNT = BLDCNT_TGT1_BG3 | BLDCNT_EFFECT_DARKEN;
    REG_BLDY = 16;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff000000u); // BG3 can be first target.

    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_BG1_ON | DISPCNT_WIN1_ON;
    REG_WIN1H = 8;
    REG_WIN1V = 8;
    REG_WININ = WININ_WIN1_BG0 | WININ_WIN1_BG1 | WININ_WIN1_CLR;
    REG_WINOUT = WINOUT_WIN01_BG0 | WINOUT_WIN01_BG1;
    REG_BLDCNT = BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_BLEND | BLDCNT_TGT2_BG1;
    PortPpu_Render(sFrame);
    assert(sFrame[0] == 0xff7b007bu);
    assert(sFrame[10] == 0xffff0000u); // WIN1 effect bit is independent.

    REG_DISPCNT = DISPCNT_BG0_ON | DISPCNT_OBJ_ON;
    REG_BLDCNT = BLDCNT_TGT2_BG0 | BLDCNT_TGT2_OBJ;
    oam[0] = 0x0400 | 5;
    oam[1] = 5;
    oam[2] = 0;
    oam[4] = 5;
    oam[5] = 5;
    oam[6] = 1;
    memset(vram + 0x10020, 0x22, 32);
    palette[258] = 0x7c00;
    PortPpu_Render(sFrame);
    assert(sFrame[5 * PORT_SCREEN_WIDTH + 5] == 0xff7b7b00u);
    // The lower OBJ is hidden before blending; BG0 is the second layer.

    PortPpu_Render(sFrame);
    PortPpu_BeginFrame();
    for (unsigned y = 0; y < PORT_SCREEN_HEIGHT; ++y)
        PortPpu_RenderLine(y, sLineFrame + y * PORT_SCREEN_WIDTH);
    assert(memcmp(sFrame, sLineFrame, sizeof(sFrame)) == 0);

    memset(vram, 0, 0x18000);
    memset(io, 0, 0x1000);
    for (unsigned row = 0; row < 8; ++row)
        vram[0x4000 + row * 4] = 0x21;
    palette[1] = 0x001f;
    palette[2] = 0x7c00;
    REG_BG0CNT = BGCNT_CHARBASE(1);
    REG_DISPCNT = DISPCNT_BG0_ON;
    PortPpu_BeginFrame();
    REG_BG0HOFS = 0;
    PortPpu_RenderLine(0, sLineFrame);
    REG_BG0HOFS = 1;
    PortPpu_RenderLine(1, sLineFrame + PORT_SCREEN_WIDTH);
    assert(sLineFrame[0] == 0xffff0000u);
    assert(sLineFrame[PORT_SCREEN_WIDTH] == 0xff0000ffu);

    memset(vram, 0, 0x18000);
    memset(vram + 0x4000, 1, 64);
    memset(vram + 0x4040, 2, 64);
    for (unsigned mapRow = 0; mapRow < 16; ++mapRow)
        vram[mapRow * 16 + 1] = 1;
    REG_BG2CNT = BGCNT_CHARBASE(1);
    REG_BG2PA = REG_BG2PD = 256;
    REG_BG2PB = REG_BG2PC = 0;
    REG_BG2X = REG_BG2Y = 0;
    REG_DISPCNT = DISPCNT_MODE_1 | DISPCNT_BG2_ON;
    PortPpu_BeginFrame();
    for (unsigned y = 0; y < 80; ++y)
        PortPpu_RenderLine(y, sLineFrame + y * PORT_SCREEN_WIDTH);
    REG_BG2X = 8 << 8;
    PortPpu_RenderLine(80, sLineFrame + 80 * PORT_SCREEN_WIDTH);
    assert(sLineFrame[80 * PORT_SCREEN_WIDTH] == 0xff0000ffu);

    VirtualFree(oam, 0, MEM_RELEASE);
    VirtualFree(vram, 0, MEM_RELEASE);
    VirtualFree(palette, 0, MEM_RELEASE);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
