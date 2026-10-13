"""Controlled low-HP fixture must use and consume a real bag medicine."""
from campaign_battle_menu_smoke import scenario


def main():
    # Setup is isolated from campaign; treatment itself uses action/bag/party UI.
    log=scenario('healing','''
set *(unsigned short *)((char *)&gPlayerParty+86) = 1
call (int)AddBagItem(22,1)
call (void)CreateMon((void *)&gEnemyParty,286,4,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
''','''
assert d.value('(int)CountTotalItemQuantityInBag(22)') == 0
assert d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)') > 1
''','d.HEAL_ITEMS=(22,)\n')
    print('PASS bag medicine selected, applied and consumed:',log)


if __name__ == '__main__':
    main()
