"""Storage callback lifetime fixture; run wild_battle_smoke.py first."""

from pathlib import Path
import shutil

from process_watchdog import run_logged


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build/wild-battle-regression"
    source = scratch / "test.gdb"
    if not source.is_file():
        raise SystemExit("Run wild_battle_smoke.py to prepare the isolated fixture first")
    shutil.copy2(project / "build/emerald-pc-diagnostic.exe",
                 scratch / "build/emerald-pc-diagnostic.exe")
    (scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
    commands = source.read_text()
    start = commands.index("call (void)SetWarpDestination")
    end = commands.index("set var sStopFrame = 31000", start)
    commands = commands[:start] + "call (void)EnterPokeStorage(2)\n" + commands[end:]
    start = commands.index("python\naddress", commands.index("set var sStopFrame = 31000"))
    commands = commands[:start] + r'''
printf "STORAGE loaded frame=%u\n", sDiagnosticFrame
call (void)FreePokeStorageData()
python
assert int(gdb.parse_and_eval("(unsigned int)gMain.vblankCallback")) == 0, "Storage callback still registered after cleanup"
end
set var sStopFrame = 31500
call (void)PortHost_RunFrame()
call (void)SetMainCallback2((void *)CB2_ExitPokeStorage)
return
continue
printf "STORAGE returned frame=%u\n", sDiagnosticFrame
continue
quit
'''
    script = scratch / "storage.gdb"
    script.write_text(commands, encoding="ascii")
    log = scratch / "storage.log"
    result = run_logged(["gdb", "-batch", "-x", str(script),
                         str(scratch / "build/emerald-pc-diagnostic.exe")],
                        project, log, "PC diagnostic: frame=")
    text = log.read_text(errors="replace")
    if (result or "received signal" in text or "STORAGE loaded frame=31000" not in text
            or "STORAGE returned frame=31500" not in text or "exited normally" not in text):
        raise SystemExit(f"Storage regression failed: {log}")
    print(f"PASS storage: cleanup before cooperative VBlank and clean return; {log}")


if __name__ == "__main__":
    main()
