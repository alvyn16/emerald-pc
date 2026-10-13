"""Verify real battle-menu switching grants shared experience to the lead."""
from campaign_battle_menu_smoke import scenario


def main():
    # Explicit controlled party/encounter, independent of campaign progression.
    log=scenario('switch-training','''
call (void)CreateMon((void *)&gPlayerParty,309,12,32,0,0,0,0)
call (void)CreateMon((void *)((char *)&gPlayerParty+100),284,20,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 2
call (void)CreateMon((void *)&gEnemyParty,354,13,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
set $lead_exp = (int)GetMonData3((void *)&gPlayerParty,25,0)
''','''
assert d.value('(int)GetMonData3((void *)&gPlayerParty,25,0)') > d.value('$lead_exp')
assert d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)') > 0
assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),57,0)') > 0
''','d.SWITCH_FROM_TYPES={13}\n')
    print('PASS switch training through real action/party menus:',log)
    # Two consecutive voluntary switches exercise a nonidentity menu order.
    reorder=scenario('switch-reorder','''
call (void)CreateMon((void *)&gPlayerParty,309,50,32,0,0,0,0)
call (void)CreateMon((void *)((char *)&gPlayerParty+100),284,40,32,0,0,0,0)
set *(unsigned char *)&gPlayerPartyCount = 2
call (void)CreateMon((void *)&gEnemyParty,354,13,32,0,0,0,0)
set *(unsigned char *)&gEnemyPartyCount = 1
''','''
assert switch_count[0] == 2
assert d.value('(int)GetMonData3((void *)&gPlayerParty,57,0)') > 0
assert d.value('(int)GetMonData3((void *)((char *)&gPlayerParty+100),57,0)') > 0
''','''
original_button=d.battle_button
switch_count=[0]
previous_active=[0]
def two_switches():
    active=d.struct.unpack_from('<H',d.memory('gBattlerPartyIndexes',8))[0]
    if active != previous_active[0]:
        switch_count[0]+=1; previous_active[0]=active
    function=gdb.execute('info symbol %d'%d.struct.unpack_from('<I',d.memory('gBattlerControllerFuncs',16))[0],to_string=True).split(' in ')[0]
    if switch_count[0] < 2 and function == 'HandleInputChooseAction':
        return d.cursor_button(d.memory('gActionSelectionCursor',4)[0],2)
    return original_button()
d.battle_button=two_switches
''')
    print('PASS reordered battle-party slots:',reorder)


if __name__ == '__main__':
    main()
