#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "gba/io_reg.h"
#include "port_dma.h"

void PortDma_Set(int channel, const void *source, void *destination, unsigned control)
{
    if (channel < 0 || channel > 3)
        return;

    volatile uint32_t *registers = (volatile uint32_t *)(uintptr_t)(REG_ADDR_DMA0 + channel * 12);
    registers[0] = (uint32_t)(uintptr_t)source;
    registers[1] = (uint32_t)(uintptr_t)destination;
    registers[2] = control;

    const unsigned flags = control >> 16;
    if (!(flags & DMA_ENABLE) || (flags & DMA_START_MASK) != DMA_START_NOW)
        return;

    unsigned count = control & 0xffff;
    if (count == 0)
        count = channel == 3 ? 0x10000 : 0x4000;
    const unsigned width = flags & DMA_32BIT ? 4 : 2;
    const unsigned sourceMode = (flags >> 7) & 3;
    const unsigned destinationMode = (flags >> 5) & 3;
    if (sourceMode == 3 || source == NULL || destination == NULL)
    {
        fprintf(stderr, "PC: invalid immediate DMA%d request\n", channel);
        return;
    }

    const uint8_t *from = source;
    uint8_t *to = destination;
    for (unsigned i = 0; i < count; i++)
    {
        uint32_t value = 0;
        memcpy(&value, from, width);
        memcpy(to, &value, width);
        if (sourceMode == 0) from += width;
        else if (sourceMode == 1) from -= width;
        if (destinationMode == 0 || destinationMode == 3) to += width;
        else if (destinationMode == 1) to -= width;
    }

    registers[0] = (uint32_t)(uintptr_t)from;
    registers[1] = (uint32_t)(uintptr_t)to;
    registers[2] = control & ~(DMA_ENABLE << 16);
}
