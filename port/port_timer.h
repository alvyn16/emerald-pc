#ifndef EMERALD_PC_PORT_TIMER_H
#define EMERALD_PC_PORT_TIMER_H

#include <stdint.h>

#define PORT_CYCLES_PER_FRAME 280896u

void PortTimer_Reset(void);
void PortTimer_Advance(uint32_t cycles);

#endif
