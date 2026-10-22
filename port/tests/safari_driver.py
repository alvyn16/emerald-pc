"""Natural Safari quotas: actual admission, encounters, keys and walking."""
import struct
import json
import gdb
import campaign_driver as d


def counters():
    return dict(active=d.value('(unsigned int)GetSafariZoneFlag()'),
                balls=d.memory('gNumSafariBalls',1)[0],
                steps=int.from_bytes(d.memory('sSafariZoneStepCounter',2),'little'))


def prepare():
    assert d.state()['map'] == 'Route117'
    d.RUN_WILD=True
    d.fly_to('DewfordTown')
    for attempt in range(20):
        if d.value('(int)CountTotalItemQuantityInBag(262)'):break
        objects=d.memory('gObjectEvents',16*36)
        slot=next(i for i in range(16) if objects[i*36]&1 and objects[i*36+8] == 3)
        x,y=struct.unpack_from('<hh',objects,slot*36+16)
        d.go(x-7,y-8)
        d.advance('DOWN',8,1); d.advance('A',24,1); d.settle()
    assert d.value('(int)CountTotalItemQuantityInBag(262)') == 1
    d.fly_to('LilycoveCity')
    d.go(23,25); d.cross('UP','LilycoveCity_ContestLobby')
    d.go(14,4); d.advance('UP',24,4); d.advance('A',24,1)
    for step in range(200):
        if d.value('(int)CountTotalItemQuantityInBag(273)'):break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Pokeblock Case gift deadline')
    for step in range(200):
        if d.field_ready(d.state()):break
        d.advance('B',96,1)
    else:
        raise RuntimeError('Contest reception exit deadline')
    assert d.value('(int)CountTotalItemQuantityInBag(273)') == 1
    d.warp_to(14,11,'LilycoveCity'); d.connect('Route121')
    d.go(37,6); d.cross('UP','Route121_SafariZoneEntrance')
    print('NATURAL SAFARI RECEPTION READY PASS',d.state(),counters())
    return d.save_checkpoint('r07-safari-reception')


def enter():
    assert d.state()['map'] == 'Route121_SafariZoneEntrance'
    assert counters()['active'] == 0
    address=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    before=d.value(f'(int)GetMoney((void *)({address}+0x490))')
    d.go(8,4,dialogue_limit=60000)
    d.settle(60000)
    assert d.state()['map'] == 'SafariZone_South'
    address=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    after=d.value(f'(int)GetMoney((void *)({address}+0x490))')
    assert after == before-500
    assert counters() == dict(active=1,balls=30,steps=500)
    print('NATURAL SAFARI ADMISSION PASS',before,after,counters(),d.state())


