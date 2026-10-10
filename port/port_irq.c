#include "global.h"
#include "main.h"
#include "port_irq.h"

#define IRQ_MASK 0x3fffu
#define IRQ_SOURCE_COUNT 14u

static uint16_t sPending;
static int sDispatching;

/* Emerald's IntrMain/gIntrTable order, rather than numerical bit order. */
static const uint16_t sSources[IRQ_SOURCE_COUNT] = {
    INTR_FLAG_VCOUNT, INTR_FLAG_SERIAL, INTR_FLAG_TIMER3,
    INTR_FLAG_HBLANK, INTR_FLAG_VBLANK,
    INTR_FLAG_TIMER0, INTR_FLAG_TIMER1, INTR_FLAG_TIMER2,
    INTR_FLAG_DMA0, INTR_FLAG_DMA1, INTR_FLAG_DMA2, INTR_FLAG_DMA3,
    INTR_FLAG_KEYPAD, INTR_FLAG_GAMEPAK
};

void PortIrq_Reset(void)
{
    sPending = 0;
    sDispatching = 0;
    REG_IF = 0;
    INTR_CHECK = 0;
}

void PortIrq_Raise(uint16_t flags)
{
    sPending |= flags & IRQ_MASK;
    REG_IF = sPending;
}

void PortIrq_Acknowledge(uint16_t flags)
{
    sPending &= ~(flags & IRQ_MASK);
    REG_IF = sPending;
}

uint16_t PortIrq_Pending(void)
{
    return sPending;
}

uint16_t PortIrq_Dispatch(void)
{
    uint16_t delivered = 0;
    if (sDispatching)
        return 0;
    sDispatching = 1;
    while (REG_IME & 1)
    {
        uint16_t eligible = sPending & REG_IE & ~delivered;
        unsigned index;
        for (index = 0; index < IRQ_SOURCE_COUNT; ++index)
            if (eligible & sSources[index])
                break;
        if (index == IRQ_SOURCE_COUNT)
            break;
        const uint16_t source = sSources[index];
        PortIrq_Acknowledge(source);
        delivered |= source;
        INTR_CHECK |= source;
        if (gIntrTable[index] != NULL)
            gIntrTable[index]();
    }
    sDispatching = 0;
    return delivered;
}
