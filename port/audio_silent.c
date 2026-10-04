/* Silent host replacements for the GBA m4a engine and its ARM command handlers. */
#include "global.h"
#include "gba/m4a_internal.h"
#include "m4a.h"
#include "constants/songs.h"

struct SoundInfo gSoundInfo;
struct MusicPlayerInfo gMPlayInfo_BGM;
struct MusicPlayerInfo gMPlayInfo_SE1;
struct MusicPlayerInfo gMPlayInfo_SE2;
struct MusicPlayerInfo gMPlayInfo_SE3;
struct PokemonCrySong gPokemonCrySongs[MAX_POKEMON_CRIES];

void m4aSoundInit(void) {}
void m4aSoundMain(void) {}
void m4aSoundVSync(void) {}
void m4aSoundVSyncOn(void) {}
void m4aSoundVSyncOff(void) {}
// Preserve logical BGM state while the host deliberately produces no audio.
void m4aSongNumStart(u16 n) { if (n >= MUS_LITTLEROOT_TEST) gMPlayInfo_BGM.status = 1; }
void m4aSongNumStartOrChange(u16 n) { m4aSongNumStart(n); }
void m4aSongNumStop(u16 n) { if (n >= MUS_LITTLEROOT_TEST) gMPlayInfo_BGM.status = 0; }
void m4aMPlayAllStop(void) { gMPlayInfo_BGM.status = 0; }
void m4aMPlayContinue(struct MusicPlayerInfo *p) { p->status &= ~MUSICPLAYER_STATUS_PAUSE; }
void m4aMPlayFadeOut(struct MusicPlayerInfo *p, u16 speed) { (void)speed; p->status = 0; }
void m4aMPlayFadeOutTemporarily(struct MusicPlayerInfo *p, u16 speed) { (void)speed; p->status |= MUSICPLAYER_STATUS_PAUSE; }
void m4aMPlayFadeIn(struct MusicPlayerInfo *p, u16 speed) { (void)speed; p->status &= ~MUSICPLAYER_STATUS_PAUSE; }
void m4aMPlayImmInit(struct MusicPlayerInfo *p) { (void)p; }
void m4aMPlayStop(struct MusicPlayerInfo *p) { p->status = 0; }
void m4aMPlayTempoControl(struct MusicPlayerInfo *p, u16 tempo) { (void)p; (void)tempo; }
void m4aMPlayVolumeControl(struct MusicPlayerInfo *p, u16 tracks, u16 volume) { (void)p; (void)tracks; (void)volume; }
void m4aMPlayPitchControl(struct MusicPlayerInfo *p, u16 tracks, s16 pitch) { (void)p; (void)tracks; (void)pitch; }
void m4aMPlayPanpotControl(struct MusicPlayerInfo *p, u16 tracks, s8 pan) { (void)p; (void)tracks; (void)pan; }

void FadeOutBody(struct MusicPlayerInfo *p) { (void)p; }
void RealClearChain(void *p) { (void)p; }
void SampleFreqSet(u32 freq) { (void)freq; }
void SoundMainBTM(void) {}
void TrackStop(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t) { (void)p; (void)t; }
void TrkVolPitSet(struct MusicPlayerInfo *p, struct MusicPlayerTrack *t) { (void)p; (void)t; }

struct MusicPlayerInfo *SetPokemonCryTone(struct ToneData *tone) { (void)tone; return &gMPlayInfo_BGM; }
void SetPokemonCryVolume(u8 value) { (void)value; }
void SetPokemonCryPanpot(s8 value) { (void)value; }
void SetPokemonCryPitch(s16 value) { (void)value; }
void SetPokemonCryLength(u16 value) { (void)value; }
void SetPokemonCryRelease(u8 value) { (void)value; }
void SetPokemonCryProgress(u32 value) { (void)value; }
bool32 IsPokemonCryPlaying(struct MusicPlayerInfo *p) { (void)p; return FALSE; }
void SetPokemonCryChorus(s8 value) { (void)value; }
void SetPokemonCryStereo(u32 value) { (void)value; }
void SetPokemonCryPriority(u8 value) { (void)value; }

#define SILENT_COMMAND(name) \
    void name(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track) \
    { (void)player; (void)track; }

SILENT_COMMAND(ply_fine)
SILENT_COMMAND(ply_goto)
SILENT_COMMAND(ply_patt)
SILENT_COMMAND(ply_pend)
SILENT_COMMAND(ply_rept)
SILENT_COMMAND(ply_prio)
SILENT_COMMAND(ply_tempo)
SILENT_COMMAND(ply_keysh)
SILENT_COMMAND(ply_voice)
SILENT_COMMAND(ply_vol)
SILENT_COMMAND(ply_pan)
SILENT_COMMAND(ply_bend)
SILENT_COMMAND(ply_bendr)
SILENT_COMMAND(ply_lfos)
SILENT_COMMAND(ply_lfodl)
SILENT_COMMAND(ply_mod)
SILENT_COMMAND(ply_modt)
SILENT_COMMAND(ply_tune)
SILENT_COMMAND(ply_port)
SILENT_COMMAND(ply_endtie)
SILENT_COMMAND(ply_xxx)
SILENT_COMMAND(ply_xwave)
SILENT_COMMAND(ply_xtype)
SILENT_COMMAND(ply_xatta)
SILENT_COMMAND(ply_xdeca)
SILENT_COMMAND(ply_xsust)
SILENT_COMMAND(ply_xrele)
SILENT_COMMAND(ply_xiecv)
SILENT_COMMAND(ply_xiecl)
SILENT_COMMAND(ply_xleng)
SILENT_COMMAND(ply_xswee)
SILENT_COMMAND(ply_xwait)
SILENT_COMMAND(ply_xcmd_0D)
