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


def checkpoint(name):
    facts=d.save_checkpoint(name)
    facts['breeding']=daycare()
    facts['breeding_party']=[dict(mon,
        personality=d.value(f'(unsigned int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),0,0)'),
        is_egg=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),45,0)'),
        cycles=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{mon["slot"]*100}),32,0)'))
        for mon in party()]
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
