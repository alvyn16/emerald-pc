#include <stdint.h>

#include <SDL.h>

#include "global.h"
#include "main.h"
#include "gba/io_reg.h"
#include "platform.h"
#include "port_ppu.h"
#include "port_dma.h"
#include "sdl_loader.h"
#include "speed_menu.h"
#include "port_timer.h"
#include "port_audio.h"
#include "port_irq.h"
#include "port_input.h"
#ifdef PORT_DIAGNOSTIC
#include <stdio.h>
#include "battle.h"
#include "input_script.h"
#endif

#define FRAME_RATE_NUMERATOR 597275u
#define FRAME_RATE_DENOMINATOR 10000u

static SDL_Renderer *sRenderer;
static SDL_Texture *sTexture;
static uint32_t sPixels[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];
static Uint64 sNextFrameTick;
static Uint64 sFrameRemainder;
static Uint64 sTimerLastTick;
static Uint64 sTimerCycleRemainder;
#ifdef PORT_DIAGNOSTIC
static unsigned sDiagnosticFrame;
#endif

void Port_AttachRenderer(SDL_Renderer *renderer, SDL_Texture *texture)
{
    sRenderer = renderer;
    sTexture = texture;
    sNextFrameTick = 0;
    sFrameRemainder = 0;
    sTimerLastTick = 0;
    sTimerCycleRemainder = 0;
    PortTimer_Reset();
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
    unsigned pressed = PortInput_ReadButtons();

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
    const Uint64 divisor = FRAME_RATE_NUMERATOR * (Uint64)PortSpeedMenu_Multiplier();
    const Uint64 wholeTicks = scaled / divisor;
    Uint64 now = portSDL.GetPerformanceCounter();

    if (sNextFrameTick == 0 || now > sNextFrameTick + wholeTicks)
    {
        sNextFrameTick = now;
        sFrameRemainder = 0;
        sTimerLastTick = 0;
    }

    sNextFrameTick += wholeTicks;
    sFrameRemainder += scaled % divisor;
    if (sFrameRemainder >= divisor)
    {
        sNextFrameTick++;
        sFrameRemainder -= divisor;
    }

    while ((now = portSDL.GetPerformanceCounter()) < sNextFrameTick)
    {
        const Uint64 remaining = sNextFrameTick - now;
        const Uint64 milliseconds = remaining * 1000 / frequency;
        if (milliseconds > 2)
            portSDL.Delay((Uint32)(milliseconds - 1));
    }
}

static void PollHostEvents(void)
{
    SDL_Event event;
    while (portSDL.PollEvent(&event))
    {
        if (event.type == SDL_QUIT ||
            (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE))
            Port_ExitCleanly();
        PortSpeedMenu_HandleEvent(&event);
        PortInput_HandleEvent(&event);
        PortAudio_SetPaused(PortSpeedMenu_IsOpen());
        if (PortSpeedMenu_IsOpen())
            PortInput_SuppressMenuKeys();
    }
}

static void PresentFrame(int render)
{
    if (sRenderer == NULL || sTexture == NULL)
        return;

    if (render)
        PortPpu_Render(sPixels);
    PortSpeedMenu_Draw(sPixels);
    portSDL.UpdateTexture(sTexture, NULL, sPixels, PORT_SCREEN_WIDTH * sizeof(uint32_t));
    portSDL.SetRenderDrawColor(sRenderer, 0, 0, 0, 255);
    portSDL.RenderClear(sRenderer);
    portSDL.RenderCopy(sRenderer, sTexture, NULL, NULL);
    portSDL.RenderPresent(sRenderer);
}

