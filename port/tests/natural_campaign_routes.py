"""Measured route actions after the real intro; keys and read-only checkpoints."""
import campaign_driver as d
import gdb


def rest_old_lady():
    """Accept one real heal and decline the repeated rest question via keys."""
    assert d.state()['map'] == 'Route111_OldLadysRestStop'

    class HealObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            return False  # Observe execution; never skip the game's function.

    observer=HealObservation('HealPlayerParty',internal=True)
    observer.calls=0; observer.silent=True
    try:
        d.go(6,4); d.advance('UP',24,4); d.advance('A',24,4)
        start=d.value('sDiagnosticFrame')
        while not d.field_ready(d.state()):
            assert d.value('sDiagnosticFrame')-start < 8000, 'Rest dialogue deadline'
            d.advance('B' if observer.calls else 'A',96,1)
        assert observer.calls == 1, 'Expected exactly one script-triggered heal'
        for slot in range(d.state()['party']):
            mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
            assert d.value(f'(int)GetMonData3({mon},57,0)') == d.value(f'(int)GetMonData3({mon},58,0)')
            assert d.value(f'(unsigned int)GetMonData3({mon},55,0)') == 0
            bonuses=d.value(f'(int)GetMonData3({mon},21,0)')
            for index in range(4):
                move=d.value(f'(int)GetMonData3({mon},{13+index},0)')
                assert d.value(f'(int)GetMonData3({mon},{17+index},0)') == d.value(f'(int)CalculatePPWithBonus({move},{bonuses},{index})')
        print('NATURAL REST ONCE PASS',d.state())
        return d.state()
    finally:
        observer.delete()


def meet_may():
    assert d.state()["map"] == "LittlerootTown" and d.state()["party"] == 0
    d.walk(14,9); d.advance("UP",300,8); d.settle()
    d.walk(2,2); d.advance("NONE",300); d.settle()
    d.walk(4,4); d.advance("RIGHT",24,4); d.advance("A",24,4); d.settle()
    assert d.value("(unsigned int)VarGet(0x408D)") == 3
    d.walk(1,1); d.advance("NONE",300)
    d.walk(2,8); d.advance("DOWN",300,8); d.settle()
    print("NATURAL MET MAY PASS", d.state())


def rescue_birch():
    assert d.state()["map"] == "LittlerootTown" and d.state()["party"] == 0
    d.walk(11,1); d.settle()
    assert d.value("(unsigned int)VarGet(0x4050)") == 2
    d.walk(11,0); d.advance("UP",300,8); d.settle()
    assert d.state()["map"] == "Route101"
    d.walk(7,15); d.advance("UP",24,4); d.advance("A",300,4)
    assert d.state()["callback"] == "CB2_StarterChoose"
    d.advance("RIGHT",24,4); d.advance("A",24,4); d.settle(16000)
    d.advance("NONE",300); d.settle(16000)
    assert d.state()["map"] == "LittlerootTown_ProfessorBirchsLab"
    assert d.state()["party"] == 1
    assert d.value("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)") == 283
    assert d.value("(unsigned int)GetMonData3((void *)&gPlayerParty,56,0)") == 5
    assert d.value("*(unsigned char *)&gBattleOutcome") == 1
    print("NATURAL MUDKIP AND BIRCH PASS", d.state())


def leave_lab():
    d.go(6,12); d.advance("DOWN",300,8); d.settle()
    assert d.state()["map"] == "LittlerootTown"


def north_to_oldale():
    d.go(11,0); d.advance("UP",300,8); d.settle()
    assert d.state()["map"] == "Route101"
    d.go(10,0); d.advance("UP",300,8); d.settle()
    assert d.state()["map"] == "OldaleTown"


