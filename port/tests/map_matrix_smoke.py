"""Controlled map loads; this is not a continuous story playthrough."""
import argparse
import json
from game_fixture import PROJECT, prepare, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--all", action="store_true")
parser.add_argument("--group", type=int)
args = parser.parse_args()
groups = json.loads((PROJECT / "pokeemerald/data/maps/map_groups.json").read_text(encoding="utf-8"))
layouts = {x["id"]: x for x in json.loads((PROJECT / "pokeemerald/data/layouts/layouts.json").read_text(encoding="utf-8"))["layouts"]}
representatives = {"LittlerootTown", "OldaleTown", "PetalburgCity", "RustboroCity", "DewfordTown",
    "SlateportCity", "MauvilleCity", "VerdanturfTown", "FallarborTown", "LavaridgeTown",
    "FortreeCity", "LilycoveCity", "MossdeepCity", "SootopolisCity", "PacifidlogTown",
    "EverGrandeCity", "Route101", "Route110", "Route119", "Route124", "Route134",
    "LittlerootTown_BrendansHouse_1F", "RustboroCity_PokemonCenter_1F", "PetalburgWoods",
    "GraniteCave_1F", "MeteorFalls_1F_1R", "VictoryRoad_1F", "SafariZone_South",
    "BattleFrontier_OutsideWest", "BattleFrontier_BattleTowerLobby",
    "LilycoveCity_ContestLobby", "Route117_PokemonDayCare"}
maps = []
for group, key in enumerate(groups["group_order"]):
    for index, name in enumerate(groups[key]):
        data = json.loads((PROJECT / f"pokeemerald/data/maps/{name}/map.json").read_text(encoding="utf-8"))
        if (args.group is None or group == args.group) and (args.all or name in representatives):
            layout = layouts[data["layout"]]
            warps = data.get("warp_events", [])
            x, y = (warps[0]["x"], warps[0]["y"]) if warps else (int(layout["width"])//2, int(layout["height"])//2)
            maps.append((group, index, name, x, y, data["map_type"]))
assert maps, "No maps selected"
name = "map-matrix" + (f"-{args.group}" if args.group is not None else "")
scratch, commands = prepare(name, "")
markers = []
for number, (group, index, label, x, y, kind) in enumerate(maps):
    stop = 31000 + (number+1)*300
    commands += f"""
call (void)ResetInitialPlayerAvatarState()
call (void)ScriptContext_Init()
call (void)UnlockPlayerFieldControls()
set *(unsigned int *)&gFieldCallback = 0
set *(unsigned int *)&gFieldCallback2 = 0
call (void)SetWarpDestination({group},{index},-1,{x},{y})
call (void)WarpIntoMap()
call (void)SetMainCallback2((void *)CB2_LoadMap)
set var sStopFrame = {stop}
return
continue
python
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes(({group},{index})), "Wrong map"
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld")), "Map load not complete"
end
printf "MAP {label} PASS\\n"
"""
    markers.append(f"MAP {label} PASS")
commands += "continue\nquit\n"
log = run(scratch, commands, markers)
(scratch / "inventory.json").write_text(json.dumps(maps, indent=2), encoding="utf-8")
print(f"PASS {len(maps)} controlled map loads; {log}")
