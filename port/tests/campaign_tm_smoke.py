"""Controlled HM teaching must use the bag/party/summary UI and retain the HM."""
from game_fixture import prepare, run


def main():
    scratch,commands=prepare('campaign-hm-teaching','31001 31002 NONE\n')
    # Isolated compatible party and owned HM; no natural campaign credit.
    commands+='''
call (void)CreateMon((void *)&gPlayerParty,284,25,32,0,0,0,0)
call (int)AddBagItem(344,1)
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
'''+f'd.SCRATCH=Path({scratch.as_posix()!r})\n'+'''
d.teach_tm(344,0)
assert d.value('(int)CountTotalItemQuantityInBag(344)') == 1
assert 249 in [d.value(f'(int)GetMonData3((void *)&gPlayerParty,{13+i},0)') for i in range(4)]
assert d.field_ready(d.state())
print('HM TEACHING FIELD RETURN PASS',d.state())
end
continue
quit
'''
    print('PASS Rock Smash taught through menus:',run(scratch,commands,['HM TEACHING FIELD RETURN PASS']))


if __name__ == '__main__':
    main()
