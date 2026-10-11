#define SDL_MAIN_HANDLED
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "port_input.h"
#include "sdl_loader.h"
struct PortSDL portSDL;
static Uint8 keys[SDL_NUM_SCANCODES], buttons[SDL_CONTROLLER_BUTTON_MAX];
static int connected, opened, closed;
static Sint16 axes[2];
static const Uint8 *GetKeys(int *count) { (void)count; return keys; }
static int Init(Uint32 flags) { assert(flags == SDL_INIT_GAMECONTROLLER); return 0; }
static int Count(void) { return connected; }
static SDL_bool IsController(int index) { assert(index == 0); return SDL_TRUE; }
static SDL_GameController *Open(int index) { assert(index == 0); opened++; return (void *)1; }
static void Close(SDL_GameController *c) { assert(c == (void *)1); closed++; }
static SDL_bool Attached(SDL_GameController *c) { assert(c == (void *)1); return connected; }
static Uint8 Button(SDL_GameController *c, SDL_GameControllerButton b) { assert(c == (void *)1); return buttons[b]; }
static Sint16 Axis(SDL_GameController *c, SDL_GameControllerAxis a) { assert(c == (void *)1); return axes[a]; }
static void Event(Uint32 type, Uint8 window)
{ SDL_Event e; memset(&e,0,sizeof(e)); e.type=type; e.window.event=window; PortInput_HandleEvent(&e); }
int main(void)
{
    portSDL.GetKeyboardState=GetKeys; portSDL.InitSubSystem=Init;
    portSDL.NumJoysticks=Count; portSDL.IsGameController=IsController;
    portSDL.GameControllerOpen=Open; portSDL.GameControllerClose=Close;
    portSDL.GameControllerGetAttached=Attached; portSDL.GameControllerGetButton=Button;
    portSDL.GameControllerGetAxis=Axis;
    const char *path="build/tests/controls-test.cfg";
    remove(path); PortInput_Init(path); assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_Z]=1; assert(PortInput_ReadButtons()==1);
    Event(SDL_WINDOWEVENT,SDL_WINDOWEVENT_FOCUS_LOST); assert(PortInput_ReadButtons()==0);
    Event(SDL_WINDOWEVENT,SDL_WINDOWEVENT_FOCUS_GAINED); assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_Z]=0; assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_Z]=1; assert(PortInput_ReadButtons()==1); keys[SDL_SCANCODE_Z]=0;
    connected=1; buttons[SDL_CONTROLLER_BUTTON_A]=1;
    Event(SDL_CONTROLLERDEVICEADDED,0); assert(PortInput_ReadButtons()==0);
    buttons[SDL_CONTROLLER_BUTTON_A]=0; assert(PortInput_ReadButtons()==0);
    buttons[SDL_CONTROLLER_BUTTON_A]=1; assert(PortInput_ReadButtons()==1);
    connected=0; Event(SDL_CONTROLLERDEVICEREMOVED,0);
    assert(PortInput_ReadButtons()==0 && closed==1);
    buttons[SDL_CONTROLLER_BUTTON_A]=0; connected=1; Event(SDL_CONTROLLERDEVICEADDED,0);
    assert(PortInput_ReadButtons()==0 && opened==2);
    axes[0]=15999; assert(PortInput_ReadButtons()==0);
    axes[0]=16001; assert(PortInput_ReadButtons()==0x10);
    keys[SDL_SCANCODE_LEFT]=1; assert(PortInput_ReadButtons()==0); keys[SDL_SCANCODE_LEFT]=0; axes[0]=0;
    FILE *file=fopen(path,"w"); assert(file);
    const int mappings[10]={SDL_SCANCODE_RETURN,SDL_SCANCODE_X,SDL_SCANCODE_BACKSPACE,SDL_SCANCODE_Z,
        SDL_SCANCODE_RIGHT,SDL_SCANCODE_LEFT,SDL_SCANCODE_UP,SDL_SCANCODE_DOWN,SDL_SCANCODE_S,SDL_SCANCODE_A};
    const int pad[10]={0,1,4,6,14,13,11,12,10,9};
    for(int i=0;i<10;i++) fprintf(file,"%d %d\n",mappings[i],pad[i]);
    fclose(file);
    assert(PortInput_LoadConfig(path)==0); assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_RETURN]=1; assert(PortInput_ReadButtons()==1);
    PortInput_SuppressMenuKeys(); assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_RETURN]=0; assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_RETURN]=1; assert(PortInput_ReadButtons()==1); keys[SDL_SCANCODE_RETURN]=0;
    assert(PortInput_SaveConfig(path)==0);
    PortInput_Shutdown(); PortInput_Init(path); assert(PortInput_ReadButtons()==0);
    keys[SDL_SCANCODE_RETURN]=1; assert(PortInput_ReadButtons()==1); keys[SDL_SCANCODE_RETURN]=0;
    file=fopen(path,"w"); assert(file); fprintf(file,"%d 0\n",SDL_SCANCODE_P); fclose(file);
    assert(PortInput_LoadConfig(path)==-1); keys[SDL_SCANCODE_RETURN]=1;
    assert(PortInput_ReadButtons()==1); keys[SDL_SCANCODE_RETURN]=0;
    PortInput_Shutdown(); PortInput_Shutdown(); assert(opened==closed);
    remove(path); puts("Input: keyboard/remap/persistence, controller/hotplug, focus, axes and menu isolation OK");
    return 0;
}
