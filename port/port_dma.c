#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "gba/io_reg.h"
#include "port_dma.h"
#include "port_irq.h"
#include "port_ppu.h"

struct DmaState
{
    const uint8_t *source;
    uint8_t *destination;
    unsigned count;
    unsigned flags;
    int armed;
};

static struct DmaState sChannels[4];

static uintptr_t DestinationAddress(int channel, uintptr_t address, unsigned width)
{
    address &= ~(uintptr_t)(width - 1);
    if (address < 0x10000000u)
        address &= channel == 3 ? 0x0fffffffu : 0x07ffffffu;
    return address;
}

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
        if ((uintptr_t)to >= REG_BASE && (uintptr_t)to < REG_BASE + 0x60)
            PortPpu_NotifyWrite((uintptr_t)to, width);
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
        dma->destination = (uint8_t *)DestinationAddress(channel, registers[1], width);
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
    // Hardware address masks apply to GBA addresses, not native heap/image
    // pointers that the i686 port also passes through DmaSet.
    uintptr_t from = (uintptr_t)source, to = (uintptr_t)destination;
    if (from < 0x10000000u) from &= channel == 0 ? 0x07ffffffu : 0x0fffffffu;
    to = DestinationAddress(channel, to, alignmentMask + 1);
    *dma = (struct DmaState){(const uint8_t *)from, (uint8_t *)to, count, flags, 1};
    if ((flags & DMA_START_MASK) == DMA_START_NOW)
        Transfer(channel, dma);
}

void PortDma_Reset(void)
{
    memset(sChannels, 0, sizeof(sChannels));
    memset((void *)REG_ADDR_DMA0, 0, 48);
}

void PortDma_Write16(uintptr_t address, uint16_t value)
{
    if (address < REG_ADDR_DMA0 || address >= REG_ADDR_DMA0 + 48 || (address & 1)) return;
    const unsigned channel = (address - REG_ADDR_DMA0) / 12;
    const unsigned offset = (address - REG_ADDR_DMA0) % 12;
    volatile uint16_t *regs = (volatile uint16_t *)(REG_ADDR_DMA0 + channel * 12);
    const uint16_t oldControl = regs[5];
    if (offset == 8) value &= channel == 3 ? 0xffff : 0x3fff;
    if (offset == 10) value &= channel == 3 ? 0xffe0 : 0xf7e0;
    regs[offset / 2] = value;
    if (offset != 10) return;
    if (!(value & DMA_ENABLE)) sChannels[channel].armed = 0;
    else if (!(oldControl & DMA_ENABLE))
    {
        volatile uint32_t *wide = (volatile uint32_t *)regs;
        PortDma_Set(channel, (const void *)(uintptr_t)wide[0],
                    (void *)(uintptr_t)wide[1], wide[2]);
    }
}

void PortDma_Write32(uintptr_t address, uint32_t value)
{
    if (address & 3) return;
    PortDma_Write16(address, value);
    PortDma_Write16(address + 2, value >> 16);
}

void PortDma_Stop(int channel)
{
    if (channel < 0 || channel > 3) return;
    const uintptr_t address = REG_ADDR_DMA0CNT_H + channel * 12;
    PortDma_Write16(address, *(volatile uint16_t *)address &
                    ~(DMA_START_MASK | DMA_DREQ_ON | DMA_REPEAT | DMA_ENABLE));
}

static void OnEvent(unsigned start)
{
    for (int channel = 0; channel < 4; ++channel)
    {
        struct DmaState *dma = &sChannels[channel];
        volatile uint16_t *control = (volatile uint16_t *)(uintptr_t)
                (REG_ADDR_DMA0CNT_H + channel * 12);
        if (dma->armed && (*control & DMA_ENABLE) &&
            (*control & DMA_START_MASK) == start)
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
