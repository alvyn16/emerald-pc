"""Natural Battle Frontier access and challenges, driven only by keyboard input."""
import gdb
import campaign_driver as d


def board(destination):
    """Choose an available ferry destination from its live native menu."""
    d.go(8,11); d.advance('UP',8,1); d.advance('A',24,1)
    for attempt in range(600):
        current=d.state()
        if current['map'] != 'LilycoveCity_Harbor':
            return d.settle(60000)
        button='A'
        if d.value('(int)FuncIsActiveTask((void *)Task_HandleMultichoiceInput)'):
            choices=d.memory('sLilycoveSSTidalSelections',7)
            target=choices.index(destination)
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor == target else 'DOWN' if cursor < target else 'UP'
        d.advance(button,48,1)
    raise RuntimeError('Ferry destination deadline: '+str(d.state()))


def access():
    assert d.state()['map'] == 'Route121_SafariZoneEntrance'
    d.warp_to(14,13,'Route121')
    d.fly_to('LilycoveCity')
    d.go(12,33); d.cross('UP','LilycoveCity_Harbor')
    board(0)
    assert d.state()['map'] == 'SSTidalCorridor'
    assert d.value('(int)FlagGet(0x1d0)') == 1
    print('NATURAL SCOTT FERRY INVITATION PASS',d.state())
    d.go(7,10); d.cross('UP','SSTidalRooms')
    # Cabin two's bed advances the voyage normally, once per rest.
    for rest in range(2):
        d.go(14,12); d.advance('RIGHT',8,1); d.advance('A',24,1); d.settle(60000)
    d.warp_to(13,16,'SSTidalCorridor')
    d.go(1,10); d.advance('DOWN',8,1); d.advance('A',24,1); d.settle(60000)
    assert d.state()['map'] == 'SlateportCity_Harbor'
    d.warp_to(11,14,'SlateportCity')
    d.fly_to('LilycoveCity')
    d.go(12,33); d.cross('UP','LilycoveCity_Harbor')
    board(1)
    assert d.state()['map'] == 'BattleFrontier_OutsideWest'
    print('NATURAL FRONTIER FERRY ARRIVAL PASS',d.state())
    return d.save_checkpoint('r08-frontier-arrival')


def tower_lobby():
    assert d.state()['map'] == 'BattleFrontier_OutsideWest'
    d.warp_to(26,65,'BattleFrontier_ReceptionGate')
    d.warp_to(4,1,'BattleFrontier_OutsideWest')
    d.connect('BattleFrontier_OutsideEast')
    d.go(16,15); d.cross('UP','BattleFrontier_BattleTowerLobby')
    d.go(6,7)
    print('NATURAL TOWER RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r08-tower-reception')


def choose_party(slots):
    """Select legal party members via the native Enter/Confirm actions."""
    desired=[slot+1 for slot in slots]
    for step in range(300):
        if d.state()['callback'] != 'CB2_UpdatePartyMenu':
            assert list(d.memory('gSelectedOrderFromParty',len(slots))) == desired
            return
        selected=list(d.memory('gSelectedOrderFromParty',len(slots)))
        button='A'
        if d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
            if selected == desired:
                if d.memory('gPartyMenu',10)[9] < 6:button='START'
            else:
                count=next(i for i,n in enumerate(selected) if not n)
                d.select_party_slot(slots[count])
        d.advance(button,24,1)
    raise RuntimeError('Frontier party selection deadline')


def tower_enter():
    assert d.state()['map'] == 'BattleFrontier_BattleTowerLobby'
    d.go(6,7); d.advance('UP',8,1); d.advance('A',24,1)
    for step in range(1000):
        current=d.state()
        if current['callback'] == 'CB2_UpdatePartyMenu':
            choose_party([4,1,2])
            print('NATURAL TOWER PARTY SELECTED PASS',list(d.memory('gSelectedOrderFromParty',3)))
            continue
        if current['callback'] == 'BattleMainCB2':
            print('NATURAL TOWER FIRST BATTLE START PASS',current)
            return
        button='A'
        task=d.value('(unsigned char)FindTaskIdByFunc((void *)Task_HandleMultichoiceInput)')
        if task != 255:
            menu=int.from_bytes(d.memory('gTasks',640)[task*40+22:task*40+24],'little')
            target=1 if menu == 24 else 0
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor == target else 'DOWN' if cursor < target else 'UP'
        d.advance(button,48,1)
    raise RuntimeError('Tower admission deadline: '+str(d.state()))