def heal_oldale():
    d.go(6,17); d.advance("UP",300,8); d.settle()
    assert d.state()["map"] == "OldaleTown_PokemonCenter_1F"
    d.go(7,4); d.advance("UP",24,4); d.advance("A",24,4); d.settle()
    assert d.value("(int)GetMonData3((void *)&gPlayerParty,57,0)") == d.value("(int)GetMonData3((void *)&gPlayerParty,58,0)")
    d.go(7,8); d.advance("DOWN",300,8); d.settle()
    assert d.state()["map"] == "OldaleTown"


def rival_and_dex():
    leave_lab(); north_to_oldale(); heal_oldale()
    d.go(10,0); d.advance("UP",300,8); d.settle()
    assert d.state()["map"] == "Route103"
    d.go(10,4); d.advance("UP",24,4); d.advance("A",24,4); d.settle(16000)
    assert d.value("(int)FlagGet(0x82)") == 1
    assert d.memory("gBattleOutcome",1)[0] == 1
    d.go(10,21); d.advance("DOWN",300,8); d.settle()
    assert d.state()["map"] == "OldaleTown"
    d.go(10,19); d.advance("DOWN",300,8); d.settle()
    assert d.state()["map"] == "Route101"
    d.go(11,19); d.advance("DOWN",300,8); d.settle()
    assert d.state()["map"] == "LittlerootTown"
    d.go(7,17); d.advance("UP",300,8); d.settle(18000)
    assert d.state()["map"] == "LittlerootTown_ProfessorBirchsLab"
    assert d.value("(int)FlagGet(0x861)") == 1
    assert d.value("(int)CountTotalItemQuantityInBag(4)") == 5
    assert d.value("(int)VarGet(0x4084)") == 5
    d.save_checkpoint("r01-birch-dex")


def cut_peeko_and_pokenav():
    """Continue after the real Stone Badge; includes the forced call tutorial."""
    assert d.state()["map"] == "RustboroCity"
    assert d.value("(int)FlagGet(0x867)") == 1
    d.go(23,20); d.settle(); d.go(29,10); d.settle()
    d.go(16,39); d.cross("UP","RustboroCity_PokemonCenter_1F"); d.nurse()
    d.go(7,8); d.cross("DOWN","RustboroCity")
    d.go(9,39); d.cross("UP","RustboroCity_CuttersHouse")
    d.talk(7,6,"UP")
    assert d.value("(int)FlagGet(0x89)") == 1
    d.go(5,8); d.cross("DOWN","RustboroCity")
    d.go(39,10); d.cross("RIGHT","Route116")
    d.go(47,9); d.cross("UP","RusturfTunnel")
    d.go(9,5); d.settle(); d.talk(13,5,"RIGHT")
    assert d.value("(int)FlagGet(0x8f)") == 1
    assert d.value("(int)VarGet(0x4090)") == 1
    d.save_checkpoint("r02-peeko")
    d.go(4,10); d.cross("DOWN","Route116")
    d.go(0,10); d.cross("LEFT","RustboroCity")
    d.go(31,10); d.settle(30000)
    assert d.state()["map"] == "RustboroCity_DevonCorp_3F"
    assert d.value("(int)FlagGet(0x862)") == 1
    assert d.value("(int)VarGet(0x405a)") == 6
    d.save_checkpoint("r02-pokenav")
    d.go(2,2); d.cross("UP","RustboroCity_DevonCorp_2F")
    d.go(14,2); d.cross("UP","RustboroCity_DevonCorp_1F")
    d.go(5,8); d.cross("DOWN","RustboroCity")
    assert d.value("(int)VarGet(0x405a)") == 7
    d.save_checkpoint("r02-matchcall")


