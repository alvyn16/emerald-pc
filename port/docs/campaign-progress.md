# T27: progreso de campaña con scripts reales

La prueba conserva el estado y el guardado entre encuentros. Parte de una
partida nueva de diagnóstico, con Swampert nivel 80 preparado por el harness.
Los desplazamientos entre gimnasios se asisten mediante warps y se invoca
el script de conversación del NPC. Los scripts originales ejecutan los
combates, entregan premios y actualizan medallas y variables de historia.
El test no escribe esos flags ni fuerza resultados de combate.

## Evidencia

| Tramo | Comprobación | Resultado |
| --- | --- | --- |
| Wally | Tutorial de captura, regreso al gimnasio, restauración del equipo, estado de Norman 2 | PASS |
| Roxanne, Brawly, Wattson, Flannery | Cuatro victorias mediante scripts NPC; medallas acumuladas; estado de Norman 3/4/5/6; guardado tras cada encuentro | PASS |
| Reinicio con cuatro medallas | Otro proceso carga el mismo save, conserva medallas y estado 6; lectura no cambia el archivo | PASS |
| Norman | Victoria, quinta medalla, secuencia del padre de Wally hasta su casa; estado 7 y guardado | PASS |
| Winona, Tate y Liza | Sexta y séptima medallas, incluido combate doble; mismo estado y guardado | PASS |
| Juan y recarga final | Octava medalla, ocho MT y Surf persistentes; otro proceso carga el save sin cambiarlo | PASS |
| Alto Mando | Sidney/Phoebe/Glacia/Drake mediante scripts NPC; entrada de sala avanza estado 1/2/3/4; victorias y guardados acumulados | PASS |
| Wallace y final | Entrada de sala inicia su script; victoria, diálogos con rival/Birch, warp al Hall of Fame y llegada a The End | PASS |
| Recarga tras créditos | Ocho medallas, juego completado, equipo y sectores válidos del Hall of Fame con los tres Pokémon; archivo sin cambios | PASS |
| Safari independiente | Recepción cobra 500, entrega 30 bolas y entra; captura Magikarp, cuota de pasos agotada y regreso a recepción | PASS |

Logs privados: `build/campaign-script-chain/progress-four.log`,
`juan-party-wait.log`, `juan-party-order-wait.log`; resultados en
`build/t27-campaign-*.log`. Capturas crudas de 240x160 en esa misma carpeta.
Todo permanece en `build/`, ignorado por Git.
Liga: `build/league-campaign/elite-four.log`, checkpoints 51.683/69.843/
88.603/111.443. Final: `build/champion-campaign/champion.log` y `reload.log`;
captura `end.raw`. Safari: `build/safari-admission/gdb.log`.

## Esperas del harness diagnosticadas con GDB

- Wally: el límite inicial cortaba el diálogo de regreso; seguir pulsando A
  volvía a iniciar conversaciones. Se detecta el final del contexto global
  del script y se comprueba su estado de cierre.
- El bloque de save cambia de dirección al hacer warp. El breakpoint utiliza
  un desplazamiento y el puntero vigente, en lugar de retener una dirección.
- Norman: la secuencia continúa fuera del gimnasio y entrega Surf en la casa
  de Wally. El plazo del tramo permite completar esos diálogos y movimientos.
- Juan: `CB2_UpdatePartyMenu`, `Task_ReturnToChooseMonAfterText` y
  `Task_PrintAndWaitForText`, con ambos Pokémon vivos. El menú reordena el
  equipo; comparar su posición con el índice original seleccionaba al Pokémon
  activo. El test usa `GetPartyIdFromBattleSlot` para elegir otro miembro vivo.
  Los frames continuaban avanzando: era una espera de entrada del guion.
- Captura final: detenerse al entrar en `Task_CreditsTheEnd5` capturaba el
  fade negro previo al dibujo. Se espera `Task_CreditsTheEnd6` y cuatro frames
  más; la captura se comprueba no vacía y muestra visualmente `THE END`.

Estas correcciones pertenecen al harness. No se modificaron fuentes upstream
ni el ejecutable normal para resolverlas.

## Reproducción en MINGW32

Preparar primero `wild_battle_smoke.py --quick --scenario catch` y compilar
el ejecutable de diagnóstico. Ejecutar con el Python del entorno:

```sh
python port/tests/campaign_smoke.py --through-four
python port/tests/campaign_reload_smoke.py --badges 4 --progress 6
python port/tests/campaign_smoke.py --from-four-save
python port/tests/campaign_reload_smoke.py --badges 8 --progress 7
python port/tests/league_campaign_smoke.py
python port/tests/champion_campaign_smoke.py
python port/tests/champion_reload_smoke.py
python port/tests/safari_admission_smoke.py
```

