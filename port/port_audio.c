#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gba/m4a_internal.h"
#include "m4a_engine.h"
#include "port_audio.h"
#include "port_psg.h"
#include "sdl_loader.h"
#include "speed_menu.h"

#define OUTPUT_RATE 48000u
#define MAX_QUEUE_FRAMES (OUTPUT_RATE * 150 / 1000)
#define MAX_OUTPUT_FRAMES 16000u
static SDL_AudioDeviceID sDevice;
static int sOpened, sActive, sPaused;
static unsigned sRetryFrames;
static unsigned sLastSpeed;
static double sPosition;
static int16_t sSource[PCM_DMA_BUF_SIZE * 2];
static int16_t sOutput[MAX_OUTPUT_FRAMES * 2];
#ifdef PORT_DIAGNOSTIC
static FILE *sDump;
static uint32_t sDumpBytes;
static void WriteHeader(void)
{
    uint8_t header[44] = {0};
    memcpy(header, "RIFF", 4); memcpy(header + 8, "WAVEfmt ", 8);
    memcpy(header + 36, "data", 4);
    const uint32_t values[] = {36 + sDumpBytes, 16, OUTPUT_RATE, OUTPUT_RATE * 4, sDumpBytes};
    const unsigned offsets[] = {4, 16, 24, 28, 40};
    for (unsigned i = 0; i < 5; ++i)
        for (unsigned j = 0; j < 4; ++j) header[offsets[i] + j] = values[i] >> (j * 8);
    header[20] = 1; header[22] = 2; header[32] = 4; header[34] = 16;
    fseek(sDump, 0, SEEK_SET);
    fwrite(header, 1, sizeof(header), sDump);
}
#endif

static int OpenDevice(unsigned rate)
{
    if (portSDL.InitSubSystem(SDL_INIT_AUDIO) != 0) return -1;
    SDL_AudioSpec desired = {0}, obtained;
    desired.freq = rate;
    desired.format = AUDIO_S16SYS;
    desired.channels = 2;
    desired.samples = 1024;
    sDevice = portSDL.OpenAudioDevice(NULL, 0, &desired, &obtained, 0);
    if (!sDevice) return -1;
    portSDL.PauseAudioDevice(sDevice, 0);
    return 0;
}
static int QueueDevice(const int16_t *data, unsigned frames)
{ return portSDL.QueueAudio(sDevice, data, frames * 4); }
static unsigned QueuedDevice(void) { return portSDL.GetQueuedAudioSize(sDevice) / 4; }
static void ClearDevice(void) { portSDL.ClearQueuedAudio(sDevice); }
static void CloseDevice(void) { portSDL.CloseAudioDevice(sDevice); sDevice = 0; }
static void PauseDevice(int paused) { portSDL.PauseAudioDevice(sDevice, paused); }
static int HealthyDevice(void) { return portSDL.GetAudioDeviceStatus(sDevice) != SDL_AUDIO_STOPPED; }
static const struct PortAudioBackend sRealBackend = {OpenDevice, QueueDevice, QueuedDevice, ClearDevice, CloseDevice, PauseDevice, HealthyDevice};
static const struct PortAudioBackend *sBackend = &sRealBackend;

void PortAudio_SetBackend(const struct PortAudioBackend *backend)
{ sBackend = backend != NULL ? backend : &sRealBackend; }

int PortAudio_Init(void)
{
    sActive = 1;
    sPaused = 0;
    sRetryFrames = 120;
    sPosition = 0;
    sLastSpeed = 0;
    PortPsg_Reset();
#ifdef PORT_DIAGNOSTIC
    sDumpBytes = 0;
    const char *path = getenv("EMERALD_PC_AUDIO_DUMP");
    if (path != NULL && *path)
    {
        sDump = fopen(path, "wb");
        if (sDump != NULL) WriteHeader();
        else fprintf(stderr, "PC audio: cannot create WAV %s\n", path);
    }
#endif
    sOpened = sBackend->open(OUTPUT_RATE) == 0;
    if (!sOpened) fprintf(stderr, "PC audio: no device; continuing in silence\n");
    return sOpened ? 0 : -1;
}

void PortAudio_SubmitFrame(void)
{
    if (!sActive || sPaused) return;
    if (sOpened && !sBackend->healthy())
    {
        sBackend->close();
        sOpened = 0;
        sRetryFrames = 0;
    }
    if (!sOpened && (sRetryFrames == 0 || --sRetryFrames == 0))
    {
        sOpened = sBackend->open(OUTPUT_RATE) == 0;
        sRetryFrames = 120; // Game frames; no blocking loop or repeated log spam.
        if (sOpened) { sPosition = 0; fprintf(stderr, "PC audio: device reconnected\n"); }
    }
    const int8_t *left, *right;
    unsigned samples;
    PortM4a_GetLastMix(&left, &right, &samples);
    const struct SoundInfo *sound = SOUND_INFO_PTR;
    if (samples == 0 || samples > PCM_DMA_BUF_SIZE || sound == NULL || sound->pcmFreq <= 0) return;
    unsigned speed = PortSpeedMenu_Multiplier();
    if (speed < 1 || speed > 4) speed = 1;
    if (sLastSpeed != speed)
    {
        if (sOpened && sLastSpeed) sBackend->clear();
        sPosition = 0;
        sLastSpeed = speed;
    }
    for (unsigned i = 0; i < samples; ++i)
    { sSource[i * 2] = (int)left[i] * 256; sSource[i * 2 + 1] = (int)right[i] * 256; }
    PortPsg_Render(sSource, samples, sound->pcmFreq);
    const double step = (double)sound->pcmFreq * speed / OUTPUT_RATE;
    unsigned outputFrames = 0;
    while (sPosition < samples && outputFrames < MAX_OUTPUT_FRAMES)
    {
        unsigned first = (unsigned)sPosition;
        unsigned second = first + 1 < samples ? first + 1 : first;
        double fraction = sPosition - first;
        for (unsigned channel = 0; channel < 2; ++channel)
        {
            int a = sSource[first * 2 + channel], b = sSource[second * 2 + channel];
            sOutput[outputFrames * 2 + channel] = a + (b - a) * fraction;
        }
        sPosition += step;
        outputFrames++;
    }
    sPosition -= samples;
    if (sOpened)
    {
        if (sBackend->queued() + outputFrames > MAX_QUEUE_FRAMES) sBackend->clear();
        if (sBackend->queue(sOutput, outputFrames) != 0)
        {
            fprintf(stderr, "PC audio: queue failed; continuing in silence\n");
            sBackend->close();
            sOpened = 0;
            sRetryFrames = 120;
        }
    }
#ifdef PORT_DIAGNOSTIC
    if (sDump != NULL && sDumpBytes <= UINT32_MAX - 44 - outputFrames * 4)
        sDumpBytes += fwrite(sOutput, 4, outputFrames, sDump) * 4;
#endif
}

void PortAudio_SetPaused(int paused)
{
    paused = !!paused;
    if (!sActive || paused == sPaused) return;
    if (sOpened)
    {
        sBackend->pause(paused);
        if (paused) sBackend->clear();
    }
    sPosition = 0;
    sPaused = paused;
}

void PortAudio_Shutdown(void)
{
    sActive = 0;
    if (sOpened) { sBackend->close(); sOpened = 0; }
#ifdef PORT_DIAGNOSTIC
    if (sDump != NULL) { WriteHeader(); fclose(sDump); sDump = NULL; }
#endif
}
