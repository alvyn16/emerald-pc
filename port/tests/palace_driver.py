"""Natural Battle Palace admission and automatic battles through keyboard UI."""
import campaign_driver as d


def lobby():
    assert d.state()['map']=='BattleFrontier_BattleTowerLobby'
    d.warp_to(12,9,'BattleFrontier_OutsideEast')
    d.go(45,57); d.cross('UP','BattleFrontier_BattlePalaceLobby')
    d.go(5,8)
    print('NATURAL PALACE RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r10-palace-reception')


def first_battle():
    import frontier_driver as frontier
    frontier.owned_enter('BattleFrontier_BattlePalaceLobby',5,7)
    print('NATURAL PALACE FIRST BATTLE PASS',d.state())


def round_trip():
    import gdb,json
    import frontier_driver as frontier
    before=frontier.records(); outcomes=[]; automatic=[]; manual=[]
    class AutoMove(gdb.Breakpoint):
        def stop(self):
            automatic.append(d.value('sDiagnosticFrame'))
            return False
    class ManualMove(gdb.Breakpoint):
        def stop(self):
            if d.value('*(unsigned int *)&gBattleTypeFlags') & (1<<17):manual.append(d.value('sDiagnosticFrame'))
            return False
    class End(gdb.Breakpoint):
        def stop(self):
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            print('NATURAL PALACE BATTLE END',len(outcomes),outcomes[-1],frontier.records())
            return False
    observers=[AutoMove('PlayerChooseMoveInBattlePalace',internal=True),
               ManualMove('HandleInputChooseMove',internal=True),
               End('HandleSpecialTrainerBattleEnd',internal=True)]
    for observer in observers:observer.silent=True
    try:
        first_battle(); d.settle(300000)
        assert d.state()['map']=='BattleFrontier_BattlePalaceLobby'
        after=frontier.records()
        assert automatic and not manual, (len(automatic),manual)
        print('NATURAL PALACE ROUND RESULT',outcomes,'automatic callbacks',len(automatic),'manual moves',manual,before,after)
        if outcomes==[1]*7:
            assert after['palaceWinStreaks'][1]==7
            assert after['battlePoints']>before['battlePoints']
            name='r10-palace-seven-wins'
        else:
            assert outcomes and outcomes[-1]==2, outcomes
            name='r10-palace-loss'
        facts=d.save_checkpoint(name);facts['frontier']=frontier.records()
        (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    finally:
        for observer in observers:observer.delete()
