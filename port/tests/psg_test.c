#include <assert.h>
#include <string.h>
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
    REG_NR43 = 8; // 7-bit LFSR, one shift per sample at 65536 Hz.
    REG_NR44 = 0x80;
    PortPsg_Render(sSamples, 512, 65536);
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
    for (unsigned i = 0; i < 16; ++i)
        ((volatile uint8_t *)0x04000090)[i] = ((i & 7) * 2 << 4) | ((i & 7) * 2 + 1);
    REG_NR30 = 0x80;
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
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
