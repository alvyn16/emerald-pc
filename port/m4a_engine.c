/* Host implementation of the m4a sequence format. Game data stays upstream. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "gba/m4a_internal.h"
#include "m4a_engine.h"

extern void *const gMPlayJumpTableTemplate[36];
extern const u8 gClockTable[];
extern u32 MidiKeyToFreq(struct WaveData *, u8, u8);

static int8_t sLeft[PCM_DMA_BUF_SIZE], sRight[PCM_DMA_BUF_SIZE];
static unsigned sMixSamples;
static unsigned sPositions[MAX_DIRECTSOUND_CHANNELS];
static unsigned sDecodedBlock[MAX_DIRECTSOUND_CHANNELS];
static s8 sDecoded[MAX_DIRECTSOUND_CHANNELS][64];
extern const s8 gDeltaEncodingTable[];

static int WaveSample(unsigned channel, const struct WaveData *wave, unsigned position)
{
    if (!wave->type) return wave->data[position];
    unsigned block = position / 64;
    if (block != sDecodedBlock[channel])
    {
        const u8 *encoded = (const u8 *)wave->data + block * 33;
        s8 sample = encoded[0];
        sDecoded[channel][0] = sample;
        for (unsigned i = 1; i < 64; ++i)
        {
            unsigned packed = encoded[1 + i / 2];
            unsigned nibble = (i & 1) ? packed & 15 : packed >> 4;
            sample = (s8)(sample + gDeltaEncodingTable[nibble]);
            sDecoded[channel][i] = sample;
        }
        sDecodedBlock[channel] = block;
    }
    return sDecoded[channel][position & 63];
}

static int AdvanceEnvelope(struct SoundChannel *c, unsigned index)
{
    unsigned volume = c->envelopeVolume;
    if (c->statusFlags & SOUND_CHANNEL_SF_START)
    {
        if ((c->statusFlags & SOUND_CHANNEL_SF_STOP) || c->wav == NULL || c->count >= c->wav->size)
        { c->statusFlags = 0; return 0; }
        sPositions[index] = c->type & 0x10 ? c->wav->size - 1 - c->count : c->count;
        sDecodedBlock[index] = UINT32_MAX;
        c->fw = 0;
        volume = 0;
        c->statusFlags = SOUND_CHANNEL_SF_ENV_ATTACK;
        if (c->wav->status & 0xc000) c->statusFlags |= SOUND_CHANNEL_SF_LOOP;
    }
    if (c->statusFlags & SOUND_CHANNEL_SF_IEC)
    {
        if (!c->pseudoEchoLength || --c->pseudoEchoLength == 0)
        { c->statusFlags = 0; return 0; }
    }
    else if (c->statusFlags & SOUND_CHANNEL_SF_STOP)
    {
        volume = volume * c->release >> 8;
        if (volume <= c->pseudoEchoVolume)
        {
            volume = c->pseudoEchoVolume;
            if (!volume) { c->statusFlags = 0; return 0; }
            c->statusFlags |= SOUND_CHANNEL_SF_IEC;
        }
    }
    else if ((c->statusFlags & SOUND_CHANNEL_SF_ENV) == SOUND_CHANNEL_SF_ENV_ATTACK)
    {
        volume += c->attack;
        if (volume >= 255)
        { volume = 255; c->statusFlags = (c->statusFlags & ~SOUND_CHANNEL_SF_ENV) | SOUND_CHANNEL_SF_ENV_DECAY; }
    }
    else if ((c->statusFlags & SOUND_CHANNEL_SF_ENV) == SOUND_CHANNEL_SF_ENV_DECAY)
    {
        volume = volume * c->decay >> 8;
        if (volume <= c->sustain)
        { volume = c->sustain; c->statusFlags = (c->statusFlags & ~SOUND_CHANNEL_SF_ENV) | SOUND_CHANNEL_SF_ENV_SUSTAIN; }
    }
    c->envelopeVolume = volume;
    return 1;
}

static int8_t ClipSample(int value)
{ return value < -128 ? -128 : value > 127 ? 127 : value; }

static void MixPcm(struct SoundInfo *sound)
{
    int left[PCM_DMA_BUF_SIZE] = {0}, right[PCM_DMA_BUF_SIZE] = {0};
    const unsigned period = sound->pcmDmaPeriod ? sound->pcmDmaPeriod : 1;
    const unsigned counter = sound->pcmDmaCounter <= period ? sound->pcmDmaCounter : 0;
    const unsigned offset = ((period + 1 - counter) % period) * sMixSamples;
    const unsigned nextOffset = (offset + sMixSamples) % (period * sMixSamples);
    if (sound->reverb)
        for (unsigned i = 0; i < sMixSamples; ++i)
            left[i] = right[i] = (sound->pcmBuffer[offset + i] + sound->pcmBuffer[offset + i + PCM_DMA_BUF_SIZE]
                    + sound->pcmBuffer[nextOffset + i] + sound->pcmBuffer[nextOffset + i + PCM_DMA_BUF_SIZE]) * sound->reverb / 512;
    for (unsigned channel = 0; channel < sound->maxChans && channel < MAX_DIRECTSOUND_CHANNELS; ++channel)
    {
        struct SoundChannel *c = &sound->chans[channel];
        if (!(c->statusFlags & SOUND_CHANNEL_SF_ON) || !AdvanceEnvelope(c, channel)) continue;
        const struct WaveData *wave = c->wav;
        const unsigned envelope = c->envelopeVolume * (sound->masterVolume + 1) >> 4;
        const unsigned lv = envelope * c->leftVolume >> 8;
        const unsigned rv = envelope * c->rightVolume >> 8;
        c->envelopeVolumeLeft = lv;
        c->envelopeVolumeRight = rv;
        const uint64_t step = c->type & TONEDATA_TYPE_FIX ? 0x800000u : (uint64_t)c->frequency * (unsigned)sound->divFreq;
        unsigned position = sPositions[channel];
        const int reverse = (c->type & 0x10) != 0;
        for (unsigned i = 0; i < sMixSamples; ++i)
        {
            unsigned next = reverse ? (position ? position - 1 : position) : position + 1;
            if (next >= wave->size) next = (c->statusFlags & SOUND_CHANNEL_SF_LOOP) && wave->loopStart < wave->size ? wave->loopStart : position;
            const int sample = WaveSample(channel, wave, position);
            const int interpolated = sample + (int)(((int64_t)(WaveSample(channel, wave, next) - sample) * c->fw) >> 23);
            left[i] += interpolated * (int)lv >> 8;
            right[i] += interpolated * (int)rv >> 8;
            uint64_t phase = c->fw + step;
            unsigned advance = phase >> 23;
            c->fw = phase & 0x7fffff;
            if (reverse)
            {
                if (advance > position) { c->statusFlags = 0; break; }
                position -= advance;
            }
            else
            {
                uint64_t advanced = (uint64_t)position + advance;
                if (advanced >= wave->size)
                {
                    if (!(c->statusFlags & SOUND_CHANNEL_SF_LOOP) || wave->loopStart >= wave->size)
                    { c->statusFlags = 0; break; }
                    advanced = wave->loopStart + (advanced - wave->loopStart) % (wave->size - wave->loopStart);
                }
                position = advanced;
            }
        }
        sPositions[channel] = position;
        c->count = reverse ? position + 1 : wave->size - position;
        if (!wave->type) c->currentPointer = (s8 *)wave->data + position;
    }
    for (unsigned i = 0; i < sMixSamples; ++i)
    {
        sLeft[i] = ClipSample(left[i]);
        sRight[i] = ClipSample(right[i]);
        sound->pcmBuffer[offset + i] = sLeft[i];
        sound->pcmBuffer[offset + i + PCM_DMA_BUF_SIZE] = sRight[i];
    }
}

u32 umul3232H32(u32 a, u32 b) { return (u32)(((uint64_t)a * b) >> 32); }
void SoundMainBTM(void) { } // The host jump table uses ClearHost64 instead.
static void ClearHost64(void *p) { memset(p, 0, 64); }

void MPlayJumpTableCopy(MPlayFunc *table)
{
    memcpy(table, gMPlayJumpTableTemplate, 36 * sizeof(*table));
    table[35] = (MPlayFunc)ClearHost64;
}

void RealClearChain(void *p)
{
    struct SoundChannel *channel = p;
    if (channel->track == NULL) return;
    struct SoundChannel *prev = channel->prevChannelPointer;
    struct SoundChannel *next = channel->nextChannelPointer;
    if (prev != NULL) prev->nextChannelPointer = next;
    else channel->track->chan = next;
    if (next != NULL) next->prevChannelPointer = prev;
    channel->track = NULL;
}

void TrackStop(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track)
{
    (void)player;
    for (struct SoundChannel *c = track->chan; c != NULL;)
    {
        struct SoundChannel *next = c->nextChannelPointer;
        if (c->type & TONEDATA_TYPE_CGB)
            SOUND_INFO_PTR->CgbOscOff(c->type & TONEDATA_TYPE_CGB);
        c->statusFlags = 0;
        RealClearChain(c);
        c = next;
    }
    track->chan = NULL;
}

void ply_fine(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track)
{
    (void)player;
    for (struct SoundChannel *c = track->chan; c != NULL;)
    {
        struct SoundChannel *next = c->nextChannelPointer;
        if (c->statusFlags & SOUND_CHANNEL_SF_ON) c->statusFlags |= SOUND_CHANNEL_SF_STOP;
        RealClearChain(c);
        c = next;
    }
    track->flags = 0;
}

static u8 *ReadAddress(const u8 *bytes)
{
    uint32_t address;
    memcpy(&address, bytes, 4);
    return (u8 *)(uintptr_t)address;
}

void ply_goto(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ (void)p; t->cmdPtr = ReadAddress(t->cmdPtr); }
void ply_patt(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{
    if (t->patternLevel >= 3) { ply_fine(p, t); return; }
    t->patternStack[t->patternLevel++] = t->cmdPtr + 4;
    ply_goto(p, t);
}
void ply_pend(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ (void)p; if (t->patternLevel) t->cmdPtr = t->patternStack[--t->patternLevel]; }
void ply_rept(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{
    unsigned times = *t->cmdPtr++;
    if (!times || ++t->repN < times) ply_goto(p, t);
    else { t->repN = 0; t->cmdPtr += 4; }
}
void ply_tempo(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ p->tempoD = *t->cmdPtr++ * 2; p->tempoI = p->tempoD * p->tempoU >> 8; }
void ply_voice(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ t->tone = p->tone[*t->cmdPtr++]; }

#define BYTE_COMMAND(name, field, offset, change) \
void name(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t) \
{ (void)p; t->field = *t->cmdPtr++ - (offset); t->flags |= (change); }
BYTE_COMMAND(ply_prio, priority, 0, 0)
BYTE_COMMAND(ply_keysh, keyShift, 0, MPT_FLG_PITCHG)
BYTE_COMMAND(ply_vol, vol, 0, MPT_FLG_VOLCHG)
BYTE_COMMAND(ply_pan, pan, 64, MPT_FLG_VOLCHG)
BYTE_COMMAND(ply_bend, bend, 64, MPT_FLG_PITCHG)
BYTE_COMMAND(ply_bendr, bendRange, 0, MPT_FLG_PITCHG)
BYTE_COMMAND(ply_lfodl, lfoDelay, 0, 0)
BYTE_COMMAND(ply_modt, modT, 0, MPT_FLG_VOLCHG | MPT_FLG_PITCHG)
BYTE_COMMAND(ply_tune, tune, 64, MPT_FLG_PITCHG)

void ply_lfos(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ (void)p; t->lfoSpeed = *t->cmdPtr++; if (!t->lfoSpeed) ClearModM(t); }
void ply_mod(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{ (void)p; t->mod = *t->cmdPtr++; if (!t->mod) ClearModM(t); }
void ply_port(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{
    (void)p;
    unsigned offset = *t->cmdPtr++;
    unsigned value = *t->cmdPtr++;
    if (offset < 0x40) *(volatile u8 *)(uintptr_t)(0x04000060 + offset) = value;
}
void ply_endtie(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{
    (void)p;
    if (*t->cmdPtr < 0x80) t->key = *t->cmdPtr++;
    for (struct SoundChannel *c = t->chan; c != NULL; c = c->nextChannelPointer)
        if ((c->statusFlags & SOUND_CHANNEL_SF_ON) && !(c->statusFlags & SOUND_CHANNEL_SF_STOP) && c->midiKey == t->key)
        { c->statusFlags |= SOUND_CHANNEL_SF_STOP; break; }
}

static unsigned ClampByte(unsigned n) { return n > 255 ? 255 : n; }
static void SetVolumes(struct SoundChannel *c, const struct MusicPlayerTrack *t)
{
    int pan = (s8)c->rhythmPan;
    c->rightVolume = ClampByte((128 + pan) * c->velocity * t->volMR >> 14);
    c->leftVolume = ClampByte((127 - pan) * c->velocity * t->volML >> 14);
}
static void SetPitch(struct SoundChannel *c, const struct MusicPlayerTrack *t)
{
    int key = c->key + (s8)t->keyM;
    if (key < 0) key = 0;
    if (key > 178) key = 178;
    if (c->type & TONEDATA_TYPE_CGB)
    {
        struct CgbChannel *cg = (struct CgbChannel *)c;
        cg->frequency = SOUND_INFO_PTR->MidiKeyToCgbFreq(c->type & TONEDATA_TYPE_CGB, key, t->pitM);
        cg->modify |= CGB_CHANNEL_MO_PIT;
    }
    else if (c->wav != NULL) c->frequency = MidiKeyToFreq(c->wav, key, t->pitM);
}

void ply_note(u32 command, struct MusicPlayerInfo *p, struct MusicPlayerTrack *t)
{
    struct SoundInfo *sound = SOUND_INFO_PTR;
    if (command > 48) return;
    t->gateTime = gClockTable[command];
    if (*t->cmdPtr < 0x80)
    {
        t->key = *t->cmdPtr++;
        if (*t->cmdPtr < 0x80)
        {
            t->velocity = *t->cmdPtr++;
            if (*t->cmdPtr < 0x80) t->gateTime += *t->cmdPtr++;
        }
    }
    const struct ToneData *tone = &t->tone;
    unsigned key = t->key;
    int rhythmPan = 0;
    if (tone->type & (TONEDATA_TYPE_SPL | TONEDATA_TYPE_RHY))
    {
        unsigned index = key;
        if (tone->type & TONEDATA_TYPE_SPL)
        {
            const u8 *keyMap;
            memcpy(&keyMap, &tone->attack, sizeof(keyMap));
            index = keyMap[key];
        }
        const struct ToneData *selected = &((const struct ToneData *)tone->wav)[index];
        if (tone->type & TONEDATA_TYPE_RHY)
        {
            key = selected->key;
            if (selected->pan_sweep & 0x80) rhythmPan = ((int)selected->pan_sweep - 0xc0) * 2;
        }
        tone = selected;
    }
    if (tone->type & (TONEDATA_TYPE_SPL | TONEDATA_TYPE_RHY)) return;
    const unsigned priority = ClampByte(p->priority + t->priority);
    unsigned cgb = tone->type & TONEDATA_TYPE_CGB;
    struct SoundChannel *channel = NULL;
    if (cgb)
    {
        if (cgb > 4 || sound->cgbChans == NULL) return;
        channel = (struct SoundChannel *)&sound->cgbChans[cgb - 1];
        if ((channel->statusFlags & SOUND_CHANNEL_SF_ON) && !(channel->statusFlags & SOUND_CHANNEL_SF_STOP) && channel->priority > priority) return;
    }
    else
    {
        for (unsigned i = 0; i < sound->maxChans && i < MAX_DIRECTSOUND_CHANNELS; ++i)
        {
            struct SoundChannel *candidate = &sound->chans[i];
            if (!(candidate->statusFlags & SOUND_CHANNEL_SF_ON)) { channel = candidate; break; }
            if (candidate->priority <= priority && (channel == NULL || candidate->priority <= channel->priority)) channel = candidate;
        }
        if (channel == NULL || tone->wav == NULL) return;
    }
    RealClearChain(channel);
    channel->prevChannelPointer = NULL;
    channel->nextChannelPointer = t->chan;
    if (t->chan != NULL) t->chan->prevChannelPointer = channel;
    t->chan = channel;
    channel->track = t;
    channel->type = tone->type;
    channel->attack = tone->attack;
    channel->decay = tone->decay;
    channel->sustain = tone->sustain;
    channel->release = tone->release;
    channel->gateTime = t->gateTime;
    channel->midiKey = t->key;
    channel->key = key;
    channel->velocity = t->velocity;
    channel->priority = priority;
    channel->rhythmPan = rhythmPan;
    channel->pseudoEchoVolume = t->pseudoEchoVolume;
    channel->pseudoEchoLength = t->pseudoEchoLength;
    channel->wav = tone->wav;
    channel->count = t->unk_3C;
    t->lfoDelayC = t->lfoDelay;
    if (t->lfoDelay) ClearModM(t);
    TrkVolPitSet(p, t);
    SetVolumes(channel, t);
    if (cgb)
    {
        struct CgbChannel *cg = (struct CgbChannel *)channel;
        cg->length = tone->length;
        cg->sweep = (tone->pan_sweep & 0x70) && !(tone->pan_sweep & 0x80) ? tone->pan_sweep : 8;
        cg->modify = CGB_CHANNEL_MO_VOL | CGB_CHANNEL_MO_PIT;
    }
    SetPitch(channel, t);
    channel->statusFlags = SOUND_CHANNEL_SF_START;
    t->flags &= 0xf0;
}

static void Modulate(struct MusicPlayerTrack *t)
{
    if (!t->lfoSpeed || !t->mod) return;
    if (t->lfoDelayC) { --t->lfoDelayC; return; }
    t->lfoSpeedC += t->lfoSpeed;
    int phase = t->lfoSpeedC;
    int triangle = phase < 64 ? phase : phase < 192 ? 128 - phase : phase - 256;
    s8 modulation = triangle * t->mod >> 6;
    if (modulation != t->modM)
    {
        t->modM = modulation;
        t->flags |= t->modT ? MPT_FLG_VOLCHG : MPT_FLG_PITCHG;
    }
}

void MPlayMain(struct MusicPlayerInfo *p)
{
    if (p == NULL || p->ident != ID_NUMBER) return;
    p->ident++;
    if (p->MPlayMainNext != NULL) p->MPlayMainNext(p->musicPlayerNext);
    if (p->status & MUSICPLAYER_STATUS_PAUSE) goto done;
    FadeOutBody(p);
    if (p->status & MUSICPLAYER_STATUS_PAUSE) goto done;
    p->tempoC += p->tempoI;
    while (p->tempoC >= 150)
    {
        p->tempoC -= 150;
        unsigned active = 0;
        for (unsigned i = 0; i < p->trackCount; ++i)
        {
            struct MusicPlayerTrack *t = &p->tracks[i];
            if (!(t->flags & MPT_FLG_EXIST)) continue;
            for (struct SoundChannel *c = t->chan; c != NULL;)
            {
                struct SoundChannel *next = c->nextChannelPointer;
                if (!(c->statusFlags & SOUND_CHANNEL_SF_ON)) RealClearChain(c);
                else if (c->gateTime && --c->gateTime == 0) c->statusFlags |= SOUND_CHANNEL_SF_STOP;
                c = next;
            }
            if (t->flags & MPT_FLG_START)
            {
                ClearHost64(t);
                t->flags = MPT_FLG_EXIST;
                t->bendRange = 2;
                t->volX = 64;
                t->lfoSpeed = 22;
                t->tone.type = 1;
            }
            unsigned budget = 1024;
            while (!t->wait && (t->flags & MPT_FLG_EXIST) && budget > 0)
            {
                --budget;
                unsigned command = *t->cmdPtr;
                if (command < 0x80) command = t->runningStatus;
                else { ++t->cmdPtr; if (command >= 0xbd) t->runningStatus = command; }
                if (command >= 0xcf) ply_note(command - 0xcf, p, t);
                else if (command >= 0xb1)
                {
                    p->cmd = command - 0xb1;
                    gMPlayJumpTable[p->cmd](p, t);
                }
                else if (command >= 0x80) t->wait = gClockTable[command - 0x80];
                else { ply_fine(p, t); break; }
            }
            if (!budget && !t->wait && (t->flags & MPT_FLG_EXIST))
            {
                fprintf(stderr, "m4a: sequence exceeded command budget; stopping track\n");
                ply_fine(p, t);
            }
            if (t->wait) --t->wait;
            Modulate(t);
            if (t->flags & MPT_FLG_EXIST) active |= 1u << i;
        }
        ++p->clock;
        p->status = active ? active : MUSICPLAYER_STATUS_PAUSE;
        if (!active) break;
    }
    for (unsigned i = 0; i < p->trackCount; ++i)
    {
        struct MusicPlayerTrack *t = &p->tracks[i];
        unsigned changes = t->flags & 15;
        if (!(t->flags & MPT_FLG_EXIST) || !changes) continue;
        TrkVolPitSet(p, t);
        for (struct SoundChannel *c = t->chan; c != NULL; c = c->nextChannelPointer)
        {
            if (changes & MPT_FLG_VOLCHG)
            {
                SetVolumes(c, t);
                if (c->type & TONEDATA_TYPE_CGB) ((struct CgbChannel *)c)->modify |= CGB_CHANNEL_MO_VOL;
            }
            if (changes & MPT_FLG_PITCHG) SetPitch(c, t);
        }
        t->flags &= 0xf0;
    }
done:
    p->ident = ID_NUMBER;
}

void m4aSoundVSync(void)
{
    struct SoundInfo *sound = SOUND_INFO_PTR;
    if (sound == NULL || (sound->ident != ID_NUMBER && sound->ident != ID_NUMBER + 1)) return;
    if (!sound->pcmDmaCounter || --sound->pcmDmaCounter == 0)
        sound->pcmDmaCounter = sound->pcmDmaPeriod;
}

void SoundMain(void)
{
    struct SoundInfo *sound = SOUND_INFO_PTR;
    if (sound == NULL || sound->ident != ID_NUMBER) return;
    sound->ident++;
    if (sound->MPlayMainHead != NULL) sound->MPlayMainHead(sound->musicPlayerHead);
    if (sound->CgbSound != NULL) sound->CgbSound();
    sMixSamples = sound->pcmSamplesPerVBlank > 0 && sound->pcmSamplesPerVBlank <= PCM_DMA_BUF_SIZE ? sound->pcmSamplesPerVBlank : 0;
    if (sMixSamples) MixPcm(sound);
    sound->ident = ID_NUMBER;
}

void PortM4a_GetLastMix(const int8_t **left, const int8_t **right, unsigned *samples)
{ *left = sLeft; *right = sRight; *samples = sMixSamples; }
