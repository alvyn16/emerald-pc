"""GDB helper: read live field state and drive keys; never write game progress."""
from collections import deque
from pathlib import Path
import json
import struct
import gdb

ROOT = Path.cwd()
SCRATCH = ROOT / "build/natural-campaign"
RUN_WILD = False  # Opt in after starter/rival; preserves HP during travel.
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
                locked=memory("sLockFieldControls",1)[0],
                callback=gdb.execute("info symbol %d" % callback,to_string=True).split(" in ")[0],
                party=memory("gPlayerPartyCount",1)[0])


def advance(buttons="NONE", frames=24, hold=None):
    assert gdb.newest_frame().name() == "Port_ExitCleanly", "Unexpected debugger stop; inspect backtrace"
    frame = value("sDiagnosticFrame")
    hold = frames-1 if hold is None else hold
    assert frames > 0 and 0 < hold < frames
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
        if field_ready(current):
            current = advance("NONE",24)
            if field_ready(current):
                return current
            continue
        if current["callback"] == "CB2_NamingScreen":
            advance("START",24,4)
            advance("A",24,4)
            continue
        button=battle_button() if current["callback"] == "BattleMainCB2" else "A"
        # One pulse avoids reopening NPC dialogue or accepting a move before
        # the next checkpoint can inspect the move-selection cursor.
        advance(button,96 if button == "A" else 24,1)
    raise RuntimeError("Dialog/battle needs a specific input: "+str(state()))


def field_ready(current):
    return (current["callback"] == "CB2_Overworld" and current["script"] == 2
            and not current["locked"])


def battle_button():
    """Choose a damaging move with PP using only the actual menu's keys."""
    controllers=struct.unpack("<4I",memory("gBattlerControllerFuncs",16))
    can_run=RUN_WILD and not value("*(unsigned int *)&gBattleTypeFlags") & (8|16|512)
    for battler in (0,2):
        function=gdb.execute("info symbol %d" % controllers[battler],to_string=True).split(" in ")[0]
        if function == "HandleInputChooseAction":
            target=3 if can_run else 0
            cursor=memory("gActionSelectionCursor",4)[battler]
            return cursor_button(cursor,target)
        if function != "HandleInputChooseMove":
            continue
        if can_run:
            return "B"
        choices=memory("gBattleBufferA",2048)[battler*512+4:battler*512+24]
        moves=struct.unpack_from("<4H",choices)
        types=choices[18:20]
        candidates=[]
        for index,move in enumerate(moves):
            if move and choices[8+index]:
                definition=bytes(gdb.selected_inferior().read_memory(value("(unsigned int)&gBattleMoves")+move*9,9))
                power=definition[1]
                score=power*(3 if definition[2] in types else 2)
                candidates.append((score,-index,index))
        if not candidates:
            return "A"  # Engine offers Struggle when all PP are exhausted.
        target=max(candidates)[2]
        cursor=memory("gMoveSelectionCursor",4)[battler]
        return cursor_button(cursor,target)
    return "A"


def cursor_button(cursor,target):
    if cursor&1 != target&1:
        return "RIGHT" if target&1 else "LEFT"
    if cursor&2 != target&2:
        return "DOWN" if target&2 else "UP"
    return "A"


def cross(button,destination,limit=4):
    """Face then cross a door/connection and check the resulting map."""
    for attempt in range(limit):
        advance(button,300,8)
        current=settle()
        if current["map"] == destination:
            return current
    raise RuntimeError("Expected transition to "+destination+": "+str(state()))


def talk(x,y,facing,limit=30000):
    origin=state()["map"]
    go(x,y)
    assert state()["map"] == origin and (state()["x"],state()["y"]) == (x,y)
    advance(facing,24,4)
    advance("A",24,4)
    return settle(limit)


def nurse():
    assert state()["map"].endswith("PokemonCenter_1F")
    talk(7,4,"UP")
    for index in range(state()["party"]):
        mon=f"(void *)((char *)&gPlayerParty+{index*100})"
        assert value(f"(int)GetMonData3({mon},57,0)") == value(f"(int)GetMonData3({mon},58,0)")
    return state()


