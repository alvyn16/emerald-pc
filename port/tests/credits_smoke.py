"""Isolated Hall of Fame save and credits segment, not story progression."""
from game_fixture import prepare, run

inputs = "".join(f"{n} {n+1} A\n" for n in range(31400, 61000, 40))
scratch, commands = prepare("credits-segment", inputs)
commands += '''
call (unsigned char)GetSetPokedexFlag(258,2)
call (unsigned char)GetSetPokedexFlag(258,3)
set var sStopFrame = 70000
break CB2_StartCreditsSequence
commands
silent
printf "CREDITS ENTER PASS\\n"
disable 3
continue
end
break Task_CreditsTheEnd5
commands
silent
printf "CREDITS END PASS\\n"
dump binary memory build/credits-segment/end.raw &sPixels ((char *)&sPixels)+153600
disable 1
set $pc = (unsigned int)&Port_ExitCleanly
continue
end
call (void)SetMainCallback2((void *)CB2_DoHallOfFameScreen)
return
continue
quit
'''
print("PASS Hall of Fame/credits:", run(scratch, commands, ["CREDITS ENTER PASS", "CREDITS END PASS"]))
assert (scratch / "saves/emerald-pc-diagnostic.sav").read_bytes() != b"\xff" * 131072
