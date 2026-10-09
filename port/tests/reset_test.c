#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
#include <windows.h>

#include "host_flash.h"
#include "port_reset.h"

static wchar_t sPath[MAX_PATH];
static int sSpawned;
static int sFailSpawn;

static int MockSpawner(const wchar_t *module, wchar_t *commandLine)
{
    wchar_t expected[32768];
    assert(GetModuleFileNameW(NULL, expected, 32768) > 0);
    assert(wcscmp(module, expected) == 0);
    assert(commandLine != NULL && commandLine[0] != 0);

    // The original file mapping must already be closed. Its handle was
    // opened for writing with FILE_SHARE_READ, so this would otherwise fail.
    HANDLE file = CreateFileW(sPath, GENERIC_READ | GENERIC_WRITE,
                              FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    assert(file != INVALID_HANDLE_VALUE);
    CloseHandle(file);
    sSpawned++;
    return !sFailSpawn;
}

int main(void)
{
    char path[MAX_PATH];
    snprintf(path, sizeof(path), "build/reset-test-%lu.sav",
             (unsigned long)GetCurrentProcessId());
    assert(MultiByteToWideChar(CP_UTF8, 0, path, -1, sPath, MAX_PATH) > 0);
    assert(PortFlash_OpenFile(path) == 0);
    PortReset_SetSpawner(MockSpawner);
    assert(PortReset_Restart() == 0);
    assert(sSpawned == 1);

    assert(PortFlash_OpenFile(path) == 0);
    sFailSpawn = 1;
    assert(PortReset_Restart() == -1);
    assert(sSpawned == 2);
    PortReset_SetSpawner(NULL);
    assert(DeleteFileA(path));
    return 0;
}
