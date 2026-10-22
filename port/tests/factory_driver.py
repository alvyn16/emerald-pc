"""Natural Battle Factory routes, rental selection and exchange through UI."""
import campaign_driver as d


def lobby():
    assert d.state()['map'] == 'BattleFrontier_OutsideWest'
    d.warp_to(26,65,'BattleFrontier_ReceptionGate')
    d.warp_to(4,1,'BattleFrontier_OutsideWest')
    d.go(11,39); d.cross('UP','BattleFrontier_BattleFactoryLobby')
    d.go(4,9)
    print('NATURAL FACTORY RECEPTION READY PASS',d.state())
    return d.save_checkpoint('r09-factory-reception')


def enter():
    assert d.state()['map'] == 'BattleFrontier_BattleFactoryLobby'
    d.go(4,8); d.advance('UP',24,4); d.advance('A',24,1)
    for step in range(600):
        current=d.state()
        if current['callback'] == 'CB2_SelectScreen':
            print('NATURAL FACTORY RENTAL SCREEN PASS',current)
            return
        d.advance('A',48,1)  # Challenge, Lv50, Yes/save, then native rental screen.
    raise RuntimeError('Factory admission deadline: '+str(d.state()))
