"""Optional Windows/GDB integration regression; uses an isolated local ROM/save."""

from pathlib import Path
import shutil
import subprocess
import sys


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build" / "wild-battle-regression"
    # Keep generated executables, ROM copies, saves and debugger output ignored.
    if not scratch.resolve().is_relative_to((project / "build").resolve()):
        raise SystemExit("Regression directory must remain inside build/")
    for name in ("build", "roms", "saves"):
        (scratch / name).mkdir(parents=True, exist_ok=True)
    roms = list((project / "roms").glob("*.gba"))
    if len(roms) != 1:
        raise SystemExit("Place exactly one legal Emerald ROM in roms/")
    for name in ("emerald-pc-diagnostic.exe", "SDL2.dll"):
        shutil.copy2(project / "build" / name, scratch / "build" / name)
    # Never open the user's save for writing. Start the known new-game route.
    shutil.copy2(roms[0], scratch / "roms" / "test.gba")
    (scratch / "saves" / "emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
    normal_save = scratch / "saves" / "emerald-pc.sav"
    normal_save.write_bytes(b"\xa5" * 131072)
    input_file = scratch / "input.txt"
    subprocess.run(
        [sys.executable, str(project / "port/tests/gameplay_smoke.py"), str(input_file)],
        check=True,
    )
    with input_file.open("a", encoding="ascii") as output:
        for frame in range(31500, 36900, 40):
            output.write(f"{frame} {frame + 1} A\n")

    # Fixture setup uses real game functions. The battle runs through its normal
    # task, transition, controller and script paths, with A selecting the move.
    commands = r"""
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT build/wild-battle-regression/input.txt
set environment EMERALD_PC_STOP_FRAME 30500
break Port_ExitCleanly
run
printf "FIXTURE frame=%u\n", sDiagnosticFrame
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address + 4, 2)) == bytes((0, 9)), "Expected Littleroot house exit"
end
call (void)CreateMon((void *)&gPlayerParty,280,5,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 1
call (void)FlagSet(0x860)
call (void)SetWarpDestination(0,16,-1,10,10)
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = 31000
return
continue
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address + 4, 2)) == bytes((0, 16)), "Battle fixture must be on Route 101"
end
printf "ROUTE101 fixture frame=%u\n", sDiagnosticFrame
call (void)CreateMon((void *)&gEnemyParty,286,2,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
call (void)BattleSetup_StartWildBattle()
set var sStopFrame = 37000
return
break CB2_EndWildBattle
commands
silent
printf "BATTLE END frame=%u outcome=%u\n", sDiagnosticFrame, *(unsigned char *)&gBattleOutcome
disable 2
continue
end
continue
printf "STOP frame=%u\n", sDiagnosticFrame
bt
dump binary memory build/wild-battle-regression/frame.raw &sPixels ((char *)&sPixels)+153600
continue
quit
"""
    script = scratch / "test.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "gdb.log"
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            ["gdb", "-batch", "-x", str(script),
             str(scratch / "build" / "emerald-pc-diagnostic.exe")],
            cwd=project, stdout=output, stderr=subprocess.STDOUT, timeout=600,
        )
    text = log.read_text(encoding="utf-8", errors="replace")
    if normal_save.read_bytes() != b"\xa5" * 131072:
        raise SystemExit("Diagnostic executable modified the normal save")
    won = any("BATTLE END frame=" in line and "outcome=1" in line
              for line in text.splitlines())
    if (result.returncode or "received signal" in text or not won
            or "ROUTE101 fixture frame=31000" not in text
            or "STOP frame=37000" not in text or "exited normally" not in text):
        raise SystemExit(f"Wild battle regression failed; inspect {log}")
    print(f"PASS wild battle: victory, return to map and clean exit; {log}")


if __name__ == "__main__":
    main()
