"""Natural Battle Dome entry, tournament bracket and team selection."""
import campaign_driver as d


def lobby():
    assert d.state()['map']=='BattleFrontier_BattleTowerLobby'
    d.warp_to(12,9,'BattleFrontier_OutsideEast')
    d.connect('BattleFrontier_OutsideWest')
    d.go(19,18);d.cross('UP','BattleFrontier_BattleDomeLobby')
    d.go(5,12)
    print('NATURAL DOME RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r12-dome-reception')


def registration():
    import frontier_driver as frontier
    ready=lambda current:current['map']=='BattleFrontier_BattleDomePreBattleRoom' and frontier.multichoice() in (73,107)
    result=frontier.owned_enter('BattleFrontier_BattleDomeLobby',5,11,stop_when=ready)
    assert ready(result),result
    assert d.state()['party']==3
    assert frontier.records()['selectedPartyMons'][:3]==[5,2,3]
    print('NATURAL DOME LEGAL REGISTRATION PASS',result,frontier.records())


def bracket():
    import frontier_driver as frontier
    registration()
    for step in range(300):
        current=d.state()
        if current['callback']=='CB2_TourneyTree':
            if d.value('(int)FuncIsActiveTask((void *)Task_HandleTourneyTreeInput)'):break
            button='NONE'
        elif frontier.multichoice() in (73,107):
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor==1 else 'DOWN' if cursor<1 else 'UP'
        else:button='A'
        d.advance(button,48,1)
    else:raise RuntimeError('Dome tournament bracket deadline')
    d.advance('NONE',120,1)
    (d.SCRATCH/'r12-dome-bracket.raw').write_bytes(d.memory('sPixels',153600))
    print('NATURAL DOME TOURNAMENT BRACKET PASS',d.state())
    d.advance('B',240,1)
    for step in range(200):
        if frontier.multichoice() in (73,107):
            print('NATURAL DOME BRACKET RETURN PASS',d.state())
            return
        d.advance('A',48,1)
    raise RuntimeError('Dome bracket return deadline')


def next_battle():
    import frontier_driver as frontier
    for step in range(1000):
        current=d.state()
        if current['callback']=='BattleMainCB2':
            assert current['party']==2,current
            print('NATURAL DOME TWO MONS BATTLE PASS',current)
            return current
        if d.field_ready(current) and current['map']=='BattleFrontier_BattleDomeLobby':return current
        if current['callback']=='CB2_UpdatePartyMenu':
            frontier.choose_party([0,1]);continue
        if current['callback']=='CB2_TourneyTree':button='B'
        elif frontier.multichoice() in (73,107):
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor==2 else 'DOWN' if cursor<2 else 'UP'
        else:button='A'
        d.advance(button,48,1)
    raise RuntimeError('Dome next battle deadline')


def first_battle():
    bracket()
    result=next_battle()
    assert result['callback']=='BattleMainCB2'


def round_trip():
    import gdb, json
    import frontier_driver as frontier
    before=frontier.records(); outcomes=[]
    class End(gdb.Breakpoint):
        def stop(self):
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            print('NATURAL DOME BATTLE END',len(outcomes),outcomes[-1],frontier.records())
            return False
    observer=End('HandleSpecialTrainerBattleEnd',internal=True);observer.silent=True
    try:
        bracket()
        for _ in range(5):
            current=next_battle()
            if current['map']=='BattleFrontier_BattleDomeLobby' and d.field_ready(current):break
            def pause(current):
                return (current['callback'] in ('CB2_TourneyTree','CB2_UpdatePartyMenu')
                        or frontier.multichoice() in (73,107))
            d.settle(180000,stop_when=pause)
        else:raise RuntimeError('Dome tournament deadline')
        after=frontier.records()
        print('NATURAL DOME ROUND RESULT',outcomes,before,after)
        if outcomes==[1]*4:
            assert after['domeWinStreaks'][1]==1 and after['domeTotalChampionships'][1]==1
            assert after['battlePoints']>before['battlePoints']
            name='r12-dome-champion'
        else:
            assert outcomes and outcomes[-1]==2,outcomes
            name='r12-dome-loss'
        facts=d.save_checkpoint(name);facts['frontier']=frontier.records()
        (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    finally:observer.delete()
