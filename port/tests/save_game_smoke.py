"""Exercise game save dialogs, restart, and slot recovery in build/ only.

Requires wild_battle_smoke.py's new-game fixture template. GDB prepares
known semantic values; the real save UI/task runs with scripted A presses.
"""

from pathlib import Path
import os
import shutil
import struct
import sys

from process_watchdog import run_logged


def run_case(project: Path, scratch: Path, name: str, commands: str,
             killed: bool = False) -> str:
    script = scratch / f"{name}.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / f"{name}.log"
    result = run_logged(["gdb", "-batch", "-x", str(script),
                         str(scratch / "build/emerald-pc-diagnostic.exe")],
                        project, log, "PC diagnostic: frame=")
    text = log.read_text(errors="replace")
    expected_exit = "killed" if killed else "exited normally"
    if result or "received signal" in text or expected_exit not in text:
        raise SystemExit(f"Save regression {name} failed; inspect {log}")
    return text


def main() -> None:
    if sys.argv[1:] not in ([], ["--reload-only"]):
        raise SystemExit("usage: python save_game_smoke.py [--reload-only]")
    reuse_save = bool(sys.argv[1:])
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build/save-game-regression"
    template = project / "build/wild-battle-regression/test.gdb"
    if not template.is_file():
        raise SystemExit("Run wild_battle_smoke.py to prepare the fixture template")
    for directory in ("build", "roms", "saves"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    for filename in ("emerald-pc-diagnostic.exe", "SDL2.dll"):
        shutil.copy2(project / "build" / filename, scratch / "build" / filename)
    roms = list((project / "roms").glob("*.gba"))
    if len(roms) != 1:
        raise SystemExit("Exactly one legal ROM is required")
    shutil.copy2(roms[0], scratch / "roms/test.gba")
    save = scratch / "saves/emerald-pc-diagnostic.sav"
    if not reuse_save:
        save.write_bytes(b"\xff" * 131072)
    normal_save = scratch / "saves/emerald-pc.sav"
    normal_save.write_bytes(b"\xa5" * 131072)
    inputs = (project / "build/wild-battle-regression/input.txt").read_text()
    inputs = "".join(line + "\n" for line in inputs.splitlines()
                     if int(line.split()[0]) < 30500)
    for first, last in ((30710, 31990), (32210, 33690)):
        inputs += "".join(f"{frame} {frame + 1} A\n" for frame in range(first, last, 35))
    (scratch / "input.txt").write_text(inputs, encoding="ascii")
    commands = template.read_text().replace(
        "build/wild-battle-regression/input.txt", "build/save-game-regression/input.txt")
    commands = commands[:commands.index("call (void)SetWarpDestination")]
    commands += r'''
call (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),12345)
call (unsigned char)AddBagItem(13,7)
call (unsigned char)VarSet(0x4023,1)
call (void)ShowStartMenu()
set var sStopFrame = 30700
return
continue
call (unsigned char)StartMenuSaveCallback()
set var sStopFrame = 32000
return
continue
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gSaveAttemptStatus")) == 1
assert int(gdb.parse_and_eval("*(unsigned int *)&gSaveCounter")) == 1
layout = bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval("(unsigned int)&sSaveSlotLayout")),56))
open("build/save-game-regression/layout.bin","wb").write(layout)
end
printf "SAVE FIRST counter=%u frame=%u\n", *(unsigned int *)&gSaveCounter, sDiagnosticFrame
call (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),23456)
call (unsigned char)VarSet(0x4023,2)
call (void)ShowStartMenu()
set var sStopFrame = 32200
return
continue
call (unsigned char)StartMenuSaveCallback()
set var sStopFrame = 33700
return
continue
python
assert int(gdb.parse_and_eval("*(unsigned char *)&gSaveAttemptStatus")) == 1
assert int(gdb.parse_and_eval("*(unsigned int *)&gSaveCounter")) == 2
end
printf "SAVE SECOND counter=%u frame=%u\n", *(unsigned int *)&gSaveCounter, sDiagnosticFrame
continue
quit
'''
    if not reuse_save:
        text = run_case(project, scratch, "create", commands)
        if "SAVE FIRST counter=1" not in text or "SAVE SECOND counter=2" not in text:
            raise SystemExit("Both game save operations must complete")
        (scratch / "two-slots.sav").write_bytes(save.read_bytes())
    saved = (scratch / "two-slots.sav").read_bytes()
    sizes = [size for offset, size in struct.iter_unpack("<HH", (scratch / "layout.bin").read_bytes())]
    for slot in (0, 1):
        ids = set()
        for sector in range(slot * 14, slot * 14 + 14):
            data = saved[sector * 4096:(sector + 1) * 4096]
            ident, checksum, signature, counter = struct.unpack_from("<HHII", data, 4084)
            assert ident < 14 and signature == 0x08012025
            total = sum(word[0] for word in struct.iter_unpack("<I", data[:sizes[ident] // 4 * 4])) & 0xffffffff
            assert ((total >> 16) + total) & 0xffff == checksum
            assert counter == (2 if slot == 0 else 1)
            ids.add(ident)
        assert ids == set(range(14)), "Incomplete save slot"

    def load(name: str, data: bytes, counter: int, money: int, progress: int, status: int) -> None:
        save.write_bytes(data)
        commands = r'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
unset environment EMERALD_PC_INPUT_SCRIPT
unset environment EMERALD_PC_STOP_FRAME
break LoadGameSave
run
finish
python
assert int(gdb.parse_and_eval("*(unsigned short *)&gSaveFileStatus")) == EXPECT_STATUS
assert int(gdb.parse_and_eval("*(unsigned int *)&gSaveCounter")) == EXPECT_COUNTER
assert int(gdb.parse_and_eval("*(unsigned char *)&gPlayerPartyCount")) == 1
assert int(gdb.parse_and_eval("(unsigned int)GetMonData2((void *)&gPlayerParty,11)")) == 280
address = int(gdb.parse_and_eval("*(unsigned int *)&gSaveBlock1Ptr"))
assert bytes(gdb.selected_inferior().read_memory(address+4,2)) == bytes((0,9))
assert int(gdb.parse_and_eval("(unsigned int)GetMoney((void *)(%d+0x490))" % address)) == EXPECT_MONEY
assert int(gdb.parse_and_eval("(unsigned char)CheckBagHasItem(13,7)")) == 1
assert int(gdb.parse_and_eval("(unsigned char)CheckBagHasItem(13,8)")) == 0
assert int(gdb.parse_and_eval("(unsigned char)FlagGet(0x860)")) == 1
assert int(gdb.parse_and_eval("(unsigned short)VarGet(0x4023)")) == EXPECT_PROGRESS
end
printf "SAVE RELOAD verified\n"
set $pc = (unsigned int)&Port_ExitCleanly
continue
quit
'''
        for token, value in (("STATUS", status), ("COUNTER", counter), ("MONEY", money), ("PROGRESS", progress)):
            commands = commands.replace(f"EXPECT_{token}", str(value))
        text = run_case(project, scratch, name, commands)
        assert "SAVE RELOAD verified" in text
        assert save.read_bytes() == data, "Reload modified the save"

    load("reload", saved, 2, 23456, 2, 1)
    damaged = bytearray(saved)
    damaged[0] ^= 1  # Change payload without updating checksum in newest slot.
    load("recover-checksum", damaged, 1, 12345, 1, 255)
    damaged = bytearray(saved)
    struct.pack_into("<H", damaged, 4084, 0xffff)
    load("recover-invalid-id", damaged, 1, 12345, 1, 255)

    # Interrupt a third save after four sector writes; the latest complete
    # slot must survive, even without running the host's close handler.
    save.write_bytes(saved)
    commands = r'''
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
unset environment EMERALD_PC_INPUT_SCRIPT
unset environment EMERALD_PC_STOP_FRAME
break LoadGameSave
run
finish
call (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),34567)
call (unsigned char)VarSet(0x4023,3)
break PortFlash_ProgramSector
ignore 2 4
python
try:
    gdb.execute("call (unsigned char)TrySavingData(0)")
except gdb.error:
    assert gdb.newest_frame().name() == "PortFlash_ProgramSector"
else:
    raise RuntimeError("Save did not stop at the fifth sector")
end
printf "SAVE INTERRUPTED counter=%u\n", *(unsigned int *)&gSaveCounter
kill
quit
'''
    text = run_case(project, scratch, "interrupt-write", commands, killed=True)
    assert "SAVE INTERRUPTED counter=3" in text
    load("recover-interrupted-write", save.read_bytes(), 2, 23456, 2, 255)

    # Failed writable opens must stop host startup, before a nonprogressing
    # window appears. No resize or data writes are allowed on either failure.
    for name, data in (("invalid-size", b"bad save size"), ("read-only", saved)):
        save.write_bytes(data)
        if name == "read-only":
            os.chmod(save, 0o444)
        environment = os.environ.copy()
        os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        for key in ("EMERALD_PC_INPUT_SCRIPT", "EMERALD_PC_STOP_FRAME"):
            os.environ.pop(key, None)
        try:
            log = scratch / f"{name}.log"
            result = run_logged([str(scratch / "build/emerald-pc-diagnostic.exe")],
                                project, log, "PC diagnostic: frame=", timeout=20)
            text = log.read_text(errors="replace")
            assert result == 1 and "cannot open save; startup aborted" in text
            assert "SDL window ready" not in text
            assert save.read_bytes() == data, "Failed save modified the original file"
        finally:
            os.environ.clear()
            os.environ.update(environment)
            if name == "read-only":
                os.chmod(save, 0o666)
    save.write_bytes(saved)
    assert normal_save.read_bytes() == b"\xa5" * 131072
    print("PASS game save: semantic reload, checksums, corrupt slot and interrupted-write recovery")


if __name__ == "__main__":
    main()
