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
#include "port_irq.h"
#include "port_bios.h"
#include "port_ram_reset.h"
#include "gba/io_reg.h"
#include "gba/defines.h"

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
    // ARM word block transfers ignore the low two address bits. Halfword
    // callers retain the documented aligned-address contract.
    if (unitSize == 4)
    {
        from = (const u8 *)((uintptr_t)source & ~(uintptr_t)3);
        to = (u8 *)((uintptr_t)destination & ~(uintptr_t)3);
    }
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
    u32 count = control & BIOS_COUNT_MASK;
    CopyUnits(source, destination, (count + 7u) & ~7u, 4,
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

static s32 FloorShift(int64_t value, unsigned bits)
{
    int64_t divisor = (int64_t)1 << bits;
    return (s32)(value >= 0 ? value / divisor : -((-value + divisor - 1) / divisor));
}

static s32 FixedArcTangent(s32 tangent)
{
    // Evaluate the documented fixed-point approximation in Horner form.
    // Coefficients are numeric facts; this evaluator is host code of our own.
    static const s32 coefficients[] = {169, 912, 2332, 4022, 5802, 8321, 13905, 41721};
    s32 square = -FloorShift((int64_t)tangent * tangent, 14);
    s32 polynomial = coefficients[0];
    for (unsigned i = 1; i < sizeof(coefficients) / sizeof(coefficients[0]); ++i)
        polynomial = FloorShift((int64_t)polynomial * square, 14) + coefficients[i];
    return FloorShift((int64_t)tangent * polynomial, 16);
}

u16 ArcTan2(s16 x, s16 y)
{
    s32 horizontal = x, vertical = y;
    if (!vertical) return horizontal < 0 ? 0x8000 : 0;
    if (!horizontal) return vertical < 0 ? 0xc000 : 0x4000;
    if (abs(horizontal) >= abs(vertical))
        return (u16)(FixedArcTangent(vertical * 16384 / horizontal)
                     + (horizontal < 0 ? 0x8000 : 0));
    return (u16)((vertical < 0 ? 0xc000 : 0x4000)
                 - FixedArcTangent(horizontal * 16384 / vertical));
}

static s32 Sine14(unsigned phase)
{
    // Generate mathematical samples; no BIOS table or ROM bytes are used.
    phase &= 255;
    if (!(phase & 63))
        return phase == 64 ? 16384 : phase == 192 ? -16384 : 0;
    return (s32)lround(sin(phase * (2.0 * 3.14159265358979323846 / 256.0)) * 16384.0);
}

static void AffineMatrix(s16 sx, s16 sy, u16 angle, s16 matrix[4])
{
    unsigned phase = angle >> 8;
    s32 sine = Sine14(phase), cosine = Sine14(phase + 64);
    const int64_t products[4] = {
        (int64_t)sx * cosine, -(int64_t)sx * sine,
        (int64_t)sy * sine, (int64_t)sy * cosine,
    };
    for (unsigned i = 0; i < 4; ++i)
        matrix[i] = (s16)(u16)FloorShift(products[i], 14);
}

void BgAffineSet(struct BgAffineSrcData *source, struct BgAffineDstData *destination, s32 count)
{
    if (source == NULL || destination == NULL)
        return;
    for (s32 i = 0; i < count; ++i)
    {
        s16 matrix[4];
        AffineMatrix(source[i].sx, source[i].sy, source[i].alpha, matrix);
        struct BgAffineDstData *out = &destination[i];
        out->pa = matrix[0]; out->pb = matrix[1];
        out->pc = matrix[2]; out->pd = matrix[3];
        // Unsigned subtraction defines the 32-bit wrap even at extrema.
        out->dx = (s32)((u32)source[i].texX - (u32)(out->pa * source[i].scrX)
                        - (u32)(out->pb * source[i].scrY));
        out->dy = (s32)((u32)source[i].texY - (u32)(out->pc * source[i].scrX)
                        - (u32)(out->pd * source[i].scrY));
    }
}

void ObjAffineSet(struct ObjAffineSrcData *source, void *destination, s32 count, s32 offset)
{
    if (source == NULL || destination == NULL || offset < 0)
        return;
    u8 *out = destination;
    for (s32 i = 0; i < count; ++i)
    {
        s16 matrix[4];
        AffineMatrix(source[i].xScale, source[i].yScale, source[i].rotation, matrix);
        for (unsigned j = 0; j < 4; ++j)
        {
            memcpy(out, &matrix[j], sizeof(matrix[j]));
            out += offset;
        }
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
    PortRamReset(resetFlags);
}

void VBlankIntrWait(void)
{
    IntrWait(1, INTR_FLAG_VBLANK);
}

void IntrWait(u32 discard, u32 flags)
{
    const u16 mask = (u16)flags;
    REG_IME = 1;
    if (discard)
        INTR_CHECK &= ~mask;
    while (!(INTR_CHECK & mask))
        PortHost_RunFrame();
    INTR_CHECK &= ~mask;
}

void Halt(void)
{
    const uint64_t wake = PortIrq_WakeCounter();
    while (!(PortIrq_Pending() & REG_IE) && PortIrq_WakeCounter() == wake)
        PortHost_RunFrame();
}

int MultiBoot(struct MultiBootParam *parameters)
{
    (void)parameters;
    fprintf(stderr, "BIOS: MultiBoot is unavailable on PC\n");
    return -1;
}
