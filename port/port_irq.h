#ifndef EMERALD_PC_PORT_IRQ_H
#define EMERALD_PC_PORT_IRQ_H

#include <stdint.h>

/* Main-thread only. IO and IWRAM must be mapped before using this module. */
void PortIrq_Reset(void);
void PortIrq_Raise(uint16_t flags);
void PortIrq_Acknowledge(uint16_t flags);
uint16_t PortIrq_Pending(void);
/* Acknowledge and deliver each eligible source at most once; no reentry. */
uint16_t PortIrq_Dispatch(void);

#endif
