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
