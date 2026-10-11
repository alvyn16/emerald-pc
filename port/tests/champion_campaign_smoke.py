"""Wallace entry, Hall of Fame and credits from the measured Elite Four save."""
import json
from game_fixture import PROJECT, prepare_saved, run

source = PROJECT / "build/league-campaign/saves/emerald-pc-diagnostic.sav"
inputs = "".join(f"{n} {n+1} A\n" for n in range(31200, 185000, 40))
scratch, commands = prepare_saved("champion-campaign", inputs, source)
groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
group, index = next((g, names.index("EverGrandeCity_ChampionsRoom"))
                    for g,key in enumerate(groups["group_order"])
                    if "EverGrandeCity_ChampionsRoom" in (names := groups[key]))
commands += '''python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1
assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x409C)")) == 4
for flag in list(range(0x867,0x86F))+list(range(0x4FB,0x4FF)):
    assert int(gdb.parse_and_eval("(int)FlagGet(%d)" % flag)) == 1
assert int(gdb.parse_and_eval("(int)FlagGet(0x864)")) == 0
end
call (void)HealPlayerParty()
call (void)CreateMon((char *)&gPlayerParty+200,400,80,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 3
'''
for slot,move in enumerate((57,58,89,157)):
    commands += f"call (void)SetMonMoveSlot((void *)&gPlayerParty,{move},{slot})\n"
for slot,move in enumerate((94,9,89,157)):
    commands += f"call (void)SetMonMoveSlot((char *)&gPlayerParty+200,{move},{slot})\n"
# Created fixture mons must be registered as owned, as a real acquisition does.
for national in (258,260,376):
    for operation in (2,3):
        commands += f"call (unsigned char)GetSetPokedexFlag({national},{operation})\n"
commands += f'''
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
enemy = int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gEnemyParty+100*((unsigned short *)&gBattlerPartyIndexes)[1],11,0)"))
preferred = 3 if enemy == 130 else 1 if enemy == 297 else 2
species = int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,11,0)" % party))
if species == 400:
    preferred = 0 if enemy == 297 else 2 if enemy == 324 else 1
elif species == 283:
    preferred = 0
slots = [preferred] + [i for i in range(4) if i != preferred]
slot = next(i for i in slots if int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,%d,0)" % (party,17+i))) > 0)
gdb.execute("set ((unsigned char *)&gMoveSelectionCursor)[%d] = %d" % (active,slot))
gdb.execute("set gMain.newKeys = 1")
end
continue
end
break Task_HandleChooseMonInput
commands
silent
python
active = int(gdb.parse_and_eval("((unsigned short *)&gBattlerPartyIndexes)[0]"))
count = int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount"))
candidates = [i for i in range(count) if int(gdb.parse_and_eval("(unsigned char)GetPartyIdFromBattleSlot(%d)" % i)) != active and int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,57,0)" % i)) > 0]
slot = next((i for i in candidates if int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,11,0)" % i)) == 400), candidates[0])
gdb.execute("set *((signed char *)&gPartyMenu+9) = %d" % slot)
gdb.execute("set gMain.newKeys = 1")
end
continue
end
break CB2_EndTrainerBattle
commands
silent
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1
end
printf "CHAMPION VICTORY PASS\\n"
continue
end
break CB2_StartCreditsSequence
commands
silent
python
assert int(gdb.parse_and_eval("(int)FlagGet(0x864)")) == 1
end
printf "CAMPAIGN CREDITS ENTER PASS\\n"
disable 7
continue
end
break Task_CreditsTheEnd5
commands
silent
printf "CAMPAIGN THE END PASS\\n"
dump binary memory build/champion-campaign/end.raw &sPixels ((char *)&sPixels)+153600
disable 1
set $pc = (unsigned int)&Port_ExitCleanly
continue
end
call (void)SetWarpDestination({group},{index},-1,6,12)
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = 185000
return
continue
quit
'''
log = run(scratch, commands, ["CHAMPION VICTORY PASS", "CAMPAIGN CREDITS ENTER PASS",
                            "CAMPAIGN THE END PASS"], timeout=1200)
log.replace(scratch / "champion.log")
print("PASS same-campaign Wallace, natural Hall of Fame and The End")
