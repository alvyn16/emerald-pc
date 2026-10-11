"""Directed, continuous NPC-script progression; not an unassisted playthrough."""
import argparse
import json
from game_fixture import PROJECT, prepare, run

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--through-four", action="store_true")
mode.add_argument("--from-four-save", action="store_true")
mode.add_argument("--from-seven-save", action="store_true")
args = parser.parse_args()
stages = [
    ("PetalburgCity_Gym", "Norman", 4, 108, None, 2),
    ("RustboroCity_Gym", "Roxanne", 5, 3, 0, 3),
    ("DewfordTown_Gym", "Brawly", 4, 4, 1, 4),
    ("MauvilleCity_Gym", "Wattson", 5, 3, 2, 5),
    ("LavaridgeTown_Gym_1F", "Flannery", 6, 3, 3, 6),
    ("PetalburgCity_Gym", "Norman", 4, 3, 4, 7),
    ("FortreeCity_Gym", "Winona", 15, 3, 5, 7),
    ("MossdeepCity_Gym", "TateAndLiza", 23, 8, 6, 7),
    ("SootopolisCity_Gym_1F", "Juan", 8, 3, 7, 7),
]
if args.through_four:
    stages = stages[:5]
if args.from_four_save:
    stages = stages[5:]
if args.from_seven_save:
    stages = stages[8:]
groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
maps = {name: (group, index) for group, key in enumerate(groups["group_order"])
        for index, name in enumerate(groups[key])}
inputs = "".join(f"{frame} {frame+1} A\n" for frame in range(31400, 190000, 40))
save_path = PROJECT / "build/campaign-script-chain/saves/emerald-pc-diagnostic.sav"
starting_badges = 7 if args.from_seven_save else 4
checkpoint = save_path.parents[1] / f"checkpoint-{starting_badges}.sav"
saved = (checkpoint if checkpoint.exists() else save_path).read_bytes() if args.from_four_save or args.from_seven_save else None
scratch, commands = prepare("campaign-script-chain", inputs)
if saved is not None:
    checkpoint.write_bytes(saved)
    save_path.write_bytes(saved)
    commands = commands.replace("call (void)NewGameInitData()", "call (unsigned char)LoadGameSave(0)")
    for line in ("call (void)CreateMon((void *)&gPlayerParty,283,8,32,0,0,0,0)",
                 "set *(unsigned char *)&gPlayerPartyCount = 1",
                 "call (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),5000)"):
        commands = commands.replace(line, "")
    commands += f'''python
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x4085)")) == {6 if starting_badges == 4 else 7}
for badge in range(8):
    assert int(gdb.parse_and_eval("(int)FlagGet(%d)" % (0x867+badge))) == int(badge < {starting_badges})
end
'''
else:
    commands += "call (void)CreateMon((void *)&gPlayerParty,285,80,32,0,0,0,0)\n"
