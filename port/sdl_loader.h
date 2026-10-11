#ifndef PORT_SDL_LOADER_H
#define PORT_SDL_LOADER_H

#include <SDL.h>

struct PortSDL
{
    __typeof__(&SDL_SetMainReady) SetMainReady;
    __typeof__(&SDL_Init) Init;
    __typeof__(&SDL_InitSubSystem) InitSubSystem;
    __typeof__(&SDL_OpenAudioDevice) OpenAudioDevice;
    __typeof__(&SDL_CloseAudioDevice) CloseAudioDevice;
    __typeof__(&SDL_PauseAudioDevice) PauseAudioDevice;
    __typeof__(&SDL_GetAudioDeviceStatus) GetAudioDeviceStatus;
    __typeof__(&SDL_QueueAudio) QueueAudio;
    __typeof__(&SDL_GetQueuedAudioSize) GetQueuedAudioSize;
    __typeof__(&SDL_ClearQueuedAudio) ClearQueuedAudio;
    __typeof__(&SDL_Quit) Quit;
    __typeof__(&SDL_GetError) GetError;
    __typeof__(&SDL_CreateWindow) CreateWindow;
    __typeof__(&SDL_DestroyWindow) DestroyWindow;
    __typeof__(&SDL_CreateRenderer) CreateRenderer;
    __typeof__(&SDL_DestroyRenderer) DestroyRenderer;
    __typeof__(&SDL_CreateTexture) CreateTexture;
    __typeof__(&SDL_DestroyTexture) DestroyTexture;
    __typeof__(&SDL_UpdateTexture) UpdateTexture;
    __typeof__(&SDL_RenderCopy) RenderCopy;
    __typeof__(&SDL_RenderSetLogicalSize) RenderSetLogicalSize;
    __typeof__(&SDL_SetRenderDrawColor) SetRenderDrawColor;
    __typeof__(&SDL_RenderClear) RenderClear;
    __typeof__(&SDL_RenderPresent) RenderPresent;
    __typeof__(&SDL_PollEvent) PollEvent;
    __typeof__(&SDL_GetKeyboardState) GetKeyboardState;
    __typeof__(&SDL_GetPerformanceFrequency) GetPerformanceFrequency;
    __typeof__(&SDL_GetPerformanceCounter) GetPerformanceCounter;
    __typeof__(&SDL_Delay) Delay;
};

extern struct PortSDL portSDL;
int Port_LoadSDL2(void);

#endif
