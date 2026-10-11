#ifndef EMERALD_PC_PORT_AUDIO_H
#define EMERALD_PC_PORT_AUDIO_H
#include <stdint.h>
struct PortAudioBackend
{
    int (*open)(unsigned rate);
    int (*queue)(const int16_t *stereo, unsigned frames);
    unsigned (*queued)(void);
    void (*clear)(void);
    void (*close)(void);
    void (*pause)(int paused);
    int (*healthy)(void);
};
void PortAudio_SetBackend(const struct PortAudioBackend *backend);
int PortAudio_Init(void);
void PortAudio_SubmitFrame(void);
void PortAudio_Shutdown(void);
void PortAudio_SetPaused(int paused);
#endif