def go(x,y,limit=50,dialogue_limit=30000):
    """Resume a path after dialogues/battles; never continue across a map warp."""
    origin=state()["map"]
    for attempt in range(limit):
        current=settle(dialogue_limit)
        if current["map"] != origin or (current["x"],current["y"]) == (x,y):
            return current
        walk(x,y)
    raise RuntimeError("Repeated movement interruptions: "+str(state()))


def save_checkpoint(name):
    """Use the actual Start/Save menu, then preserve a private save copy."""
    assert field_ready(state())
    previous=value("*(unsigned int *)&gSaveCounter")
    advance("START",120,4)
    actions=memory("sCurrentStartMenuActions",memory("sNumStartMenuActions",1)[0])
    target=actions.index(5)
    for step in range(9):
        cursor=memory("sStartMenuCursorPos",1)[0]
        if cursor == target:
            break
        advance("DOWN" if cursor < target else "UP",24,4)
    assert memory("sStartMenuCursorPos",1)[0] == target
    advance("A",24,4)
    settle()
    assert value("*(unsigned int *)&gSaveCounter") == previous+1
    assert memory("gSaveAttemptStatus",1)[0] == 1
    destination=SCRATCH/(name+".sav")
    destination.write_bytes((SCRATCH/"saves/emerald-pc-diagnostic.sav").read_bytes())
    facts=state()
    facts["team"]=[dict(species=value(f"(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),11,0)"),
                        level=value(f"(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),56,0)"))
                   for i in range(facts["party"])]
    facts["dex"]=value("(int)FlagGet(0x861)")
    facts["rival"]=value("(int)FlagGet(0x82)")
    facts["balls"]=value("(int)CountTotalItemQuantityInBag(4)")
    facts["badges"]=[value(f"(int)FlagGet({0x867+i})") for i in range(8)]
    facts["norman"]=value("(int)VarGet(0x4085)")
    facts["woods"]=value("(int)VarGet(0x4098)")
    (SCRATCH/(name+".json")).write_text(json.dumps(facts,indent=2),encoding="utf-8")
    gdb.execute(f"dump binary memory {SCRATCH.as_posix()}/{name}.raw &sPixels ((char *)&sPixels)+153600")
    print("NATURAL SAVE PASS",facts)
    return facts


def path_to(x,y):
    current = state(); start = (current["x"]+7,current["y"]+7); goal=(x+7,y+7)
    width,height,address = struct.unpack("<III",memory("gBackupMapLayout",12))
    cells = struct.unpack("<%dH" % (width*height),bytes(gdb.selected_inferior().read_memory(address,width*height*2)))
    read=gdb.selected_inferior().read_memory
    layout=struct.unpack("<I",memory("gMapHeader",4))[0]
    tilesets=struct.unpack("<2I",bytes(read(layout+16,8)))
    attributes=[]
    for tileset in tilesets:
        pointer=struct.unpack("<I",bytes(read(tileset+16,4)))[0]
        attributes.extend(struct.unpack("<512H",bytes(read(pointer,1024))))
    traits=memory("sTileBitAttributes",256)
    surfing=bool(memory("gPlayerAvatar",1)[0]&8)
    def passable(cell):
        tile=cell&0x3ff
        if cell&0xc00 or tile == 0x3ff:
            return False
        behavior=attributes[tile]&0xff
        return (surfing or not traits[behavior]&2) and not 0x30 <= behavior <= 0x37
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
            if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in previous and nxt not in blocked and passable(cells[nxt[1]*width+nxt[0]]):
                previous[nxt]=(node,button); queue.append(nxt)
    raise RuntimeError("No walkable path to "+str(goal)+" from "+str(current))


def walk(x,y,limit=200):
    origin=state()["map"]
    for step in range(limit):
        current=state()
        if current["map"] != origin or (current["x"],current["y"]) == (x,y):
            return current
        route=path_to(x,y)
        straight=1
        while straight < min(4,len(route)) and route[straight] == route[0]:
            straight += 1
        hold=16*(straight-1)+4
        advance(route[0],hold+20,hold)
        if state()["script"] != 2 or state()["callback"] != "CB2_Overworld":
            return state()
    raise RuntimeError("Movement deadline: "+str(state()))
