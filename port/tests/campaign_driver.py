"""GDB helper: read live field state and drive keys; never write game progress."""
from collections import deque
from pathlib import Path
import json
import struct
import gdb

ROOT = Path.cwd()
SCRATCH = ROOT / "build/natural-campaign"
GROUPS = json.loads((ROOT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
MAPS = {(group,index): name for group,key in enumerate(GROUPS["group_order"])
        for index,name in enumerate(GROUPS[key])}


def value(expression):
    return int(gdb.parse_and_eval(expression))


def memory(symbol, count):
    return bytes(gdb.selected_inferior().read_memory(value("(unsigned int)&"+symbol), count))


def state():
    save = value("*(unsigned int *)&gSaveBlock1Ptr")
    location = bytes(gdb.selected_inferior().read_memory(save+4,2))
    objects = memory("gObjectEvents", 16*36)
    player = memory("gPlayerAvatar", 6)[5]
    x,y = struct.unpack_from("<hh", objects, player*36+16)
    callback = value("(unsigned int)gMain.callback2")
    return dict(frame=value("sDiagnosticFrame"), map=MAPS[tuple(location)], x=x-7,y=y-7,
                script=memory("sGlobalScriptContextStatus",1)[0],
                callback=gdb.execute("info symbol %d" % callback,to_string=True).split(" in ")[0],
                party=memory("gPlayerPartyCount",1)[0])


def advance(buttons="NONE", frames=24, hold=None):
    assert gdb.newest_frame().name() == "Port_ExitCleanly", "Unexpected debugger stop; inspect backtrace"
    frame = value("sDiagnosticFrame")
    hold = frames-1 if hold is None else hold
    (SCRATCH / "input.txt").write_text(f"{frame+1} {frame+hold} {buttons}\n",encoding="ascii")
    gdb.execute("call (int)PortInputScript_Init()",to_string=True)
    gdb.execute("set var sStopFrame = %d" % (frame+frames))
    gdb.execute("return",to_string=True)
    gdb.execute("continue",to_string=True)
    if gdb.newest_frame().name() != "Port_ExitCleanly":
        gdb.execute("bt")
        raise RuntimeError("Game stopped outside the frame checkpoint")
    result = state()
    assert result["frame"] == frame+frames, "Window close or unexpected frame checkpoint"
    result["input"] = dict(buttons=buttons, hold=hold, frames=frames)
    with (SCRATCH / "route.jsonl").open("a",encoding="utf-8") as trace:
        trace.write(json.dumps(result)+"\n")
    return result


def settle(limit=10000):
    start = value("sDiagnosticFrame")
    while value("sDiagnosticFrame")-start < limit:
        current = state()
        if current["callback"] == "CB2_Overworld" and current["script"] == 2:
            return current
        advance("A",24,1)
    raise RuntimeError("Dialog/battle needs a specific input: "+str(state()))


def path_to(x,y):
    current = state(); start = (current["x"]+7,current["y"]+7); goal=(x+7,y+7)
    width,height,address = struct.unpack("<III",memory("gBackupMapLayout",12))
    cells = struct.unpack("<%dH" % (width*height),bytes(gdb.selected_inferior().read_memory(address,width*height*2)))
    objects = memory("gObjectEvents",16*36); player=memory("gPlayerAvatar",6)[5]
    blocked = {struct.unpack_from("<hh",objects,i*36+16) for i in range(16)
               if i != player and objects[i*36]&1}
    queue=deque([start]); previous={start:None}
    while queue:
        node=queue.popleft()
        if node == goal:
            route=[]
            while previous[node] is not None:
                node,button = previous[node]; route.append(button)
            return route[::-1]
        for dx,dy,button in ((1,0,"RIGHT"),(-1,0,"LEFT"),(0,1,"DOWN"),(0,-1,"UP")):
            nxt=(node[0]+dx,node[1]+dy)
            if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in previous and nxt not in blocked and cells[nxt[1]*width+nxt[0]] & 0xC00 == 0:
                previous[nxt]=(node,button); queue.append(nxt)
    raise RuntimeError("No walkable path to "+str(goal)+" from "+str(current))


def walk(x,y,limit=200):
    origin=state()["map"]
    for step in range(limit):
        current=state()
        if current["map"] != origin or (current["x"],current["y"]) == (x,y):
            return current
        route=path_to(x,y)
        advance(route[0],24,4)
        if state()["script"] != 2 or state()["callback"] != "CB2_Overworld":
            return state()
    raise RuntimeError("Movement deadline: "+str(state()))
