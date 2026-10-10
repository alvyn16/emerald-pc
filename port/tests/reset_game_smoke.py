"""Real normal-executable restart fixtures, isolated under build/.

GDB changes only process memory to request keyboard/game reset. A second
debugger verifies the actual replacement process and closes it normally.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess
import os

from process_watchdog import run_logged


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build/save reset regression"
    save_source = project / "build/save-game-regression/two-slots.sav"
    if not save_source.is_file():
        raise SystemExit("Run save_game_smoke.py first")
    for directory in ("build", "roms", "saves", "outside cwd"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    module = scratch / "build/emerald-pc.exe"
    # Process inventory is restricted to this exact isolated executable path.
    inventory = scratch / "processes.ps1"
    inventory.write_text('''param([string]$Target)
@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $Target } |
Select-Object ProcessId, ParentProcessId) | ConvertTo-Json -Compress
''')
    powershell = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")

    def processes() -> list:
        result = subprocess.run([powershell, "-NoProfile", "-File", str(inventory), str(module)],
                                capture_output=True, text=True, timeout=20, check=True)
        text = result.stdout.strip()
        data = json.loads(text) if text else []
        return data if isinstance(data, list) else [data]

    if processes():
        raise SystemExit("The isolated reset executable is already running")
    for filename in ("emerald-pc.exe", "SDL2.dll"):
        shutil.copy2(project / "build" / filename, scratch / "build" / filename)
    roms = list((project / "roms").glob("*.gba"))
    if len(roms) != 1:
        raise SystemExit("Exactly one legal ROM is required")
    shutil.copy2(roms[0], scratch / "roms/test.gba")
    save = scratch / "saves/emerald-pc.sav"
    saved = save_source.read_bytes()
    save.write_bytes(saved)
    cwd = scratch / "outside cwd"
    for mode in ("keyboard", "game"):
        commands = r'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
break ReadKeys
run
delete 1
python
print("RESET PARENT pid=%d" % gdb.selected_inferior().pid, flush=True)
end
set *(unsigned int *)&sMultiplier = 4
REQUEST_RESET
break Port_ExitCleanly
continue
printf "RESET replacement spawned\n"
continue
quit
'''
        request = ("set *(unsigned short *)0x04000130 = 0x03f0"
                   if mode == "keyboard" else "set $pc = (unsigned int)&DoSoftReset")
        script = scratch / f"{mode}-parent.gdb"
        script.write_text(commands.replace("REQUEST_RESET", request), encoding="ascii")
        log = scratch / f"{mode}-parent.log"
        child = None
        try:
            result = run_logged(["gdb", "-batch", "-x", str(script), str(module)],
                                cwd, log, "RESET PARENT", timeout=60, stall_timeout=30)
            text = log.read_text(errors="replace")
            assert result == 0 and "exited normally" in text and "replacement spawned" in text, text
            parent = int(re.search(r"RESET PARENT pid=(\d+)", text)[1])
            active = processes()
            assert len(active) == 1 and active[0]["ParentProcessId"] == parent, active
            child = active[0]["ProcessId"]
            assert child != parent
            commands = r'''
set pagination off
set confirm off
attach CHILD_PID
break PortHost_RunFrame
continue
delete 1
python
if int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) != 1:
    gdb.Breakpoint("LoadGameSave", temporary=True)
    gdb.execute("continue")
    gdb.execute("finish")
assert int(gdb.parse_and_eval("*(unsigned int *)&sMultiplier")) == 1, "Speed not reset"
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1, "Save not loaded"
assert int(gdb.parse_and_eval("*(unsigned int *)&gSaveCounter")) == 2, "Wrong save counter"
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 1, "Party count"
assert int(gdb.parse_and_eval("(unsigned int)GetMonData2((void *)&gPlayerParty,11)")) == 280
assert int(gdb.parse_and_eval("(unsigned int)GetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490))")) == 23456
end
printf "RESET CHILD verified speed=1 save=2\n"
set $pc = (unsigned int)&Port_ExitCleanly
continue
quit
'''
            script = scratch / f"{mode}-child.gdb"
            script.write_text(commands.replace("CHILD_PID", str(child)), encoding="ascii")
            log = scratch / f"{mode}-child.log"
            result = run_logged(["gdb", "-batch", "-x", str(script), str(module)],
                                cwd, log, "RESET CHILD", timeout=60, stall_timeout=30)
            text = log.read_text(errors="replace")
            assert result == 0 and "RESET CHILD verified" in text and "exited normally" in text, text
            assert not processes(), "A replacement process survived clean shutdown"
            assert save.read_bytes() == saved, "Reset modified the save"
            print(f"PASS reset {mode}: one replacement, speed 1, save intact and clean close")
        finally:
            # Exact fixture path was unused before this run; clean up only its
            # surviving processes if a debugger assertion/deadline failed.
            for process in processes():
                subprocess.run(["taskkill", "/PID", str(process["ProcessId"]), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Override only SpawnProcess's argument in debugger memory. The real
    # CreateProcessW must fail opening this missing executable, then cleanup
    # must run. The normal binary on disk and its spawner remain untouched.
    missing = scratch / "missing-replacement.exe"
    assert not missing.exists()
    commands = r'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
break ReadKeys
run
delete 1
set $pc = (unsigned int)&DoSoftReset
break *SpawnProcess
continue
set $missing = (unsigned int)malloc(1024)
python
assert int(gdb.parse_and_eval("$missing")) != 0
gdb.selected_inferior().write_memory(int(gdb.parse_and_eval("$missing")), MISSING_PATH)
end
set *(unsigned int *)($esp+4) = $missing
break ShutdownHost
continue
printf "RESET FAILURE cleanup reached\n"
continue
quit
'''
    commands = commands.replace("MISSING_PATH", repr((str(missing) + "\0").encode("utf-16-le")))
    script = scratch / "spawn-failure.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "spawn-failure.log"
    try:
        result = run_logged(["gdb", "-batch", "-x", str(script), str(module)],
                            cwd, log, "RESET FAILURE", timeout=60, stall_timeout=30)
        text = log.read_text(errors="replace")
        assert result == 0 and "Windows error 2" in text and "soft reset failed" in text, text
        assert "RESET FAILURE cleanup reached" in text and "exited with code 01" in text, text
        assert not processes() and save.read_bytes() == saved
        print("PASS reset failure: real CreateProcess error 2, cleanup reached, no replacement")
    finally:
        for process in processes():
            subprocess.run(["taskkill", "/PID", str(process["ProcessId"]), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