Sin opciones, el harness programa tutorial y ocho gimnasios en un proceso.
La ejecución medida se hizo por tramos reanudados desde el mismo save:
cuatro medallas, siete medallas y finalmente ocho, con recargas verificadas.
`--from-seven-save` reanuda desde el checkpoint privado de siete medallas.
Cada reanudación valida las medallas previas. Los checkpoints se generan
desde guardados reales y nunca se distribuyen.

Se restauran HP y PP con `HealPlayerParty` entre tramos, se preparan movimientos
del Swampert y se añade un Mudkip nivel 80 para el gimnasio doble. El plazo
total es 20 minutos y el watchdog sigue limitando falta de avance a 60 segundos.
Wallace añade un Metagross 80 al fixture para el reemplazo tras una derrota de
un miembro. Se preparan movimientos y registros vistos/capturados coherentes
con los Pokémon creados por el test. La entrada de la sala inicia la secuencia
de Wallace; el harness no llama directamente al Hall of Fame ni a los créditos.

Safari prepara el Pokéblock Case y un encuentro Magikarp con RNG fijado;
la captura consume bolas por el algoritmo real. La cuota se agota invocando
`SafariZoneTakeStep` por cada paso restante, sin escribir el contador. Esto
comprueba el script de salida, pero no un paseo de 500 casillas ni agotamiento
de las 30 bolas.

## Cobertura pendiente

Este recorrido dirigido valida continuidad de estado entre scripts. Todavía
quedan desplazamientos y puzzles,
Aqua/Magma, meteorito, Weather Institute, Space Center, Sky Pillar/Rayquaza
y las condiciones que permiten llegar a cada gimnasio y entrar en la Liga.
El estado/save dirigido sí continúa desde Wally hasta los créditos.
También quedan agotamiento de bolas de Safari y rachas/otras instalaciones
del Frontier. Crianza aún no comprueba eclosión ni espera de pasos natural.
T27 y Checkpoint E permanecen abiertos.

Verificación de base: 21 suites host y `verify-normal` PASS;
`make compare KEEP_TEMPS=1 NODEP=1`: `pokeemerald.gba: OK`.

## R01: inicio natural y recarga mediante Continue

Partida nueva en `build/natural-campaign/`, con save privado vacío. La intro,
reloj, madre y visita a May se controlaron con entradas de teclado. El driver
lee colisiones del mapa y posición del jugador para planear desplazamientos;
solo recarga el archivo de input y mueve el límite de frames del diagnóstico.
No llama funciones para conceder Pokémon, experiencia, objetos, flags o warps.
Solo omite la salida programada de `Port_ExitCleanly` para continuar el test;
una parada en otra función falla y conserva el backtrace.

Checkpoints medidos:

| Frame | Resultado leído |
|---:|---|
| 35540 | Visita a May, estado de casa rival 3; equipo vacío |
| 39272 | Selector de inicial abierto desde la bolsa de Birch |
| 42176 | Victoria en el rescate, Mudkip recibido, laboratorio de Birch |
| 45932 | Entrega/nombre completados; especie 283, nivel 5 |
| 56696 | Enfermera de Oldale cura por diálogo: HP 23/23 |
| 64928 | May en Ruta 103 derrotada: outcome 1, flag 0x82 activo |
| 78680 | Pokédex entregada, cinco Poké Balls; guardado por Start/Save |

Los encuentros salvajes del camino elevaron naturalmente a Mudkip a nivel 7.
El save final está en el laboratorio, casilla (6,5), un miembro en el equipo.
`r01-birch-dex.json` registra mapa, especie, nivel, flags y bolas.
`natural_campaign_reload.py` abre una copia en un proceso nuevo, pulsa A
en intro/título/Continue y comprueba esos campos sin escribir progreso.
Resultado: `Natural campaign Continue/reload PASS; save unchanged`.

Los helpers medidos están en `campaign_driver.py` y
`natural_campaign_routes.py`. El recorrido interactivo conserva inputs y
checkpoints en `build/natural-campaign/route.jsonl`; no se publica la partida,
ROM, mapas, capturas ni datos del juego. ROM y save originales mantienen sus
hashes anteriores. Esta evidencia cierra R01; no acredita R02–R15.

Reproducción de la recarga tras generar el checkpoint privado:
`python port/tests/natural_campaign_reload.py`, desde MINGW32 con GDB.

Reproducción completa desde un save vacío:
`python port/tests/natural_campaign_smoke.py`.
La repetición independiente pasó y guardó Mudkip nivel 8 en el laboratorio
(frame 85752). El nivel varía con los encuentros naturales y tiempos de
desplazamiento; se compara con el JSON leído de cada guardado, no se fija por
el debugger. Todos sus inputs y artefactos quedan en `build/natural-campaign-replay/`.

