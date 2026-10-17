"""Natural R05 preparation and League travel; inputs only, no progress writes."""
import campaign_driver as d


def ball_supplies():
    assert d.state()['map'] == 'DewfordTown' and d.state()['party'] == 4
    assert d.value('(int)FlagGet(0x86e)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(2)') == 0
    d.fly_to('MossdeepCity')
    d.go(37,19); d.cross('UP','MossdeepCity_Mart'); d.buy_item(2,3)
    d.go(3,7); d.cross('DOWN','MossdeepCity')
    d.go(28,17); d.cross('UP','MossdeepCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','MossdeepCity')
    d.fly_to('DewfordTown')
    assert d.value('(int)CountTotalItemQuantityInBag(2)') == 3
    print('NATURAL R05 BALL SUPPLIES PASS',d.state())
    return d.save_checkpoint('r05-tentacool-catch-ready')


def catch_waterfall_user():
    assert d.state()['map'] == 'DewfordTown' and d.state()['party'] == 4
    assert d.value('(int)CountTotalItemQuantityInBag(1)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(2)') == 3
    assert d.value('(int)CountTotalItemQuantityInBag(4)') == 4
    previous=d.RUN_WILD,d.CATCH_SPECIES,d.CATCH_BALL
    try:
        d.RUN_WILD=True; d.CATCH_SPECIES={72}; d.CATCH_BALL=2
        d.talk(13,9,'RIGHT')
        assert d.memory('gPlayerAvatar',1)[0]&8
        for step in range(500):
            d.go(18 if step%2 == 0 else 16,8); d.settle(40000)
            if d.state()['party'] > 4:
                break
        else:
            raise RuntimeError('Tentacool encounter/capture deadline')
        assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+400),11,0)') == 72
        assert d.value('(int)CountTotalItemQuantityInBag(1)') == 1
        assert d.value('(int)CountTotalItemQuantityInBag(4)') == 4
        assert d.value('(int)CountTotalItemQuantityInBag(2)') < 3
        print('NATURAL TENTACOOL CATCH PASS',d.state())
        d.save_checkpoint('r05-tentacool-caught')
    finally:
        d.RUN_WILD,d.CATCH_SPECIES,d.CATCH_BALL=previous
    d.teach_tm(345,4)
    assert 127 in [d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+400),%d,0)'%(13+i))
                   for i in range(4)]
    assert d.value('(int)CountTotalItemQuantityInBag(345)') == 1
    return d.save_checkpoint('r05-waterfall-learned')


def road_trip():
    assert d.state()['map'] == 'DewfordTown' and d.state()['party'] == 5
    assert d.value('(int)FlagGet(0x86e)') == 1
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.teach_tm(343,2)
    assert 148 in [d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+200),%d,0)'%(13+i))
                   for i in range(4)]
    d.save_checkpoint('r05-hm-team-ready')
    d.fly_to('MossdeepCity')
    d.talk(25,30,'DOWN')
    for destination in ('Route127','Route128','EverGrandeCity'):
        d.connect(destination)
    print('NATURAL EVER GRANDE ARRIVAL',d.state())
    return d.save_checkpoint('r05-ever-grande-waterfall-bottom')


