#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "gba/m4a_internal.h"
#include "m4a.h"
#include "m4a_engine.h"
#include "port_psg.h"

static struct MusicPlayerTrack sTracks[4][2];
const struct MusicPlayer gMPlayTable[] = {
    {&gMPlayInfo_BGM, sTracks[0], 2, 0},
    {&gMPlayInfo_SE1, sTracks[1], 2, 0},
    {&gMPlayInfo_SE2, sTracks[2], 2, 0},
    {&gMPlayInfo_SE3, sTracks[3], 2, 0},
};
const struct Song gSongTable[] = {{0}};
const struct ToneData voicegroup_dummy = {0};
void PortHost_RunFrame(void) { }
int PortReset_Restart(void) { return 0; }
void Port_ExitCleanly(void) { }
// BIOS waits are not exercised by this audio-only fixture.
void (*gIntrTable[14])(void);

static void DumpVector(const char *name, const int8_t *samples, unsigned count)
{
    static unsigned records;
    FILE *file = fopen("build/m4a-host-vectors.csv", records++ ? "a" : "w");
    assert(file != NULL);
    fprintf(file, "%s", name);
    for (unsigned i = 0; i < count; ++i) fprintf(file, ",%d", samples[i]);
    fputc('\n', file); fclose(file);
}

