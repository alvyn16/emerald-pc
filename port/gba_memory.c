#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include <psapi.h>

#include "gba_memory.h"

struct GbaRegion
{
    const char *name;
    uintptr_t address;
    size_t size;
    void *allocation;
};

static struct GbaRegion sRegions[] = {
    {"EWRAM",   0x02000000u, 0x40000u, NULL},
    {"IWRAM",   0x03000000u, 0x08000u, NULL},
    {"IO",      0x04000000u, 0x00400u, NULL},
    {"palette", 0x05000000u, 0x00400u, NULL},
    {"VRAM",    0x06000000u, 0x18000u, NULL},
    {"OAM",     0x07000000u, 0x00400u, NULL},
    {"ROM",     0x08000000u, 0x2000000u, NULL},
};

#define ROM_START ((unsigned char *)0x08000000u)
#define ROM_SIZE 0x02000000u

static int FindUserRom(char *path, size_t capacity)
{
    char module[MAX_PATH];
    DWORD length = GetModuleFileNameA(NULL, module, sizeof(module));
    if (length == 0 || length >= sizeof(module))
    {
        fprintf(stderr, "Cannot locate executable directory for roms/\n");
        return -1;
    }

    char *slash = strrchr(module, '\\');
    if (slash == NULL)
        return -1;
    *slash = '\0'; // Remove executable name (inside build/).
    slash = strrchr(module, '\\');
    if (slash == NULL)
        return -1;
    *slash = '\0'; // Project root.

    char pattern[MAX_PATH];
    if (snprintf(pattern, sizeof(pattern), "%s\\roms\\*.gba", module) >= (int)sizeof(pattern))
        return -1;

    WIN32_FIND_DATAA entry;
    HANDLE search = FindFirstFileA(pattern, &entry);
    if (search == INVALID_HANDLE_VALUE)
    {
        fprintf(stderr, "No .gba ROM found in project roms/ directory\n");
        return -1;
    }
    char firstName[MAX_PATH];
    if (snprintf(firstName, sizeof(firstName), "%s", entry.cFileName) >= (int)sizeof(firstName))
    {
        FindClose(search);
        return -1;
    }
    if (FindNextFileA(search, &entry))
    {
        FindClose(search);
        fprintf(stderr, "More than one .gba ROM found in roms/; keep exactly one\n");
        return -1;
    }
    DWORD scanError = GetLastError();
    FindClose(search);
    if (scanError != ERROR_NO_MORE_FILES)
    {
        fprintf(stderr, "Cannot enumerate roms/ (Windows error %lu)\n", (unsigned long)scanError);
        return -1;
    }
    if (snprintf(path, capacity, "%s\\roms\\%s", module, firstName) >= (int)capacity)
        return -1;
    return 0;
}

int Port_LoadGbaRom(void)
{
    char path[MAX_PATH];
    if (FindUserRom(path, sizeof(path)) != 0)
        return -1;

    HANDLE file = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL,
                              OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE)
    {
        fprintf(stderr, "Cannot open user ROM for reading (Windows error %lu)\n",
                (unsigned long)GetLastError());
        return -1;
    }

    LARGE_INTEGER size;
    if (!GetFileSizeEx(file, &size) || size.QuadPart <= 0 || size.QuadPart > ROM_SIZE)
    {
        fprintf(stderr, "User ROM must contain 1 to 33554432 bytes\n");
        CloseHandle(file);
        return -1;
    }

    memset(ROM_START, 0xFF, ROM_SIZE);
    DWORD read = 0;
    BOOL ok = ReadFile(file, ROM_START, (DWORD)size.QuadPart, &read, NULL);
    CloseHandle(file);
    if (!ok || read != (DWORD)size.QuadPart)
    {
        fprintf(stderr, "Could not read the complete user ROM\n");
        return -1;
    }

    /* The cartridge GPIO overlaps ROM header space. Memory writes here are
     * host-only; zero values plus the PORT_PC probe guard mean no RTC. */
    *(volatile uint16_t *)0x080000C4u = 0;
    *(volatile uint16_t *)0x080000C6u = 0;
    *(volatile uint16_t *)0x080000C8u = 0;
    fprintf(stderr, "PC: loaded %ld ROM bytes at 0x08000000; RTC GPIO absent\n",
            (long)size.QuadPart);
    return 0;
}

void Port_FreeGbaMemory(void)
{
    for (size_t i = 0; i < sizeof(sRegions) / sizeof(sRegions[0]); ++i)
    {
        if (sRegions[i].allocation != NULL)
        {
            VirtualFree(sRegions[i].allocation, 0, MEM_RELEASE);
            sRegions[i].allocation = NULL;
        }
    }
}

int Port_InitGbaMemory(void)
{
    for (size_t i = 0; i < sizeof(sRegions) / sizeof(sRegions[0]); ++i)
    {
        struct GbaRegion *region = &sRegions[i];
        void *address = (void *)region->address;
        region->allocation = VirtualAlloc(address, region->size,
                                          MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (region->allocation != address)
        {
            DWORD failure = GetLastError();
            MEMORY_BASIC_INFORMATION info;
            SIZE_T queried = VirtualQuery(address, &info, sizeof(info));
            fprintf(stderr, "Cannot map GBA %s at 0x%08" PRIXPTR
                            " (%zu bytes; Windows error %lu)\n",
                    region->name, region->address, region->size,
                    (unsigned long)failure);
            if (queried != 0)
            {
                char mappedPath[MAX_PATH] = {0};
                GetMappedFileNameA(GetCurrentProcess(), address, mappedPath, sizeof(mappedPath));
                fprintf(stderr, "Address occupied: allocation base %p, size %zu, state 0x%lx, type 0x%lx, file %s\n",
                        info.AllocationBase, (size_t)info.RegionSize,
                        (unsigned long)info.State, (unsigned long)info.Type,
                        mappedPath[0] ? mappedPath : "<none>");
            }
            Port_FreeGbaMemory();
            return -1;
        }
    }

    /* On GBA, one bits in KEYINPUT indicate released keys. */
    *(volatile uint16_t *)0x04000130u = 0x03FFu;
    return 0;
}
