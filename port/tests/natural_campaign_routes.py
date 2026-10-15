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


def route119_rival():
    """Use the trained Pelipper and win the real rival encounter for Fly."""
    assert d.state()['map'] == 'Route119_WeatherInstitute_1F'
    assert d.value('(int)FlagGet(0x6e)') == 0
    assert d.value('(int)VarGet(0x4072)') == 0
    assert d.value('(int)GetMonData3((void *)&gPlayerParty,11,0)') == 310
    d.RUN_WILD=True; d.HEAL_ITEMS=(22,13)
    d.teach_tm(341,0)
    d.go(9,11); d.cross('DOWN','Route119')
    d.go(25,31); d.settle(70000)
    assert d.value('(int)FlagGet(0x6e)') == 1
    assert d.value('(int)VarGet(0x4072)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(340)') == 1
    assert d.memory('gBattleOutcome',1)[0] == 1
    return d.save_checkpoint('r03-fly')


def devon_scope():
    """Observe the hidden obstacle, earn the Scope and clear gym access."""
    assert d.state()['map'] == 'FortreeCity'
    assert d.value('(int)FlagGet(0x11d)') == 0
    assert d.value('(int)FlagGet(0x127)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(288)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(25,7,'DOWN')
    assert (d.state()['x'],d.state()['y']) == (25,7)
    assert d.value('(int)FlagGet(0x127)') == 0
    print('NATURAL INVISIBLE GATE CLOSED PASS',d.state())
    d.connect('Route120'); d.go(14,15)
    d.RUN_WILD=False
    d.talk(14,15,'LEFT',50000)
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)FlagGet(0x11d)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(288)') == 1
    d.save_checkpoint('r03-devon-scope')
    d.go(11,15)
    assert (d.state()['x'],d.state()['y']) == (11,15)
    d.RUN_WILD=True; d.connect('FortreeCity')
    d.talk(25,7,'DOWN')
    assert d.value('(int)FlagGet(0x127)') == 1
    d.go(25,8)
    assert (d.state()['x'],d.state()['y']) == (25,8)
    print('NATURAL INVISIBLE GATE OPEN PASS',d.state())
    d.go(22,12); d.cross('UP','FortreeCity_Gym')
    return d.save_checkpoint('r03-gym-access')


def fly_badge_gate():
    """An owned, learned Fly must still reject use before Winona's badge."""
    before=d.state()
    assert d.field_ready(before) and before['map'] == 'FortreeCity'
    assert d.value('(int)FlagGet(0x86c)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(340)') == 1
    d.choose_field_move(1,5)
    assert d.value('(int)FuncIsActiveTask((void *)Task_ReturnToChooseMonAfterText)')
    gdb.execute(f'dump binary memory {d.SCRATCH.as_posix()}/r03-fly-denied.raw &sPixels ((char *)&sPixels)+153600')
    for step in range(20):
        if d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)'):
            break
        d.advance('B',96,1)
    assert d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)')
    d.advance('B',180,1); d.advance('B',48,1)
    assert d.field_ready(d.state())
    assert all(d.state()[key] == before[key] for key in ('map','x','y'))
    print('NATURAL FLY BADGE GATE CLOSED PASS',d.state())
    return d.save_checkpoint('r03-fly-gate')


def fortree_gates():
    """Traverse the puzzle from its entrance with native rotations observed."""
    import rotating_gate_driver as gates
    assert d.state()['map'] == 'FortreeCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (15,24)
    class RotationObservation(gdb.Breakpoint):
        def stop(self):
            self.calls += 1
            return False
    observer=RotationObservation('RotatingGate_RotateInDirection',internal=True)
    observer.calls=0; observer.silent=True
    d.HEAL_ITEMS=(21,22,13)
    try:
        gates.walk_to(15,3)
        assert observer.calls > 0, 'Expected real gate rotations, not a bypass'
        print('NATURAL NATIVE GATE ROTATIONS PASS',observer.calls)
        return d.save_checkpoint('r03-winona-ready')
    finally:
        observer.delete()


