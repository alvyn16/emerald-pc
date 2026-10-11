#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <windows.h>
#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_psg.h"

static int16_t sSamples[48000 * 2];
static void Reset(void)
{
    memset((void *)0x04000000, 0, 4096);
    memset(sSamples, 0, sizeof(sSamples));
    PortPsg_Reset();
    REG_NR52 = 0x80;
    REG_NR50 = 0x77;
    REG_NR51 = 0xff;
    REG_SOUNDCNT_H = 2;
}
int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);
    Reset();
    REG_NR11 = 0x80;
    REG_NR12 = 0xf0;
    REG_NR13 = 1917 & 255;
    REG_NR14 = 0x80 | (1917 >> 8);
    PortPsg_Render(sSamples, 48000, 48000);
    assert(!(REG_NR14 & 0x80));
    unsigned rising = 0, positive = 0;
    for (unsigned i = 1; i < 48000; ++i)
    {
        if (sSamples[(i - 1) * 2] <= 0 && sSamples[i * 2] > 0) rising++;
        if (sSamples[i * 2] > 0) positive++;
    }
    assert(rising >= 998 && rising <= 1002);
    assert(positive > 23900 && positive < 24100);

    Reset();
    REG_NR42 = 0xf0;
    REG_NR43 = 8; // 7-bit LFSR, one shift per sample at 524288 Hz.
    REG_NR44 = 0x80;
    PortPsg_Render(sSamples, 512, 524288);
    for (unsigned i = 128; i < 384; ++i)
        assert(sSamples[i * 2] == sSamples[(i + 127) * 2]);
    assert(!(REG_NR44 & 0x80));

    Reset();
    REG_NR11 = 0x80;
    REG_NR12 = 0xf1;
    REG_NR14 = 0x80;
    PortPsg_Render(sSamples, 48000, 48000);
    assert(sSamples[0] != 0);
    assert(sSamples[47999 * 2] == 0);

    Reset();
    PortPsg_Write8(0x04000070, 0x40); // CPU writes opposite bank: fill bank 0.
    for (unsigned i = 0; i < 16; ++i)
        PortPsg_Write8(0x04000090+i, ((i & 7) * 2 << 4) | ((i & 7) * 2 + 1));
    PortPsg_Write8(0x04000070, 0x80);
    REG_NR32 = 0x20;
    REG_NR33 = 0;
    REG_NR34 = 0x80 | 6; // 128 Hz.
    PortPsg_Render(sSamples, 170, 48000);
    for (unsigned i = 1; i < 160; ++i)
        assert(sSamples[i * 2] >= sSamples[(i - 1) * 2]);
    assert(sSamples[150 * 2] > sSamples[0]);
    REG_NR52 = 0;
    memset(sSamples, 0, sizeof(sSamples));
    PortPsg_Render(sSamples, 100, 48000);
    for (unsigned i = 0; i < 200; ++i) assert(sSamples[i] == 0);
    // Multiple bank switches/writes before rendering preserve both banks.
    Reset();
    PortPsg_Write8(0x04000084, 0x80);
    PortPsg_Write8(0x04000080, 0x77);
    PortPsg_Write8(0x04000081, 0x44);
    PortPsg_Write8(0x04000070, 0x40); // Fill bank 0, playback bank 1.
    for (unsigned i=0;i<4;++i) PortPsg_Write32(0x04000090+i*4,0xffffffff);
    PortPsg_Write8(0x04000070, 0); // Fill bank 1, playback bank 0.
    for (unsigned i=0;i<8;++i) PortPsg_Write16(0x04000090+i*2,0);
    PortPsg_Write8(0x04000070, 0xa0); // Play 64 nibbles, bank 0 then 1.
    PortPsg_Write16(0x04000072, 0x2000);
    PortPsg_Write16(0x04000074, 0x8600);
    PortPsg_Render(sSamples,64,4096); // Exactly one nibble/sample.
    for (unsigned i=0;i<64;++i) assert(sSamples[i*2] == (i<32?3840:-3840));
    assert(REG_NR52 & 4);
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,32,4096);
    assert(REG_NR30 & 0x40); // Playback has entered bank 1, CPU sees bank 0.
    assert(REG_WAVE_RAM0 == 0xffffffff);
    for (unsigned i=0;i<4;++i) PortPsg_Write32(0x04000090+i*4,0);
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,64,4096);
    for (unsigned i=0;i<64;++i) assert(sSamples[i*2]==-3840);
    PortPsg_Write8(0x04000070, 0x40); // DAC stop, visible bank 0 still intact.
    assert(!(REG_NR52 & 4));
    assert(REG_WAVE_RAM0 == 0);
    PortPsg_Write8(0x04000070, 0); assert(REG_WAVE_RAM0 == 0);

    // Same-value trigger is an event even when the visible trigger bit is zero.
    Reset();
    PortPsg_Write8(0x04000084,0x80);
    PortPsg_Write8(0x04000081,0x10); // Square 1 left only.
    PortPsg_Write16(0x04000062,0xf080);
    PortPsg_Write16(0x04000064,0x87ff);
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,1,65536);
    assert(sSamples[0] == 3840 && sSamples[1] == 0);
    PortPsg_Write16(0x04000064,0x87ff);
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,1,65536);
    assert(sSamples[0] == 3840 && sSamples[1] == 0);
    PortPsg_Write8(0x04000063,0); assert(!(REG_NR52 & 1));
    // Length 1 expires at first sequencer clock; sweep 1000->500 at step 2.
    Reset(); PortPsg_Write8(0x04000084,0x80);
    PortPsg_Write16(0x04000062,0xf0bf);
    PortPsg_Write16(0x04000064,0xc000);
    PortPsg_Render(sSamples,94,48000); assert(!(REG_NR52 & 1));
    Reset(); PortPsg_Write8(0x04000084,0x80);
    PortPsg_Write8(0x04000060,0x19);
    PortPsg_Write16(0x04000062,0xf080);
    PortPsg_Write16(0x04000064,0x83e8);
    PortPsg_Render(sSamples,282,48000);
    assert((REG_NR13 | ((REG_NR14 & 7)<<8)) == 500);
    // Sweep update must survive a second render call (no reset from raw regs).
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,1,48000);
    assert((REG_NR13 | ((REG_NR14 & 7)<<8)) == 500);
    Reset(); PortPsg_Write8(0x04000084,0x80);
    PortPsg_Write8(0x04000060,0x11);
    PortPsg_Write16(0x04000062,0xf080);
    PortPsg_Write16(0x04000064,0x8672); // 1650 + 825 => overflow at trigger.
    assert(!(REG_NR52 & 1));
    // Disable/re-enable cannot resurrect a voice; RAM reset clears wave banks.
    PortPsg_Write8(0x04000084,0); PortPsg_Write8(0x04000084,0x80);
    memset(sSamples,0,sizeof(sSamples)); PortPsg_Render(sSamples,100,48000);
    assert((REG_NR52 & 15)==0);
    for (unsigned i=0;i<200;++i) assert(sSamples[i]==0);
    PortPsg_Reset(); PortPsg_Write8(0x04000070,0x40); assert(REG_WAVE_RAM0==0);
    // A hooked routing write must not hide an earlier legacy raw trigger.
    Reset(); PortPsg_Write8(0x04000084,0x80);
    REG_NR11=0x80; REG_NR12=0xf0; REG_NR13=0xff; REG_NR14=0x87;
    PortPsg_Write8(0x04000082,2);
    PortPsg_Render(sSamples,1,65536);
    assert(sSamples[0]==3840 && !(REG_NR14 & 0x80));
    puts("PSG vectors: two banks, repeated triggers, length, sweep, noise and power OK");
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