commands += """
break CB2_EndTrainerBattle
commands
silent
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1
end
printf "CAMPAIGN trainer victory frame=%u\\n", sDiagnosticFrame
continue
end
break Task_HandleChooseMonInput
commands
silent
python
active = int(gdb.parse_and_eval("((unsigned short *)&gBattlerPartyIndexes)[0]"))
count = int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount"))
slot = next(i for i in range(count) if int(gdb.parse_and_eval("(unsigned char)GetPartyIdFromBattleSlot(%d)" % i)) != active and int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,57,0)" % i)) > 0)
gdb.execute("set *((signed char *)&gPartyMenu+9) = %d" % slot)
gdb.execute("set gMain.newKeys = 1")
end
continue
end
"""
markers = []
for number, (name, npc, x, y, badge, progress) in enumerate(stages):
    group, index = maps[name]
    mapdata = json.loads((PROJECT / f"pokeemerald/data/maps/{name}/map.json").read_text(encoding="utf-8"))
    obj = next(i for i, obj in enumerate(mapdata["object_events"], 1)
               if obj["script"] == f"{name}_EventScript_{npc}")
    if name != "PetalburgCity_Gym":
        x, y = mapdata["object_events"][obj-1]["x"], mapdata["object_events"][obj-1]["y"] + 1
    if badge == 6:
        commands += '''call (void)CreateMon((char *)&gPlayerParty+100,283,80,32,0,0,0,0)
call (void)SetMonMoveSlot((char *)&gPlayerParty+100,57,0)
set *(unsigned char *)&gPlayerPartyCount = 2
'''
    move = 58 if badge == 5 else 89 if badge == 7 else 57
    commands += f"call (void)SetMonMoveSlot((void *)&gPlayerParty,{move},0)\ncall (void)HealPlayerParty()\n"
    # Resolve save offsets rather than retaining pointers across map warps.
    badge_condition = ""
    if badge is not None:
        flag = 0x867 + badge
        commands += f"set $badge_offset = (unsigned int)GetFlagPointer({flag}) - *(unsigned int *)&gSaveBlock1Ptr\n"
        badge_condition = f" && (*(unsigned char *)(*(unsigned int *)&gSaveBlock1Ptr+$badge_offset) & {1 << (flag % 8)})"
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
break *ScrCmd_end if *(unsigned short *)(*(unsigned int *)&gSaveBlock1Ptr+$progress_offset) == {progress}{badge_condition} && *(unsigned int *)($esp+4) == (unsigned int)&sGlobalScriptContext
commands
silent
set var sStopFrame = sDiagnosticFrame + 2
disable {5+number}
continue
end
set var sStopFrame = sDiagnosticFrame + 30000
return
continue
python
print("CHECKPOINT {npc}", int(gdb.parse_and_eval("sDiagnosticFrame")))
for task in range(16):
    if int(gdb.parse_and_eval("*((unsigned char *)&gTasks+40*%d+4)" % task)):
        gdb.execute("info symbol %d" % int(gdb.parse_and_eval("*(unsigned int *)((char *)&gTasks+40*%d)" % task)))
print("party HP", [int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,57,0)" % i)) for i in range(int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")))])
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x4085)")) == {progress}, "Norman progression"
assert int(gdb.parse_and_eval("*(unsigned char *)&sGlobalScriptContextStatus")) == 2, "NPC script did not finish"
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
"""
    for flag in range(8):
        commands += f'assert int(gdb.parse_and_eval("(int)FlagGet({0x867+flag})")) == {int(badge is not None and flag <= badge)}, "Badge {flag+1}"\n'
    if badge is not None:
        commands += f'assert int(gdb.parse_and_eval("(int)HasTrainerBeenFought({265+badge})")) == 1\n'
        commands += f'assert int(gdb.parse_and_eval("(int)FlagGet({0xA5+badge})")) == 1, "Leader TM delivery"\n'
    if badge == 4:
        commands += 'assert int(gdb.parse_and_eval("(int)FlagGet(0x7A)")) == 1, "Surf delivery"\n'
    commands += f"""assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)")) == 285
assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "CAMPAIGN {npc} PROGRESS {progress} PASS\\n"
dump binary memory build/campaign-script-chain/{npc}-{progress}.raw &sPixels ((char *)&sPixels)+153600
"""
    markers.append(f"CAMPAIGN {npc} PROGRESS {progress} PASS")
    if badge in (3, 6):
        commands += f'''python
from pathlib import Path
save = Path("build/campaign-script-chain/saves/emerald-pc-diagnostic.sav")
Path("build/campaign-script-chain/checkpoint-{badge+1}.sav").write_bytes(save.read_bytes())
end
'''
commands += "continue\nquit\n"
log = run(scratch, commands, markers, timeout=1200)
log.replace(scratch / ("progress-eight.log" if not args.through_four else "progress-four.log"))
print("PASS continuous NPC badge script chain")
