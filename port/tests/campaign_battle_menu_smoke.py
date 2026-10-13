"""Controlled battle fixtures verify keyboard replacements and move refusal."""
from pathlib import Path
from game_fixture import prepare, run


def scenario(name,setup,checks,driver_setup=''):
    scratch,commands=prepare('campaign-menu-'+name,'31001 31002 NONE\n')
    commands+=setup+'''
call (void)BattleSetup_StartWildBattle()
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f'd.SCRATCH=Path({scratch.as_posix()!r})\n'+driver_setup+'''
d.settle(24000)
assert d.memory('gBattleOutcome',1)[0] == 1
assert d.state()['callback'] == 'CB2_Overworld'
'''+checks+f"\nprint('BATTLE MENU {name} PASS',d.state())\n"+'''
end
continue
quit
'''
    return run(scratch,commands,['BATTLE MENU '+name+' PASS'])


def main():
    # Explicit isolated setup: no campaign save or campaign credit.
    replacement=scenario('replacement','''
call (void)CreateMon((void *)&gPlayerParty,283,1,0,0,0,0,0)
call (void)CreateMon((void *)((char *)&gPlayerParty+100),309,25,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 2
call (void)CreateMon((void *)&gEnemyParty,286,12,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
''','''
assert d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)') == 0
assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),57,0)') > 0
''')
    # Splash-only Chansey isolates the move-learning UI from opponent tactics.
    refusal=scenario('status-move','''
call (void)CreateMon((void *)&gPlayerParty,309,20,32,0,0,0,0)
call (void)CreateMon((void *)&gEnemyParty,113,50,0,0,0,0,0)
call (void)SetMonMoveSlot((void *)&gEnemyParty,150,0)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,1)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,2)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,3)
set *(unsigned char *)&gEnemyPartyCount = 1
''','''
assert d.value('(int)GetMonData3((void *)&gPlayerParty,56,0)') >= 21
moves=[d.value(f'(int)GetMonData3((void *)&gPlayerParty,{13+i},0)') for i in range(4)]
assert 54 not in moves, 'Mist must not replace an attack'
assert 17 in moves and 55 in moves, 'Preserve Wing Attack and Water Gun'
''')
    upgrade=scenario('attack-upgrade','''
call (void)CreateMon((void *)&gPlayerParty,309,30,32,0,0,0,0)
call (void)CreateMon((void *)&gEnemyParty,113,80,0,0,0,0,0)
call (void)SetMonMoveSlot((void *)&gEnemyParty,150,0)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,1)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,2)
call (void)SetMonMoveSlot((void *)&gEnemyParty,0,3)
set *(unsigned char *)&gEnemyPartyCount = 1
''','''
assert d.value('(int)GetMonData3((void *)&gPlayerParty,56,0)') >= 31
moves=[d.value(f'(int)GetMonData3((void *)&gPlayerParty,{13+i},0)') for i in range(4)]
assert all(move in moves for move in (17,55,98)), 'Retain attacks and learn Quick Attack'
''')
    print('PASS replacement, status refusal and attack upgrade:',replacement,refusal,upgrade)


if __name__ == '__main__':
    main()