def shore():
    layout=struct.unpack('<I',d.memory('gMapHeader',4))[0]
    width,height=struct.unpack('<II',bytes(gdb.selected_inferior().read_memory(layout,8)))
    position=d.state()
    points=sorted(((x,y) for y in range(1,height-1) for x in range(1,width-1)),
                  key=lambda p:abs(p[0]-position['x'])+abs(p[1]-position['y']))
    for x,y in points:
        for dx,dy,direction in ((1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN'),(0,-1,'UP')):
            behavior=d.value(f'(unsigned char)MapGridGetMetatileBehaviorAt({x+dx+7},{y+dy+7})')
            if not d.value(f'(unsigned char)MetatileBehavior_IsSurfableWaterOrUnderwater({behavior})'):continue
            try:d.path_to(x,y)
            except RuntimeError:continue
            d.go(x,y,dialogue_limit=60000); d.advance(direction,24,4)
            print('NATURAL SAFARI FISHING SHORE',x,y,direction,counters())
            return
    raise RuntimeError('No reachable Safari fishing shore')


def fish():
    d.open_start_action(2)
    for step in range(200):
        if d.value('(int)FuncIsActiveTask((void *)Task_Fishing)'):break
        button='A'
        if d.value('(int)FuncIsActiveTask((void *)Task_BagMenu_HandleInput)'):
            bag=d.memory('gBagPosition',28); pocket=bag[5]
            if pocket != 4:button='RIGHT'
            else:
                entries=[d.value(f'(int)BagGetItemIdByPocketPosition(5,{i})') for i in range(30)]
                cursor=struct.unpack_from('<H',bag,16)[0]+struct.unpack_from('<H',bag,26)[0]
                target=entries.index(262)
                button='A' if cursor == target else 'DOWN' if cursor < target else 'UP'
        d.advance(button,24,1)
    else:raise RuntimeError('Old Rod menu deadline')
    for step in range(300):
        task=d.value('(unsigned char)FindTaskIdByFunc((void *)Task_Fishing)')
        if task == 255:
            d.settle(60000)
            return
        state=struct.unpack_from('<h',d.memory('gTasks',640),task*40+8)[0]
        d.advance('A' if state in (7,10) or state >= 13 else 'NONE',24,1)
    raise RuntimeError('Fishing deadline at task state '+str(state))


def checkpoint(name):
    assert d.state()['map'] == 'Route121_SafariZoneEntrance'
    assert counters() == dict(active=0,balls=0,steps=0)
    facts=d.save_checkpoint(name); facts['safari']=counters()
    (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    return facts


def balls():
    d.SAFARI_ACTION=0
    enter()
    throws=[]
    class Throw(gdb.Breakpoint):
        def stop(self):
            throws.append(d.memory('gNumSafariBalls',1)[0])
            return False
    observer=Throw('HandleAction_SafariZoneBallThrow',internal=True); observer.silent=True
    try:
        d.connect('SafariZone_Southwest'); shore()
        outcomes=[]
        for attempt in range(300):
            if counters()['active'] == 0:break
            before=counters(); fish(); after=counters()
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            print('NATURAL SAFARI FISHING RESULT',attempt,before,after,outcomes[-1])
        else:raise RuntimeError('Safari ball exhaustion deadline')
        assert throws == list(range(30,0,-1)), throws
        assert 7 in outcomes, 'No real capture observed'
        print('NATURAL SAFARI ALL BALLS EXHAUSTED PASS',throws,outcomes,counters(),d.state())
        return checkpoint('r07-balls-exhausted')
    finally:
        observer.delete()


def steps():
    d.SAFARI_ACTION=3
    enter()
    remaining=[]
    class Step(gdb.Breakpoint):
        def stop(self):
            count=int.from_bytes(d.memory('sSafariZoneStepCounter',2),'little')
            if count:remaining.append(count)
            return False
    observer=Step('SafariZoneTakeStep',internal=True); observer.silent=True
    try:
        start=d.state(); origin=(start['x'],start['y']); neighbor=None
        for dx,dy,button in ((-1,0,'LEFT'),(1,0,'RIGHT'),(0,1,'DOWN')):
            point=(origin[0]+dx,origin[1]+dy)
            if d.value(f'(unsigned char)MapGridGetMetatileBehaviorAt({point[0]+7},{point[1]+7})') != 0:continue
            try:route=d.path_to(*point)
            except RuntimeError:continue
            if route == [button]:neighbor=point; break
        assert neighbor, 'No open Safari walking pair'
        for attempt in range(1200):
            if counters()['active'] == 0:break
            current=d.state(); position=(current['x'],current['y'])
            assert position in (origin,neighbor), current
            target=neighbor if position == origin else origin
            route=d.path_to(*target); assert len(route) == 1
            d.advance(route[0],32,12)
            if not d.field_ready(d.state()):d.settle(60000)
            if counters()['active']:assert counters()['balls'] == 30
        else:raise RuntimeError('Safari walking quota deadline')
        assert remaining == list(range(500,0,-1)), remaining
        print('NATURAL SAFARI 500 WALKED STEPS PASS',len(remaining),counters(),d.state())
        return checkpoint('r07-steps-exhausted')
    finally:
        observer.delete()
