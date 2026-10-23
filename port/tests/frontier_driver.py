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
    d.go(6,6); d.advance('UP',24,4); d.advance('A',24,1)
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


def records():
    """Read measured i686 save offsets; never use stale GBA layout comments."""
    import json
    import struct
    layout=json.loads((d.ROOT/'build/frontier-layout.json').read_text())
    address=d.value('*(unsigned int *)&gSaveBlock2Ptr')
    data=bytes(gdb.selected_inferior().read_memory(address,layout['SaveBlock2_size']))
    sizes={'towerWinStreaks':8,'towerRecordWinStreaks':8,'domeWinStreaks':4,
           'domeTotalChampionships':4,'palaceWinStreaks':4,'arenaWinStreaks':2,
           'factoryWinStreaks':4,'factoryRentsCount':4,'pikeWinStreaks':2,
           'pyramidWinStreaks':2,'selectedPartyMons':4}
    result={name:list(struct.unpack_from('<'+'H'*count,data,layout[name])) for name,count in sizes.items()}
    for name in ('battlePoints','curChallengeBattleNum'):
        result[name]=struct.unpack_from('<H',data,layout[name])[0]
    result['battlesCount']=struct.unpack_from('<I',data,layout['battlesCount'])[0]
    result['challengeStatus']=data[layout['challengeStatus']]
    return result


def tower_round():
    before=records(); outcomes=[]
    class End(gdb.Breakpoint):
        def stop(self):
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            print('NATURAL TOWER BATTLE END',len(outcomes),outcomes[-1],records(),flush=True)
            return False
    observer=End('HandleSpecialTrainerBattleEnd',internal=True); observer.silent=True
    try:
        tower_enter()
        d.settle(250000)
        assert d.state()['map'] == 'BattleFrontier_BattleTowerLobby'
        after=records()
        print('NATURAL TOWER ROUND RESULT',outcomes,before,after,flush=True)
        if outcomes == [1]*7:
            assert after['towerWinStreaks'][1] == 7
            assert after['towerRecordWinStreaks'][1] >= 7
            assert after['battlePoints'] > before['battlePoints']
            name='r08-tower-seven-wins'
        else:
            assert outcomes and outcomes[-1] == 2, outcomes
            name='r08-tower-loss'
        facts=d.save_checkpoint(name)
        facts['frontier']=records()
        import json
        (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
        print('NATURAL TOWER RESULT SAVED PASS',name)
    finally:
        observer.delete()


def multichoice():
    task=d.value('(unsigned char)FindTaskIdByFunc((void *)Task_HandleMultichoiceInput)')
    if task == 255:return None
    return int.from_bytes(d.memory('gTasks',640)[task*40+22:task*40+24],'little')


def tower_pause():
    import json
    before=records()
    tower_enter()
    d.settle(100000,stop_when=lambda current:multichoice() in (103,104))
    assert records()['towerWinStreaks'][1] == before['towerWinStreaks'][1]+1
    for step in range(500):
        menu=multichoice(); button='A'
        if menu in (103,104):
            target=2 if menu == 103 else 1
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor == target else 'DOWN' if cursor < target else 'UP'
        try:
            d.advance(button,48,1)
        except AssertionError:
            # Diagnostic SoftReset intentionally exits before the next frame target.
            # Accept only this exact native path after its real paused save.
            assert gdb.newest_frame().name() == 'Port_ExitCleanly'
            assert gdb.newest_frame().older().name() == 'SoftReset'
            result=records(); assert result['challengeStatus'] == 2, result
            assert result['towerWinStreaks'][1] == before['towerWinStreaks'][1]+1
            source=d.SCRATCH/'saves/emerald-pc-diagnostic.sav'
            (d.SCRATCH/'r08-tower-paused.sav').write_bytes(source.read_bytes())
            (d.SCRATCH/'r08-tower-paused.json').write_text(json.dumps(result,indent=2))
            (d.SCRATCH/'r08-tower-paused.raw').write_bytes(d.memory('sPixels',153600))
            print('NATURAL TOWER PAUSED SAVE AND SOFT RESET PASS',result)
            return
    raise RuntimeError('Tower suspension deadline')


def tower_resume():
    import json
    expected=json.loads((d.ROOT/'build/natural-campaign/r08-tower-paused.json').read_text())
    initial=records()
    for key in ('towerWinStreaks','selectedPartyMons','curChallengeBattleNum','battlesCount'):
        assert initial[key] == expected[key], (key,initial,expected)
    assert initial['challengeStatus'] in (1,2), initial
    result=d.settle(60000,stop_when=lambda current:current['callback'] == 'BattleMainCB2')
    assert result['map'] == 'BattleFrontier_BattleTowerBattleRoom'
    assert result['party'] == 3
    resumed=records()
    for key in ('towerWinStreaks','selectedPartyMons','curChallengeBattleNum','battlesCount'):
        assert resumed[key] == expected[key], (key,resumed,expected)
    assert resumed['challengeStatus'] == 1
    assert [d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),11,0)') for i in range(3)] == [285,310,385]
    (d.SCRATCH/'r08-tower-resumed.raw').write_bytes(d.memory('sPixels',153600))
    (d.SCRATCH/'r08-tower-resumed.json').write_text(json.dumps(resumed,indent=2))
    print('NATURAL TOWER CONTINUE RESUMED SECOND BATTLE PASS',resumed,result)
