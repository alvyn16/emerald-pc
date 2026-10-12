"""Reproduce R01 with actual keyboard menus, paths and battles from a blank save."""
from pathlib import Path
import shutil
import sys
import gameplay_smoke
from process_watchdog import run_logged


def main():
    project=Path(__file__).resolve().parents[2]
    scratch=project/"build/natural-campaign-replay"
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
    save.write_bytes(b"\xff"*131072)
    inputs=scratch/"input.txt"
    previous=sys.argv
    try:
        sys.argv=["gameplay_smoke.py",str(inputs)]
        gameplay_smoke.main()
    finally:
        sys.argv=previous
    script=scratch/"campaign.gdb"
    script.write_text(f'''set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT {inputs.as_posix()}
set environment EMERALD_PC_STOP_FRAME 30500
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
route.meet_may()
route.rescue_birch()
route.rival_and_dex()
print('NATURAL R01 REPLAY PASS')
end
continue
quit
''',encoding="utf-8")
    log=scratch/"campaign.log"
    result=run_logged(["gdb","-batch","-x",str(script),str(scratch/"build/emerald-pc-diagnostic.exe")],project,log,"PC diagnostic: frame=",timeout=1800)
    output=log.read_text(errors="replace")
    assert result==0 and "NATURAL R01 REPLAY PASS" in output
    assert "received signal" not in output and "exited normally" in output
    print("Natural R01 campaign replay PASS")


if __name__ == "__main__":
    main()
