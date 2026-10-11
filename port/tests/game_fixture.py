"""Own isolated debugger fixture setup shared by gameplay matrices."""
from pathlib import Path
import shutil
from process_watchdog import run_logged

PROJECT = Path(__file__).resolve().parents[2]


def prepare(name, inputs):
    template = PROJECT / "build/wild-battle-regression-catch/test.gdb"
    if not template.is_file():
        raise SystemExit("Run wild_battle_smoke.py --scenario catch first")
    scratch = PROJECT / "build" / name
    assert scratch.resolve().is_relative_to((PROJECT / "build").resolve())
    for directory in ("build", "roms", "saves"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    roms = list((PROJECT / "roms").glob("*.gba")); assert len(roms) == 1
    shutil.copy2(roms[0], scratch / "roms/test.gba")
    for filename in ("SDL2.dll", "emerald-pc-diagnostic.exe"):
        shutil.copy2(PROJECT / "build" / filename, scratch / "build" / filename)
    (scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
    (scratch / "input.txt").write_text(inputs, encoding="ascii")
    commands = template.read_text(encoding="ascii")
    commands = commands[:commands.index("call (void)CreateMon((void *)&gEnemyParty")]
    commands = commands.replace("wild-battle-regression-catch", name)
    return scratch, commands


def prepare_saved(name, inputs, save_path):
    """Resume a measured save instead of constructing a new party or progress."""
    saved = save_path.read_bytes()
    scratch, commands = prepare(name, inputs)
    (scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(saved)
    replacements = {
        "call (void)NewGameInitData()": "call (unsigned char)LoadGameSave(0)",
        "call (void)CreateMon((void *)&gPlayerParty,283,8,32,0,0,0,0)": "",
        "set *(unsigned char *)&gPlayerPartyCount = 1": "",
        "call (void)FlagSet(0x860)": "",
        "call (void)SetLastHealLocationWarp(1)": "",
        "call (void)SetMoney((void *)(*(unsigned int *)&gSaveBlock1Ptr+0x490),5000)": "",
    }
    for old, new in replacements.items():
        assert old in commands, "Catch fixture changed; review saved-game setup"
        commands = commands.replace(old, new)
    return scratch, commands


def run(scratch, commands, markers, timeout=600):
    script = scratch / "test.gdb"; script.write_text(commands, encoding="ascii")
    log = scratch / "gdb.log"
    code = run_logged(["gdb", "-batch", "-x", str(script),
                       str(scratch / "build/emerald-pc-diagnostic.exe")],
                      PROJECT, log, "PC diagnostic: frame=", timeout=timeout)
    text = log.read_text(encoding="utf-8", errors="replace")
    assert code == 0 and "received signal" not in text and "exited normally" in text, text[-4000:]
    for marker in markers:
        assert marker in text, marker
    return log
