"""Controlled Roxanne loss: final fade must retire shadows after data teardown."""
from game_fixture import prepare, run


def main():
    inputs="".join(f"{frame} {frame+1} A\n" for frame in range(31001,45000,24))
    scratch,commands=prepare("battle-shadow-teardown",inputs)
    # A weak party deliberately loses to Roxanne's floating Geodude. This is
    # a separate regression fixture, never the keyboard-created campaign save.
    commands=commands.replace("gPlayerParty,283,8,32","gPlayerParty,129,2,32")
    commands+='''
set *(unsigned short *)&gTrainerBattleOpponent_A = 265
call (void)BattleSetup_StartTrainerBattle()
set var sStopFrame = 45000
return
break SpriteCB_EnemyShadow if *(unsigned int *)&gBattleSpritesDataPtr == 0
commands
silent
printf "SHADOW AFTER TEARDOWN frame=%u\\n", sDiagnosticFrame
continue
end
break CB2_EndTrainerBattle
commands
silent
printf "TRAINER LOSS END outcome=%u\\n", *(unsigned char *)&gBattleOutcome
continue
end
continue
python
assert int(gdb.parse_and_eval('*(unsigned char *)&gBattleOutcome')) == 2
assert int(gdb.parse_and_eval('(int)GetMonData3((void *)&gPlayerParty,57,0)')) > 0
assert int(gdb.parse_and_eval('(int)GetMonData3((void *)&gPlayerParty,57,0)')) == int(gdb.parse_and_eval('(int)GetMonData3((void *)&gPlayerParty,58,0)'))
assert int(gdb.parse_and_eval('(unsigned int)gMain.callback2')) == int(gdb.parse_and_eval('(unsigned int)&CB2_Overworld'))
assert int(gdb.parse_and_eval('*(unsigned int *)&gBattleSpritesDataPtr')) == 0
end
printf "SHADOW LOSS BLACKOUT RETURN PASS\\n"
continue
quit
'''
    log=run(scratch,commands,["SHADOW AFTER TEARDOWN","TRAINER LOSS END outcome=2","SHADOW LOSS BLACKOUT RETURN PASS"])
    print(f"PASS shadow teardown: actual trainer loss, fade, blackout and healed field return; {log}")


if __name__ == "__main__":
    main()
