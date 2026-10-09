#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "gba/io_reg.h"
#include "port_dma.h"

struct DmaState
{
    const uint8_t *source;
    uint8_t *destination;
    uint8_t *initialDestination;
    unsigned count;
    unsigned flags;
    int armed;
};

static struct DmaState sChannels[4];

static void Transfer(int channel, struct DmaState *dma)
{
    const unsigned width = dma->flags & DMA_32BIT ? 4 : 2;
    const unsigned sourceMode = (dma->flags >> 7) & 3;
    const unsigned destinationMode = (dma->flags >> 5) & 3;
    if (sourceMode == 3 || dma->source == NULL || dma->destination == NULL)
    {
        fprintf(stderr, "PC: invalid DMA%d request\n", channel);
        dma->armed = 0;
        return;
    }

    const uint8_t *from = dma->source;
    uint8_t *to = dma->destination;
    for (unsigned i = 0; i < dma->count; i++)
    {
        uint32_t value = 0;
        memcpy(&value, from, width);
        memcpy(to, &value, width);
        if (sourceMode == 0) from += width;
        else if (sourceMode == 1) from -= width;
        if (destinationMode == 0 || destinationMode == 3) to += width;
        else if (destinationMode == 1) to -= width;
    }
    dma->source = from;
    dma->destination = to;
    volatile uint32_t *registers = (volatile uint32_t *)(uintptr_t)(REG_ADDR_DMA0 + channel * 12);
    registers[0] = (uint32_t)(uintptr_t)from;
    registers[1] = (uint32_t)(uintptr_t)to;
    if (!(dma->flags & DMA_REPEAT) || (dma->flags & DMA_START_MASK) == DMA_START_NOW)
    {
        registers[2] &= ~(DMA_ENABLE << 16);
        dma->armed = 0;
    }
    else if (destinationMode == 3)
        dma->destination = dma->initialDestination;
}

void PortDma_Set(int channel, const void *source, void *destination, unsigned control)
{
    if (channel < 0 || channel > 3)
        return;

    volatile uint32_t *registers = (volatile uint32_t *)(uintptr_t)(REG_ADDR_DMA0 + channel * 12);
    struct DmaState *dma = &sChannels[channel];
    dma->armed = 0;
    registers[0] = (uint32_t)(uintptr_t)source;
    registers[1] = (uint32_t)(uintptr_t)destination;
    registers[2] = control;

    const unsigned flags = control >> 16;
    if (!(flags & DMA_ENABLE))
        return;

    unsigned count = control & 0xffff;
    if (count == 0)
        count = channel == 3 ? 0x10000 : 0x4000;
    *dma = (struct DmaState){source, destination, destination, count, flags, 1};
    if ((flags & DMA_START_MASK) == DMA_START_NOW)
        Transfer(channel, dma);
}

static void OnEvent(unsigned start)
{
    for (int channel = 0; channel < 4; ++channel)
    {
        struct DmaState *dma = &sChannels[channel];
        volatile uint16_t *control = (volatile uint16_t *)(uintptr_t)
                (REG_ADDR_DMA0CNT_H + channel * 12);
        if (dma->armed && (*control & DMA_ENABLE) &&
            (dma->flags & DMA_START_MASK) == start)
            Transfer(channel, dma);
        else if (!(*control & DMA_ENABLE))
            dma->armed = 0;
    }
}

void PortDma_OnHBlank(void) { OnEvent(DMA_START_HBLANK); }
void PortDma_OnVBlank(void) { OnEvent(DMA_START_VBLANK); }