def ice_tm_supplies():
    """Buy two consumable TMs and medicine using the earned campaign money."""
    assert d.state()['map'] == 'LilycoveCity_DepartmentStore_4F'
    assert d.value('(int)CountTotalItemQuantityInBag(302)') == 0
    d.buy_item(302,2,(7,4),'DOWN')
    assert d.value('(int)CountTotalItemQuantityInBag(302)') == 2
    d.save_checkpoint('r03-blizzard-purchased')
    d.teach_tm(302,0); d.teach_tm(302,1)
    assert d.value('(int)CountTotalItemQuantityInBag(302)') == 0
    for slot in (0,1):
        moves=[d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{slot*100}),{13+i},0)') for i in range(4)]
        assert 59 in moves and 57 in moves
    d.go(16,2); d.cross('UP','LilycoveCity_DepartmentStore_3F')
    d.go(13,2); d.cross('UP','LilycoveCity_DepartmentStore_2F')
    d.buy_item(21,6,(10,4),'DOWN')
    return d.save_checkpoint('r03-winona-supplies')


def winona_battle():
    assert d.state()['map'] == 'FortreeCity_Gym'
    assert (d.state()['x'],d.state()['y']) == (15,3)
    assert d.value('(int)FlagGet(0x86c)') == 0
    d.HEAL_ITEMS=(21,22,13)
    d.talk(15,3,'UP',80000)
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)FlagGet(0x86c)') == 1
    return d.save_checkpoint('r03-winona')


def fly_roundtrip():
    """Confirm two real flights and cancel one map after the sixth badge."""
    assert d.state()['map'] == 'FortreeCity'
    d.RUN_WILD=True
    d.fly_to('RustboroCity')
    d.save_checkpoint('r03-fly-rustboro')
    before=d.state()
    d.choose_field_move(1,5); d.advance('NONE',600)
    assert d.state()['callback'] == 'CB2_FlyMap'
    d.advance('B',600,1)
    assert d.value('*(unsigned int *)&sFlyMap') == 0
    assert d.state()['callback'] == 'CB2_UpdatePartyMenu'
    d.advance('B',180,1); d.advance('B',48,1)
    assert d.field_ready(d.state())
    assert all(d.state()[key] == before[key] for key in ('map','x','y'))
    print('NATURAL FLY CANCEL PASS',d.state())
    d.fly_to('FortreeCity')
    return d.save_checkpoint('r03-fly-roundtrip')