def steven_letter():
    """Walk from the real Knuckle Badge checkpoint through Granite Cave."""
    assert d.state()['map'] == 'DewfordTown_Gym'
    assert d.value('(int)FlagGet(0x868)') == 1
    d.go(5,27); d.cross('DOWN','DewfordTown')
    d.go(2,11); d.cross('UP','DewfordTown_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','DewfordTown')
    d.go(8,0); d.cross('UP','Route106')
    d.go(48,17); d.cross('UP','GraniteCave_1F')
    d.talk(36,10,'UP')
    assert d.value('(int)FlagGet(0x6d)') == 1
    d.go(17,11); d.cross('NONE','GraniteCave_B1F')
    assert d.value('(int)VarGet(0x4022)') == 1
    d.go(28,21); d.cross('NONE','GraniteCave_B2F')
    d.go(29,13); d.cross('NONE','GraniteCave_B1F')
    d.go(25,13); d.cross('NONE','GraniteCave_1F')
    d.go(5,10); d.cross('DOWN','GraniteCave_StevensRoom')
    d.talk(7,7,'DOWN')
    assert d.value('(int)FlagGet(0xbd)') == 1
    d.save_checkpoint('r02-steven')


def sail_to_slateport():
    assert d.state()['map'] == 'GraniteCave_StevensRoom'
    assert d.value('(int)FlagGet(0xbd)') == 1
    d.go(7,3); d.cross('UP','GraniteCave_1F')
    d.go(35,3); d.cross('NONE','GraniteCave_B1F')
    d.go(29,13); d.cross('NONE','GraniteCave_B2F')
    d.go(28,21); d.cross('NONE','GraniteCave_B1F')
    d.go(4,21); d.cross('NONE','GraniteCave_1F')
    d.go(37,12); d.cross('DOWN','Route106')
    d.go(68,19); d.cross('DOWN','DewfordTown')
    d.choose_dialogue(11,9,'RIGHT',1)
    assert d.state()['map'] == 'Route109'
    d.go(20,0); d.cross('UP','SlateportCity')
    d.go(19,20); d.cross('UP','SlateportCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','SlateportCity')


def heal_slateport():
    if d.state()['map'] == 'Route110':
        d.go(15,99); d.cross('DOWN','SlateportCity')
    assert d.state()['map'] == 'SlateportCity'
    d.go(19,20); d.cross('UP','SlateportCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','SlateportCity')


def rock_smash_route111():
    """Receive/teach the HM, reject the rock collision, then use it by dialog."""
    assert d.state()['map'] == 'MauvilleCity_Gym'
    assert d.value('(int)FlagGet(0x869)') == 1
    d.RUN_WILD=True
    d.go(4,20); d.cross('DOWN','MauvilleCity')
    d.go(22,6); d.cross('UP','MauvilleCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','MauvilleCity')
    d.go(32,15); d.cross('UP','MauvilleCity_House1')
    d.talk(4,5,'UP'); assert d.value('(int)FlagGet(0x6b)') == 1
    d.teach_tm(344,0)
    d.go(3,7); d.cross('DOWN','MauvilleCity')
    d.go(18,0); d.cross('UP','Route111')
    d.go(18,102); d.advance('UP',48,4)
    assert (d.state()['x'],d.state()['y']) == (18,102)
    print('ROCK COLLISION CLOSED PASS',d.state())
    d.talk(18,102,'UP')
    assert d.value('(int)FlagGet(0x11)') == 1
    d.go(18,100)
    assert (d.state()['x'],d.state()['y']) == (18,100)
    return d.save_checkpoint('r02-route111-rock')


def meteor_falls_scene():
    """Walk from Fallarbor to the scripted meteorite theft and cable-car gate."""
    assert d.state()['map'] == 'FallarborTown'
    assert d.value('(int)VarGet(0x40bf)') == 0
    assert d.value('(int)FlagGet(0x333)') == 0
    d.RUN_WILD=True
    d.go(0,10); d.cross('LEFT','Route114')
    d.go(8,64); d.cross('UP','MeteorFalls_1F_1R')
    d.go(14,18); d.settle(30000)
    assert d.value('(int)VarGet(0x40bf)') == 1
    assert d.value('(int)FlagGet(0x333)') == 1
    return d.save_checkpoint('r02-meteor-falls')


