"""Operate the measured Mossdeep floor switches and transports by keyboard."""
import campaign_driver as d
import map_warp_driver as pads


def press(x,y):
    if (d.state()['x'],d.state()['y']) == (x,y):
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            try:
                path=d.path_to(x+dx,y+dy)
            except RuntimeError:
                continue
            if len(path) == 1:
                d.go(x+dx,y+dy)
                break
        else:
            raise RuntimeError('No free floor-switch neighbor')
    d.go(x,y,dialogue_limit=80000)
    assert (d.state()['x'],d.state()['y']) == (x,y)


def blue_room(checkpoint='r04-mossdeep-green-room'):
    assert d.state()['map'] == 'MossdeepCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (8,12)
    for _ in range(3):
        press(8,10)
    for _ in range(3):
        press(8,6)
    for _ in range(4):
        press(6,7)
    press(8,10)
    pads.activate(10)
    return d.save_checkpoint(checkpoint) if checkpoint else d.state()


def purple_room(checkpoint='r04-mossdeep-leaders-ready'):
    assert d.state()['map'] == 'MossdeepCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (23,20)
    press(23,21)
    press(23,24)
    press(23,24)
    press(15,34)
    press(15,34)
    press(23,21)
    pads.activate(7)
    pads.activate(4)
    for _ in range(3):
        press(8,10)
    pads.activate(10)
    assert d.path_to(13,32)
    pads.activate(12)
    d.go(23,9)
    return d.save_checkpoint(checkpoint) if checkpoint else d.state()


def entry_to_blue():
    assert d.state()['map'] == 'MossdeepCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (6,35)
    press(3,30)
    pads.activate(2)
    press(2,21)
    pads.activate(4)
    return d.state()


def circuit():
    entry_to_blue()
    blue_room(None)
    pads.activate(11)
    press(8,10)
    pads.activate(5)
    pads.activate(6)
    return purple_room(None)


def leaders(expected_outcome=1):
    assert d.field_ready(d.state()) and d.state()['map'] == 'MossdeepCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (23,9)
    assert d.value('(int)HasTrainerBeenFought(271)') == 0
    for flag in (0x86d,0x4f6,0xab):
        assert d.value(f'(int)FlagGet({flag})') == 0
    for var in (0x405d,0x409f):
        assert d.value(f'(int)VarGet({var})') == 0
    d.talk(23,8,'UP',120000)
    assert d.memory('gBattleOutcome',1)[0] == expected_outcome, d.state()
    if expected_outcome == 2:
        assert d.state()['map'] == 'MossdeepCity', d.state()
        assert (d.state()['x'],d.state()['y']) == (28,17)
        for slot in range(d.state()['party']):
            mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
            assert d.value(f'(int)GetMonData3({mon},57,0)') == d.value(f'(int)GetMonData3({mon},58,0)')
        assert d.value('(int)HasTrainerBeenFought(271)') == 0
        for flag in (0x86d,0x4f6,0xab):
            assert d.value(f'(int)FlagGet({flag})') == 0
        for var in (0x405d,0x409f):
            assert d.value(f'(int)VarGet({var})') == 0
        return d.save_checkpoint('r04-mossdeep-defeat')
    assert expected_outcome == 1
    assert d.state()['map'] == 'MossdeepCity_Gym'
    assert d.value('(int)HasTrainerBeenFought(271)') == 1
    for flag in (0x86d,0x4f6,0xab):
        assert d.value(f'(int)FlagGet({flag})') == 1
    for var in (0x405d,0x409f):
        assert d.value(f'(int)VarGet({var})') == 1
    d.go(23,9)
    return d.save_checkpoint('r04-mossdeep-win')
