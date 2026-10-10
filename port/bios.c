#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gba/types.h"
#include "gba/multiboot.h"
#include "gba/syscall.h"
#include "platform.h"
#include "port_reset.h"

#define BIOS_COUNT_MASK 0x001FFFFFu
#define BIOS_SOURCE_FIXED 0x01000000u
#define BIOS_COPY_32BIT 0x04000000u

static void CopyUnits(const void *source, void *destination, u32 count, size_t unitSize, int fixed)
{
    const u8 *from = source;
    u8 *to = destination;
    u8 value[4];

    if (source == NULL || destination == NULL || count == 0)
        return;
    if (fixed)
        memcpy(value, from, unitSize);
    for (u32 i = 0; i < count; ++i)
    {
        memcpy(to + i * unitSize, fixed ? value : from + i * unitSize, unitSize);
    }
}

void CpuSet(const void *source, void *destination, u32 control)
{
    CopyUnits(source, destination, control & BIOS_COUNT_MASK,
              (control & BIOS_COPY_32BIT) ? 4 : 2,
              (control & BIOS_SOURCE_FIXED) != 0);
}

void CpuFastSet(const void *source, void *destination, u32 control)
{
    CopyUnits(source, destination, control & BIOS_COUNT_MASK, 4,
              (control & BIOS_SOURCE_FIXED) != 0);
}

static u32 DecompressedLength(const u8 *source, u8 expectedType)
{
    if (source == NULL || source[0] != expectedType)
    {
        fprintf(stderr, "BIOS: invalid compressed stream (expected 0x%02X)\n", expectedType);
        return 0;
    }
    return (u32)source[1] | ((u32)source[2] << 8) | ((u32)source[3] << 16);
}

static void Lz77Unpack(const u32 *source, void *destination)
{
    const u8 *input = (const u8 *)source;
    u8 *output = destination;
    u32 length = DecompressedLength(input, 0x10);
    u32 written = 0;
    if (destination == NULL || length == 0)
        return;
    input += 4;

    while (written < length)
    {
        u8 flags = *input++;
        for (int bit = 7; bit >= 0 && written < length; --bit)
        {
            if ((flags & (1u << bit)) == 0)
            {
                output[written++] = *input++;
            }
            else
            {
                u8 high = *input++;
                u8 low = *input++;
                u32 distance = (((u32)high & 0x0f) << 8) | low;
                u32 count = (high >> 4) + 3;
                distance++;
                if (distance > written)
                {
                    fprintf(stderr, "BIOS: invalid LZ77 back-reference\n");
                    return;
                }
                while (count-- && written < length)
                {
                    output[written] = output[written - distance];
                    written++;
                }
            }
        }
    }
}

static void RlUnpack(const u32 *source, void *destination)
{
    const u8 *input = (const u8 *)source;
    u8 *output = destination;
    u32 length = DecompressedLength(input, 0x30);
    u32 written = 0;
    if (destination == NULL || length == 0)
        return;
    input += 4;

    while (written < length)
    {
        u8 control = *input++;
        u32 count = (control & 0x7f) + ((control & 0x80) ? 3 : 1);
        if (control & 0x80)
        {
            u8 value = *input++;
            while (count-- && written < length)
                output[written++] = value;
        }
        else
        {
            while (count-- && written < length)
                output[written++] = *input++;
        }
    }
}

void LZ77UnCompWram(const u32 *source, void *destination) { Lz77Unpack(source, destination); }
void LZ77UnCompVram(const u32 *source, void *destination) { Lz77Unpack(source, destination); }
void RLUnCompWram(const u32 *source, void *destination) { RlUnpack(source, destination); }
void RLUnCompVram(const u32 *source, void *destination) { RlUnpack(source, destination); }

s32 Div(s32 numerator, s32 denominator)
{
    if (denominator == 0)
    {
        fprintf(stderr, "BIOS: Div by zero\n");
        return 0;
    }
    if (numerator == INT_MIN && denominator == -1)
        return INT_MIN;
    return numerator / denominator;
}

