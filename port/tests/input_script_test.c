#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "gba/io_reg.h"
#include "input_script.h"

int main(void)
{
    const char *path = "build/input-script-test.txt";
    FILE *file = fopen(path, "w");
    assert(file != NULL);
    fputs("# frame ranges are inclusive\n2 3 A+START\n7 7 DOWN\n", file);
    fclose(file);
    assert(_putenv_s("EMERALD_PC_INPUT_SCRIPT", path) == 0);
    assert(_putenv_s("EMERALD_PC_FAST", "1") == 0);
    assert(_putenv_s("EMERALD_PC_STOP_FRAME", "9") == 0);
    assert(PortInputScript_Init() == 0);
    assert(PortInputScript_Fast());
    assert(PortInputScript_StopFrame() == 9);
    unsigned pressed = ~0u;
    assert(PortInputScript_GetPressed(1, &pressed) && pressed == 0);
    assert(PortInputScript_GetPressed(2, &pressed) && pressed == (A_BUTTON | START_BUTTON));
    assert(PortInputScript_GetPressed(3, &pressed) && pressed == (A_BUTTON | START_BUTTON));
    assert(PortInputScript_GetPressed(4, &pressed) && pressed == 0);
    assert(PortInputScript_GetPressed(7, &pressed) && pressed == DPAD_DOWN);
    assert(PortInputScript_GetPressed(8, &pressed) && pressed == 0);

    file = fopen(path, "w");
    assert(file != NULL);
    fputs("1 3 A\n3 4 B\n", file);
    fclose(file);
    assert(PortInputScript_Init() != 0); // Overlap is rejected.
    assert(_putenv_s("EMERALD_PC_INPUT_SCRIPT", "") == 0);
    assert(PortInputScript_Init() == 0);
    assert(!PortInputScript_GetPressed(1, &pressed));
    remove(path);
    return 0;
}
