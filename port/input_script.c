#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gba/io_reg.h"
#include "input_script.h"

#define MAX_EVENTS 4096

struct InputEvent
{
    unsigned first;
    unsigned last;
    unsigned buttons;
};

static struct InputEvent sEvents[MAX_EVENTS];
static unsigned sEventCount;
static unsigned sNextEvent;
static int sScriptActive;
static int sFast;
static unsigned sStopFrame;

static int ParseButtons(char *text, unsigned *buttons)
{
    static const struct { const char *name; unsigned bit; } names[] = {
        {"A", A_BUTTON}, {"B", B_BUTTON}, {"SELECT", SELECT_BUTTON},
        {"START", START_BUTTON}, {"RIGHT", DPAD_RIGHT},
        {"LEFT", DPAD_LEFT}, {"UP", DPAD_UP}, {"DOWN", DPAD_DOWN},
        {"R", R_BUTTON}, {"L", L_BUTTON}
    };
    *buttons = 0;
    if (strcmp(text, "NONE") == 0)
        return 0;
    for (char *token = strtok(text, "+"); token != NULL; token = strtok(NULL, "+"))
    {
        unsigned i;
        for (i = 0; i < sizeof(names) / sizeof(names[0]); ++i)
            if (strcmp(token, names[i].name) == 0)
                break;
        if (i == sizeof(names) / sizeof(names[0]))
            return -1;
        *buttons |= names[i].bit;
    }
    return 0;
}

int PortInputScript_Init(void)
{
    const char *path = getenv("EMERALD_PC_INPUT_SCRIPT");
    const char *fast = getenv("EMERALD_PC_FAST");
    const char *stop = getenv("EMERALD_PC_STOP_FRAME");
    sFast = fast != NULL && strcmp(fast, "1") == 0;
    sStopFrame = stop != NULL ? (unsigned)strtoul(stop, NULL, 10) : 0;
    sEventCount = sNextEvent = 0;
    sScriptActive = path != NULL && *path != '\0';
    if (!sScriptActive)
        return 0;

    FILE *file = fopen(path, "r");
    if (file == NULL)
    {
        fprintf(stderr, "PC input: cannot open %s: %s\n", path, strerror(errno));
        return -1;
    }
    char line[256];
    unsigned lineNumber = 0;
    while (fgets(line, sizeof(line), file) != NULL)
    {
        ++lineNumber;
        char *start = line;
        while (isspace((unsigned char)*start)) ++start;
        if (*start == '#' || *start == '\0') continue;
        unsigned first, last, buttons;
        char name[80], extra;
        if (sscanf(start, "%u %u %79s %c", &first, &last, name, &extra) != 3 ||
            first == 0 || first > last || sEventCount == MAX_EVENTS ||
            (sEventCount && first <= sEvents[sEventCount - 1].last) ||
            ParseButtons(name, &buttons) != 0)
        {
            fprintf(stderr, "PC input: invalid or overlapping event at %s:%u\n", path, lineNumber);
            fclose(file);
            return -1;
        }
        sEvents[sEventCount++] = (struct InputEvent){first, last, buttons};
    }
    if (ferror(file))
    {
        fprintf(stderr, "PC input: read error in %s\n", path);
        fclose(file);
        return -1;
    }
    fclose(file);
    fprintf(stderr, "PC input: %u scripted ranges from %s%s\n", sEventCount,
            path, sFast ? " (unthrottled)" : "");
    return 0;
}

int PortInputScript_GetPressed(unsigned frame, unsigned *pressed)
{
    if (!sScriptActive)
        return 0;
    while (sNextEvent < sEventCount && frame > sEvents[sNextEvent].last)
        ++sNextEvent;
    *pressed = sNextEvent < sEventCount && frame >= sEvents[sNextEvent].first
            ? sEvents[sNextEvent].buttons : 0;
    return 1;
}

int PortInputScript_Fast(void)
{
    return sFast;
}

unsigned PortInputScript_StopFrame(void)
{
    return sStopFrame;
}
