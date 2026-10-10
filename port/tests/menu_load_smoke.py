"""Load and close summary/party menus in isolated debugger fixtures.

Requires the fixture template prepared by wild_battle_smoke.py. Game entry
is prepared in GDB; subsequent loading and B-button closing use game code.
"""

from pathlib import Path
import shutil
import sys

from process_watchdog import run_logged


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("summary", "party"):
        raise SystemExit("usage: python menu_load_smoke.py summary|party")
    menu = sys.argv[1]
    project = Path(__file__).resolve().parents[2]
    template = project / "build/wild-battle-regression/test.gdb"
    if not template.is_file():
        raise SystemExit("Run wild_battle_smoke.py to prepare the fixture template")
    scratch = project / f"build/menu-load-{menu}"
    if not scratch.resolve().is_relative_to((project / "build").resolve()):
        raise SystemExit("Fixture directory must remain in build/")
    for directory in ("build", "roms", "saves"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    for filename in ("emerald-pc-diagnostic.exe", "SDL2.dll"):
        shutil.copy2(project / "build" / filename, scratch / "build" / filename)
    roms = list((project / "roms").glob("*.gba"))
    if len(roms) != 1:
        raise SystemExit("Exactly one legal ROM is required")
    shutil.copy2(roms[0], scratch / "roms/test.gba")
    (scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
    # Keep the known house-exit route; only B is used after entering the menu.
    inputs = (project / "build/wild-battle-regression/input.txt").read_text()
    inputs = "".join(line + "\n" for line in inputs.splitlines()
                     if int(line.split()[0]) < 30500)
    inputs += "31200 31201 B\n31300 31301 B\n31400 31401 B\n"
    (scratch / "input.txt").write_text(inputs, encoding="ascii")
    commands = template.read_text().replace(
        "build/wild-battle-regression/input.txt", f"build/menu-load-{menu}/input.txt")
    start = commands.index("call (void)SetWarpDestination")
    commands = commands[:start]
    entry = (
        "call (void)ShowPokemonSummaryScreen(0,(void *)&gPlayerParty,0,0,(void *)CB2_ReturnToField)"
        if menu == "summary" else
        "call (void)InitPartyMenu(0,0,0,0,0,(void *)Task_HandleChooseMonInput,(void *)CB2_ReturnToField)"
    )
    commands += entry + r'''
set var sStopFrame = 31100
python
class LoadProbe(gdb.Breakpoint):
    previous = None
    repeats = 0
    def stop(self):
        state = (int(gdb.parse_and_eval("gMain.state")),
                 int(gdb.parse_and_eval("sDiagnosticFrame")))
        self.repeats = self.repeats + 1 if state == self.previous else 0
        self.previous = state
        if self.repeats >= 256:
            print("LOAD STALLED state=%d frame=%d" % state, flush=True)
            gdb.execute("bt")
            gdb.execute("info registers")
            gdb.execute("quit 1")
        return False
probe = LoadProbe("MenuHelpers_ShouldWaitForLinkRecv")
end
return
continue
python
probe.enabled = False
callback = int(gdb.parse_and_eval("(unsigned int)gMain.callback2"))
READY_ASSERTION
end
printf "MENU READY frame=%u\n", sDiagnosticFrame
dump binary memory CAPTURE_PATH &sPixels ((char *)&sPixels)+153600
set var sStopFrame = 31600
return
continue
python
callback = int(gdb.parse_and_eval("(unsigned int)gMain.callback2"))
assert callback == int(gdb.parse_and_eval("(unsigned int)&CB2_Overworld")), "B did not return to overworld"
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address + 4, 2)) == bytes((0, 9))
end
printf "MENU RETURN frame=%u\n", sDiagnosticFrame
continue
quit
'''
    assertion = (
        'assert callback != int(gdb.parse_and_eval("(unsigned int)&CB2_InitSummaryScreen")) '
        'and int(gdb.parse_and_eval("*(unsigned int *)&sMonSummaryScreen")) != 0 '
        'and int(gdb.parse_and_eval("(unsigned int)gMain.vblankCallback")) != 0, "Summary not ready"'
        if menu == "summary" else
        'assert callback == int(gdb.parse_and_eval("(unsigned int)&CB2_UpdatePartyMenu")), "Party not ready"'
    )
    commands = commands.replace("READY_ASSERTION", assertion)
    commands = commands.replace("CAPTURE_PATH", f"build/menu-load-{menu}/menu.raw")
    script = scratch / "test.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "gdb.log"
    result = run_logged(["gdb", "-batch", "-x", str(script),
                         str(scratch / "build/emerald-pc-diagnostic.exe")],
                        project, log, "PC diagnostic: frame=")
    text = log.read_text(errors="replace")
    if (result or "received signal" in text or "LOAD STALLED" in text
            or "MENU READY frame=31100" not in text or "MENU RETURN frame=31600" not in text
            or "exited normally" not in text):
        raise SystemExit(f"{menu} load regression failed; inspect {log}")
    print(f"PASS {menu}: loaded, closed with B and returned to Littleroot")


if __name__ == "__main__":
    main()