void PortHost_RunFrame(void)
{
    SetVideoLine(0, 0);
    PollHostEvents();
    if (PortSpeedMenu_IsOpen())
    {
        REG_KEYINPUT = KEYS_MASK;
        while (PortSpeedMenu_IsOpen())
        {
            PresentFrame(1);
            portSDL.Delay(16);
            PollHostEvents();
        }
        sNextFrameTick = 0;
        sFrameRemainder = 0;
    }
    else
    {
        UpdateKeyInput();
    }
#ifdef PORT_DIAGNOSTIC
    if (!PortInputScript_Fast())
#endif
        WaitForFrameDeadline();
#ifdef PORT_DIAGNOSTIC
    const uint32_t frameCycles = PORT_CYCLES_PER_FRAME;
#else
    // A faster display rate also advances the emulated clock faster.
    // Retain the small host timing variation used by the game's RNG seed.
    const Uint64 now = portSDL.GetPerformanceCounter();
    const Uint64 frequency = portSDL.GetPerformanceFrequency();
    const Uint64 multiplier = PortSpeedMenu_Multiplier();
    Uint64 elapsed = sTimerLastTick == 0 ? frequency * FRAME_RATE_DENOMINATOR / (FRAME_RATE_NUMERATOR * multiplier) : now - sTimerLastTick;
    const Uint64 maxElapsed = 2 * frequency * FRAME_RATE_DENOMINATOR / (FRAME_RATE_NUMERATOR * multiplier);
    if (elapsed > maxElapsed)
        elapsed = maxElapsed;
    sTimerLastTick = now;
    const Uint64 scaled = elapsed * 16777216u * multiplier + sTimerCycleRemainder;
    const uint32_t frameCycles = (uint32_t)(scaled / frequency);
    sTimerCycleRemainder = scaled % frequency;
#endif
    // A cooperative frame starts at VBlank, where Emerald commits OAM/VRAM,
    // then traverses every hidden and visible line before returning to main.
    for (unsigned step = 0; step < 228; ++step)
    {
        const unsigned y = (160 + step) % 228;
        SetVideoLine(y, y >= 160 && y < 227);
        if (y == 160)
        {
            PortDma_OnVBlank();
            if (REG_DISPSTAT & DISPSTAT_VBLANK_INTR)
                PortIrq_Raise(INTR_FLAG_VBLANK);
        }
        if ((REG_DISPSTAT & (DISPSTAT_VCOUNT | DISPSTAT_VCOUNT_INTR)) ==
                (DISPSTAT_VCOUNT | DISPSTAT_VCOUNT_INTR))
            PortIrq_Raise(INTR_FLAG_VCOUNT);
        PortIrq_Dispatch();
        if (y == 160)
            PortAudio_SubmitFrame();
        if (y == 0)
            PortPpu_BeginFrame();
        if (y < PORT_SCREEN_HEIGHT)
            PortPpu_RenderLine(y, sPixels + y * PORT_SCREEN_WIDTH);
        // Device time advances at phase boundaries; native instructions do
        // not have ARM cycle costs. Distribute host variation without losing
        // a cycle; diagnostics always total exactly 280896 cycles/frame.
        const uint64_t startCycle = (uint64_t)step * 1232;
        const uint32_t drawCycles = frameCycles * (startCycle + 1006) / PORT_CYCLES_PER_FRAME
                                 - frameCycles * startCycle / PORT_CYCLES_PER_FRAME;
        const uint32_t blankCycles = frameCycles * (startCycle + 1232) / PORT_CYCLES_PER_FRAME
                                  - frameCycles * (startCycle + 1006) / PORT_CYCLES_PER_FRAME;
        PortTimer_Advance(drawCycles);
        REG_DISPSTAT |= DISPSTAT_HBLANK;
        // HBlank status/IRQ runs on all lines; HBlank DMA only on visible ones.
        if (y < PORT_SCREEN_HEIGHT)
            PortDma_OnHBlank();
        if (REG_DISPSTAT & DISPSTAT_HBLANK_INTR)
            PortIrq_Raise(INTR_FLAG_HBLANK);
        PortIrq_Dispatch();
        PortTimer_Advance(blankCycles);
        PortIrq_Dispatch();
    }
    PresentFrame(0);
    SetVideoLine(0, 0);
#ifdef PORT_DIAGNOSTIC
    // Metadata only: leave ROM, save and resource contents out of diagnostics.
    // A stopped sequence of these lines identifies the last completed frame.
    if (sDiagnosticFrame % 600 == 0)
    {
        const struct WarpData *map = gSaveBlock1Ptr ? &gSaveBlock1Ptr->location : NULL;
        fprintf(stderr, "PC diagnostic: frame=%u map=%d.%d callbacks=%p/%p "
                "battle=0x%08lx outcome=%u IE=%04x IME=%04x DISPSTAT=%04x\n",
                sDiagnosticFrame, map ? map->mapGroup : -1, map ? map->mapNum : -1,
                (void *)gMain.callback1, (void *)gMain.callback2,
                (unsigned long)gBattleTypeFlags, gBattleOutcome,
                REG_IE, REG_IME, REG_DISPSTAT);
        fflush(stderr);
    }
    if (PortInputScript_StopFrame() != 0 &&
        sDiagnosticFrame >= PortInputScript_StopFrame())
        Port_ExitCleanly();
#endif
}
