/* Host stand-ins for GBA startup, serial link, and multiboot ARM routines. */
#include <stdio.h>

#include "global.h"
#include "crt0.h"
#include "libgcnmultiboot.h"
#include "librfu.h"
#include "main.h"
#include "multiboot.h"

/* The original copies 0x800 bytes of IRQ code into IWRAM. The host never
 * executes it; VBlank timing is handled by port/frame.c. Keep the source
 * large enough for the original copy expression. */
u32 IntrMain[0x200];

const u8 RomHeaderGameCode[GAME_CODE_LENGTH] = {'B', 'P', 'E', 'E'};
const u8 RomHeaderSoftwareVersion = 0;
vu16 GPIOPortDirection;

static void UnsupportedLink(const char *operation)
{
    static int warned;
    if (!warned)
    {
        fprintf(stderr, "GBA link hardware unavailable (%s); serial functions are disabled\n", operation);
        warned = 1;
    }
}

void IntrSIO32(void) { UnsupportedLink("IntrSIO32"); }

void MultiBootInit(struct MultiBootParam *mp) { (void)mp; UnsupportedLink("MultiBootInit"); }
int MultiBootMain(struct MultiBootParam *mp) { (void)mp; UnsupportedLink("MultiBootMain"); return -1; }
int MultiBootCheckComplete(struct MultiBootParam *mp) { (void)mp; return 0; }
void MultiBootStartMaster(struct MultiBootParam *mp, const u8 *source, int length,
                          u8 color, s8 speed)
{
    (void)mp; (void)source; (void)length; (void)color; (void)speed;
    UnsupportedLink("MultiBootStartMaster");
}

void GameCubeMultiBoot_Init(struct GcmbStruct *state) { (void)state; UnsupportedLink("GameCubeMultiBoot_Init"); }
void GameCubeMultiBoot_Main(struct GcmbStruct *state) { (void)state; UnsupportedLink("GameCubeMultiBoot_Main"); }
void GameCubeMultiBoot_ExecuteProgram(struct GcmbStruct *state) { (void)state; UnsupportedLink("GameCubeMultiBoot_ExecuteProgram"); }
void GameCubeMultiBoot_HandleSerialInterrupt(struct GcmbStruct *state) { (void)state; UnsupportedLink("GameCubeMultiBoot_HandleSerialInterrupt"); }
void GameCubeMultiBoot_Quit(void) { UnsupportedLink("GameCubeMultiBoot_Quit"); }
