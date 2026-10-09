#include <assert.h>
#include <string.h>
#include <windows.h>

#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_timer.h"

static void Reset(void)
{
    memset((void *)REG_ADDR_TM0CNT_L, 0, 16);
    PortTimer_Reset();
}

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);

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

    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
