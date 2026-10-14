"""GDB helper: read live field state and drive keys; never write game progress."""
from collections import deque
from pathlib import Path
import json
import struct
import gdb

ROOT = Path.cwd()
SCRATCH = ROOT / "build/natural-campaign"
RUN_WILD = False  # Opt in after starter/rival; preserves HP during travel.
CATCH_SPECIES = set()  # Optional natural catches; never constructs a Pokemon.
RUN_FROM_TYPES = set()  # Training may avoid unfavorable wild matchups.
SWITCH_FROM_TYPES = set()  # Lead training can share XP with a healthy partner.
TARGET_CHOICES = {}  # Planned targets, applied exclusively through menu keys.
HEAL_ITEMS = ()  # Optional campaign consumables, never granted by the driver.
HEAL_PLAN = {}
EVENT_FLAGS = {"flash":0x6d,"cut":0x89,"recovered_goods":0x8f,"returned_goods":0x90,
               "match_call":0x12f,"pokenav":0x862,"letter":0xbd,"delivered_goods":0x95,
               "wally_mauville":0xbe,"rock_smash":0x6b}
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
            HEAL_PLAN.clear()
            current = advance("NONE",24)
            if field_ready(current):
                return current
            continue
        if current["callback"] == "CB2_NamingScreen":
            advance("START",24,4)
            advance("A",24,4)
            continue
        if value('(int)FuncIsActiveTask((void *)Task_HandleReplaceMoveInput)'):
            pointer=value('*(unsigned int *)&sMonSummaryScreen')
            if pointer:
                selected=bytes(gdb.selected_inferior().read_memory(pointer+0x40c4,4))
                if struct.unpack_from('<H',selected)[0]:
                    advance(learn_move_button(pointer,selected[2]),24,1)
                    continue
        if current['callback'] == 'CB2_BagMenuRun' and (CATCH_SPECIES or HEAL_PLAN):
            advance(item_bag_button(HEAL_PLAN.get('item')),24,1)
            continue
        if current['callback'] == 'CB2_UpdatePartyMenu' and memory('gPartyMenu',9)[8]&15 == 1:
            if HEAL_PLAN and memory('gPartyMenu',12)[11] == 3:
                advance(heal_party_button(),24,1)
            else:
                advance(battle_party_button(),24,1)
            continue
        if (current["map"] == "RustboroCity" and current["callback"] == "CB2_Overworld"
                and value("(int)VarGet(0x405a)") == 6
                and value("(int)FuncIsActiveTask((void *)Task_HandleMultichoiceInput)")):
            cursor=value("(int)Menu_GetCursorPos()")
            advance("DOWN" if cursor < 3 else "UP" if cursor > 3 else "A",24,1)
            continue
        if current["callback"] == "CB2_Pokenav":
            mode=value("(int)GetPokenavMode()")
            if mode == 2:
                advance("B",96,1)
                continue
            pointer=value("(unsigned int)GetSubstructPtr(1)")
            if mode == 1 and pointer:
                menu=bytes(gdb.selected_inferior().read_memory(pointer,16))
                callback=struct.unpack_from("<I",menu,12)[0]
                name=gdb.execute("info symbol %d" % callback,to_string=True).split(" in ")[0]
                if name == "HandleMainMenuInputTutorial":
                    cursor=struct.unpack_from("<h",menu,2)[0]
                    advance("DOWN" if cursor < 2 else "UP" if cursor > 2 else "A",24,1)
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
    instruction=value('(unsigned int)gBattlescriptCurrInstr')
    opcode=bytes(gdb.selected_inferior().read_memory(instruction,1))[0] if instruction else None
    if opcode == 0x67 and value('*(unsigned int *)&gBattleTypeFlags')&8:
        return 'B'  # Script-level optional switch after an opposing trainer mon.
    if opcode == 0x5a:
        move=value('*(unsigned short *)&gMoveToLearn')
        definition=bytes(gdb.selected_inferior().read_memory(value('(unsigned int)&gBattleMoves')+move*9,9))
        if definition[1] == 0:
            return 'B'  # Decline status moves instead of replacing an attack.
    controllers=struct.unpack("<4I",memory("gBattlerControllerFuncs",16))
    if HEAL_PLAN and value(f"(int)CountTotalItemQuantityInBag({HEAL_PLAN['item']})") < HEAL_PLAN['quantity']:
        HEAL_PLAN.clear()
    wild=not value("*(unsigned int *)&gBattleTypeFlags") & (8|16|512)
    battle_mons=memory('gBattleMons',352)
    catching=wild and struct.unpack_from('<H',battle_mons,88)[0] in CATCH_SPECIES
    avoid=bool(set(battle_mons[88+33:88+35]) & RUN_FROM_TYPES)
    can_run=(RUN_WILD or avoid) and wild and not catching
    share=wild and bool(set(battle_mons[88+33:88+35]) & SWITCH_FROM_TYPES)
    share=share and struct.unpack_from('<H',memory('gBattlerPartyIndexes',8))[0] == 0
    for battler in (0,2):
        function=gdb.execute("info symbol %d" % controllers[battler],to_string=True).split(" in ")[0]
        if function == 'PlayerHandleYesNoInput':
            return 'B'  # Keep current mon for optional between-opponent swaps.
        if function == "HandleInputChooseAction":
            hp,max_hp=struct.unpack_from('<H',battle_mons,battler*88+40)[0],struct.unpack_from('<H',battle_mons,battler*88+44)[0]
            if HEAL_ITEMS and not catching and hp and hp*2 <= max_hp:
                for item in HEAL_ITEMS:
                    quantity=value(f'(int)CountTotalItemQuantityInBag({item})')
                    if quantity:
                        HEAL_PLAN.update(item=item,quantity=quantity,
                                         field_slot=struct.unpack_from('<H',memory('gBattlerPartyIndexes',8),battler*2)[0])
                        break
            if HEAL_PLAN:
                return cursor_button(memory('gActionSelectionCursor',4)[battler],1)
            target=1 if catching else 3 if can_run else 2 if share else 0
            cursor=memory("gActionSelectionCursor",4)[battler]
            return cursor_button(cursor,target)
        if function == 'HandleInputChooseTarget':
            desired=TARGET_CHOICES.get(battler,1)
            cursor=memory('gMultiUsePlayerCursor',1)[0]
            if cursor == desired:
                log_battle_choice('target',battler,target=cursor)
            return 'A' if cursor == desired else 'RIGHT'
        if function != "HandleInputChooseMove":
            continue
        if can_run or catching:
            return "B"
        choices=memory("gBattleBufferA",2048)[battler*512+4:battler*512+24]
        moves=struct.unpack_from("<4H",choices)
        types=choices[18:20]
        battle=memory("gBattleMons",4*88)
        absent=memory('gAbsentBattlerFlags',1)[0]
        opponents=[opponent for opponent in (1,3)
                   if opponent < memory('gBattlersCount',1)[0] and
                   not absent&(1<<opponent) and struct.unpack_from('<H',battle,opponent*88+40)[0]]
        chart=memory("gTypeEffectiveness",336)
        candidates=[]
        for index,move in enumerate(moves):
            if move and choices[8+index]:
                definition=bytes(gdb.selected_inferior().read_memory(value("(unsigned int)&gBattleMoves")+move*9,9))
                physical=definition[2] < 10  # Gen III categories are by type.
                attack_offset,defense_offset=(2,4) if physical else (8,10)
                attack_stage,defense_stage=(1,2) if physical else (4,5)
                attack=struct.unpack_from("<H",battle,battler*88+attack_offset)[0]
                attack *= stat_stage_factor(battle[battler*88+24+attack_stage])
                for opponent in opponents:
                    score=definition[1]*(3 if definition[2] in types else 2)
                    defense=struct.unpack_from('<H',battle,opponent*88+defense_offset)[0]
                    defense *= stat_stage_factor(battle[opponent*88+24+defense_stage])
                    score *= attack/max(1,defense)
                    for enemy_type in set(battle[opponent*88+33:opponent*88+35]):
                        multiplier=10
                        for move_type,defender_type,factor in struct.iter_unpack('BBB',chart):
                            if move_type == definition[2] and defender_type == enemy_type:
                                multiplier=factor; break
                        score *= multiplier
                    immunity={4:26,10:18,11:11,13:10}.get(definition[2])
                    if immunity and battle[opponent*88+32] == immunity:
                        score=0
                    candidates.append((score,-index,-opponent,index,opponent))
        if not candidates:
            return "A"  # Engine offers Struggle when all PP are exhausted.
        best=max(candidates); target=best[3]; TARGET_CHOICES[battler]=best[4]
        cursor=memory("gMoveSelectionCursor",4)[battler]
        button=cursor_button(cursor,target)
        if button == 'A':
            log_battle_choice('move',battler,move=moves[target],target=best[4])
        return button
    return "A"


