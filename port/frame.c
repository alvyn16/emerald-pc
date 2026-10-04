#include <stdio.h>
#include <stdlib.h>

#include <SDL.h>

#include "platform.h"

static SDL_Renderer *sRenderer;
static Uint64 sNextFrameTick;

void Port_AttachRenderer(SDL_Renderer *renderer)
{
    sRenderer = renderer;
    sNextFrameTick = 0;
}

void Port_PresentAndWait(void)
{
    SDL_Event event;
    while (SDL_PollEvent(&event))
    {
        if (event.type == SDL_QUIT)
        {
            fprintf(stderr, "PC: window closed\n");
            exit(EXIT_SUCCESS);
        }
    }

    if (sRenderer != NULL)
    {
        SDL_SetRenderDrawColor(sRenderer, 0, 0, 0, 255);
        SDL_RenderClear(sRenderer);
        SDL_RenderPresent(sRenderer);
    }

    const Uint64 frequency = SDL_GetPerformanceFrequency();
    const Uint64 interval = (Uint64)((double)frequency / 59.73 + 0.5);
    Uint64 now = SDL_GetPerformanceCounter();
    if (sNextFrameTick == 0 || now > sNextFrameTick + interval)
        sNextFrameTick = now + interval;
    else
        sNextFrameTick += interval;

    while (now < sNextFrameTick)
    {
        Uint64 remaining = sNextFrameTick - now;
        Uint32 milliseconds = (Uint32)(remaining * 1000 / frequency);
        SDL_Delay(milliseconds > 1 ? milliseconds - 1 : 1);
        now = SDL_GetPerformanceCounter();
    }
}
