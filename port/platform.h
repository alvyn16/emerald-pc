#ifndef EMERALD_PC_PLATFORM_H
#define EMERALD_PC_PLATFORM_H

typedef struct SDL_Renderer SDL_Renderer;
typedef struct SDL_Texture SDL_Texture;

void Port_AttachRenderer(SDL_Renderer *renderer, SDL_Texture *texture);
void PortHost_RunFrame(void);
void Port_ExitCleanly(void);

#endif