def log_battle_choice(kind,battler,**fields):
    if memory('gBattlersCount',1)[0] != 4:
        return
    entry=dict(frame=value('sDiagnosticFrame'),kind=kind,battler=battler,**fields)
    with (SCRATCH/'battle-choices.jsonl').open('a',encoding='utf-8') as output:
        output.write(json.dumps(entry)+'\n')


def item_bag_button(item=None):
    if not value('(int)FuncIsActiveTask((void *)Task_BagMenu_HandleInput)'):
        return 'A'  # Context menu's default is Use.
    position=memory('gBagPosition',28)
    pocket=position[5]
    desired_pocket=0 if item else 1  # Items or Poke Balls.
    if pocket != desired_pocket:
        return 'RIGHT' if pocket < desired_pocket else 'LEFT'
    cursor=struct.unpack_from('<H',position,8+pocket*2)[0]
    scroll=struct.unpack_from('<H',position,18+pocket*2)[0]
    if item:
        entries=[value(f'(int)BagGetItemIdByPocketPosition(1,{i})') for i in range(30)]
        target=entries.index(item)
        current=cursor+scroll
        return 'A' if current == target else 'DOWN' if current < target else 'UP'
    # Prefer the first ball stack. Assert it really contains a Poke Ball type.
    item=value('(int)BagGetItemIdByPocketPosition(2,0)')
    assert 1 <= item <= 12, 'No available ball stack for natural capture'
    return 'UP' if cursor+scroll else 'A'


