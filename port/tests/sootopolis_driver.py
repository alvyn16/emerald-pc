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
