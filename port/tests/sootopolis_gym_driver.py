"""Solve Sootopolis ice from live tile observations, then execute only keys."""
import gdb
import campaign_driver as d


def ice_path(tiles,start,end):
    """Visit each thin-ice tile once, with connectivity/degree pruning."""
    neighbors={p:{q for q in ((p[0]+1,p[1]),(p[0]-1,p[1]),
                              (p[0],p[1]+1),(p[0],p[1]-1)) if q in tiles}
               for p in tiles}
    def search(current,left):
        if not left:
            return [current] if current == end else None
        if current == end:
            return None
        available=left|{current}
        if any(len(neighbors[p]&available) < (1 if p == end else 2) for p in left):
            return None
        seen={current}; queue=[current]
        while queue:
            for point in (neighbors[queue.pop()]&available)-seen:
                seen.add(point); queue.append(point)
        if seen != available:
            return None
        for point in sorted(neighbors[current]&left,
                            key=lambda p:(len(neighbors[p]&left),p)):
            path=search(point,left-{point})
            if path:
                return [current]+path
        return None
    result=search(start,set(tiles)-{start})
    assert result and len(result) == len(tiles) and len(set(result)) == len(tiles)
    return result


def ice_step(x,y):
    origin=d.state(); dx,dy=x-origin['x'],y-origin['y']
    assert abs(dx)+abs(dy) == 1
    button={(1,0):'RIGHT',(-1,0):'LEFT',(0,1):'DOWN',(0,-1):'UP'}[(dx,dy)]
    for _ in range(4):
        d.advance(button,32,4); d.settle(10000)
        state=d.state()
        assert state['map'] == 'SootopolisCity_Gym_1F'
        if (state['x'],state['y']) == (x,y):
            assert d.value('(int)MapGridGetMetatileBehaviorAt(%d,%d)'%(x+7,y+7)) == 0x27
            return
        # A short pulse may only turn the player. Retry only if no step occurred.
        assert (state['x'],state['y']) == (origin['x'],origin['y'])
    raise RuntimeError('Ice movement deadline: '+str(d.state()))


def board(bottom,top,count,complete):
    tiles={(x,y) for y in range(top,bottom+1) for x in range(3,14)
           if d.value('(int)MapGridGetMetatileBehaviorAt(%d,%d)'%(x+7,y+7)) == 0x26
           and d.value('(int)MapGridGetCollisionAt(%d,%d)'%(x+7,y+7)) == 0}
    assert len(tiles) == count, tiles
    path=ice_path(tiles,(8,bottom),(8,top))
    for x,y in path:
        ice_step(x,y)
    assert d.value('(int)VarGet(0x4022)') == complete
    print('NATURAL SOOTOPOLIS ICE BOARD PASS',count,path,d.state())


def puzzle():
    assert d.state()['map'] == 'SootopolisCity_Gym_1F'
    assert d.value('(int)VarGet(0x4022)') == 1
    d.go(8,20)
    for bottom,top,count,complete in ((19,17,7,9),(14,12,19,29),(9,6,38,68)):
        board(bottom,top,count,complete)
        if complete != 68:
            d.go(8,15 if complete == 9 else 10)
    d.go(8,3)
    return d.save_checkpoint('r04-juan-ready')


def juan():
    assert d.state()['map'] == 'SootopolisCity_Gym_1F'
    assert d.value('(int)FlagGet(0x86e)') == 0
    assert d.value('(int)HasTrainerBeenFought(272)') == 0
    assert d.value('(int)FlagGet(0x4f7)') == 0
    assert d.value('(int)FlagGet(0xac)') == 0
    d.HEAL_ITEMS=(21,22,13)
    d.talk(8,3,'UP',180000)
    assert d.value('*(unsigned char *)&gBattleOutcome') == 1, d.state()
    assert d.value('(int)HasTrainerBeenFought(272)') == 1
    assert all(d.value('(int)FlagGet(%d)'%(0x867+i)) for i in range(8))
    assert d.value('(int)FlagGet(0x4f7)') == 1
    assert d.value('(int)FlagGet(0xac)') == 1
    assert d.value('(int)VarGet(0x405e)') == 6
    assert d.value('(int)CountTotalItemQuantityInBag(291)') == 1
    print('NATURAL JUAN VICTORY PASS',d.state())
    return d.save_checkpoint('r04-juan-win')


