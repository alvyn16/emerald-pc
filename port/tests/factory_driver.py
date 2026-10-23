"""Natural Battle Factory routes, rental selection and exchange through UI."""
import campaign_driver as d


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
        d.advance('A',48,1)  # Challenge, Lv50, Yes/save, then native rental screen.
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
        fields={key:d.value(f'(int)GetMonData3((void *){address},{field},0)') for key,field in
                (('species',11),('level',56),('hp',58),('attack',59),('defense',60),('speed',61),('spattack',62),('spdefense',63))}
        assert fields['species'] > 0 and fields['level'] == 50, fields
        fields['index']=index
        fields['score']=fields['hp']+max(fields['attack'],fields['spattack'])*1.5+fields['speed']+(fields['defense']+fields['spdefense'])*0.5
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
    print('NATURAL FACTORY FIRST BATTLE PASS',result)
