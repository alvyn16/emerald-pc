"""Read-only puzzle planning; every actual rotation is made by keyboard input."""
import heapq
import struct
import campaign_driver as d
import gdb


def plan(x,y):
    assert d.state()['map'] == 'FortreeCity_Gym'
    read=gdb.selected_inferior().read_memory
    width,height,address=struct.unpack('<III',d.memory('gBackupMapLayout',12))
    cells=struct.unpack('<%dH'%(width*height),bytes(read(address,width*height*2)))
    layout=struct.unpack('<I',d.memory('gMapHeader',4))[0]
    map_width,map_height=struct.unpack('<II',bytes(read(layout,8)))
    count=d.memory('sRotatingGate_PuzzleCount',1)[0]
    assert 0 < count <= 12
    config=d.value('*(unsigned int *)&sRotatingGate_PuzzleConfig')
    gates=list(struct.iter_unpack('<hhBB',bytes(read(config,count*6))))
    pointer=d.value('(unsigned int)GetVarPointer(0x4000)')
    orientations=tuple(bytes(read(pointer,count)))
    assert all(0 <= orientation < 4 for orientation in orientations)
    arms=d.memory('sRotatingGate_ArmLayout',12*8)
    rotations={name:d.memory('sRotatingGate_RotationInfo'+name,16)
               for name in ('North','South','West','East')}
    sweeps={rotation:list(struct.iter_unpack('bb',d.memory(symbol,16)))
            for rotation,symbol in ((1,'sRotatingGate_ArmPositionsAntiClockwiseRotation'),
                                    (2,'sRotatingGate_ArmPositionsClockwiseRotation'))}
    objects=d.memory('gObjectEvents',16*36); player=d.memory('gPlayerAvatar',6)[5]
    blocked={(struct.unpack_from('<h',objects,i*36+16)[0]-7,
              struct.unpack_from('<h',objects,i*36+18)[0]-7)
             for i in range(16) if i != player and objects[i*36]&1}
    def collision(px,py):
        if not (0 <= px < map_width and 0 <= py < map_height):
            return 1
        return (cells[(py+7)*width+px+7]>>10)&3
    rotation_cache={}
    def can_rotate(index,orientation,rotation):
        key=index,orientation,rotation
        if key not in rotation_cache:
            gx,gy,shape,_=gates[index]
            sweep=sweeps[rotation]
            occupied=[sweep[2*((orientation+arm)%4)+length]
                      for arm in range(4) for length in range(2)
                      if arms[shape*8+arm*2+length]]
            # The original build's CanRotate rejects collision value 1.
            rotation_cache[key]=all(collision(gx+dx,gy+dy) != 1 for dx,dy in occupied)
        return rotation_cache[key]
    # Check our hypothetical-state model against native read-only queries.
    for index,orientation in enumerate(orientations):
        for rotation in (1,2):
            assert can_rotate(index,orientation,rotation) == bool(
                d.value(f'(int)RotatingGate_CanRotate({index},{rotation})'))
    current=d.state(); start=(current['x'],current['y'],orientations)
    queue=[(abs(start[0]-x)+abs(start[1]-y),0,start)]
    costs={start:0}; previous={start:None}
    while queue:
        _,cost,node=heapq.heappop(queue)
        if cost != costs[node]:
            continue
        if node[:2] == (x,y):
            route=[]
            while previous[node] is not None:
                parent,button=previous[node]
                route.append((button,node)); node=parent
            return route[::-1],pointer,count
        assert len(costs) < 500000, 'Rotating puzzle search budget exceeded'
        for dx,dy,name,button in ((0,-1,'North','UP'),(0,1,'South','DOWN'),
                                  (-1,0,'West','LEFT'),(1,0,'East','RIGHT')):
            point=node[0]+dx,node[1]+dy
            if collision(*point) or point in blocked or point in ((15,24),(16,24)):
                continue
            changed=list(node[2]); allowed=True
            for index,(gx,gy,shape,_) in enumerate(gates):
                local=point[0]-gx+2,point[1]-gy+2
                if not all(0 <= coordinate < 4 for coordinate in local):
                    continue
                code=rotations[name][local[1]*4+local[0]]
                if code == 255:
                    continue
                arm=code&15; orientation=changed[index]
                if not arms[shape*8+2*((arm//2-orientation)%4)+arm%2]:
                    continue
                rotation=code>>4
                if not can_rotate(index,orientation,rotation):
                    allowed=False
                else:
                    changed[index]=(orientation+(-1 if rotation == 1 else 1))%4
                break
            next_node=(*point,tuple(changed))
            if allowed and cost+1 < costs.get(next_node,float('inf')):
                costs[next_node]=cost+1; previous[next_node]=(node,button)
                distance=abs(point[0]-x)+abs(point[1]-y)
                heapq.heappush(queue,(cost+1+distance,cost+1,next_node))
    raise RuntimeError('No rotating-gate route from '+str(current))


def walk_to(x,y,limit=300):
    for step in range(limit):
        assert d.field_ready(d.state()) and d.state()['map'] == 'FortreeCity_Gym'
        if (d.state()['x'],d.state()['y']) == (x,y):
            print('NATURAL ROTATING GATE ROUTE PASS',d.state())
            return d.state()
        route,pointer,count=plan(x,y)
        for button,expected in route[:4]:
            d.advance(button,48,4)
            if not d.field_ready(d.state()):
                d.settle(50000)
                break  # Trainers can move; read the new object positions.
            actual=tuple(bytes(gdb.selected_inferior().read_memory(pointer,count)))
            if (d.state()['x'],d.state()['y']) != expected[:2]:
                d.advance('NONE',96)
                break  # A facing/step animation may need another pulse.
            assert actual == expected[2], ('Native gate orientation differs',actual,expected)
    raise RuntimeError('Rotating-gate movement deadline: '+str(d.state()))
