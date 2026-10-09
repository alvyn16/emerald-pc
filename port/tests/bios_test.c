#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "gba/types.h"
#include "gba/multiboot.h"
#include "gba/syscall.h"

static int frames;
void PortHost_RunFrame(void) { frames++; }
int PortReset_Restart(void) { return 0; }
void Port_ExitCleanly(void) { }

extern s32 DivArm(s32 denominator, s32 numerator);

int main(void)
{
    u16 fill = 0x1234;
    u16 filled[4] = {0};
    CpuSet(&fill, filled, 0x01000004);
    for (int i = 0; i < 4; ++i)
        assert(filled[i] == fill);

    u32 sourceWords[8] = {1, 2, 3, 4, 5, 6, 7, 8};
    u32 copiedWords[8] = {0};
    CpuSet(sourceWords, copiedWords, 0x04000008);
    assert(memcmp(sourceWords, copiedWords, sizeof(sourceWords)) == 0);
    memset(copiedWords, 0, sizeof(copiedWords));
    CpuFastSet(sourceWords, copiedWords, 8);
    assert(memcmp(sourceWords, copiedWords, sizeof(sourceWords)) == 0);

    const u8 lz[] = {0x10, 6, 0, 0, 0x20, 'A', 'B', 0x10, 1};
    const u8 rl[] = {0x30, 5, 0, 0, 0x82, 'X'};
    u8 unpacked[8] = {0};
    LZ77UnCompWram((const u32 *)lz, unpacked);
    assert(memcmp(unpacked, "ABABAB", 6) == 0);
    memset(unpacked, 0, sizeof(unpacked));
    LZ77UnCompVram((const u32 *)lz, unpacked);
    assert(memcmp(unpacked, "ABABAB", 6) == 0);
    RLUnCompWram((const u32 *)rl, unpacked);
    assert(memcmp(unpacked, "XXXXX", 5) == 0);
    memset(unpacked, 0, sizeof(unpacked));
    RLUnCompVram((const u32 *)rl, unpacked);
    assert(memcmp(unpacked, "XXXXX", 5) == 0);

    assert(Div(-13, 4) == -3);
    assert(DivArm(4, -13) == -3);
    assert(Sqrt(65535) == 255);
    assert(Sqrt(65536) == 256);
    assert(ArcTan2(1, 0) == 0);
    assert(ArcTan2(0, 1) == 16384);

    struct BgAffineSrcData bg = {.texX = 0, .texY = 0, .scrX = 0, .scrY = 0,
                                 .sx = 256, .sy = 256, .alpha = 0};
    struct BgAffineDstData bgResult = {0};
    BgAffineSet(&bg, &bgResult, 1);
    assert(bgResult.pa == 256 && bgResult.pb == 0);
    assert(bgResult.pc == 0 && bgResult.pd == 256);

    struct ObjAffineSrcData obj = {.xScale = 256, .yScale = 256, .rotation = 0};
    s16 objResult[4] = {0};
    ObjAffineSet(&obj, objResult, 1, sizeof(s16));
    assert(objResult[0] == 256 && objResult[1] == 0);
    assert(objResult[2] == 0 && objResult[3] == 256);

    VBlankIntrWait();
    assert(frames == 1);
    return 0;
}
