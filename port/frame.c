#include <stdint.h>

#include <SDL.h>

#include "global.h"
#include "main.h"
#include "gba/io_reg.h"
#include "platform.h"
#include "sdl_loader.h"

/* gIntrTableTemplate in upstream main.c puts VBlank at index four. */
#define VBLANK_INTR_INDEX 4
#define FRAME_RATE_NUMERATOR 597275u
#define FRAME_RATE_DENOMINATOR 10000u

static SDL_Renderer *sRenderer;
static Uint64 sNextFrameTick;
static Uint64 sFrameRemainder;

void Port_AttachRenderer(SDL_Renderer *renderer)
{
    sRenderer = renderer;
    sNextFrameTick = 0;
    sFrameRemainder = 0;
}

static void UpdateKeyInput(void)
{
    const Uint8 *keys = portSDL.GetKeyboardState(NULL);
    u16 pressed = 0;

    if (keys[SDL_SCANCODE_Z]) pressed |= A_BUTTON;
    if (keys[SDL_SCANCODE_X]) pressed |= B_BUTTON;
    if (keys[SDL_SCANCODE_BACKSPACE]) pressed |= SELECT_BUTTON;
    if (keys[SDL_SCANCODE_RETURN]) pressed |= START_BUTTON;
    if (keys[SDL_SCANCODE_RIGHT]) pressed |= DPAD_RIGHT;
    if (keys[SDL_SCANCODE_LEFT]) pressed |= DPAD_LEFT;
    if (keys[SDL_SCANCODE_UP]) pressed |= DPAD_UP;
    if (keys[SDL_SCANCODE_DOWN]) pressed |= DPAD_DOWN;
    if (keys[SDL_SCANCODE_S]) pressed |= R_BUTTON;
    if (keys[SDL_SCANCODE_A]) pressed |= L_BUTTON;

    REG_KEYINPUT = KEYS_MASK & ~pressed;
}

static void WaitForFrameDeadline(void)
{
    const Uint64 frequency = portSDL.GetPerformanceFrequency();
    const Uint64 scaled = frequency * FRAME_RATE_DENOMINATOR;
    const Uint64 wholeTicks = scaled / FRAME_RATE_NUMERATOR;
    Uint64 now = portSDL.GetPerformanceCounter();

    if (sNextFrameTick == 0 || now > sNextFrameTick + wholeTicks)
    {
        sNextFrameTick = now;
        sFrameRemainder = 0;
    }

    sNextFrameTick += wholeTicks;
    sFrameRemainder += scaled % FRAME_RATE_NUMERATOR;
    if (sFrameRemainder >= FRAME_RATE_NUMERATOR)
    {
        sNextFrameTick++;
        sFrameRemainder -= FRAME_RATE_NUMERATOR;
    }

    while ((now = portSDL.GetPerformanceCounter()) < sNextFrameTick)
    {
        const Uint64 remaining = sNextFrameTick - now;
        const Uint64 milliseconds = remaining * 1000 / frequency;
        if (milliseconds > 2)
            portSDL.Delay((Uint32)(milliseconds - 1));
    }
}

void PortHost_RunFrame(void)
{
    SDL_Event event;
    while (portSDL.PollEvent(&event))
    {
        if (event.type == SDL_QUIT ||
            (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE))
            Port_ExitCleanly();
    }
    UpdateKeyInput();
    WaitForFrameDeadline();

    if (gIntrTable[VBLANK_INTR_INDEX] != NULL)
        gIntrTable[VBLANK_INTR_INDEX]();
    gMain.intrCheck |= INTR_FLAG_VBLANK;

    if (sRenderer != NULL)
    {
        portSDL.SetRenderDrawColor(sRenderer, 0, 0, 0, 255);
        portSDL.RenderClear(sRenderer);
        portSDL.RenderPresent(sRenderer);
    }
}
