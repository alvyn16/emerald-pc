"""Natural daycare coverage: keyboard actions and read-only observations."""
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
