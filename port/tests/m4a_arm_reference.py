"""Execute local GBA mixer code on private synthetic waves, never distribute ROM/code.
Optional: pip install unicorn. Requires the verified upstream .elf and .gba.
"""
from pathlib import Path
import json
import struct
import subprocess
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

root = Path(__file__).resolve().parents[2]
nm = root / "pokeemerald/.toolchains/arm-binutils-2.43.1/mingw64/bin/arm-none-eabi-nm.exe"
symbols = {}
for line in subprocess.check_output([str(nm), "-n",str(root/"pokeemerald/pokeemerald.elf")],text=True).splitlines():
    fields=line.split()
    if len(fields)==3:
        symbols[fields[2]]=int(fields[0],16)
rom=(root/"pokeemerald/pokeemerald.gba").read_bytes()

def run(name, data, wave_type=0, voice_type=8, channels=1, reverb=0, initial=0,
        frequency=1, divfreq=0x400000):
    cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    for address,size in ((0x02000000,0x40000),(0x03000000,0x8000),(0x04000000,0x1000),(0x08000000,0x2000000)):
        cpu.mem_map(address,size)
    cpu.mem_write(0x08000000,rom)
    ram=symbols["SoundMainRAM_Buffer"]
    code=symbols["SoundMainRAM"] & ~1
    cpu.mem_write(ram, bytes(cpu.mem_read(code,0x800)))
    cpu.mem_write(0x03007010,b"\x70\x47") # Own no-op CGB callback.
    sound=0x02000000; wave=0x02008000
    cpu.mem_write(0x03007ff0,struct.pack("<I",sound))
    cpu.mem_write(sound, struct.pack("<I",0x68736d53))
    def write(field, value, fmt="I"):
        cpu.mem_write(sound+symbols["o_SoundInfo_"+field],struct.pack("<"+fmt,value))
    for field,value in (("pcmDmaCounter",0),("pcmDmaPeriod",7),("maxChans",channels),("masterVolume",15),("reverb",reverb)):
        write(field,value,"B")
    for field,value in (("pcmSamplesPerVBlank",224),("divFreq",divfreq),("CgbSound",0x03007011)):
        write(field,value)
    size=64 if wave_type else len(data)
    cpu.mem_write(wave,struct.pack("<HHIII",wave_type,0xc000,13379*1024,0,size)+bytes(data))
    for index in range(channels):
        addr=sound+symbols["o_SoundInfo_chans"]+index*64
        def channel(field,value,fmt="B"):
            cpu.mem_write(addr+symbols["o_SoundChannel_"+field],struct.pack("<"+fmt,value))
        for field,value in (("statusFlags",0x80),("type",voice_type),("leftVolume",255),("rightVolume",255),("attack",255),("decay",255),("sustain",255)):
            channel(field,value)
        channel("wav",wave,"I"); channel("frequency",frequency,"I")
    pcm=sound+symbols["o_SoundInfo_pcmBuffer"]
    cpu.mem_write(pcm,bytes([initial&255])*3168)
    cpu.reg_write(UC_ARM_REG_SP,0x03007e00);cpu.reg_write(UC_ARM_REG_LR,0x03007001)
    cpu.emu_start(symbols["SoundMain"]|1,0x03007000,count=1000000)
    assert cpu.reg_read(UC_ARM_REG_PC) == 0x03007000, "ARM reference hit its instruction budget"
    assert bytes(cpu.mem_read(sound,4)) == struct.pack("<I",0x68736d53)
    result=list(struct.unpack("224b",cpu.mem_read(pcm+1584,224)))
    return name,result

vectors=dict([
    run("constant",[64]*64),
    run("dpcm",[0,1,0x23]+[0]*30,wave_type=1,voice_type=0x28),
    run("half_rate",list(range(0,128,16)),voice_type=0),
    run("wrap_three",[64]*64,channels=3),
    run("reverb_negative",[0]*64,channels=0,reverb=128,initial=-1),
    run("reverb_positive",[0]*64,channels=0,reverb=128,initial=64),
])
assert vectors["constant"] == [63]*224
assert vectors["dpcm"][:4] == [0,0,4,13]
assert vectors["wrap_three"] == [-67]*224
assert vectors["reverb_negative"] == [0]*224
assert vectors["reverb_positive"] == [64]*224
# Nonloop end interpolation is a documented safety difference; compare prefix.
assert vectors["half_rate"][:14] == [0]+[i*8-1 for i in range(1,14)]
host = root/"build/m4a-host-vectors.csv"
assert host.exists(), "Run make -C port test first"
for line in host.read_text(encoding="ascii").splitlines():
    name,*values=line.split(',')
    count=14 if name == "half_rate" else 224
    assert list(map(int,values[:count])) == vectors[name][:count], name
output=root/"build/m4a-arm-vectors.json"
output.write_text(json.dumps(vectors,indent=2),encoding="utf-8")
print("PASS original ARM mixer: constant, DPCM, half pitch, wrap and reverb;",output)
