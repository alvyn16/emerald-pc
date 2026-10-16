"""Reach Sootopolis through the real Dive path and observe camera cleanup."""
import gdb
import campaign_driver as d


def arrive():
    assert d.state()['map'] == 'Route126'
    assert d.value('(int)FlagGet(0x81)') == 1
    assert d.value('(int)VarGet(0x405e)') == 1
    d.RUN_WILD=True
    d.go(45,66); d.choose_field_move(0,6); d.settle(30000)
    assert d.state()['map'] == 'Underwater_Route126'
    assert (d.state()['x'],d.state()['y']) == (45,66)
    d.cross('UP','Underwater_SootopolisCity')

    class CameraObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            return False

    observer=CameraObservation('SpawnCameraObject',internal=True)
    observer.calls=0; observer.silent=True
    try:
        d.choose_field_move(0,6); d.settle(100000)
        assert d.field_ready(d.state()) and d.state()['map'] == 'SootopolisCity'
        assert (d.state()['x'],d.state()['y']) == (29,53)
        assert d.value('(int)VarGet(0x405e)') == 2
        assert observer.calls > 0, 'The original camera scene must execute'
        objects=d.memory('gObjectEvents',16*36)
        assert not any(objects[i*36]&1 and objects[i*36+8] == 127 for i in range(16))
        print('NATURAL CAMERA LIFECYCLE PASS',observer.calls,d.state())
        return d.save_checkpoint('r04-sootopolis-arrival')
    finally:
        observer.delete()


def wallace():
    """Follow Steven, then choose Sky Pillar through Wallace's actual menu."""
    assert d.state()['map'] == 'SootopolisCity'
    assert d.value('(int)VarGet(0x405e)') == 2
    assert d.value('(int)FlagGet(0x137)') == 0
    d.RUN_WILD=True
    d.talk(20,37,'UP',60000)
    assert d.state()['map'] == 'CaveOfOrigin_Entrance'
    assert d.value('(int)FlagGet(0x133)') == 1
    d.warp_to(9,5,'CaveOfOrigin_1F')
    d.warp_to(14,5,'CaveOfOrigin_B1F')
    # The tile north of Wallace is a wall: approach from his west.
    d.go(8,13); d.advance('RIGHT',24,4); d.advance('A',24,1)
    for _ in range(150):
        if d.value('(int)FuncIsActiveTask((void *)Task_HandleMultichoiceInput)'):
            break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Wallace choice deadline: '+str(d.state()))
    for _ in range(5):
        cursor=d.value('(int)Menu_GetCursorPos()')
        if cursor == 2:
            break
        d.advance('DOWN' if cursor < 2 else 'UP',24,1)
    assert d.value('(int)Menu_GetCursorPos()') == 2
    d.advance('A',24,1); d.settle(20000)
    assert d.value('(int)FlagGet(0x137)') == 1
    assert d.value('(int)VarGet(0x405e)') == 3
    print('NATURAL WALLACE SKY PILLAR PASS',d.state())
    return d.save_checkpoint('r04-wallace-sky-pillar')


def pillar_open():
    """Enter from Route131 and let Wallace open the tower by script."""
    assert d.state()['map'] == 'Route131'
    assert d.value('(int)VarGet(0x405e)') == 3
    assert d.value('(int)FlagGet(0x137)') == 1
    d.RUN_WILD=True
    d.go(36,7); d.cross('UP','SkyPillar_Entrance')
    d.warp_to(14,4,'SkyPillar_Outside',100000)
    d.settle(100000)
    assert d.value('(int)VarGet(0x405e)') == 4
    assert d.field_ready(d.state())
    print('NATURAL SKY PILLAR OPEN',d.state())
    return d.save_checkpoint('r04-sky-pillar-open')


