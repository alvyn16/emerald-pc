#ifndef PORT_INPUT_H
#define PORT_INPUT_H
#include <SDL.h>
void PortInput_Init(const char *configPath);
void PortInput_Shutdown(void);
void PortInput_HandleEvent(const SDL_Event *event);
void PortInput_SuppressMenuKeys(void);
unsigned PortInput_ReadButtons(void);
/* Ten lines in GBA bit order: keyboard scancode, SDL controller button. */
int PortInput_LoadConfig(const char *path);
int PortInput_SaveConfig(const char *path);
#endif
