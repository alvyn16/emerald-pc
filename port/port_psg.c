/* Sample-level PSG synthesis from the host's mapped GBA sound registers. */
#include <string.h>
#include "gba/types.h"
#include "gba/io_reg.h"
#include "port_psg.h"

struct Oscillator
{
    double phase;
    unsigned frequency, length, volume, envelopePeriod, envelopeTicks;
    unsigned sweepFrequency, sweepTicks;
    uint16_t lfsr;
    int enabled, envelopeUp, lengthEnabled;
};

static struct Oscillator sChannels[4];
static double sClock;
static unsigned sClockStep;
static uint8_t sWaveBanks[2][16];
static uint8_t sObserved[64];
static void ResetOscillators(void)
{
    memset(sChannels, 0, sizeof(sChannels));
    sClock = 0;
    sClockStep = 0;
}

void PortPsg_Reset(void)
{
    ResetOscillators();
    memset(sWaveBanks, 0, sizeof(sWaveBanks));
    memset(sObserved, 0, sizeof(sObserved));
}

static unsigned Sweep(unsigned frequency)
{
    unsigned delta = frequency >> (REG_NR10 & 7);
    return REG_NR10 & 8 ? frequency - delta : frequency + delta;
}

static void Trigger(unsigned i, uint8_t length, uint8_t envelope, uint8_t control)
{
    struct Oscillator *c = &sChannels[i];
    c->enabled = i == 2 ? (REG_NR30 & 0x80) != 0 : (envelope & 0xf8) != 0;
    c->phase = 0;
    if (!c->length) c->length = i == 2 ? 256 - length : 64 - (length & 63);
    c->lengthEnabled = (control & 0x40) != 0;
    c->volume = envelope >> 4;
    c->envelopePeriod = envelope & 7;
    c->envelopeTicks = 0;
    c->envelopeUp = (envelope & 8) != 0;
    c->lfsr = 0x7fff;
    if (!i)
    {
        c->sweepFrequency = c->frequency;
        c->sweepTicks = 0;
        if ((REG_NR10 & 7) && Sweep(c->frequency) > 2047) c->enabled = 0;
    }
}

static void UpdateStatus(void)
{
    unsigned enabled = 0;
    for (unsigned i = 0; i < 4; ++i) if (sChannels[i].enabled) enabled |= 1u << i;
    REG_NR52 = (REG_NR52 & 0x80) | enabled;
}

void PortPsg_Write8(uintptr_t address, uint8_t value)
{
    if (address < 0x04000060 || address >= 0x040000a0) return;
    volatile uint8_t *reg = (volatile uint8_t *)address;
    unsigned offset = address - 0x04000060;
    if (offset >= 0x30)
    {
        *reg = value;
        sWaveBanks[((REG_NR30 >> 6) & 1) ^ 1][offset - 0x30] = value;
    }
    else if (offset == 0x24)
    {
        int powered = sObserved[0x24] & 0x80;
        if (powered && !(value & 0x80))
        {
            ResetOscillators();
            memset((void *)0x04000060, 0, 0x22);
            memcpy((void *)0x04000090, sWaveBanks[1], 16);
        }
        else if (!powered && (value & 0x80)) ResetOscillators();
        *reg = value & 0x80;
    }
    else if (offset >= 0x22 || (REG_NR52 & 0x80))
    {
        *reg = value;
        if (offset == 0x10)
        {
            if (!(value & 0x80)) sChannels[2].enabled = 0;
            memcpy((void *)0x04000090, sWaveBanks[((value >> 6) & 1) ^ 1], 16);
        }
        static const unsigned lengths[] = {2,8,0x12,0x18};
        static const unsigned envelopes[] = {3,9,0x13,0x19};
        static const unsigned controls[] = {5,0xd,0x15,0x1d};
        for (unsigned i = 0; i < 4; ++i)
        {
            struct Oscillator *c = &sChannels[i];
            if (offset == lengths[i]) c->length = i == 2 ? 256 - value : 64 - (value & 63);
            if (i != 2 && offset == envelopes[i] && !(value & 0xf8)) c->enabled = 0;
            if (i < 3 && (offset == controls[i] - 1 || offset == controls[i]))
                c->frequency = ((volatile uint8_t *)0x04000060)[controls[i]-1]
                    | ((((volatile uint8_t *)0x04000060)[controls[i]] & 7) << 8);
            if (offset == controls[i])
            {
                c->lengthEnabled = (value & 0x40) != 0;
                if (value & 0x80) Trigger(i, ((volatile uint8_t *)0x04000060)[lengths[i]],
                    ((volatile uint8_t *)0x04000060)[envelopes[i]], value);
                *reg &= ~0x80; // Trigger is a write event, not a persistent bit.
            }
        }
    }
    UpdateStatus();
    memcpy(sObserved, (const void *)0x04000060, sizeof(sObserved));
}

void PortPsg_Write16(uintptr_t address, uint16_t value)
{
    if (address & 1) return;
    PortPsg_Write8(address, value);
    PortPsg_Write8(address + 1, value >> 8);
}
void PortPsg_Write32(uintptr_t address, uint32_t value)
{
    if (address & 3) return;
    PortPsg_Write16(address, value);
    PortPsg_Write16(address + 2, value >> 16);
}