def jagged_pass_to_lavaridge():
    """Descend by foot and ledge jumps, then heal in Lavaridge."""
    assert d.state()['map'] == 'MtChimney'
    assert d.value('(int)FlagGet(0x8b)') == 1
    d.RUN_WILD=True; d.HEAL_ITEMS=(22,13)
    before=d.value('(unsigned int)GetGameStat(43)')
    d.go(20,40); d.cross('DOWN','JaggedPass')
    d.go(14,39)
    assert d.value('(unsigned int)GetGameStat(43)') > before
    print('NATURAL LEDGE DESCENT PASS',d.state())
    d.cross('DOWN','Route112'); d.connect('LavaridgeTown')
    d.go(9,7); d.cross('UP','LavaridgeTown_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','LavaridgeTown')
    return d.save_checkpoint('r02-lavaridge')


def flannery_gym():
    """Traverse the actual two-floor pool puzzle and earn the fourth badge."""
    assert d.state()['map'] == 'LavaridgeTown'
    assert [d.value(f'(int)FlagGet({0x867+i})') for i in range(4)] == [1,1,1,0]
    d.HEAL_ITEMS=(22,13)
    d.go(5,16); d.cross('UP','LavaridgeTown_Gym_1F')
    before=d.value('(unsigned int)GetGameStat(43)')
    pools=((8,9),(0,17),(0,10),(0,6),(2,3),(7,2),(10,6),(12,12))
    for index,(x,y) in enumerate(pools):
        origin=d.state()['map']
        d.go(x,y); d.advance('NONE',300); d.settle(30000)
        expected='LavaridgeTown_Gym_B1F' if index%2 == 0 else 'LavaridgeTown_Gym_1F'
        assert d.state()['map'] != origin and d.state()['map'] == expected
        print('NATURAL GYM POOL PASS',index,x,y,d.state())
    assert d.value('(unsigned int)GetGameStat(43)') > before
    d.go(13,10); d.save_checkpoint('r02-flannery-ready')
    d.talk(13,10,'UP',60000)
    assert d.state()['map'] == 'LavaridgeTown_Gym_1F'
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)FlagGet(0x86a)') == 1
    return d.save_checkpoint('r02-flannery')


def rusturf_strength():
    """Break the reunion rock with the owned HM, then receive Strength."""
    assert d.state()['map'] == 'VerdanturfTown'
    assert d.value('(int)CountTotalItemQuantityInBag(342)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(22,13)
    d.go(8,2); d.cross('UP','RusturfTunnel')
    d.go(25,5); d.advance('LEFT',48,4)
    assert (d.state()['x'],d.state()['y']) == (25,5)
    print('NATURAL RUSTURF ROCK CLOSED PASS',d.state())
    d.talk(25,5,'LEFT',30000)
    assert d.value('(int)CountTotalItemQuantityInBag(342)') == 1
    d.go(24,5)
    assert (d.state()['x'],d.state()['y']) == (24,5)
    print('NATURAL RUSTURF ROCK OPEN PASS',d.state())
    return d.save_checkpoint('r03-strength-reunion')


def surf_gate_closed():
    """A real shore remains impassable before receiving Surf and badge five."""
    assert d.state()['map'] == 'PetalburgCity'
    assert d.value('(int)FlagGet(0x86b)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(341)') == 0
    d.go(7,20); d.advance('LEFT',48,4); d.advance('A',24,1); d.settle()
    assert (d.state()['x'],d.state()['y']) == (7,20)
    assert not d.memory('gPlayerAvatar',1)[0]&8
    print('NATURAL SURF GATE CLOSED PASS',d.state())


def norman_gym():
    """Unlock the Speed/Confusion/Strength rooms by winning their battles."""
    assert d.state()['map'] == 'PetalburgCity'
    surf_gate_closed()
    d.HEAL_ITEMS=(22,13)
    d.teach_tm(342,0)
    d.go(15,9); d.cross('UP','PetalburgCity_Gym')
    d.talk(1,106,'UP')  # These doors use A/Yes, not walking into the tile.
    assert (d.state()['x'],d.state()['y']) == (7,85)
    for trainer,door,arrival in (((4,82),(1,80),(7,46)),
                                  ((4,43),(7,41),(1,20)),
                                  ((4,17),(7,15),(1,7))):
        d.talk(*door,'UP')
        assert (d.state()['x'],d.state()['y']) == door
        print('NATURAL NORMAN ROOM LOCKED PASS',door,d.state())
        d.talk(*trainer,'UP',50000)
        assert d.memory('gBattleOutcome',1)[0] == 1
        d.talk(*door,'UP')
        assert (d.state()['x'],d.state()['y']) == arrival
        print('NATURAL NORMAN ROOM OPEN PASS',door,d.state())
    d.save_checkpoint('r03-norman-ready')
    d.talk(4,3,'UP',70000)
    assert d.value('(int)FlagGet(0x86b)') == 1
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)CountTotalItemQuantityInBag(341)') == 1
    return d.save_checkpoint('r03-norman')


