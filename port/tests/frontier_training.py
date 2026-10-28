"""Prepare natural Battle Frontier training through the ordinary field UI."""
import campaign_driver as d


def prepare():
    import pyramid_driver
    assert d.state()['map']=='BattleFrontier_BattlePalaceLobby'
    assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+200),56,0)')==25
    pyramid_driver.take_held(1)
    pyramid_driver.take_held(2)
    d.give_item(182,2)
    d.go(12,10);d.cross('DOWN','BattleFrontier_OutsideEast')
    d.fly_to('EverGrandeCity',1)
    current=d.state()
    if current['y']<35:
        d.go(18,28);d.cross('UP','VictoryRoad_1F')
    else:
        d.go(18,42);d.cross('UP','VictoryRoad_1F')
    print('NATURAL FRONTIER TRAINING CAVE PASS',d.state(),flush=True)
    return d.save_checkpoint('r10-training-cave')


def train(target=30,checkpoint="r10-castform-trained"):
    mon='(void *)((char *)&gPlayerParty+200)'
    assert d.state()['map']=='VictoryRoad_1F'
    assert d.value(f'(int)GetMonData3({mon},12,0)')==182
    candidates=[]
    for y in range(3,13):
        for x in range(33,45):
            if (x,y)==(39,5):continue
            try:route=d.path_to(x,y)
            except RuntimeError:continue
            if 2<=len(route)<=12:candidates.append((x,y))
    pair=next(((a,b) for a in candidates for b in candidates
               if abs(a[0]-b[0])+abs(a[1]-b[1])>=3),None)
    assert pair,('No safe cave training route',candidates)
    print('NATURAL TRAINING WALK ROUTE',pair,flush=True)
    saved_level=d.value(f'(int)GetMonData3({mon},56,0)')
    for visit in range(10):
        d.RUN_WILD=False
        for step in range(120):
            d.go(*pair[step%2],dialogue_limit=90000)
            d.settle(90000)
            level=d.value(f'(int)GetMonData3({mon},56,0)')
            pp=sum(d.value(f'(int)GetMonData3((void *)&gPlayerParty,{17+i},0)') for i in range(4))
            hp=d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)')
            print('NATURAL TRAINING PROGRESS',level,hp,pp,step,flush=True)
            if level>=target:
                print('NATURAL CASTFORM TRAINING PASS',level,flush=True)
                return d.save_checkpoint(checkpoint)
            if level>saved_level:
                d.save_checkpoint('r10-training-progress')
                saved_level=level
            if hp<50 or pp<5:break
        d.RUN_WILD=True
        d.warp_to(39,5,'EverGrandeCity',90000)
        d.go(18,6);d.cross('UP','EverGrandeCity_PokemonLeague_1F')
        d.talk(3,4,'UP');d.go(9,10);d.cross('DOWN','EverGrandeCity')
        d.go(18,28);d.cross('UP','VictoryRoad_1F')
    raise RuntimeError('Training visit limit reached')


def return_to_palace():
    assert d.state()['map']=='VictoryRoad_1F'
    d.teach_tm(291,2)  # Owned TM03 Water Pulse.
    d.RUN_WILD=True
    d.warp_to(39,5,'EverGrandeCity',90000)
    d.go(18,6);d.cross('UP','EverGrandeCity_PokemonLeague_1F')
    d.talk(3,4,'UP');d.go(9,10);d.cross('DOWN','EverGrandeCity')
    d.fly_to('BattleFrontier_OutsideEast',1)
    d.go(45,57);d.cross('UP','BattleFrontier_BattlePalaceLobby')
    d.go(5,8)
    print('NATURAL TRAINED PALACE RECEPTION PASS',d.state(),flush=True)
    return d.save_checkpoint('r10-palace-trained-ready')