## R02: Wally, Devon y primera medalla — parcial

La misma campaña completó el tutorial de Wally (estado del gimnasio 2,
frame 125108) y comprobó que Norman todavía rechaza el combate y que la puerta
superior izquierda permanece bloqueada: posición (1,106) antes/después de Up.
Después del robo en el bosque, la primera derrota contra Aqua volvió a la
enfermería; un segundo recorrido ganó, recibió la Great Ball y dejó el estado
del bosque en 1. Checkpoint `r02-devon-woods`: Mudkip nivel 11, frame 189536.

La derrota contra Geodude en Rustboro descubrió la excepción corregida por
0041, descrita en `first-run-report.md`. Se reanudó desde ese último guardado
mediante Continue. El equipo subió y evolucionó mediante combates del juego.
Victoria contra Roxanne: flag 0x4F0 activo, medalla 0x867 activa, estado de
Norman 3. `r02-roxanne` guarda Marshtomp (especie 284) nivel 16, mapa gimnasio
de Rustboro, casilla (5,3), frame 83784 del proceso reanudado.
Su copia reabre por Continue y conserva especie/nivel, mapa/casilla, Pokédex,
bolas, medalla, estado del bosque y estado de Norman; save sin cambios: PASS.

`python port/tests/natural_campaign_reload.py r02-roxanne` reproduce esa
recarga. Los mapas se recorren con teclas; el planner lee colisiones, atributos
y objetos activos para evitar agua sin Surf. Las opciones de combate también
se eligen con direcciones/A/B, leyendo PP y el cursor. Las excepciones y los
deadlines fallan explícitamente. No se acredita todavía el resto de R02–R15.

Verificación de 0041 en el clon de reproducción: normal/diagnóstico,
21 suites y `verify-normal` PASS (`build/t27-shadow-clean-build.log`).

### Peeko, PokéNav y Brawly

En el mismo save, Corte se obtuvo por diálogo y el combate de Rusturf Tunnel
rescató a Peeko: flag 0x8F activo, estado de Briney 1. Checkpoint `r02-peeko`,
frame 131996 del segundo proceso: Marshtomp nivel 17 y una medalla.
La devolución de bienes activó 0x90; Mr Stone entregó carta y PokéNav por
su secuencia. El tutorial de Match Call se completó con direcciones/A/B y
dejó Rustboro en estado 7. `r02-matchcall` guarda ese avance.

La espera de Match Call era de la prueba: A repetido no selecciona su opción
ni sale del dispositivo. El driver lee el cursor/callback y pulsa las teclas
correctas. Un SIGINT de GDB pausó deliberadamente el harness para actualizarlo;
se continuó hasta el siguiente checkpoint de frames, sin saltar código del
juego. No fue una excepción del port.

`python port/tests/natural_campaign_smoke.py --phase r02-devon` reabre una
copia del save real de Roxanne y repite Corte, Peeko, entrega a Stone y llamada.
Repetición independiente PASS, sin escribir progreso desde GDB:
`build/natural-campaign-replay-r02-devon/campaign.log`.

Briney llevó al jugador a Dewford por la secuencia real del barco. Se caminó
el gimnasio y Brawly fue derrotado: flag de segunda medalla 0x868 activo.
Checkpoint `r02-brawly` (frame 247673): Marshtomp nivel 19, dos medallas,
estado de Norman 4. Una copia reabre por Continue y conserva equipo, ubicación,
medallas y flags de los eventos anteriores, sin modificar el save: PASS
(`build/t27-brawly-reload.log`). Capturas privadas: `r02-brawly.png` y
`r02-dewford.png` en `build/natural-campaign/`.

Al entrar realmente a Granite Cave B1F se encontró el copyvar literal
documentado en `first-run-report.md`. Seleccionar UBFIX en los datos host
corrige esa transición. Tras reabrir el checkpoint de Brawly y repetir
enfermera, costa, hiker y escalera, B1F carga y VAR_ICE_STEP_COUNT vale 1.
También pasan normal/diagnóstico, 21 suites y verify-normal en el clon de
reproducción (`build/t27-script-ubfix-clean-build.log`). R02 sigue parcial.

### Carta a Steven y museo de Slateport

Desde Brawly se recorrieron las escaleras reales de Granite Cave hasta Steven.
El hiker entregó Flash (flag 0x6D); Steven recibió la carta por diálogo
(0xBD). Checkpoint `r02-steven`: frame 53044 del tercer proceso, Marshtomp
nivel 19 y dos medallas. `natural_campaign_reload.py r02-steven` reabre
Continue y conserva los campos del checkpoint y el save sin cambios: PASS
(`build/t27-steven-reload.log`).

