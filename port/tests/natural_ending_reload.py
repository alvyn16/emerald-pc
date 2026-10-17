"""Continue the natural Champion save and validate its persisted Hall of Fame."""
from pathlib import Path
import json
import shutil
from process_watchdog import run_logged


def main():
    project=Path(__file__).resolve().parents[2]
    source=project/'build/natural-campaign'
    scratch=project/'build/natural-campaign-ending-reload'
    expected=json.loads((source/'r05-the-end.json').read_text(encoding='utf-8'))
    saved=(source/'r05-the-end.sav').read_bytes()
    assert expected['game_clear'] == 1 and expected['badges'] == [1]*8
    for directory in ('build','roms','saves'):
        (scratch/directory).mkdir(parents=True,exist_ok=True)
    for name in ('emerald-pc-diagnostic.exe','SDL2.dll'):
        shutil.copy2(project/'build'/name,scratch/'build'/name)
    roms=list((project/'roms').glob('*.gba'))
    assert len(roms) == 1
    shutil.copy2(roms[0],scratch/'roms/test.gba')
    save=scratch/'saves/emerald-pc-diagnostic.sav'
    save.write_bytes(saved)
    inputs=scratch/'input.txt'
    inputs.write_text(''.join(f'{frame} {frame+1} A\n' for frame in range(1000,1181,45)),encoding='ascii')
    script=scratch/'reload.gdb'
    script.write_text(f'''set pagination off
set confirm off
set python print-stack full
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT {inputs.as_posix()}
set environment EMERALD_PC_STOP_FRAME 10000
break Port_ExitCleanly
run
python
import sys,json,gdb
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
d.SCRATCH=Path({scratch.as_posix()!r})
assert gdb.newest_frame().name() == 'Port_ExitCleanly'
actual=d.state()
assert d.field_ready(actual), actual
assert actual['map'] == 'LittlerootTown_BrendansHouse_2F', actual
assert d.value('*(unsigned short *)&gSaveFileStatus') == 1
assert d.value('(int)FlagGet(0x864)') == 1
assert [d.value(f'(int)FlagGet({{0x867+i}})') for i in range(8)] == [1]*8
expected={expected!r}
assert actual['party'] == len(expected['team'])
for slot,mon in enumerate(expected['team']):
    address=f'(void *)((char *)&gPlayerParty+{{slot*100}})'
    assert d.value(f'(int)GetMonData3({{address}},11,0)') == mon['species']
    assert d.value(f'(int)GetMonData3({{address}},56,0)') == mon['level']
assert d.value('(unsigned char)LoadGameSave(3)') == 1, 'Hall of Fame checksum/load failed'
records=d.memory('gDecompressionBuffer',120)
for slot,mon in enumerate(expected['team']):
    packed=int.from_bytes(records[slot*20+8:slot*20+10],'little')
    assert packed&511 == mon['species'], (slot,packed,mon)
    assert packed>>9 == mon['level'], (slot,packed,mon)
Path({str(scratch/'reload.raw')!r}).write_bytes(d.memory('sPixels',153600))
Path({str(scratch/'reload.json')!r}).write_text(json.dumps(actual,indent=2),encoding='utf-8')
print('NATURAL POST-CREDITS CONTINUE AND HALL OF FAME PASS',actual,expected['team'])
end
continue
quit
''',encoding='utf-8')
    log=scratch/'reload.log'
    result=run_logged(['gdb','-batch','-x',str(script),str(scratch/'build/emerald-pc-diagnostic.exe')],
                      project,log,'PC diagnostic: frame=',timeout=180)
    output=log.read_text(errors='replace')
    assert result == 0 and 'NATURAL POST-CREDITS CONTINUE AND HALL OF FAME PASS' in output
    assert 'received signal' not in output and 'exited normally' in output
    assert save.read_bytes() == saved, 'Continue changed the saved game'
    print('Natural post-credits Continue and Hall of Fame PASS; save unchanged')


if __name__ == '__main__':
    main()
