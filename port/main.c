#include <stdio.h>
#include <stdlib.h>

#define SDL_MAIN_HANDLED
#include <SDL.h>
#undef main

#include "gba_memory.h"
#include "host_flash.h"
#include "port_audio.h"
#include "platform.h"
#include "sdl_loader.h"
#ifdef PORT_DIAGNOSTIC
#include "input_script.h"
#endif

/* Entry point provided by the user's ignored pokeemerald checkout. */
extern void AgbMain(void);

static SDL_Window *sWindow;
static SDL_Renderer *sRenderer;
static SDL_Texture *sTexture;

void Port_ExitCleanly(void)
{
    fprintf(stderr, "PC: window closed; exiting cleanly\n");
    Port_AttachRenderer(NULL, NULL);
    PortFlash_Close();
    PortAudio_Shutdown();
    portSDL.DestroyTexture(sTexture);
    portSDL.DestroyRenderer(sRenderer);
    portSDL.DestroyWindow(sWindow);
    portSDL.Quit();
    Port_FreeGbaMemory();
    exit(EXIT_SUCCESS);
}

int main(void)
{
#ifdef PORT_DIAGNOSTIC
    const char *windowTitle = "emerald-pc [DIAGNOSTIC - TEST ONLY]";
    fprintf(stderr, "PC: DIAGNOSTIC build; scripted input may be active\n");
    if (PortInputScript_Init() != 0)
        return 1;
#else
    const char *windowTitle = "emerald-pc";
    fprintf(stderr, "PC: normal game build; keyboard input only\n");
#endif
    if (Port_InitGbaMemory() != 0)
        return 1;
    if (Port_LoadGbaRom() != 0)
    {
        Port_FreeGbaMemory();
        return 1;
    }

    if (Port_LoadSDL2() != 0)
    {
        Port_FreeGbaMemory();
        return 1;
    }
    portSDL.SetMainReady();
    if (portSDL.Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_TIMER) != 0)
    {
        fprintf(stderr, "SDL_Init failed: %s\n", portSDL.GetError());
        Port_FreeGbaMemory();
        return 1;
    }

    SDL_Window *window = portSDL.CreateWindow(windowTitle,
                                         SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                         240 * 4, 160 * 4, SDL_WINDOW_SHOWN);
    if (window == NULL)
    {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", portSDL.GetError());
        portSDL.Quit();
        Port_FreeGbaMemory();
        return 1;
    }

    SDL_Renderer *renderer = portSDL.CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE);
    if (renderer == NULL || portSDL.RenderSetLogicalSize(renderer, 240, 160) != 0)
    {
        fprintf(stderr, "SDL renderer failed: %s\n", portSDL.GetError());
        if (renderer != NULL)
            portSDL.DestroyRenderer(renderer);
        portSDL.DestroyWindow(window);
        portSDL.Quit();
        Port_FreeGbaMemory();
        return 1;
    }

    SDL_Texture *texture = portSDL.CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888,
                                                SDL_TEXTUREACCESS_STREAMING, 240, 160);
    if (texture == NULL)
    {
        fprintf(stderr, "SDL texture failed: %s\n", portSDL.GetError());
        portSDL.DestroyRenderer(renderer);
        portSDL.DestroyWindow(window);
        portSDL.Quit();
        Port_FreeGbaMemory();
        return 1;
    }

    Port_AttachRenderer(renderer, texture);
    sWindow = window;
    sRenderer = renderer;
    sTexture = texture;
    portSDL.SetRenderDrawColor(renderer, 0, 0, 0, 255);
    portSDL.RenderClear(renderer);
    portSDL.RenderPresent(renderer);
    fprintf(stderr, "PC: SDL window ready (240x160, scale 4); entering AgbMain\n");
    PortAudio_Init();
    AgbMain();
    fprintf(stderr, "PC: AgbMain returned\n");

    Port_AttachRenderer(NULL, NULL);
    PortAudio_Shutdown();
    PortFlash_Close();
    portSDL.DestroyTexture(texture);
    portSDL.DestroyRenderer(renderer);
    portSDL.DestroyWindow(window);
    portSDL.Quit();
    Port_FreeGbaMemory();
    return 0;
}
