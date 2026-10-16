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
