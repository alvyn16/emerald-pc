#ifndef PORT_HOST_FLASH_H
#define PORT_HOST_FLASH_H

#include "gba/types.h"

int PortFlash_Open(void);
int PortFlash_OpenFile(const char *path);
void PortFlash_Close(void);
void PortFlash_Read(u16 sector, u32 offset, u8 *destination, u32 size);
u32 PortFlash_Verify(u16 sector, const u8 *source, u32 size);
u16 PortFlash_ProgramByte(u16 sector, u32 offset, u8 value);
u16 PortFlash_ProgramSector(u16 sector, u8 *source);
u16 PortFlash_EraseSector(u16 sector);
u16 PortFlash_EraseChip(void);
u16 PortFlash_WaitForWrite(u8 phase, u8 *address, u8 lastData);

#endif
