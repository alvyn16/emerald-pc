#include <stdio.h>
#include <stddef.h>
#include "global.h"
_Static_assert(sizeof(void *) == 4, "Run the layout probe under MINGW32");
#define FIELD(name) printf("\"" #name "\":%zu,", offsetof(struct SaveBlock2, frontier) + offsetof(struct BattleFrontier, name))
int main(void) {
 printf("{");
 FIELD(challengeStatus); FIELD(selectedPartyMons); FIELD(curChallengeBattleNum);
 FIELD(winStreakActiveFlags); FIELD(towerWinStreaks); FIELD(towerRecordWinStreaks);
 FIELD(domeWinStreaks); FIELD(domeTotalChampionships); FIELD(palaceWinStreaks);
 FIELD(arenaWinStreaks); FIELD(factoryWinStreaks); FIELD(factoryRentsCount);
 FIELD(pikeWinStreaks); FIELD(pyramidWinStreaks); FIELD(battlePoints);
 FIELD(rentalMons); FIELD(battlesCount);
 printf("\"SaveBlock2_size\":%zu,\"RentalMon_size\":%zu}\n", sizeof(struct SaveBlock2), sizeof(struct RentalMon));
 return 0;
}
