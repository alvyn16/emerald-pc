#include <stdio.h>
#include <string.h>
#include <windows.h>

#include "sdl_loader.h"

struct PortSDL portSDL;
static HMODULE sLibrary;

int Port_LoadSDL2(void)
{
    sLibrary = LoadLibraryA("SDL2.dll");
    if (sLibrary == NULL)
    {
        fprintf(stderr, "Cannot load SDL2.dll after GBA memory reservation (Windows error %lu)\n",
                (unsigned long)GetLastError());
        return -1;
    }

#define LOAD(name) do { \
    FARPROC address = GetProcAddress(sLibrary, "SDL_" #name); \
    if (address == NULL) { \
        fprintf(stderr, "SDL2.dll has no SDL_%s\n", #name); \
        return -1; \
    } \
    memcpy(&portSDL.name, &address, sizeof(address)); \
} while (0)

    LOAD(SetMainReady);
    LOAD(Init);
    LOAD(Quit);
    LOAD(GetError);
    LOAD(CreateWindow);
    LOAD(DestroyWindow);
    LOAD(CreateRenderer);
    LOAD(DestroyRenderer);
    LOAD(CreateTexture);
    LOAD(DestroyTexture);
    LOAD(UpdateTexture);
    LOAD(RenderCopy);
    LOAD(RenderSetLogicalSize);
    LOAD(SetRenderDrawColor);
    LOAD(RenderClear);
    LOAD(RenderPresent);
    LOAD(PollEvent);
    LOAD(GetKeyboardState);
    LOAD(GetPerformanceFrequency);
    LOAD(GetPerformanceCounter);
    LOAD(Delay);
#undef LOAD
    return 0;
}
