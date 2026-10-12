"""Isolated capture fixture: accept nickname UI, return to battle, then field."""
import argparse
from pathlib import Path
import shutil
from game_fixture import prepare, run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,help='Optional prior diagnostic executable for regression comparison')
    options=parser.parse_args()
    scratch,commands=prepare('caught-naming-teardown','31001 31002 NONE\n')
    if options.exe:
        shutil.copy2(options.exe,scratch/'build/emerald-pc-diagnostic.exe')
    # This controlled setup is independent of the natural campaign. The ball,
    # wild encounter and party are explicit fixtures; the nickname UI uses keys.
    commands+='''
call (void)CreateMon((void *)&gEnemyParty,309,12,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
call (int)AddBagItem(1,1)
call (void)BattleSetup_StartWildBattle()
break MainState_Exit
commands
silent
printf "CAUGHT NAMING EXIT frame=%u\\n", sDiagnosticFrame
continue
end
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f"d.SCRATCH=Path({scratch.as_posix()!r})\n"+'''
d.CATCH_SPECIES={309}
d.settle(16000)
assert d.memory('gBattleOutcome',1)[0] == 7
assert d.state()['party'] == 2
assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),11,0)') == 309
assert d.value('*(unsigned int *)&sNamingScreen') == 0
assert d.state()['callback'] == 'CB2_Overworld'
assert d.value('(int)CountTotalItemQuantityInBag(1)') == 0
print('CAUGHT NAMING BATTLE FIELD RETURN PASS',d.state())
end
continue
quit
'''
    log=run(scratch,commands,['CAUGHT NAMING EXIT','CAUGHT NAMING BATTLE FIELD RETURN PASS'])
    print('PASS caught naming teardown:',log)


if __name__ == '__main__':
    main()
