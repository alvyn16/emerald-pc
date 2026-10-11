#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "port_rtc.h"
static int64_t now = 1709164800; // 2024-02-29 00:00 UTC.
static int64_t Clock(void) { return now; }
int main(void)
{
    const char *path="build/rtc-test.rtc";
    FILE *f=fopen(path,"wb"); assert(f);
    fputs("EMERALD_PC_RTC 1\n0 1709164800 64\n",f); fclose(f);
    PortRtc_SetClock(Clock);
    assert(PortRtc_OpenFile(path)==0 && PortRtc_Ready());
    struct SiiRtcInfo date={0};
    assert(PortRtc_Get(&date));
    assert(date.year==0x24 && date.month==2 && date.day==0x29 && date.hour==0);
    now+=86400; assert(PortRtc_Get(&date));
    assert(date.month==3 && date.day==1);
    now-=2*86400; assert(PortRtc_Get(&date));
    assert(date.month==3 && date.day==1); // Rollback does not repeat a day.
    date.hour=0x12; date.minute=0x34; date.second=0x56;
    assert(PortRtc_SetTime(&date));
    assert(PortRtc_Get(&date) && date.hour==0x12 && date.minute==0x34);
    PortRtc_Close();
    assert(PortRtc_OpenFile(path)==0);
    now+=61; assert(PortRtc_Get(&date));
    assert(date.minute==0x35 && date.second==0x57);
    for (unsigned speed=1;speed<=4;++speed)
        for (unsigned frames=0;frames<10000;++frames)
        { struct SiiRtcInfo same; assert(PortRtc_Get(&same)); assert(same.second==date.second); }
    date.month=2; date.day=0x30; assert(!PortRtc_Set(&date));
    date.month=0xfa; assert(!PortRtc_Set(&date));
    assert(!PortRtc_Get(NULL));
    PortRtc_Close();
    f=fopen(path,"wb"); assert(f); fputs("invalid config",f); fclose(f);
    assert(PortRtc_OpenFile(path)==-1 && !PortRtc_Ready());
    PortRtc_Close();
    char contents[32]={0}; f=fopen(path,"rb"); assert(f);
    assert(fread(contents,1,sizeof(contents),f)==14); fclose(f);
    assert(!strcmp(contents,"invalid config"));
    assert(PortRtc_OpenFile("build/missing-rtc-parent/config")==-1);
    remove(path);
    return 0;
}
