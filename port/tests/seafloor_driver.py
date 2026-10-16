"""Exercise the real Dive menu and cave route without writing story state."""
import campaign_driver as d


def dive_entry():
    assert d.state()['map'] == 'Route128'
    assert d.value('(int)FlagGet(0x86d)') == 1
    assert d.value('(int)FlagGet(0x7b)') == 1
    d.RUN_WILD=True
    d.go(38,27)
    d.choose_field_move(0,6); d.settle(30000)
    assert d.state()['map'] == 'Underwater_Route128'
    assert (d.state()['x'],d.state()['y']) == (38,27)
    assert d.memory('gPlayerAvatar',1)[0]&16
    # The cave door has collision; approach it and press UP as a player would.
    d.cross('UP','Underwater_SeafloorCavern')
    assert (d.state()['x'],d.state()['y']) == (6,7)
    d.choose_field_move(0,6); d.settle(30000)
    assert d.state()['map'] == 'SeafloorCavern_Entrance'
    assert (d.state()['x'],d.state()['y']) == (10,17)
    assert d.memory('gPlayerAvatar',1)[0]&8
    return d.save_checkpoint('r04-seafloor-entry')


def positions():
    import struct
    objects=d.memory('gObjectEvents',16*36)
    return {objects[i*36+8]:tuple(c-7 for c in struct.unpack_from('<hh',objects,i*36+16))
            for i in range(16) if objects[i*36]&1}


def push(local_id,button):
    """Make exactly one observed push; retry a missed key, never a game call."""
    dx,dy={'UP':(0,-1),'DOWN':(0,1),'LEFT':(-1,0),'RIGHT':(1,0)}[button]
    start=d.state(); origin=start['x'],start['y']
    box=origin[0]+dx,origin[1]+dy
    assert positions()[local_id] == box
    assert d.value('(int)FlagGet(0x889)') == 1
    for _ in range(4):
        d.advance(button,96,4); d.settle(30000)
        current=d.state(); actual=current['x'],current['y']
        assert current['map'] == start['map'] and actual in (origin,box), current
        if actual == box:
            assert positions()[local_id] == (box[0]+dx,box[1]+dy)
            return current
    raise RuntimeError('Boulder push key deadline')


def first_room():
    assert d.state()['map'] == 'SeafloorCavern_Room1'
    assert positions()[1] == (5,11) and positions()[2] == (12,11)
    d.RUN_WILD=True
    d.talk(4,10,'RIGHT')
    assert 3 not in positions(), 'The rock must be smashed before pushing north'
    d.talk(5,12,'UP')
    push(1,'UP')
    d.go(11,11); push(2,'RIGHT')
    d.go(6,3,dialogue_limit=80000); d.cross('UP','SeafloorCavern_Room2')
    assert (d.state()['x'],d.state()['y']) == (10,7)
    return d.save_checkpoint('r04-seafloor-room2')


def second_room():
    assert d.state()['map'] == 'SeafloorCavern_Room2'
    d.RUN_WILD=True
    d.talk(9,7,'LEFT')
    assert 6 not in positions()
    d.talk(4,6,'UP')
    for _ in range(3):
        push(4,'UP')
    assert positions()[4] == (4,2)
    d.go(6,2); d.cross('UP','SeafloorCavern_Room6')
    assert (d.state()['x'],d.state()['y']) == (11,21)
    return d.save_checkpoint('r04-seafloor-currents-entry')


def currents():
    assert d.state()['map'] == 'SeafloorCavern_Room6'
    assert (d.state()['x'],d.state()['y']) == (11,21)
    d.RUN_WILD=True
    d.talk(11,20,'UP')
    assert (d.state()['x'],d.state()['y']) == (11,19)
    assert d.memory('gPlayerAvatar',1)[0]&8
    # These are measured endpoints of the original current arrows.
    for button,target in (('UP',(14,16)),('RIGHT',(19,11)),
                          ('RIGHT',(8,12)),('LEFT',(4,8))):
        current=d.state(); origin=current['x'],current['y']
        for _ in range(4):
            d.advance(button,600,4); d.settle(30000)
            current=d.state(); actual=current['x'],current['y']
            assert current['map'] == 'SeafloorCavern_Room6' and actual in (origin,target), current
            if actual == target:
                break
        else:
            raise RuntimeError('Current route key deadline')
        print('NATURAL CURRENT ENDPOINT PASS',button,target,current['frame'])
    d.go(4,2)
    assert not d.memory('gPlayerAvatar',1)[0]&8
    d.cross('UP','SeafloorCavern_Room3')
    assert (d.state()['x'],d.state()['y']) == (4,15)
    return d.save_checkpoint('r04-seafloor-shelly-entry')


def shelly():
    assert d.state()['map'] == 'SeafloorCavern_Room3'
    assert d.value('(int)HasTrainerBeenFought(33)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.go(9,4,dialogue_limit=100000); d.talk(9,4,'DOWN',100000)
    assert d.value('(int)HasTrainerBeenFought(33)') == 1
    assert d.memory('gBattleOutcome',1)[0] == 1
    d.go(8,2); d.cross('UP','SeafloorCavern_Room8')
    assert (d.state()['x'],d.state()['y']) == (5,12)
    return d.save_checkpoint('r04-seafloor-final-puzzle-entry')


def final_puzzle():
    assert d.state()['map'] == 'SeafloorCavern_Room8'
    assert (d.state()['x'],d.state()['y']) == (5,12)
    d.RUN_WILD=True
    d.talk(4,8,'UP'); push(1,'UP')
    d.go(6,8); push(3,'UP')
    d.go(6,7); push(2,'LEFT')
    d.go(5,6); push(7,'UP')
    push(6,'LEFT'); push(10,'UP')
    d.go(5,5); push(8,'RIGHT'); push(11,'UP'); push(7,'LEFT')
    d.go(5,3); d.cross('UP','SeafloorCavern_Room9')
    assert (d.state()['x'],d.state()['y']) == (5,4)
    return d.save_checkpoint('r04-seafloor-archie-entry')


def archie():
    assert d.field_ready(d.state()) and d.state()['map'] == 'SeafloorCavern_Room9'
    assert (d.state()['x'],d.state()['y']) == (15,42)
    assert d.value('(int)HasTrainerBeenFought(34)') == 0
    assert d.value('(int)FlagGet(0x81)') == 0
    assert d.value('(int)FlagGet(0x53)') == 0
    for var in (0x407b,0x40a2,0x405e):
        assert d.value(f'(int)VarGet({var})') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(314)') == 1
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.go(17,42,dialogue_limit=150000)
    assert d.state()['map'] == 'Route128'
    assert d.value('(int)HasTrainerBeenFought(34)') == 1
    assert d.value('(int)FlagGet(0x81)') == 1
    assert d.value('(int)FlagGet(0x53)') == 1
    assert d.value('(int)VarGet(0x40a2)') == 1
    assert d.value('(int)VarGet(0x405e)') == 1
    assert d.value('(int)VarGet(0x407b)') == 2
    return d.save_checkpoint('r04-kyogre-escaped')
