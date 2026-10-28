"""Natural Battle Pike access driven through the game's controls."""
import campaign_driver as d


def lobby():
    assert d.state()['map']=='BattleFrontier_BattleTowerLobby'
    d.warp_to(12,9,'BattleFrontier_OutsideEast')
    d.connect('BattleFrontier_OutsideWest')
    d.go(42,27); d.cross('UP','BattleFrontier_BattlePikeLobby')
    d.go(5,6)
    print('NATURAL PIKE RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r13-pike-reception')


def enter():
    import frontier_driver as frontier
    ready=lambda current:current['map']=='BattleFrontier_BattlePikeThreePathRoom' and d.field_ready(current)
    result=frontier.owned_enter('BattleFrontier_BattlePikeLobby',5,6,stop_when=ready)
    assert ready(result),result
    print('NATURAL PIKE ENTRY PASS',result,frontier.records())


def round_trip():
    import json
    import frontier_driver as frontier
    before=frontier.records(); enter(); visits=[]; statuses=[]
    d.RUN_WILD=True  # Use the ordinary Run command in wild Pike rooms.
    for step in range(60):
        current=d.settle(90000)
        room=current['map']
        if room=='BattleFrontier_BattlePikeLobby':break
        count=frontier.records()['curChallengeBattleNum']
        visits.append((room,count))
        party_status=[d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),55,0)')
                      for i in range(current['party'])]
        statuses.append((count,party_status))
        print('NATURAL PIKE ROOM',room,count,current,'status',party_status,flush=True)
        if room=='BattleFrontier_BattlePikeThreePathRoom':
            d.go(2,3,dialogue_limit=90000)
        elif room=='BattleFrontier_BattlePikeRoomNormal':
            # Entering y=6 triggers status encounters that move blocking NPCs.
            for x in (4,3,5):
                try:d.path_to(x,6)
                except RuntimeError:continue
                d.go(x,6,dialogue_limit=90000);break
            else:raise RuntimeError('No reachable Pike entry trigger')
            if d.state()['map']==room:d.go(4,3,dialogue_limit=90000)
        elif room=='BattleFrontier_BattlePikeRoomWildMons':
            d.go(4,3,dialogue_limit=90000)
        else:
            raise RuntimeError('Unexpected Pike room '+str(current))
    else:raise RuntimeError('Pike circuit deadline')
    after=frontier.records()
    print('NATURAL PIKE ROUND RESULT',visits,before,after,flush=True)
    if set(range(1,15)).issubset({count for _,count in visits}) and after['battlePoints']>before['battlePoints']:
        assert after['battlePoints']>before['battlePoints']
        name='r13-pike-complete'
    else:name='r13-pike-loss'
    facts=d.save_checkpoint(name);facts['frontier']=frontier.records();facts['pike_visits']=visits;facts['pike_statuses']=statuses
    (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
