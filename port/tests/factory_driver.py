"""Natural Battle Factory routes, rental selection and exchange through UI."""
import campaign_driver as d
import gdb

PAUSE_AFTER=0  # Optional real Rest/save checkpoint between wins.
LEVEL_MODE=0  # Real reception choice: Lv50=0, Open Level=1.


def lobby():
    assert d.state()['map'] == 'BattleFrontier_OutsideWest'
    d.warp_to(26,65,'BattleFrontier_ReceptionGate')
    d.warp_to(4,1,'BattleFrontier_OutsideWest')
    d.go(11,39); d.cross('UP','BattleFrontier_BattleFactoryLobby')
    d.go(4,9)
    print('NATURAL FACTORY RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r09-factory-reception')


def enter():
    assert d.state()['map'] == 'BattleFrontier_BattleFactoryLobby'
    d.go(4,8); d.advance('UP',24,4); d.advance('A',24,1)
    for step in range(600):
        current=d.state()
        if current['callback'] == 'CB2_SelectScreen':
            print('NATURAL FACTORY RENTAL SCREEN PASS',current)
            return
        import frontier_driver
        target=LEVEL_MODE if frontier_driver.multichoice()==24 else 0
        if frontier_driver.multichoice() is None:button='A'
        else:
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor==target else 'DOWN' if cursor<target else 'UP'
        d.advance(button,48,1)
    raise RuntimeError('Factory admission deadline: '+str(d.state()))


def rent():
    import gdb
    import json
    layout=json.loads((d.ROOT/'build/factory-layout.json').read_text())
    pointer=d.value('*(unsigned int *)&sFactorySelectScreen')
    assert pointer and d.state()['callback'] == 'CB2_SelectScreen'
    def read(offset,size=1):
        return bytes(gdb.selected_inferior().read_memory(pointer+offset,size))
    mons=[]
    for index in range(6):
        address=pointer+layout['FactorySelectScreen_mons']+index*layout['FactorySelectableMon_size']+layout['FactorySelectableMon_monData']
        fields=mon_stats(address)
        assert fields['species'] > 0 and fields['level'] == (100 if LEVEL_MODE else 50), fields
        fields['index']=index
        mons.append(fields)
    desired=[mon['index'] for mon in sorted(mons,key=lambda mon:mon['score'],reverse=True)[:3]]
    print('NATURAL FACTORY RENTAL CANDIDATES',mons,'chosen',desired)
    for step in range(500):
        if d.state()['callback'] != 'CB2_SelectScreen':
            actual=[d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),11,0)') for i in range(3)]
            assert actual == [mons[i]['species'] for i in desired], actual
            print('NATURAL FACTORY RENTED THREE PASS',actual)
            return
        button='NONE'
        if d.value('(int)FuncIsActiveTask((void *)Select_Task_HandleChooseMons)'):
            selected=[read(layout['FactorySelectScreen_mons']+i*layout['FactorySelectableMon_size']+layout['FactorySelectableMon_selectedId'])[0] for i in range(6)]
            count=sum(bool(n) for n in selected)
            assert count < 3, selected
            cursor=read(layout['FactorySelectScreen_cursorPos'])[0]; target=desired[count]
            button='A' if cursor == target else 'RIGHT' if cursor < target else 'LEFT'
        elif d.value('(int)FuncIsActiveTask((void *)Select_Task_HandleMenu)'):
            cursor=read(layout['FactorySelectScreen_menuCursorPos'])[0]
            button='A' if cursor == 1 else 'DOWN' if cursor < 1 else 'UP'
        elif d.value('(int)FuncIsActiveTask((void *)Select_Task_HandleYesNo)'):
            button='A' if read(layout['FactorySelectScreen_yesNoCursorPos'])[0] == 0 else 'UP'
        d.advance(button,24,1)
    raise RuntimeError('Factory rental selection deadline')


def first_battle():
    enter(); rent()
    result=d.settle(60000,stop_when=lambda current:current['callback'] == 'BattleMainCB2')
    import json
    rosters={name:[mon_stats(d.value('(unsigned int)&'+symbol)+i*100) for i in range(3)]
             for name,symbol in (('player','gPlayerParty'),('opponent','gEnemyParty'))}
    (d.SCRATCH/'factory-rosters.json').write_text(json.dumps(rosters,indent=2))
    print('NATURAL FACTORY FIRST BATTLE PASS',result)


