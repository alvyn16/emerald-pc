"""Measured route actions after the real intro; keys and read-only checkpoints."""
import campaign_driver as d


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
