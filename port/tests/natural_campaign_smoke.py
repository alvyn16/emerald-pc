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
    parser.add_argument("--phase",choices=("r01","r02-devon","r02-steven","r02-catch","r02-museum","r02-rocksmash","r02-rest","r02-meteor","r02-connections","r02-shop","r02-jagged","r02-flannery","r03-petalburg","r03-norman","r03-strength","r03-surf","r03-weather"),default="r01")
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
    checkpoint={'r02-devon':'r02-roxanne','r02-steven':'r02-brawly',
                'r02-catch':'r02-route110','r02-museum':'r02-steven',
                'r02-rocksmash':'r02-wattson','r02-rest':'r02-route111-north',
                'r02-meteor':'r02-fallarbor','r02-connections':'r02-fallarbor',
                'r02-shop':'r02-fallarbor','r02-jagged':'r02-maxie-meteorite',
                'r02-flannery':'r02-lavaridge','r03-petalburg':'r03-strength',
                'r03-norman':'r03-petalburg','r03-strength':'r03-verdanturf','r03-surf':'r03-norman','r03-weather':'r03-weather-arrival'}
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
    actions={
        'r01':'''route.meet_may()
route.rescue_birch()
route.rival_and_dex()''',
        'r02-devon':'''d.RUN_WILD=True
d.settle(30000)
assert d.state()['map'] == 'RustboroCity_Gym'
d.go(5,19); d.cross('DOWN','RustboroCity')
route.cut_peeko_and_pokenav()''',
        'r02-steven':'''d.RUN_WILD=True
d.settle(30000)
route.steven_letter()
route.sail_to_slateport()
d.save_checkpoint('r02-slateport-arrival')''',
        'r02-catch':'''d.settle(30000)
route.catch_wingull()''',
        'r02-museum':'''d.RUN_WILD=True
d.settle(30000)
route.sail_to_slateport()
route.museum_delivery()''',
        'r02-rocksmash':'''d.settle(30000)
route.rock_smash_route111()''',
        'r02-rest':'''d.RUN_WILD=True
d.go(26,19); d.cross('UP','Route111_OldLadysRestStop')
route.rest_old_lady()
d.save_checkpoint('r02-rested-north')''',
        'r02-meteor':'''route.meteor_falls_scene()''',
        'r02-connections':'''d.RUN_WILD=True
for target in ('Route113','Route111','Route112','Route111','Route113','FallarborTown'):
    d.connect(target)
    assert d.state()['map'] == target
    print('NATURAL CONNECTION PASS',target,d.state())
d.save_checkpoint('r02-connections')''',
        'r02-shop':'''d.go(15,16); d.cross('UP','FallarborTown_Mart')
d.buy_item(22,3)
d.go(3,7); d.cross('DOWN','FallarborTown')
d.save_checkpoint('r02-shop-supplies')''',
        'r02-jagged':'''route.jagged_pass_to_lavaridge()''',
        'r03-weather':'''route.weather_institute()''',
        'r03-surf':'''route.surf_crossing()''',
        'r03-strength':'''route.rusturf_strength()''',
        'r03-norman':'''d.go(25,13); d.cross('UP','PetalburgCity_Mart')
d.buy_item(22,6)
d.go(3,7); d.cross('DOWN','PetalburgCity')
route.norman_gym()''',
        'r03-petalburg':'''d.RUN_WILD=True
d.HEAL_ITEMS=(22,13)
d.go(10,29); d.cross('DOWN','PetalburgWoods')
d.go(16,37); d.cross('DOWN','Route104')
d.connect('PetalburgCity')
assert d.state()['map'] == 'PetalburgCity'
print('NATURAL CONNECTED BORDER PASS',d.state())
d.go(20,17); d.cross('UP','PetalburgCity_PokemonCenter_1F')
d.nurse(); d.go(7,8); d.cross('DOWN','PetalburgCity')
d.save_checkpoint('r03-petalburg')''',
        'r02-flannery':'''d.go(15,6); d.cross('UP','LavaridgeTown_Mart')
d.buy_item(22,6)
d.go(3,7); d.cross('DOWN','LavaridgeTown')
route.flannery_gym()''',
    }[phase]
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
