#ifndef EMERALD_PC_PORT_BIOS_H
#define EMERALD_PC_PORT_BIOS_H

#include <stdint.h>

/* Extra BIOS entry points not declared by the upstream gba/syscall.h. */
void IntrWait(uint32_t discard, uint32_t flags);
void Halt(void);

#endif
