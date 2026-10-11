"""Directed, continuous NPC-script progression; not an unassisted playthrough."""
import json
from game_fixture import PROJECT, prepare, run

stages = [
    ("PetalburgCity_Gym", "Norman", 4, 108, None, 2),
    ("RustboroCity_Gym", "Roxanne", 5, 3, 0, 3),
    ("DewfordTown_Gym", "Brawly", 4, 4, 1, 4),
    ("MauvilleCity_Gym", "Wattson", 5, 3, 2, 5),
    ("LavaridgeTown_Gym_1F", "Flannery", 6, 3, 3, 6),
]
groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
maps = {name: (group, index) for group, key in enumerate(groups["group_order"])
        for index, name in enumerate(groups[key])}
inputs = "".join(f"{frame} {frame+1} A\n" for frame in range(31400, 112000, 20))
scratch, commands = prepare("campaign-script-chain", inputs)
commands += """
call (void)CreateMon((void *)&gPlayerParty,285,80,32,0,0,0,0)
call (void)SetMonMoveSlot((void *)&gPlayerParty,57,0)
break CB2_EndTrainerBattle
commands
silent
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1
end
printf "CAMPAIGN trainer victory frame=%u\\n", sDiagnosticFrame
continue
end
"""
markers = []
for number, (name, npc, x, y, badge, progress) in enumerate(stages):
    group, index = maps[name]
    mapdata = json.loads((PROJECT / f"pokeemerald/data/maps/{name}/map.json").read_text(encoding="utf-8"))
    obj = next(i for i, obj in enumerate(mapdata["object_events"], 1)
               if obj["script"] == f"{name}_EventScript_{npc}")
    commands += f"""
call (void)ResetInitialPlayerAvatarState()
call (void)ScriptContext_Init()
call (void)UnlockPlayerFieldControls()
set *(unsigned int *)&gFieldCallback = 0
set *(unsigned int *)&gFieldCallback2 = 0
call (void)SetWarpDestination({group},{index},-1,{x},{y})
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = sDiagnosticFrame + 300
return
continue
set *(unsigned short *)&gSpecialVar_LastTalked = {obj}
set *(unsigned char *)&gSelectedObjectEvent = (unsigned char)GetObjectEventIdByLocalIdAndMap({obj},{index},{group})
set *(unsigned short *)&gSpecialVar_Facing = 2
call (void)ScriptContext_SetupScript((void *)&{name}_EventScript_{npc})
set $progress_offset = (unsigned int)GetVarPointer(0x4085) - *(unsigned int *)&gSaveBlock1Ptr
break *ScrCmd_end if *(unsigned short *)(*(unsigned int *)&gSaveBlock1Ptr+$progress_offset) == {progress} && *(unsigned int *)($esp+4) == (unsigned int)&sGlobalScriptContext
commands
silent
set var sStopFrame = sDiagnosticFrame + 2
disable {4+number}
continue
end
set var sStopFrame = sDiagnosticFrame + 20000
return
continue
python
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x4085)")) == {progress}, "Norman progression"
assert int(gdb.parse_and_eval("*(unsigned char *)&sGlobalScriptContextStatus")) == 2, "NPC script did not finish"
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
"""
    for flag in range(4):
        commands += f'assert int(gdb.parse_and_eval("(int)FlagGet({0x867+flag})")) == {int(badge is not None and flag <= badge)}, "Badge {flag+1}"\n'
    commands += f"""assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "CAMPAIGN {npc} PROGRESS {progress} PASS\\n"
dump binary memory build/campaign-script-chain/{npc}.raw &sPixels ((char *)&sPixels)+153600
"""
    markers.append(f"CAMPAIGN {npc} PROGRESS {progress} PASS")
commands += "continue\nquit\n"
print("PASS continuous Wally/four-badge script chain;", run(scratch, commands, markers))