def mon_stats(address):
    fields={key:d.value(f'(unsigned int)GetMonData3((void *){address},{field},0)') for key,field in
            (('species',11),('personality',0),('level',56),('hp',58),('attack',59),('defense',60),('speed',61),('spattack',62),('spdefense',63))}
    fields['moves']=[d.value(f'(int)GetMonData3((void *){address},{13+i},0)') for i in range(4)]
    normal_attack=any(move and bytes(gdb.selected_inferior().read_memory(d.value('(unsigned int)&gBattleMoves')+move*9,2))[1]>1 for move in fields['moves'])
    fields['score']=fields['hp']+max(fields['attack'],fields['spattack'])*1.5+fields['speed']+(fields['defense']+fields['spdefense'])*0.5 if normal_attack else -10000
    return fields


def exchange():
    import gdb,json
    layout=json.loads((d.ROOT/'build/factory-layout.json').read_text())
    pointer=d.value('*(unsigned int *)&sFactorySwapScreen')
    def byte(field):
        return bytes(gdb.selected_inferior().read_memory(pointer+layout['FactorySwapScreen_'+field],1))[0]
    players=[mon_stats(d.value('(unsigned int)&gPlayerParty')+i*100) for i in range(3)]
    enemies=[mon_stats(d.value('(unsigned int)&gEnemyParty')+i*100) for i in range(3)]
    remove=min(range(3),key=lambda i:players[i]['score'])
    allowed=[i for i in range(3) if enemies[i]['species'] not in {players[j]['species'] for j in range(3) if j!=remove}]
    assert allowed, 'No legal exchange'
    receive=max(allowed,key=lambda i:enemies[i]['score'])
    print('NATURAL FACTORY EXCHANGE CHOICE',remove,players[remove],receive,enemies[receive])
    for step in range(600):
        if d.state()['callback'] != 'Swap_CB2':
            actual=mon_stats(d.value('(unsigned int)&gPlayerParty')+remove*100)
            for key in ('species','personality','level','moves'):
                assert actual[key] == enemies[receive][key], (key,actual,enemies[receive])
            print('NATURAL FACTORY EXCHANGE PASS',actual)
            return
        button='NONE'
        if d.value('(int)FuncIsActiveTask((void *)Swap_Task_HandleChooseMons)'):
            target=receive if byte('inEnemyScreen') else remove
            cursor=byte('cursorPos')
            button='UP' if cursor>2 else 'A' if cursor==target else 'RIGHT' if cursor<target else 'LEFT'
        elif d.value('(int)FuncIsActiveTask((void *)Swap_Task_HandleMenu)'):
            cursor=byte('menuCursorPos');button='A' if cursor==1 else 'DOWN' if cursor<1 else 'UP'
        elif d.value('(int)FuncIsActiveTask((void *)Swap_Task_HandleYesNo)'):
            button='A' if byte('yesNoCursorPos')==0 else 'UP'
        d.advance(button,24,1)
    raise RuntimeError('Factory exchange deadline')


def first_exchange():
    first_battle()
    result=d.settle(100000,stop_when=lambda current:current['callback']=='Swap_CB2')
    assert result['callback']=='Swap_CB2', result
    exchange()
    result=d.settle(60000,stop_when=lambda current:current['callback']=='BattleMainCB2')
    import frontier_driver
    assert frontier_driver.records()['factoryRentsCount'][0] == 1
    print('NATURAL FACTORY SECOND BATTLE AFTER EXCHANGE PASS',result)


