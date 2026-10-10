#include <assert.h>
#include <stdio.h>
#include <string.h>
#define NOMINMAX
#include <windows.h>

#include "global.h"
#include "main.h"
#include "port_irq.h"

IntrFunc gIntrTable[14];
static unsigned sCalls;
static unsigned sOrder[4];
static int sDisable;
static int sRegenerate;

static void VCount(void)
{
    sOrder[sCalls++] = 0;
    assert(!(REG_IF & INTR_FLAG_VCOUNT)); // Acknowledge precedes callback.
    if (sDisable)
        REG_IME = 0;
}

static void VBlank(void)
{
    sOrder[sCalls++] = 4;
    if (sRegenerate)
    {
        PortIrq_Raise(INTR_FLAG_VBLANK);
        assert(PortIrq_Dispatch() == 0); // No recursive callback delivery.
    }
}

static void ResetFixture(void)
{
    memset((void *)REG_BASE, 0, 4096);
    PortIrq_Reset();
    memset(gIntrTable, 0, sizeof(gIntrTable));
    gIntrTable[0] = VCount;
    gIntrTable[4] = VBlank;
    sCalls = 0;
    sDisable = sRegenerate = 0;
}

int main(void)
{
    assert(VirtualAlloc((void *)0x03000000, 32768, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    assert(VirtualAlloc((void *)REG_BASE, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    ResetFixture();
    REG_IE = INTR_FLAG_VBLANK;
    PortIrq_Raise(INTR_FLAG_VBLANK | INTR_FLAG_VCOUNT);
    assert(PortIrq_Dispatch() == 0 && sCalls == 0 && INTR_CHECK == 0);
    REG_IME = 1;
    assert(PortIrq_Dispatch() == INTR_FLAG_VBLANK && sCalls == 1);
    assert(PortIrq_Pending() == INTR_FLAG_VCOUNT && REG_IF == INTR_FLAG_VCOUNT);
    assert(INTR_CHECK == INTR_FLAG_VBLANK);
    assert(PortIrq_Dispatch() == 0 && sCalls == 1);
    REG_IE |= INTR_FLAG_VCOUNT;
    assert(PortIrq_Dispatch() == INTR_FLAG_VCOUNT && sCalls == 2);

    ResetFixture();
    PortIrq_Raise(INTR_FLAG_DMA0 | INTR_FLAG_DMA1 | 0xc000);
    PortIrq_Acknowledge(0);
    assert(REG_IF == (INTR_FLAG_DMA0 | INTR_FLAG_DMA1));
    PortIrq_Acknowledge(INTR_FLAG_DMA0);
    PortIrq_Acknowledge(INTR_FLAG_DMA0);
    assert(REG_IF == INTR_FLAG_DMA1 && PortIrq_Pending() == INTR_FLAG_DMA1);

    ResetFixture();
    REG_IE = INTR_FLAG_VBLANK | INTR_FLAG_VCOUNT;
    REG_IME = 1;
    PortIrq_Raise(REG_IE);
    assert(PortIrq_Dispatch() == REG_IE);
    assert(sCalls == 2 && sOrder[0] == 0 && sOrder[1] == 4);
    sCalls = 0;
    sDisable = 1;
    PortIrq_Raise(REG_IE);
    assert(PortIrq_Dispatch() == INTR_FLAG_VCOUNT && sCalls == 1);
    assert(PortIrq_Pending() == INTR_FLAG_VBLANK);
    REG_IME = 1;
    assert(PortIrq_Dispatch() == INTR_FLAG_VBLANK);

    ResetFixture();
    REG_IE = INTR_FLAG_VBLANK;
    REG_IME = 1;
    sRegenerate = 1;
    PortIrq_Raise(INTR_FLAG_VBLANK);
    assert(PortIrq_Dispatch() == INTR_FLAG_VBLANK && sCalls == 1);
    assert(PortIrq_Pending() == INTR_FLAG_VBLANK);
    sRegenerate = 0;
    assert(PortIrq_Dispatch() == INTR_FLAG_VBLANK && sCalls == 2);
    PortIrq_Reset();
    assert(REG_IF == 0 && INTR_CHECK == 0 && PortIrq_Pending() == 0);
    VirtualFree((void *)REG_BASE, 0, MEM_RELEASE);
    VirtualFree((void *)0x03000000, 0, MEM_RELEASE);
    puts("IRQ pending, masks, acknowledge, priority and reentry OK");
    return 0;
}
