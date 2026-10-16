"""Drive the Space Center's story encounters and party selection through UI."""
import campaign_driver as d


def upper_floor():
    assert d.state()['map'] == 'MossdeepCity_SpaceCenter_1F'
    assert d.value('(int)VarGet(0x405d)') == 2
    assert d.value('(int)VarGet(0x409f)') == 1
    assert d.value('(int)HasTrainerBeenFought(116)') == 0
    d.talk(13,3,'UP',80000)
    assert d.value('(int)HasTrainerBeenFought(116)') == 1
    assert d.value('(int)VarGet(0x409e)') == 2
    d.warp_to(13,1,'MossdeepCity_SpaceCenter_2F',100000)
    d.settle(120000)
    assert d.value('(int)VarGet(0x409f)') == 2
    for trainer in (588,589,590):
        assert d.value(f'(int)HasTrainerBeenFought({trainer})') == 1
    assert d.value('(int)FlagGet(0xcd)') == 0
    d.talk(2,8,'LEFT')
    assert d.value('(int)FlagGet(0xcd)') == 1
    d.go(3,8)
    return d.save_checkpoint('r04-steven-ready')


def wait_task(name):
    for _ in range(100):
        if d.value(f'(int)FuncIsActiveTask((void *){name})'):
            return
        d.advance('NONE',24)
    raise RuntimeError('Party selection task deadline: '+name)


def steven_battle():
    assert d.field_ready(d.state())
    assert d.state()['map'] == 'MossdeepCity_SpaceCenter_2F'
    assert d.value('(int)FlagGet(0xcd)') == 1
    assert d.value('(int)FlagGet(0x75)') == 0
    assert d.value('(int)VarGet(0x409f)') == 2
    d.go(2,8); d.advance('LEFT',24,4); d.advance('A',24,1)
    for _ in range(150):
        if d.state()['callback'] == 'CB2_UpdatePartyMenu':
            break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Steven did not open the party selection menu')
    assert d.memory('gPartyMenu',9)[8]&15 == 4
    assert d.memory('gSelectedOrderFromParty',6) == bytes(6)
    wait_task('Task_HandleChooseMonInput')
    # Select the actual Swampert, Pelipper and Castform in this natural party.
    for slot in (0,1,3):
        assert d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{slot*100}),57,0)') > 0
        d.select_party_slot(slot); d.advance('A',24,1)
        wait_task('Task_HandleSelectionMenuInput')
        assert d.value('(int)Menu_GetCursorPos()') == 0  # Enter
        d.advance('A',24,1)
        wait_task('Task_HandleChooseMonInput')
    assert list(d.memory('gSelectedOrderFromParty',6)) == [1,2,4,0,0,0]
    assert d.memory('gPartyMenu',10)[9] == 6  # Confirm
    d.advance('A',600,1); d.settle(120000)
    assert d.field_ready(d.state())
    assert d.state()['map'] == 'MossdeepCity_SpaceCenter_2F'
    assert d.value('(int)FlagGet(0x75)') == 1
    assert d.value('(int)VarGet(0x405d)') == 3
    assert d.value('(int)VarGet(0x409f)') == 3
    assert d.value('(int)VarGet(0x40c6)') == 1
    assert d.state()['party'] == 4  # Steven's party was removed again.
    return d.save_checkpoint('r04-steven-result')


def dive_gift():
    assert d.state()['map'] == 'MossdeepCity_SpaceCenter_2F'
    assert d.value('(int)FlagGet(0x75)') == 1
    assert d.value('(int)FlagGet(0x7b)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(346)') == 0
    assert d.value('(int)VarGet(0x40c6)') == 1
    d.warp_to(13,1,'MossdeepCity_SpaceCenter_1F')
    d.warp_to(7,9,'MossdeepCity')
    d.go(19,11); d.cross('UP','MossdeepCity_StevensHouse'); d.settle()
    assert d.value('(int)FlagGet(0x7b)') == 1
    assert d.value('(int)CountTotalItemQuantityInBag(346)') == 1
    assert d.value('(int)VarGet(0x40c6)') == 2
    # Pelipper's native learnset rejects Dive; the real starter can learn it.
    assert d.value('(unsigned int)CanMonLearnTMHM((void *)((char *)&gPlayerParty+100),57)') == 0
    d.teach_tm(346,0)
    assert d.value('(int)CountTotalItemQuantityInBag(346)') == 1
    return d.save_checkpoint('r04-dive-learned')
