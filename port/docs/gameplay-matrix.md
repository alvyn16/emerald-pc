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

## T25 — entrenadores y mecánicas

trainer_battle_smoke.py usa el fixture rápido de captura como plantilla. Casos:
Calvin (318), May Route 103 (529), Roxanne (265), Amy/Liv (481, doble), veneno
con Guts, cambio de Pokémon, poción, combate de ≥10 turnos contra Calvin5 (331),
y Torchic 15→16, aprendizaje de Double Kick y evolución a Combusken.
Todos PASS: outcome 1, XP aumenta, dinero aumenta, flag del entrenador activado,
HP positivos, callback CB2_Overworld y Route 101. Switch verifica contador de
cambios; poción verifica contador y consumo; veneno valida Guts 62/estado durante
la selección y persistencia del estado; evolución verifica especie 281 y move 24.
El gym fixture prueba batalla de Roxanne y flag, no entrega de medalla por su script.
Los fixtures seleccionan acciones de UI en GDB; no alteran outcomes ni resultados.

Tres fallos encontrados y corregidos:
- 0033 AnimShakeMonOrBattlePlatforms (32.493): low s16 f20e se extendía a
  fffff20e y anulaba los bits altos del puntero. Reconstrucción de ambas mitades
  como u16/u32 en inicialización, paso y restauración; Rock Slide ahora PASS.
- 0034 m4aMPlayStop (31.993 doble): StopCryAndClearCrySongs antes del primer
  grito pasa NULL; lectura de ident en 0x34. Stop nulo seguro solo PORT_PC,
  regresión en suite m4a y doble combate real PASS.
- 0035 BtlController_EmitChosenMonReturnValue (33.420 gym): oponente pasa
  battlePartyOrder=NULL al sustituir un Pokémon. Son bytes sin consumidor rival;
  en host se emiten ceros sin leer address 0; cambio rival y victoria PASS.

Logs build/t25-{scenario}.log, t25-{trainer,double,gym}-crash.log. GBA original
OK (t25-gba-final.log, KEEP_TEMPS=1); 19 suites PASS. 35 parches aplicados en
checkout limpio, árbol a7fc46cdf960c354915bec3ea8339364b4cfd984 idéntico.
No se afirma cobertura de todos los estados, habilidades o combinaciones de equipos.

## T26 — menús y almacenamiento

PASS: resumen, equipo, bolsa, Pokédex, opciones y nombre, tres aperturas/cierres
por pantalla, callback de campo y especie conservados. Nombre cambia realmente
en la primera edición; las siguientes vuelven a abrir/cerrar sin bloquear.
PASS: depósito Mudkip al PC conservando Ralts en equipo; retirada Torchic;
movimiento Ralts caja 0/slot 0 → caja 1/slot 2 mediante cursor/título de caja;
depósito y retirada de una poción en el PC de objetos. Cada operación verifica
contenidos, vuelta al campo, guardado, nuevo proceso y recarga sin alterar el
archivo. Evolución y aprendizaje real: fixture evolution de T25.

0036: SetMovingMonPriority dereferenciaba sprite NULL al ocultar equipo tras
retirada (0x102890d6, dirección 5); se omite prioridad si no hay sprite. Además,
RunTasks puede liberar sStorage al salir, pero CB2_PokeStorage seguía leyendo
closeBoxFlashing (0x10286cc6, dirección 0x2c7). Sale del callback si sStorage es
NULL. Ambas protecciones PORT_PC, no cambian GBA. Logs privados
build/t26-withdraw-first.log y t26-withdraw-crash.log.

Repro MINGW32: python port/tests/menu_matrix_smoke.py <summary|party|bag|dex|options|naming>
y python port/tests/pc_matrix_smoke.py <deposit|withdraw|box|items>.
Requieren primero wild_battle_smoke.py --quick --scenario catch como plantilla.
Los fixtures crean un estado de campo aislado; no recorren la historia para llegar
al PC. No fuerzan resultados de almacenamiento. Capturas raw locales en build/.

## T27 — matriz de campaña y segmentos

Estado al 17 de octubre de 2026: campaña natural R01–R05 completa;
ocho medallas, Calle Victoria, Alto Mando, Wallace, Hall of Fame y The End.
Replay y Continue final PASS, incluyendo integridad del equipo y Hall of Fame.
R06–R15 y Checkpoint E abiertos. La tabla conserva pruebas con fixtures
preparados, identificadas como evidencia independiente de la campaña natural.

El upstream contiene 518 mapas en 34 grupos. PASS para 32 cargas seleccionadas:
las 16 ciudades/pueblos, rutas 101/110/119/124/134, casa de Brendan, Centro
Pokémon de Rustboro, Petalburg Woods, Granite Cave, Meteor Falls, Victory Road,
Safari South, exteriores/lobby Battle Tower, lobby de Concurso y guardería.
Cada carga verifica grupo/número y CB2_Overworld después de 300 frames.
Inventario exacto privado: build/map-matrix/inventory.json. `--all --group N`
permite ampliar la matriz; los otros mapas no se consideran probados.
Marcha/bici en Route 101 y surf en Route 124: flag de avatar correcto, coordenadas
cambian con input real y callback de campo conservado. Capturas privadas en build/.

