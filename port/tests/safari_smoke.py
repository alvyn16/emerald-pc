"""Isolated Safari encounter, escape, ball preservation and mode cleanup."""
from game_fixture import prepare, run

inputs="".join(f"{n} {n+1} A\n" for n in range(31200,36800,40))
scratch,commands=prepare("safari-segment",inputs)
commands+='''
call (void)EnterSafariMode()
call (void)CreateMon((void *)&gEnemyParty,43,22,32,0,0,0,0)
call (void)BattleSetup_StartWildBattle()
break CB2_EndSafariBattle
commands
silent
printf "SAFARI END outcome=%u\\n", *(unsigned char *)&gBattleOutcome
disable 3
continue
end
break HandleInputChooseAction
commands
silent
set ((unsigned char *)&gActionSelectionCursor)[*(unsigned char *)&gActiveBattler] = 3
set gMain.newKeys = 1
continue
end
set var sStopFrame = 37000
return
continue
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 4
assert int(gdb.parse_and_eval("*(unsigned char *)&gNumSafariBalls")) == 30
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 1
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
end
call (void)ExitSafariMode()
python
assert int(gdb.parse_and_eval("(unsigned int)GetSafariZoneFlag()")) == 0
assert int(gdb.parse_and_eval("*(unsigned char *)&gNumSafariBalls")) == 0
end
printf "SAFARI SEMANTIC PASS\\n"
continue
quit
'''
print("PASS Safari escape:",run(scratch,commands,["SAFARI END outcome=4","SAFARI SEMANTIC PASS"]))