def earthquake_prep():
    """Use the real Move Deleter to free an HM slot, then consume the owned TM26."""
    assert d.state()['map'] == 'SootopolisCity'
    assert d.value('(int)FlagGet(0x86e)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(314)') == 1
    assert [d.value('(int)GetMonData3((void *)&gPlayerParty,%d,0)'%(13+i))
            for i in range(4)] == [249,291,70,57]
    d.fly_to('LilycoveCity')
    d.go(36,7); d.cross('UP','LilycoveCity_MoveDeletersHouse')
    d.go(4,5); d.advance('UP',24,4); d.advance('A',24,1)
    for _ in range(200):
        if (d.state()['callback'] == 'CB2_UpdatePartyMenu'
                and d.value('(int)FuncIsActiveTask((void *)Task_HandleChooseMonInput)')):
            break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Move Deleter party deadline: '+str(d.state()))
    d.select_party_slot(0); d.advance('A',24,1)
    for _ in range(100):
        if d.value('(int)FuncIsActiveTask((void *)Task_HandleReplaceMoveInput)'):
            break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Move Deleter summary deadline: '+str(d.state()))
    pointer=d.value('*(unsigned int *)&sMonSummaryScreen')
    assert pointer
    for _ in range(6):
        cursor=bytes(gdb.selected_inferior().read_memory(pointer+0x40c6,1))[0]
        if cursor == 1:
            break
        d.advance('DOWN' if cursor < 1 else 'UP',24,1)
    assert bytes(gdb.selected_inferior().read_memory(pointer+0x40c6,1))[0] == 1
    d.advance('A',24,1); d.settle(20000)
    assert [d.value('(int)GetMonData3((void *)&gPlayerParty,%d,0)'%(13+i))
            for i in range(4)] == [249,70,57,0]
    print('NATURAL MOVE DELETER DIVE PASS',d.state())
    d.teach_tm(314,0)
    assert [d.value('(int)GetMonData3((void *)&gPlayerParty,%d,0)'%(13+i))
            for i in range(4)] == [249,70,57,89]
    assert d.value('(int)CountTotalItemQuantityInBag(314)') == 0
    print('NATURAL EARTHQUAKE PREP PASS',d.state())
    return d.save_checkpoint('r04-earthquake-learned')


def juan_tactical():
    """Reset Luvdisc's debuffs by switching, then use owned battle items via Bag."""
    assert d.value('(int)CountTotalItemQuantityInBag(75)') == 2
    assert d.value('(int)CountTotalItemQuantityInBag(77)') == 1
    original=d.battle_button
    phase='first-opponent'
    def choose():
        nonlocal phase
        battle=d.memory('gBattleMons',352)
        species=int.from_bytes(battle[:2],'little')
        controller=d.value('*(unsigned int *)&gBattlerControllerFuncs')
        function=gdb.execute('info symbol %d'%controller,to_string=True).split(' in ')[0]
        instruction=d.value('(unsigned int)gBattlescriptCurrInstr')
        opcode=bytes(gdb.selected_inferior().read_memory(instruction,1))[0] if instruction else None
        if phase == 'first-opponent' and d.memory('gBattleResults',2)[1] == 1:
            if function == 'PlayerHandleYesNoInput':
                return 'UP' if d.memory('gMultiUsePlayerCursor',1)[0] else 'A'
            if opcode == 0x67:
                return 'A'  # Close the announcement before a cursor can respond.
        if phase == 'first-opponent' and species == 310:  # Pelipper actually sent out.
            phase='return-swamp'
            print('NATURAL JUAN SWITCH OUT',d.state())
        if phase == 'return-swamp' and species == 285:
            phase='boost'
            print('NATURAL JUAN SWITCH BACK',list(battle[24:32]),d.state())
        if function == 'HandleInputChooseAction':
            if phase == 'return-swamp':
                return d.cursor_button(d.memory('gActionSelectionCursor',1)[0],2)
            hp=int.from_bytes(battle[40:42],'little')
            maximum=int.from_bytes(battle[44:46],'little')
            if phase == 'boost' and species == 285 and not d.HEAL_PLAN and hp*2 > maximum:
                item=75 if battle[25] < 8 else 77 if battle[27] < 7 else None
                # A spare Accuracy X is used only if the opponent gained evasion.
                if item is None and battle[88+31] > 6:
                    item=78
                quantity=d.value('(int)CountTotalItemQuantityInBag(%d)'%item) if item else 0
                if quantity:
                    slot=int.from_bytes(d.memory('gBattlerPartyIndexes',2),'little')
                    d.HEAL_PLAN.update(item=item,quantity=quantity,field_slot=slot)
                    print('NATURAL JUAN BAG PLAN',item,list(battle[24:32]),d.state()['frame'])
        return original()
    try:
        d.battle_button=choose
        result=juan()
        assert phase == 'boost'
        assert d.value('(int)CountTotalItemQuantityInBag(75)') == 0
        assert d.value('(int)CountTotalItemQuantityInBag(77)') == 0
        print('NATURAL JUAN TACTICAL PASS',result)
        return result
    finally:
        d.battle_button=original


def tactical_shop():
    assert d.state()['map'] == 'SootopolisCity'
    assert d.value('(int)FlagGet(0x86e)') == 0
    assert d.value('(int)CountTotalItemQuantityInBag(21)') == 0
    d.fly_to('LilycoveCity')
    d.go(27,7); d.cross('UP','LilycoveCity_DepartmentStore_1F')
    d.warp_to(16,1,'LilycoveCity_DepartmentStore_2F')
    d.buy_item(21,4,position=(10,4),facing='DOWN')
    d.warp_to(13,1,'LilycoveCity_DepartmentStore_3F')
    for item,quantity in ((75,2),(77,1),(78,1)):
        assert d.value('(int)CountTotalItemQuantityInBag(%d)'%item) == 0
        d.buy_item(item,quantity,position=(10,4),facing='UP')
    print('NATURAL TACTICAL SHOP PASS',d.state())
    return d.save_checkpoint('r04-juan-tactical-items')
