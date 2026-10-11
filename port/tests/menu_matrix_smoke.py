"""Open and close real field menus repeatedly using isolated diagnostic inputs."""
import argparse
from game_fixture import prepare, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("menu", choices=("summary", "party", "bag", "dex", "options", "naming"))
menu = parser.parse_args().menu
inputs = ""
for cycle in range(3):
    start = 31000 + cycle * 1000
    if menu == "naming":
        # Add a character then select OK with Start, and confirm with A.
        inputs += f"{start+250} {start+251} A\n{start+300} {start+301} START\n"
        inputs += "".join(f"{n} {n+1} A\n" for n in range(start+350, start+900, 50))
    else:
        inputs += "".join(f"{n} {n+1} B\n" for n in range(start+250, start+900, 50))
scratch, commands = prepare(f"menu-matrix-{menu}", inputs)
entries = {
    "summary": "call (void)ShowPokemonSummaryScreen(0,(void *)&gPlayerParty,0,0,(void *)CB2_ReturnToField)",
    "party": "call (void)InitPartyMenu(0,0,0,0,0,(void *)Task_HandleChooseMonInput,(void *)CB2_ReturnToField)",
    "bag": "call (void)CB2_BagMenuFromStartMenu()",
    "dex": "call (void)SetMainCallback2((void *)CB2_OpenPokedex)",
    "options": "call (void)SetMainCallback2((void *)CB2_InitOptionMenu)",
    "naming": "call (void)DoNamingScreen(3,(char *)&gPlayerParty+8,283,0,0,(void *)CB2_ReturnToField)",
}
markers = []
for cycle in range(3):
    start = 31000 + cycle * 1000
    if menu == "naming":
        commands += 'python\nold_name = bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval("(unsigned int)&gPlayerParty"))+8,10))\nend\n'
    commands += f"""
set gMain.savedCallback = (void *)CB2_ReturnToField
{entries[menu]}
set var sStopFrame = {start+200}
return
continue
python
callback = int(gdb.parse_and_eval("(unsigned int)gMain.callback2"))
assert callback != int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld")), "Menu did not open"
end
dump binary memory build/menu-matrix-{menu}/open-{cycle}.raw &sPixels ((char *)&sPixels)+153600
set var sStopFrame = {start+1000}
return
continue
python
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld")), "Menu did not return to field"
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes((0,16))
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)")) == 283
end
printf "MENU {menu} cycle {cycle} PASS\\n"
"""
    markers.append(f"MENU {menu} cycle {cycle} PASS")
    if menu == "naming" and cycle == 0:
        commands += 'python\nassert bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval("(unsigned int)&gPlayerParty"))+8,10)) != old_name, "Nickname unchanged"\nend\n'
commands += "continue\nquit\n"
print(f"PASS {menu}: 3 open/close cycles, field and party preserved;", run(scratch, commands, markers))
