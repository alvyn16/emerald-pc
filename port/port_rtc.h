#ifndef EMERALD_PC_RTC_H
#define EMERALD_PC_RTC_H
#include <stdint.h>
#include "siirtc.h"
int PortRtc_Open(void);
int PortRtc_OpenFile(const char *path);
void PortRtc_Close(void);
void PortRtc_SetClock(int64_t (*clock)(void));
int PortRtc_Ready(void);
int PortRtc_Get(struct SiiRtcInfo *info);
int PortRtc_Set(const struct SiiRtcInfo *info);
int PortRtc_GetStatus(struct SiiRtcInfo *info);
int PortRtc_SetStatus(const struct SiiRtcInfo *info);
int PortRtc_SetTime(const struct SiiRtcInfo *info);
int PortRtc_Reset(void);
#ifdef PORT_DIAGNOSTIC
void PortRtc_DiagnosticSetTime(int64_t seconds);
#endif
#endif
