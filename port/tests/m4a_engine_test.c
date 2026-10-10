#include <assert.h>
#include <string.h>
#include <windows.h>
#include "gba/m4a_internal.h"
#include "m4a.h"
#include "m4a_engine.h"

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
    VirtualFree(iwram, 0, MEM_RELEASE);
    VirtualFree(io, 0, MEM_RELEASE);
    return 0;
}
