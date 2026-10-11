#include <assert.h>
#include <string.h>
#include <windows.h>
#define SDL_MAIN_HANDLED
#include "gba/m4a_internal.h"
#include "port_audio.h"
#include "sdl_loader.h"
#undef main

struct PortSDL portSDL;
static struct SoundInfo sSound;
static int8_t sLeft[224], sRight[224];
static unsigned sSpeed = 1, sQueued, sLastFrames, sQueueCalls, sClears, sCloses, sOpens, sRenders, sPauses;
static int sOpenFailure, sQueueFailure, sPaused, sHealthy = 1;
static int16_t sFirstLeft, sFirstRight;
unsigned PortSpeedMenu_Multiplier(void) { return sSpeed; }
void PortPsg_Reset(void) { }
void PortPsg_Render(int16_t *stereo, unsigned frames, unsigned rate)
{ (void)stereo; (void)frames; (void)rate; sRenders++; }
void PortM4a_GetLastMix(const int8_t **left, const int8_t **right, unsigned *samples)
{ *left = sLeft; *right = sRight; *samples = 224; }
static int Open(unsigned rate) { assert(rate == 48000); sOpens++; sQueued = 0; return sOpenFailure ? -1 : 0; }
static int Queue(const int16_t *stereo, unsigned frames)
{
    sFirstLeft = stereo[0]; sFirstRight = stereo[1];
    sLastFrames = frames; sQueueCalls++; sQueued += frames;
    assert(sQueued <= 7200);
    return sQueueFailure ? -1 : 0;
}
static unsigned Queued(void) { return sQueued; }
static void Clear(void) { sClears++; sQueued = 0; }
static void Close(void) { sCloses++; }
static void Pause(int paused) { sPaused = paused; sPauses++; }
static int Healthy(void) { return sHealthy; }
int main(void)
{
    void *iwram = VirtualAlloc((void *)0x03000000, 32768, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(iwram == (void *)0x03000000);
    SOUND_INFO_PTR = &sSound;
    sSound.pcmFreq = 13379;
    memset(sLeft, 127, sizeof(sLeft));
    memset(sRight, -128, sizeof(sRight));
    const struct PortAudioBackend backend = {Open, Queue, Queued, Clear, Close, Pause, Healthy};
    PortAudio_SetBackend(&backend);
    sOpenFailure = 1;
    assert(PortAudio_Init() == -1);
    PortAudio_SubmitFrame();
    assert(sQueueCalls == 0 && sRenders == 1);
    for (unsigned i = 0; i < 118; ++i) PortAudio_SubmitFrame();
    assert(sOpens == 1);
    sOpenFailure = 0;
    PortAudio_SubmitFrame();
    assert(sOpens == 2 && sQueueCalls == 1);
    PortAudio_Shutdown();
    assert(sCloses == 1);
    sClears = sQueueCalls = sCloses = 0;

    sOpenFailure = 0;
    assert(PortAudio_Init() == 0);
    PortAudio_SubmitFrame();
    assert(sLastFrames >= 803 && sLastFrames <= 805);
    assert(sFirstLeft == 32512 && sFirstRight == -32768);
    sSpeed = 2;
    PortAudio_SubmitFrame();
    assert(sLastFrames >= 401 && sLastFrames <= 403);
    assert(sClears == 1);
    sQueued = 9600;
    PortAudio_SubmitFrame();
    assert(sClears == 2);
    sSpeed = 4;
    for (unsigned frame = 0; frame < 1000; ++frame) PortAudio_SubmitFrame();
    assert(sLastFrames >= 200 && sLastFrames <= 202);
    assert(sClears > 20);
    unsigned renders = sRenders, queues = sQueueCalls;
    PortAudio_SetPaused(1);
    assert(sPaused && sQueued == 0);
    PortAudio_SetPaused(1); // Idempotent.
    PortAudio_SubmitFrame();
    assert(sRenders == renders && sQueueCalls == queues && sPauses == 1);
    PortAudio_SetPaused(0);
    assert(!sPaused && sPauses == 2);
    PortAudio_SubmitFrame();
    sHealthy = 0;
    sOpenFailure = 1;
    PortAudio_SubmitFrame();
    assert(sCloses == 1);
    sHealthy = 1; sOpenFailure = 0;
    for (unsigned i = 0; i < 120; ++i) PortAudio_SubmitFrame();
    sCloses = 0;
    sQueueFailure = 1;
    PortAudio_SubmitFrame();
    unsigned calls = sQueueCalls;
    PortAudio_SubmitFrame();
    assert(sQueueCalls == calls && sCloses == 1);
    sQueueFailure = 0;
    for (unsigned i = 0; i < 119; ++i) PortAudio_SubmitFrame();
    assert(sQueueCalls > calls);
    for (unsigned speed = 1; speed <= 4; ++speed)
    {
        sSpeed = speed;
        unsigned frames = 0;
        for (unsigned i = 0; i < 1000; ++i)
        {
            sQueued = 0; // Device consuming previous block.
            PortAudio_SubmitFrame();
            frames += sLastFrames;
        }
        double expected = 224.0 * 1000 * 48000 / (13379 * speed);
        assert(frames >= expected - 1 && frames <= expected + 1);
    }
    PortAudio_SetPaused(1);
    PortAudio_Shutdown();
    assert(sCloses == 2);
    calls = sQueueCalls;
    PortAudio_SubmitFrame();
    assert(sQueueCalls == calls);
    PortAudio_Shutdown();
    assert(sCloses == 2);
    PortAudio_SetBackend(NULL);
    VirtualFree(iwram, 0, MEM_RELEASE);
    return 0;
}
