"""Controlled single Battle Tower battle with generated facility opponent."""
from game_fixture import prepare, run

inputs="".join(f"{n} {n+1} A\n" for n in range(31200,69500,40))
scratch,commands=prepare("frontier-segment",inputs)
commands+='''
call (void)CreateMon((void *)&gPlayerParty,285,50,32,0,0,0,0)
call (void)SetMonMoveSlot((void *)&gPlayerParty,57,0)
call (void)CreateMon((char *)&gPlayerParty+100,397,50,32,0,0,0,0)
call (void)CreateMon((char *)&gPlayerParty+200,400,50,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 3
call (unsigned char)VarSet(0x40CE,0)
call (unsigned char)VarSet(0x40CF,0)
set *(unsigned short *)&gTrainerBattleOpponent_A = 0
set *(unsigned short *)&gSpecialVar_0x8004 = 0
call (void)DoSpecialTrainerBattle()
break HandleSpecialTrainerBattleEnd
commands
silent
printf "TOWER END outcome=%u\\n", *(unsigned char *)&gBattleOutcome
set var sStopFrame = sDiagnosticFrame+1500
disable 3
continue
end
set var sStopFrame = 70000
return
continue
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,57,0)")) > 0
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "TOWER SEMANTIC PASS\\n"
continue
quit
'''
print("PASS Tower singles:",run(scratch,commands,["TOWER END outcome=1","TOWER SEMANTIC PASS"]))