def pillar_climb():
    """Climb the early-story layouts, including the intended cracked-floor fall."""
    assert d.state()['map'] == 'SkyPillar_Outside'
    assert d.value('(int)VarGet(0x405e)') == 4
    assert d.value('(int)VarGet(0x40ca)') == 0
    d.RUN_WILD=True
    d.go(14,6); d.cross('UP','SkyPillar_1F')
    for x,y,target in ((10,1,'SkyPillar_2F'),(3,1,'SkyPillar_3F'),
                       (11,1,'SkyPillar_4F')):
        d.warp_to(x,y,target,80000)
    # The western stairs are isolated. Walking onto the cracked tiles drops
    # through the actual hole into 3F's central compartment.
    d.go(7,4); d.settle(30000)
    assert d.state()['map'] == 'SkyPillar_3F'
    assert (d.state()['x'],d.state()['y']) == (6,4)
    for x,y,target in ((7,1,'SkyPillar_4F'),(3,1,'SkyPillar_5F'),
                       (10,1,'SkyPillar_Top')):
        d.warp_to(x,y,target,80000)
    d.go(14,10)
    print('NATURAL SKY PILLAR CLIMB PASS',d.state())
    return d.save_checkpoint('r04-rayquaza-ready')


def awaken():
    assert d.state()['map'] == 'SkyPillar_Top'
    assert d.value('(int)VarGet(0x405e)') == 4
    assert d.value('(int)VarGet(0x40ca)') == 0
    d.go(14,9,dialogue_limit=100000); d.settle(100000)
    assert d.value('(int)VarGet(0x405e)') == 5
    assert d.value('(int)VarGet(0x40ca)') == 1
    assert d.field_ready(d.state())
    objects=d.memory('gObjectEvents',16*36)
    assert not any(objects[i*36]&1 and objects[i*36+8] == 127 for i in range(16))
    print('NATURAL RAYQUAZA AWAKENED',d.state())
    return d.save_checkpoint('r04-rayquaza-awakened')


def peace():
    """Fly back legally; observe all five loaders and capture their rendered frames."""
    assert d.state()['map'] == 'SkyPillar_Top'
    assert d.value('(int)VarGet(0x405e)') == 5
    assert d.value('(int)VarGet(0x40ca)') == 1
    loads=[]
    captured=set()

    class SceneObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            loads.append((self.label,d.value('sDiagnosticFrame')))
            return False

    advance=d.advance
    def capture_advance(*args,**kwargs):
        current=advance(*args,**kwargs)
        if loads and current['callback'] == 'CB2_RayquazaScene':
            label,loaded=loads[-1]
            if label not in captured and current['frame'] >= loaded+100:
                path=(d.SCRATCH/('rayquaza-scene-'+label+'.raw')).as_posix()
                gdb.execute(f'dump binary memory {path} &sPixels ((char *)&sPixels)+153600')
                captured.add(label)
        return current

    observers=[]
    try:
        for label in ('LoadDuoFightSceneGfx','LoadTakesFlightSceneGfx',
                      'LoadDescendsSceneGfx','LoadChargesSceneGfx','LoadChasesAwaySceneGfx'):
            observer=SceneObservation(label,internal=True)
            observer.label=label; observer.calls=0; observer.silent=True
            observers.append(observer)
        d.advance=capture_advance
        d.fly_to('SootopolisCity'); d.settle(100000)
        assert all(observer.calls == 1 for observer in observers), loads
        assert len(captured) == 5, captured
        assert d.value('(int)VarGet(0x40ca)') == 3
        assert d.value('(int)FlagGet(0x53)') == 0
        assert d.field_ready(d.state())
        objects=d.memory('gObjectEvents',16*36)
        assert not any(objects[i*36]&1 and objects[i*36+8] == 127 for i in range(16))
        print('NATURAL RAYQUAZA PEACE PASS',loads,d.state())
        return d.save_checkpoint('r04-sootopolis-peace')
    finally:
        d.advance=advance
        for observer in observers:
            observer.delete()
