#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

#include "host_flash.h"

#define FLASH_SIZE (128u * 1024u)
#define SECTOR_SIZE 4096u
#define SECTOR_COUNT (FLASH_SIZE / SECTOR_SIZE)
#define FLASH_ERROR 0x8000u

static HANDLE sFile = INVALID_HANDLE_VALUE;
static HANDLE sMapping;
static u8 *sBytes;
static unsigned sWritesSinceFlush;

void PortFlash_Close(void)
{
    if (sBytes != NULL)
    {
        FlushViewOfFile(sBytes, FLASH_SIZE);
        UnmapViewOfFile(sBytes);
        sBytes = NULL;
    }
    if (sMapping != NULL)
    {
        CloseHandle(sMapping);
        sMapping = NULL;
    }
    if (sFile != INVALID_HANDLE_VALUE)
    {
        FlushFileBuffers(sFile);
        CloseHandle(sFile);
        sFile = INVALID_HANDLE_VALUE;
    }
    sWritesSinceFlush = 0;
}

static int SavePath(char *path, size_t capacity)
{
    char executable[MAX_PATH];
    DWORD length = GetModuleFileNameA(NULL, executable, sizeof(executable));
    if (length == 0 || length >= sizeof(executable))
        return -1;
    char *slash = strrchr(executable, '\\');
    if (slash == NULL)
        return -1;
    *slash = '\0'; // Remove executable name.
    slash = strrchr(executable, '\\');
    if (slash == NULL)
        return -1;
    *slash = '\0'; // Project root, next to build/.

    char directory[MAX_PATH];
    if (snprintf(directory, sizeof(directory), "%s\\saves", executable) >= (int)sizeof(directory))
        return -1;
    if (!CreateDirectoryA(directory, NULL) && GetLastError() != ERROR_ALREADY_EXISTS)
    {
        fprintf(stderr, "Flash: cannot create saves/ (Windows error %lu)\n",
                (unsigned long)GetLastError());
        return -1;
    }
    if (snprintf(path, capacity, "%s\\emerald-pc.sav", directory) >= (int)capacity)
        return -1;
    return 0;
}

int PortFlash_Open(void)
{
    char path[MAX_PATH];
    if (SavePath(path, sizeof(path)) != 0)
    {
        fprintf(stderr, "Flash: cannot locate saves/ beside project build/\n");
        return -1;
    }

    return PortFlash_OpenFile(path);
}

int PortFlash_OpenFile(const char *path)
{
    if (sBytes != NULL)
        return 0;
    if (path == NULL || path[0] == '\0')
        return -1;

    sFile = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ,
                        NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (sFile == INVALID_HANDLE_VALUE)
    {
        fprintf(stderr, "Flash: cannot open saves/emerald-pc.sav (Windows error %lu)\n",
                (unsigned long)GetLastError());
        return -1;
    }
    int created = GetLastError() != ERROR_ALREADY_EXISTS;
    if (created)
    {
        LARGE_INTEGER end;
        end.QuadPart = FLASH_SIZE;
        if (!SetFilePointerEx(sFile, end, NULL, FILE_BEGIN) || !SetEndOfFile(sFile))
        {
            fprintf(stderr, "Flash: cannot size new save file to 128 KiB\n");
            PortFlash_Close();
            return -1;
        }
    }
    else
    {
        LARGE_INTEGER size;
        if (!GetFileSizeEx(sFile, &size) || size.QuadPart != FLASH_SIZE)
        {
            fprintf(stderr, "Flash: existing save must be exactly 131072 bytes; left untouched\n");
            PortFlash_Close();
            return -1;
        }
    }

    sMapping = CreateFileMappingA(sFile, NULL, PAGE_READWRITE, 0, 0, NULL);
    if (sMapping != NULL)
        sBytes = MapViewOfFile(sMapping, FILE_MAP_READ | FILE_MAP_WRITE, 0, 0, FLASH_SIZE);
    if (sBytes == NULL)
    {
        fprintf(stderr, "Flash: cannot map save file (Windows error %lu)\n",
                (unsigned long)GetLastError());
        PortFlash_Close();
        return -1;
    }
    if (created)
    {
        memset(sBytes, 0xFF, FLASH_SIZE);
        if (!FlushViewOfFile(sBytes, FLASH_SIZE))
        {
            fprintf(stderr, "Flash: cannot initialize new save file\n");
            PortFlash_Close();
            return -1;
        }
    }
    atexit(PortFlash_Close);
    fprintf(stderr, "PC: 128 KiB flash ready (%s)\n",
            created ? "new" : "existing");
    return 0;
}

static int ValidRange(u16 sector, u32 offset, u32 size)
{
    return sBytes != NULL && sector < SECTOR_COUNT && offset <= SECTOR_SIZE
        && size <= SECTOR_SIZE - offset;
}

void PortFlash_Read(u16 sector, u32 offset, u8 *destination, u32 size)
{
    if (destination == NULL)
        return;
    if (!ValidRange(sector, offset, size))
    {
        fprintf(stderr, "Flash: invalid read sector %u offset %u size %u\n",
                sector, offset, size);
        memset(destination, 0xFF, size);
        return;
    }
    memcpy(destination, sBytes + sector * SECTOR_SIZE + offset, size);
}

u32 PortFlash_Verify(u16 sector, const u8 *source, u32 size)
{
    if (source == NULL || !ValidRange(sector, 0, size))
        return UINT32_MAX;
    const u8 *target = sBytes + sector * SECTOR_SIZE;
    for (u32 i = 0; i < size; ++i)
    {
        if (source[i] != target[i])
            return (u32)(uintptr_t)(target + i);
    }
    return 0;
}

u16 PortFlash_EraseSector(u16 sector)
{
    if (!ValidRange(sector, 0, SECTOR_SIZE))
        return FLASH_ERROR;
    u8 *start = sBytes + sector * SECTOR_SIZE;
    memset(start, 0xFF, SECTOR_SIZE);
    return FlushViewOfFile(start, SECTOR_SIZE) ? 0 : FLASH_ERROR;
}

u16 PortFlash_EraseChip(void)
{
    if (sBytes == NULL)
        return FLASH_ERROR;
    memset(sBytes, 0xFF, FLASH_SIZE);
    return FlushViewOfFile(sBytes, FLASH_SIZE) ? 0 : FLASH_ERROR;
}

u16 PortFlash_ProgramSector(u16 sector, u8 *source)
{
    if (source == NULL || !ValidRange(sector, 0, SECTOR_SIZE))
        return FLASH_ERROR;
    u8 *start = sBytes + sector * SECTOR_SIZE;
    memset(start, 0xFF, SECTOR_SIZE);
    memcpy(start, source, SECTOR_SIZE);
    return FlushViewOfFile(start, SECTOR_SIZE) ? 0 : FLASH_ERROR;
}

u16 PortFlash_ProgramByte(u16 sector, u32 offset, u8 value)
{
    if (!ValidRange(sector, offset, 1))
        return FLASH_ERROR;
    u8 *byte = sBytes + sector * SECTOR_SIZE + offset;
    if ((*byte & value) != value) // Flash programming cannot restore 0 bits.
        return FLASH_ERROR;
    *byte = value;
    if (++sWritesSinceFlush == 256)
    {
        sWritesSinceFlush = 0;
        if (!FlushViewOfFile(sBytes, FLASH_SIZE))
            return FLASH_ERROR;
    }
    return 0;
}

u16 PortFlash_WaitForWrite(u8 phase, u8 *address, u8 lastData)
{
    (void)phase;
    (void)address;
    (void)lastData;
    return FLASH_ERROR; // GBA command protocol must never be called on host.
}
