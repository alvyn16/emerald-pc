#ifndef EMERALD_PC_PORT_PSG_H
#define EMERALD_PC_PORT_PSG_H
#include <stdint.h>
void PortPsg_Reset(void);
void PortPsg_Render(int16_t *stereo, unsigned frames, unsigned sampleRate);
#endif
