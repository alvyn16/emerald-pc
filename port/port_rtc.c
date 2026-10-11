#include <stdio.h>
#include <string.h>
#include <time.h>
#include <io.h>
#include <windows.h>
#include "port_rtc.h"

#define RTC_FIRST 946684800LL
#define RTC_END 4102444800LL
#define RTC_MAX_OFFSET 3155760000LL

/* Check before adding offsets: injected/changed clocks may be any int64. */
static int ClockTime(int64_t clock, int64_t offset, int64_t *result)
{
    if (clock < RTC_FIRST - offset || clock >= RTC_END - offset) return 0;
    *result = clock + offset;
    return 1;
}

struct RtcState { int64_t offset, last; unsigned status; };
static struct RtcState sState;
static char sPath[MAX_PATH];
static int sReady;
static int64_t SystemClock(void)
{
    FILETIME time;
    GetSystemTimeAsFileTime(&time);
    uint64_t ticks = ((uint64_t)time.dwHighDateTime << 32) | time.dwLowDateTime;
    return (int64_t)(ticks / 10000000) - 11644473600LL;
}
static int64_t (*sClock)(void) = SystemClock;
void PortRtc_SetClock(int64_t (*clock)(void)) { sClock = clock ? clock : SystemClock; }
#ifdef PORT_DIAGNOSTIC
static int64_t sDiagnosticTime;
static int64_t DiagnosticClock(void) { return sDiagnosticTime; }
void PortRtc_DiagnosticSetTime(int64_t seconds)
{ sDiagnosticTime = seconds; sClock = DiagnosticClock; }
#endif

