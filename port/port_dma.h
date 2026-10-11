#ifndef EMERALD_PC_PORT_DMA_H
#define EMERALD_PC_PORT_DMA_H

#include <stdint.h>

void PortDma_Set(int channel, const void *source, void *destination, unsigned control);
void PortDma_OnHBlank(void);
void PortDma_OnVBlank(void);
void PortDma_Reset(void);
void PortDma_Stop(int channel);
void PortDma_Write16(uintptr_t address, uint16_t value);
void PortDma_Write32(uintptr_t address, uint32_t value);

#endif
