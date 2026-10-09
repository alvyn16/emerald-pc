#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <windows.h>

#include "host_flash.h"
#include "port_reset.h"

static int SpawnProcess(const wchar_t *module, wchar_t *commandLine)
{
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(module, commandLine, NULL, NULL, FALSE, 0,
                        NULL, NULL, &startup, &process))
    {
        fprintf(stderr, "PC: cannot restart executable (Windows error %lu)\n",
                (unsigned long)GetLastError());
        return 0;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 1;
}

static PortResetSpawner sSpawner = SpawnProcess;

void PortReset_SetSpawner(PortResetSpawner spawner)
{
    sSpawner = spawner != NULL ? spawner : SpawnProcess;
}

int PortReset_Restart(void)
{
    wchar_t module[32768];
    DWORD length = GetModuleFileNameW(NULL, module, sizeof(module) / sizeof(module[0]));
    if (length == 0 || length >= sizeof(module) / sizeof(module[0]))
    {
        fprintf(stderr, "PC: cannot determine executable path for soft reset\n");
        return -1;
    }
    const wchar_t *original = GetCommandLineW();
    wchar_t *commandLine = malloc((wcslen(original) + 1) * sizeof(*commandLine));
    if (commandLine == NULL)
        return -1;
    wcscpy(commandLine, original);

    PortFlash_Close();
    const int started = sSpawner(module, commandLine);
    free(commandLine);
    if (!started)
    {
        fprintf(stderr, "PC: soft reset failed to launch a replacement process\n");
        return -1;
    }
    return 0;
}