def surf_crossing():
    """Teach the received Surf, enter water, cross it and dismount on land."""
    assert d.state()['map'] == 'PetalburgCity_WallysHouse'
    assert d.value('(int)FlagGet(0x86b)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(341)') == 1
    d.teach_tm(341,0)
    d.go(3,7); d.cross('DOWN','PetalburgCity')
    d.go(20,17); d.cross('UP','PetalburgCity_PokemonCenter_1F'); d.nurse()
    d.go(7,8); d.cross('DOWN','PetalburgCity')
    d.talk(7,20,'LEFT')
    assert d.memory('gPlayerAvatar',1)[0]&8
    assert (d.state()['x'],d.state()['y']) == (6,20)
    d.go(4,20)
    assert (d.state()['x'],d.state()['y']) == (4,20)
    d.go(7,20)
    assert not d.memory('gPlayerAvatar',1)[0]&8
    print('NATURAL SURF CROSSING PASS',d.state())
    return d.save_checkpoint('r03-surf')


def weather_bed():
    assert d.state()['map'] == 'Route119_WeatherInstitute_1F'
    d.talk(2,3,'LEFT')
    for slot in range(d.state()['party']):
        mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
        assert d.value(f'(int)GetMonData3({mon},57,0)') == d.value(f'(int)GetMonData3({mon},58,0)')
        assert d.value(f'(unsigned int)GetMonData3({mon},55,0)') == 0
    print('NATURAL WEATHER BED PASS',d.state())


def weather_institute():
    """Defeat Aqua, receive the actual gift and cross the cleared bridge."""
    assert d.state()['map'] == 'Route119_WeatherInstitute_1F'
    assert d.value('(int)FlagGet(0x97)') == 0
    assert d.value('(int)VarGet(0x40b3)') == 0
    count=d.state()['party']
    d.RUN_WILD=True; d.HEAL_ITEMS=(22,13)
    d.go(17,2); d.cross('UP','Route119_WeatherInstitute_2F')
    d.talk(5,6,'LEFT',60000)
    assert d.value('(int)FlagGet(0x97)') == 1
    assert d.value('(int)VarGet(0x40b3)') == 1  # Route119 advances this to 2 on exit.
    assert d.state()['party'] == count+1
    mon=f'(void *)((char *)&gPlayerParty+{count*100})'
    assert d.value(f'(int)GetMonData3({mon},11,0)') == 385
    assert d.value(f'(int)GetMonData3({mon},56,0)') == 25
    d.save_checkpoint('r03-castform')
    d.go(17,2); d.cross('UP','Route119_WeatherInstitute_1F')
    weather_bed()
    d.go(9,11); d.cross('DOWN','Route119')
    d.go(14,33)
    assert (d.state()['x'],d.state()['y']) == (14,33)
    print('NATURAL WEATHER BRIDGE OPEN PASS',d.state())
    return d.save_checkpoint('r03-weather-cleared')


