"""Natural daycare coverage: keyboard actions and read-only observations."""
import json
import struct
import gdb
import campaign_driver as d


def party():
    result=[]
    for slot in range(d.memory('gPlayerPartyCount',1)[0]):
        mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
        result.append(dict(slot=slot,
                           species=d.value(f'(int)GetMonData3({mon},11,0)'),
                           gender=d.value(f'(unsigned char)GetMonGender({mon})'),
                           level=d.value(f'(int)GetMonData3({mon},56,0)')))
    return result


def daycare():
    # Measured i686 layout; also checked in the linked compatibility getter.
    address=d.value('*(unsigned int *)&gSaveBlock1Ptr')+0x2ee8
    raw=bytes(gdb.selected_inferior().read_memory(address,288))
    parents=[]
    for slot in range(2):
        mon=f'(void *){address+140*slot}'
        parents.append(dict(species=d.value(f'(int)GetBoxMonData3({mon},11,0)'),
                            personality=d.value(f'(unsigned int)GetBoxMonData3({mon},0,0)'),
                            steps=struct.unpack_from('<I',raw,140*slot+136)[0]))
    return dict(parents=parents,offspring=struct.unpack_from('<I',raw,280)[0],
                counter=raw[284],pending=d.value('(int)FlagGet(0x86)'),
                compatibility=d.value('(unsigned char)GetDaycareCompatibilityScoreFromSave()'))


def party_details():
    return [dict(mon,
        personality=d.value(f'(unsigned int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),0,0)'),
        is_egg=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),45,0)'),
        cycles=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),32,0)'))
        for mon in party()]


