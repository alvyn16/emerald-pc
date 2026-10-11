"""Safari admission, real ball capture and step-quota exit in one fixture."""
import json
from game_fixture import PROJECT, prepare, run

groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
maps = {name: (group, index) for group, key in enumerate(groups["group_order"])
        for index, name in enumerate(groups[key])}
entrance = maps["Route121_SafariZoneEntrance"]
south = maps["SafariZone_South"]
inputs = "".join(f"{n} {n+1} A\n" for n in range(31200, 62000, 40))
scratch, commands = prepare("safari-admission", inputs)
commands += f'''
call (int)AddBagItem(273,1)
call (void)SetWarpDestination({entrance[0]},{entrance[1]},-1,8,5)
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = 31300
return
continue
call (void)ScriptContext_SetupScript((void *)&Route121_SafariZoneEntrance_EventScript_EntranceCounterTrigger)
set var sStopFrame = 40000
return
continue
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes({south!r})
assert int(gdb.parse_and_eval("(unsigned int)GetMoney((void *)(%d+0x490))" % address)) == 4500
assert int(gdb.parse_and_eval("(unsigned int)GetSafariZoneFlag()")) == 1
assert int(gdb.parse_and_eval("*(unsigned char *)&gNumSafariBalls")) == 30
assert int(gdb.parse_and_eval("*(unsigned short *)&sSafariZoneStepCounter")) == 500
end
printf "SAFARI ADMISSION PASS\\n"
call (void)CreateMon((void *)&gEnemyParty,129,5,32,0,0,0,0)
call (void)SeedRng(0)
call (void)BattleSetup_StartWildBattle()
break HandleInputChooseAction
commands
silent
set ((unsigned char *)&gActionSelectionCursor)[*(unsigned char *)&gActiveBattler] = 0
set gMain.newKeys = 1
continue
end
break Cmd_trygivecaughtmonnick
commands
silent
set gMain.newKeys = 2
continue
end
set var sStopFrame = 52000
return
continue
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 7
assert 0 < int(gdb.parse_and_eval("*(unsigned char *)&gNumSafariBalls")) < 30
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 2
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100,11,0)")) == 129
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
end
printf "SAFARI CAPTURE PASS\\n"
disable 3 4
python
steps = int(gdb.parse_and_eval("*(unsigned short *)&sSafariZoneStepCounter"))
for step in range(steps):
    ended = int(gdb.parse_and_eval("(unsigned char)SafariZoneTakeStep()"))
    assert ended == int(step == steps-1)
end
set var sStopFrame = 61000
return
continue
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes({entrance!r})
assert int(gdb.parse_and_eval("(unsigned int)GetSafariZoneFlag()")) == 0
assert int(gdb.parse_and_eval("*(unsigned char *)&gNumSafariBalls")) == 0
assert int(gdb.parse_and_eval("*(unsigned short *)&sSafariZoneStepCounter")) == 0
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "SAFARI QUOTA EXIT PASS\\n"
dump binary memory build/safari-admission/exit.raw &sPixels ((char *)&sPixels)+153600
continue
quit
'''
print("PASS Safari admission/capture/step expiry;", run(scratch, commands,
      ["SAFARI ADMISSION PASS", "SAFARI CAPTURE PASS", "SAFARI QUOTA EXIT PASS"]))
