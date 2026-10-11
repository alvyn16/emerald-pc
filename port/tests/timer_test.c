#include <assert.h>
#include <string.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_timer.h"
#include "port_irq.h"
void (*gIntrTable[14])(void);

static void Reset(void)
{
    memset((void *)REG_ADDR_TM0CNT_L, 0, 16);
    PortTimer_Reset();
    PortIrq_Reset();
}

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);
    void *iwram = VirtualAlloc((void *)0x03000000, 32768,
                              MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(iwram == (void *)0x03000000);

    Reset();
    REG_TM0CNT_H = TIMER_ENABLE;
    PortTimer_Advance(100);
    assert(REG_TM0CNT_L == 100);
    REG_TM0CNT_H = 0;
    PortTimer_Advance(100);
    assert(REG_TM0CNT_L == 100);

    Reset();
    REG_TM0CNT_L = 0xfffe;
    REG_TM0CNT_H = TIMER_ENABLE | TIMER_64CLK;
    PortTimer_Advance(63);
    assert(REG_TM0CNT_L == 0xfffe);
    PortTimer_Advance(64);
    assert(REG_TM0CNT_L == 0xffff);
    PortTimer_Advance(64);
    assert(REG_TM0CNT_L == 0xfffe);
    REG_TM0CNT_L = 0xfffc;
    REG_TM0CNT_H = 0;
    PortTimer_Advance(0);
    assert(REG_TM0CNT_L == 0xfffe); // Reload write leaves the stopped counter.
    REG_TM0CNT_H = TIMER_ENABLE;
    PortTimer_Advance(7);
    assert(REG_TM0CNT_L == 0xffff);

    Reset();
    REG_TM0CNT_L = 0xffff;
    REG_TM0CNT_H = TIMER_ENABLE;
    REG_TM1CNT_H = TIMER_ENABLE | 4;
    PortTimer_Advance(3);
    assert(REG_TM1CNT_L == 3);
    PortTimer_Advance(1);
    assert(REG_TM1CNT_L == 4);

    Reset();
    REG_TM2CNT_H = TIMER_ENABLE | TIMER_1024CLK;
    PortTimer_Advance(1023);
    assert(REG_TM2CNT_L == 0);
    PortTimer_Advance(1);
    assert(REG_TM2CNT_L == 1);

    Reset();
    REG_TM0CNT_L = 0xffff;
    REG_TM0CNT_H = TIMER_ENABLE;
    REG_TM1CNT_H = TIMER_ENABLE | 4;
    PortTimer_Advance(UINT32_MAX);
    assert(REG_TM0CNT_L == 0xffff && REG_TM1CNT_L == 0xffff);

    Reset();
    PortTimer_Write32(REG_ADDR_TM0CNT_L,
                     ((TIMER_ENABLE | TIMER_INTR_ENABLE) << 16) | 0xfffe);
    PortTimer_Advance(1);
    assert(REG_TM0CNT_L == 0xffff);
    // Same as current counter: polling would miss the new reload 0xffff.
    PortTimer_Write16(REG_ADDR_TM0CNT_L, 0xffff);
    PortTimer_Advance(1);
    assert(REG_TM0CNT_L == 0xffff);
    assert(PortIrq_Pending() == INTR_FLAG_TIMER0);
    PortIrq_Acknowledge(INTR_FLAG_TIMER0);
    PortTimer_Advance(100);
    assert(REG_TM0CNT_L == 0xffff && PortIrq_Pending() == INTR_FLAG_TIMER0);
    PortTimer_Write16(REG_ADDR_TM0CNT_H, 0);
    PortTimer_Write16(REG_ADDR_TM0CNT_L, 7);
    assert(REG_TM0CNT_L == 0xffff);
    PortTimer_Write16(REG_ADDR_TM0CNT_H, TIMER_ENABLE);
    assert(REG_TM0CNT_L == 7);
    PortTimer_Advance(2);
    assert(REG_TM0CNT_L == 9);

    Reset();
    PortTimer_Write32(REG_ADDR_TM0CNT_L, (TIMER_ENABLE << 16) | 0xffff);
    PortTimer_Write32(REG_ADDR_TM1CNT_L,
                     ((TIMER_ENABLE | TIMER_INTR_ENABLE | 4) << 16) | 0xfffe);
    PortTimer_Advance(5);
    assert(REG_TM1CNT_L == 0xffff);
    assert(PortIrq_Pending() == INTR_FLAG_TIMER1);

    VirtualFree(io, 0, MEM_RELEASE);
    VirtualFree(iwram, 0, MEM_RELEASE);
    return 0;
}
