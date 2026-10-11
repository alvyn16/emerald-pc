#ifndef EMERALD_PC_PORT_PSG_H
#define EMERALD_PC_PORT_PSG_H
#include <stdint.h>
void PortPsg_Reset(void);
void PortPsg_Write8(uintptr_t address, uint8_t value);
void PortPsg_Write16(uintptr_t address, uint16_t value);
void PortPsg_Write32(uintptr_t address, uint32_t value);
void PortPsg_Render(int16_t *stereo, unsigned frames, unsigned sampleRate);
#endif
