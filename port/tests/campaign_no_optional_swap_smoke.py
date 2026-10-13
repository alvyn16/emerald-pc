"""Trainer's next-mon question must decline via keys and retain the lead."""
from game_fixture import prepare,run


def main():
    scratch,commands=prepare('campaign-no-optional-swap','31001 31002 NONE\n')
    commands+='''
call (void)CreateMon((void *)&gPlayerParty,284,30,32,0,0,0,0)
call (void)CreateMon((void *)((char *)&gPlayerParty+100),309,24,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 2
set $partner_exp = (int)GetMonData3((void *)((char *)&gPlayerParty+100),25,0)
set *(unsigned short *)&gTrainerBattleOpponent_A = 194
call (void)BattleSetup_StartTrainerBattle()
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f'd.SCRATCH=Path({scratch.as_posix()!r})\n'+'''
d.settle(20000)
assert d.memory('gBattleOutcome',1)[0] == 1
assert d.state()['callback'] == 'CB2_Overworld'
assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),25,0)') == d.value('$partner_exp')
assert d.value('(int)GetMonData3((void *)&gPlayerParty,11,0)') == 284
print('OPTIONAL SWAP DECLINED PASS',d.state())
end
continue
quit
'''
    print('PASS trainer question retains lead:',run(scratch,commands,['OPTIONAL SWAP DECLINED PASS']))


if __name__ == '__main__':
    main()