def round_trip(resume=False):
    import json
    import frontier_driver as frontier
    before=frontier.records(); outcomes=[]; swaps=0
    class End(gdb.Breakpoint):
        def stop(self):
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            import struct
            mons=d.memory('gBattleMons',352)
            last=[dict(species=struct.unpack_from('<H',mons,i*88)[0],
                       hp=struct.unpack_from('<H',mons,i*88+40)[0],
                       moves=list(struct.unpack_from('<4H',mons,i*88+12)),
                       pp=list(mons[i*88+36:i*88+40])) for i in (0,1)]
            with (d.SCRATCH/'factory-results.jsonl').open('a') as log:
                log.write(json.dumps(dict(frame=d.value('sDiagnosticFrame'),outcome=outcomes[-1],last=last))+chr(10))
            print('NATURAL FACTORY BATTLE END',len(outcomes),outcomes[-1],frontier.records())
            return False
    observer=End('HandleSpecialTrainerBattleEnd',internal=True); observer.silent=True
    try:
        if resume:
            expected=json.loads((d.ROOT/'build/natural-campaign/r09-factory-open-paused-four.json').read_text())
            for key in ('factoryWinStreaks','factoryRentsCount','curChallengeBattleNum','battlesCount'):
                assert before[key]==expected[key],(key,before,expected)
            current=d.settle(60000,stop_when=lambda state:state['callback']=='Swap_CB2')
            assert current['callback']=='Swap_CB2',current
            expected_team=json.loads((d.ROOT/'build/natural-campaign/r09-factory-open-paused-four-team.json').read_text())
            actual=[mon_stats(d.value('(unsigned int)&gPlayerParty')+i*100) for i in range(3)]
            for old,new in zip(expected_team,actual):
                for key in ('species','personality','level','moves'):assert old[key]==new[key],(key,old,new)
            print('NATURAL FACTORY RESUMED RENTALS PASS',actual)
            swaps=3
            exchange();swaps+=1
        else:
            first_battle()
        for stage in range(8):
            current=d.settle(100000,stop_when=lambda state:state['callback']=='Swap_CB2' or (PAUSE_AFTER and len(outcomes)>=PAUSE_AFTER and frontier.multichoice() in (103,104)))
            if PAUSE_AFTER and len(outcomes)>=PAUSE_AFTER and frontier.multichoice() in (103,104):
                assert outcomes==[1]*PAUSE_AFTER,outcomes
                pause_challenge(PAUSE_AFTER)
                return
            if current['map']=='BattleFrontier_BattleFactoryLobby':break
            assert current['callback']=='Swap_CB2',current
            exchange(); swaps+=1
        else:raise RuntimeError('Factory round did not end after seven battles')
        after=frontier.records()
        print('NATURAL FACTORY ROUND RESULT',outcomes,'exchanges',swaps,before,after)
        if outcomes==[1]*(3 if resume else 7):
            assert swaps==6 and after['factoryRentsCount'][LEVEL_MODE]>=6
            assert after['factoryWinStreaks'][LEVEL_MODE]==7
            assert after['battlePoints']>before['battlePoints']
            name='r09-factory-open-seven-wins' if LEVEL_MODE else 'r09-factory-seven-wins'
        else:
            assert outcomes and outcomes[-1]==2,outcomes
            name='r09-factory-open-loss' if LEVEL_MODE else 'r09-factory-loss'
        facts=d.save_checkpoint(name); facts['frontier']=frontier.records()
        (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    finally:
        observer.delete()


def pause_challenge(wins):
    import json
    import frontier_driver as frontier
    for step in range(400):
        menu=frontier.multichoice();button='A'
        if menu in (103,104):
            target=2 if menu==103 else 1
            cursor=d.value('(int)Menu_GetCursorPos()')
            button='A' if cursor==target else 'DOWN' if cursor<target else 'UP'
        try:
            d.advance(button,48,1)
        except AssertionError:
            assert gdb.newest_frame().name()=='Port_ExitCleanly'
            assert gdb.newest_frame().older().name()=='SoftReset'
            result=frontier.records()
            assert result['challengeStatus']==2,result
            assert result['factoryWinStreaks'][LEVEL_MODE]==wins,result
            name='r09-factory-open-paused-four'
            (d.SCRATCH/(name+'.sav')).write_bytes((d.SCRATCH/'saves/emerald-pc-diagnostic.sav').read_bytes())
            (d.SCRATCH/(name+'.json')).write_text(json.dumps(result,indent=2))
            (d.SCRATCH/(name+'.raw')).write_bytes(d.memory('sPixels',153600))
            print('NATURAL FACTORY REAL PAUSED CHECKPOINT PASS',result)
            return
    raise RuntimeError('Factory native suspension deadline')
