"""Controlled cracked-floor map transitions and host bytecode selection."""
import json
from game_fixture import PROJECT, prepare, run


def main():
    groups=json.loads((PROJECT/"pokeemerald/data/maps/map_groups.json").read_text())
    maps={name:(group,index) for group,key in enumerate(groups["group_order"])
          for index,name in enumerate(groups[key])}
    scratch,commands=prepare("script-ubfix","")
    commands+='''
python
address=int(gdb.parse_and_eval('(unsigned int)&CaveHole_FixCrackedGround'))
assert bytes(gdb.selected_inferior().read_memory(address,5)) == bytes((0x16,0x22,0x40,1,0)), 'Host must select setvar, not the invalid copyvar literal'
end
'''
    markers=[]
    for number,name in enumerate(("GraniteCave_B1F","SkyPillar_2F","SkyPillar_4F")):
        group,index=maps[name]
        data=json.loads((PROJECT/f"pokeemerald/data/maps/{name}/map.json").read_text())
        x,y=data["warp_events"][0]["x"],data["warp_events"][0]["y"]
        commands+=f'''
call (int)VarSet(0x4022,0)
call (void)SetWarpDestination({group},{index},-1,{x},{y})
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = {31500+number*500}
return
continue
python
assert int(gdb.parse_and_eval('(int)VarGet(0x4022)')) == 1
address=int(gdb.parse_and_eval('*(unsigned int *)&gSaveBlock1Ptr'))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes(({group},{index}))
assert int(gdb.parse_and_eval('(unsigned int)gMain.callback2')) == int(gdb.parse_and_eval('(unsigned int)&CB2_Overworld'))
end
printf "CRACKED FLOOR {name} PASS\\n"
'''
        markers.append(f"CRACKED FLOOR {name} PASS")
    commands+="continue\nquit\n"
    log=run(scratch,commands,markers)
    print(f"PASS host setvar bytecode and three cracked-floor map transitions; {log}")


if __name__ == "__main__":
    main()