def checkpoint(name):
    facts=d.save_checkpoint(name)
    facts['breeding']=daycare()
    facts['breeding_party']=party_details()
    (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    print('NATURAL BREEDING CHECKPOINT',name,facts['breeding'],facts['breeding_party'])
    return facts


def deposit(slot):
    assert d.state()['map'] == 'Route117_PokemonDayCare'
    before=d.state()['party']; species=party()[slot]['species']
    d.go(2,4); d.advance('UP',24,4); d.advance('A',24,1)
    for step in range(300):
        if d.state()['callback'] == 'CB2_UpdatePartyMenu' and d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
            d.select_party_slot(slot); d.advance('A',24,1)
        elif d.state()['party'] < before:
            if d.field_ready(d.state()):break
            d.advance('B',96,1)
        else:
            d.advance('A',96,1)
    else:
        raise RuntimeError('Daycare deposit deadline: '+str(d.state()))
    assert d.state()['party'] == before-1
    assert species in [parent['species'] for parent in daycare()['parents']]
    print('NATURAL DAYCARE DEPOSIT PASS',species,daycare())


def mother():
    assert d.state()['map'] == 'Route117'
    d.fly_to('MauvilleCity')
    d.go(23,15); d.cross('UP','MauvilleCity_Mart'); d.buy_item(4,20)
    d.go(3,7); d.cross('DOWN','MauvilleCity'); d.connect('Route117')
    d.go(51,6); d.cross('UP','Route117_PokemonDayCare')
    assert party()[2]['species'] == 44 and party()[2]['gender'] == 254
    deposit(2)
    d.warp_to(2,8,'Route117')
    assert daycare()['offspring'] == 0
    return checkpoint('r06-mother-deposited')


def catch_father():
    assert d.state()['map'] == 'Route117' and d.state()['party'] == 5
    assert daycare()['parents'][0]['species'] == 44
    previous=d.CATCH_SPECIES,d.CATCH_GENDER,d.CATCH_BALL,d.RUN_WILD
    try:
        d.CATCH_SPECIES={43}; d.CATCH_GENDER=0; d.CATCH_BALL=4; d.RUN_WILD=True
        grass=None
        layout=struct.unpack('<I',d.memory('gMapHeader',4))[0]
        width,height=struct.unpack('<II',bytes(gdb.selected_inferior().read_memory(layout,8)))
        position=d.state()
        points=sorted(((x,y) for y in range(height) for x in range(width-1)),
                      key=lambda p:abs(p[0]-position['x'])+abs(p[1]-position['y']))
        for x,y in points:
            if not all(d.value(f'(unsigned char)MapGridGetMetatileBehaviorAt({xx+7},{y+7})') == 2 for xx in (x,x+1)):
                continue
            try:
                d.path_to(x,y)
            except RuntimeError:
                continue
            grass=(x,y); break
        assert grass, 'No reachable grass pair in Route117'
        print('NATURAL BREEDING GRASS',grass)
        before=d.value('(int)CountTotalItemQuantityInBag(4)')
        for step in range(400):
            d.go(grass[0]+step%2,grass[1],dialogue_limit=60000)
            if d.state()['party'] == 6:break
        else:
            raise RuntimeError('Male Oddish encounter deadline')
        assert party()[5]['species'] == 43 and party()[5]['gender'] == 0
        assert d.value('(int)CountTotalItemQuantityInBag(4)') < before
        print('NATURAL MALE ODDISH CATCH PASS',party()[5])
        return checkpoint('r06-father-caught')
    finally:
        d.CATCH_SPECIES,d.CATCH_GENDER,d.CATCH_BALL,d.RUN_WILD=previous


def pace(stop_when=None):
    current=d.state()
    assert current['map'] == 'Route117' and current['y'] == 6
    target=58 if current['x'] <= 54 else 51
    route=d.path_to(target,6)
    assert route and all(button == route[0] for button in route)
    assert route[0] in ('LEFT','RIGHT')
    hold=8*(len(route)-1)+4
    d.advance(route[0]+'+B',hold+20,hold)
    d.settle(60000,stop_when=stop_when)
    current=d.state()
    assert current['map'] == 'Route117' and current['y'] == 6 and 50 <= current['x'] <= 59


def generate():
    assert d.state()['party'] == 6 and party()[5]['species'] == 43
    assert party()[5]['gender'] == 0
    d.RUN_WILD=True
    d.go(51,6); d.cross('UP','Route117_PokemonDayCare'); deposit(5)
    d.warp_to(2,8,'Route117')
    before=daycare()
    assert [mon['species'] for mon in before['parents']] == [44,43]
    assert before['compatibility'] == 20 and before['offspring'] == 0
    checkpoint('r06-parents-deposited')
    d.go(51,6)
    for step in range(2000):
        if daycare()['pending']:break
        pace()
    else:
        raise RuntimeError('Daycare egg generation deadline: '+str(daycare()))
    after=daycare()
    assert after['offspring'] != 0 and after['pending'] == 1
    assert all(a['steps'] > b['steps'] for a,b in zip(after['parents'],before['parents']))
    print('NATURAL DAYCARE EGG GENERATED PASS',before,after)
    return checkpoint('r06-egg-pending')


def receive():
    assert daycare()['pending'] == 1 and daycare()['offspring'] != 0
    assert d.state()['party'] == 5
    d.go(51,6); d.cross('UP','Route117_PokemonDayCare')
    d.warp_to(2,8,'Route117')  # The map script moves the waiting keeper outside.
    d.talk(47,7,'UP')
    assert d.state()['party'] == 6
    egg=party_details()[5]
    assert egg['species'] == 43 and egg['is_egg'] == 1 and egg['cycles'] == 20
    assert daycare()['pending'] == 0 and daycare()['offspring'] == 0
    print('NATURAL DAYCARE EGG RECEIVED PASS',egg,daycare())
    return checkpoint('r06-egg-received')


def hatch():
    original=party_details()[5]
    assert original['is_egg'] == 1 and original['species'] == 43
    d.go(51,6)
    captured=False
    for step in range(2000):
        if party_details()[5]['is_egg'] == 0:break
        pace(stop_when=lambda current:current['callback'] == 'CB2_EggHatch')
        if d.state()['callback'] == 'CB2_EggHatch':
            d.advance('NONE',480)
            (d.SCRATCH/'r06-hatch-animation.raw').write_bytes(d.memory('sPixels',153600))
            captured=True
            d.settle(60000)
        if step%100 == 0:
            print('NATURAL EGG WALKING',step,party_details()[5],daycare())
    else:
        raise RuntimeError('Egg hatch walking deadline: '+str(party_details()))
    hatched=party_details()[5]
    assert captured and hatched['is_egg'] == 0 and hatched['species'] == 43
    assert hatched['level'] == 5 and hatched['personality'] == original['personality']
    assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+500),4,0)') == 0
    assert d.field_ready(d.state())
    print('NATURAL EGG HATCH PASS',original,hatched)
    return checkpoint('r06-oddish-hatched')


def prepare():
    assert d.state()['map'] == 'LittlerootTown_BrendansHouse_2F'
    assert d.value('(int)FlagGet(0x864)') == 1
    print('NATURAL BREEDING ORIGINAL PARTY',party())
    d.warp_to(7,1,'LittlerootTown_BrendansHouse_1F',60000)
    d.go(9,8,dialogue_limit=60000)
    if d.state()['map'] == 'LittlerootTown_BrendansHouse_1F':
        d.advance('DOWN',300,8)
        d.settle(60000)
    if d.state()['map'] == 'LittlerootTown_ProfessorBirchsLab':
        d.save_checkpoint('r06-postgame-lab')
        d.warp_to(6,12,'LittlerootTown')
    assert d.state()['map'] == 'LittlerootTown'
    d.fly_to('MauvilleCity')
    d.RUN_WILD=True
    d.connect('Route117')
    d.go(51,6)
    print('NATURAL DAYCARE ARRIVAL PASS',d.state(),party())
    return d.save_checkpoint('r06-daycare-arrival')
