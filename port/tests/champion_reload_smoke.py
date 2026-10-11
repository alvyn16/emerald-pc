"""Read the campaign's post-credits save and real Hall of Fame in a new process."""
from game_fixture import PROJECT, run

scratch = PROJECT / "build/champion-campaign"
save = scratch / "saves/emerald-pc-diagnostic.sav"
before = save.read_bytes()
commands = '''set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
unset environment EMERALD_PC_INPUT_SCRIPT
unset environment EMERALD_PC_STOP_FRAME
break LoadGameSave
run
finish
disable 1
python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1
assert int(gdb.parse_and_eval("(int)FlagGet(0x864)")) == 1
for badge in range(8):
    assert int(gdb.parse_and_eval("(int)FlagGet(%d)" % (0x867+badge))) == 1
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 3
for slot,species in enumerate((285,283,400)):
    assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100*%d,11,0)" % slot)) == species
assert int(gdb.parse_and_eval("(unsigned char)LoadGameSave(3)")) == 1
# Real saved HallofFameMon: tid/personality, packed species/level, nickname.
buffer = int(gdb.parse_and_eval("(unsigned int)&gDecompressionBuffer"))
data = bytes(gdb.selected_inferior().read_memory(buffer,120))
for slot,species in enumerate((285,283,400)):
    packed = int.from_bytes(data[slot*20+8:slot*20+10], "little")
    assert packed & 0x1FF == species
    assert packed >> 9 >= 80
end
printf "CAMPAIGN CHAMPION SAVE AND HOF RELOAD PASS\\n"
set $pc = (unsigned int)&Port_ExitCleanly
continue
quit
'''
log = run(scratch, commands, ["CAMPAIGN CHAMPION SAVE AND HOF RELOAD PASS"])
log.replace(scratch / "reload.log")
assert save.read_bytes() == before
print("PASS post-credits game-clear, eight badges, party, Hall of Fame; save unchanged")
