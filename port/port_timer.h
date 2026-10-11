#ifndef EMERALD_PC_PORT_TIMER_H
#define EMERALD_PC_PORT_TIMER_H

#include <stdint.h>

#define PORT_CYCLES_PER_FRAME 280896u

void PortTimer_Reset(void);
void PortTimer_Advance(uint32_t cycles);
// Writes change reload/control, while reads of CNT_L expose the counter.
// Write32 is ordered low halfword then high halfword (enable).
void PortTimer_Write16(uintptr_t address, uint16_t value);
void PortTimer_Write32(uintptr_t address, uint32_t value);

#endif
