"""Natural Wattson sidequest: keys and read-only assertions, no progress writes."""
import campaign_driver as d


def get_key():
    assert d.state()['map'] == 'EverGrandeCity'
    assert d.value('(int)FlagGet(0xd0)') == 0
    d.RUN_WILD=True
    d.fly_to('MauvilleCity')
    d.talk(29,10,'UP')
    assert d.value('(int)FlagGet(0xd0)') == 1
    assert d.value('(int)VarGet(0x40ba)') == 0
    d.go(22,6); d.cross('UP','MauvilleCity_PokemonCenter_1F')
    d.nurse()
    d.go(7,8); d.cross('DOWN','MauvilleCity')
    print('NATURAL NEW MAUVILLE KEY PASS',d.state())
    return d.save_checkpoint('r05-new-mauville-key')


def enter():
    assert d.state()['map'] == 'MauvilleCity'
    assert d.value('(int)CountTotalItemQuantityInBag(271)') == 1
    d.RUN_WILD=True
    d.connect('Route110')
    # Shore measured from the live map and verified in the entry replay.
    d.talk(14,19,'DOWN')
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.go(35,25)
    d.warp_to(35,24,'NewMauville_Entrance')
    d.go(4,2)
    d.settle()
    assert d.value('(int)VarGet(0x40ba)') == 1
    d.warp_to(4,1,'NewMauville_Inside')
    print('NATURAL NEW MAUVILLE ENTRY PASS',d.state())
    return d.save_checkpoint('r05-new-mauville-inside')


def stop_generator():
    assert d.state()['map'] == 'NewMauville_Inside'
    assert d.value('(int)VarGet(0x40ba)') == 1
    d.RUN_WILD=True
    for x,y,blue in ((30,38,1),(18,36,0)):
        d.go(x,y); d.settle()
        assert d.value('(int)VarGet(0x4001)') == blue
        assert d.value('(int)VarGet(0x4002)') == 1-blue
        print('NATURAL NEW MAUVILLE BUTTON PASS',x,y,blue)
    ropes=d.value('(int)CountTotalItemQuantityInBag(85)')
    d.talk(16,23,'UP')
    assert d.value('(int)CountTotalItemQuantityInBag(85)') == ropes+1
    d.go(16,22); d.settle()
    assert d.value('(int)VarGet(0x4001)') == 1
    before=d.value('(int)CountTotalItemQuantityInBag(23)')
    d.talk(17,11,'UP')
    assert d.value('(int)CountTotalItemQuantityInBag(23)') == before+1
    d.go(17,10); d.settle()
    assert d.value('(int)VarGet(0x4002)') == 1
    d.go(33,6); d.settle()
    assert d.value('(int)VarGet(0x40ba)') == 2
    print('NATURAL NEW MAUVILLE GENERATOR OFF PASS',d.state())
    return d.save_checkpoint('r05-new-mauville-generator-off')


def collect_thunderbolt():
    assert d.state()['map'] == 'NewMauville_Inside'
    assert d.value('(int)VarGet(0x40ba)') == 2
    ropes=d.value('(int)CountTotalItemQuantityInBag(85)')
    assert ropes > 0
    d.RUN_WILD=True
    d.open_start_action(2)
    for step in range(300):
        if d.state()['map'] == 'Route110' and d.field_ready(d.state()): break
        button=d.item_bag_button(85) if d.state()['callback'] == 'CB2_BagMenuRun' else 'A'
        d.advance(button,96 if button == 'A' else 24,1)
    else:
        raise RuntimeError('Escape Rope exit deadline: '+str(d.state()))
    assert d.value('(int)CountTotalItemQuantityInBag(85)') == ropes-1
    print('NATURAL NEW MAUVILLE ESCAPE ROPE PASS',d.state())
    d.fly_to('MauvilleCity')
    assert d.value('(int)FlagGet(0xd1)') == 0
    d.talk(29,10,'UP')
    assert d.value('(int)FlagGet(0xd1)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(312)') == 1
    assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+500),11,0)') == 406
    d.teach_tm(312,5)
    assert d.value('(int)CountTotalItemQuantityInBag(312)') == 0
    d.set_lead(5)
    moves=[d.value(f'(int)GetMonData3((void *)&gPlayerParty,{13+i},0)') for i in range(4)]
    assert 85 in moves
    print('NATURAL WATTSON THUNDERBOLT LEARNED PASS',moves)
    return d.save_checkpoint('r05-rayquaza-thunderbolt')


def prepare_league():
    assert d.state()['map'] == 'MauvilleCity'
    assert d.value('(int)FlagGet(0xd1)') == 1
    d.settle()
    d.fly_to('MossdeepCity')
    d.go(37,19); d.cross('UP','MossdeepCity_Mart')
    d.buy_item(21,4)
    d.go(3,7); d.cross('DOWN','MossdeepCity')
    d.go(28,17); d.cross('UP','MossdeepCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','MossdeepCity')
    d.fly_to('EverGrandeCity')
    d.go(18,6); d.cross('UP','EverGrandeCity_PokemonLeague_1F')
    d.talk(3,4,'UP')
    d.warp_to(9,1,'EverGrandeCity_Hall5',50000)
    d.warp_to(5,2,'EverGrandeCity_SidneysRoom',50000)
    assert d.value('(int)CountTotalItemQuantityInBag(21)') == 4
    assert d.value('(int)CountTotalItemQuantityInBag(24)') == 2
    print('NATURAL THUNDERBOLT LEAGUE PREPARATION PASS',d.state())
    return d.save_checkpoint('r05-thunderbolt-league-ready')
