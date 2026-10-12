"""Reproduce R01 with actual keyboard menus, paths and battles from a blank save."""
from pathlib import Path
import shutil
import sys
import argparse
import gameplay_smoke
from process_watchdog import run_logged


def main():
    project=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=("r01","r02-devon","r02-steven"),default="r01")
    phase=parser.parse_args().phase
    scratch=project/("build/natural-campaign-replay" if phase == "r01" else "build/natural-campaign-replay-"+phase)
    for directory in ("build","roms","saves"):
        (scratch/directory).mkdir(parents=True,exist_ok=True)
    for filename in ("emerald-pc-diagnostic.exe","SDL2.dll"):
        shutil.copy2(project/"build"/filename,scratch/"build"/filename)
    roms=list((project/"roms").glob("*.gba"))
    assert len(roms)==1, "Exactly one legal ROM is required"
    shutil.copy2(roms[0],scratch/"roms/test.gba")
    save=scratch/"saves/emerald-pc-diagnostic.sav"
    if save.exists():
        shutil.copy2(save,scratch/"previous-replay.sav")
    checkpoint={'r02-devon':'r02-roxanne','r02-steven':'r02-brawly'}
    save.write_bytes(b"\xff"*131072 if phase == "r01" else
                     (project/('build/natural-campaign/'+checkpoint[phase]+'.sav')).read_bytes())
    inputs=scratch/"input.txt"
    previous=sys.argv
    try:
        sys.argv=["gameplay_smoke.py",str(inputs)]
        if phase == "r01":
            gameplay_smoke.main()
        else:
            inputs.write_text("".join(f"{frame} {frame+1} A\n" for frame in range(1000,8000,45)))
    finally:
        sys.argv=previous
    script=scratch/"campaign.gdb"
    actions='''route.meet_may()
route.rescue_birch()
route.rival_and_dex()''' if phase == "r01" else '''d.RUN_WILD=True
d.settle(30000)
assert d.state()['map'] == 'RustboroCity_Gym'
d.go(5,19); d.cross('DOWN','RustboroCity')
route.cut_peeko_and_pokenav()''' if phase == 'r02-devon' else '''d.RUN_WILD=True
d.settle(30000)
route.steven_letter()
route.sail_to_slateport()
d.save_checkpoint('r02-slateport-arrival')'''
    script.write_text(f'''set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT {inputs.as_posix()}
set environment EMERALD_PC_STOP_FRAME {30500 if phase == 'r01' else 10000}
break Port_ExitCleanly
run
commands 1
silent
end
python
import sys
from pathlib import Path
sys.path.insert(0,'port/tests')
import campaign_driver as d
import natural_campaign_routes as route
d.SCRATCH=Path({scratch.as_posix()!r})
{actions}
print('NATURAL {phase.upper()} REPLAY PASS')
end
continue
quit
''',encoding="utf-8")
    log=scratch/"campaign.log"
    result=run_logged(["gdb","-batch","-x",str(script),str(scratch/"build/emerald-pc-diagnostic.exe")],project,log,"PC diagnostic: frame=",timeout=1800)
    output=log.read_text(errors="replace")
    assert result==0 and f"NATURAL {phase.upper()} REPLAY PASS" in output
    assert "received signal" not in output and "exited normally" in output
    print(f"Natural {phase} campaign replay PASS")


if __name__ == "__main__":
    main()
