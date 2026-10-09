#ifndef EMERALD_PC_PORT_RESET_H
#define EMERALD_PC_PORT_RESET_H

#include <wchar.h>

typedef int (*PortResetSpawner)(const wchar_t *module, wchar_t *commandLine);

void PortReset_SetSpawner(PortResetSpawner spawner);
int PortReset_Restart(void);

#endif
