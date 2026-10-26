"""Natural Battle Arena admission, restrictions and judgment verification."""
import campaign_driver as d


def lobby():
    assert d.state()['map']=='BattleFrontier_BattleTowerLobby'
    d.warp_to(12,9,'BattleFrontier_OutsideEast')
    d.go(39,30); d.cross('UP','BattleFrontier_BattleArenaLobby')
    d.go(7,9)
    print('NATURAL ARENA RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r11-arena-reception')


def restriction():
    import struct,gdb
    import frontier_driver as frontier
    frontier.owned_enter('BattleFrontier_BattleArenaLobby',7,8)
    assert d.value('*(unsigned int *)&gBattleTypeFlags') & (1<<18)
    original=struct.unpack_from('<H',d.memory('gBattlerPartyIndexes',8))[0]
    for step in range(250):
        current=d.state()
        if current['callback']=='CB2_UpdatePartyMenu' and d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):break
        pointer=struct.unpack_from('<I',d.memory('gBattlerControllerFuncs',16))[0]
        name=gdb.execute('info symbol %d'%pointer,to_string=True).split(' in ')[0]
        button=d.cursor_button(d.memory('gActionSelectionCursor',4)[0],2) if name=='HandleInputChooseAction' else 'A'
        d.advance(button,48,1)
    else:raise RuntimeError('Arena party-menu deadline')
    assert d.memory('gPartyMenu',12)[11]==2, 'Arena did not request CANT_SWITCH'
    d.select_party_slot(1);d.advance('A',120,1)
    assert d.value('(int)FuncIsActiveTask((void *)Task_HandleSelectionMenuInput)')
    # This native menu must contain Summary/Cancel, so its second entry
    # returns to the party; a Shift/Summary/Cancel menu would open Summary.
    assert d.value('(int)Menu_GetCursorPos()')==0
    d.advance('DOWN',24,1);d.advance('A',120,1)
    assert d.state()['callback']=='CB2_UpdatePartyMenu'
    assert d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)')
    assert struct.unpack_from('<H',d.memory('gBattlerPartyIndexes',8))[0]==original
    d.advance('B',300,1)
    assert d.state()['callback']=='BattleMainCB2'
    assert struct.unpack_from('<H',d.memory('gBattlerPartyIndexes',8))[0]==original
    (d.SCRATCH/'r11-arena-restriction.raw').write_bytes(d.memory('sPixels',153600))
    print('NATURAL ARENA SWITCH RESTRICTION PASS',d.state(),original)
