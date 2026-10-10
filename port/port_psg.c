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

void PortPsg_Reset(void)
{
    memset(sChannels, 0, sizeof(sChannels));
    memset(sWaveBanks, 0, sizeof(sWaveBanks));
    sClock = 0;
    sClockStep = 0;
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
    c->length = i == 2 ? 256 - length : 64 - (length & 63);
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
    if (!(REG_NR52 & 0x80)) { PortPsg_Reset(); return; }
    const unsigned controls[] = {REG_NR14, REG_NR24, REG_NR34, REG_NR44};
    const unsigned lengths[] = {REG_NR11, REG_NR21, REG_NR31, REG_NR41};
    const unsigned envelopes[] = {REG_NR12, REG_NR22, REG_NR32, REG_NR42};
    sChannels[0].frequency = REG_NR13 | ((REG_NR14 & 7) << 8);
    sChannels[1].frequency = REG_NR23 | ((REG_NR24 & 7) << 8);
    sChannels[2].frequency = REG_NR33 | ((REG_NR34 & 7) << 8);
    for (unsigned i = 0; i < 4; ++i)
    {
        if (controls[i] & 0x80) Trigger(i, lengths[i], envelopes[i], controls[i]);
        sChannels[i].lengthEnabled = (controls[i] & 0x40) != 0;
        if (i != 2 && !(envelopes[i] & 0xf8)) sChannels[i].enabled = 0;
    }
    REG_NR14 &= ~0x80;
    REG_NR24 &= ~0x80;
    REG_NR34 &= ~0x80;
    REG_NR44 &= ~0x80;
    if (!(REG_NR30 & 0x80)) sChannels[2].enabled = 0;

    const unsigned waveBank = (REG_NR30 >> 6) & 1;
    memcpy(sWaveBanks[waveBank], (const void *)0x04000090, 16);
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
                unsigned divisor = (REG_NR43 & 7) ? (REG_NR43 & 7) * 16 : 8;
                c->phase += 524288.0 / divisor / (1u << (REG_NR43 >> 4)) / sampleRate;
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
    unsigned enabled = 0;
    for (unsigned i = 0; i < 4; ++i) if (sChannels[i].enabled) enabled |= 1u << i;
    REG_NR52 = (REG_NR52 & 0xf0) | enabled;
}
