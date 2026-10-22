"""Reproduce R01 with actual keyboard menus, paths and battles from a blank save."""
from pathlib import Path
import shutil
import sys
import argparse
import time
import gameplay_smoke
from process_watchdog import run_logged



def preserve_previous_run(scratch):
    """Keep the previous attempt's evidence before a replay overwrites it."""
    if not (scratch/'campaign.log').exists():
        return None
    history=scratch/'history'/str(time.time_ns())
    history.mkdir(parents=True)
    for name in ('campaign.log','campaign.gdb','input.txt','route.jsonl','battle-choices.jsonl',
                 'saves/emerald-pc-diagnostic.sav'):
        source=scratch/name
        if source.exists():
            target=history/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
    return history


def main():
    project=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=("r01","r02-devon","r02-steven","r02-catch","r02-museum","r02-rocksmash","r02-rest","r02-meteor","r02-connections","r02-shop","r02-jagged","r02-flannery","r03-petalburg","r03-norman","r03-strength","r03-surf","r03-weather","r03-rival","r03-scope","r03-fly-gate","r03-gates","r03-tms","r03-winona","r03-fly","r04-pyre","r04-magma-entry","r04-maxie","r04-aqua-gate","r04-harbor","r04-master-ball","r04-wailmer-gate","r04-aqua-route","r04-matt","r04-exp-share","r03-surf-speed","r04-mossdeep-blue","r04-mossdeep-purple","r04-mossdeep-circuit","r04-mossdeep-leaders","r04-mossdeep-leaders-loss","r04-space-upper","r04-steven","r04-dive-gift","r04-seafloor-dive","r04-seafloor-first-room","r04-seafloor-second-room","r04-seafloor-currents","r04-seafloor-shelly","r04-seafloor-final-puzzle","r04-archie","r04-sootopolis-entry","r04-wallace","r04-sky-open","r04-sky-climb","r04-rayquaza-awaken","r04-rayquaza-peace","r04-waterfall-gift","r04-sootopolis-ice","r04-earthquake-prep","r04-juan-tactical","r04-tactical-shop","r05-ball-supplies","r05-waterfall-catch","r05-road-trip","r05-waterfall","r05-wally","r05-flash","r05-upper-boulders","r05-smash-corridor","r05-second-basement","r05-b2f-crossing","r05-cave-waterfalls","r05-central-puzzle","r05-victory-exit","r05-league-lobby","r05-league-gate","r05-sidney-supplies","r05-sidney-tactical","r05-phoebe-loss","r05-mach-bike","r05-bike-toggle","r05-pillar-return","r05-broken-floor-entry","r05-broken-floor-crossing","r05-upper-floor","r05-rayquaza-catch","r05-rayquaza-league-prep","r05-rayquaza-sidney","r05-rayquaza-phoebe","r05-rayquaza-glacia","r05-rayquaza-drake","r05-league-restock","r05-league-retry","r05-drake-rest","r05-leppa-prep","r05-leppa-league","r05-leppa-finish","r05-leppa-use","r05-leppa-precharged","r05-glacia-ground-lead","r05-new-mauville-key","r05-new-mauville-entry","r05-new-mauville-generator","r05-new-mauville-reward","r05-thunderbolt-league-prep","r05-thunderbolt-league","r05-champion-door","r05-wallace-champion","r06-daycare","r06-mother","r06-father-catch","r06-generate","r06-receive","r06-hatch"),default="r01")
    phase=parser.parse_args().phase
    scratch=project/("build/natural-campaign-replay" if phase == "r01" else "build/natural-campaign-replay-"+phase)
    preserve_previous_run(scratch)
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
                'r03-norman':'r03-petalburg','r03-strength':'r03-verdanturf','r03-surf':'r03-norman','r03-weather':'r03-weather-arrival','r03-rival':'r03-wingull-training','r03-scope':'r03-scope-supplies','r03-fly-gate':'r03-fly-learned','r03-gates':'r03-gym-entry','r03-tms':'r03-tm-counter','r03-winona':'r03-winona-ice-ready','r03-fly':'r03-fly-enabled','r04-pyre':'r04-mtpyre-arrival','r04-magma-entry':'r04-jagged-emblem','r04-maxie':'r04-maxie-ready','r04-aqua-gate':'r04-aqua-gate-ready','r04-harbor':'r04-slateport-harbor-ready','r04-master-ball':'r04-aqua-b1f','r04-wailmer-gate':'r04-aqua-gate-ready','r04-aqua-route':'r04-master-ball-verified','r04-matt':'r04-matt-ready','r04-exp-share':'r04-devon-exp-share-ready','r03-surf-speed':'r03-surf','r04-mossdeep-blue':'r04-mossdeep-blue-room','r04-mossdeep-purple':'r04-mossdeep-purple-room','r04-mossdeep-circuit':'r04-mossdeep-gym-entry','r04-mossdeep-leaders':'r04-mossdeep-battle-ready','r04-mossdeep-leaders-loss':'r04-mossdeep-battle-ready','r04-space-upper':'r04-space-center-entry','r04-steven':'r04-steven-ready','r04-dive-gift':'r04-steven-result','r04-seafloor-dive':'r04-route128-dive','r04-seafloor-first-room':'r04-seafloor-room1','r04-seafloor-second-room':'r04-seafloor-room2','r04-seafloor-currents':'r04-seafloor-currents-entry','r04-seafloor-shelly':'r04-seafloor-shelly-entry','r04-seafloor-final-puzzle':'r04-seafloor-final-puzzle-entry','r04-archie':'r04-archie-ready','r04-sootopolis-entry':'r04-route126-entry','r04-wallace':'r04-sootopolis-arrival','r04-sky-open':'r04-route131-entry','r04-sky-climb':'r04-sky-pillar-open','r04-rayquaza-awaken':'r04-rayquaza-ready','r04-rayquaza-peace':'r04-rayquaza-awakened','r04-waterfall-gift':'r04-sootopolis-peace','r04-sootopolis-ice':'r04-sootopolis-gym-entry','r04-earthquake-prep':'r04-juan-loss','r04-juan-tactical':'r04-juan-tactical-ready','r04-tactical-shop':'r04-juan-earthquake-loss','r05-ball-supplies':'r05-dewford-entry','r05-waterfall-catch':'r05-tentacool-catch-ready','r05-road-trip':'r05-waterfall-learned','r05-waterfall':'r05-ever-grande-waterfall-bottom','r05-wally':'r05-wally-ready','r05-flash':'r05-victory-road-b1f-entry','r05-upper-boulders':'r05-victory-road-b1f-flash','r05-smash-corridor':'r05-victory-road-upper-boulders','r05-second-basement':'r05-victory-road-rock-smashed','r05-b2f-crossing':'r05-victory-road-b2f-entry','r05-cave-waterfalls':'r05-victory-road-b2f-entry','r05-central-puzzle':'r05-victory-road-center-stairs','r05-victory-exit':'r05-victory-road-central-upper','r05-league-lobby':'r05-victory-road-exit','r05-league-gate':'r05-league-lobby-rested','r05-sidney-supplies':'r05-sidney-result','r05-sidney-tactical':'r05-sidney-tactical-ready','r05-phoebe-loss':'r05-phoebe-ready','r05-mach-bike':'r05-phoebe-loss','r05-bike-toggle':'r05-mach-bike-rested','r05-pillar-return':'r05-mach-bike-tested','r05-broken-floor-entry':'r05-sky-pillar-return','r05-broken-floor-crossing':'r05-sky-pillar-broken-floor','r05-upper-floor':'r05-sky-pillar-3f-mach','r05-rayquaza-catch':'r05-sky-pillar-5f-mach','r05-rayquaza-league-prep':'r05-rayquaza-caught','r05-rayquaza-sidney':'r05-rayquaza-sidney-ready','r05-rayquaza-phoebe':'r05-rayquaza-sidney-win','r05-rayquaza-glacia':'r05-rayquaza-phoebe-win','r05-rayquaza-drake':'r05-rayquaza-glacia-win','r05-league-restock':'r05-rayquaza-drake-loss','r05-league-retry':'r05-league-restocked','r05-drake-rest':'r05-league-retry-drake-ready','r05-leppa-prep':'r05-drake-rest-loss','r05-leppa-league':'r05-league-leppa-ready','r05-leppa-finish':'r05-leppa-phoebe-win','r05-leppa-use':'r05-leppa-phoebe-win','r05-leppa-precharged':'r05-phoebe-leppa-restored','r05-glacia-ground-lead':'r05-phoebe-leppa-restored','r05-new-mauville-key':'r05-glacia-ground-lead-loss','r05-new-mauville-entry':'r05-new-mauville-key','r05-new-mauville-generator':'r05-new-mauville-inside','r05-new-mauville-reward':'r05-new-mauville-generator-off','r05-thunderbolt-league-prep':'r05-rayquaza-thunderbolt','r05-thunderbolt-league':'r05-thunderbolt-league-ready','r05-champion-door':'r05-thunderbolt-drake-win','r05-wallace-champion':'r05-wallace-door-ready','r06-daycare':'r05-the-end','r06-mother':'r06-daycare-arrival','r06-father-catch':'r06-mother-deposited','r06-generate':'r06-father-caught','r06-receive':'r06-egg-pending','r06-hatch':'r06-egg-received'}
    save.write_bytes(b"\xff"*131072 if phase == "r01" else
                     (project/('build/natural-campaign/'+checkpoint[phase]+'.sav')).read_bytes())
    inputs=scratch/"input.txt"
    previous=sys.argv
    try:
        sys.argv=["gameplay_smoke.py",str(inputs)]
        if phase == "r01":
            gameplay_smoke.main()
        else:
            # These checkpoints face an NPC or deep water. Stop Continue pulses before
            # field control returns, so the route itself starts the event.
            continue_until=1181 if phase in ('r04-maxie','r04-wallace','r04-juan-tactical','r05-sidney-tactical','r05-phoebe-loss','r05-leppa-finish','r05-leppa-use','r05-leppa-precharged','r05-glacia-ground-lead','r05-thunderbolt-league-prep','r05-champion-door','r05-wallace-champion','r06-daycare','r06-mother','r06-father-catch','r06-generate','r06-receive','r06-hatch') else 8000
            if phase == 'r05-broken-floor-crossing':
                continue_until=1800
            inputs.write_text("".join(f"{frame} {frame+1} A\n" for frame in range(1000,continue_until,45)))
    finally:
        sys.argv=previous
    script=scratch/"campaign.gdb"
    actions={
        'r06-receive':'''import breeding_driver as breeding
breeding.receive()''',
        'r06-hatch':'''import breeding_driver as breeding
breeding.hatch()''',
        'r06-generate':'''import breeding_driver as breeding
breeding.generate()''',
        'r06-father-catch':'''import breeding_driver as breeding
breeding.catch_father()''',
        'r06-mother':'''import breeding_driver as breeding
breeding.mother()''',
        'r06-daycare':'''import breeding_driver as breeding
breeding.prepare()''',
        'r05-wallace-champion':'''import champion_driver as champion
champion.wallace()''',
        'r05-champion-door':'''import league_driver as league
league.champion_door()''',
        'r05-thunderbolt-league':'''import league_driver as league
league.league_with_leppa()''',
        'r05-thunderbolt-league-prep':'''import new_mauville_driver as quest
quest.prepare_league()''',
        'r05-new-mauville-reward':'''import new_mauville_driver as quest
quest.collect_thunderbolt()''',
        'r05-new-mauville-generator':'''import new_mauville_driver as quest
quest.stop_generator()''',
        'r05-new-mauville-entry':'''import new_mauville_driver as quest
quest.enter()''',
        'r05-new-mauville-key':'''import new_mauville_driver as quest
quest.get_key()''',
        'r05-glacia-ground-lead':'''import league_driver as league
league.league_with_leppa(start='glacia',glacia_lead=5)''',
        'r05-leppa-precharged':'''import league_driver as league
league.league_with_leppa(start='glacia')''',
        'r05-leppa-use':'''import league_driver as league
league.restore_outrage()
d.save_checkpoint('r05-phoebe-leppa-restored')''',
        'r05-leppa-finish':'''import league_driver as league
league.league_with_leppa(start='glacia')''',
        'r05-leppa-league':'''import league_driver as league
league.league_with_leppa()''',
        'r05-leppa-prep':'''import league_driver as league
league.leppa_preparation()''',
        'r05-drake-rest':'''import league_driver as league
league.drake_with_rest()''',
        'r05-league-retry':'''import league_driver as league
league.league_retry()''',
        'r05-league-restock':'''import league_driver as league
league.league_restock()''',
        'r05-rayquaza-drake':'''import league_driver as league
league.rayquaza_elite('drake',expected_outcome=None)''',
        'r05-rayquaza-phoebe':'''import league_driver as league
league.rayquaza_elite('phoebe')''',
        'r05-rayquaza-glacia':'''import league_driver as league
league.rayquaza_elite('glacia',expected_outcome=None)''',
        'r05-rayquaza-league-prep':'''import league_driver as league
league.rayquaza_league_preparation()''',
        'r05-rayquaza-sidney':'''import league_driver as league
league.rayquaza_sidney()''',
        'r05-rayquaza-catch':'''import league_driver as league
league.catch_rayquaza()''',
        'r05-upper-floor':'''import league_driver as league
league.upper_broken_floor()''',
        'r05-broken-floor-crossing':'''import league_driver as league
league.broken_floor_crossing()''',
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
        'r05-broken-floor-entry':'''import league_driver as league
league.broken_floor_entry()''',
        'r05-pillar-return':'''import league_driver as league
league.return_to_pillar()''',
        'r05-bike-toggle':'''import league_driver as league
league.toggle_mach_bike()
assert d.memory('gPlayerAvatar',1)[0]&2
d.save_checkpoint('r05-mach-bike-mounted')
league.toggle_mach_bike()
assert not d.memory('gPlayerAvatar',1)[0]&2
d.save_checkpoint('r05-mach-bike-tested')''',
        'r05-mach-bike':'''import league_driver as league
league.get_mach_bike()''',
        'r05-phoebe-loss':'''import league_driver as league
league.phoebe_loss()''',
        'r05-sidney-supplies':'''import league_driver as league
league.retry_supplies()''',
        'r05-sidney-tactical':'''import league_driver as league
league.sidney_tactical()''',
        'r05-league-gate':'''import league_driver as league
league.league_gate()''',
        'r05-league-lobby':'''import league_driver as league
league.league_lobby()''',
        'r05-central-puzzle':'''import league_driver as league
league.central_puzzle()''',
        'r05-victory-exit':'''import league_driver as league
league.victory_exit()''',
        'r05-cave-waterfalls':'''import league_driver as league
league.cave_waterfalls()''',
        'r05-b2f-crossing':'''import league_driver as league
league.cross_second_basement()''',
        'r05-second-basement':'''import league_driver as league
league.second_basement()''',
        'r05-smash-corridor':'''import league_driver as league
league.smash_corridor()''',
        'r05-flash':'''import league_driver as league
league.basement_flash()''',
        'r05-upper-boulders':'''import league_driver as league
league.upper_boulders()''',
        'r05-wally':'''import league_driver as league
league.wally()''',
        'r05-road-trip':'''import league_driver as league
league.road_trip()''',
        'r05-waterfall':'''import league_driver as league
league.waterfall()''',
        'r05-ball-supplies':'''import league_driver as league
league.ball_supplies()''',
        'r05-waterfall-catch':'''import league_driver as league
league.catch_waterfall_user()''',
        'r04-tactical-shop':'''import sootopolis_gym_driver as gym
gym.tactical_shop()''',
        'r04-juan-tactical':'''import sootopolis_gym_driver as gym
gym.juan_tactical()''',
        'r04-earthquake-prep':'''import sootopolis_gym_driver as gym
gym.earthquake_prep()''',
        'r04-waterfall-gift':'''import sootopolis_driver as city
city.waterfall_gift()''',
        'r04-sootopolis-ice':'''import sootopolis_gym_driver as gym
gym.puzzle()''',
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
set environment EMERALD_PC_STOP_FRAME {30500 if phase == 'r01' else 2000 if phase == 'r05-broken-floor-crossing' or phase.startswith('r06-') and phase != 'r06-daycare' else 10000}
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
