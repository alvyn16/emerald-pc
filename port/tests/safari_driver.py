"""Natural Safari quotas: actual admission, encounters, keys and walking."""
import struct
import campaign_driver as d


def counters():
    return dict(active=d.value('(unsigned int)GetSafariZoneFlag()'),
                balls=d.memory('gNumSafariBalls',1)[0],
                steps=int.from_bytes(d.memory('sSafariZoneStepCounter',2),'little'))


def prepare():
    assert d.state()['map'] == 'Route117'
    d.RUN_WILD=True
    d.fly_to('DewfordTown')
    for attempt in range(20):
        if d.value('(int)CountTotalItemQuantityInBag(262)'):break
        objects=d.memory('gObjectEvents',16*36)
        slot=next(i for i in range(16) if objects[i*36]&1 and objects[i*36+8] == 3)
        x,y=struct.unpack_from('<hh',objects,slot*36+16)
        d.go(x-7,y-8)
        d.advance('DOWN',8,1); d.advance('A',24,1); d.settle()
    assert d.value('(int)CountTotalItemQuantityInBag(262)') == 1
    d.fly_to('LilycoveCity')
    d.go(23,25); d.cross('UP','LilycoveCity_ContestLobby')
    d.go(14,4); d.advance('UP',24,4); d.advance('A',24,1)
    for step in range(200):
        if d.value('(int)CountTotalItemQuantityInBag(273)'):break
        d.advance('A',96,1)
    else:
        raise RuntimeError('Pokeblock Case gift deadline')
    for step in range(200):
        if d.field_ready(d.state()):break
        d.advance('B',96,1)
    else:
        raise RuntimeError('Contest reception exit deadline')
    assert d.value('(int)CountTotalItemQuantityInBag(273)') == 1
    d.warp_to(14,11,'LilycoveCity'); d.connect('Route121')
    d.go(37,6); d.cross('UP','Route121_SafariZoneEntrance')
    print('NATURAL SAFARI RECEPTION READY PASS',d.state(),counters())
    return d.save_checkpoint('r07-safari-reception')


def enter():
    assert d.state()['map'] == 'Route121_SafariZoneEntrance'
    assert counters()['active'] == 0
    address=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    before=d.value(f'(int)GetMoney((void *)({address}+0x490))')
    d.go(8,4,dialogue_limit=60000)
    d.settle(60000)
    assert d.state()['map'] == 'SafariZone_South'
    address=d.value('*(unsigned int *)&gSaveBlock1Ptr')
    after=d.value(f'(int)GetMoney((void *)({address}+0x490))')
    assert after == before-500
    assert counters() == dict(active=1,balls=30,steps=500)
    print('NATURAL SAFARI ADMISSION PASS',before,after,counters(),d.state())
