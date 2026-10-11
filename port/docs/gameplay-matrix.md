# Matriz T24–T28

Los fixtures controlados no equivalen a una campaña completa. ROM/save/capturas
solo en build/. T24 usa varias especies, niveles y resultados reales del motor;
GDB prepara estado y selecciona acciones, sin escribir outcomes ni forzar la victoria.
El modo --quick inicializa partida válida y salta la intro; el contador diagnóstico
se coloca en 30.500 para reutilizar pulsaciones del fixture. El recorrido de UI
original también pasó antes de activar estos fixtures rápidos.

## T24 — salvajes

| Escenario | Fixture / estado final comprobado | Resultado |
| --- | --- | --- |
| Victoria | Torchic 5 / Poochyena 2; outcome 1, experiencia aumenta, dinero intacto, Route 101 | PASS |
| Derrota | Ralts 2 / Poochyena 50; outcome 2, vuelta a casa 2F (heal location), HP restaurados, dinero disminuye | PASS |
| Huida | Treecko 80 / Zigzagoon 3; outcome 4, Route 101, HP/dinero intactos | PASS |
| Captura | Mudkip 8 / Ralts 4, Master Ball; outcome 7, equipo pasa 1→2, especie Ralts presente, bola consumida, dinero intacto, Route 101 | PASS |

Todos: exit normal, sin señales ni stream inválido; battle.raw/frame.raw locales.
Logs build/t24-{victory,loss,run,catch}.log y directorios wild-battle-regression*.

Fallo real: captura con Master Ball, Cmd_handleballthrow, frame 32.167,
eip 0x100f7b7b divl, odds=0, item=1, target=1. La tabla sBallCatchBonuses
empieza en Ultra Ball (2): índice -1 en Master Ball, luego división 16711680/0.
En ARM retail la división no lanza SIGFPE y después se fuerza captura. Parche
0032 evita el acceso fuera de tabla y fija odds=255 bajo PORT_PC; GBA no cambia.
Captura posterior: outcome 7, regreso al mapa, equipo/item correctos.
Diagnóstico privado build/t24-catch-crash.log; make compare OK en
build/t24-gba-retry.log. El primer compare paralelo se quedó esperando sin
progreso; se detuvo solo ese make y se repitió secuencialmente, sin cambiar fuentes.
32 parches reproducen árbol dbf4d4f08bcafa9e83d419538e85d4e4e6331a61.

Repro MINGW32: python port/tests/wild_battle_smoke.py --quick --scenario
victory|loss|run|catch (ejecutar un escenario por llamada).

T25, T26, T27 y T28: pendientes hasta tener sus pruebas y evidencia.
