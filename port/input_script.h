#ifndef EMERALD_PC_INPUT_SCRIPT_H
#define EMERALD_PC_INPUT_SCRIPT_H

int PortInputScript_Init(void);
int PortInputScript_GetPressed(unsigned frame, unsigned *pressed);
int PortInputScript_Fast(void);
unsigned PortInputScript_StopFrame(void);

#endif
