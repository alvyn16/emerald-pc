"""Capture aligned intro/starter fixtures using an isolated diagnostic executable."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
from process_watchdog import run_logged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--label', default='after')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.label):
        raise SystemExit('Label must be a simple filename component')
    project = Path(__file__).resolve().parents[2]
    source = (args.exe or project / 'build/emerald-pc-diagnostic.exe').resolve()
    if not source.is_relative_to((project / 'build').resolve()):
        raise SystemExit('Use a local diagnostic executable inside build/')
    scratch = project / 'build' / ('visual-' + args.label)
    for name in ('build', 'roms', 'saves'):
        (scratch / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, scratch / 'build/emerald-pc-diagnostic.exe')
    shutil.copy2(project / 'build/SDL2.dll', scratch / 'build/SDL2.dll')
    roms = list((project / 'roms').glob('*.gba'))
    if len(roms) != 1:
        raise SystemExit('Exactly one user-provided legal ROM is required')
    shutil.copy2(roms[0], scratch / 'roms/test.gba')
    subprocess.run([sys.executable, str(project / 'port/tests/gameplay_smoke.py'),
                    str(scratch / 'input.txt')], check=True)
    with (scratch / 'input.txt').open('a') as output:
        output.write('30600 30601 A\n')
    relative = scratch.relative_to(project).as_posix()
    metadata = r'''
printf "VISUAL frame=%u DISPCNT=%04x BG2CNT=%04x PA/PB/PC/PD=%d/%d/%d/%d XY=%08x/%08x\n", sDiagnosticFrame, *(unsigned short *)0x04000000, *(unsigned short *)0x0400000c, *(short *)0x04000020, *(short *)0x04000022, *(short *)0x04000024, *(short *)0x04000026, *(unsigned int *)0x04000028, *(unsigned int *)0x0400002c
info symbol *(void **)((char *)&gMain + 4)
'''
    intro = f'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
unset environment EMERALD_PC_INPUT_SCRIPT
set environment EMERALD_PC_STOP_FRAME 2665
break Port_ExitCleanly
run
{metadata}
dump binary memory {relative}/intro.raw &sPixels ((char *)&sPixels)+153600
continue
quit
'''
    template = (project / 'build/wild-battle-regression/test.gdb').read_text()
    starter = template.split('call (void)CreateMon')[0]
    starter = starter.replace('build/wild-battle-regression/', relative + '/')
    starter += f'''
call (void)SetMainCallback2((void *)CB2_ChooseStarter)
set var sStopFrame = 30800
return
continue
{metadata}
dump binary memory {relative}/starter.raw &sPixels ((char *)&sPixels)+153600
continue
quit
'''
    intro2400 = intro.replace('2665', '2400').replace('intro.raw', 'intro-2400.raw')
    for name, commands in (('intro-2400', intro2400), ('intro', intro), ('starter', starter)):
        (scratch / 'saves/emerald-pc-diagnostic.sav').write_bytes(b'\xff' * 131072)
        script, log = scratch / (name + '.gdb'), scratch / (name + '.log')
        script.write_text(commands, encoding='ascii')
        result = run_logged(['gdb', '-batch', '-x', str(script),
                              str(scratch / 'build/emerald-pc-diagnostic.exe')],
                             project, log, 'PC diagnostic: frame=')
        text = log.read_text(errors='replace')
        if result or 'received signal' in text or 'exited normally' not in text:
            raise SystemExit(f'Visual fixture failed: {log}')
        raw = (scratch / (name + '.raw')).read_bytes()
        if len(raw) != 240 * 160 * 4:
            raise SystemExit('Unexpected framebuffer size')
        from PIL import Image
        Image.frombytes('RGBA', (240, 160), raw, 'raw', 'BGRA').save(scratch / (name + '.png'))
    print(f'PASS visual fixtures: intro 2400/2665, starter confirmation 30800; {scratch}')


if __name__ == '__main__':
    main()
