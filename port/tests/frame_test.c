#include <assert.h>
#include <setjmp.h>
#include <string.h>
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
static int sQuitEvent;
static SDL_Keycode sMenuKeys[2];
static unsigned sMenuKeyCount;
static unsigned sMenuKeyIndex;
static jmp_buf sExit;

static int PollEvent(SDL_Event *event)
{
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
static void Delay(Uint32 milliseconds) { sCounter += milliseconds * 1000; }
static void VBlank(void)
{
    assert(REG_VCOUNT == 160);
    assert(REG_DISPSTAT & DISPSTAT_VBLANK);
    sVBlanks++;
}
static void HBlank(void)
{
    assert(REG_VCOUNT < 160);
    assert(REG_DISPSTAT & DISPSTAT_HBLANK);
    sHBlanks++;
}
static void VCount(void)
{
    assert(REG_VCOUNT == 42);
    assert(REG_DISPSTAT & DISPSTAT_VCOUNT);
    sVCounts++;
}
void Port_ExitCleanly(void) { longjmp(sExit, 1); }
void PortPpu_Render(uint32_t *pixels) { (void)pixels; }
void PortPpu_BeginFrame(void) { }
void PortPpu_RenderLine(unsigned y, uint32_t *row)
{
    (void)row;
    assert(REG_VCOUNT == y);
    sRenderedLines++;
}
void PortDma_OnHBlank(void) { sHBlankDma++; }
void PortDma_OnVBlank(void) { sVBlankDma++; }
void PortAudio_SubmitFrame(void) { }

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096,
                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000);
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
    for (int i = 0; i < 1000; ++i)
        PortHost_RunFrame();
    Uint64 expected = 1000000ull * 10000 * 1000 / 597275;
    Uint64 elapsed = sCounter - start;
    assert(elapsed >= expected - 2000 && elapsed <= expected + 2000);
    assert(sVBlanks == 1002);

    // Confirming with Enter may leave the physical key held for later frames.
    sMenuKeys[0] = SDLK_p;
    sMenuKeys[1] = SDLK_RETURN;
    sMenuKeyCount = 2;
    sKeys[SDL_SCANCODE_RETURN] = 1;
    PortHost_RunFrame();
    assert(!PortSpeedMenu_IsOpen());
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
    assert(sHBlanks == 160);
    assert(sVCounts == 1);
    REG_IE = 0;
    PortHost_RunFrame();
    assert(sHBlanks == 160 && sVCounts == 1);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
