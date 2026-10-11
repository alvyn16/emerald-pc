#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include <stdio.h>
#define NOMINMAX
#include <windows.h>

#define SDL_MAIN_HANDLED

#include "global.h"
#include "main.h"
#include "gba/io_reg.h"
#include "platform.h"
#include "port_ppu.h"
#include "sdl_loader.h"
#include "speed_menu.h"
#include "port_irq.h"
#undef main

struct PortSDL portSDL;
struct Main gMain;
IntrFunc gIntrTable[14];

static Uint8 sKeys[SDL_NUM_SCANCODES];
static Uint64 sCounter;
static unsigned sVBlanks;
static unsigned sHBlanks;
static unsigned sVCounts;
static unsigned sRenderedLines;
static unsigned sHBlankDma;
static unsigned sVBlankDma;
static int sVBlankDmaReady;
static unsigned sExpectedVCount = 42;
static unsigned sLineVisits[228];
static int sQuitEvent;
static SDL_Keycode sMenuKeys[2];
static unsigned sMenuKeyCount;
static unsigned sMenuKeyIndex;
static int sBreakPoll, sAudioPaused;
static unsigned sAudioPauseCalls, sPauseVBlanks;
static jmp_buf sExit;

static int PollEvent(SDL_Event *event)
{
    if (sBreakPoll && sMenuKeyIndex == 1) { sBreakPoll = 0; return 0; }
    if (sMenuKeyIndex < sMenuKeyCount)
    {
        memset(event, 0, sizeof(*event));
        event->type = SDL_KEYDOWN;
        event->key.keysym.sym = sMenuKeys[sMenuKeyIndex++];
        return 1;
    }
    if (!sQuitEvent)
        return 0;
    sQuitEvent = 0;
    memset(event, 0, sizeof(*event));
    event->type = SDL_QUIT;
    return 1;
}

static const Uint8 *MockGetKeyboardState(int *count)
{
    if (count != NULL)
        *count = SDL_NUM_SCANCODES;
    return sKeys;
}

