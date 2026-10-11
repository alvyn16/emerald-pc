#define SDL_MAIN_HANDLED
#include <assert.h>
#include <stdio.h>
#include "port_input.h"
#include "sdl_loader.h"
static void Pump(void)
{
    SDL_Event event;
    SDL_PumpEvents();
    while (SDL_PollEvent(&event)) PortInput_HandleEvent(&event);
}
int main(void)
{
    SDL_SetMainReady();
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    assert(Port_LoadSDL2()==0);
    assert(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER)==0);
    SDL_Window *window=SDL_CreateWindow("input test",0,0,240,160,SDL_WINDOW_HIDDEN);
    assert(window);
    printf("Physical SDL joystick count before fixture: %d\n",SDL_NumJoysticks());
    const char *path="build/tests/controls-sdl.cfg";
    remove(path); PortInput_Init(path); Pump(); assert(PortInput_ReadButtons()==0);
    int index=SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,6,21,0);
    assert(index>=0 && SDL_IsGameController(index));
    SDL_Joystick *stick=SDL_JoystickOpen(index); assert(stick);
    Pump(); assert(PortInput_ReadButtons()==0);
    assert(SDL_JoystickSetVirtualButton(stick,SDL_CONTROLLER_BUTTON_A,1)==0);
    Pump(); assert(PortInput_ReadButtons()==1);
    assert(SDL_JoystickSetVirtualButton(stick,SDL_CONTROLLER_BUTTON_A,0)==0);
    assert(SDL_JoystickSetVirtualAxis(stick,SDL_CONTROLLER_AXIS_LEFTX,-20000)==0);
    Pump(); assert(PortInput_ReadButtons()==0x20);
    SDL_JoystickClose(stick); assert(SDL_JoystickDetachVirtual(index)==0);
    Pump(); assert(PortInput_ReadButtons()==0);
    index=SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,6,21,0);
    assert(index>=0); stick=SDL_JoystickOpen(index); assert(stick);
    Pump(); assert(PortInput_ReadButtons()==0);
    assert(SDL_JoystickSetVirtualButton(stick,SDL_CONTROLLER_BUTTON_B,1)==0);
    Pump(); assert(PortInput_ReadButtons()==2);
    PortInput_Shutdown(); SDL_JoystickClose(stick); SDL_JoystickDetachVirtual(index);
    SDL_DestroyWindow(window); SDL_Quit(); remove(path);
    puts("PASS real SDL virtual controller: buttons, axes, disconnect/reconnect");
    return 0;
}
