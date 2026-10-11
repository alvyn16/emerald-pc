"""Controlled breeding and contest segments; no claim of story completion."""
import argparse
from game_fixture import prepare, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("segment", choices=("breeding", "contest"))
segment = parser.parse_args().segment
inputs = "".join(f"{n} {n+1} A\n" for n in range(31300, 69500, 40))
scratch, commands = prepare(f"content-{segment}", inputs)
if segment == "breeding":
    # SaveBlock1 daycare is 0x3030 in the pinned GBA layout; leave a third mon.
    commands += '''
call (void)CreateMon((char *)&gPlayerParty+100,132,8,32,0,0,0,0)
call (void)CreateMon((char *)&gPlayerParty+200,280,8,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 3
set *((signed char *)&gPartyMenu+9) = 0
call (void)StoreSelectedPokemonInDaycare()
call (void)StoreSelectedPokemonInDaycare()
python
assert int(gdb.parse_and_eval("(unsigned char)GetDaycareState()")) == 3
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 1
end
call (void)TriggerPendingDaycareEgg()
call (void)GiveEggFromDaycare()
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 2
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100,11,0)")) == 283
assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1
end
printf "BREEDING EGG PASS\\n"
continue
quit
'''
    markers = ["BREEDING EGG PASS"]
else:
    commands += '''
set *(unsigned char *)&gLinkContestFlags = 0
set *(unsigned char *)&gContestMonPartyIndex = 0
set *(unsigned short *)&gSpecialVar_ContestCategory = 0
set *(unsigned short *)&gSpecialVar_ContestRank = 0
call (void)SetContestants(0,0)
call (void)CalculateRound1Points(0)
set var sStopFrame = 70000
break Task_EndAppeals
commands
silent
printf "CONTEST FIVE APPEALS PASS\\n"
disable $bpnum
continue
end
call (void)SetMainCallback2((void *)CB2_StartContest)
return
continue
python
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
end
printf "CONTEST FIELD PASS\\n"
continue
quit
'''
    markers = ["CONTEST FIVE APPEALS PASS", "CONTEST FIELD PASS"]
print(f"PASS {segment}:", run(scratch, commands, markers))
