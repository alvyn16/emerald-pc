"""Capture identified real m4a sequences in isolated diagnostic processes."""
from pathlib import Path
import array
import json
import math
import shutil
import wave
from process_watchdog import run_logged

project=Path(__file__).resolve().parents[2]
scratch=project/"build/audio-scene-regression"
for directory in ("build","roms","saves"):
    (scratch/directory).mkdir(parents=True,exist_ok=True)
roms=list((project/"roms").glob("*.gba")); assert len(roms)==1
shutil.copy2(roms[0],scratch/"roms/test.gba")
for name in ("SDL2.dll","emerald-pc-diagnostic.exe"):
    shutil.copy2(project/"build"/name,scratch/"build"/name)
(scratch/"saves/emerald-pc-diagnostic.sav").write_bytes(b"\xff"*131072)
measurements={}
for name,call in (("title","m4aSongNumStart(413)"),("select","PlaySE(5)"),("torchic","PlayCry_Normal(280,0)")):
    wav=scratch/(name+".wav")
    commands=f"""
set pagination off
set confirm off
set environment SDL_VIDEODRIVER dummy
set environment SDL_AUDIODRIVER dummy
set environment EMERALD_PC_FAST 1
set environment EMERALD_PC_STOP_FRAME 601
set environment EMERALD_PC_AUDIO_DUMP build/audio-scene-regression/{name}.wav
break PortHost_RunFrame
run
set *(void **)&gMain = 0
call (void)SetMainCallback2((void *)DummyFunc)
call (void)SetVBlankCallback(0)
call (void)m4aMPlayAllStop()
call (void){call}
disable 1
continue
quit
"""
    script=scratch/(name+".gdb");script.write_text(commands,encoding="ascii")
    log=scratch/(name+".log")
    result=run_logged(["gdb","-batch","-x",str(script),str(scratch/"build/emerald-pc-diagnostic.exe")],project,log,"PC diagnostic: frame=")
    text=log.read_text(encoding="utf-8",errors="replace")
    assert not result and "received signal" not in text and "exited normally" in text, text[-2000:]
    with wave.open(str(wav),"rb") as source:
        assert source.getframerate()==48000 and source.getnchannels()==2 and source.getsampwidth()==2
        samples=array.array("h",source.readframes(source.getnframes()))
        duration=source.getnframes()/48000
    assert 10.0<duration<10.1 and any(samples), (name,duration)
    measurements[name]={"duration_seconds":duration,"peak":max(abs(x) for x in samples),
        "rms":math.sqrt(sum(x*x for x in samples)/len(samples)),
        "saturated_samples":sum(x in (-32768,32767) for x in samples),
        "nonzero_stereo_frames":sum(samples[i]!=0 or samples[i+1]!=0 for i in range(0,len(samples),2))}
(scratch/"measurements.json").write_text(json.dumps(measurements,indent=2),encoding="utf-8")
print("PASS audio scenes: MUS_TITLE 413, SE_SELECT 5, Torchic cry 280;",scratch)
