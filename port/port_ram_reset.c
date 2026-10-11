#include <string.h>
#include "gba/types.h"
#include "gba/io_reg.h"
#include "gba/defines.h"
#include "port_ram_reset.h"
#include "port_dma.h"
#include "port_irq.h"
#include "port_timer.h"
#include "port_psg.h"
#include "port_ppu.h"

static void Clear(uintptr_t address, unsigned bytes)
{
    memset((void *)address, 0, bytes);
}

void PortRamReset(uint32_t flags)
{
    // These are the mapped GBA regions, never the native C heap or stack.
    if (flags & 1) Clear(0x02000000, 0x40000);
    if (flags & 2) Clear(0x03000000, 0x7e00);
    if (flags & 4) Clear(0x05000000, 0x400);
    if (flags & 8) Clear(0x06000000, 0x18000);
    if (flags & 16) Clear(0x07000000, 0x400);
    REG_DISPCNT = 0x80; // BIOS forces blank even with flags=0.
    *(volatile uint16_t *)0x04000120 = 0; // Documented SIODATA32 low-half side effect.
    if (flags & 32)
    {
        Clear(0x04000120, 12);
        *(volatile uint16_t *)0x04000134 = 0x8000;
        *(volatile uint16_t *)0x04000140 = 0;
        Clear(0x04000150, 12);
    }
    if (flags & 64)
    {
        Clear(0x04000060, 0x48);
        REG_SOUNDBIAS = 0x200;
        PortPsg_Reset();
    }
    if (flags & 128)
    {
        Clear(REG_BASE, 0x60);
        REG_DISPCNT = 0x80;
        REG_BG2PA = REG_BG2PD = REG_BG3PA = REG_BG3PD = 0x100;
        PortDma_Reset();
        PortTimer_Reset();
        *(volatile uint16_t *)0x04000132 = 0; // KEYCNT; KEYINPUT is read-only.
        Clear(0x04000200, 10);
        uint16_t preservedCheck = INTR_CHECK;
        PortIrq_Reset();
        INTR_CHECK = preservedCheck; // Last 0x200 IWRAM bytes are excluded.
        PortPpu_BeginFrame();
    }
}
