#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "port_input.h"
#include "sdl_loader.h"

static int sKeys[10], sButtons[10];
static int sDefaultsReady, sControllerEnabled, sFocused = 1;
static unsigned sBlocked, sMenuKeys;
static SDL_GameController *sController;

static void Defaults(void)
{
    const int keys[10] = {SDL_SCANCODE_Z, SDL_SCANCODE_X, SDL_SCANCODE_BACKSPACE,
        SDL_SCANCODE_RETURN, SDL_SCANCODE_RIGHT, SDL_SCANCODE_LEFT,
        SDL_SCANCODE_UP, SDL_SCANCODE_DOWN, SDL_SCANCODE_S, SDL_SCANCODE_A};
    const int buttons[10] = {SDL_CONTROLLER_BUTTON_A, SDL_CONTROLLER_BUTTON_B,
        SDL_CONTROLLER_BUTTON_BACK, SDL_CONTROLLER_BUTTON_START,
        SDL_CONTROLLER_BUTTON_DPAD_RIGHT, SDL_CONTROLLER_BUTTON_DPAD_LEFT,
        SDL_CONTROLLER_BUTTON_DPAD_UP, SDL_CONTROLLER_BUTTON_DPAD_DOWN,
        SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, SDL_CONTROLLER_BUTTON_LEFTSHOULDER};
    memcpy(sKeys, keys, sizeof(keys));
    memcpy(sButtons, buttons, sizeof(buttons));
    sDefaultsReady = 1;
}

int PortInput_LoadConfig(const char *path)
{
    int keys[10], buttons[10];
    FILE *file = fopen(path, "r");
    if (!file) return -1;
    int valid = 1;
    for (unsigned i = 0; i < 10 && valid; i++)
    {
        valid = fscanf(file, "%d %d", &keys[i], &buttons[i]) == 2;
        valid = valid && keys[i] > SDL_SCANCODE_UNKNOWN && keys[i] < SDL_NUM_SCANCODES
            && keys[i] != SDL_SCANCODE_P && buttons[i] >= 0 && buttons[i] < SDL_CONTROLLER_BUTTON_MAX;
        for (unsigned j = 0; j < i && valid; j++)
            valid = keys[j] != keys[i] && buttons[j] != buttons[i];
    }
    char extra;
    if (valid && fscanf(file, " %c", &extra) == 1) valid = 0;
    fclose(file);
    if (!valid) return -1; /* Transactional: keep the previous valid mapping. */
    memcpy(sKeys, keys, sizeof(keys)); memcpy(sButtons, buttons, sizeof(buttons));
    sDefaultsReady = 1;
    sBlocked = 0x3ff; /* A changed binding must be released before activation. */
    return 0;
}

int PortInput_SaveConfig(const char *path)
{
    if (!sDefaultsReady) Defaults();
    FILE *file = fopen(path, "w");
    if (!file) return -1;
    int failed = 0;
    for (unsigned i = 0; i < 10; i++)
        if (fprintf(file, "%d %d\n", sKeys[i], sButtons[i]) < 0) failed = 1;
    if (fclose(file) != 0) failed = 1;
    return failed ? -1 : 0;
}

static void ScanControllers(void)
{
    if (!sControllerEnabled) return;
    if (sController && !portSDL.GameControllerGetAttached(sController))
    { portSDL.GameControllerClose(sController); sController = NULL; sBlocked = 0x3ff; }
    if (sController) return;
    for (int i = 0; i < portSDL.NumJoysticks(); i++)
        if (portSDL.IsGameController(i) && (sController = portSDL.GameControllerOpen(i)))
        { sBlocked = 0x3ff; break; }
}

void PortInput_Shutdown(void)
{
    if (sController) portSDL.GameControllerClose(sController);
    sController = NULL; sControllerEnabled = 0;
    sFocused = 1; sBlocked = sMenuKeys = 0;
}

void PortInput_Init(const char *configPath)
{
    PortInput_Shutdown(); Defaults();
    char path[MAX_PATH];
    if (!configPath)
    {
        DWORD length = GetModuleFileNameA(NULL, path, sizeof(path));
        char *slash = length && length < sizeof(path) ? strrchr(path, '\\') : NULL;
        if (slash) { *slash = 0; slash = strrchr(path, '\\'); }
        if (slash && (size_t)(slash-path) + sizeof("\\saves\\controls.cfg") <= sizeof(path))
        {
            strcpy(slash, "\\saves"); CreateDirectoryA(path, NULL);
            strcat(path, "\\controls.cfg"); configPath = path;
        }
    }
    if (configPath)
    {
        FILE *existing = fopen(configPath, "r");
        if (existing)
        {
            fclose(existing);
            if (PortInput_LoadConfig(configPath)) fprintf(stderr, "Input: invalid controls.cfg; defaults used, file preserved\n");
        }
        else if (PortInput_SaveConfig(configPath)) fprintf(stderr, "Input: cannot save default bindings\n");
    }
    sControllerEnabled = portSDL.NumJoysticks && portSDL.InitSubSystem(SDL_INIT_GAMECONTROLLER) == 0;
    if (sControllerEnabled) ScanControllers();
    sBlocked = 0x3ff;
}

void PortInput_HandleEvent(const SDL_Event *event)
{
    if (event->type == SDL_CONTROLLERDEVICEADDED || event->type == SDL_CONTROLLERDEVICEREMOVED)
        ScanControllers();
    if (event->type == SDL_WINDOWEVENT)
    {
        if (event->window.event == SDL_WINDOWEVENT_FOCUS_LOST) { sFocused = 0; sBlocked = 0x3ff; }
        if (event->window.event == SDL_WINDOWEVENT_FOCUS_GAINED) { sFocused = 1; sBlocked = 0x3ff; }
    }
}

void PortInput_SuppressMenuKeys(void) { sMenuKeys |= 7; }

unsigned PortInput_ReadButtons(void)
{
    if (!sDefaultsReady) Defaults();
    const Uint8 *keys = portSDL.GetKeyboardState(NULL);
    const int menuKeys[3] = {SDL_SCANCODE_RETURN, SDL_SCANCODE_UP, SDL_SCANCODE_DOWN};
    unsigned pressed = 0;
    ScanControllers();
    for (unsigned j = 0; j < 3; j++)
        if (!keys[menuKeys[j]]) sMenuKeys &= ~(1u << j);
    for (unsigned i = 0; i < 10; i++)
    {
        int suppressed = 0;
        for (unsigned j = 0; j < 3; j++)
            if ((sMenuKeys & (1u << j)) && sKeys[i] == menuKeys[j]) suppressed = 1;
        if (keys[sKeys[i]] && !suppressed) pressed |= 1u << i;
        if (sController && portSDL.GameControllerGetButton(sController, sButtons[i])) pressed |= 1u << i;
    }
    if (sController)
    {
        Sint16 x = portSDL.GameControllerGetAxis(sController, SDL_CONTROLLER_AXIS_LEFTX);
        Sint16 y = portSDL.GameControllerGetAxis(sController, SDL_CONTROLLER_AXIS_LEFTY);
        if (x > 16000) pressed |= 0x10;
        if (x < -16000) pressed |= 0x20;
        if (y > 16000) pressed |= 0x80;
        if (y < -16000) pressed |= 0x40;
    }
    if ((pressed & 0x30) == 0x30) pressed &= ~0x30;
    if ((pressed & 0xc0) == 0xc0) pressed &= ~0xc0;
    sBlocked &= pressed;
    return sFocused ? pressed & ~sBlocked : 0;
}