def museum_delivery():
    """Check the blocked museum, talk to Dock, pay, then finish Stern's scene."""
    assert d.state()['map'] == 'SlateportCity'
    assert d.value('(int)FlagGet(0x94)') == 0
    d.go(30,28); d.advance('UP',48,4)
    assert d.state()['map'] == 'SlateportCity'
    assert (d.state()['x'],d.state()['y']) == (30,28)
    print('MUSEUM GATE CLOSED PASS',d.state())
    d.go(26,39); d.cross('UP','SlateportCity_SternsShipyard_1F')
    d.talk(4,5,'RIGHT'); assert d.value('(int)FlagGet(0x94)') == 1
    d.go(2,14); d.cross('DOWN','SlateportCity')
    d.go(30,27)
    save=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    money=d.value(f'(int)GetMoney((void *)({save}+0x490))')
    d.cross('UP','SlateportCity_OceanicMuseum_1F')
    d.go(9,7)  # The fee is a coordinate event one tile past the entrance warp.
    save=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    assert d.value(f'(int)GetMoney((void *)({save}+0x490))') == money-50
    assert d.value('(int)VarGet(0x40aa)') == 1
    print('MUSEUM ADMISSION FEE PASS',d.state())
    d.go(6,2); d.cross('UP','SlateportCity_OceanicMuseum_2F')
    d.talk(13,5,'DOWN',40000)
    assert d.value('(int)FlagGet(0x95)') == 1
    assert d.memory('gBattleOutcome',1)[0] == 1
    d.save_checkpoint('r02-stern')
    d.go(6,1); d.cross('UP','SlateportCity_OceanicMuseum_1F')
    d.go(9,8); d.cross('DOWN','SlateportCity')
    return d.save_checkpoint('r02-slateport')


def catch_wingull():
    assert d.state()['map'] == 'Route110' and d.state()['party'] == 1
    previous=(d.RUN_WILD,d.CATCH_SPECIES)
    try:
        d.RUN_WILD=True; d.CATCH_SPECIES={309}
        d.go(9,93)
        for step in range(600):
            # Face alternating waypoints; releasing input for dialog/battles
            # can interrupt a step, so never assume symmetric held-key travel.
            d.go(11 if step%2 == 0 else 9,93)
            d.settle(30000)
            if d.state()['party'] > 1:
                break
        assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),11,0)') == 309
        return d.save_checkpoint('r02-first-catch')
    finally:
        d.RUN_WILD,d.CATCH_SPECIES=previous


def train_wingull(target=17,visits=6):
    """Experience from actual wild fights, with real nurse visits as needed."""
    assert d.value('(int)GetMonData3((void *)&gPlayerParty,11,0)') == 309
    previous=(d.RUN_WILD,d.RUN_FROM_TYPES,d.SWITCH_FROM_TYPES)
    try:
        d.RUN_FROM_TYPES=set()
        d.SWITCH_FROM_TYPES={13}  # Switch to Marshtomp before Electric attacks.
        for visit in range(visits):
            d.RUN_WILD=True; heal_slateport()
            d.save_checkpoint('r02-training')
            if d.value('(int)GetMonData3((void *)&gPlayerParty,56,0)') >= target:
                return d.save_checkpoint('r02-wingull-trained')
            d.go(15,0); d.cross('UP','Route110'); d.go(9,93)
            d.RUN_WILD=False
            for step in range(200):
                d.go(11 if step%2 == 0 else 9,93)
                d.settle(30000)
                owned={d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),11,0)')
                       for i in range(d.state()['party'])}
                d.CATCH_SPECIES.difference_update(owned)
                if d.state()['map'] != 'Route110':
                    break
                level=d.value('(int)GetMonData3((void *)&gPlayerParty,56,0)')
                hp=d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)')
                if level >= target or hp < 10:
                    break
            if d.field_ready(d.state()):
                d.save_checkpoint('r02-training')
        raise RuntimeError('Training target not reached through actual battles')
    finally:
        d.RUN_WILD,d.RUN_FROM_TYPES,d.SWITCH_FROM_TYPES=previous
