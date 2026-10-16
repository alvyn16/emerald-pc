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
    parser.add_argument("--phase",choices=("r01","r02-devon","r02-steven","r02-catch","r02-museum","r02-rocksmash","r02-rest","r02-meteor","r02-connections","r02-shop","r02-jagged","r02-flannery","r03-petalburg","r03-norman","r03-strength","r03-surf","r03-weather","r03-rival","r03-scope","r03-fly-gate","r03-gates","r03-tms","r03-winona","r03-fly","r04-pyre","r04-magma-entry","r04-maxie","r04-aqua-gate","r04-harbor","r04-master-ball","r04-wailmer-gate","r04-aqua-route","r04-matt","r04-exp-share","r03-surf-speed","r04-mossdeep-blue","r04-mossdeep-purple","r04-mossdeep-circuit","r04-mossdeep-leaders","r04-mossdeep-leaders-loss","r04-space-upper","r04-steven","r04-dive-gift","r04-seafloor-dive","r04-seafloor-first-room","r04-seafloor-second-room","r04-seafloor-currents","r04-seafloor-shelly","r04-seafloor-final-puzzle","r04-archie","r04-sootopolis-entry","r04-wallace","r04-sky-open","r04-sky-climb","r04-rayquaza-awaken","r04-rayquaza-peace"),default="r01")
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
                'r03-norman':'r03-petalburg','r03-strength':'r03-verdanturf','r03-surf':'r03-norman','r03-weather':'r03-weather-arrival','r03-rival':'r03-wingull-training','r03-scope':'r03-scope-supplies','r03-fly-gate':'r03-fly-learned','r03-gates':'r03-gym-entry','r03-tms':'r03-tm-counter','r03-winona':'r03-winona-ice-ready','r03-fly':'r03-fly-enabled','r04-pyre':'r04-mtpyre-arrival','r04-magma-entry':'r04-jagged-emblem','r04-maxie':'r04-maxie-ready','r04-aqua-gate':'r04-aqua-gate-ready','r04-harbor':'r04-slateport-harbor-ready','r04-master-ball':'r04-aqua-b1f','r04-wailmer-gate':'r04-aqua-gate-ready','r04-aqua-route':'r04-master-ball-verified','r04-matt':'r04-matt-ready','r04-exp-share':'r04-devon-exp-share-ready','r03-surf-speed':'r03-surf','r04-mossdeep-blue':'r04-mossdeep-blue-room','r04-mossdeep-purple':'r04-mossdeep-purple-room','r04-mossdeep-circuit':'r04-mossdeep-gym-entry','r04-mossdeep-leaders':'r04-mossdeep-battle-ready','r04-mossdeep-leaders-loss':'r04-mossdeep-battle-ready','r04-space-upper':'r04-space-center-entry','r04-steven':'r04-steven-ready','r04-dive-gift':'r04-steven-result','r04-seafloor-dive':'r04-route128-dive','r04-seafloor-first-room':'r04-seafloor-room1','r04-seafloor-second-room':'r04-seafloor-room2','r04-seafloor-currents':'r04-seafloor-currents-entry','r04-seafloor-shelly':'r04-seafloor-shelly-entry','r04-seafloor-final-puzzle':'r04-seafloor-final-puzzle-entry','r04-archie':'r04-archie-ready','r04-sootopolis-entry':'r04-route126-entry','r04-wallace':'r04-sootopolis-arrival','r04-sky-open':'r04-route131-entry','r04-sky-climb':'r04-sky-pillar-open','r04-rayquaza-awaken':'r04-rayquaza-ready','r04-rayquaza-peace':'r04-rayquaza-awakened'}
    save.write_bytes(b"\xff"*131072 if phase == "r01" else
                     (project/('build/natural-campaign/'+checkpoint[phase]+'.sav')).read_bytes())
    inputs=scratch/"input.txt"
    previous=sys.argv
    try:
        sys.argv=["gameplay_smoke.py",str(inputs)]
        if phase == "r01":
            gameplay_smoke.main()
        else:
            # Maxie's checkpoint faces his NPC. Stop Continue pulses before
            # field control returns, so the route itself starts the event.
            continue_until=1181 if phase in ('r04-maxie','r04-wallace') else 8000
            inputs.write_text("".join(f"{frame} {frame+1} A\n" for frame in range(1000,continue_until,45)))
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
        'r04-aqua-route':'''route.aqua_to_matt()''',
        'r04-rayquaza-peace':'''import sootopolis_driver as city
city.peace()''',
        'r04-sky-climb':'''import sootopolis_driver as city
city.pillar_climb()''',
        'r04-rayquaza-awaken':'''import sootopolis_driver as city
city.awaken()''',
        'r04-sky-open':'''import sootopolis_driver as city
city.pillar_open()''',
        'r04-wallace':'''import sootopolis_driver as city
city.wallace()''',
        'r04-sootopolis-entry':'''import sootopolis_driver as city
city.arrive()''',
        'r04-archie':'''import seafloor_driver as cave
cave.archie()''',
        'r04-seafloor-shelly':'''import seafloor_driver as cave
cave.shelly()''',
        'r04-seafloor-final-puzzle':'''import seafloor_driver as cave
cave.final_puzzle()''',
        'r04-seafloor-currents':'''import seafloor_driver as cave
cave.currents()''',
        'r04-seafloor-second-room':'''import seafloor_driver as cave
cave.second_room()''',
        'r04-seafloor-first-room':'''import seafloor_driver as cave
cave.first_room()''',
        'r04-seafloor-dive':'''import seafloor_driver as cave
cave.dive_entry()''',
        'r04-dive-gift':'''import space_center_driver as center
center.dive_gift()''',
        'r04-space-upper':'''import space_center_driver as center
d.HEAL_ITEMS=(21,22,13)
center.upper_floor()''',
        'r04-steven':'''import space_center_driver as center
d.HEAL_ITEMS=(21,22,13)
center.steven_battle()''',
        'r04-mossdeep-leaders-loss':'''import mossdeep_gym_driver as gym
d.HEAL_ITEMS=(21,22,13)
gym.leaders(expected_outcome=2)''',
        'r04-mossdeep-leaders':'''import mossdeep_gym_driver as gym
d.HEAL_ITEMS=(21,22,13)
gym.leaders()''',
        'r04-mossdeep-circuit':'''import mossdeep_gym_driver as gym
d.HEAL_ITEMS=(21,22,13)
gym.circuit()
d.save_checkpoint('r04-mossdeep-circuit-ready')''',
        'r04-mossdeep-purple':'''import mossdeep_gym_driver as gym
d.HEAL_ITEMS=(21,22,13)
gym.purple_room()''',
        'r04-mossdeep-blue':'''import mossdeep_gym_driver as gym
d.HEAL_ITEMS=(21,22,13)
gym.blue_room()''',
        'r03-surf-speed':'''route.surf_speed_regression()''',
        'r04-exp-share':'''route.devon_exp_share()''',
        'r04-matt':'''route.matt_battle()''',
        'r04-wailmer-gate':'''route.wailmer_gate_closed()''',
        'r04-master-ball':'''route.aqua_master_ball()''',
        'r04-harbor':'''route.harbor_submarine()''',
        'r04-aqua-gate':'''route.aqua_gate_closed()''',
        'r04-maxie':'''route.maxie_magma()''',
        'r04-magma-entry':'''route.magma_entry()''',
        'r04-pyre':'''route.mt_pyre()''',
        'r03-fly':'''route.fly_roundtrip()''',
        'r03-winona':'''route.winona_battle()''',
        'r03-tms':'''route.ice_tm_supplies()''',
        'r03-gates':'''route.fortree_gates()''',
        'r03-fly-gate':'''route.fly_badge_gate()''',
        'r03-scope':'''route.devon_scope()''',
        'r03-rival':'''route.route119_rival()''',
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
set python print-stack full
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
