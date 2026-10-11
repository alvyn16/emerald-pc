"""Measure real SDL output at 1x-4x; private ROM, saves and WAVs stay in build/."""
from pathlib import Path
import array
import json
import math
import re
import shutil
import wave
from process_watchdog import run_logged

project = Path(__file__).resolve().parents[2]
scratch = project / "build/audio-output-regression"
for directory in ("build", "roms", "saves"):
    (scratch / directory).mkdir(parents=True, exist_ok=True)
roms = list((project / "roms").glob("*.gba"))
assert len(roms) == 1
shutil.copy2(roms[0], scratch / "roms/test.gba")
for name in ("SDL2.dll", "emerald-pc-diagnostic.exe"):
    shutil.copy2(project / "build" / name, scratch / "build" / name)
(scratch / "saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff" * 131072)
results = {}
for scene, call in (("title", "m4aSongNumStart(413)"),
                    ("menu", "PlaySE(5)"),
                    ("battle", "m4aSongNumStart(474)"),
                    ("torchic", "PlayCry_Normal(280,0)")):
    for speed in range(1, 5):
        name = f"{scene}-{speed}x"
        wav = scratch / f"{name}.wav"
        commands = f"""
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
unset environment SDL_AUDIODRIVER
set environment EMERALD_PC_FAST 0
set environment EMERALD_PC_STOP_FRAME 241
set environment EMERALD_PC_AUDIO_DUMP build/audio-output-regression/{name}.wav
break PortHost_RunFrame
run
set var sMultiplier = {speed}
set *(void **)&gMain = 0
call (void)SetMainCallback2((void *)DummyFunc)
call (void)SetVBlankCallback(0)
call (void)m4aMPlayAllStop()
call (void){call}
disable 1
continue
quit
"""
        script = scratch / f"{name}.gdb"
        script.write_text(commands, encoding="ascii")
        log = scratch / f"{name}.log"
        code = run_logged(["gdb", "-batch", "-x", str(script),
                           str(scratch / "build/emerald-pc-diagnostic.exe")],
                          project, log, "PC diagnostic: frame=")
        text = log.read_text(encoding="utf-8", errors="replace")
        assert code == 0 and "received signal" not in text and "exited normally" in text, text[-2000:]
        stats = re.search(r"peak_queue=(\d+) clears=(\d+) errors=(\d+) reconnects=(\d+) device=(\d+)", text)
        assert stats, text[-2000:]
        peak_queue, clears, errors, reconnects, device = map(int, stats.groups())
        assert peak_queue <= 7200 and errors == 0
        # Device absence is reported, never disguised as a real-device pass.
        assert device != 0, "No real SDL audio device: run backend tests and report manual output pending"
        with wave.open(str(wav), "rb") as source:
            assert source.getframerate() == 48000 and source.getnchannels() == 2
            assert source.getsampwidth() == 2
            frames = source.getnframes()
            pcm = array.array("h", source.readframes(frames))
        duration = frames / 48000
        assert abs(duration - 241 * 224 / 13379 / speed) < 0.001
        assert any(pcm)
        # Compare discontinuities at frame boundaries with ordinary adjacent deltas.
        boundaries = {math.ceil(n * 224 * 48000 / (13379 * speed)) for n in range(1, 241)}
        jumps = [abs(pcm[i * 2 + ch] - pcm[(i - 1) * 2 + ch])
                 for i in range(1, frames) for ch in range(2)]
        boundary_jumps = [abs(pcm[i * 2 + ch] - pcm[(i - 1) * 2 + ch])
                          for i in boundaries if i < frames for ch in range(2)]
        results[name] = dict(duration_seconds=duration, peak=max(abs(x) for x in pcm),
                             saturated_samples=sum(x in (-32768, 32767) for x in pcm),
                             rms=math.sqrt(sum(x*x for x in pcm) / len(pcm)),
                             max_adjacent_delta=max(jumps), max_boundary_delta=max(boundary_jumps),
                             queue_peak_frames=peak_queue, queue_clears=clears,
                             queue_errors=errors, reconnects=reconnects)
        print(f"PASS {name}: {duration:.6f}s, queue {peak_queue}/7200, clears {clears}", flush=True)
(scratch / "measurements.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("PASS real SDL output: 16 scene/speed runs;", scratch)
