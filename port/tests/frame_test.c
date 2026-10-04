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
#undef main

struct PortSDL portSDL;
struct Main gMain;
IntrFunc gIntrTable[14];

static Uint8 sKeys[SDL_NUM_SCANCODES];
static Uint64 sCounter;
static unsigned sVBlanks;
static int sQuitEvent;
static jmp_buf sExit;

static int PollEvent(SDL_Event *event)
{
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
void Port_ExitCleanly(void) { longjmp(sExit, 1); }
void PortPpu_Render(uint32_t *pixels) { (void)pixels; }

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
    PortHost_RunFrame();
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

    sQuitEvent = 1;
    if (setjmp(sExit) == 0)
    {
        PortHost_RunFrame();
        assert(0 && "SDL_QUIT must exit before the callback");
    }
    assert(sVBlanks == 1002);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
