"""Controlled double battle: choose a damaging move and its actual UI target."""
import json
from pathlib import Path
from game_fixture import prepare,run


def main():
    scratch,commands=prepare('campaign-double-target','31001 31002 NONE\n')
    decisions=scratch/'battle-choices.jsonl'; decisions.write_text('')
    # Isolated legal party and opponents; this does not grant campaign progress.
    commands+='''
call (void)CreateMon((void *)&gPlayerParty,284,25,32,0,0,0,0)
call (void)SetMonMoveSlot((void *)&gPlayerParty,189,0)
call (void)SetMonMoveSlot((void *)&gPlayerParty,55,1)
call (void)SetMonMoveSlot((void *)&gPlayerParty,45,2)
call (void)SetMonMoveSlot((void *)&gPlayerParty,193,3)
call (void)CreateMon((void *)((char *)&gPlayerParty+100),309,24,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 2
set *(unsigned short *)&gTrainerBattleOpponent_A = 649
set *(unsigned short *)&gTrainerBattleOpponent_B = 194
set *(unsigned char *)&gNoOfApproachingTrainers = 2
call (void)BattleSetup_StartTrainerBattle()
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f'd.SCRATCH=Path({scratch.as_posix()!r})\n'+'''
d.settle(30000)
assert d.memory('gBattleOutcome',1)[0] == 1
assert d.state()['callback'] == 'CB2_Overworld'
print('DOUBLE TARGET FIELD RETURN PASS',d.state())
end
continue
quit
'''
    log=run(scratch,commands,['DOUBLE TARGET FIELD RETURN PASS'])
    choices=[json.loads(line) for line in decisions.read_text().splitlines()]
    assert any(c['kind']=='move' and c['battler']==0 and c['move']==189 and c['target']==3 for c in choices)
    assert any(c['kind']=='move' and c['battler']==2 and c['move']==17 and c['target']==1 for c in choices)
    assert any(c['kind']=='target' and c['battler']==0 and c['target']==3 for c in choices)
    assert any(c['kind']=='target' and c['battler']==2 and c['target']==1 for c in choices)
    print('PASS double Ground/Flying moves and confirmed menu targets:',log)


if __name__ == '__main__':
    main()