static Uint64 GetPerformanceFrequency(void) { return 1000000; }
static Uint64 GetPerformanceCounter(void) { return sCounter += 1000; }
static void Delay(Uint32 milliseconds) { if (sAudioPaused) assert(sVBlanks == sPauseVBlanks); sCounter += milliseconds * 1000; }
static void VBlank(void)
{
    assert(REG_VCOUNT == 160);
    assert(REG_DISPSTAT & DISPSTAT_VBLANK);
    assert(sVBlankDmaReady); // DMA precedes the IRQ callback.
    sVBlankDmaReady = 0;
    sVBlanks++;
    gMain.intrCheck |= INTR_FLAG_VBLANK;
}
static void HBlank(void)
{
    assert(REG_VCOUNT < 228);
    assert(REG_VCOUNT == (160 + sHBlanks) % 228);
    assert(!!(REG_DISPSTAT & DISPSTAT_VBLANK) ==
           (REG_VCOUNT >= 160 && REG_VCOUNT < 227));
    assert(REG_DISPSTAT & DISPSTAT_HBLANK);
    sLineVisits[REG_VCOUNT]++;
    sHBlanks++;
}
static void VCount(void)
{
    assert(REG_VCOUNT == sExpectedVCount);
    assert(REG_DISPSTAT & DISPSTAT_VCOUNT);
    sVCounts++;
}
void Port_ExitCleanly(void) { longjmp(sExit, 1); }
void PortPpu_Render(uint32_t *pixels) { (void)pixels; }
void PortPpu_BeginFrame(void) { sVBlankDmaReady = 0; }
void PortPpu_RenderLine(unsigned y, uint32_t *row)
{
    (void)row;
    assert(REG_VCOUNT == y);
    assert(!(REG_DISPSTAT & (DISPSTAT_VBLANK | DISPSTAT_HBLANK)));
    sRenderedLines++;
}
void PortDma_OnHBlank(void) { sHBlankDma++; }
void PortDma_OnVBlank(void) { sVBlankDma++; sVBlankDmaReady = 1; }
void PortAudio_SubmitFrame(void) { assert(!sAudioPaused); }
void PortAudio_SetPaused(int paused) { if (paused != sAudioPaused) sAudioPauseCalls++; sAudioPaused = paused; if (paused) sPauseVBlanks = sVBlanks; }

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);
    void *iwram = VirtualAlloc((void *)0x03000000, 32768,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(iwram == (void *)0x03000000);
    PortIrq_Reset();
    REG_IE = INTR_FLAG_VBLANK;
    REG_IME = 1;
    REG_DISPSTAT = DISPSTAT_VBLANK_INTR;
    portSDL.PollEvent = PollEvent;
    portSDL.GetKeyboardState = MockGetKeyboardState;
    portSDL.GetPerformanceFrequency = GetPerformanceFrequency;
    portSDL.GetPerformanceCounter = GetPerformanceCounter;
    portSDL.Delay = Delay;
    gIntrTable[4] = VBlank;
    Port_AttachRenderer(NULL, NULL);

    sKeys[SDL_SCANCODE_Z] = 1;
    sKeys[SDL_SCANCODE_UP] = 1;
    REG_TM1CNT_H = TIMER_ENABLE;
    PortHost_RunFrame();
    assert(REG_TM1CNT_L != 0);
    assert(REG_KEYINPUT == (KEYS_MASK & ~(A_BUTTON | DPAD_UP)));
    assert(gMain.intrCheck & INTR_FLAG_VBLANK);
    assert(REG_VCOUNT == 0);
    assert(!(REG_DISPSTAT & DISPSTAT_VBLANK));
    assert(sVBlanks == 1);

    memset(sKeys, 0, sizeof(sKeys));
    PortHost_RunFrame();
    assert(REG_KEYINPUT == KEYS_MASK);
    assert(sVBlanks == 2);

    Uint64 start = sCounter;
    LARGE_INTEGER wallStart, wallEnd, wallFrequency;
    QueryPerformanceFrequency(&wallFrequency);
    QueryPerformanceCounter(&wallStart);
    for (int i = 0; i < 1000; ++i)
        PortHost_RunFrame();
    Uint64 expected = 1000000ull * 10000 * 1000 / 597275;
    QueryPerformanceCounter(&wallEnd);
    printf("calendar fixture: 1000 frames %.3f ms (mock SDL, no PPU)\n",
           1000.0 * (wallEnd.QuadPart - wallStart.QuadPart) / wallFrequency.QuadPart);
    Uint64 elapsed = sCounter - start;
    assert(elapsed >= expected - 2000 && elapsed <= expected + 2000);
    assert(sVBlanks == 1002);

    // Confirming with Enter may leave the physical key held for later frames.
    sMenuKeys[0] = SDLK_p;
    sMenuKeys[1] = SDLK_RETURN;
    sMenuKeyCount = 2;
    sBreakPoll = 1;
    sKeys[SDL_SCANCODE_RETURN] = 1;
    PortHost_RunFrame();
    assert(!PortSpeedMenu_IsOpen());
    assert(!sAudioPaused && sAudioPauseCalls == 2);
    assert(REG_KEYINPUT & START_BUTTON);
    PortHost_RunFrame();
    assert(REG_KEYINPUT & START_BUTTON);
    sKeys[SDL_SCANCODE_RETURN] = 0;
    PortHost_RunFrame();
    sKeys[SDL_SCANCODE_RETURN] = 1;
    PortHost_RunFrame();
    assert(!(REG_KEYINPUT & START_BUTTON));

    sQuitEvent = 1;
    if (setjmp(sExit) == 0)
    {
        PortHost_RunFrame();
        assert(0 && "SDL_QUIT must exit before the callback");
    }
    assert(sVBlanks == 1006);
    assert(sRenderedLines == 1006 * 160);
    assert(sHBlankDma == 1006 * 160);
    assert(sVBlankDma == 1006);

    gIntrTable[0] = VCount;
    gIntrTable[3] = HBlank;
    REG_DISPSTAT = DISPSTAT_HBLANK_INTR | DISPSTAT_VCOUNT_INTR | (42 << 8);
    REG_IE = INTR_FLAG_HBLANK | INTR_FLAG_VCOUNT;
    REG_IME = 1;
    PortHost_RunFrame();
    assert(sHBlanks == 228);
    for (unsigned y = 0; y < 228; ++y) assert(sLineVisits[y] == 1);
    assert(sVCounts == 1);
    sExpectedVCount = 227;
    REG_DISPSTAT = DISPSTAT_VCOUNT_INTR | (227 << 8);
    PortHost_RunFrame();
    assert(sVCounts == 2);
    REG_DISPSTAT = DISPSTAT_HBLANK_INTR | DISPSTAT_VCOUNT_INTR | (42 << 8);
    sExpectedVCount = 42;
    REG_IE = 0;
    PortHost_RunFrame();
    assert(sHBlanks == 228 && sVCounts == 2);
    assert(PortIrq_Pending() == (INTR_FLAG_HBLANK | INTR_FLAG_VCOUNT));
    PortIrq_Reset();
    REG_DISPSTAT = DISPSTAT_VBLANK_INTR;
    REG_IE = INTR_FLAG_VBLANK;
    REG_IME = 0;
    gMain.intrCheck = 0;
    PortHost_RunFrame();
    assert(sVBlanks == 1006 && INTR_CHECK == 0 && gMain.intrCheck == 0);
    assert(PortIrq_Pending() == INTR_FLAG_VBLANK);

    SDL_Event speed;
    memset(&speed, 0, sizeof(speed));
    speed.type = SDL_KEYDOWN;
    speed.key.keysym.sym = SDLK_p;
    PortSpeedMenu_HandleEvent(&speed);
    speed.key.keysym.sym = SDLK_DOWN;
    for (unsigned i = 0; i < 3; ++i) PortSpeedMenu_HandleEvent(&speed);
    speed.key.keysym.sym = SDLK_RETURN;
    PortSpeedMenu_HandleEvent(&speed);
    assert(PortSpeedMenu_Multiplier() == 4);
    PortIrq_Reset();
    REG_IE = INTR_FLAG_VBLANK;
    REG_IME = 1;
    PortHost_RunFrame(); // Settle the transition from 1x.
    start = sCounter;
    for (unsigned i = 0; i < 1000; ++i) PortHost_RunFrame();
    elapsed = sCounter - start;
    expected = 1000000ull * 10000 * 1000 / (597275 * 4);
    assert(elapsed >= expected - 2000 && elapsed <= expected + 2000);
    VirtualFree(io, 0, MEM_RELEASE);
    VirtualFree(iwram, 0, MEM_RELEASE);
    return 0;
}
