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


def cross_second_basement():
    assert d.state()['map'] == 'VictoryRoad_B2F'
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(33,17,'UP')
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.warp_to(43,2,'VictoryRoad_B1F',150000)
    assert (d.state()['x'],d.state()['y']) == (42,2)
    print('NATURAL VICTORY B2F CROSSING PASS',d.state())
    return d.save_checkpoint('r05-victory-road-b2f-crossed')


def cave_waterfalls():
    assert d.state()['map'] == 'VictoryRoad_B2F'
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(33,17,'UP')
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.go(26,13); d.go(26,12)
    assert d.value('(int)IsPlayerSurfingNorth()') == 1
    d.advance('A',48,8); d.settle(30000)
    assert (d.state()['x'],d.state()['y']) == (26,8)
    d.go(8,10,dialogue_limit=150000)
    # Ordinary DOWN enters the western waterfall's native forced descent.
    d.advance('DOWN',180,4); d.settle(50000)
    assert (d.state()['x'],d.state()['y']) == (8,14)
    d.warp_to(19,12,'VictoryRoad_B1F',150000)
    assert (d.state()['x'],d.state()['y']) == (17,16)
    print('NATURAL VICTORY CAVE WATERFALLS PASS',d.state())
    return d.save_checkpoint('r05-victory-road-center-stairs')


def central_puzzle():
    import seafloor_driver as rocks
    assert d.state()['map'] == 'VictoryRoad_B1F'
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(19,25,'RIGHT',150000)
    assert 11 not in rocks.positions()
    d.talk(20,27,'UP',150000); rocks.push(5,'UP')
    d.talk(20,26,'RIGHT',150000)
    assert 12 not in rocks.positions()
    d.warp_to(20,21,'VictoryRoad_1F',150000)
    assert (d.state()['x'],d.state()['y']) == (21,32)
    print('NATURAL VICTORY CENTRAL PUZZLE PASS',d.state())
    return d.save_checkpoint('r05-victory-road-central-upper')


def victory_exit():
    assert d.state()['map'] == 'VictoryRoad_1F'
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.warp_to(39,5,'EverGrandeCity',200000)
    assert (d.state()['x'],d.state()['y']) == (18,28)
    print('NATURAL VICTORY ROAD EXIT PASS',d.state())
    return d.save_checkpoint('r05-victory-road-exit')


def league_lobby():
    assert d.state()['map'] == 'EverGrandeCity'
    d.go(18,6); d.cross('UP','EverGrandeCity_PokemonLeague_1F')
    # League layout differs from an ordinary Pokemon Center: counter at y3.
    d.talk(3,4,'UP')
    for index in range(d.state()['party']):
        mon='(void *)((char *)&gPlayerParty+%d)'%(index*100)
        assert d.value('(int)GetMonData3(%s,57,0)'%mon) == d.value('(int)GetMonData3(%s,58,0)'%mon)
    print('NATURAL LEAGUE LOBBY HEAL PASS',d.state())
    return d.save_checkpoint('r05-league-lobby-rested')


def league_gate():
    assert d.state()['map'] == 'EverGrandeCity_PokemonLeague_1F'
    assert d.value('(int)FlagGet(0x107)') == 0
    assert [d.value('(int)FlagGet(%d)'%(0x867+i)) for i in range(8)] == [1]*8
    d.talk(9,3,'UP',50000)
    assert d.value('(int)FlagGet(0x107)') == 1
    d.warp_to(9,1,'EverGrandeCity_Hall5',50000)
    assert (d.state()['x'],d.state()['y']) == (5,12)
    print('NATURAL LEAGUE BADGE GATE PASS',d.state())
    return d.save_checkpoint('r05-league-entered')