s32 DivArm(s32 denominator, s32 numerator)
{
    return Div(numerator, denominator);
}

u16 Sqrt(u32 number)
{
    u32 result = 0;
    u32 bit = 1u << 30;
    while (bit > number)
        bit >>= 2;
    while (bit != 0)
    {
        if (number >= result + bit)
        {
            number -= result + bit;
            result = (result >> 1) + bit;
        }
        else
            result >>= 1;
        bit >>= 2;
    }
    return (u16)result;
}

u16 ArcTan2(s16 x, s16 y)
{
    double angle = atan2((double)y, (double)x);
    long units = lround(angle * (32768.0 / 3.14159265358979323846));
    return (u16)units;
}

static s16 Fixed8_8(double value)
{
    long scaled = lround(value * 256.0);
    if (scaled > INT16_MAX)
        scaled = INT16_MAX;
    if (scaled < INT16_MIN)
        scaled = INT16_MIN;
    return (s16)scaled;
}

void BgAffineSet(struct BgAffineSrcData *source, struct BgAffineDstData *destination, s32 count)
{
    if (source == NULL || destination == NULL)
        return;
    for (s32 i = 0; i < count; ++i)
    {
        double angle = source[i].alpha * (2.0 * 3.14159265358979323846 / 65536.0);
        double cosine = cos(angle);
        double sine = sin(angle);
        struct BgAffineDstData *out = &destination[i];
        out->pa = Fixed8_8((source[i].sx / 256.0) * cosine);
        out->pb = Fixed8_8(-(source[i].sx / 256.0) * sine);
        out->pc = Fixed8_8((source[i].sy / 256.0) * sine);
        out->pd = Fixed8_8((source[i].sy / 256.0) * cosine);
        out->dx = source[i].texX - out->pa * source[i].scrX - out->pb * source[i].scrY;
        out->dy = source[i].texY - out->pc * source[i].scrX - out->pd * source[i].scrY;
    }
}

void ObjAffineSet(struct ObjAffineSrcData *source, void *destination, s32 count, s32 offset)
{
    if (source == NULL || destination == NULL || offset <= 0)
        return;
    u8 *out = destination;
    for (s32 i = 0; i < count; ++i)
    {
        double angle = source[i].rotation * (2.0 * 3.14159265358979323846 / 65536.0);
        double cosine = cos(angle);
        double sine = sin(angle);
        s16 matrix[4] = {
            Fixed8_8((source[i].xScale / 256.0) * cosine),
            Fixed8_8(-(source[i].xScale / 256.0) * sine),
            Fixed8_8((source[i].yScale / 256.0) * sine),
            Fixed8_8((source[i].yScale / 256.0) * cosine),
        };
        for (int j = 0; j < 4; ++j)
            memcpy(out + ((size_t)i * 4 + j) * (size_t)offset, &matrix[j], sizeof(matrix[j]));
    }
}

void SoftReset(u32 resetFlags)
{
#ifdef PORT_DIAGNOSTIC
    fprintf(stderr, "BIOS: SoftReset(0x%02X) ends diagnostic run\n", resetFlags);
    Port_ExitCleanly();
#else
    fprintf(stderr, "BIOS: SoftReset(0x%02X) relaunching host\n", resetFlags);
    if (PortReset_Restart() != 0)
        exit(EXIT_FAILURE);
    Port_ExitCleanly();
#endif
}

void RegisterRamReset(u32 resetFlags)
{
    static int warned;
    if (!warned)
    {
        fprintf(stderr, "BIOS: RegisterRamReset(0x%02X) is a safe no-op on PC\n", resetFlags);
        warned = 1;
    }
}

void VBlankIntrWait(void)
{
    PortHost_RunFrame();
}

void IntrWait(u32 discard, u32 flags)
{
    (void)discard;
    (void)flags;
    PortHost_RunFrame();
}

void Halt(void)
{
    PortHost_RunFrame();
}

int MultiBoot(struct MultiBootParam *parameters)
{
    (void)parameters;
    fprintf(stderr, "BIOS: MultiBoot is unavailable on PC\n");
    return -1;
}
