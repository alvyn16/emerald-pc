#include <stdint.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_ppu.h"

#define VRAM ((const uint8_t *)0x06000000u)
#define PALETTE ((const uint16_t *)0x05000000u)
#define OAM ((const uint16_t *)0x07000000u)

static uint16_t ReadVram16(unsigned offset)
{
    if (offset + 1 >= 0x18000)
        return 0;
    return (uint16_t)(VRAM[offset] | (VRAM[offset + 1] << 8));
}

static uint32_t ExpandColor(uint16_t color)
{
    unsigned red = color & 31;
    unsigned green = (color >> 5) & 31;
    unsigned blue = (color >> 10) & 31;
    return 0xff000000u | ((red << 3 | red >> 2) << 16)
           | ((green << 3 | green >> 2) << 8) | (blue << 3 | blue >> 2);
}

static void RenderBackground(uint32_t *pixels, unsigned bg)
{
    const uint16_t control = ((const volatile uint16_t *)REG_ADDR_BG0CNT)[bg];
    const uint16_t *scroll = (const uint16_t *)(uintptr_t)REG_ADDR_BG0HOFS;
    const unsigned width = (control & 0x4000) ? 512 : 256;
    const unsigned height = (control & 0x8000) ? 512 : 256;
    const unsigned blocksWide = width / 256;
    const unsigned charBase = ((control >> 2) & 3) * 0x4000;
    const unsigned screenBase = ((control >> 8) & 31) * 0x800;
    const unsigned bpp8 = (control & 0x80) != 0;
    const unsigned hscroll = scroll[bg * 2] & 0x1ff;
    const unsigned vscroll = scroll[bg * 2 + 1] & 0x1ff;

    for (unsigned y = 0; y < PORT_SCREEN_HEIGHT; ++y)
    {
        const unsigned mapY = (y + vscroll) & (height - 1);
        const unsigned tileY = mapY >> 3;
        for (unsigned x = 0; x < PORT_SCREEN_WIDTH; ++x)
        {
            const unsigned mapX = (x + hscroll) & (width - 1);
            const unsigned tileX = mapX >> 3;
            const unsigned block = (tileY >> 5) * blocksWide + (tileX >> 5);
            const unsigned mapOffset = screenBase + block * 0x800
                    + (((tileY & 31) * 32 + (tileX & 31)) * 2);
            const uint16_t entry = ReadVram16(mapOffset);
            unsigned pixelX = mapX & 7;
            unsigned pixelY = mapY & 7;
            if (entry & 0x0400) pixelX = 7 - pixelX;
            if (entry & 0x0800) pixelY = 7 - pixelY;
            const unsigned tileOffset = charBase + (entry & 0x03ff) * (bpp8 ? 64 : 32)
                    + pixelY * (bpp8 ? 8 : 4) + (bpp8 ? pixelX : pixelX / 2);
            if (tileOffset >= 0x10000)
                continue;
            const uint8_t data = VRAM[tileOffset];
            const unsigned index = bpp8 ? data : ((data >> ((pixelX & 1) * 4)) & 15);
            if (index != 0)
            {
                const unsigned paletteIndex = bpp8 ? index : ((entry >> 12) * 16 + index);
                pixels[y * PORT_SCREEN_WIDTH + x] = ExpandColor(PALETTE[paletteIndex]);
            }
        }
    }
}

static void SpriteDimensions(unsigned shape, unsigned size, unsigned *width, unsigned *height)
{
    static const uint8_t widths[3][4] = {
        {8, 16, 32, 64}, {16, 32, 32, 64}, {8, 8, 16, 32}
    };
    static const uint8_t heights[3][4] = {
        {8, 16, 32, 64}, {8, 8, 16, 32}, {16, 32, 32, 64}
    };
    *width = widths[shape][size];
    *height = heights[shape][size];
}

static void RenderSprites(uint32_t *pixels, unsigned priority, uint16_t displayControl)
{
    const unsigned oneDimensional = (displayControl & DISPCNT_OBJ_1D_MAP) != 0;
    for (int sprite = 127; sprite >= 0; --sprite)
    {
        const uint16_t attr0 = OAM[sprite * 4];
        const uint16_t attr1 = OAM[sprite * 4 + 1];
        const uint16_t attr2 = OAM[sprite * 4 + 2];
        const unsigned shape = (attr0 >> 14) & 3;
        if ((attr0 & 0x0100) || (attr0 & 0x0200) || shape == 3 ||
            ((attr0 >> 10) & 3) == 2 || ((attr2 >> 10) & 3) != priority)
            continue;

        unsigned width, height;
        SpriteDimensions(shape, (attr1 >> 14) & 3, &width, &height);
        int originX = attr1 & 0x1ff;
        int originY = attr0 & 0xff;
        if (originX >= 256) originX -= 512;
        if (originY >= 160) originY -= 256;
        const unsigned bpp8 = (attr0 & 0x2000) != 0;
        const unsigned tileStep = bpp8 ? 2 : 1;
        const unsigned tileBase = (attr2 & 0x3ff) & (bpp8 ? ~1u : ~0u);
        const unsigned rowStride = oneDimensional ? (width / 8) * tileStep : 32;

        for (unsigned sy = 0; sy < height; ++sy)
        {
            const int screenY = originY + (int)sy;
            if (screenY < 0 || screenY >= PORT_SCREEN_HEIGHT) continue;
            const unsigned tileY = (attr1 & 0x2000) ? height - 1 - sy : sy;
            for (unsigned sx = 0; sx < width; ++sx)
            {
                const int screenX = originX + (int)sx;
                if (screenX < 0 || screenX >= PORT_SCREEN_WIDTH) continue;
                const unsigned tileX = (attr1 & 0x1000) ? width - 1 - sx : sx;
                const unsigned tileNumber = tileBase + (tileY / 8) * rowStride
                        + (tileX / 8) * tileStep;
                const unsigned offset = 0x10000 + tileNumber * 32
                        + (tileY & 7) * (bpp8 ? 8 : 4)
                        + (bpp8 ? (tileX & 7) : ((tileX & 7) / 2));
                if (offset >= 0x18000) continue;
                const uint8_t data = VRAM[offset];
                const unsigned index = bpp8 ? data : ((data >> ((tileX & 1) * 4)) & 15);
                if (index != 0)
                {
                    const unsigned paletteIndex = bpp8 ? index : ((attr2 >> 12) * 16 + index);
                    pixels[screenY * PORT_SCREEN_WIDTH + screenX] =
                            ExpandColor(PALETTE[256 + paletteIndex]);
                }
            }
        }
    }
}

void PortPpu_Render(uint32_t *pixels)
{
    const uint16_t displayControl = REG_DISPCNT;
    const uint32_t backdrop = (displayControl & DISPCNT_FORCED_BLANK)
            ? 0xffffffffu : ExpandColor(PALETTE[0]);
    for (unsigned i = 0; i < PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT; ++i)
        pixels[i] = backdrop;

    if ((displayControl & 7) != DISPCNT_MODE_0 ||
        (displayControl & DISPCNT_FORCED_BLANK))
        return;

    for (int priority = 3; priority >= 0; --priority)
    {
        for (int bg = 3; bg >= 0; --bg)
        {
            if ((displayControl & (DISPCNT_BG0_ON << bg)) &&
                ((((volatile uint16_t *)REG_ADDR_BG0CNT)[bg] & 3) == priority))
                RenderBackground(pixels, bg);
        }
        if (displayControl & DISPCNT_OBJ_ON)
            RenderSprites(pixels, priority, displayControl);
    }
}