static int Persist(void)
{
    char temporary[MAX_PATH];
    if (snprintf(temporary, sizeof(temporary), "%s.tmp", sPath) >= (int)sizeof(temporary)) return 0;
    FILE *file = fopen(temporary, "wb");
    if (!file) return 0;
    int ok = fprintf(file, "EMERALD_PC_RTC 1\n%lld %lld %u\n",
                     (long long)sState.offset, (long long)sState.last, sState.status) > 0;
    if (fflush(file) || _commit(_fileno(file))) ok = 0;
    if (fclose(file)) ok = 0;
    if (!ok || !MoveFileExA(temporary, sPath, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
    { DeleteFileA(temporary); return 0; }
    return 1;
}

int PortRtc_OpenFile(const char *path)
{
    sReady = 0;
    if (!path || strlen(path) >= sizeof(sPath) - 4) return -1;
    strcpy(sPath, path);
    FILE *file = fopen(path, "rb");
    if (file)
    {
        long long offset, last;
        unsigned version, status;
        char trailing;
        int fields = fscanf(file, "EMERALD_PC_RTC %u\n%lld %lld %u %c", &version, &offset, &last, &status, &trailing);
        fclose(file);
        if (fields != 4 || version != 1 || offset < -3155760000LL || offset > 3155760000LL
            || last < 946684800LL || last >= 4102444800LL || (status & ~0x47u))
        { fprintf(stderr, "RTC: invalid configuration; file preserved\n"); return -1; }
        sState = (struct RtcState){offset, last, status | 0x40};
    }
    else
    {
        if (GetFileAttributesA(path) != INVALID_FILE_ATTRIBUTES) return -1;
        TIME_ZONE_INFORMATION zone;
        DWORD kind = GetTimeZoneInformation(&zone);
        long bias = kind == TIME_ZONE_ID_INVALID ? 0 : zone.Bias
                    + (kind == TIME_ZONE_ID_DAYLIGHT ? zone.DaylightBias : zone.StandardBias);
        sState = (struct RtcState){-(int64_t)bias * 60, 0, 0x40};
        if (!ClockTime(sClock(), sState.offset, &sState.last)) return -1;
        if (!Persist()) return -1;
    }
    sReady = 1;
    return 0;
}

int PortRtc_Open(void)
{
    char path[MAX_PATH];
    DWORD length = GetModuleFileNameA(NULL, path, sizeof(path));
    if (!length || length >= sizeof(path)) return -1;
    for (unsigned i = 0; i < 2; ++i)
    {
        char *slash = strrchr(path, '\\');
        if (!slash) return -1;
        *slash = 0;
    }
#ifdef PORT_DIAGNOSTIC
    const char *suffix = "\\saves\\emerald-pc-diagnostic.rtc";
#else
    const char *suffix = "\\saves\\emerald-pc.rtc";
#endif
    if (strlen(path) + strlen(suffix) >= sizeof(path)) return -1;
    strcat(path, suffix);
    return PortRtc_OpenFile(path);
}

static int64_t GuestTime(void)
{
    int64_t clock = sClock(), now;
    if (clock < RTC_FIRST - sState.offset) return sState.last;
    if (!ClockTime(clock, sState.offset, &now)) return -1;
    if (now > sState.last) sState.last = now;
    return sState.last; // OS clock rollback freezes time until it catches up.
}
void PortRtc_Close(void)
{
    if (sReady) { GuestTime(); if (!Persist()) fprintf(stderr, "RTC: configuration flush failed\n"); }
    sReady = 0;
}
int PortRtc_Ready(void) { struct SiiRtcInfo date; return PortRtc_Get(&date); }
static unsigned Bcd(unsigned number) { return (number / 10) * 16 + number % 10; }
static int Binary(unsigned bcd)
{ return bcd > 0x99 || (bcd & 15) > 9 ? -1 : (int)((bcd >> 4) * 10 + (bcd & 15)); }
int PortRtc_Get(struct SiiRtcInfo *info)
{
    if (!info) return 0;
    *info = (struct SiiRtcInfo){.month=1, .day=1, .status=0xc0};
    if (!sReady) return 0;
    __time64_t now = GuestTime();
    int valid = now >= RTC_FIRST;
    if (!valid) now = sState.last; // rtc.c ignores transport errors: supply safe last date.
    struct tm date;
    if (_gmtime64_s(&date, &now) || date.tm_year < 100 || date.tm_year > 199) return 0;
    info->year = Bcd(date.tm_year - 100); info->month = Bcd(date.tm_mon + 1);
    info->day = Bcd(date.tm_mday); info->dayOfWeek = date.tm_wday;
    info->hour = Bcd(date.tm_hour); info->minute = Bcd(date.tm_min); info->second = Bcd(date.tm_sec);
    info->status = sState.status | (valid ? 0 : 0x80);
    return valid;
}
int PortRtc_Set(const struct SiiRtcInfo *info)
{
    if (!sReady || !info) return 0;
    struct tm date = {0};
    int fields[] = {Binary(info->year), Binary(info->month), Binary(info->day),
                    Binary(info->hour), Binary(info->minute), Binary(info->second)};
    for (unsigned i = 0; i < 6; ++i) if (fields[i] < 0) return 0;
    date.tm_year = fields[0] + 100; date.tm_mon = fields[1] - 1; date.tm_mday = fields[2];
    date.tm_hour = fields[3]; date.tm_min = fields[4]; date.tm_sec = fields[5];
    struct tm requested = date;
    __time64_t seconds = _mkgmtime64(&date);
    if (seconds < 946684800LL || date.tm_year != requested.tm_year || date.tm_mon != requested.tm_mon
        || date.tm_mday != requested.tm_mday || date.tm_hour != requested.tm_hour
        || date.tm_min != requested.tm_min || date.tm_sec != requested.tm_sec) return 0;
    int64_t clock = sClock();
    if (clock < seconds - RTC_MAX_OFFSET || clock > seconds + RTC_MAX_OFFSET) return 0;
    struct RtcState previous = sState;
    sState.offset = seconds - clock; sState.last = seconds;
    if (!Persist()) { sState = previous; return 0; }
    return 1;
}
int PortRtc_GetStatus(struct SiiRtcInfo *info)
{
    if (!info) return 0;
    info->status = sReady ? sState.status | (GuestTime() < 0 ? 0x80 : 0) : 0xc0;
    return sReady;
}
int PortRtc_SetStatus(const struct SiiRtcInfo *info)
{
    if (!sReady || !info) return 0;
    unsigned old = sState.status;
    sState.status = (info->status & 7) | 0x40;
    if (!Persist()) { sState.status = old; return 0; }
    return 1;
}
int PortRtc_SetTime(const struct SiiRtcInfo *info)
{
    struct SiiRtcInfo date;
    if (!info || !PortRtc_Get(&date)) return 0;
    date.hour = info->hour; date.minute = info->minute; date.second = info->second;
    return PortRtc_Set(&date);
}
int PortRtc_Reset(void)
{
    struct SiiRtcInfo status = {.status = 0x40};
    return PortRtc_SetStatus(&status);
}
