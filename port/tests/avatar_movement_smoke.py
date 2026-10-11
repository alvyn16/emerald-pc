"""Controlled walking, bike and surf movement segments on real map tiles."""
import argparse
import json
from game_fixture import PROJECT, prepare, run

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode",choices=("walk","bike","surf"))
mode=parser.parse_args().mode
inputs="31500 31540 RIGHT\n"
scratch,commands=prepare(f"avatar-{mode}",inputs)
maps=json.loads((PROJECT/"pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
group=maps[maps["group_order"][0]]
target="Route124" if mode=="surf" else "Route101"
index=group.index(target)
x,y=(15,15) if mode=="surf" else (10,10)
flag={"walk":1,"bike":2,"surf":8}[mode]
commands+=f'''
call (void)SetWarpDestination(0,{index},-1,{x},{y})
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = 31400
return
continue
call (void)ScriptContext_Init()
call (void)UnlockPlayerFieldControls()
call (void)SetPlayerAvatarTransitionFlags({flag})
set $coords = (short *)Alloc(4)
call (void)PlayerGetDestCoords($coords,$coords+1)
set $start_x = *$coords
set $start_y = *($coords+1)
set var sStopFrame = 31700
return
continue
call (void)PlayerGetDestCoords($coords,$coords+1)
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerAvatar")) & {flag}
assert (int(gdb.parse_and_eval("*$coords")),int(gdb.parse_and_eval("*($coords+1)"))) != (int(gdb.parse_and_eval("$start_x")),int(gdb.parse_and_eval("$start_y"))), "No movement"
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
end
printf "AVATAR {mode} PASS\\n"
dump binary memory build/avatar-{mode}/frame.raw &sPixels ((char *)&sPixels)+153600
call (void)Free($coords)
continue
quit
'''
print(f"PASS {mode}:",run(scratch,commands,[f"AVATAR {mode} PASS"]))
