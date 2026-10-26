"""Isolated synthetic animation terminators; does not credit campaign progress."""
from pathlib import Path
import json
import shutil
from frontier_layout import measure
from process_watchdog import run_logged


def main():
    project=Path(__file__).resolve().parents[2]
    scratch=project/'build/animation-terminators'
    for name in ('build','roms','saves'):(scratch/name).mkdir(parents=True,exist_ok=True)
    for name in ('emerald-pc-diagnostic.exe','SDL2.dll'):
        shutil.copy2(project/'build'/name,scratch/'build'/name)
    roms=list((project/'roms').glob('*.gba'));assert len(roms)==1
    shutil.copy2(roms[0],scratch/'roms/test.gba')
    save=scratch/'saves/emerald-pc-diagnostic.sav'
    save.write_bytes((project/'build/natural-campaign/r09-factory-open-loss.sav').read_bytes())
    saved=save.read_bytes()
    layout=json.loads(measure(project,scratch).read_text())
    inputs=scratch/'input.txt'
    inputs.write_text(''.join(f'{frame} {frame+1} A\n' for frame in range(1000,1181,45)))
    script=scratch/'terminators.gdb'
    script.write_text(f'''set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT {inputs.as_posix()}
set environment EMERALD_PC_STOP_FRAME 2000
break Port_ExitCleanly
run
python
import gdb
assert gdb.newest_frame().name()=='Port_ExitCleanly'
gdb.execute('set $sprite = (unsigned int)AllocZeroed({layout['Sprite_size']})')
address=int(gdb.parse_and_eval('$sprite'));assert address
for function in ('VerticalShakeTwice','VerticalShakeLowTwice'):
    gdb.execute('set *(short *)($sprite+{layout['Sprite_data']+10}) = 3')
    gdb.execute('set *(short *)($sprite+{layout['Sprite_y2']}) = 99')
    gdb.execute('set *(unsigned int *)($sprite+{layout['Sprite_callback']}) = 0')
    gdb.execute('call (void)'+function+'((void *)$sprite)')
    assert int(gdb.parse_and_eval('*(short *)($sprite+{layout['Sprite_y2']})'))==0
    assert int(gdb.parse_and_eval('*(unsigned int *)($sprite+{layout['Sprite_callback']})'))==int(gdb.parse_and_eval('(unsigned int)&WaitAnimEnd'))
    print('SYNTHETIC ANIMATION TERMINATOR PASS',function)
gdb.execute('call (void)Free((void *)$sprite)')
end
continue
quit
''',encoding='utf-8')
    log=scratch/'terminators.log'
    result=run_logged(['gdb','-batch','-x',str(script),str(scratch/'build/emerald-pc-diagnostic.exe')],project,log,'PC diagnostic: frame=')
    output=log.read_text(errors='replace')
    assert result==0 and output.count('SYNTHETIC ANIMATION TERMINATOR PASS')==2
    assert 'received signal' not in output and 'exited normally' in output
    assert save.read_bytes()==saved
    print('PASS isolated animation terminators; private save unchanged')


if __name__=='__main__':main()
