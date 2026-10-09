#ifndef EMERALD_PC_PORT_DMA_H
#define EMERALD_PC_PORT_DMA_H

void PortDma_Set(int channel, const void *source, void *destination, unsigned control);
void PortDma_OnHBlank(void);
void PortDma_OnVBlank(void);

#endif
