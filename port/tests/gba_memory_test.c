#include <stdint.h>
#include <stdio.h>

#include "gba_memory.h"

int main(void)
{
    if (Port_InitGbaMemory() != 0)
        return 1;
    if (*(volatile uint16_t *)0x04000130u != 0x03FFu)
        return 2;
    *(volatile uint32_t *)0x02000000u = 0x12345678u;
    if (*(volatile uint32_t *)0x02000000u != 0x12345678u)
        return 3;
    Port_FreeGbaMemory();
    puts("GBA regions mapped and writable");
    return 0;
}