def sidney_tactical():
    """Switch through the real battle menu so Grass cannot sweep Swampert."""
    import gdb
    assert d.state()['map'] == 'EverGrandeCity_SidneysRoom'
    assert d.value('(int)FlagGet(0x4fb)') == 0
    original_heals=d.HEAL_ITEMS; d.HEAL_ITEMS=(21,22,13)
    original_choose=d.battle_button; original_party=d.battle_party_button
    desired=None; switches=0; last_action=None
    def choose():
        nonlocal desired,last_action,switches
        battle=d.memory('gBattleMons',352)
        function=gdb.execute('info symbol %d'%d.value('*(unsigned int *)&gBattlerControllerFuncs'),to_string=True).split(' in ')[0]
        if function == 'HandleInputChooseAction':
            player=int.from_bytes(battle[:2],'little')
            enemy=int.from_bytes(battle[88:90],'little')
            if player == desired:
                desired=None; switches+=1
            target=310 if 12 in battle[121:123] else 285  # TYPE_GRASS.
            healthy=any(d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+%d),11,0)'%(i*100)) == target and
                        d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+%d),57,0)'%(i*100)) > 0
                        for i in range(d.state()['party']))
            action=(player,enemy,int.from_bytes(battle[40:42],'little'),tuple(battle[24:32]))
            if action != last_action:
                print('NATURAL SIDNEY TURN',d.state()['frame'],action)
                last_action=action
            if player != target and healthy and not d.HEAL_PLAN:
                desired=target
                return d.cursor_button(d.memory('gActionSelectionCursor',1)[0],2)
        return original_choose()
    def party():
        if desired is None:
            return original_party()
        if not d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
            return 'A'  # Wait for initialization, or choose Send Out in context menu.
        slots=[i for i in range(d.state()['party'])
               if d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+%d),11,0)'%(i*100)) == desired and
                  d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+%d),57,0)'%(i*100)) > 0]
        assert len(slots) == 1
        target=slots[0]; cursor=d.memory('gPartyMenu',10)[9]
        return 'A' if cursor == target else 'RIGHT' if cursor == 0 else 'LEFT' if target == 0 else 'DOWN' if cursor < target else 'UP'
    try:
        d.battle_button=choose; d.battle_party_button=party
        d.talk(6,6,'UP',220000)
        outcome=d.value('*(unsigned char *)&gBattleOutcome')
        print('NATURAL SIDNEY TACTICAL RESULT',outcome,switches,d.state())
        assert outcome == 1 and d.value('(int)FlagGet(0x4fb)') == 1
        assert switches > 0
        return d.save_checkpoint('r05-sidney-win')
    finally:
        d.battle_button=original_choose; d.battle_party_button=original_party
        d.HEAL_ITEMS=original_heals


def retry_supplies():
    assert d.state()['map'] == 'EverGrandeCity'
    assert d.value('(int)CountTotalItemQuantityInBag(21)') == 0
    d.cross('UP','EverGrandeCity_PokemonLeague_1F')
    d.buy_item(21,5,position=(16,4),facing='UP')
    d.talk(3,4,'UP')
    assert d.value('(int)CountTotalItemQuantityInBag(21)') == 5
    print('NATURAL LEAGUE RETRY SUPPLIES PASS',d.state())
    return d.save_checkpoint('r05-sidney-retry-supplies')


def phoebe_loss():
    """Record the real resource-limited loss, never count it as League coverage."""
    assert d.state()['map'] == 'EverGrandeCity_PhoebesRoom'
    d.HEAL_ITEMS=(21,22,13)
    d.talk(6,6,'UP',220000)
    assert d.value('*(unsigned char *)&gBattleOutcome') == 2
    assert d.value('(int)FlagGet(0x4fc)') == 0
    assert d.state()['map'] == 'EverGrandeCity'
    assert (d.state()['x'],d.state()['y']) == (18,6)
    assert [d.value('(int)FlagGet(%d)'%(0x867+i)) for i in range(8)] == [1]*8
    print('NATURAL PHOEBE BLACKOUT PASS',d.state())
    return d.save_checkpoint('r05-phoebe-loss')


def get_mach_bike():
    assert d.state()['map'] == 'EverGrandeCity'
    assert d.value('(int)CountTotalItemQuantityInBag(259)') == 0
    d.fly_to('MauvilleCity')
    d.go(35,6); d.cross('UP','MauvilleCity_BikeShop')
    d.talk(3,5,'LEFT')
    assert d.value('(int)CountTotalItemQuantityInBag(259)') == 1
    d.save_checkpoint('r05-mach-bike-received')
    d.go(3,8); d.cross('DOWN','MauvilleCity')
    d.go(22,6); d.cross('UP','MauvilleCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','MauvilleCity')
    print('NATURAL MACH BIKE RECEIVED PASS',d.state())
    return d.save_checkpoint('r05-mach-bike-rested')


def toggle_mach_bike():
    """Use the owned Key Item through Bag; do not call bike/game functions."""
    import struct
    before=d.memory('gPlayerAvatar',1)[0]&2
    assert d.field_ready(d.state())
    assert d.value('(int)CountTotalItemQuantityInBag(259)') == 1
    d.open_start_action(2)
    for _ in range(180):
        if d.value('(int)FuncIsActiveTask((void *)Task_ItemContext_MultipleRows)'):
            break
        button='NONE'
        if d.value('(int)FuncIsActiveTask((void *)Task_BagMenu_HandleInput)'):
            position=d.memory('gBagPosition',28); pocket=position[5]
            if pocket != 4:
                button='RIGHT'
            else:
                entries=[d.value('(int)BagGetItemIdByPocketPosition(5,%d)'%i) for i in range(30)]
                target=entries.index(259)
                cursor=struct.unpack_from('<H',position,16)[0]+struct.unpack_from('<H',position,26)[0]
                button='A' if cursor == target else 'DOWN' if cursor < target else 'UP'
        d.advance(button,24,1)
    else:
        raise RuntimeError('Mach Bike bag selection deadline')
    assert d.value('(int)Menu_GetCursorPos()') == 0
    d.advance('A',120,1); d.settle(10000)
    assert bool(d.memory('gPlayerAvatar',1)[0]&2) != bool(before)
    print('NATURAL MACH BIKE TOGGLE PASS',d.memory('gPlayerAvatar',1)[0],d.state())


