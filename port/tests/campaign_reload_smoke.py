"""Reopen the isolated campaign save in a fresh process, without rewriting it."""
import argparse
from game_fixture import PROJECT, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--badges", type=int, choices=range(1, 9), required=True)
parser.add_argument("--progress", type=int, choices=range(2, 9), required=True)
args = parser.parse_args()
scratch = PROJECT / "build/campaign-script-chain"
save = scratch / "saves/emerald-pc-diagnostic.sav"
before = save.read_bytes()
commands = """set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
unset environment EMERALD_PC_INPUT_SCRIPT
unset environment EMERALD_PC_STOP_FRAME
break LoadGameSave
run
finish
python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)")) == 285
"""
commands += f'assert int(gdb.parse_and_eval("(unsigned int)VarGet(0x4085)")) == {args.progress}\n'
for badge in range(8):
    commands += f'assert int(gdb.parse_and_eval("(int)FlagGet({0x867+badge})")) == {int(badge < args.badges)}\n'
commands += '''end
printf "CAMPAIGN RELOAD PASS\\n"
set $pc = (unsigned int)&Port_ExitCleanly
continue
quit
'''
log = run(scratch, commands, ["CAMPAIGN RELOAD PASS"])
log.replace(scratch / "reload.log")
assert save.read_bytes() == before, "Read-only reload must preserve the save"
print(f"PASS fresh-process reload: {args.badges} badges, progress {args.progress}, save unchanged")
