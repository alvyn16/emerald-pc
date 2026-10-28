"""Natural Battle Pyramid access driven through the game's controls."""
import campaign_driver as d


def lobby():
    assert d.state()['map']=='BattleFrontier_BattleTowerLobby'
    d.warp_to(12,9,'BattleFrontier_OutsideEast')
    d.go(58,15);d.cross('UP','BattleFrontier_BattlePyramidLobby')
    d.go(7,13)
    print('NATURAL PYRAMID RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r14-pyramid-reception')


def take_held(slot):
    item=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{slot*100}),12,0)')
    assert item
    d.open_start_action(1); d.select_party_slot(slot);d.advance('A',48,1)
    def choose(action):
        pointer=d.value('*(unsigned int *)&sPartyMenuInternal')
        context=bytes(d.gdb.selected_inferior().read_memory(pointer+15,9))
        target=context[:context[8]].index(action)
        for _ in range(12):
            cursor=d.value('(int)Menu_GetCursorPos()')
            if cursor==target:
                d.advance('A',96,1);return
            d.advance('DOWN' if cursor<target else 'UP',24,1)
        raise RuntimeError('Pyramid preparation item menu deadline')
    choose(3);choose(5)
    for _ in range(30):
        if d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{slot*100}),12,0)')==0:break
        d.advance('A',48,1)
    else:raise RuntimeError('Held item not returned to bag')
    for _ in range(30):
        if d.field_ready(d.state()):break
        d.advance('B',96,1)
    else:raise RuntimeError('Did not leave party menu')
    print('NATURAL PYRAMID ITEM REMOVED PASS',slot,item,flush=True)


def prepare():
    assert d.state()['map']=='BattleFrontier_BattlePyramidLobby'
    for slot in (1,2):take_held(slot)
    print('NATURAL PYRAMID ELIGIBLE TEAM PASS',d.state())
    return d.save_checkpoint('r14-pyramid-ready')


def enter():
    import frontier_driver as frontier
    ready=lambda current:current['map']=='BattleFrontier_BattlePyramidFloor' and d.field_ready(current)
    result=frontier.owned_enter('BattleFrontier_BattlePyramidLobby',7,13,stop_when=ready)
    assert ready(result),result
    print('NATURAL PYRAMID FLOOR ENTRY PASS',result,frontier.records(),flush=True)


def exit_location():
    import struct
    width,height,address=struct.unpack('<III',d.memory('gBackupMapLayout',12))
    cells=struct.unpack('<%dH'%(width*height),bytes(d.gdb.selected_inferior().read_memory(address,width*height*2)))
    exits=[(x,y) for y in range(32) for x in range(32)
           if cells[(y+7)*width+x+7]&0x3ff==0x28e]
    assert len(exits)==1,exits
    return exits[0]


def first_floor():
    import frontier_driver as frontier
    enter(); before=frontier.records()['curChallengeBattleNum']
    for attempt in range(150):
        current=d.settle(90000)
        if current['map']=='BattleFrontier_BattlePyramidLobby':
            raise RuntimeError('Pyramid challenge lost before first ascent: '+str(current))
        assert current['map']=='BattleFrontier_BattlePyramidFloor',current
        floor=frontier.records()['curChallengeBattleNum']
        if floor>before:
            print('NATURAL PYRAMID ASCENT PASS',before,floor,current,flush=True);return
        x,y=exit_location()
        print('NATURAL PYRAMID EXIT',floor,x,y,current,flush=True)
        d.walk(x,y)
    raise RuntimeError('Pyramid first floor deadline')


def round_trip():
    import json
    import frontier_driver as frontier
    before=frontier.records();enter(); floors=[]
    d.open_start_action(12)  # MENU_ACTION_PYRAMID_BAG
    assert d.value('(int)FuncIsActiveTask((void *)Task_HandlePyramidBagInput)')
    assert d.value('*(unsigned int *)&gPyramidBagMenu')!=0
    print('NATURAL PYRAMID SEPARATE BAG PASS',d.state(),flush=True)
    for _ in range(50):
        if d.field_ready(d.state()):break
        d.advance('B',96,1)
    else:raise RuntimeError('Pyramid bag did not close')
    for attempt in range(500):
        current=d.settle(90000);room=current['map']
        if room=='BattleFrontier_BattlePyramidLobby':break
        if room=='BattleFrontier_BattlePyramidTop':
            d.talk(17,12,'UP',90000);continue
        assert room=='BattleFrontier_BattlePyramidFloor',current
        floor=frontier.records()['curChallengeBattleNum']
        if floor not in floors:floors.append(floor)
        x,y=exit_location()
        print('NATURAL PYRAMID FLOOR',floor,x,y,current,flush=True)
        d.walk(x,y)
    else:raise RuntimeError('Pyramid circuit deadline')
    after=frontier.records()
    print('NATURAL PYRAMID ROUND RESULT',floors,before,after,flush=True)
    if floors==list(range(7)) and after['battlePoints']>before['battlePoints']:
        assert after['pyramidWinStreaks'][1]>=7
        name='r14-pyramid-complete'
    else:name='r14-pyramid-loss'
    facts=d.save_checkpoint(name);facts['frontier']=frontier.records();facts['pyramid_floors']=floors
    (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')

