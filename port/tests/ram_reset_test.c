#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
#include "gba/types.h"
#include "gba/io_reg.h"
#include "gba/defines.h"
#include "port_ram_reset.h"
#include "port_dma.h"
#include "port_timer.h"
#include "port_irq.h"
void (*gIntrTable[14])(void);

int main(void)
{
    const uintptr_t regions[] = {0x02000000,0x03000000,0x05000000,0x06000000,0x07000000};
    const unsigned sizes[] = {0x40000,0x8000,0x400,0x18000,0x400};
    for (unsigned i=0;i<5;++i)
        assert(VirtualAlloc((void *)regions[i], sizes[i], MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    assert(VirtualAlloc((void *)REG_BASE,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    assert(VirtualAlloc((void *)0x08000000,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    *(uint32_t *)0x08000000=0x12345678;
    uint32_t nativeCanary=0x87654321;
    const unsigned flags[]={0,1,2,4,8,16,32,64,128,255};
    for (unsigned f=0;f<sizeof(flags)/sizeof(flags[0]);++f)
    {
        for (unsigned i=0;i<5;++i) memset((void *)regions[i],0xa5,sizes[i]);
        memset((void *)REG_BASE,0xa5,4096);
        PortRamReset(flags[f]);
        for (unsigned i=0;i<5;++i)
        {
            unsigned length=i==1?0x7e00:sizes[i];
            unsigned expected=flags[f]&(1u<<i)?0:0xa5;
            for (unsigned j=0;j<length;++j) assert(((uint8_t *)regions[i])[j]==expected);
        }
        for (unsigned j=0x7e00;j<0x8000;++j) assert(((uint8_t *)regions[1])[j]==0xa5);
        assert(REG_DISPCNT==0x80 && REG_KEYINPUT==0xa5a5);
        assert(*(uint16_t *)0x04000120==0);
        assert(*(uint16_t *)0x04000134==(flags[f]&32?0x8000:0xa5a5));
        assert(REG_SOUNDBIAS==(flags[f]&64?0x200:0xa5a5));
        assert(REG_BG2PA==(flags[f]&128?256:0xa5a5));
        assert(*(uint32_t *)0x08000000==0x12345678 && nativeCanary==0x87654321);
    }
    PortTimer_Write32(REG_ADDR_TM0CNT_L,(TIMER_ENABLE<<16)|10);
    uint16_t source=7,destination=0;
    PortDma_Set(0,&source,&destination,((DMA_ENABLE|DMA_START_HBLANK)<<16)|1);
    PortIrq_Raise(INTR_FLAG_VBLANK);
    PortRamReset(128);
    PortTimer_Advance(100); PortDma_OnHBlank();
    assert(REG_TM0CNT_L==0 && destination==0 && !PortIrq_Pending());
    return 0;
}