Se salió de la cueva, se seleccionó Slateport en el menú de Briney y se
recorrió Ruta 109. El planner anterior intentaba subir directamente del muelle
(elevación 4) a la playa (3): GetCollisionAtCoords devuelve 3, rechazo correcto
del juego. El planner ahora conserva elevación y busca las transiciones 0/15.
Usa las escaleras reales, sin escribir coordenadas ni colisiones.

`natural_campaign_smoke.py --phase r02-steven` repite en otro proceso desde
una copia del save de Brawly: Flash, escaleras, Steven, retorno, menú del barco,
Ruta 109, enfermera y guardado en Slateport. PASS, salida normal, sin señales:
`build/t27-natural-steven-replay.log`. La diferencia de frames/combates entre
recorridos procede del avance real de RNG; no se modifica la semilla.

En la campaña principal se habló con Dock (0x94 activo), se pagó la entrada
del museo y se completaron los dos combates seguidos de Aqua y la intervención
de Archie. Stern recibió los bienes (0x95 activo); el script curó el equipo.
`r02-stern`: frame 132876, Marshtomp nivel 20; `r02-slateport`: frame 138224,
tras salir del museo y completar el diálogo de Scott. Ruta 110 se alcanzó
desde la conexión norte de la ciudad; checkpoint `r02-route110`, frame 148256.
R02 aún requiere Wattson, Flannery y los eventos de Mt. Chimney; R03–R15
siguen pendientes. Este tramo no cierra T27 ni Checkpoint E.

### Capturas, aprendizaje y rival de Ruta 110

La captura natural de Wingull abrió el nombre y descubrió el fallo 0042.
Tras corregirlo se reabrió `r02-route110` por Continue y se repitió la captura:
`r02-first-catch`, frame 19448 del cuarto proceso, Marshtomp 20/Wingull 12,
Poké Balls 5→4. La recarga conserva equipo, ubicación, eventos y save sin
cambios: PASS (`build/t27-first-catch-reload.log`).

`natural_campaign_smoke.py --phase r02-catch` repite desde esa copia previa
de Ruta 110 y captura Wingull con bolsa/teclas, acepta el nombre y guarda:
PASS (`build/t27-natural-catch-replay.log`). Buscar una especie rara tiene
un límite explícito; los waypoints se alcanzan leyendo la posición, porque
un encuentro puede interrumpir una pulsación y deshacer la simetría de un
recorrido basado únicamente en tiempo. No se modifica RNG ni se crea el mon.

La campaña perdió inicialmente contra el rival y volvió al Centro Pokémon.
Se cambió el orden del equipo desde su menú, se entrenó mediante combates,
se visitó la enfermera y se capturó Oddish por la misma bolsa. En encuentros
eléctricos el driver cambia a Marshtomp con el menú real; el juego concede
experiencia compartida. `r02-wingull-trained`, frame 245100 del quinto
proceso, guarda Wingull 17/Marshtomp 22/Oddish 13. Los guardados `r02-training`
conservan cada visita/tramo para reanudar sin conceder experiencia.

Una interrupción de la sesión de terminal obligó a reabrir el último save
real; el entrenamiento no guardado del proceso anterior se repitió.
Las pausas SIGINT posteriores fueron deliberadas para ajustar el driver,
sin saltar funciones del juego. La espera en el menú de equipo era del
harness: al abrirlo se reordena gPlayerParty para mostrarlo; los índices de
los battlers conservan el orden de campo. Ahora se compara mediante los
nibbles de gBattlePartyCurrentOrder antes de seleccionar con direcciones/A.

Regresiones aisladas (no progreso de campaña): reemplazo tras desmayo,
rechazo de Mist conservando ataques, aprendizaje de Quick Attack en un slot
de estado, cambio para compartir experiencia y dos cambios consecutivos con
orden no identidad: PASS (`build/t27-battle-menu-regression.log` y
`build/t27-switch-training-regression.log`). Los dos casos de aprendizaje
usan Chansey con Splash para aislar la UI de la táctica del rival.

Tras corregir el driver se completó el segundo intento del rival por teclas:
outcome 1 y VAR_ROUTE110_STATE (0x4069)=1. `r02-may110`, frame 315256,
guarda Marshtomp 23/Wingull 18/Oddish 13, dos medallas. Una recarga conserva
los campos registrados y el save sin cambios: PASS
(`build/t27-may110-reload.log`).

`--phase r02-museum` también pasó desde una copia del save de Steven:
Up ante el grunt mantiene (30,28), Dock desbloquea la entrada, el evento de
la casilla (9,7) cobra exactamente 50 y cambia el estado del museo a 1.
Terminan los dos combates y la entrega a Stern por diálogo; salida normal:
`build/t27-natural-museum-replay.log`. R02 sigue abierto para los gimnasios
y eventos restantes; T27/Checkpoint E continúan abiertos.
