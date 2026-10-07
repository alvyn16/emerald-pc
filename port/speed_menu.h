#ifndef EMERALD_PC_SPEED_MENU_H
#define EMERALD_PC_SPEED_MENU_H

#include <stdint.h>
#include <SDL.h>

void PortSpeedMenu_HandleEvent(const SDL_Event *event);
int PortSpeedMenu_IsOpen(void);
unsigned PortSpeedMenu_Multiplier(void);
void PortSpeedMenu_Draw(uint32_t *pixels);

#endif
