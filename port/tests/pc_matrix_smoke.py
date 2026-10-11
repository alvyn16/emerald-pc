"""Real storage/PC UI operations with semantic checks and save roundtrip."""
import argparse
from game_fixture import prepare, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("operation", choices=("deposit", "withdraw", "box", "items"))
operation = parser.parse_args().operation
events = [(31700,"A"),(31750,"A"),(31800,"A"),(31850,"A")]
if operation == "box": events = [(31700,"A"),(31750,"A"),(31900,"START"),(31950,"RIGHT"),(32100,"DOWN"),(32200,"A"),(32250,"A")]
if operation == "items":
    events = [(31500,"A"),(31560,"DOWN"),(31620,"A"),(32000,"A"),(32060,"A"),
              (32120,"A"),(32200,"B"),(32400,"UP"),(32460,"A"),(32520,"A"),
              (32580,"A"),(32640,"A"),(32700,"B"),(32760,"B"),(32820,"B")]
else:
    events += [(32700,"B"),(32750,"B"),(32900,"B"),(32950,"B")]
scratch, commands = prepare(f"pc-matrix-{operation}", "".join(f"{n} {n+1} {key}\n" for n,key in events))
setup = ""
if operation == "deposit":
    setup = "call (void)CreateMon((char *)&gPlayerParty+100,392,8,32,0,0,0,0)\nset *(unsigned char *)&gPlayerPartyCount = 2\n"
if operation == "withdraw": setup = "call (void)CreateBoxMonAt(0,0,280,5,32,0,0,0,0)\n"
if operation == "box": setup = "call (void)CreateBoxMonAt(0,0,392,8,32,0,0,0,0)\n"
if operation == "items": setup = "call (int)AddBagItem(13,2)\n"
mode = {"deposit":1,"withdraw":0,"box":2}.get(operation)
entry = "call (void)PlayerPC()" if operation == "items" else f"call (void)EnterPokeStorage({mode})"
commands += setup + f"""
{entry}
set var sStopFrame = 31600
return
continue
dump binary memory build/pc-matrix-{operation}/open.raw &sPixels ((char *)&sPixels)+153600
set var sStopFrame = {32500 if operation == "box" else 32200}
return
continue
"""
checks = {
    "deposit": 'assert int(gdb.parse_and_eval("(unsigned int)GetBoxMonDataAt(0,0,11)")) == 283\nassert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)")) == 392\n',
    "withdraw": 'assert int(gdb.parse_and_eval("(unsigned int)GetBoxMonDataAt(0,0,11)")) == 0\nassert int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gPlayerParty+100,11,0)")) == 280\n',
    "box": 'assert int(gdb.parse_and_eval("(unsigned int)GetBoxMonDataAt(0,0,11)")) == 0\nassert int(gdb.parse_and_eval("(unsigned int)GetBoxMonDataAt(1,2,11)")) == 392\n',
    "items": 'assert int(gdb.parse_and_eval("(int)CheckBagHasItem(13,2)")) == 0\nassert int(gdb.parse_and_eval("(int)CheckPCHasItem(13,2)")) == 1\n',
}[operation]
commands += "python\n" + checks + f"end\nprintf \"PC {operation} MUTATION PASS\\n\"\n"
commands += "set var sStopFrame = 33500\nreturn\ncontinue\n"
commands += "python\n"
commands += 'assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))\n'
if operation == "items":
    commands += 'assert int(gdb.parse_and_eval("(int)CheckBagHasItem(13,2)")) == 1\nassert int(gdb.parse_and_eval("(int)CheckPCHasItem(13,2)")) == 0\n'
else: commands += checks
commands += 'assert int(gdb.parse_and_eval("(int)TrySavingData(0)")) == 1\nend\n'
commands += f'printf "PC {operation} SAVED PASS\\n"\ncontinue\nquit\n'
print("Saved:", run(scratch, commands, [f"PC {operation} MUTATION PASS", f"PC {operation} SAVED PASS"]))
saved = (scratch / "saves/emerald-pc-diagnostic.sav").read_bytes()
reload_checks = checks if operation != "items" else 'assert int(gdb.parse_and_eval("(int)CheckBagHasItem(13,2)")) == 1\nassert int(gdb.parse_and_eval("(int)CheckPCHasItem(13,2)")) == 0\n'
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
python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == 1
''' + reload_checks + '''end
printf "PC RELOAD PASS\\n"
set $pc = (unsigned int)&Port_ExitCleanly
continue
quit
'''
print(f"PASS PC {operation}: restart/reload;", run(scratch, commands, ["PC RELOAD PASS"]))
assert (scratch / "saves/emerald-pc-diagnostic.sav").read_bytes() == saved

