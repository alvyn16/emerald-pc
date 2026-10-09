#include <string.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_timer.h"

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
}

static uint32_t AddTicks(struct TimerState *timer, uint32_t ticks)
{
    uint32_t total = (uint32_t)timer->counter + ticks;
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

        // Memory-mapped writes cannot be trapped here. A changed CNT_L
        // value is treated as a new reload; equal-value writes are invisible.
        if (observed != timer->lastWritten)
            timer->reload = observed;
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
                const uint32_t accumulated = cycles + timer->dividerRemainder;
                ticks = accumulated / divider;
                timer->dividerRemainder = accumulated % divider;
            }
            previousOverflows = AddTicks(timer, ticks);
        }
        else
            previousOverflows = 0;

        timer->control = control;
        registers[i * 2] = timer->counter;
        timer->lastWritten = timer->counter;
    }
}
