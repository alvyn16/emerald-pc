#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
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
};

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
