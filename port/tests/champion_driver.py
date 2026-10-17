"""Drive the Champion and ending through keys; observe outcomes without grants."""
import json
import gdb
import campaign_driver as d


def capture(name):
    (d.SCRATCH/(name+'.raw')).write_bytes(d.memory('sPixels',153600))
    (d.SCRATCH/(name+'.sav')).write_bytes(
        (d.SCRATCH/'saves/emerald-pc-diagnostic.sav').read_bytes())
    facts=d.state()
    facts['game_clear']=d.value('(int)FlagGet(0x864)')
    facts['badges']=[d.value(f'(int)FlagGet({0x867+i})') for i in range(8)]
    facts['team']=[dict(species=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),11,0)'),
                        level=d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{i*100}),56,0)'))
                   for i in range(facts['party'])]
    (d.SCRATCH/(name+'.json')).write_text(json.dumps(facts,indent=2),encoding='utf-8')
    print('NATURAL ENDING OBSERVATION',name,facts)


def wallace():
    assert d.state()['map'] == 'EverGrandeCity_Hall4'
    assert d.value('(int)FlagGet(0x864)') == 0
    outcomes=[]

    class Outcome(gdb.Breakpoint):
        def stop(self):
            outcomes.append(d.memory('gBattleOutcome',1)[0])
            return False

    observer=Outcome('CB2_EndTrainerBattle',internal=True)
    observer.silent=True
    previous=d.REST_SPECIES,d.REVIVE_SPECIES
    try:
        d.REST_SPECIES=set(); d.REVIVE_SPECIES={406}
        for step in range(3):
            if d.state()['map'] != 'EverGrandeCity_Hall4':
                break
            d.advance('UP',120,60)
        assert d.state()['map'] == 'EverGrandeCity_ChampionsRoom'

        def finished(current):
            return (d.value('(int)FuncIsActiveTask((void *)Task_Hof_ExitOnKeyPressed)')
                    or (outcomes and d.field_ready(current)))

        result=d.settle(240000,stop_when=finished)
        assert outcomes, 'Champion battle outcome was not observed'
        print('NATURAL WALLACE BATTLE OUTCOME',outcomes,result)
        if outcomes[-1] != 1:
            assert outcomes[-1] == 2 and result['map'] == 'EverGrandeCity'
            assert d.value('(int)FlagGet(0x864)') == 0
            d.save_checkpoint('r05-wallace-loss')
            return
        assert d.value('(int)FlagGet(0x864)') == 1
        assert d.value('(int)FuncIsActiveTask((void *)Task_Hof_ExitOnKeyPressed)')
        pointer=d.value('*(unsigned int *)&sHofMonPtr')
        assert pointer
        records=bytes(gdb.selected_inferior().read_memory(pointer,120))
        for slot in range(result['party']):
            packed=int.from_bytes(records[slot*20+8:slot*20+10],'little')
            mon=f'(void *)((char *)&gPlayerParty+{slot*100})'
            assert packed&511 == d.value(f'(int)GetMonData3({mon},11,0)')
            assert packed>>9 == d.value(f'(int)GetMonData3({mon},56,0)')
        capture('r05-hall-of-fame')
        print('NATURAL WALLACE AND HALL OF FAME PASS')
        credits()
    finally:
        observer.delete()
        d.REST_SPECIES,d.REVIVE_SPECIES=previous


def credits():
    """Let the real ending run without skipping The End with an A pulse."""
    assert d.value('(int)FuncIsActiveTask((void *)Task_Hof_ExitOnKeyPressed)')
    d.advance('A',120,1)
    d.settle(10000,stop_when=lambda current: current['callback'] == 'CB2_Credits')
    assert d.state()['callback'] == 'CB2_Credits'
    print('NATURAL CREDITS ENTER PASS',d.state())
    for step in range(400):
        if d.value('(int)FuncIsActiveTask((void *)Task_CreditsTheEnd6)'):
            d.advance('NONE',64)
            assert d.value('(int)FlagGet(0x864)') == 1
            capture('r05-the-end')
            assert any(d.memory('sPixels',153600)[i:i+3] != b'\0\0\0'
                       for i in range(0,153600,4)), 'The End capture is blank'
            print('NATURAL THE END PASS',d.state())
            return
        d.advance('NONE',240)
    raise RuntimeError('Credits deadline: '+str(d.state()))
