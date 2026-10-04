#include <assert.h>
#include <stdint.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_dma.h"

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);

    uint16_t source16[] = {1, 2, 3, 4};
    uint16_t output16[4] = {0};
    PortDma_Set(3, source16, output16,
                ((DMA_ENABLE | DMA_START_NOW | DMA_16BIT | DMA_SRC_INC | DMA_DEST_INC) << 16) | 4);
    for (int i = 0; i < 4; ++i) assert(output16[i] == source16[i]);
    assert(!(REG_DMA3CNT_H & DMA_ENABLE));

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

    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
