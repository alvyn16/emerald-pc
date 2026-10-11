#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "gba/io_reg.h"
#include "port_dma.h"
#include "port_irq.h"

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

static unsigned TransferCount(int channel, unsigned count)
{
    count &= channel == 3 ? 0xffff : 0x3fff;
    return count ? count : (channel == 3 ? 0x10000 : 0x4000);
}

static void Transfer(int channel, struct DmaState *dma)
{
    const unsigned width = dma->flags & DMA_32BIT ? 4 : 2;
    const unsigned sourceMode = (dma->flags >> 7) & 3;
    const unsigned destinationMode = (dma->flags >> 5) & 3;
    if (sourceMode == 3 || dma->source == NULL || dma->destination == NULL)
    {
        fprintf(stderr, "PC: invalid DMA%d request\n", channel);
        dma->armed = 0;
        *(volatile uint16_t *)(uintptr_t)(REG_ADDR_DMA0CNT_H + channel * 12) &= ~DMA_ENABLE;
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
    // Programmed SAD/DAD are not the advancing internal DMA pointers.
    if (!(dma->flags & DMA_REPEAT) || (dma->flags & DMA_START_MASK) == DMA_START_NOW)
    {
        registers[2] &= ~(DMA_ENABLE << 16);
        dma->armed = 0;
    }
    else if (destinationMode == 3)
        dma->destination = (uint8_t *)(uintptr_t)(registers[1] & ~(width - 1));
    if (dma->armed)
        dma->count = TransferCount(channel, registers[2]);
    if (dma->flags & DMA_INTR_ENABLE)
        PortIrq_Raise(INTR_FLAG_DMA0 << channel);
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

    const unsigned flags = (control >> 16) & (channel == 3 ? 0xffe0 : 0xf7e0);
    registers[2] = (flags << 16) | (control & (channel == 3 ? 0xffff : 0x3fff));
    if (!(flags & DMA_ENABLE))
        return;

    unsigned count = TransferCount(channel, control);
    const unsigned alignmentMask = (flags & DMA_32BIT) ? 3 : 1;
    source = (const void *)((uintptr_t)source & ~(uintptr_t)alignmentMask);
    destination = (void *)((uintptr_t)destination & ~(uintptr_t)alignmentMask);
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
        {
            dma->flags = *control;
            Transfer(channel, dma);
        }
        else if (!(*control & DMA_ENABLE))
            dma->armed = 0;
    }
}

void PortDma_OnHBlank(void) { OnEvent(DMA_START_HBLANK); }
void PortDma_OnVBlank(void) { OnEvent(DMA_START_VBLANK); }
