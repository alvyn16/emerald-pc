"""RTC integration through the bedroom clock and real daily/berry functions."""
from pathlib import Path
import shutil
import subprocess
import sys
from process_watchdog import run_logged

project = Path(__file__).resolve().parents[2]
scratch = project / "build/rtc-game-regression"
for name in ("build", "roms", "saves"):
    (scratch/name).mkdir(parents=True, exist_ok=True)
roms = list((project/"roms").glob("*.gba"))
assert len(roms) == 1
shutil.copy2(roms[0], scratch/"roms/test.gba")
for name in ("SDL2.dll", "emerald-pc-diagnostic.exe"):
    shutil.copy2(project/"build"/name, scratch/"build"/name)
(scratch/"saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff"*131072)
(scratch/"saves/emerald-pc-diagnostic.rtc").write_text("EMERALD_PC_RTC 1\n0 1709164800 64\n", encoding="ascii")
subprocess.run([sys.executable, str(project/"port/tests/gameplay_smoke.py"),str(scratch/"input.txt")],check=True)
commands = r"""
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_INPUT_SCRIPT build/rtc-game-regression/input.txt
set environment EMERALD_PC_STOP_FRAME 30500
break PortRtc_Open
run
call (void)PortRtc_DiagnosticSetTime(1709164800LL)
disable 1
break RtcInitLocalTimeOffset
commands
silent
printf "BEDROOM CLOCK set frame=%u\n", sDiagnosticFrame
continue
end
break Port_ExitCleanly
continue
python
assert int(gdb.parse_and_eval("(unsigned short)RtcGetErrorStatus()")) == 0
assert int(gdb.parse_and_eval("(unsigned char)FlagGet(0x895)")) == 1, "Clock must be set by bedroom route"
end
call (void)PlantBerryTree(0,1,1,1)
call (void)DoTimeBasedEvents()
call (void)PortRtc_DiagnosticSetTime(1709175600LL)
call (void)DoTimeBasedEvents()
python
assert int(gdb.parse_and_eval("(unsigned char)GetStageByBerryTreeId(0)")) == 2, "Cheri berry should sprout after three hours"
end
printf "BERRY sprouted after 3h\n"
call (void)PortRtc_DiagnosticSetTime(1709251200LL)
call (void)DoTimeBasedEvents()
python
assert int(gdb.parse_and_eval("(unsigned short)VarGet(0x4040)")) == 1, "Daily event did not advance"
gdb.execute("set $berry_time = *(unsigned long long *)(*(unsigned int *)&gSaveBlock2Ptr + 0xa0)")
end
printf "DAILY counter=1\n"
call (void)PortRtc_DiagnosticSetTime(1709078400LL)
call (void)DoTimeBasedEvents()
python
assert int(gdb.parse_and_eval("(unsigned short)VarGet(0x4040)")) == 1
assert int(gdb.parse_and_eval("*(unsigned long long *)(*(unsigned int *)&gSaveBlock2Ptr + 0xa0)")) == int(gdb.parse_and_eval("$berry_time"))
end
printf "ROLLBACK no duplicate events\n"
continue
quit
"""
script = scratch/"test.gdb"
script.write_text(commands, encoding="ascii")
log = scratch/"gdb.log"
result = run_logged(["gdb","-batch","-x",str(script),str(scratch/"build/emerald-pc-diagnostic.exe")],project,log,"PC diagnostic: frame=")
text = log.read_text(encoding="utf-8",errors="replace")
assert result == 0 and "received signal" not in text and "exited normally" in text, text[-3000:]
for marker in ("BEDROOM CLOCK set", "BERRY sprouted", "DAILY counter=1", "ROLLBACK no duplicate"):
    assert marker in text, marker
print("PASS RTC: bedroom, berry growth, daily event and rollback;",log)