| Segmento | Evidencia medida | Estado |
| --- | --- | --- |
| Liga | Fixtures previos independientes más cadena NPC Sidney/Phoebe/Glacia/Drake/Wallace desde save de ocho medallas; entrada de salas y flags por scripts | PASS, cadena dirigida con estado conservado |
| Hall of Fame/créditos | La secuencia de Wallace lleva al Hall of Fame y The End; recarga verifica game-clear, ocho medallas y un equipo HOF de tres Pokémon | PASS, transición natural tras combate dirigido |
| Concurso | Categoría Cool/Normal, cinco rondas de apelación y retorno al campo | PASS |
| Crianza | Mudkip + Ditto guardados, huevo generado por rutinas reales, especie Mudkip, IS_EGG=1, save | PASS; readiness del huevo dirigida, no espera de pasos ni eclosión |
| Safari | Huida previa más admisión/cobro 500/30 bolas, captura Magikarp, salida por pasos y limpieza de modo | PASS dirigido; rutina de pasos invocada, no paseo ni agotamiento de bolas |
| Battle Frontier | Tower singles, rival generado de la tabla de facility, Swampert/Salamence/Metagross 50, victoria y save | PASS de un combate; no racha completa ni otras seis facilities |
| Campaña continua | R01–R05 naturales completos; ocho medallas, Calle Victoria, Alto Mando, Wallace, Hall of Fame y The End; replay/Continue final | R05 PASS; R06-R15 pendientes |
| Historia | R01–R04: Devon/Peeko/Steven, gimnasios, escondites, Space Center, Dive/Seafloor, Sky Pillar/Rayquaza de historia y Sootopolis por input real | PASS para R01–R04; captura de Rayquaza PASS; contenidos posteriores pendientes |

El progreso medido procede de scripts NPC y guardados reales; warps y equipo
asistidos no acreditan recorrido ni desbloqueos de historia. T27 y Checkpoint E
siguen abiertos por esos tramos, crianza/eclosión y ampliación del Frontier.
Detalle y comandos: [campaign-progress.md](campaign-progress.md).

Fallos reales corregidos:
- 0037: Cmd_playanimation, lluvia de Wallace (frame 33.728, eip 0x100e5e91).
  Script `45 01 0a 00 00 00 00`: argumentPtr=0; lectura u16 en cero. Cero
  explícito solo PORT_PC para argumentos ausentes, también en playanimation_var.
- 0038/0039: Centro Pokémon inicia detección RFU; AgbRFU_SoftReset espera timer
  <=0x11 dentro del pump RfuMain1/HandleLinkConnection y no devuelve un frame.
  El host reporta adaptador ausente y omite el pump serie/RFU sin transporte.
  Un segundo intento mostró que omitir solo checkID no elimina otras esperas;
  ambos parches son necesarios. Accesorios continúan deshabilitados, no exitosos.
- 0040: AnimSparkElectricityFlashing_Step, SIGFPE eip 0x10035c65 durante Concurso:
  data[7] % data[4], divisor cero. Resto igual al dividendo como ARM, solo PORT_PC.
- Primer fixture de créditos tenía caught sin seen; GetSetPokedexFlag lo limpiaba
  y no quedaban especies para el sorteo. Se corrigió el fixture (seen+caught),
  sin cambiar el juego ni presentar el estado inválido como recorrido real.

Repro MINGW32: map_matrix_smoke.py; avatar_movement_smoke.py walk|bike|surf;
trainer_battle_smoke.py sidney|phoebe|glacia|drake|wallace; credits_smoke.py;
content_segment_smoke.py breeding|contest; safari_smoke.py; frontier_smoke.py.
Primero preparar wild_battle_smoke.py --quick --scenario catch. Logs t27-*.log
locales. Save/ROM del usuario intactos; ninguna fixture se publica con assets.

T28: consultar controller-input.md.


T27, recursos de campana: cosecha de Leppa del arbol, uso en Mochila, Enfado8->15PP,
consumo de Hyper Potion/Revive y Continue de PS/estados/PP/inventario: PASS.
Las derrotas nuevas de Glacia/Drake no amplian la cobertura de victorias.


### Actualizacion T27 (17-10-2026): New Mauville y Drake

Llave, puzzle del generador y Rayo de Wattson obtenidos por UI; replays PASS.
Parche0048 corrige Continue en New Mauville antes de asignar buffers BG.
Sidney/Phoebe/Glacia/Drake ganados en el replay con Rayo; Continue Drake PASS.
R05 sigue PARCIAL: puerta de Wallace guardada; final y recarga pendientes.
R06-R15 y Checkpoint E siguen abiertos. Detalle: campaign-progress.md.


Actualizacion posterior: R05 COMPLETO; Wallace/Hall of Fame/The End y Continue
final PASS. R06-R15 y Checkpoint E siguen abiertos. Ver campaign-progress.md.
