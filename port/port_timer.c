#include <string.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_timer.h"
#include "port_irq.h"

struct TimerState
{
    uint16_t counter;
    uint16_t reload;
    uint16_t lastWritten;
    uint16_t control;
    uint16_t dividerRemainder;
};

static struct TimerState sTimers[4];

void PortTimer_Reset(void)
{
    memset(sTimers, 0, sizeof(sTimers));
    memset((void *)REG_ADDR_TM0CNT_L, 0, 16);
}

void PortTimer_Write16(uintptr_t address, uint16_t value)
{
    if (address < REG_ADDR_TM0CNT_L || address >= REG_ADDR_TM0CNT_L + 16 || (address & 1))
        return;
    struct TimerState *timer = &sTimers[(address - REG_ADDR_TM0CNT_L) / 4];
    if (!(address & 2))
        timer->reload = value;
    else
    {
        value &= 0xc7;
        if ((value & TIMER_ENABLE) && !(timer->control & TIMER_ENABLE))
        {
            timer->counter = timer->reload;
            timer->dividerRemainder = 0;
        }
        timer->control = value;
        *(volatile uint16_t *)address = value;
    }
    *(volatile uint16_t *)(address & ~(uintptr_t)3) = timer->counter;
    timer->lastWritten = timer->counter;
}

void PortTimer_Write32(uintptr_t address, uint32_t value)
{
    if (address & 3) return;
    PortTimer_Write16(address, value);
    PortTimer_Write16(address + 2, value >> 16);
}

static uint32_t AddTicks(struct TimerState *timer, uint32_t ticks)
{
    uint64_t total = (uint64_t)timer->counter + ticks;
    if (total < 0x10000u)
    {
        timer->counter = total;
        return 0;
    }

    const uint32_t period = 0x10000u - timer->reload;
    total -= 0x10000u;
    timer->counter = timer->reload + total % period;
    return 1u + total / period;
}

void PortTimer_Advance(uint32_t cycles)
{
    static const unsigned prescaler[] = {1, 64, 256, 1024};
    volatile uint16_t *const registers = (volatile uint16_t *)REG_ADDR_TM0CNT_L;
    uint32_t previousOverflows = 0;

    for (unsigned i = 0; i < 4; i++)
    {
        struct TimerState *timer = &sTimers[i];
        const uint16_t observed = registers[i * 2];
        const uint16_t control = registers[i * 2 + 1];
        const int wasEnabled = (timer->control & TIMER_ENABLE) != 0;
        const int enabled = (control & TIMER_ENABLE) != 0;
        uint32_t ticks = 0;

        // Compatibility for unhooked fixtures. Game writes use Write16/32;
        // only those hooks can observe a write equal to the published counter.
        if (observed != timer->lastWritten)
        {
            timer->reload = observed;
        }
        if (enabled && !wasEnabled)
        {
            timer->counter = timer->reload;
            timer->dividerRemainder = 0;
        }
        if (enabled)
        {
            if (i != 0 && (control & 4))
                ticks = previousOverflows;
            else
            {
                const uint32_t divider = prescaler[control & 3];
                const uint64_t accumulated = (uint64_t)cycles + timer->dividerRemainder;
                ticks = accumulated / divider;
                timer->dividerRemainder = accumulated % divider;
            }
            previousOverflows = AddTicks(timer, ticks);
            if (previousOverflows && (control & TIMER_INTR_ENABLE))
                PortIrq_Raise(INTR_FLAG_TIMER0 << i);
        }
        else
            previousOverflows = 0;

        timer->control = control;
        registers[i * 2] = timer->counter;
        timer->lastWritten = timer->counter;
    }
}
