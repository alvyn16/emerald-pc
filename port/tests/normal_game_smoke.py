"""Exercise the production binary under GDB, never the user's ROM/save files.

The debugger injects keys and skips pacing in its isolated process only.
No fixture creates Pokemon or starts battles. Unexpected battles are failures.
"""

from pathlib import Path
import shutil
import subprocess
import sys


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build/normal-game-regression"
    if not scratch.resolve().is_relative_to((project / "build").resolve()):
        raise SystemExit("Test directory must remain inside build/")
    for directory in ("build", "roms", "saves"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    roms = list((project / "roms").glob("*.gba"))
    if len(roms) != 1:
        raise SystemExit("Exactly one legal ROM is required in roms/")
    for name in ("emerald-pc.exe", "SDL2.dll"):
        shutil.copy2(project / "build" / name, scratch / "build" / name)
    shutil.copy2(roms[0], scratch / "roms/test.gba")
    (scratch / "saves/emerald-pc.sav").write_bytes(b"\xff" * 131072)
    inputs = scratch / "input.txt"
    subprocess.run([sys.executable, str(project / "port/tests/gameplay_smoke.py"),
                    str(inputs)], check=True)
    commands = r'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
# These must have no effect on the normal executable.
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_STOP_FRAME 1
set environment EMERALD_PC_INPUT_SCRIPT nonexistent-diagnostic-script.txt
break AgbMain
run
set {unsigned char}&WaitForFrameDeadline = 0xc3
delete 1
python
import gdb, struct
from pathlib import Path
events = []
bits = dict(A=1, B=2, SELECT=4, START=8, RIGHT=16, LEFT=32,
            UP=64, DOWN=128, R=256, L=512, NONE=0)
for line in Path("build/normal-game-regression/input.txt").read_text().splitlines():
    first, last, buttons = line.split()
    events.append((int(first), int(last), sum(bits[b] for b in buttons.split("+"))))
class Keys(gdb.Breakpoint):
    frame = -1
    def stop(self):
        self.frame += 1
        if self.frame >= 30500:
            address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
            group, number = bytes(gdb.selected_inferior().read_memory(address + 4, 2))
            print("NORMAL STOP frame=%d map=%d.%d" % (self.frame, group, number))
            if (group, number) != (0, 9):
                gdb.execute("quit 1")
            self.enabled = False
            return True
        pressed = next((mask for first, last, mask in events
                        if first <= self.frame <= last), 0)
        gdb.selected_inferior().write_memory(0x04000130, struct.pack("<H", 1023 ^ pressed))
        return False
class Battle(gdb.Breakpoint):
    def stop(self):
        print("FAIL unexpected wild battle during house exit")
        gdb.execute("bt")
        gdb.execute("quit 1")
Keys("ReadKeys")
Battle("BattleSetup_StartWildBattle")
end
continue
set $pc = &Port_ExitCleanly
continue
quit
'''
    script = scratch / "test.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "gdb.log"
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(["gdb", "-batch", "-x", str(script),
                                 str(scratch / "build/emerald-pc.exe")],
                                cwd=project, stdout=output, stderr=subprocess.STDOUT,
                                timeout=600)
    text = log.read_text(encoding="utf-8", errors="replace")
    if (result.returncode or "received signal" in text or "FAIL" in text
            or "NORMAL STOP frame=30500 map=0.9" not in text
            or "exited normally" not in text):
        raise SystemExit(f"Normal game regression failed: {log}")
    print(f"PASS normal game: house exit in Littleroot without a wild battle; {log}")


if __name__ == "__main__":
    main()
