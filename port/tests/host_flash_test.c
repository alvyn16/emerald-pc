#include <stdio.h>
#include <string.h>
#include <windows.h>

#include "host_flash.h"

#define REQUIRE(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "flash test failed at line %d: %s\n", __LINE__, #condition); \
        return 1; \
    } \
} while (0)

int main(void)
{
    char path[MAX_PATH];
    snprintf(path, sizeof(path), "build/host-flash-test-%lu.sav",
             (unsigned long)GetCurrentProcessId());
    REQUIRE(GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES);
    REQUIRE(PortFlash_OpenFile(path) == 0);

    u8 byte = 0;
    PortFlash_Read(17, 23, &byte, 1);
    REQUIRE(byte == 0xFF);
    REQUIRE(PortFlash_ProgramByte(17, 23, 0xA5) == 0);
    PortFlash_Read(17, 23, &byte, 1);
    REQUIRE(byte == 0xA5);
    REQUIRE(PortFlash_ProgramByte(17, 23, 0xFF) != 0);
    REQUIRE(PortFlash_EraseSector(17) == 0);
    PortFlash_Read(17, 23, &byte, 1);
    REQUIRE(byte == 0xFF);

    u8 sector[4096];
    memset(sector, 0x5A, sizeof(sector));
    REQUIRE(PortFlash_ProgramSector(2, sector) == 0);
    REQUIRE(PortFlash_Verify(2, sector, sizeof(sector)) == 0);
    REQUIRE(PortFlash_ProgramByte(32, 0, 0) != 0);
    PortFlash_Close();

    REQUIRE(PortFlash_OpenFile(path) == 0);
    PortFlash_Read(2, 100, &byte, 1);
    REQUIRE(byte == 0x5A);
    REQUIRE(PortFlash_EraseChip() == 0);
    PortFlash_Read(2, 100, &byte, 1);
    REQUIRE(byte == 0xFF);
    PortFlash_Close();

    REQUIRE(DeleteFileA(path));
    puts("host flash read/write/erase/persistence OK");
    return 0;
}
