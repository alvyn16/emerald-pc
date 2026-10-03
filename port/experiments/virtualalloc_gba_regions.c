#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>

struct Region
{
    const char *name;
    uintptr_t address;
    SIZE_T size;
    void *allocation;
};

int main(void)
{
    struct Region regions[] = {
        {"EWRAM",   0x02000000, 0x40000, NULL},
        {"IWRAM",   0x03000000, 0x08000, NULL},
        {"IO",      0x04000000, 0x00400, NULL},
        {"palette", 0x05000000, 0x00400, NULL},
        {"VRAM",    0x06000000, 0x18000, NULL},
        {"OAM",     0x07000000, 0x00400, NULL},
    };
    int failed = 0;

    for (size_t i = 0; i < sizeof(regions) / sizeof(regions[0]); i++)
    {
        struct Region *r = &regions[i];
        r->allocation = VirtualAlloc((void *)r->address, r->size,
                                     MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (r->allocation != (void *)r->address)
        {
            printf("%s 0x%08llX: FAIL (GetLastError=%lu, returned=%p)\n",
                   r->name, (unsigned long long)r->address,
                   GetLastError(), r->allocation);
            failed = 1;
            continue;
        }

        volatile unsigned char *bytes = r->allocation;
        bytes[0] = 0x5a;
        bytes[r->size - 1] = 0xa5;
        if (bytes[0] != 0x5a || bytes[r->size - 1] != 0xa5)
            failed = 1;
        printf("%s 0x%08llX size 0x%llX: %s\n", r->name,
               (unsigned long long)r->address, (unsigned long long)r->size,
               failed ? "CHECK" : "OK");
    }

    for (size_t i = 0; i < sizeof(regions) / sizeof(regions[0]); i++)
        if (regions[i].allocation != NULL)
            VirtualFree(regions[i].allocation, 0, MEM_RELEASE);
    return failed;
}
