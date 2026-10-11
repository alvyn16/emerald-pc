#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <setjmp.h>
#define NOMINMAX
#include <windows.h>

#include "gba/types.h"
#include "gba/multiboot.h"
#include "gba/syscall.h"
#include "gba/io_reg.h"
#include "gba/defines.h"
#include "port_irq.h"
#include "port_bios.h"

static int frames;
static unsigned eventFrame;
static u16 eventFlags;
static unsigned closeFrame;
static jmp_buf closeJump;
void (*gIntrTable[14])(void);
void PortHost_RunFrame(void)
{
    ++frames;
    if (closeFrame && frames == (int)closeFrame)
        longjmp(closeJump, 1); // Model the frame pump's SDL close path.
    if (frames == (int)eventFrame)
        PortIrq_Raise(eventFlags);
    PortIrq_Dispatch();
}
int PortReset_Restart(void) { return 0; }
void Port_ExitCleanly(void) { }

extern s32 DivArm(s32 denominator, s32 numerator);

int main(void)
{
    assert(VirtualAlloc((void *)0x03000000, 32768, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    assert(VirtualAlloc((void *)REG_BASE, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    u16 fill = 0x1234;
    u16 filled[4] = {0};
    CpuSet(&fill, filled, 0x01000004);
    for (int i = 0; i < 4; ++i)
        assert(filled[i] == fill);

    u32 sourceWords[8] = {1, 2, 3, 4, 5, 6, 7, 8};
    u32 copiedWords[8] = {0};
    CpuSet(sourceWords, copiedWords, 0x04000008);
    assert(memcmp(sourceWords, copiedWords, sizeof(sourceWords)) == 0);

    // CpuFastSet transfers complete 32-byte blocks, even for count=1/9.
    u32 blocks[24], blockCopy[24];
    for (unsigned i = 0; i < 24; ++i) blocks[i] = 0x12340000 + i;
    memset(blockCopy, 0xa5, sizeof(blockCopy));
    CpuFastSet(blocks, blockCopy, 1);
    assert(memcmp(blocks, blockCopy, 32) == 0 && blockCopy[8] == 0xa5a5a5a5);
    CpuFastSet(blocks, blockCopy, 9);
    assert(memcmp(blocks, blockCopy, 64) == 0 && blockCopy[16] == 0xa5a5a5a5);
    CpuFastSet(blocks, blockCopy, 0x01000009);
    for (unsigned i = 0; i < 16; ++i) assert(blockCopy[i] == blocks[0]);
    CpuFastSet(NULL, blockCopy, 0);
    assert(blockCopy[16] == 0xa5a5a5a5);
    // Word transfers ignore low address bits (LDM/STM alignment).
    CpuFastSet((u8 *)blocks + 1, (u8 *)blockCopy + 3, 8);
    assert(memcmp(blocks, blockCopy, 32) == 0);
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

    // Raw tile data must not be accepted as an LZ stream or overwrite output.
    // Trainer back pictures use the copy consumer instead of this API.
    const u32 rawTiles[2] = {0, 0};
    memset(unpacked, 0xa5, sizeof(unpacked));
    LZ77UnCompWram(rawTiles, unpacked);
    LZ77UnCompVram(rawTiles, unpacked);
    for (unsigned i = 0; i < sizeof(unpacked); ++i)
        assert(unpacked[i] == 0xa5);

    assert(Div(-13, 4) == -3);
    assert(DivArm(4, -13) == -3);
    assert(Sqrt(65535) == 255);
    assert(Sqrt(65536) == 256);
    assert(ArcTan2(1, 0) == 0);
    assert(ArcTan2(0, 1) == 16384);
    assert(Div(INT_MIN, -1) == INT_MIN);
    assert(Div(INT_MIN, 1) == INT_MIN);
    assert(Div(INT_MAX, -2) == -1073741823);
    assert(Div(13, -4) == -3 && Div(-13, -4) == 3);
    assert(Div(1, 0) == 0); // Explicit host safety policy, not BIOS accuracy.
    for (u32 root = 1; root <= 65535; ++root)
    {
        u32 square = root * root;
        assert(Sqrt(square) == root && Sqrt(square - 1) == root - 1);
    }
    assert(Sqrt(UINT32_MAX) == 65535 && Sqrt(0) == 0);
    // Numerical vectors evaluated against the open mGBA HLE reference.
    const struct { s16 x, y; u16 angle; } angles[] = {
        {0, 0, 0}, {-1, 0, 32768}, {0, -1, 49152},
        {3, 1, 3355}, {1, 3, 13029}, {7, 2, 2902},
        {-3, 1, 29412}, {3, -1, 62180}, {-3, -1, 36123},
        {1, 1, 8192}, {-1, -1, 40960},
        {32767, 32766, 8191}, {-32768, 32767, 24576},
    };
    for (unsigned i = 0; i < sizeof(angles) / sizeof(angles[0]); ++i)
        assert(ArcTan2(angles[i].x, angles[i].y) == angles[i].angle);

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
    obj.rotation = 0x20ff; // Low angle byte is ignored.
    ObjAffineSet(&obj, objResult, 1, 2);
    assert(objResult[0] == 181 && objResult[1] == -182);
    assert(objResult[2] == 181 && objResult[3] == 181);
    obj.rotation = 0x4000;
    obj.xScale = INT16_MIN;
    obj.yScale = -256;
    s16 strided[16];
    for (unsigned i = 0; i < 16; ++i) strided[i] = 1234;
    ObjAffineSet(&obj, strided, 1, 8);
    assert(strided[0] == 0 && strided[4] == INT16_MIN);
    assert(strided[8] == -256 && strided[12] == 0);
    assert(strided[1] == 1234 && strided[15] == 1234);
    ObjAffineSet(&obj, strided, 0, 8);
    assert(strided[1] == 1234);
    bg.alpha = 0x2001;
    bg.texX = INT32_MIN; bg.texY = INT32_MAX;
    bg.scrX = 120; bg.scrY = -80;
    BgAffineSet(&bg, &bgResult, 1);
    assert(bgResult.pa == 181 && bgResult.pb == -182);
    assert(bgResult.pc == 181 && bgResult.pd == 181);
    assert((u32)bgResult.dx == (u32)INT32_MIN - 36280u);
    assert((u32)bgResult.dy == (u32)INT32_MAX - 7240u);

    PortIrq_Reset();
    REG_IE = INTR_FLAG_VBLANK;
    eventFrame = 1;
    eventFlags = INTR_FLAG_VBLANK;
    VBlankIntrWait();
    assert(frames == 1);
    assert(REG_IME == 1 && !(INTR_CHECK & INTR_FLAG_VBLANK));

    INTR_CHECK = INTR_FLAG_VBLANK | INTR_FLAG_TIMER0;
    IntrWait(0, INTR_FLAG_TIMER0);
    assert(frames == 1 && INTR_CHECK == INTR_FLAG_VBLANK);
    eventFrame = 3;
    IntrWait(1, INTR_FLAG_VBLANK);
    assert(frames == 3 && INTR_CHECK == 0);

    // An enabled but different IRQ cannot satisfy the requested wait.
    PortIrq_Reset();
    frames = 0;
    eventFrame = 1;
    eventFlags = INTR_FLAG_TIMER0;
    REG_IE = INTR_FLAG_TIMER0 | INTR_FLAG_VBLANK;
    closeFrame = 3;
    if (setjmp(closeJump) == 0)
    {
        IntrWait(1, INTR_FLAG_VBLANK);
        assert(0 && "Wrong IRQ satisfied IntrWait");
    }
    assert(frames == 3 && INTR_CHECK == INTR_FLAG_TIMER0);

    // A requested source with IE=0 stays pending and does not become a BIOS flag.
    PortIrq_Reset();
    frames = 0;
    REG_IE = 0;
    eventFlags = INTR_FLAG_VBLANK;
    if (setjmp(closeJump) == 0)
    {
        IntrWait(1, INTR_FLAG_VBLANK);
        assert(0 && "Masked IRQ satisfied IntrWait");
    }
    assert(frames == 3 && INTR_CHECK == 0 && PortIrq_Pending() == INTR_FLAG_VBLANK);

    // Halt wakes with IME=0; even an IRQ acknowledged in the pump wakes it.
    PortIrq_Reset();
    frames = 0;
    REG_IE = INTR_FLAG_VBLANK;
    REG_IME = 0;
    eventFrame = 2;
    closeFrame = 0;
    Halt();
    assert(frames == 2 && INTR_CHECK == 0 && REG_IME == 0);
    Halt(); // Existing enabled pending request returns immediately.
    assert(frames == 2);
    PortIrq_Reset();
    frames = 0;
    REG_IME = 1;
    Halt();
    assert(frames == 2 && INTR_CHECK == INTR_FLAG_VBLANK && PortIrq_Pending() == 0);
    VirtualFree((void *)REG_BASE, 0, MEM_RELEASE);
    VirtualFree((void *)0x03000000, 0, MEM_RELEASE);
    return 0;
}
