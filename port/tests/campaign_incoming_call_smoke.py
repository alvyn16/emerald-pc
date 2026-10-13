"""An incoming Match Call pauses walking and is acknowledged through keys."""
from game_fixture import prepare, run


def main():
    scratch,commands=prepare('campaign-incoming-call','31001 31002 NONE\n')
    # Controlled call setup; no campaign flags or progress are granted.
    commands+='''
set *(unsigned short *)((char *)&sMatchCallState+4) = *(unsigned short *)&sMatchCallTrainers
call (void)StartMatchCall()
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f'd.SCRATCH=Path({scratch.as_posix()!r})\n'+'''
assert d.state()['locked'] == 1 and d.state()['script'] == 2
before=d.state()
d.walk(before['x']+1,before['y'],limit=2)
assert d.state()['locked'] == 1
assert (d.state()['x'],d.state()['y']) == (before['x'],before['y'])
d.settle(5000)
assert not d.value('(int)IsMatchCallTaskActive()')
d.go(before['x']+1,before['y'])
assert (d.state()['x'],d.state()['y']) == (before['x']+1,before['y'])
print('INCOMING CALL WALK RESUME PASS',d.state())
end
continue
quit
'''
    print('PASS locked walking pauses for Match Call:',run(scratch,commands,['INCOMING CALL WALK RESUME PASS']))


if __name__ == '__main__':
    main()
