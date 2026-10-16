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
