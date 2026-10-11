"""Optional Windows/GDB integration regression; uses an isolated local ROM/save."""

from pathlib import Path
import argparse
import shutil
import subprocess
import sys

from process_watchdog import run_logged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--battle-speed', type=int, choices=(1, 4),
                        help='Pace only the battle at 1x/4x; route setup stays fast')
    parser.add_argument("--scenario", choices=("victory", "loss", "run", "catch"), default="victory")
    parser.add_argument("--quick", action="store_true", help="Controlled setup instead of replaying intro UI")
    options = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    regressionName = 'wild-battle-regression'
    if options.battle_speed:
        regressionName += f'-{options.battle_speed}x'
    if options.scenario != "victory": regressionName += "-" + options.scenario
    scratch = project / "build" / regressionName
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
break PortHost_RunFrame if sDiagnosticFrame == 31300
commands
silent
printf "BATTLE CAPTURE frame=%u\n", sDiagnosticFrame
dump binary memory build/wild-battle-regression/battle.raw &sPixels ((char *)&sPixels)+153600
disable 3
continue
end
continue
printf "STOP frame=%u\n", sDiagnosticFrame
bt
dump binary memory build/wild-battle-regression/frame.raw &sPixels ((char *)&sPixels)+153600
continue
quit
"""
    if options.battle_speed:
        commands = commands.replace('call (void)BattleSetup_StartWildBattle()',
            f'set var sFast = 0\nset var sMultiplier = {options.battle_speed}\n'
            'call (void)BattleSetup_StartWildBattle()')
        commands = commands.replace('wild-battle-regression/', regressionName + '/')
    commands = commands.replace('wild-battle-regression/', regressionName + '/')
    scenario = options.scenario
    configs = {"victory": (280,5,286,2,1), "loss": (392,2,286,50,2),
               "run": (277,80,288,3,4), "catch": (283,8,392,4,7)}
    player, level, enemy, enemy_level, outcome = configs[scenario]
    commands = commands.replace('gPlayerParty,280,5,32', f'gPlayerParty,{player},{level},32')
    commands = commands.replace('gEnemyParty,286,2,32', f'gEnemyParty,{enemy},{enemy_level},32')
    commands = commands.replace('call (void)FlagSet(0x860)',
        'call (void)FlagSet(0x860)\ncall (void)SetLastHealLocationWarp(1)\ncall (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),5000)')
    commands = commands.replace('call (void)BattleSetup_StartWildBattle()',
        'set $start_hp = (unsigned int)GetMonData3((void *)&gPlayerParty,57,0)\n'
        'set $start_exp = (unsigned int)GetMonData3((void *)&gPlayerParty,25,0)\n'
        + ('call (int)AddBagItem(1,1)\nset *((unsigned char *)&gBagPosition + 5) = 1\n' if scenario == "catch" else '')
        + 'call (void)BattleSetup_StartWildBattle()')
    hooks = ""
    if scenario in ("run", "catch"):
        hooks += f"""
break HandleInputChooseAction
commands
silent
set ((unsigned char *)&gActionSelectionCursor)[*(unsigned char *)&gActiveBattler] = {3 if scenario == 'run' else 1}
set gMain.newKeys = 1
continue
end
"""
    if scenario == "catch":
        hooks += """
break Cmd_trygivecaughtmonnick
commands
silent
set gMain.newKeys = 2
continue
end
"""
    commands = commands.replace('continue\nprintf "STOP', hooks + 'continue\nprintf "STOP')
    checks = f"""
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == {outcome}
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,57,0)")) > 0
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
location = bytes(gdb.selected_inferior().read_memory(address + 4, 2))
assert location == {bytes((1,1)) if scenario == 'loss' else bytes((0,16))!r}, location
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == {2 if scenario == 'catch' else 1}
"""
    if scenario == "victory":
        checks += 'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,25,0)")) > int(gdb.parse_and_eval("$start_exp"))\n'
    if scenario == "loss":
        checks += 'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,57,0)")) == int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,58,0)"))\n'
    if scenario == "run":
        checks += 'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,57,0)")) == int(gdb.parse_and_eval("$start_hp"))\n'
    if scenario == "catch":
        checks += f'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty + 100,11,0)")) == {enemy}\nassert int(gdb.parse_and_eval("(int)CheckBagHasItem(1,1)")) == 0\n'
    checks += f'assert int(gdb.parse_and_eval("(unsigned int)GetMoney((void *)(%d+0x490))" % address)) {"< 5000" if scenario == "loss" else "== 5000"}\n'
    checks += f'end\nprintf "SEMANTIC {scenario} PASS\\n"\n'
    commands = commands.replace('bt\ndump binary memory', checks + 'bt\ndump binary memory')
    if scenario != "victory" or options.quick:
        # Controlled scenario setup; skip repeating the separately tested UI route.
        start = commands.index('set environment EMERALD_PC_STOP_FRAME 30500')
        end = commands.index('call (void)CreateMon((void *)&gPlayerParty', start)
        prefix = """set environment EMERALD_PC_STOP_FRAME 31000
break Port_ExitCleanly
break PortHost_RunFrame
run
call (void)SetSaveBlocksPointers(0)
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock2Ptr"))
gdb.selected_inferior().write_memory(address, bytes((0xce,0xbf,0xcd,0xce,0xff,0xff,0xff,0xff)))
end
call (void)NewGameInitData()
call (void)ResetInitialPlayerAvatarState()
call (void)ScriptContext_Init()
call (void)UnlockPlayerFieldControls()
call (void)SetMainCallback1((void *)CB1_Overworld)
set *(void **)&gFieldCallback = 0
set *(void **)&gFieldCallback2 = 0
set var sDiagnosticFrame = 30500
delete 2
"""
        commands = commands[:start] + prefix + commands[end:]
        commands = commands.replace('disable 3', 'disable 4').replace('disable 2', 'disable 3')
    script = scratch / "test.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "gdb.log"
    result = run_logged(
        ["gdb", "-batch", "-x", str(script),
         str(scratch / "build" / "emerald-pc-diagnostic.exe")],
        project, log, "PC diagnostic: frame=",
    )
    text = log.read_text(encoding="utf-8", errors="replace")
    if normal_save.read_bytes() != b"\xa5" * 131072:
        raise SystemExit("Diagnostic executable modified the normal save")
    won = any("BATTLE END frame=" in line and f"outcome={outcome}" in line
              for line in text.splitlines())
    if (result or "received signal" in text or not won
            or "invalid compressed stream" in text
            or "BATTLE CAPTURE frame=31300" not in text
            or f"SEMANTIC {scenario} PASS" not in text
            or "ROUTE101 fixture frame=31000" not in text
            or "STOP frame=37000" not in text or "exited normally" not in text):
        raise SystemExit(f"Wild battle regression failed; inspect {log}")
    print(f"PASS wild battle {scenario}: outcome {outcome}, semantic state and clean exit; {log}")


if __name__ == "__main__":
    main()
