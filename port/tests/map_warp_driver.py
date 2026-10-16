"""Operate same-map teleport pads by keys; read destinations from local JSON."""
import json
import campaign_driver as d


def activate(index):
    current=d.state()
    name=current['map']
    behavior={'AquaHideout_B1F':0x67,'AquaHideout_B2F':0x67,
              'MossdeepCity_Gym':0x0e}[name]
    data=json.loads((d.ROOT/'pokeemerald/data/maps'/name/'map.json').read_text())
    pads=data['warp_events']
    assert 0 <= index < len(pads)
    pad=pads[index]
    assert pad['dest_map'] == data['id'], 'Use warp_to for stairs between maps'
    target=pads[int(pad['dest_warp_id'])]
    x,y=pad['x'],pad['y']
    assert d.value(f'(int)MapGridGetMetatileBehaviorAt({x+7},{y+7})') == behavior
    path=d.path_to(x,y)
    if not path:
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            try:
                if len(d.path_to(x+dx,y+dy)) != 1:
                    continue
            except RuntimeError:
                continue
            if d.value(f'(int)MapGridGetMetatileBehaviorAt({x+dx+7},{y+dy+7})') in (0x67,0x0e):
                continue
            d.go(x+dx,y+dy)
            break
        else:
            raise RuntimeError('No space to step off the current teleport pad')
        path=d.path_to(x,y)
    button=path[-1]
    dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[button]
    approach=x-dx,y-dy
    d.go(*approach,dialogue_limit=80000)
    assert d.state()['map'] == name
    for attempt in range(4):
        d.advance(button,300,8); d.settle(80000)
        actual=d.state()
        if actual['map'] == name and (actual['x'],actual['y']) == (target['x'],target['y']):
            print('NATURAL MAP PAD PASS',name,index,pad['dest_warp_id'],actual)
            return actual
        assert actual['map'] == name and (actual['x'],actual['y']) == approach, (
            'Unexpected pad destination',index,actual,target)
    raise RuntimeError('Teleport pad input deadline: '+str(d.state()))
