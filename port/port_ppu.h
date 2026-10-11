#ifndef EMERALD_PC_PORT_PPU_H
#define EMERALD_PC_PORT_PPU_H

#include <stdint.h>

#define PORT_SCREEN_WIDTH 240
#define PORT_SCREEN_HEIGHT 160

void PortPpu_Render(uint32_t *pixels);
void PortPpu_BeginFrame(void);
void PortPpu_RenderLine(unsigned y, uint32_t *row);
// Call after a mapped IO write: even an identical BG reference reloads its
// internal accumulator. Matrix writes take effect on the next sampled line.
void PortPpu_NotifyWrite(uintptr_t address, unsigned bytes);

#endif
