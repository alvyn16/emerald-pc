#include <assert.h>
#include <stdint.h>
#include <string.h>
#define SDL_MAIN_HANDLED
#include <SDL.h>
#undef main

#include "speed_menu.h"
#include "port_ppu.h"

static uint32_t sPixels[PORT_SCREEN_WIDTH * PORT_SCREEN_HEIGHT];

static void Key(SDL_Keycode key)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = SDL_KEYDOWN;
    event.key.keysym.sym = key;
    PortSpeedMenu_HandleEvent(&event);
}

int main(void)
{
    assert(PortSpeedMenu_Multiplier() == 1);
    Key(SDLK_p);
    assert(PortSpeedMenu_IsOpen());
    PortSpeedMenu_Draw(sPixels);
    assert(sPixels[17 * PORT_SCREEN_WIDTH + 67] == 0xffe8e8e8u);
    Key(SDLK_DOWN);
    Key(SDLK_DOWN);
    Key(SDLK_RETURN);
    assert(!PortSpeedMenu_IsOpen());
    assert(PortSpeedMenu_Multiplier() == 3);
    Key(SDLK_p);
    Key(SDLK_DOWN);
    Key(SDLK_ESCAPE);
    assert(PortSpeedMenu_Multiplier() == 3);
    Key(SDLK_p);
    Key(SDLK_DOWN);
    Key(SDLK_RETURN);
    assert(PortSpeedMenu_Multiplier() == 4);
    Key(SDLK_p);
    Key(SDLK_UP);
    Key(SDLK_UP);
    Key(SDLK_UP);
    Key(SDLK_RETURN);
    assert(PortSpeedMenu_Multiplier() == 1);
    return 0;
}