def waterfall():
    import gdb
    assert d.state()['map'] == 'EverGrandeCity'
    assert d.value('(int)FlagGet(0x86e)') == 1
    assert 127 in [d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+400),%d,0)'%(13+i))
                   for i in range(4)]
    # Arrive facing north from ordinary water. Stepping into the waterfall
    # before using the move invokes the game's forced southward slide.
    d.go(0,69); d.go(18,69); d.go(18,68)
    assert d.value('(int)IsPlayerSurfingNorth()') == 1
    class WaterfallObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            self.mon=d.value('*(unsigned int *)&gFieldEffectArguments')
            return False
    observer=WaterfallObservation('FldEff_UseWaterfall',internal=True)
    observer.silent=True; observer.calls=0; observer.mon=None
    try:
        d.advance('A',48,8); d.settle(30000)
        assert observer.calls == 1 and observer.mon == 4
        assert (d.state()['x'],d.state()['y']) == (18,59)
        assert d.memory('gPlayerAvatar',1)[0]&8
        assert d.field_ready(d.state())
        print('NATURAL WATERFALL PASS',observer.calls,observer.mon,d.state())
        d.save_checkpoint('r05-waterfall-used')
    finally:
        observer.delete()
    d.go(27,49); d.cross('UP','EverGrandeCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','EverGrandeCity')
    d.save_checkpoint('r05-victory-road-rested')
    d.go(18,42); d.cross('UP','VictoryRoad_1F')
    return d.save_checkpoint('r05-victory-road-entry')


def wally():
    assert d.state()['map'] == 'VictoryRoad_1F'
    assert d.value('(int)FlagGet(0x7e)') == 0
    assert d.value('(int)HasTrainerBeenFought(519)') == 0
    assert d.value('(int)VarGet(0x40c3)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.go(3,23,dialogue_limit=150000); d.settle(150000)
    assert d.value('*(unsigned char *)&gBattleOutcome') == 1
    assert d.state()['map'] == 'VictoryRoad_1F'
    assert d.value('(int)HasTrainerBeenFought(519)') == 1
    assert d.value('(int)FlagGet(0x7e)') == 1
    assert d.value('(int)VarGet(0x40c3)') == 2
    print('NATURAL WALLY VICTORY ROAD PASS',d.state())
    return d.save_checkpoint('r05-wally-win')


def basement_flash():
    import gdb
    assert d.state()['map'] == 'VictoryRoad_B1F'
    assert d.value('(int)FlagGet(0x888)') == 0
    before=d.value('(int)GetFlashLevel()')
    assert before > 1
    class FlashObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            return False
    observer=FlashObservation('FldEff_UseFlash',internal=True)
    observer.calls=0; observer.silent=True
    try:
        d.choose_field_move(2,1); d.settle(20000)
        assert observer.calls == 1
        assert d.value('(int)FlagGet(0x888)') == 1
        assert d.value('(int)GetFlashLevel()') == 1
        assert d.field_ready(d.state())
        print('NATURAL VICTORY ROAD FLASH PASS',before,d.state())
        return d.save_checkpoint('r05-victory-road-b1f-flash')
    finally:
        observer.delete()


def upper_boulders():
    import seafloor_driver as rocks
    assert d.state()['map'] == 'VictoryRoad_B1F'
    assert d.value('(int)FlagGet(0x888)') == 1
    assert rocks.positions()[3] == (4,7) and rocks.positions()[4] == (9,10)
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(5,7,'LEFT'); rocks.push(3,'LEFT')
    d.go(8,10); rocks.push(4,'RIGHT')
    assert rocks.positions()[3] == (3,7) and rocks.positions()[4] == (10,10)
    print('NATURAL VICTORY UPPER BOULDERS PASS',d.state())
    return d.save_checkpoint('r05-victory-road-upper-boulders')


def smash_corridor():
    import seafloor_driver as rocks
    assert d.state()['map'] == 'VictoryRoad_B1F'
    assert d.value('(int)FlagGet(0x888)') == 1
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(17,12,'RIGHT',100000)
    assert 10 not in rocks.positions()
    print('NATURAL VICTORY ROCK SMASH PASS',d.state())
    return d.save_checkpoint('r05-victory-road-rock-smashed')


def second_basement():
    assert d.state()['map'] == 'VictoryRoad_B1F'
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.warp_to(30,25,'VictoryRoad_B2F',120000)
    assert (d.state()['x'],d.state()['y']) == (30,25)
    print('NATURAL VICTORY SECOND BASEMENT PASS',d.state())
    return d.save_checkpoint('r05-victory-road-b2f-entry')