def mt_pyre():
    """Climb from the real entrance and receive the emblem through the event."""
    assert d.state()['map'] == 'MtPyre_1F'
    assert d.value('(int)VarGet(0x40b9)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(375)') == 0
    assert d.value('(int)FlagGet(0x34f)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.warp_to(3,6,'MtPyre_Exterior')
    d.warp_to(19,10,'MtPyre_Summit')
    d.go(23,7,dialogue_limit=80000)
    assert d.state()['map'] == 'MtPyre_Summit'
    assert d.value('(int)VarGet(0x40b9)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(375)') == 1
    assert d.value('(int)FlagGet(0xd4)') == 1
    assert d.value('(int)FlagGet(0x34f)') == 1
    return d.save_checkpoint('r04-magma-emblem')


def magma_entry():
    """Open the hideout with the earned emblem and push its entrance boulders."""
    assert d.state()['map'] == 'JaggedPass'
    assert d.value('(int)VarGet(0x40c8)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(375)') == 1
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.go(14,15)
    assert d.value('(int)VarGet(0x40c8)') == 2
    d.warp_to(16,18,'MagmaHideout_1F')
    d.talk(7,23,'LEFT')
    assert d.value('(int)FlagGet(0x889)') == 1
    d.advance('LEFT',180,32); d.settle()
    d.go(6,22)
    for attempt in range(8):
        # An encounter can consume the push input. Retry only if the live
        # boulder is still blocking the corridor after returning to the field.
        objects=d.memory('gObjectEvents',576)
        boulder=next(objects[i:i+36] for i in range(0,576,36)
                     if objects[i]&1 and objects[i+8] == 4)
        if int.from_bytes(boulder[16:18],'little',signed=True)-7 == 4:
            break
        d.advance('LEFT',180,32); d.settle()
    else:
        raise RuntimeError('Strength push deadline: '+str(d.state()))
    print('NATURAL STRENGTH PUSH PASS',d.state())
    d.warp_to(25,34,'MagmaHideout_2F_1R',dialogue_limit=80000)
    return d.save_checkpoint('r04-magma-2f')


def maxie_magma():
    """Run Groudon's awakening and Maxie's battle, then check the story gates."""
    print('NATURAL MAXIE PRECONDITION',d.state())
    assert d.field_ready(d.state()), ('Continue must not start the NPC event',d.state())
    assert d.state()['map'] == 'MagmaHideout_4F'
    assert (d.state()['x'],d.state()['y']) == (15,21)
    assert d.value('(int)FlagGet(0x6f)') == 0
    assert d.value('(int)HasTrainerBeenFought(601)') == 0
    assert d.value('(int)VarGet(0x4058)') == 0
    assert d.value('(int)VarGet(0x40a0)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(15,21,'RIGHT',100000)
    assert d.state()['map'] == 'MagmaHideout_4F'
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)HasTrainerBeenFought(601)') == 1
    assert d.value('(int)FlagGet(0x6f)') == 1
    assert d.value('(int)VarGet(0x4058)') == 1
    assert d.value('(int)VarGet(0x40a0)') == 1
    return d.save_checkpoint('r04-maxie')


def aqua_gate_closed():
    assert d.state()['map'] == 'AquaHideout_1F'
    assert d.value('(int)VarGet(0x40a0)') == 1
    assert d.value('(int)FlagGet(0x61)') == 0
    assert d.value('(int)FlagGet(0x335)') == 0
    assert d.value('(int)FlagGet(0x336)') == 0
    for x in (13,14):
        d.talk(x,12,'UP'); d.advance('UP',96,32); d.settle()
        assert d.state()['map'] == 'AquaHideout_1F'
        assert (d.state()['x'],d.state()['y']) == (x,12)
    print('NATURAL AQUA GATE CLOSED PASS',d.state())
    return d.save_checkpoint('r04-aqua-blocked')


def harbor_submarine():
    """See the interview/theft, then cross the previously blocked Aqua gate."""
    assert d.state()['map'] == 'SlateportCity'
    assert d.value('(int)VarGet(0x4058)') == 1
    assert d.value('(int)VarGet(0x40a0)') == 1
    assert all(d.value(f'(int)FlagGet({flag})') == 0 for flag in (0x61,0x335,0x336))
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    d.talk(27,13,'RIGHT',60000)
    assert d.state()['map'] == 'SlateportCity_Harbor'
    assert d.value('(int)VarGet(0x4058)') == 2
    d.go(8,13,dialogue_limit=60000)
    assert d.value('(int)VarGet(0x40a0)') == 2
    assert all(d.value(f'(int)FlagGet({flag})') == 1 for flag in (0x61,0x335,0x336))
    d.save_checkpoint('r04-submarine-theft')
    d.warp_to(11,14,'SlateportCity')
    d.fly_to('LilycoveCity')
    d.talk(61,12,'RIGHT')
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.go(70,6); d.cross('UP','AquaHideout_1F')
    d.go(13,10)
    assert d.state()['map'] == 'AquaHideout_1F'
    assert (d.state()['x'],d.state()['y']) == (13,10)
    print('NATURAL AQUA GATE OPEN PASS',d.state())
    return d.save_checkpoint('r04-aqua-opened')


def aqua_master_ball():
    """Solve the real pad puzzle and collect the two left-hand item balls."""
    import aqua_warp_driver as pads
    assert d.state()['map'] == 'AquaHideout_B1F'
    assert d.value('(int)CountTotalItemQuantityInBag(1)') == 0
    assert d.value('(int)FlagGet(0x464)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    for index in (4,7,5,9,13,17,19,22):
        pads.activate(index)
    assert (d.state()['x'],d.state()['y']) == (23,10)
    # The Nugget below the Master Ball blocks the approach from below.
    d.talk(15,11,'UP'); d.talk(15,10,'UP')
    assert d.value('(int)CountTotalItemQuantityInBag(1)') == 1
    assert d.value('(int)FlagGet(0x464)') == 1
    return d.save_checkpoint('r04-master-ball')


def wailmer_gate_closed():
    """Use the earlier natural save to measure the sea barrier before Matt."""
    assert d.state()['map'] == 'AquaHideout_1F'
    assert d.value('(int)FlagGet(0x70)') == 0
    d.RUN_WILD=True
    d.warp_to(13,27,'LilycoveCity')
    d.go(75,12); d.advance('RIGHT',96,32); d.settle()
    assert d.state()['map'] == 'LilycoveCity'
    assert (d.state()['x'],d.state()['y']) == (75,12)
    assert d.value('(int)FlagGet(0x70)') == 0
    print('NATURAL WAILMER GATE CLOSED PASS',d.state())
    return d.save_checkpoint('r04-wailmer-blocked')


def aqua_to_matt():
    import aqua_warp_driver as pads
    assert d.state()['map'] == 'AquaHideout_B1F'
    assert d.value('(int)CountTotalItemQuantityInBag(1)') == 1
    assert d.value('(int)FlagGet(0x70)') == 0
    d.RUN_WILD=True; d.HEAL_ITEMS=(21,22,13)
    for index in (11,24,20,18,14,12,10):
        pads.activate(index)
    d.warp_to(18,1,'AquaHideout_B2F')
    pads.activate(3)
    d.warp_to(3,3,'AquaHideout_B1F')
    d.warp_to(12,1,'AquaHideout_B2F')
    pads.activate(4)
    d.go(25,19,dialogue_limit=80000)
    assert d.value('(int)HasTrainerBeenFought(30)') == 0
    assert d.value('(int)FlagGet(0x70)') == 0
    return d.save_checkpoint('r04-matt-ready')


def matt_battle():
    assert d.field_ready(d.state()) and d.state()['map'] == 'AquaHideout_B2F'
    assert d.value('(int)HasTrainerBeenFought(30)') == 0
    assert d.value('(int)FlagGet(0x70)') == 0
    assert d.value('(int)FlagGet(0x354)') == 0
    d.HEAL_ITEMS=(21,22,13)
    d.talk(24,19,'LEFT',100000)
    assert d.state()['map'] == 'AquaHideout_B2F'
    assert d.memory('gBattleOutcome',1)[0] == 1
    assert d.value('(int)HasTrainerBeenFought(30)') == 1
    assert d.value('(int)FlagGet(0x70)') == 1
    assert d.value('(int)FlagGet(0x354)') == 1
    return d.save_checkpoint('r04-matt')


def devon_exp_share():
    """Receive the pending letter reward and equip it through the item menu."""
    assert d.state()['map'] == 'RustboroCity_DevonCorp_3F'
    assert d.value('(int)FlagGet(0xbd)') == 1
    assert d.value('(int)FlagGet(0x110)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(182)') == 0
    d.talk(14,5,'RIGHT')
    assert d.value('(int)FlagGet(0x110)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(182)') == 1
    d.give_item(182,1)
    assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),12,0)') == 182
    assert d.value('(int)CountTotalItemQuantityInBag(182)') == 0
    return d.save_checkpoint('r04-exp-share-equipped')


def surf_speed_regression():
    """Measure the old overlong pulse, then keep the corrected batch on water."""
    assert d.state()['map'] == 'PetalburgCity'
    d.go(7,20); d.talk(7,20,'LEFT')
    assert (d.state()['x'],d.state()['y']) == (6,20)
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.advance('LEFT',56,36); d.settle()
    old=d.state()
    print('OLD WALKING PULSE ON SURF',old,d.memory('gPlayerAvatar',1)[0])
    assert (old['x'],old['y']) != (3,20), 'Expected the old three-tile pulse to overshoot'
    d.go(7,20); d.talk(7,20,'LEFT')
    assert (d.state()['x'],d.state()['y']) == (6,20)
    d.go(3,20)
    assert (d.state()['x'],d.state()['y']) == (3,20)
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.go(6,20)
    assert (d.state()['x'],d.state()['y']) == (6,20)
    assert d.memory('gPlayerAvatar',1)[0]&8
    d.go(7,20)
    assert not d.memory('gPlayerAvatar',1)[0]&8
    print('NATURAL SURF BATCH COORDINATES PASS',d.state())
    return d.save_checkpoint('r03-surf-speed')


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