int main(void)
{
    void *io = VirtualAlloc((void *)0x04000000, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    void *iwram = VirtualAlloc((void *)0x03000000, 32768, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(io == (void *)0x04000000 && iwram == (void *)0x03000000);
    struct { u16 type, status; u32 freq, loopStart, size; s8 data[64]; } wave = {0};
    wave.freq = 13379 * 1024;
    wave.status = 0xc000;
    wave.size = 64;
    memset(wave.data, 64, sizeof(wave.data));
    struct ToneData tone = {.type = TONEDATA_TYPE_FIX, .wav = (struct WaveData *)&wave,
                           .attack = 255, .decay = 255, .sustain = 255, .release = 128};
    u8 sequence[] = {0xbb, 75, 0xbd, 0, 0xbe, 100, 0xe7, 60, 100, 0x98, 0xb1};
    struct SongHeader song = {.trackCount = 1, .tone = &tone, .part = {sequence}};
    m4aSoundInit();
    MPlayStart(&gMPlayInfo_BGM, &song);
    m4aSoundMain();
    assert(gMPlayInfo_BGM.status & 1);
    assert(gMPlayInfo_BGM.tempoI == 150);
    assert(gSoundInfo.chans[0].statusFlags & SOUND_CHANNEL_SF_ON);
    assert(gSoundInfo.chans[0].key == 60);
    for (int frame = 2; frame <= 24; ++frame) m4aSoundMain();
    assert(gMPlayInfo_BGM.status & 1);
    m4aSoundMain();
    assert(!(gMPlayInfo_BGM.status & MUSICPLAYER_STATUS_TRACK));

    memset(gSoundInfo.chans, 0, sizeof(gSoundInfo.chans));
    gSoundInfo.maxChans = 1;
    gSoundInfo.masterVolume = 15;
    gSoundInfo.reverb = 0;
    struct SoundChannel *channel = &gSoundInfo.chans[0];
    *channel = (struct SoundChannel){.statusFlags = SOUND_CHANNEL_SF_START,
        .type = TONEDATA_TYPE_FIX, .wav = (struct WaveData *)&wave,
        .leftVolume = 255, .rightVolume = 255, .attack = 255,
        .decay = 255, .sustain = 255, .release = 128};
    m4aSoundMain();
    const int8_t *left, *right;
    unsigned samples;
    PortM4a_GetLastMix(&left, &right, &samples);
    assert(samples == 224);
    for (unsigned i = 0; i < samples; ++i) assert(left[i] == 63 && right[i] == 63);
    DumpVector("constant",left,samples);
    for (int i = 0; i < 10; ++i) m4aSoundMain();
    assert(channel->statusFlags & SOUND_CHANNEL_SF_ON); // Loop survives >1000 samples.
    channel->leftVolume = 0;
    m4aSoundMain();
    assert(left[0] == 0 && right[0] == 63);
    channel->statusFlags |= SOUND_CHANNEL_SF_STOP;
    for (int i = 0; i < 10; ++i) m4aSoundMain();
    assert(channel->statusFlags == 0);
    for (unsigned i = 0; i < samples; ++i) assert(left[i] == 0 && right[i] == 0);

    channel->count = 0;
    channel->leftVolume = 255;
    wave.status = 0;
    channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    assert(channel->statusFlags == 0);
    assert(left[0] == 63 && left[100] == 0);

    // Compressed PCM: each 64-sample block has a seed and squared deltas.
    wave.type = 1;
    wave.status = 0xc000;
    memset(wave.data, 0, sizeof(wave.data));
    wave.data[0] = 64;
    channel->count = 0;
    channel->type = TONEDATA_TYPE_FIX | 0x20;
    channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    for (unsigned i = 0; i < samples; ++i) assert(left[i] == 63 && right[i] == 63);
    // Nonconstant DPCM follows seed/low nibble, then high/low of next bytes.
    wave.data[0] = 0;
    wave.data[1] = 1;
    wave.data[2] = 0x23;
    channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    assert(left[0] == 0 && left[1] == 0 && left[2] == 4 && left[3] == 13);
    DumpVector("dpcm",left,samples);
    // Decode wraps signed samples (seed 120 + delta 49 => -87).
    wave.data[0] = 120; wave.data[1] = 7;
    channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    assert(left[0] == 119 && left[1] == -87);

    // Exact half-rate interpolation and reverse playback of a private ramp.
    wave.type = 0; wave.status = 0; wave.size = 8;
    for (unsigned i = 0; i < 8; ++i) wave.data[i] = i * 16;
    channel->type = 0; channel->count = 0; channel->frequency = 1;
    gSoundInfo.divFreq = 0x400000;
    channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    for (unsigned i = 0; i < 15; ++i) assert(left[i] == (i ? (int)i * 8 - 1 : 0));
    assert(left[16] == 0 && channel->statusFlags == 0);
    DumpVector("half_rate",left,samples);
    channel->type = TONEDATA_TYPE_FIX | 0x10; channel->count = 0;
    channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain();
    for (unsigned i = 0; i < 8; ++i) assert(left[i] == (i == 7 ? 0 : (7 - (int)i) * 16 - 1));
    assert(left[8] == 0);

    wave.size = 64; wave.status = 0xc000; memset(wave.data, 64, 64);
    channel->type = TONEDATA_TYPE_FIX; channel->count = 0;
    channel->attack = 64; channel->decay = 128; channel->sustain = 32;
    channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    const unsigned envelopes[] = {64,128,192,255,127,63,32,32};
    for (unsigned i = 0; i < sizeof(envelopes)/sizeof(*envelopes); ++i)
    { m4aSoundMain(); assert(channel->envelopeVolume == envelopes[i]); }
    channel->statusFlags |= SOUND_CHANNEL_SF_STOP;
    channel->release = 128;
    m4aSoundMain(); assert(channel->envelopeVolume == 16);
    for (unsigned i = 0; i < 5; ++i) m4aSoundMain();
    assert(channel->statusFlags == 0);
    channel->attack = 255; channel->sustain = 0; channel->decay = 0;
    channel->count = 0; channel->count = 0; channel->statusFlags = SOUND_CHANNEL_SF_START;
    m4aSoundMain(); m4aSoundMain(); assert(channel->statusFlags == 0);

    // Counter zero selects buffer zero, including negative reverb rounding.
    gSoundInfo.maxChans = 0; gSoundInfo.reverb = 128;
    gSoundInfo.pcmDmaPeriod = 7; gSoundInfo.pcmDmaCounter = 0;
    memset(gSoundInfo.pcmBuffer, -1, sizeof(gSoundInfo.pcmBuffer));
    m4aSoundMain(); assert(left[0] == 0);
    DumpVector("reverb_negative",left,samples);
    memset(gSoundInfo.pcmBuffer, 64, sizeof(gSoundInfo.pcmBuffer));
    m4aSoundMain(); assert(left[0] == 64);
    DumpVector("reverb_positive",left,samples);
    gSoundInfo.pcmDmaPeriod = 255; // Malformed period must not escape buffers.
    m4aSoundMain();
    // Three full-volume voices wrap signed PCM exactly like byte additions.
    gSoundInfo.reverb = 0; gSoundInfo.maxChans = 3;
    for (unsigned i = 0; i < 3; ++i)
        gSoundInfo.chans[i] = (struct SoundChannel){.statusFlags=SOUND_CHANNEL_SF_START,
            .type=TONEDATA_TYPE_FIX,.wav=(struct WaveData *)&wave,.attack=255,
            .decay=255,.sustain=255,.leftVolume=255,.rightVolume=0};
    m4aSoundMain(); assert(left[0] == -67 && right[0] == 0);
    DumpVector("wrap_three",left,samples);
    REG_SOUNDCNT_X = 0; PortM4a_GetLastMix(&left,&right,&samples);
    assert(left[0] == 0 && right[0] == 0); REG_SOUNDCNT_X = 0x80;

    // Pattern stack, repeat count and tempo use actual sequence handlers.
    extern void ply_patt(struct MusicPlayerInfo *, struct MusicPlayerTrack *);
    extern void ply_pend(struct MusicPlayerInfo *, struct MusicPlayerTrack *);
    extern void ply_rept(struct MusicPlayerInfo *, struct MusicPlayerTrack *);
    extern void ply_tempo(struct MusicPlayerInfo *, struct MusicPlayerTrack *);
    struct MusicPlayerTrack track = {.flags=MPT_FLG_EXIST};
    struct MusicPlayerInfo player = {.tempoU=256};
    u8 pattern[8] = {0}; u8 address[4]; uintptr_t target = (uintptr_t)pattern;
    memcpy(address, &target, 4); track.cmdPtr = address;
    ply_patt(&player,&track); assert(track.cmdPtr == pattern && track.patternLevel == 1);
    ply_pend(&player,&track); assert(track.cmdPtr == address+4 && !track.patternLevel);
    u8 repeat[5] = {2}; memcpy(repeat+1,&target,4); track.cmdPtr=repeat;
    ply_rept(&player,&track); assert(track.cmdPtr==pattern && track.repN==1);
    track.cmdPtr=repeat; ply_rept(&player,&track); assert(track.cmdPtr==repeat+5 && !track.repN);
    u8 tempo = 60; track.cmdPtr=&tempo; ply_tempo(&player,&track); assert(player.tempoI==120);
    for (unsigned i=0;i<4;++i) { track.cmdPtr=address; ply_patt(&player,&track); }
    assert(track.flags == 0 && track.patternLevel == 3);
    puts("PCM vectors: DPCM, half-rate, reverse, ADSR, reverb, wrap, patterns and bounds OK");
    // Run the original CgbSound writer, including its 0x40/load/0x80 wave sequence.
    m4aSoundInit();
    u32 wavePattern[4] = {0xffffffff,0xffffffff,0,0};
    gCgbChans[2] = (struct CgbChannel){.statusFlags=SOUND_CHANNEL_SF_START,
        .type=3,.leftVolume=120,.rightVolume=120,.panMask=0x44,.attack=0,.decay=0,.sustain=15,
        .frequency=1536,.wavePointer=wavePattern};
    CgbSound();
    assert((REG_NR52 & 4) && !(REG_NR34 & 0x80));
    int16_t psg[32*2] = {0};
    PortPsg_Render(psg,32,4096);
    for (unsigned i=0;i<32;++i)
        assert(psg[i*2] == (i<16 ? 3840 : -3840));
    CgbOscOff(3); assert(!(REG_NR52 & 4));
    VirtualFree(iwram, 0, MEM_RELEASE);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
