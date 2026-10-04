#ifndef EMERALD_PC_PLATFORM_H
#define EMERALD_PC_PLATFORM_H

typedef struct SDL_Renderer SDL_Renderer;

void Port_AttachRenderer(SDL_Renderer *renderer);
void Port_PresentAndWait(void);

#endif