def heal_party_button():
    if not value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
        return 'A'
    order=memory('gBattlePartyCurrentOrder',3)
    fields=[order[i//2] >> 4 if i%2 == 0 else order[i//2]&15 for i in range(6)]
    target=fields.index(HEAL_PLAN['field_slot']); cursor=memory('gPartyMenu',10)[9]
    if cursor == target:
        return 'A'
    return 'RIGHT' if cursor == 0 else 'LEFT' if target == 0 else 'DOWN' if cursor < target else 'UP'


def battle_party_button():
    if not value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
        return 'A'  # Send Out is the first battle context-menu action.
    count=memory('gPlayerPartyCount',1)[0]
    slots=struct.unpack('<4H',memory('gBattlerPartyIndexes',8))
    active={slots[0]}
    if value('*(unsigned int *)&gBattleTypeFlags')&1:
        active.add(slots[2])
    order=memory('gBattlePartyCurrentOrder',3)
    field_slots=[order[i//2] >> 4 if i%2 == 0 else order[i//2]&15 for i in range(count)]
    # Opening the battle party menu reorders gPlayerParty to display order;
    # battler indexes still refer to its saved field order.
    candidates=[i for i in range(count) if field_slots[i] not in active and
                value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),57,0)')>0]
    assert candidates, 'No legal healthy replacement in battle party menu'
    target=candidates[0]; cursor=memory('gPartyMenu',10)[9]
    if cursor == target:
        return 'A'
    if cursor == 0:
        return 'RIGHT'
    if target == 0:
        return 'LEFT'
    return 'DOWN' if cursor < target else 'UP'


def learn_move_button(pointer,cursor):
    """Replace the weakest non-HM slot using the summary-screen cursor."""
    assert 0 <= cursor <= 4
    moves=struct.unpack('<4H',bytes(gdb.selected_inferior().read_memory(pointer+0x84,8)))
    candidates=[]
    for index,move in enumerate(moves):
        if not value(f'(int)IsHMMove2({move})'):
            power=bytes(gdb.selected_inferior().read_memory(value('(unsigned int)&gBattleMoves')+move*9+1,1))[0]
            candidates.append((power,index))
    target=min(candidates)[1] if candidates else 4  # Cancel if all are HMs.
    return 'A' if cursor == target else 'DOWN' if cursor < target else 'UP'


def stat_stage_factor(stage):
    assert 0 <= stage <= 12
    return (2+max(stage-6,0))/(2+max(6-stage,0))


def cursor_button(cursor,target):
    if cursor&1 != target&1:
        return "RIGHT" if target&1 else "LEFT"
    if cursor&2 != target&2:
        return "DOWN" if target&2 else "UP"
    return "A"


def cross(button,destination,limit=4):
    """Face then cross a door/connection and check the resulting map."""
    if state()["map"] == destination:
        return settle()
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


def choose_dialogue(x,y,facing,choice,limit=10000):
    """Read a vertical script-menu cursor and select with real keys."""
    go(x,y)
    assert (state()['x'],state()['y']) == (x,y)
    advance(facing,24,4); advance('A',24,4)
    start=value('sDiagnosticFrame')
    while not value('(int)FuncIsActiveTask((void *)Task_HandleMultichoiceInput)'):
        assert value('sDiagnosticFrame')-start < limit, 'Expected script choice menu'
        advance('A',96,1)
    for step in range(16):
        cursor=value('(int)Menu_GetCursorPos()')
        if cursor == choice:
            advance('A',24,1)
            return settle(30000)
        advance('DOWN' if cursor < choice else 'UP',24,1)
    raise RuntimeError('Script menu did not reach requested choice')


def nurse():
    assert state()["map"].endswith("PokemonCenter_1F")
    talk(7,4,"UP")
    for index in range(state()["party"]):
        mon=f"(void *)((char *)&gPlayerParty+{index*100})"
        assert value(f"(int)GetMonData3({mon},57,0)") == value(f"(int)GetMonData3({mon},58,0)")
    return state()


def open_start_action(action):
    assert field_ready(state())
    advance('START',120,4)
    actions=memory('sCurrentStartMenuActions',memory('sNumStartMenuActions',1)[0])
    target=actions.index(action)
    for step in range(10):
        cursor=memory('sStartMenuCursorPos',1)[0]
        if cursor == target:
            advance('A',300,1)
            return state()
        advance('DOWN' if cursor < target else 'UP',24,1)
    raise RuntimeError('Start menu did not reach requested action')


def select_party_slot(target,switching=False):
    assert 0 <= target < memory('gPlayerPartyCount',1)[0]
    for step in range(12):
        cursor=memory('gPartyMenu',11)[10 if switching else 9]
        if cursor == target:
            return
        button=('RIGHT' if cursor == 0 else 'LEFT' if target == 0 else
                'DOWN' if cursor < target else 'UP')
        advance(button,24,1)
    raise RuntimeError('Party cursor did not reach requested slot')


def set_lead(slot):
    """Swap a party slot to first place through the field Pokemon menu."""
    if slot == 0:
        return state()
    species=value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{slot*100}),11,0)')
    open_start_action(1)
    assert state()['callback'] == 'CB2_UpdatePartyMenu'
    select_party_slot(slot); advance('A',48,1)
    internal=value('*(unsigned int *)&sPartyMenuInternal')
    context=bytes(gdb.selected_inferior().read_memory(internal+15,9))
    target=context[:context[8]].index(1)  # MENU_SWITCH; field moves may precede it.
    for step in range(10):
        cursor=value('(int)Menu_GetCursorPos()')
        if cursor == target:
            break
        advance('DOWN' if cursor < target else 'UP',24,1)
    else:
        raise RuntimeError('Expected field party Switch option')
    advance('A',48,1)
    assert memory('gPartyMenu',12)[11] == 8  # PARTY_ACTION_SWITCH.
    select_party_slot(0,True); advance('A',180,1)
    advance('B',180,1); advance('B',48,1)
    assert field_ready(state())
    assert value('(int)GetMonData3((void *)&gPlayerParty,11,0)') == species
    return state()


def teach_tm(item,slot):
    """Use an owned TM/HM via bag, party and move-summary menus."""
    assert field_ready(state())
    assert value(f'(int)CountTotalItemQuantityInBag({item})') > 0
    move=value(f'(int)ItemIdToBattleMoveId({item})')
    mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
    assert value(f'(unsigned int)CanMonLearnTMHM({mon},{item-289})'), 'Incompatible TM/HM'
    open_start_action(2)
    for step in range(160):
        if value('(int)FuncIsActiveTask((void *)Task_BagMenu_HandleInput)'):
            position=memory('gBagPosition',28); pocket=position[5]
            if pocket != 2:
                advance('RIGHT' if pocket < 2 else 'LEFT',24,1)
                continue
            entries=[value(f'(int)BagGetItemIdByPocketPosition(3,{i})') for i in range(64)]
            target=entries.index(item)
            current=struct.unpack_from('<H',position,12)[0]+struct.unpack_from('<H',position,22)[0]
            if current == target:
                advance('A',24,1)
                break
            advance('DOWN' if current < target else 'UP',24,1)
        else:
            advance('NONE',24,1)
    else:
        raise RuntimeError('TM/HM bag selection deadline')
    start=value('sDiagnosticFrame')
    while value('sDiagnosticFrame')-start < 16000:
        if state()['callback'] == 'CB2_UpdatePartyMenu' and value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
            select_party_slot(slot); advance('A',24,1)
        elif value('(int)FuncIsActiveTask((void *)Task_HandleReplaceMoveInput)'):
            pointer=value('*(unsigned int *)&sMonSummaryScreen')
            advance(learn_move_button(pointer,bytes(gdb.selected_inferior().read_memory(pointer+0x40c6,1))[0]),24,1)
        else:
            advance('A',96,1)
        learned=[value(f'(int)GetMonData3({mon},{13+i},0)') for i in range(4)]
        if move in learned and state()['callback'] == 'CB2_BagMenuRun' and value('(int)FuncIsActiveTask((void *)Task_BagMenu_HandleInput)'):
            advance('B',300,1); advance('B',120,1)
            settle()
            assert field_ready(state())
            print('NATURAL TM/HM LEARNED',item,move,slot,learned)
            return state()
    raise RuntimeError('TM/HM teaching deadline: '+str(state()))


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
                        level=value(f"(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),56,0)"),
                        moves=[value(f"(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),{13+j},0)") for j in range(4)])
                   for i in range(facts["party"])]
    facts["dex"]=value("(int)FlagGet(0x861)")
    facts["rival"]=value("(int)FlagGet(0x82)")
    facts["balls"]=value("(int)CountTotalItemQuantityInBag(4)")
    facts["badges"]=[value(f"(int)FlagGet({0x867+i})") for i in range(8)]
    facts["norman"]=value("(int)VarGet(0x4085)")
    facts["woods"]=value("(int)VarGet(0x4098)")
    facts["events"]={key:value(f"(int)FlagGet({flag})") for key,flag in EVENT_FLAGS.items()}
    facts["rustboro"]=value("(int)VarGet(0x405a)")
    facts["briney"]=value("(int)VarGet(0x4090)")
    facts['route110']=value('(int)VarGet(0x4069)')
    facts['inventory']={str(item):value(f'(int)CountTotalItemQuantityInBag({item})')
                        for item in (13,22,*range(339,347))}
    save=value('*(unsigned int *)&gSaveBlock1Ptr')
    facts['money']=value(f'(int)GetMoney((void *)({save}+0x490))')
    (SCRATCH/(name+".json")).write_text(json.dumps(facts,indent=2),encoding="utf-8")
    gdb.execute(f"dump binary memory {SCRATCH.as_posix()}/{name}.raw &sPixels ((char *)&sPixels)+153600")
    print("NATURAL SAVE PASS",facts)
    return facts


