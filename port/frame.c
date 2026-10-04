#include <stdint.h>

#include <SDL.h>

#include "global.h"
#include "main.h"
#include "gba/io_reg.h"
#include "platform.h"
#include "port_ppu.h"
#include "sdl_loader.h"
#ifdef PORT_DIAGNOSTIC
#include "input_script.h"
#endif

/* gIntrTableTemplate in upstream main.c puts VBlank at index four. */
#define VBLANK_INTR_INDEX 4
#define FRAME_RATE_NUMERATOR 597275u
#define FRAME_RATE_DENOMINATOR 10000u

static SDL_Renderer *sRenderer;
static SDL_Texture *sTexture;
static uint32_t sPixels[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];
static Uint64 sNextFrameTick;
static Uint64 sFrameRemainder;
#ifdef PORT_DIAGNOSTIC
static unsigned sDiagnosticFrame;
#endif

void Port_AttachRenderer(SDL_Renderer *renderer, SDL_Texture *texture)
{
    sRenderer = renderer;
    sTexture = texture;
    sNextFrameTick = 0;
    sFrameRemainder = 0;
}

static void SetVideoLine(unsigned line, int vblank)
{
    uint16_t status = REG_DISPSTAT;
    status &= ~(DISPSTAT_VBLANK | DISPSTAT_HBLANK | DISPSTAT_VCOUNT);
    if (vblank)
        status |= DISPSTAT_VBLANK;
    if ((status >> 8) == line)
        status |= DISPSTAT_VCOUNT;
    REG_VCOUNT = line;
    REG_DISPSTAT = status;
}

static void UpdateKeyInput(void)
{
    const Uint8 *keys = portSDL.GetKeyboardState(NULL);
    unsigned pressed = 0;

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

#ifdef PORT_DIAGNOSTIC
    if (PortInputScript_GetPressed(++sDiagnosticFrame, &pressed))
        pressed &= KEYS_MASK;
#endif
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
    SetVideoLine(0, 0);
    SDL_Event event;
    while (portSDL.PollEvent(&event))
    {
        if (event.type == SDL_QUIT ||
            (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE))
            Port_ExitCleanly();
    }
    UpdateKeyInput();
#ifdef PORT_DIAGNOSTIC
    if (!PortInputScript_Fast())
#endif
        WaitForFrameDeadline();
    SetVideoLine(160, 1);

    if (gIntrTable[VBLANK_INTR_INDEX] != NULL)
        gIntrTable[VBLANK_INTR_INDEX]();
    gMain.intrCheck |= INTR_FLAG_VBLANK;

    if (sRenderer != NULL && sTexture != NULL)
    {
        PortPpu_Render(sPixels);
        portSDL.UpdateTexture(sTexture, NULL, sPixels, PORT_SCREEN_WIDTH * sizeof(uint32_t));
        portSDL.SetRenderDrawColor(sRenderer, 0, 0, 0, 255);
        portSDL.RenderClear(sRenderer);
        portSDL.RenderCopy(sRenderer, sTexture, NULL, NULL);
        portSDL.RenderPresent(sRenderer);
    }
    SetVideoLine(0, 0);
#ifdef PORT_DIAGNOSTIC
    if (PortInputScript_StopFrame() != 0 &&
        sDiagnosticFrame >= PortInputScript_StopFrame())
        Port_ExitCleanly();
#endif
}
