#include <assert.h>
#include <stdint.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_dma.h"
#include "port_irq.h"
void (*gIntrTable[14])(void);

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);
    void *iwram = VirtualAlloc((void *)0x03000000, 32768,
                              MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(iwram == (void *)0x03000000);
    PortIrq_Reset();

    uint16_t source16[] = {1, 2, 3, 4};
    uint16_t output16[4] = {0};
    PortDma_Set(3, source16, output16,
                ((DMA_ENABLE | DMA_START_NOW | DMA_16BIT | DMA_SRC_INC | DMA_DEST_INC) << 16) | 4);
    for (int i = 0; i < 4; ++i) assert(output16[i] == source16[i]);
    assert(!(REG_DMA3CNT_H & DMA_ENABLE));
    assert(REG_DMA3SAD == (uint32_t)(uintptr_t)source16);
    assert(REG_DMA3DAD == (uint32_t)(uintptr_t)output16);

    uint32_t fill = 0x12345678;
    uint32_t output32[3] = {0};
    PortDma_Set(2, &fill, output32,
                ((DMA_ENABLE | DMA_32BIT | DMA_SRC_FIXED | DMA_DEST_INC) << 16) | 3);
    for (int i = 0; i < 3; ++i) assert(output32[i] == fill);

    uint16_t last = 0;
    PortDma_Set(2, source16, &last,
                ((DMA_ENABLE | DMA_SRC_INC | DMA_DEST_FIXED) << 16) | 4);
    assert(last == 4);

    uint16_t reverse[4] = {0};
    PortDma_Set(1, &source16[3], &reverse[3],
                ((DMA_ENABLE | DMA_SRC_DEC | DMA_DEST_DEC) << 16) | 4);
    for (int i = 0; i < 4; ++i) assert(reverse[i] == source16[i]);

    uint16_t untouched = 0;
    PortDma_Set(0, source16, &untouched,
                ((DMA_ENABLE | DMA_START_HBLANK) << 16) | 1);
    assert(untouched == 0);
    assert(REG_DMA0CNT_H & DMA_ENABLE);

    uint16_t scanlineValues[] = {11, 22, 33};
    PortDma_Set(0, scanlineValues, (void *)REG_ADDR_BG0HOFS,
                ((DMA_ENABLE | DMA_START_HBLANK | DMA_REPEAT | DMA_DEST_RELOAD) << 16) | 1);
    for (unsigned i = 0; i < 3; ++i)
    {
        PortDma_OnHBlank();
        assert(REG_BG0HOFS == scanlineValues[i]);
        assert(REG_DMA0CNT_H & DMA_ENABLE);
    }
    REG_DMA0CNT_H &= ~DMA_ENABLE;
    PortDma_OnHBlank();
    assert(REG_BG0HOFS == 33);

    REG_BG1HOFS = 0;
    PortDma_Set(0, scanlineValues, (void *)REG_ADDR_BG1HOFS,
                ((DMA_ENABLE | DMA_START_HBLANK) << 16) | 1);
    PortDma_OnHBlank();
    assert(REG_BG1HOFS == 11);
    assert(!(REG_DMA0CNT_H & DMA_ENABLE));
    PortDma_OnHBlank();
    assert(REG_BG1HOFS == 11);

    REG_BG2HOFS = 0;
    PortDma_Set(3, scanlineValues, (void *)REG_ADDR_BG2HOFS,
                ((DMA_ENABLE | DMA_START_VBLANK) << 16) | 2);
    PortDma_OnHBlank();
    assert(REG_BG2HOFS == 0);
    PortDma_OnVBlank();
    assert(REG_BG2HOFS == 11 && REG_BG2VOFS == 22);

    REG_DMA1CNT_H = DMA_ENABLE | DMA_START_SPECIAL | DMA_REPEAT;
    REG_DMA2CNT_H = DMA_ENABLE | DMA_START_HBLANK;
    PortDma_OnHBlank();
    PortDma_OnVBlank();
    assert(REG_DMA1CNT_H & DMA_ENABLE);
    assert(REG_DMA2CNT_H & DMA_ENABLE);

    for (int channel = 0; channel < 4; ++channel)
    {
        uint16_t output = 0;
        const unsigned count = channel == 3 ? 1 : 0x4001;
        PortDma_Set(channel, source16, &output,
                    ((DMA_ENABLE | DMA_INTR_ENABLE) << 16) | count);
        assert(output == 1);
        assert(PortIrq_Pending() == (INTR_FLAG_DMA0 << channel));
        PortIrq_Acknowledge(INTR_FLAG_DMA0 << channel);
    }

    static uint16_t large[0x10000];
    for (int channel = 0; channel < 4; ++channel)
    {
        large[0x3fff] = large[0xffff] = 0;
        PortDma_Set(channel, &source16[1], large,
                    ((DMA_ENABLE | DMA_SRC_FIXED) << 16));
        assert(large[0x3fff] == 2);
        assert(large[0xffff] == (channel == 3 ? 2 : 0));
    }

    PortDma_Reset();
    uint16_t dest[4] = {0};
    PortDma_Write32(REG_ADDR_DMA0SAD, (uintptr_t)source16);
    PortDma_Write32(REG_ADDR_DMA0DAD, (uintptr_t)dest);
    PortDma_Write32(REG_ADDR_DMA0CNT_L,
                   ((DMA_ENABLE | DMA_START_HBLANK | DMA_REPEAT | DMA_INTR_ENABLE |
                     DMA_DEST_RELOAD) << 16) | 1);
    PortDma_OnHBlank();
    assert(dest[0] == 1 && PortIrq_Pending() == INTR_FLAG_DMA0);
    PortIrq_Acknowledge(INTR_FLAG_DMA0);
    PortDma_Stop(0);
    PortDma_OnHBlank();
    assert(dest[0] == 1 && !PortIrq_Pending());
    // An identical control/count write after disable must latch the source anew.
    PortDma_Write32(REG_ADDR_DMA0CNT_L,
                   ((DMA_ENABLE | DMA_START_HBLANK | DMA_REPEAT | DMA_INTR_ENABLE |
                     DMA_DEST_RELOAD) << 16) | 1);
    PortDma_OnHBlank();
    assert(dest[0] == 1);
    PortDma_OnHBlank();
    assert(dest[0] == 2);
    PortDma_Stop(0);

    // Simultaneous VBlank transfers retain channel priority (DMA0 then DMA3).
    uint16_t a = 7, b = 9, shared = 0;
    PortDma_Set(3, &b, &shared, ((DMA_ENABLE | DMA_START_VBLANK) << 16) | 1);
    PortDma_Set(0, &a, &shared, ((DMA_ENABLE | DMA_START_VBLANK) << 16) | 1);
    PortDma_OnVBlank();
    assert(shared == 9);

    VirtualFree(io, 0, MEM_RELEASE);
    VirtualFree(iwram, 0, MEM_RELEASE);
    return 0;
}
