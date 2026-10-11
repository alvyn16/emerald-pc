"""Real Elite Four NPC scripts continuing the measured eight-badge save."""
import json
from game_fixture import PROJECT, prepare_saved, run

source = PROJECT / "build/campaign-script-chain/saves/emerald-pc-diagnostic.sav"
inputs = "".join(f"{n} {n+1} A\n" for n in range(31200, 190000, 40))
scratch, commands = prepare_saved("league-campaign", inputs, source)
groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
maps = {name: (group, index) for group, key in enumerate(groups["group_order"])
        for index, name in enumerate(groups[key])}
commands += '''python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x4085)")) == 7
for badge in range(8):
    assert int(gdb.parse_and_eval("(int)FlagGet(%d)" % (0x867+badge))) == 1
assert int(gdb.parse_and_eval("(int)FlagGet(0x864)")) == 0
end
break Cmd_yesnobox
commands
silent
set gMain.newKeys = 2
continue
end
break HandleInputChooseMove
commands
silent
python
active = int(gdb.parse_and_eval("*(unsigned char *)&gActiveBattler"))
party = int(gdb.parse_and_eval("((unsigned short *)&gBattlerPartyIndexes)[%d]" % active))
preferred = int(gdb.parse_and_eval("$preferred"))
slots = [preferred] + [i for i in range(4) if i != preferred]
slot = next(i for i in slots if int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,%d,0)" % (party,17+i))) > 0)
gdb.execute("set ((unsigned char *)&gMoveSelectionCursor)[%d] = %d" % (active,slot))
gdb.execute("set gMain.newKeys = 1")
end
continue
end
'''
markers = []
for number, npc in enumerate(("Sidney", "Phoebe", "Glacia", "Drake")):
    name = f"EverGrandeCity_{npc}sRoom"
    group, index = maps[name]
    flag = 0x4FB + number
    preferred = 1 if npc in ("Sidney", "Drake") else 3 if npc == "Glacia" else 2
    commands += "".join(f"call (void)SetMonMoveSlot((void *)&gPlayerParty,{move},{slot})\n" for slot,move in enumerate((57,58,89,157)))
    commands += f'''
set $preferred = {preferred}
call (void)HealPlayerParty()
call (void)ResetInitialPlayerAvatarState()
call (void)ScriptContext_Init()
call (void)UnlockPlayerFieldControls()
set *(unsigned int *)&gFieldCallback = 0
set *(unsigned int *)&gFieldCallback2 = 0
call (void)SetWarpDestination({group},{index},-1,6,13)
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = sDiagnosticFrame + 1200
return
continue
python
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x409C)")) == {number+1}, "Room entry script"
assert int(gdb.parse_and_eval("*(unsigned char *)&sGlobalScriptContextStatus")) == 2
end
set *(unsigned short *)&gSpecialVar_LastTalked = 1
set *(unsigned char *)&gSelectedObjectEvent = (unsigned char)GetObjectEventIdByLocalIdAndMap(1,{index},{group})
set *(unsigned short *)&gSpecialVar_Facing = 2
call (void)ScriptContext_SetupScript((void *)&{name}_EventScript_{npc})
set $offset = (unsigned int)GetFlagPointer({flag}) - *(unsigned int *)&gSaveBlock1Ptr
break *ScrCmd_end if (*(unsigned char *)(*(unsigned int *)&gSaveBlock1Ptr+$offset) & {1 << (flag % 8)}) && *(unsigned int *)($esp+4) == (unsigned int)&sGlobalScriptContext
commands
silent
set var sStopFrame = sDiagnosticFrame + 2
disable {5+number}
continue
end
set var sStopFrame = sDiagnosticFrame + 30000
return
continue
dump binary memory build/league-campaign/{npc}-stop.raw &sPixels ((char *)&sPixels)+153600
python
print("LEAGUE checkpoint {npc}", int(gdb.parse_and_eval("sDiagnosticFrame")))
print("PP", [int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,%d,0)" % (17+i))) for i in range(4)])
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1
assert int(gdb.parse_and_eval("(int)FlagGet({flag})")) == 1
assert int(gdb.parse_and_eval("(int)HasTrainerBeenFought({261+number})")) == 1
assert int(gdb.parse_and_eval("*(unsigned char *)&sGlobalScriptContextStatus")) == 2
assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "LEAGUE {npc} SCRIPT PASS\\n"
dump binary memory build/league-campaign/{npc}.raw &sPixels ((char *)&sPixels)+153600
'''
    markers.append(f"LEAGUE {npc} SCRIPT PASS")
commands += "continue\nquit\n"
log = run(scratch, commands, markers, timeout=1200)
log.replace(scratch / "elite-four.log")
print("PASS Elite Four scripts continuing eight-badge save")