def path_to(x,y):
    current = state(); goal=(x+7,y+7)
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
    start=(current['x']+7,current['y']+7,objects[player*36+11]&15)
    blocked = {struct.unpack_from("<hh",objects,i*36+16) for i in range(16)
               if i != player and objects[i*36]&1}
    queue=deque([start]); previous={start:None}
    while queue:
        node=queue.popleft()
        if node[:2] == goal:
            route=[]
            while previous[node] is not None:
                node,button = previous[node]; route.append(button)
            return route[::-1]
        for dx,dy,button in ((1,0,"RIGHT"),(-1,0,"LEFT"),(0,1,"DOWN"),(0,-1,"UP")):
            point=(node[0]+dx,node[1]+dy)
            if not (0 <= point[0] < width and 0 <= point[1] < height) or point in blocked:
                continue
            cell=cells[point[1]*width+point[0]]
            elevation=cell>>12
            # Match IsElevationMismatchAt/ObjectEventUpdateElevation: 0 is
            # a transition tile; 15 preserves the object's current elevation.
            if node[2] != 0 and elevation not in (0,15,node[2]):
                continue
            nxt=(*point,node[2] if elevation == 15 else elevation)
            if nxt not in previous and passable(cell):
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
        if not field_ready(state()):
            return state()
    raise RuntimeError("Movement deadline: "+str(state()))
