"""Reload a keyboard-created campaign checkpoint through the real Continue UI."""
from pathlib import Path
import json
import shutil
import argparse
import re
from process_watchdog import run_logged


def main():
    project=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint",nargs="?",default="r01-birch-dex")
    name=parser.parse_args().checkpoint
    assert re.fullmatch(r"[a-z0-9-]+",name), "Checkpoint must be a private fixture name"
    source=project/"build/natural-campaign"
    scratch=project/("build/natural-campaign-reload-"+name)
    expected=json.loads((source/(name+".json")).read_text())
    for directory in ("build","roms","saves"):
        (scratch/directory).mkdir(parents=True,exist_ok=True)
    for filename in ("emerald-pc-diagnostic.exe","SDL2.dll"):
        shutil.copy2(source/"build"/filename,scratch/"build"/filename)
    shutil.copy2(source/"roms/test.gba",scratch/"roms/test.gba")
    save=scratch/"saves/emerald-pc-diagnostic.sav"
    saved=(source/(name+".sav")).read_bytes()
    save.write_bytes(saved)
    inputs=scratch/"input.txt"
    inputs.write_text("".join(f"{frame} {frame+1} A\n" for frame in range(1000,8000,45)))
    script=scratch/"reload.gdb"
    script.write_text(f'''set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT {inputs.as_posix()}
set environment EMERALD_PC_STOP_FRAME 10000
break Port_ExitCleanly
run
python
import sys,json
sys.path.insert(0,'port/tests')
import campaign_driver as d
actual=d.state()
expected={expected!r}
for key in ('map','x','y','party'):
    assert actual[key] == expected[key], (key,actual,expected)
for index,mon in enumerate(expected['team']):
    for field,key in ((11,'species'),(56,'level')):
        assert d.value(f'(int)GetMonData3((void *)((char *)&gPlayerParty+{{index*100}}),{{field}},0)') == mon[key]
assert d.value('(int)FlagGet(0x861)') == expected['dex']
assert d.value('(int)FlagGet(0x82)') == expected['rival']
assert d.value('(int)CountTotalItemQuantityInBag(4)') == expected['balls']
if 'badges' in expected:
    assert [d.value(f'(int)FlagGet({{0x867+i}})') for i in range(8)] == expected['badges']
for key,var in (('norman',0x4085),('woods',0x4098),('rustboro',0x405a),('briney',0x4090),('route110',0x4069)):
    if key in expected:
        assert d.value(f'(int)VarGet({{var}})') == expected[key]
for key,expected_value in expected.get('events',{{}}).items():
    flag=d.EVENT_FLAGS[key]
    assert d.value(f'(int)FlagGet({{flag}})') == expected_value
print('NATURAL RELOAD PASS',actual)
end
continue
quit
''',encoding="utf-8")
    log=scratch/"reload.log"
    result=run_logged(["gdb","-batch","-x",str(script),str(scratch/"build/emerald-pc-diagnostic.exe")],project,log,"PC diagnostic: frame=")
    output=log.read_text(errors="replace")
    assert result == 0 and "NATURAL RELOAD PASS" in output and "received signal" not in output
    assert "exited normally" in output
    assert save.read_bytes() == saved, "Continue must not rewrite the checkpoint"
    print("Natural campaign Continue/reload PASS; save unchanged")


if __name__ == "__main__":
    main()