def return_to_pillar():
    assert d.state()['map'] == 'MauvilleCity'
    assert d.value('(int)CountTotalItemQuantityInBag(259)') == 1
    assert d.value('(int)VarGet(0x40ca)') == 3
    assert not d.memory('gPlayerAvatar',1)[0]&2
    d.RUN_WILD=True
    d.fly_to('MossdeepCity')
    d.talk(25,30,'DOWN')
    for target in ('Route127','Route128','Route129','Route130','Route131'):
        d.connect(target)
    d.go(36,7); d.cross('UP','SkyPillar_Entrance')
    d.warp_to(14,4,'SkyPillar_Outside',100000)
    d.go(14,6); d.cross('UP','SkyPillar_1F')
    print('NATURAL SKY PILLAR RETURN PASS',d.state())
    return d.save_checkpoint('r05-sky-pillar-return')


def broken_floor_entry():
    assert d.state()['map'] == 'SkyPillar_1F'
    assert d.value('(int)VarGet(0x40ca)') == 3
    d.RUN_WILD=True
    d.warp_to(10,1,'SkyPillar_2F',50000)
    assert (d.state()['x'],d.state()['y']) == (10,2)
    assert d.value('(int)MapGridGetMetatileBehaviorAt(20,12)') == 0xd2
    print('NATURAL SKY PILLAR BROKEN FLOOR PASS',d.state())
    return d.save_checkpoint('r05-sky-pillar-broken-floor')


def ride_to(button, x, y, limit=160):
    """Steer with continuous keys; observe every two frames without braking."""
    assert d.memory('gPlayerAvatar',1)[0]&2
    start=d.value('sDiagnosticFrame')
    origin=d.state()['map']
    while (d.state()['x'],d.state()['y']) != (x,y):
        assert d.state()['map'] == origin, d.state()
        assert d.field_ready(d.state()), d.state()
        assert d.value('sDiagnosticFrame')-start < limit, d.state()
        d.advance(button,2,2)
    print('NATURAL MACH BIKE TURN',button,d.state(),list(d.memory('gPlayerAvatar',12)))


def broken_floor_crossing():
    assert d.state()['map'] == 'SkyPillar_2F'
    assert d.value('(int)VarGet(0x40ca)') == 3
    d.RUN_WILD=True
    d.go(12,2)
    if not d.memory('gPlayerAvatar',1)[0]&2:
        toggle_mach_bike()
    # Enough straight run-up before cracks; turn before a wall brakes the bike.
    for button,x,y in (('DOWN',12,13),('LEFT',1,13),('UP',1,7),
                       ('RIGHT',3,7),('UP',3,2)):
        ride_to(button,x,y)
    d.advance('NONE',24)
    d.settle(30000)
    assert d.state()['map'] == 'SkyPillar_3F', d.state()
    assert (d.state()['x'],d.state()['y']) == (3,2)
    print('NATURAL SKY PILLAR SECOND FLOOR BIKE PASS',d.state())
    return d.save_checkpoint('r05-sky-pillar-3f-mach')


def upper_broken_floor():
    assert d.state()['map'] == 'SkyPillar_3F'
    d.RUN_WILD=True
    if d.memory('gPlayerAvatar',1)[0]&2:
        toggle_mach_bike()
    d.warp_to(11,1,'SkyPillar_4F',50000)
    d.go(12,2)
    toggle_mach_bike()
    for button,x,y in (('DOWN',12,6),('LEFT',10,6),('DOWN',10,12),
                       ('LEFT',3,12),('UP',3,4),('RIGHT',4,4)):
        ride_to(button,x,y)
    # Coasting breaks the floor over the otherwise isolated central platform.
    d.advance('NONE',300)
    d.settle(30000)
    assert d.state()['map'] == 'SkyPillar_3F', d.state()
    assert (d.state()['x'],d.state()['y']) == (6,4)
    if d.memory('gPlayerAvatar',1)[0]&2:
        toggle_mach_bike()
    d.save_checkpoint('r05-sky-pillar-central-drop')
    d.warp_to(7,1,'SkyPillar_4F',50000)
    d.warp_to(3,1,'SkyPillar_5F',50000)
    assert (d.state()['x'],d.state()['y']) == (3,2)
    print('NATURAL SKY PILLAR FOURTH FLOOR PUZZLE PASS',d.state())
    return d.save_checkpoint('r05-sky-pillar-5f-mach')
