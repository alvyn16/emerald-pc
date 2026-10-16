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


def blue_room():
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
    return d.save_checkpoint('r04-mossdeep-green-room')
