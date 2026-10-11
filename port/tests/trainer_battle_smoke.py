"""Controlled trainer fixtures; requires wild_battle_smoke.py --scenario catch."""
from pathlib import Path
import argparse
import shutil
from process_watchdog import run_logged

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("scenario", choices=("trainer", "rival", "gym", "double", "poison", "switch", "item", "long", "evolution", "sidney", "phoebe", "glacia", "drake", "wallace"))
scenario = parser.parse_args().scenario
project = Path(__file__).resolve().parents[2]
template = project / "build/wild-battle-regression-catch/test.gdb"
assert template.is_file(), "Prepare the catch fixture first"
trainer = {"trainer": 318, "rival": 529, "gym": 265, "double": 481, "poison":318, "switch":318, "item":318, "long":331, "evolution":318, "sidney":261, "phoebe":262, "glacia":263, "drake":264, "wallace":335}[scenario]
league = scenario in ("sidney", "phoebe", "glacia", "drake", "wallace")
scratch = project / f"build/trainer-{scenario}"
for directory in ("build", "roms", "saves"):
    (scratch / directory).mkdir(parents=True, exist_ok=True)
roms = list((project / "roms").glob("*.gba")); assert len(roms) == 1
shutil.copy2(roms[0], scratch / "roms/test.gba")
for filename in ("SDL2.dll", "emerald-pc-diagnostic.exe"):
    shutil.copy2(project / "build" / filename, scratch / "build" / filename)
(scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
inputs = (template.parent / "input.txt").read_text()
inputs += "".join(f"{n} {n+1} A\n" for n in range(36900, 89800 if scenario == "long" or league else 49800, 40))
(scratch / "input.txt").write_text(inputs, encoding="ascii")
commands = template.read_text().replace("wild-battle-regression-catch", f"trainer-{scenario}")
commands = commands.replace("gPlayerParty,283,8,32", "gPlayerParty,280,15,32" if scenario == "evolution" else "gPlayerParty,68,60,32")
commands = commands.replace("set *(unsigned char *)&gPlayerPartyCount = 1", """
call (void)SetMonMoveSlot((void *)&gPlayerParty,157,0)
set *(unsigned char *)&gPlayerPartyCount = 1
""" + ("""
call (void)CreateMon((char *)&gPlayerParty+100,283,60,32,0,0,0,0)
call (void)SetMonMoveSlot((char *)&gPlayerParty+100,157,0)
set *(unsigned char *)&gPlayerPartyCount = 2
""" if scenario in ("double", "switch") else ""))
start = commands.index("call (void)CreateMon((void *)&gEnemyParty")
end = commands.index("set var sStopFrame = 37000", start)
extra = ""
if scenario == "evolution":
    extra = 'set $value = (unsigned int *)Alloc(4)\nset *$value = *((unsigned int *)&gExperienceTables + 3*101+16)-1\ncall (void)SetMonData((void *)&gPlayerParty,25,$value)\ncall (void)Free($value)\n'
if scenario == "poison": extra = 'set *(unsigned int *)((char *)&gPlayerParty+80) = 8\n'
if scenario == "item": extra = 'call (int)AddBagItem(13,1)\nset *((unsigned char *)&gBagPosition+5) = 0\nset *(unsigned short *)((char *)&gPlayerParty+86) = 1\n'
if scenario == "long":
    extra = 'call (void)SetMonMoveSlot((void *)&gPlayerParty,45,0)\n'
    extra += ''.join(f'call (void)SetMonMoveSlot((void *)&gPlayerParty,157,{slot})\n' for slot in range(1,4))
commands = commands[:start] + extra + f"""
set $start_exp = (unsigned int)GetMonData3((void *)&gPlayerParty,25,0)
set *(unsigned short *)&gTrainerBattleOpponent_A = {trainer}
call (void)BattleSetup_StartTrainerBattle()
""" + commands[end:]
commands = commands.replace("CB2_EndWildBattle", "CB2_EndTrainerBattle").replace("sStopFrame = 37000", "sStopFrame = " + ("90000" if scenario == "long" else "50000"))
commands = commands.replace("disable 3\ncontinue\nend", "set var sStopFrame = sDiagnosticFrame + " + ("7000" if scenario == "evolution" else "1500") + "\ndisable 3\ncontinue\nend")
start = commands.index("\nbreak HandleInputChooseAction")
end = commands.index('continue\nprintf "STOP', start)
hooks = ""
if scenario in ("switch", "item"):
    hooks = f"""
set $chosen = 0
break HandleInputChooseAction
commands
silent
set ((unsigned char *)&gActionSelectionCursor)[*(unsigned char *)&gActiveBattler] = {2 if scenario == 'switch' else 1} * ($chosen == 0)
set $chosen = 1
set gMain.newKeys = 1
continue
end
break Task_HandleChooseMonInput
commands
silent
set *((signed char *)&gPartyMenu+9) = {1 if scenario == 'switch' else 0}
set gMain.newKeys = 1
continue
end
"""
if scenario == "poison":
    hooks = """
break HandleInputChooseAction
commands
silent
python
assert int(gdb.parse_and_eval("*((unsigned char *)&gBattleMons+0x20)")) == 62
assert int(gdb.parse_and_eval("*((unsigned int *)((char *)&gBattleMons+0x4c))")) & 8
end
printf "GUTS poison active\\n"
disable $bpnum
continue
end
"""
if scenario == "long":
    hooks = """
break HandleInputChooseMove
commands
silent
python
turn = int(gdb.parse_and_eval("*((unsigned char *)&gBattleResults+0x13)"))
slot = 0 if turn < 8 else next(i for i in range(1,4) if int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,%d,0)" % (17+i))) > 0)
gdb.execute("set ((unsigned char *)&gMoveSelectionCursor)[*(unsigned char *)&gActiveBattler] = %d" % slot)
gdb.execute("set gMain.newKeys = 1")
end
continue
end
"""
commands = commands[:start] + hooks + commands[end:]
if league:
    commands = commands.replace("gPlayerParty,68,60,32", "gPlayerParty,404,95,32")
    commands = commands.replace("call (void)SetMonMoveSlot((void *)&gPlayerParty,157,0)", "".join(f"call (void)SetMonMoveSlot((void *)&gPlayerParty,{move},{slot})\n" for slot,move in enumerate((57,58,85,247))))
    commands = commands.replace("sStopFrame = 50000", "sStopFrame = 90000")
    commands = commands.replace('continue\nprintf "STOP', '''break HandleInputChooseMove
commands
silent
python
enemy = int(gdb.parse_and_eval("(unsigned int)GetMonData3((char *)&gEnemyParty+100*((unsigned short *)&gBattlerPartyIndexes)[1],11,0)"))
preferred = 1 if SCENARIO == "drake" else (0 if enemy == 324 else 2) if SCENARIO == "wallace" else 0
slot = next(i for i in [preferred]+list(range(4)) if int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,%d,0)" % (17+i))) > 0)
gdb.execute("set ((unsigned char *)&gMoveSelectionCursor)[*(unsigned char *)&gActiveBattler] = %d" % slot)
gdb.execute("set gMain.newKeys = 1")
end
continue
end
continue
printf "STOP''')
commands = commands.replace("SCENARIO", repr(scenario))
start = commands.index("python\nassert", commands.index('printf "STOP'))
end = commands.index("bt\ndump", start)
extra_checks = ""
if scenario == "evolution": extra_checks = 'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,56,0)")) == 16\nassert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,11,0)")) == 281\nassert any(int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,%d,0)" % (13+i))) == 24 for i in range(4))\n'
if scenario == "poison": extra_checks = 'assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,55,0)")) & 8\n'
if scenario == "switch": extra_checks = 'assert int(gdb.parse_and_eval("*((unsigned char *)&gBattleResults+2)")) >= 1\n'
if scenario == "item": extra_checks = 'assert int(gdb.parse_and_eval("*((unsigned char *)&gBattleResults+3)")) == 1\nassert int(gdb.parse_and_eval("(int)CheckBagHasItem(13,1)")) == 0\n'
if scenario == "long": extra_checks = 'assert int(gdb.parse_and_eval("*((unsigned char *)&gBattleResults+0x13)")) >= 10\n'
commands = commands[:start] + f"""
python
{extra_checks}assert int(gdb.parse_and_eval("*(unsigned char *)&gBattleOutcome")) == 1, "Expected trainer victory"
assert int(gdb.parse_and_eval("(int)HasTrainerBeenFought({trainer})")) == 1
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,25,0)")) > int(gdb.parse_and_eval("$start_exp"))
assert int(gdb.parse_and_eval("(unsigned int)GetMonData3((void *)&gPlayerParty,57,0)")) > 0
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes((0,16))
assert int(gdb.parse_and_eval("(unsigned int)GetMoney((void *)(%d+0x490))" % address)) > 5000
assert int(gdb.parse_and_eval("(unsigned int)gMain.callback2")) == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld"))
end
printf "TRAINER {scenario} SEMANTIC PASS turns=%u switches=%u heals=%u\\n", *((unsigned char *)&gBattleResults+0x13), *((unsigned char *)&gBattleResults+2), *((unsigned char *)&gBattleResults+3)
""" + commands[end:]
script = scratch / "test.gdb"; script.write_text(commands, encoding="ascii")
log = scratch / "gdb.log"
result = run_logged(["gdb", "-batch", "-x", str(script), str(scratch / "build/emerald-pc-diagnostic.exe")], project, log, "PC diagnostic: frame=")
text = log.read_text(encoding="utf-8", errors="replace")
assert result == 0 and "received signal" not in text and "exited normally" in text, text[-2000:]
assert f"TRAINER {scenario} SEMANTIC PASS" in text
print(f"PASS {scenario}: victory, XP, money, trainer flag and field return; {log}")
