"""Solve Sootopolis ice from live tile observations, then execute only keys."""
import campaign_driver as d


def ice_path(tiles,start,end):
    """Visit each thin-ice tile once, with connectivity/degree pruning."""
    neighbors={p:{q for q in ((p[0]+1,p[1]),(p[0]-1,p[1]),
                              (p[0],p[1]+1),(p[0],p[1]-1)) if q in tiles}
               for p in tiles}
    def search(current,left):
        if not left:
            return [current] if current == end else None
        if current == end:
            return None
        available=left|{current}
        if any(len(neighbors[p]&available) < (1 if p == end else 2) for p in left):
            return None
        seen={current}; queue=[current]
        while queue:
            for point in (neighbors[queue.pop()]&available)-seen:
                seen.add(point); queue.append(point)
        if seen != available:
            return None
        for point in sorted(neighbors[current]&left,
                            key=lambda p:(len(neighbors[p]&left),p)):
            path=search(point,left-{point})
            if path:
                return [current]+path
        return None
    result=search(start,set(tiles)-{start})
    assert result and len(result) == len(tiles) and len(set(result)) == len(tiles)
    return result


def ice_step(x,y):
    origin=d.state(); dx,dy=x-origin['x'],y-origin['y']
    assert abs(dx)+abs(dy) == 1
    button={(1,0):'RIGHT',(-1,0):'LEFT',(0,1):'DOWN',(0,-1):'UP'}[(dx,dy)]
    for _ in range(4):
        d.advance(button,32,4); d.settle(10000)
        state=d.state()
        assert state['map'] == 'SootopolisCity_Gym_1F'
        if (state['x'],state['y']) == (x,y):
            assert d.value('(int)MapGridGetMetatileBehaviorAt(%d,%d)'%(x+7,y+7)) == 0x27
            return
        # A short pulse may only turn the player. Retry only if no step occurred.
        assert (state['x'],state['y']) == (origin['x'],origin['y'])
    raise RuntimeError('Ice movement deadline: '+str(d.state()))


def board(bottom,top,count,complete):
    tiles={(x,y) for y in range(top,bottom+1) for x in range(3,14)
           if d.value('(int)MapGridGetMetatileBehaviorAt(%d,%d)'%(x+7,y+7)) == 0x26
           and d.value('(int)MapGridGetCollisionAt(%d,%d)'%(x+7,y+7)) == 0}
    assert len(tiles) == count, tiles
    path=ice_path(tiles,(8,bottom),(8,top))
    for x,y in path:
        ice_step(x,y)
    assert d.value('(int)VarGet(0x4022)') == complete
    print('NATURAL SOOTOPOLIS ICE BOARD PASS',count,path,d.state())


def puzzle():
    assert d.state()['map'] == 'SootopolisCity_Gym_1F'
    assert d.value('(int)VarGet(0x4022)') == 1
    d.go(8,20)
    for bottom,top,count,complete in ((19,17,7,9),(14,12,19,29),(9,6,38,68)):
        board(bottom,top,count,complete)
        if complete != 68:
            d.go(8,15 if complete == 9 else 10)
    d.go(8,3)
    return d.save_checkpoint('r04-juan-ready')