/* Fallback for legacy raw writes. Same-value events require the hooks above. */
static void ObserveRawWrites(void)
{
    uint8_t snapshot[64], previous[64];
    memcpy(snapshot, (const void *)0x04000060, sizeof(snapshot));
    memcpy(previous, sObserved, sizeof(previous));
    if (snapshot[0x24] != previous[0x24]) PortPsg_Write8(0x04000084, snapshot[0x24]);
    for (unsigned i = 0; i < 64; ++i)
        if (i != 0x24 && snapshot[i] != previous[i]) PortPsg_Write8(0x04000060 + i, snapshot[i]);
}

static void ClockSequencer(void)
{
    if (!(sClockStep & 1))
        for (unsigned i = 0; i < 4; ++i)
            if (sChannels[i].enabled && sChannels[i].lengthEnabled &&
                sChannels[i].length && --sChannels[i].length == 0)
                sChannels[i].enabled = 0;
    if (sClockStep == 2 || sClockStep == 6)
    {
        struct Oscillator *c = &sChannels[0];
        unsigned period = (REG_NR10 >> 4) & 7;
        if (c->enabled && ++c->sweepTicks >= (period ? period : 8))
        {
            c->sweepTicks = 0;
            if ((REG_NR10 & 7) && period)
            {
                unsigned next = Sweep(c->sweepFrequency);
                if (next > 2047) c->enabled = 0;
                else
                {
                    c->frequency = c->sweepFrequency = next;
                    REG_NR13 = next & 255;
                    REG_NR14 = (REG_NR14 & 0x40) | (next >> 8);
                    if (Sweep(next) > 2047) c->enabled = 0;
                }
            }
        }
    }
    if (sClockStep == 7)
        for (unsigned i = 0; i < 4; ++i)
        {
            struct Oscillator *c = &sChannels[i];
            if (i == 2 || !c->enabled || !c->envelopePeriod) continue;
            if (++c->envelopeTicks >= c->envelopePeriod)
            {
                c->envelopeTicks = 0;
                if (c->envelopeUp && c->volume < 15) ++c->volume;
                else if (!c->envelopeUp && c->volume) --c->volume;
            }
        }
    sClockStep = (sClockStep + 1) & 7;
}

static int Clip(int value)
{ return value < -32768 ? -32768 : value > 32767 ? 32767 : value; }

void PortPsg_Render(int16_t *stereo, unsigned frames, unsigned sampleRate)
{
    if (!frames || !sampleRate) return;
    ObserveRawWrites();
    if (!(REG_NR52 & 0x80)) return;
    const unsigned lengths[] = {REG_NR11, REG_NR21, REG_NR31, REG_NR41};
    const unsigned waveBank = (REG_NR30 >> 6) & 1;
    const unsigned waveLength = REG_NR30 & 0x20 ? 64 : 32;
    const unsigned routing = REG_NR51, levels = REG_NR50;
    const unsigned ratio = REG_SOUNDCNT_H & 3;
    const unsigned shift = ratio < 2 ? 2 - ratio : 0;
    static const double duties[] = {0.125, 0.25, 0.5, 0.75};
    for (unsigned frame = 0; frame < frames; ++frame)
    {
        int left = 0, right = 0;
        for (unsigned i = 0; i < 4; ++i)
        {
            struct Oscillator *c = &sChannels[i];
            if (!c->enabled) continue;
            int value;
            if (i < 2)
            {
                unsigned duty = (lengths[i] >> 6) & 3;
                value = c->phase < duties[duty] ? (int)c->volume * 256 : -(int)c->volume * 256;
                c->phase += 131072.0 / (2048 - c->frequency) / sampleRate;
            }
            else if (i == 2)
            {
                unsigned position = (unsigned)(c->phase * waveLength) % waveLength;
                unsigned bank = (waveBank + position / 32) & 1;
                unsigned packed = sWaveBanks[bank][(position % 32) / 2];
                int sample = ((position & 1) ? packed & 15 : packed >> 4) * 2 - 15;
                unsigned volume = (REG_NR32 >> 5) & 3;
                value = REG_NR32 & 0x80 ? sample * 192 : volume ? sample * 256 / (1 << (volume - 1)) : 0;
                c->phase += 65536.0 * 32 / waveLength / (2048 - c->frequency) / sampleRate;
            }
            else
            {
                value = c->lfsr & 1 ? -(int)c->volume * 256 : (int)c->volume * 256;
                double divisor = (REG_NR43 & 7) ? REG_NR43 & 7 : 0.5;
                c->phase += 524288.0 / divisor / (1u << ((REG_NR43 >> 4) + 1)) / sampleRate;
                while (c->phase >= 1)
                {
                    unsigned feedback = (c->lfsr ^ (c->lfsr >> 1)) & 1;
                    c->lfsr = (c->lfsr >> 1) | (feedback << 14);
                    if (REG_NR43 & 8) c->lfsr = (c->lfsr & ~0x40) | (feedback << 6);
                    c->phase -= 1;
                }
            }
            if (i != 3) while (c->phase >= 1) c->phase -= 1;
            value >>= shift;
            if (routing & (1u << (i + 4))) left += value * (int)(((levels >> 4) & 7) + 1) / 8;
            if (routing & (1u << i)) right += value * (int)((levels & 7) + 1) / 8;
        }
        stereo[frame * 2] = Clip(stereo[frame * 2] + left);
        stereo[frame * 2 + 1] = Clip(stereo[frame * 2 + 1] + right);
        sClock += 512.0 / sampleRate;
        while (sClock >= 1) { ClockSequencer(); sClock -= 1; }
    }
    UpdateStatus();
    memcpy(sObserved, (const void *)0x04000060, sizeof(sObserved));
}
