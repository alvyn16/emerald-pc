# T27: progreso de campaña con scripts reales

## Estado actual: 30 de octubre de 2026

La campaña continua natural completa R01–R05: ocho medallas, Calle Victoria,
cuatro victorias del Alto Mando, Wallace, Hall of Fame y The End. El replay
del Campeon y la recarga final por Continue PASS: regreso al dormitorio,
ocho medallas, game-clear, seis especies/niveles y Hall of Fame valido.
Continue no modifica el archivo guardado. No se concedio progreso por GDB.

R06–R09 y R11–R15 completos. R10 y Checkpoint E siguen abiertos. Las victorias, créditos y Hall of Fame
de fixtures con equipo preparado son pruebas anteriores independientes.
Consulta [cobertura pendiente](tasks/t27-remaining.md) y
[informe de ejecución](first-run-report.md). Los checkpoints, capturas,
ROM y saves se conservan localmente y no se distribuyen en Git.

## Antecedente: fixture dirigido con equipo preparado

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

### Mauville: acceso, puzzle y controles de combate

En la campaña se comprobó el bloqueo de la puerta del gimnasio por Wally
desde (8,7), se completó su combate y diálogo y se activó 0xBE. El checkpoint
`r02-wally-mauville` conserva Marshtomp 23/Wingull 18/Oddish 13. Dentro del
gimnasio, Up desde (4,15) mantiene esa posición ante la barrera eléctrica.
Pisar los interruptores (0,15), (3,9) y (8,9) abre el camino hasta (5,3),
delante de Wattson. Los entrenadores se derrotaron mediante encuentros
reales; `r02-gym-trainers` conserva Marshtomp 25/Wingull 19/Oddish 16.

Las derrotas y retornos al Centro Pokémon de este tramo fueron resultados
del combate. El driver necesitaba escoger tanto movimiento como objetivo
en dobles, en vez de asumir un rival fijo. Ahora lee los rivales vivos,
tipos, habilidades y modificadores, y confirma el objetivo con direcciones/A.
La regresión aislada comprueba Mud-Slap contra el objetivo 3 y Wing Attack
contra el 1, incluyendo el cursor real: PASS
(`build/t27-double-target-regression.log`).

Se compraron tres Super Potions en la tienda de Mauville con los menús de
cantidad y confirmación: dinero 2434→334, coste 2100, cantidad 0→3.
`r02-supplies` (frame 477172 del quinto proceso) guarda Marshtomp 26,
Wingull 19 y Oddish 16, dos medallas y el puzzle/entrenadores anteriores.
El driver permite consumir medicina disponible mediante acción, bolsillo y
selección de Pokémon; no concede objetos. La regresión aislada de HP bajo
consume una Super Potion real del fixture: PASS
(`build/t27-healing-regression.log`).

Otro intento aceptaba el cambio opcional entre Pokémon de Wattson mediante
el opcode 0x67 del script de combate, enviando compañeros débiles frente a
ataques eléctricos. El controlador ahora rechaza esa pregunta con B.
Un fixture separado de entrenador con dos Pokémon comprueba victoria,
retorno al campo, inicial conservado y compañero sin experiencia: PASS
(`build/t27-no-optional-swap-regression.log`). Estos fixtures preparados
validan los controles; no cuentan como progreso natural. Wattson y el resto
de R02 aún requieren sus propios checkpoints de victoria.

En el sexto proceso se reabrió `r02-supplies` mediante Continue. Las pulsaciones
de A de la recarga entraron de nuevo en la tienda y compraron una Poké Ball
adicional; se salió con B según la tarea activa. Durante el paseo apareció
una llamada de PokéNav: script inactivo, pero controles bloqueados. El planner
ahora devuelve el control a `settle` también ante ese bloqueo. La regresión
`campaign_incoming_call_smoke.py` prepara una llamada de un entrenador válido,
comprueba que no se camina durante ella, la confirma por teclas y continúa:
PASS (`build/t27-incoming-call-regression.log`). Su primer fixture omitía el
trainerId requerido y fallaba al construir el texto; se corrigió la preparación
del test, sin modificar el juego.

Wattson finalmente fue derrotado: outcome 1, tercera medalla 0x869 activa,
Norman=5. Se consumieron las tres Super Potions. `r02-wattson` (frame 69068
del sexto proceso) conserva Marshtomp 27/Wingull 19/Oddish 16 y cuatro Poké
Balls. La recarga independiente conserva los campos registrados y el archivo
sin cambios: PASS (`build/t27-wattson-reload.log`). Registro de ruta/combate:
`build/natural-campaign/gdb-wattson-supply-reload.log`. R02 sigue abierto para
Flannery, meteorito y Mt. Chimney; R03–R15 continúan pendientes.

### Rock Smash y continuación hacia el norte

El NPC de Mauville entregó HM06 por diálogo (0x6B). Se enseñó Rock Smash a
Marshtomp mediante bolsa, selección de Pokémon y resumen para olvidar un
movimiento; se conservaron Growl, Mud-Slap y Water Gun. La HM permanece en la
bolsa. Checkpoint `r02-rocksmash-learned`: frame 83332 del sexto proceso.
La regresión aislada de enseñanza también pasa, incluyendo retorno al campo
y conservación de la HM (`build/t27-hm-teaching-regression.log`).

En Ruta 111, Up desde (18,102) no atraviesa la roca. El diálogo de Rock Smash
activa FLAG_TEMP_11 y permite caminar a (18,100). Checkpoint
`r02-route111-rock`: frame 95644, Marshtomp 27/Wingull 20/Oddish 16.
`natural_campaign_smoke.py --phase r02-rocksmash` repite el recorrido desde
una copia de la victoria de Wattson: enfermera, entrega, enseñanza, bloqueo,
rotura, cruce y guardado. PASS, salida normal y sin señales
(`build/t27-natural-rocksmash-replay.log`).

Se comprobó el bloqueo del teleférico antes del evento de Meteor Falls:
Up desde (26,31) mantiene la posición ante Magma (frame 118208). Se recorrió
Fiery Path hasta su salida norte; esta salida se cruza hacia abajo desde
(26,3). La conexión accesible de Ruta 112 hacia el norte pasa por el este,
no por su borde superior. Las coordenadas propuestas incorrectamente por
el harness produjeron rechazos explícitos; no se modificaron warps ni mapas.

Un combate posterior en Ruta 111 agotó el equipo y devolvió al jugador a
Mauville. `r02-road-blackout` guarda ese resultado real: frame 183628,
Marshtomp 29/Wingull 20/Oddish 18. El manifiesto ahora registra también
movimientos, cantidades de medicina/HM y dinero. Una recarga independiente
comprueba esos campos y conserva el save sin cambios: PASS
(`build/t27-road-blackout-reload.log`). Tras repetir el camino y Fiery Path,
`r02-route111-north` guarda el acceso norte (0,30), frame 209464, dinero 4047.
No se acredita todavía Ruta 113, Meteor Falls, Flannery ni el cierre de R02.

### Descanso real y acceso a Ruta 113

Se reabrió `r02-route111-north` con Continue en un séptimo proceso. El archivo
de trabajo coincide con el checkpoint (SHA-256
`405f39c0dac76cbba1704d53e6e5a919e75ef053c050b71cf0654d1883bb5469`).
Se caminó hasta la casa de descanso de Ruta 111 y se habló con la anciana
desde (6,4). El driver confirma el primer descanso y rechaza la pregunta
repetida mediante A/B. Un breakpoint de observación cuenta la ejecución real
de `HealPlayerParty`; nunca omite ni llama la función por su cuenta.

`natural_campaign_smoke.py --phase r02-rest` repite desde una copia del save:
Continue, paseo, entrada, diálogo y guardado. Comprueba exactamente una cura,
HP/PP completos y estados curados para todo el equipo. PASS, sin señales y
salida normal (`build/t27-natural-rest-replay.log`). La casilla (5,3) de la
casa resultó no transitable; se corrigió el punto de interacción del harness,
sin modificar el mapa.

La campaña principal guardó `r02-rested-north` (frame 15140) y continuó por
Ruta 111. Se ganó el combate pendiente y se cruzó a Ruta 113 por la conexión
oeste. `r02-route113` (frame 31652 del séptimo proceso) conserva Marshtomp 30,
Wingull 20/Oddish 18, tres medallas y dinero 4863. El registro permanece en
`build/natural-campaign/gdb-north-resume.log`; el tramo anterior se conserva
en `route-before-north-resume.jsonl`. R02 y T27 continúan abiertos.

### Meteor Falls y acceso al teleférico

Se cruzó Ruta 113 y se curó el equipo en Fallarbor. `r02-fallarbor` (frame
45744 del séptimo proceso) conserva tres medallas y el equipo 30/20/18.
La recarga verifica los campos registrados y conserva el save: PASS
(`build/t27-fallarbor-reload.log`). Se recorrió Ruta 114, sus entrenadores y
la entrada a Meteor Falls. La escena de Magma/Aqua terminó con
VAR_METEOR_FALLS_STATE (0x40BF)=1 y FLAG_HIDE_ROUTE_112_TEAM_MAGMA (0x333)=1.
`r02-meteor-falls` se guardó inicialmente en 85564 y se volvió a guardar en
86596 para incluir esos indicadores en el manifiesto: Marshtomp 31,
Wingull 20/Oddish 18. La recarga de ese manifiesto ampliado pasa y no reescribe
el save (`build/t27-meteor-falls-reload.log`).

`--phase r02-meteor` repite desde la copia anterior de Fallarbor, comprueba
ambos indicadores inicialmente a cero y su activación por la escena, y
guarda. PASS, sin señales y salida normal
(`build/t27-natural-meteor-replay.log`). El retorno correcto de la cueva es
hacia abajo desde (27,17): la casilla de salida tiene comportamiento 0x65,
flecha sur. La dirección este propuesta por el harness no cruzaba el warp.

El driver ahora selecciona conexiones leyendo las dimensiones, dirección,
offset y tamaño del mapa vecino, y busca el borde alcanzable más cercano.
Así no supone que Fallarbor tenga 40 casillas de ancho ni mezcla los dos
tramos de conexión oeste de Ruta 111. `--phase r02-connections` recorre
Fallarbor→113→111→112→111→113→Fallarbor mediante teclas. Comprueba cada mapa
y guarda al terminar: PASS (`build/t27-natural-connections-replay.log`).

Tras volver a Fallarbor y curarse (`r02-meteor-return`, frame 105400), la
campaña caminó por Ruta 113 y Fiery Path hasta el teleférico. Entrada libre
medida en frame 152976, viaje por diálogo completado en 154416.
`r02-chimney-arrival` (155892) guarda Mt. Chimney (17,37), equipo 32/21/18,
tres medallas y dinero 9311. El bloqueo previo al evento y el acceso posterior
están comprobados; Maxie, meteorito y Flannery aún requieren verificación.
ROM original y save del usuario conservan los hashes registrados.

### Primer intento contra Maxie y abastecimiento

Se ganaron los combates de acceso de Magma, pero el primer intento contra
Maxie terminó en outcome 2: regreso normal a Fallarbor. No hubo excepción
del port. El equipo había llegado a la cima con HP 36/95, 24/54 y 45/45.
`r02-maxie-loss` (frame 187340) conserva esa derrota y los entrenadores de
acceso ya vencidos, con Maxie aún pendiente.

Se añadió selección de artículos/cantidad, confirmación y salida de la tienda
al driver. Lee la lista y cursores reales, usa direcciones/A/B, y comprueba
el incremento exacto en la bolsa y el cargo total mostrado por el juego.
`--phase r02-shop` repite desde una copia anterior de Fallarbor y compra
tres Super Potions; salida normal, sin señales: PASS
(`build/t27-natural-shop-replay.log`).

En la campaña se compraron seis Super Potions: cantidad 0→6, coste 4200,
dinero 5495→1295. `r02-maxie-supplies` (190872) guarda el equipo 32/21/18 y
esas medicinas. El siguiente intento conserva las reglas de HP/experiencia
reales y utiliza el controlador de medicina ya verificado. No se concede
ningún objeto ni dinero por GDB.

### R02 completo: Maxie, Jagged Pass y cuarta medalla

El segundo intento contra Maxie terminó en victoria (frame 239344 del séptimo
proceso). Se recogió el meteorito por diálogo: flags 0x8B y 0x73 activos.
`r02-maxie-meteorite` (241792) guarda Marshtomp 33/Wingull 21/Oddish 18,
cinco Super Potions y dinero 3871. La recarga de equipo, eventos, cantidades
y dinero conserva el save: PASS (`build/t27-maxie-reload.log`).

El planner intentaba entrar a una pendiente de Acro Bike (comportamiento
0xD1) en Jagged Pass. El juego rechazaba el paso; no era una espera de IRQ.
Ahora se evita esa pendiente y se modelan los saltos de dos casillas solo
en la dirección permitida del desnivel. Se valida la casilla de aterrizaje
y se espera que termine la animación. `--phase r02-jagged` repite desde la
copia de Maxie, comprueba el incremento real de GAME_STAT_JUMPED_DOWN_LEDGES,
llega a Lavaridge y cura/guarda: PASS (`build/t27-natural-jagged-replay.log`).
`r02-lavaridge` principal: frame 272140, equipo 33/21/18 y cuatro Super Potions.

El puzzle de Flannery requiere también un desnivel en B1F. El planner evita
pisar piscinas intermedias: la selección de (8,9) cruzaba antes la de
(10,18), cambiando de piso antes de alcanzar el waypoint. Ruta medida desde
la entrada, alternando 1F/B1F: (8,9), (0,17), (0,10), (0,6), (2,3), (7,2),
(10,6), (12,12). Llegada a la sala de la líder en (13,12); interacción desde
(13,10). Los entrenadores enterrados encontrados se combatieron normalmente.

La campaña ganó a Flannery: `r02-flannery`, frame 332328, equipo 34/21/18,
cuatro medallas, Norman=6, dinero 10627 y las cuatro Super Potions consumidas.
Continue conserva los campos registrados y el archivo sin cambios: PASS
(`build/t27-flannery-reload.log`). Tras salir, May entregó Go-Goggles (0xDD=1)
y se visitó la enfermera: `r02-four-badges`, frame 341348.

La primera repetición independiente del puzzle llegó a la líder y perdió
el combate por agotamiento de curación; se conserva como fallo de la prueba
en `build/t27-flannery-initial-loss-gdb.log`. La repetición con compra real
de seis Super Potions adicionales usa dinero de la copia de Lavaridge,
verifica los ocho cambios de piso y el salto y obtiene la cuarta medalla.
PASS, sin señales y salida normal (`build/t27-natural-flannery-replay.log`;
checkpoint de la copia en 71860). No se fuerza RNG ni se conceden recursos.

R02 queda verificado junto con sus etapas anteriores: cuatro gimnasios,
Devon/Peeko/Briney, Aqua/Slateport, meteorito/Magma y gating antes/después.
R03–R15 y T27/Checkpoint E siguen abiertos. El runtime del juego no necesitó
parches nuevos en este tramo; los cambios son del controlador y sus pruebas.

### R03 en curso: Fuerza y regreso a Petalburgo

Se compraron diez Super Potions en Lavaridge por el menú real (7000 de dinero).
El regreso pasó por Route112/111, Mauville, Route117 y Verdanturf, con combates
de entrenadores y Rock Smash sobre la roca regenerada de Route111.
En Rusturf Tunnel, desde (25,5), LEFT fue rechazado por la roca (24,5)
(frame 374900). La interacción con Rock Smash abrió el paso y completó la
reunión de Wanda; HM Strength pasó de cero a una unidad en el frame 378068.
`r03-strength` (388620) conserva Marshtomp 35/Wingull 22/Oddish 18,
cuatro medallas, diez Super Potions y dinero 5771. No se enseñó Fuerza aún.

Route104 permitía caminar hasta (39,61), pero el paso siguiente hacia
Petalburgo era una pared. El planner ahora comprueba también la casilla
cargada del mapa vecino y que el último paso cruce en la dirección de la
conexión. El cruce real funciona en (39,63). La repetición independiente
`natural_campaign_smoke.py --phase r03-petalburg`, desde el save de Fuerza,
cruza Petalburg Woods, llega a la ciudad y cura/guarda: PASS, sin señales y
salida normal (`build/t27-natural-petalburg-replay.log`).
Checkpoint principal `r03-petalburg`: frame 407968, equipo 35/22/18,
nueve Super Potions, dinero 5915 y HM Surf aún ausente.

La repetición `--phase r03-strength` parte del save de Verdanturf y comprueba
rechazo de la roca, obtención de Fuerza y cruce posterior: PASS
(`build/t27-natural-strength-replay.log`). Continue del checkpoint principal
de Fuerza conserva todos los campos y el archivo: PASS
(`build/t27-strength-reload.log`).

### Norman y quinta medalla

La sala de Velocidad se abre mediante A/Yes, no caminando contra su puerta.
Ruta real: entrada desde (1,106), Randall desde (4,82), puerta (1,80), Parker
desde (4,43), puerta (7,41), Jody desde (4,17), puerta (7,15), Norman (4,3).
Los tres accesos rechazaron la entrada antes del entrenador correspondiente
y permitieron el paso después de vencerlo. Marshtomp evolucionó a Swampert
al nivel 36 durante los combates; Fuerza se enseñó por el menú real.

Los intentos exploratorios con pocas medicinas perdieron normalmente:
`r03-norman-result` (468120), `r03-norman-retry-result` (504324) y
`r03-norman-special-result` (522448). Los dos primeros llegaron a Slaking;
el tercero, sin medicinas, perdió ante Linoone. Ninguno produjo una señal
del debugger o un fallo del runtime. No cuentan como victoria ni como
regresión resuelta. Una preferencia experimental por Water Gun no mejoró
ese intento y se retiró del controlador; no se cambia la estrategia general.

`--phase r03-norman` repite desde `r03-petalburg`, compra seis Super Potions
con 4200 del dinero existente, prueba la orilla (7,20) sin Surf/quinta medalla,
enseña Fuerza, verifica los tres pares de puertas y gana a Norman. El script
continúa hasta casa de Blasco y entrega HM Surf. PASS, sin señales y salida
normal (`build/t27-natural-norman-replay.log`). El save `r03-norman` (91564
de esa repetición) tiene Swampert 37/Wingull 22/Oddish 18, cinco medallas,
Norman=7, Surf=1, Fuerza=1, tres Super Potions y dinero 8559.
La recarga independiente conserva equipo, movimientos, progreso e inventario
sin escribir el archivo: PASS (`build/t27-norman-reload.log`).

Para continuar se ha cargado por Continue ese guardado ganador, que desciende
del mismo checkpoint natural de Petalburgo. Se conservan aparte el guardado
y la traza de los intentos perdidos; no se mezclan sus niveles/consumibles con
los de la rama ganadora. El nuevo proceso reinicia su contador de frames.
R03 sigue abierto: faltan Surf en campo, Weather Institute, Fly y Devon Scope.

Surf en campo ya está comprobado: `--phase r03-surf` enseña HM03 a Swampert
por mochila (Water Gun se sustituye por Surf), cura y usa A/Yes desde (7,20).
El jugador entra en (6,20) con PLAYER_AVATAR_FLAG_SURFING, navega hasta (4,20)
y desembarca de nuevo en (7,20), volviendo al modo a pie. PASS
(`build/t27-natural-surf-replay.log`). El primer intento del harness falló al
planear el desembarco: rechazaba el cambio de elevación 1→3 que el juego
permite mediante CanStopSurfing. Ahora el BFS conserva el modo de movimiento
por nodo, permite ese paso y espera la animación; una vez en tierra no puede
volver al agua sin el diálogo real. El juego no requirió parche.
Checkpoint principal `r03-surf`: frame 19812 del nuevo proceso, equipo 37/22/18,
movimientos de Swampert Rock Smash/Take Down/Strength/Surf y cinco medallas.
Capturas inspeccionadas: `build/natural-campaign/r03-{strength,norman,surf}.png`.

Otro límite del planner apareció al regresar por Route117: el borde (0,6)
es una casilla aislada; el carril útil está en y=8. El BFS podía intentar salir
a Verdanturf para rodear la pared, cambiando de mapa antes de su objetivo.
Ahora solo admite casillas del mapa actual y la casilla de salida pedida
explícitamente. El recorrido medido usa Verdanturf (19,8)→Route117 (0,8).
Una casilla transitable en el borde no garantiza que conecte con el interior;
los recorridos deben seguir verificando el destino y usar waypoints medidos.

Regresión de conexiones tras estos ajustes: ida/vuelta entre Fallarbor,
Route113, Route111 y Route112 con combates reales: PASS, sin señales ni salida
anormal (`build/t27-natural-connections-shore-regression.log`). El recorrido
principal llegó después a Mauville, curó y guardó en `r03-mauville` (75624),
con el mismo equipo 37/22/18, Surf aprendido, tres Super Potions y dinero 9439.

### Instituto Meteorológico y Castform

Desde Mauville se cruzó Route118 por Surf: orilla (17,9), entrada (18,9),
desembarco (31,9). La aproximación a (17,10) se rechazó por un NPC; se usó
la casilla contigua. Tras la escena de Steven y combates de entrenadores,
`r03-route119` (110040 del octavo proceso) guarda Swampert 38/Wingull 22/
Oddish 18, cinco medallas y dinero 11503.

En Route119 el planner intentó subir la pendiente de barro (6,55), MB 0xD0.
ForcedMovement_MuddySlope devuelve al jugador hacia el sur si no se dirige
al norte con PLAYER_SPEED_FASTEST. No era un bloqueo del runtime. Se excluye
esa pendiente de las rutas a pie, como ya se hacía con la pendiente Acro 0xD1.
El recorrido rodeó el obstáculo y llegó al instituto. Antes del evento,
RIGHT desde (12,33) fue rechazado por el recluta Aqua del puente: PASS.
Se usó la cama desde (2,3), mirando a la izquierda. `r03-weather-arrival`
(153892) conserva Swampert 38/Wingull 23/Oddish 18 y dos Super Potions.

En el edificio: escalera 1F desde (17,2) hacia arriba y Shelly desde (5,6)
mirando a la izquierda; los reclutas encontrados se combatieron normalmente.
El evento dio Castform 25 y activó 0x97. `r03-castform` (192564) guarda equipo
39/23/18/25, cinco medallas, dos Super Potions y dinero 17931. Swampert aprendió
Muddy Water al nivel 39, reemplazando Take Down por la UI de movimientos.
Continue conserva ese equipo, movimientos, regalo, cantidades y dinero sin
alterar el archivo: PASS (`build/t27-castform-reload.log`).

Tras el regalo, VAR_WEATHER_INSTITUTE_STATE es 1; salir a Route119 mueve los
trabajadores y la avanza a 2. Después de descansar se cruzó el puente hasta
(14,33): PASS, `r03-weather-cleared` (196880), Route119 state=0 (rival pendiente).
`--phase r03-weather` reproduce combates/regalo/cama/cruce desde la copia de
llegada: PASS, sin señales y salida normal (`build/t27-natural-weather-replay.log`).
La cama verifica HP completos y estados curados para los cuatro Pokémon.
Las variables del instituto y Route119 se incluyen ahora en los manifiestos
y se comprueban al recargar. Capturas inspeccionadas de regalo y puente en
`build/natural-campaign/r03-{castform,weather-cleared}.png`.
Continue de `r03-weather-cleared` comprueba también ambas variables y conserva
el archivo sin cambios: PASS (`build/t27-weather-cleared-reload.log`).

Se inicia entrenamiento real de Wingull antes del rival: cambio de líder
por menú, combates en hierba (11–13,38) y descansos en la cama. No se concede
experiencia ni se altera el equipo por GDB. R03 sigue abierto por Fly/Devon Scope;
R04–R15 y T27/Checkpoint E continúan abiertos.

### Rival 119, Vuelo y Detector Devon

El entrenamiento de Wingull 23 terminó en evolución real a Pelipper 25:
`r03-wingull-training` (251548), con Protect aprendido durante la evolución.
Solo se usaron pasos, combates y la cama. Continue conserva la evolución y
los movimientos: PASS (`build/t27-pelipper-reload.log`). Con Pelipper de líder
se enseñó Surf (reemplaza Protect), se cruzó el puente y se activó el rival
en (25,31). Victoria y HM Fly por diálogo: `r03-fly` (278004), equipo
25/39/18/25, Route119=1, 0x6E=1, HM02=1, una Super Potion y dinero 19791.
Repetición `--phase r03-rival`: PASS (`build/t27-natural-rival119-replay.log`).
Continue de ese checkpoint también PASS (`build/t27-fly-reload.log`).

Se volvió a curar en el instituto y se puso a Swampert de líder por el menú.
En Fortree se usó el Centro y se probó el obstáculo invisible desde (25,7),
mirando hacia abajo: permanecía bloqueado sin el Scope (291448). Las casillas
(24,8)/(26,8) son paredes; no sirven como aproximación. Se compraron seis
Hyper Potions y cuatro Super Potions por 10000 de dinero real. En Route120,
Steven se aborda desde (14,15), mirando a la izquierda; tras el combate real
contra Kecleon entrega Devon Scope. `r03-devon-scope` (318996); luego se cruza
el puente hasta (11,15), se vuelve a Fortree y se usa el objeto desde (25,7).
0x127 pasa a 1 y se puede pisar (25,8). `r03-fortree-cleared` (326384) tiene
equipo 40/25/18/25, seis Hyper Potions, cinco Super Potions y Devon Scope=1.
Continue verifica esos nuevos campos y el resto del manifiesto: PASS
(`build/t27-fortree-cleared-reload.log`).

`--phase r03-scope` repite obstáculo cerrado, entrega tras combate, puente,
desaparición de Kecleon y entrada al gimnasio: PASS, sin señales y salida
normal (`build/t27-natural-scope-replay.log`). Pelipper aprendió Fly por
mochila en `r03-fly-learned` (334128). El uso de Fly por el menú Pokémon
presentó el rechazo de nueva medalla con FLAG_BADGE06_GET=0; se cerró el menú
sin cambiar mapa/coordenadas. `--phase r03-fly-gate`: PASS
(`build/t27-natural-fly-gate-replay.log`), captura privada del mensaje en
`build/natural-campaign-replay-r03-fly-gate/r03-fly-denied.png`.

### Puertas giratorias de Fortree y primer intento de Alana

La ruta ordinaria de casillas se detuvo en una puerta que no podía girar en
la dirección propuesta. `rotating_gate_driver.py` busca en posición más las
ocho orientaciones; lee configuración/tablas del proceso local, sin copiarlas
al repo ni escribirlas en el juego. Compara la predicción con consultas
nativas de CanRotate y verifica las orientaciones cuando el paso se completa.
Una pulsación ignorada durante una transición se resuelve esperando y
replanificando; no se altera la animación ni la colisión.

El recorrido real llegó al líder en (15,3), `r03-winona-ready` (396924), equipo
41/27/19/25, dos Hyper Potions y cinco Super Potions. La repetición independiente
`--phase r03-gates` parte de la entrada, resuelve el puzzle y observa 14 llamadas
reales de RotatingGate_RotateInDirection mediante un breakpoint que nunca
detiene ni omite la función: PASS (`build/t27-natural-gates-replay.log`).

El primer combate con Alana se perdió normalmente: `r03-winona-result`
(451212), regreso a Fortree, sin señales del debugger. Sus cuatro primeros
Pokémon quedaron debilitados y Altaria permaneció con 102 HP. Se agotaron las
medicinas; equipo 41/28/19/25, dinero 7279. No cuenta como sexta medalla.
Se inicia un desvío a Lilycove para conseguir una MT de hielo mediante tienda;
R03 permanece abierto hasta verificar también el uso de Fly tras la medalla.

### Sexta medalla, MT consumibles y Vuelo real

El desvío atravesó Route120 y Route121 a pie. Cruzar (25,7) activó el diálogo
Aqua y retiró el grupo que bloqueaba el camino; Route121=1. No se alteraron
flags ni se usó Corte para omitir ese evento. En Lilycove se curó el equipo y
se derrotó al rival que bloqueaba el centro comercial. Dinero ganado: 18403.
En 4F se compraron dos TM14 por 11000, se enseñó Blizzard a Swampert y
Pelipper por mochila, y ambas MT se consumieron. En 2F se compraron seis
Hyper Potions por 7200; quedaron 203. Los contadores reales y sus cantidades
se comprueban en `--phase r03-tms`: PASS (`build/t27-natural-tms-replay.log`).
Continue de r03-winona-supplies también PASS.

Se regresó por Route121/120 a Fortree, se curó y se resolvieron de nuevo las
puertas del gimnasio. Alana fue derrotada normalmente: r03-winona-ice-result
(frame 649964), seis medallas, equipo 44/29/19/25, seis Hyper Potions intactas
y dinero 3503. `--phase r03-winona` repite la victoria desde el guardado de
entrada al combate: PASS (`build/t27-natural-winona-replay.log`).

La primera confirmación de Vuelo descubrió un callback de icono que usaba
sFlyMap tras liberarlo. GDB, causa y parche 0043 se describen en
first-run-report.md. Con el parche, `--phase r03-fly` confirma ida a Rustboro,
cancela otra selección sin moverse y vuelve a Fortree: PASS. El checkpoint
r03-fly-roundtrip se recarga por Continue, verificando seis medallas, equipo,
movimientos, eventos, cantidades y dinero sin reescribir el archivo: PASS.
Se continúa desde ese guardado, derivado del mismo linaje natural; la ruta
anterior y el save previo quedan preservados en build/natural-campaign.
R03 queda cubierto; R04–R15 y T27/Checkpoint E continúan abiertos.

### R04: Monte Pírico y Emblema Magma

Desde r03-fly-roundtrip se continuó por Continue en un nuevo proceso con el
binario corregido: vuelo real a Lilycove, Route121 a pie y Surf desde el muelle
(30,18), mirando al sur. La conexión lleva a Route122 (10,0); se rodea la isla
por agua y se entra por (22,29). r04-mtpyre-arrival, frame 28536, conserva el
mismo equipo y seis medallas. Se consumió una Hyper Potion en el trayecto.

La salida exterior en 1F usa MB_SOUTH_ARROW_WARP (0x65) en (3,6): se pisa la
flecha y se pulsa DOWN. Intentar llegar a (3,7), una pared, o salir mirando
LEFT/UP no funciona; fueron errores del recorrido, sin excepción del juego.
Desde el exterior se subió hasta (19,11), UP a la cima. Antes del evento:
MtPyre state=0, Emblema Magma=0, flags 0xD4/0x34F=0. El checkpoint
r04-pyre-summit-arrival (39084) conserva ese estado.

Se avanzó hasta (23,7), ganando los combates Aqua interceptados por sus
scripts. La secuencia de Archie y los ancianos dio el Emblema por diálogo:
r04-magma-emblem (64428), MtPyre state=1, objeto 375=1, flags 0xD4/0x34F=1,
equipo 44/30/19/25, seis medallas, cinco Hyper Potions y dinero 5983.
La captura privada r04-magma-emblem.png muestra a los ancianos y al jugador
en la cima con niebla; el grupo Aqua se ha retirado. Después se voló a
Lavaridge y se curó en el Centro: r04-lavaridge-emblem (70164).
Los siguientes escondites y el resto de R04 todavía no se consideran cubiertos.

`--phase r04-pyre` reproduce entrada, salida por flecha, subida exterior,
combates y entrega desde r04-mtpyre-arrival: PASS, sin señales y salida normal
(`build/t27-natural-pyre-replay.log`). Continue de r04-magma-emblem verifica
MtPyre/Jagged state, objeto, flags y el manifiesto completo sin reescribir el
archivo: PASS (`build/t27-magma-emblem-reload.log`). El registro del checkpoint
y su recarga incorporan ahora esas variables, flags y cantidad del Emblema.
La comprobación de sintaxis Python pasa. No cambia el código nativo desde las
21 suites/builds/compare verificados para 0043.

### Entrada Magma, Fuerza y plantas inferiores

Desde Lavaridge se recorrió Route112, se usó el teleférico por diálogo y se
bajó desde MtChimney. r04-jagged-emblem (77072) conserva Jagged state=1:
la comprobación de posesión del Emblema la hizo el script del mapa.
Cruzar (14,15) produjo la apertura real, state=2, y permitió entrar por
(16,18). r04-magma-arrival (79904) está en la entrada del escondite.

Al avanzar, las rocas se incorporan a gObjectEvents y cierran el corredor
que parecía transitable cuando estaban fuera de pantalla. Se activó Fuerza
desde (7,23), mirando a la izquierda; se empujó la roca central y, desde
(6,22), la de (5,22) hacia (4,22). Son pulsaciones y animaciones normales.
La primera repetición vio un encuentro salvaje consumir la pulsación del
segundo empuje. La prueba ahora lee la posición de la roca y reintenta con
un límite; no escribe coordenadas ni da por realizado un empuje omitido.
`--phase r04-magma-entry`: PASS, comprobando el script de apertura,
FLAG_SYS_USE_STRENGTH y la roca desplazada, luego la entrada a 2F_1R,
sin señales y con salida normal (`build/t27-natural-magma-entry-replay.log`).

r04-magma-2f (94780) conserva seis medallas, equipo 44/30/19/25, cinco Hyper
Potions y dinero 6563. Se recorrieron 2F_1R y 3F_1R con sus combates. La salida
(7,21) de 3F_1R también es una flecha al sur, no una escalera que se active
al pisarla. r04-magma-4f (134640) llega a 4F con Swampert 45, resto 30/19/25,
cinco Hyper Potions y dinero 10003. Groudon flag 0x6F y las variables de
Slateport/Harbor seguían en cero. Tatiano fue derrotado después;
HasTrainerBeenFought(732)=1, checkpoint r04-tabitha (163536), dinero 13063.
Maxie y el evento de Groudon aún no se acreditan en este incremento.

El helper warp_to consulta el comportamiento real de la casilla y pulsa
la dirección indicada por la flecha; cualquier destino inesperado falla.
Se verifica con las transiciones de Monte Pírico y entrada Magma, evitando
que una dirección asumida se confunda con un fallo del runtime.

### Maxie, Groudon y desbloqueo del puerto

r04-maxie-ready (169288) se guardó desde (15,21), mirando al NPC a la derecha.
No hay casilla transitable en (16,22); esa aproximación se descartó leyendo
la colisión, sin cambiar el mapa. Antes del diálogo: trainer 601 sin vencer,
Groudon flag 0x6F=0, Slateport city/harbor states=0. La secuencia del orbe,
el despertar/salida de Groudon y el combate terminaron normalmente:
outcome=1, trainer 601 vencido y los tres eventos pasaron a 1.
r04-maxie-result (188008) conserva equipo 46/30/19/25, seis medallas, cinco
Hyper Potions y dinero 16183. Continue verifica también Groudon y ambas
variables del puerto, sin reescribir el guardado: PASS
(`build/t27-maxie-result-reload.log`).

La repetición inicial mantenía pulsaciones A hasta el frame 8000 después de
Continue: al estar guardado frente al NPC, iniciaba el evento antes de las
precondiciones. La variante hasta 1450 todavía abrió el diálogo. Esas pruebas
no se acreditan. Para este checkpoint se cortan las pulsaciones en 1180;
el log verifica en 10000 campo desbloqueado, script terminado y eventos aún
a cero, antes de hablar. `--phase r04-maxie`: PASS con victoria, eventos,
guardado, ausencia de señales y salida normal
(`build/t27-natural-maxie-magma-replay.log`). No se omite el evento ni el combate.

La salida real usó 4F -> 3F_3R -> 2F_3R -> 1F. Las rocas vuelven a su posición
al recargar el mapa: desde (5,21), Fuerza y un empuje DOWN, luego desde (6,22)
un empuje RIGHT, abren el corredor de vuelta. r04-magma-exit (199136) queda
en JaggedPass (16,19), con progreso conservado. Se continúa para comprobar
el bloqueo Aqua antes del robo del submarino; ese evento y el resto de R04
siguen pendientes. Continue de r04-magma-2f también PASS
(`build/t27-magma-2f-reload.log`).

### Robo del submarino y bloqueo Aqua antes/después

Antes del robo se voló a Lilycove, se curó en su Centro y se activó Surf desde
(61,12), mirando RIGHT. La cueva se aborda desde (70,6), UP.
r04-aqua-gate-ready conserva Harbor=1 y los flags 0x61/0x335/0x336 a cero.
Se habló con ambos reclutas desde (13,12)/(14,12) y se mantuvo UP: ninguna
entrada permitió cruzar su fila. r04-aqua-blocked (214628) verifica el rechazo
físico, no solo la lectura de flags. `--phase r04-aqua-gate`: PASS, sin señales
y con salida normal (`build/t27-natural-aqua-gate-replay.log`).

Se volvió a Surf desde (13,12) mirando DOWN y se salió por la flecha acuática
(13,27). Tras volar a Slateport se guardó r04-slateport-harbor-ready (219128).
La entrevista debe abordarse desde (27,13), RIGHT: Gabby ocupa (28,14), Ty
(29,13) y la puerta impide entrar por (28,12). Hablar por la izquierda hizo
que el evento llevara al jugador al puerto y avanzara City=2. Caminar hasta
(8,13) activó la escena de Archie/submarino; Harbor=2, flags 0x61/0x335/0x336=1.
r04-submarine-theft (228712) guarda equipo 46/30/19/25, seis medallas, cinco
Hyper Potions y dinero 16183. Continue verifica eventos/variables y todo el
manifiesto sin cambiar el archivo: PASS (`build/t27-submarine-theft-reload.log`).

Se salió del puerto por (11,14), se voló de nuevo a Lilycove y se repitió la
entrada por Surf. El jugador cruzó la misma fila antes cerrada hasta (13,10),
r04-aqua-opened (235776). `--phase r04-harbor` reproduce desde la ciudad la
entrevista, el robo, salida/vuelo/Surf y el cruce abierto: PASS, sin señales y
con salida normal (`build/t27-natural-harbor-replay.log`). No se alteran flags
ni coordenadas por GDB. Quedan pendientes el interior Aqua/Matt y los tramos
posteriores de R04; se continúa desde esa entrada abierta.

### Paneles Aqua y Master Ball por recogida real

r04-aqua-b1f (237344) está en (29,2), después de la escalera de 1F. Los paneles
con MB 0x67 pueden mover al jugador dentro del mismo mapa; el recorrido de
casillas ahora los evita salvo cuando son el objetivo. aqua_warp_driver lee
los destinos de los JSON ignorados, se aproxima por una casilla vecina y pisa
el panel mediante input. Comprueba mapa y coordenadas exactas del destino.
Para volver por el panel actual sale primero a una casilla libre y vuelve a
entrar; no escribe posiciones ni llama al warp del juego.

Se verificó el ramal 4 -> 7 y el retorno por 7 -> 4, luego el panel 5 hasta
(3,15). Desde allí: 9,13,17,19,22 llevan por el puzzle a (23,10), comprobando
cada destino. Las dos bolas de objetos de la columna izquierda se recogieron
desde (15,11) y (15,10), mirando arriba: primero Nugget y luego Master Ball.
Las dos de la derecha son Electrode y no se activaron. La cantidad de Master
Ball pasó de cero a uno y su bandera 0x464 a uno. r04-master-ball (246564),
y r04-master-ball-verified (247596), conservan seis medallas, equipo
46/30/19/25, cinco Hyper Potions y dinero 16183.

`--phase r04-master-ball` repite desde la entrada B1F el ramal de ida/vuelta,
el puzzle y las recogidas: PASS, sin señales y salida normal
(`build/t27-natural-master-ball-replay.log`). Continue de la versión verificada
comprueba cantidad y bandera, además del manifiesto completo, sin reescribir
el archivo: PASS (`build/t27-master-ball-reload.log`). Python compila los
helpers de prueba. El camino de vuelta por 11,24,20,18,14,12,10 y sus combates
llevó a (20,4); la campaña continúa hacia Matías, aún sin acreditar el cierre
del escondite ni el resto de R04.


### Mat�as y salida al mar

Desde la sala de la Master Ball se volvi� por los paneles 11,24,20,18,14,12,10.
En B1F (20,4), escalera (18,1) a B2F; panel 3 a (5,8), escalera (3,3) a B1F,
escalera (12,1) a B2F y panel 4 a (31,17). Los encuentros de entrenadores se
resolvieron mediante sus combates. `--phase r04-aqua-route` repite ese trayecto
completo desde el guardado de la Master Ball: PASS, sin se�ales y salida
normal (`build/t27-natural-aqua-route-replay.log`).

Mat�as se aborda desde (24,19), mirando LEFT; las otras tres casillas vecinas
no son transitables. r04-matt-ready (281144) est� dos casillas a su derecha,
(25,19), para que las pulsaciones de Continue no abran su di�logo. Trainer 30,
flag 0x70 y flag 0x354 segu�an a cero. Victoria y salida del submarino reales:
r04-matt-result (290600), outcome=1, trainer 30 vencido, ambos flags a uno,
equipo 47/30/19/25, seis medallas, cinco Hyper Potions, Master Ball=1 y dinero
20703. `--phase r04-matt`: PASS (`build/t27-natural-matt-replay.log`). Continue
verifica los nuevos flags y el manifiesto completo sin modificar el archivo:
PASS (`build/t27-matt-result-reload.log`).

La barrera Wailmer se comprob� con una copia del guardado anterior al robo:
`--phase r04-wailmer-gate` sale por Surf y mantiene RIGHT desde (75,12), sin
poder entrar en (76,12), con 0x70=0: PASS, sin se�ales y salida normal
(`build/t27-natural-wailmer-gate-replay.log`). En la campa�a tras Mat�as:
salida B2F (32,20) a B1F, escalera (29,1) a 1F, Surf desde (13,12) hacia DOWN,
y salida acu�tica (13,27). Con 0x70=1 se cruz� de (75,12) a (76,12) en Lilycove.
r04-wailmer-opened (294420) conserva ese desbloqueo y todo el equipo.
Aqua queda cubierto; Mossdeep/Space Center y los dem�s tramos de R04 contin�an
pendientes. La campa�a hace una visita real a Devon por el Exp. Share todav�a
no recogido tras entregar la carta, antes de seguir por Route124.


### Repartir Exp. y objetos equipados conservados

Antes de cruzar Route124 se vol� a Rustboro y se volvi� a Devon por sus
escaleras. r04-devon-exp-share-ready (299904) conserva la carta entregada
(0xBD=1), recompensa pendiente (0x110=0) y cantidad de Exp. Share=0.
Hablar desde (14,5), RIGHT, interact�a con el proxy del presidente tras la mesa;
el NPC entreg� el objeto 182 y activ� 0x110. r04-exp-share (303392).

La mochila permiti� elegir Give y Pelipper: cantidad 182 pas� de 1 a 0 y su
objeto equipado pas� de 0 a 182. r04-exp-share-equipped (306188) conserva
ese estado, equipo 47/30/19/25, seis medallas, Master Ball=1, cinco Hyper
Potions y dinero 20703. El Mystic Water que tra�a Castform sigue equipado
(objeto 209); los dem�s no llevan objetos. El manifiesto y Continue verifican
ahora tambi�n held_item por Pok�mon y el inventario de Exp. Share.
`--phase r04-exp-share` repite entrega y equipamiento por UI: PASS, sin se�ales
y salida normal (`build/t27-natural-exp-share-replay.log`). Continue conserva
objetos, recompensa y resto del manifiesto sin reescribir el archivo: PASS
(`build/t27-exp-share-reload.log`).

El helper give_item solo admite Items-pocket y un destino sin objeto equipado;
comprueba consumo y resultado, y falla con un l�mite si no vuelve al campo.
La campa�a sali� por las escaleras, vol� a Lilycove, cur� en su Centro y us�
Surf. r04-route124 (316512) est� en Route124 (1,22); se contin�a hacia Mossdeep
con el objeto equipado para los combates normales.


### Velocidad medida de Surf y llegada a Mossdeep

El primer recorrido Route124 termin� en un islote, (71,44), al intentar llegar
a una conexi�n prevista desde el agua. No fue una excepci�n del juego:
el avatar hab�a desembarcado. El controlador de teclas agrupaba Surf como si
fuera marcha normal, usando 16 frames por casilla. PlayerNotOnBikeMoving usa
PlayerWalkFast durante Surf (8), frente a PlayerWalkNormal (16) a pie.
Se corrigi� �nicamente el c�lculo de las pulsaciones del harness.

La prueba `--phase r03-surf-speed` parte del guardado natural de Petalburg.
Una pulsaci�n anterior de 36 frames para tres casillas movi� de (6,20) a (2,20):
cuatro casillas, manteniendo Surf. Con el controlador corregido el recorrido
llega exactamente a (3,20), vuelve a (6,20), mantiene Surf en ambos puntos y
sale a tierra en (7,20): PASS, sin se�ales y con salida normal
(`build/t27-natural-surf-speed-replay.log`). No se cambian movimiento ni
velocidad del juego; los datos son posiciones medidas por el proceso.

En la campa�a se reanud� Surf mirando UP desde el islote; la misma conexi�n
con pulsaciones corregidas lleg� a Mossdeep. Se cur� en el Centro y se guard�
r04-mossdeep (348248), exterior (28,17), seis medallas, equipo 47/31/19/25,
Pelipper con Exp. Share, cuatro Hyper Potions, Master Ball=1 y dinero 21247.
El nivel de Pelipper aument� durante los combates reales de Route124.
ROM y save originales conservan sus hashes previos. Sigue pendiente el
puzzle/l�der de Mossdeep y el resto de R04�R15.

### Transporte compartido y primera sala de Mossdeep

El helper propio de pads se renombra de aqua_warp_driver.py a
map_warp_driver.py: conserva Aqua (comportamiento 0x67) y admite los pads
0x0E de Mossdeep. Lee origen/destino de los JSON locales, entra por teclas y
exige el destino exacto; no llama a funciones de warp ni escribe coordenadas.
La repeticion completa de la Master Ball con el nuevo modulo da PASS, sin
senales y con salida normal (`build/t27-natural-map-pad-regression.log`).

El buscador evita pads intermedios y, en Mossdeep, interruptores intermedios:
los giros se solicitan como destinos explicitos. Desde r04-mossdeep-gym-entry
(350076), las pulsaciones sobre (3,30) y (2,21) ejecutaron dos llamadas reales
a MoveRotatingTileObjects, observadas sin detener ni omitir la funcion. El
pad 2 llevo a (1,23) y el pad 4 a (8,12), ambos en el mismo mapa y con los
destinos previstos. Los combates dobles de las salas se resolvieron normalmente.
Se guardo r04-mossdeep-blue-room (369384), seis medallas y equipo 47/32/19/25,
Pelipper aun con Exp. Share. El puzzle y los lideres siguen pendientes; estas
comprobaciones no cierran Mossdeep ni R04.

### Sala azul/roja repetida y transporte inferior

La secuencia reducida medida desde (8,12) es: tres pulsaciones sobre (8,10),
tres sobre (8,6), cuatro sobre (6,7) y una sobre (8,10). Los pasos intermedios
se hacen fuera del interruptor antes de volver a pisarlo; no se cambian las
plantillas de objetos. Abre el corredor hacia el pad 10, que lleva a (11,35).
El recorrido exploratorio original incluyo mas giros, conservados en el log;
la repeticion usa solo la secuencia reducida y conserva combates reales.

`--phase r04-mossdeep-blue`: PASS, sin senales y con salida normal
(`build/t27-natural-mossdeep-blue-replay.log`); checkpoint de repeticion en
frame 31524, equipo 47/33/19/25. La campana principal guarda el mismo destino
como r04-mossdeep-green-room (401356). Continue conserva mapa, coordenadas,
equipo, objetos, seis medallas, eventos y dinero sin modificar el archivo:
PASS (`build/t27-mossdeep-green-reload.log`). Esta recarga no afirma validar
cada posicion de estatua: eso se comprueba al ejecutar las siguientes rutas.

El transporte inferior llega a un pasillo bloqueado por el grupo verde. Se
regreso por el pad 11, se piso (8,10), y se usaron los pads 5 y 6 para entrar
por la sala morada: r04-mossdeep-purple-room (404356), (23,20). No hubo una
excepcion nativa en estos recorridos; Mossdeep/R04 siguen abiertos.

### Puzzle completo de Mossdeep por pulsaciones

Desde r04-mossdeep-purple-room: (23,21) una vez, (23,24) dos veces y
(15,34) dos veces. El interruptor verde mueve tambien las plantillas que
estan fuera de pantalla: se leyeron sus coordenadas sin escribirlas. Con un
solo giro aun queda un callejon sin salida; con dos, el retorno inferior
permite (11,35) -> (12,35) -> (12,34) -> (13,34) -> (13,33) -> (13,32).
Para volver se pisa (23,21), pads 7 y 4, tres veces (8,10), pad 10 y pad 12.
Este ultimo llega a (21,10); (23,9) deja una casilla antes de hablar al lider.

La exploracion original tambien comprobo los pads 9/8 (atajo a la entrada),
y se conserva en route.jsonl. La ruta reducida no necesita ese rodeo.
`--phase r04-mossdeep-purple` inicial repitio el regreso al pasillo verde:
PASS (`build/t27-natural-mossdeep-purple-replay.log`). La prueba completa
actual `--phase r04-mossdeep-circuit` parte de r04-mossdeep-gym-entry,
recorre amarillo, azul/rojo, morado y verde, y llega a (23,9), frame 72312:
PASS, sin senales y con salida normal
(`build/t27-natural-mossdeep-circuit-replay.log`). Mantiene seis medallas;
no inicia ni acredita aun el combate contra los lideres. Equipo final de
esa repeticion 47/34/19/25, con combates reales y Exp. Share.

La campana principal llego por primera vez a (23,9) en frame 430864.
Pelipper estaba debilitado; se salio por los transportes, se curo en el
Centro (r04-mossdeep-rested, 439232) y se compraron doce Hyper Potions por
14400. El inventario paso de cuatro a dieciseis y el dinero de 35647 a 21247.
Se repitio el circuito tras volver a entrar; el guardado r04-mossdeep-battle-ready
(458548) precede al combate. Captura privada revisada:
`build/natural-campaign/r04-mossdeep-battle-ready.png`, sala y lideres visibles.
ROM/save originales mantienen sus hashes. No hay cambios al juego en este
incremento; R04 y las coberturas siguientes siguen abiertos.

### Septima medalla: victoria original, persistencia y derrota de repeticion

La campana principal vencio a Tate/Liza en su primer intento: outcome=1,
trainer 271=1 y badge 0x86D=1 en frame 493092. La recompensa activo tambien
FLAG_DEFEATED_MOSSDEEP_GYM (0x4F6), Calm Mind (0xAB), ciudad 0x405D=1 y
Centro Espacial 0x409F=1; antes del combate todos estaban a cero.
r04-mossdeep-win (495252) guarda (23,9), siete medallas, equipo 48/34/21/25,
doce Hyper Potions, Master Ball=1 y dinero 29647. Continue valida ahora estos
campos nuevos ademas del manifiesto anterior: PASS, archivo sin cambios
(`build/t27-mossdeep-win-reload.log`).

La repeticion independiente NO repitio la victoria: outcome=2, retorno normal
al exterior del Centro de Mossdeep (28,17), sin senal. Se conserva el fallo
de la expectativa de victoria en `build/t27-natural-mossdeep-leaders-replay.log`
y su campaign.log. Una primera comprobacion de derrota esperaba por error el
interior del Centro; el ultimo route.jsonl mostro el exterior y se corrigio
solo la asercion del harness. Su log queda como loss-incorrect-map-expectation.log.

`--phase r04-mossdeep-leaders-loss` verifica explicitamente ESA derrota:
ninguna medalla/recompensa/trainer/evento concedido, equipo curado y guardado
por UI. PASS, sin senales, salida normal
(`build/t27-natural-mossdeep-leaders-loss-replay.log`). La expectativa de
victoria permanece separada en --phase r04-mossdeep-leaders y no se acredita
como PASS. No se alteraron RNG, equipo, dano ni resultado de combate. La
linea principal continua desde su victoria real; R04 sigue abierto.

### Centro Espacial y entrega real de Buceo

Tras la medalla se uso el transporte de retorno propio del gimnasio (21,6):
script normal hacia (7,30), salida a ciudad y curacion en el Centro. La marcha
hacia (42,24) activa los reclutas que bloqueaban el acceso oriental: ciudad
pasa de 1 a 2. r04-space-center-entry conserva el primer piso y estado de
Centro Espacial=1. Hablar al guardia desde (13,3), UP, vence al trainer 116,
lo aparta (0x409E=2) y permite subir por (13,1). Arriba se derrotan los tres
reclutas consecutivos 588/589/590, estado 0x409F=2.
`--phase r04-space-upper`: PASS, sin senales y salida normal
(`build/t27-natural-space-upper-replay.log`).

La primera conversacion con Steven activa 0xCD. r04-steven-ready (535144)
guarda (3,8), antes de aceptar el combate. En el menu real se eligieron los
slots 0/1/3: gSelectedOrderFromParty=[1,2,4,0,0,0], seguido de Confirm.
Se vence junto a Steven: outcome=1, flag 0x75=1, ciudad y Centro=3, casa de
Steven (0x40C6)=1. El juego restaura el equipo original de cuatro Pokemon,
retirando el equipo temporal del companero. r04-steven-result (566152),
equipo 48/35/21/25, once Hyper Potions, Master Ball=1, dinero 38567.
`--phase r04-steven`: PASS, sin senales, salida normal
(`build/t27-natural-steven-replay.log`). Captura privada del menu de seleccion:
`build/natural-campaign/r04-steven-party.png`.

Al salir y entrar a la casa (19,11), UP, el script entrega HM08: 0x7B pasa
de 0 a 1, cantidad 346 de 0 a 1 y casa de 1 a 2. El learnset original rechaza
Pelipper; el chequeo previo del harness lo detecto sin abrir la mochila.
Se uso Swampert, sustituyendo Blizzard por Dive (291) mediante la UI; sus
movimientos ahora son Rock Smash, Dive, Strength y Surf. HM08 conserva cantidad 1.
`--phase r04-dive-gift`: PASS, sin senales y salida normal
(`build/t27-natural-dive-gift-replay.log`).

r04-dive-verified (579212), casa (3,7), registra tambien los flags 0x75/0xCD/0x7B
y la variable de la casa. Continue conserva esos eventos, siete medallas,
HM08, movimientos, objetos equipados y dinero, sin modificar el archivo:
PASS (`build/t27-dive-verified-reload.log`). R04 sigue abierto: falta usar
Buceo, Seafloor, Sky Pillar/Rayquaza, Sootopolis y la octava medalla.

### Buceo real y siguiente cierre diagnosticado

Desde la casa se salio por el warp real (3,7), se camino a (25,30), DOWN,
y se acepto Surf. Las conexiones llevaron a Route127 y Route128; guardado
r04-route128-dive (583712), (25,0). En Route128 (38,27), el menu de Swampert
DIVE lleva a Underwater_Route128 (38,27); r04-underwater128 (586660).
La puerta submarina se entra con UP desde ahi; su casilla de warp tiene
colision y no debe tratarse como una escalera caminable.

Emerger revelo un puntero NULL a conexiones del mapa. El parche 0044 permite
el warp fijo original; --phase r04-seafloor-dive da PASS hasta la superficie
en SeafloorCavern_Entrance (10,17), con guardado por UI y sin senales.
Builds host, 21 suites, GBA compare y reproduccion del parche: PASS.
Detalle del fallo, registros y logs en first-run-report.md.

Al reiniciar la campana desde el save submarino se encontro otra lectura
NULL en LoadSaveblockObjEventScripts. Sigue pendiente corregir/verificar
Continue submarino (0045); no se salta la funcion ni se altera la partida.

### Continue submarino corregido sin sustituir la partida

El parche 0045 corrige la restauracion de scripts de objetos descrita en
first-run-report.md. El guardado r04-underwater128 original se recarga con
control de campo en frame 10000, mismas coordenadas (38,27), equipo, medallas,
movimientos, eventos, inventario y dinero. No se modifica el archivo:
PASS (t27-underwater-reload-after-fix.log). El guardado de victoria de Mossdeep,
con objetos de mapa, tambien conserva su manifiesto: PASS.
Host, 21 suites, GBA compare y reproduccion de 0045 en checkout limpio: PASS.
La linea principal reanuda ese mismo save submarino con el nuevo binario;
los dos procesos detenidos por las excepciones quedan documentados en sus logs.

### Seafloor: primeras dos salas y empujes observados

Tras Continue con 0045, la campana vuelve a emerger y guarda
r04-seafloor-entry (12652), Entrance (10,17), y r04-seafloor-room1 (15552),
(5,18). Estos frames pertenecen al nuevo proceso iniciado en 10000.

La primera maniobra exploratoria empujo el bloque izquierdo hacia el este,
cerrando el corredor. Se salio normalmente a Entrance y se volvio a entrar
para reiniciar el puzzle. La ruta correcta rompe la roca desde (4,10), RIGHT;
activa Fuerza desde (5,12), UP; empuja el bloque 1 una vez UP a (5,10), y el
bloque 2 una vez RIGHT desde (11,11) a (13,11). El paso norte lleva a Room2
(10,7): r04-seafloor-room2 (24960). --phase r04-seafloor-first-room: PASS,
sin senales y salida normal (t27-seafloor-first-room-replay.log).

Room2: Golpe Roca desde (9,7), LEFT; Fuerza desde (4,6), UP; tres empujes del
bloque 4 hasta (4,2). El paso (6,1) lleva a Room6 (11,21), guardado
r04-seafloor-currents-entry (30516). --phase r04-seafloor-second-room: PASS,
sin senales y salida normal (t27-seafloor-second-room-replay.log).
Un intento exploratorio de seguir empujando el bloque 5 hacia (7,2) fue
rechazado por una pared; el helper termino con un limite explicito. La ruta
repetida no necesita tocar ese bloque. No fue un bloqueo del juego.

El helper propio push comprueba la casilla del jugador, el ID y las coordenadas
del bloque antes/despues de cada pulsacion; solo reintenta una tecla ignorada,
con un limite de cuatro. No llama rutinas de movimiento ni escribe objetos.
Estos recorridos tambien ejercitan los scripts restaurados por Continue en
mapas con objetos despues de 0045. R04 y las salas posteriores siguen abiertos.

### Corrientes originales hasta la sala de Shelly

En Room6 se acepto Surf desde (11,20), UP. Cuatro pulsaciones medidas siguen
las flechas originales: UP termina en (14,16), RIGHT en (19,11), RIGHT en
(8,12), LEFT en (4,8). Se comprueba cada destino y se deja terminar el arrastre;
solo se repite una tecla si el jugador permanece en su origen, con limite.
Desde ahi se camina a (4,2), se desembarca y se entra por UP a Room3 (4,15).
r04-seafloor-shelly-entry (40080). --phase r04-seafloor-currents: PASS,
sin senales y salida normal (t27-seafloor-currents-replay.log).
La planificacion leyo los metatiles/flechas; la ejecucion solo envio teclas.
La ruta repetida reduce los pasos ordinarios finales usando go; conserva
las cuatro comprobaciones de arrastre. Sigue pendiente el evento final de Seafloor.

### Shelly, ultimo puzzle de Fuerza y Kyogre

La ruta desde Room3 (4,15) intercepta a Shelly al avanzar hacia (9,4).
Trainer 33 queda derrotado; el acceso (8,1) lleva a Room8 (5,12).
r04-seafloor-final-puzzle-entry (60436), equipo 48/36/21/25.
--phase r04-seafloor-shelly: PASS (t27-seafloor-shelly-replay.log).

Room8 se resuelve con nueve empujes, comprobando ID/posicion en cada paso:
1 UP desde (4,8), 3 UP desde (6,8), 2 LEFT desde (6,7), 7 UP desde (5,6),
6 LEFT, 10 UP, luego desde (5,5) 8 RIGHT, 11 UP y 7 LEFT. La salida (5,2)
lleva a Room9 (5,4), r04-seafloor-archie-entry (67736).
--phase r04-seafloor-final-puzzle: PASS (t27-seafloor-final-puzzle-replay.log).
La roca se mueve solo por Fuerza/teclas; no se escriben objetos ni coordenadas.

Se recogio TM26/Earthquake (314), desde (13,5), RIGHT: cantidad 1. La plataforma
alta (17,40) es inaccesible y no es el disparador; se guardo antes del evento
en el corredor inferior (15,42), r04-archie-ready (71240). Entrar por teclas
a (17,42) inicia la escena y combate contra Archie (trainer 34): victoria,
orb, despertar/salida de Kyogre, dialogo de Maxie y retorno original a Route128.
Tras el dialogo exterior, Route128=2, Seafloor=1, Sootopolis=1; flags 0x81/0x53=1,
trainer 34=1. Antes de entrar estaban todos a cero.
--phase r04-archie: PASS, sin senales y con salida normal (t27-archie-replay.log).
Las otras dos repeticiones tambien terminan sin senales y normalmente.

r04-kyogre-verified (107400), Route128 (38,22): siete medallas, equipo 49/37/21/25,
diez Hyper Potions, Master Ball=1, Earthquake=1, HM08=1 y dinero 44187.
Se añadieron esos eventos/variables y TM26 al manifiesto. Continue conserva
el estado completo sin modificar el archivo: PASS (t27-kyogre-verified-reload.log).
La campana principal cerro limpiamente y reabrio el MISMO save con el renderer
corregido para continuar. R04 sigue abierto para Sky Pillar/Rayquaza, Sootopolis
y la octava medalla; R05-R15 tampoco estan cerrados.

### R04: llegada natural a Sootopolis y dos correcciones host

Tras Surf y Dive desde Route126 se alcanza Underwater_SootopolisCity y el
warp fijo emerge en Sootopolis (29,53). Se corrigieron la camara sin plantilla
(0046) y la espera DMA de la escena abreviada (0047); causas y registros en
first-run-report.md. --phase r04-sootopolis-entry PASS, dos camaras observadas,
ninguna activa al devolver el control, ciudad=2. Campana principal y replay:
r04-sootopolis-arrival (19488), siete medallas, mismo equipo y dinero 44187.
El resto de R04 sigue abierto, incluidos los cuatro segmentos restantes de
la escena completa de Rayquaza. No hay push.

El manifiesto space_center_defeated=0 tras el viaje no indica perdida de
progreso: RivalRayquazaCall, SpaceCenter_2F/scripts.inc, consume el flag 0x75
al terminar la llamada Pokenav de May/Brendan. Los estados permanentes de
Mossdeep/Centro Espacial continuan en 3. No se vuelve a establecer el flag.

Continue de r04-sootopolis-arrival PASS, archivo sin modificar
(t27-sootopolis-arrival-reload-short.log). La prueba anterior pulsaba A hasta
8000 y activaba Buceo desde el campo ya cargado, terminando submarino: fue
una accion involuntaria del harness, no perdida de guardado. El reloader
permite --continue-until 1181 para cortar pulsos antes del control de campo;
las demas comprobaciones completas y los 10000 frames siguen iguales.

### R04: Steven y Wallace autorizan Sky Pillar por dialogo real

Desde la llegada se habla con Steven desde (20,37), UP. Su caminata original
lleva a CaveOfOrigin_Entrance (9,20). Las escaleras (9,5) y (14,5) llevan al
sotano; (9,12) es una pared, por lo que se rodea hasta (8,13), RIGHT.
Se elige la opcion 2/Sky Pillar del multichoice nativo de Wallace, sin escribir
VAR_RESULT. Flag 0x133=1, flag 0x137=1 y Sootopolis=3. Campana principal:
r04-wallace-sky-pillar (48216). --phase r04-wallace PASS desde el save anterior,
con guardado real y salida normal (t27-wallace-replay.log).
El manifiesto incorpora ambos flags y VAR_SKY_PILLAR_STATE para los futuros
checkpoints. Captura privada muestra la cueva, terreno y niebla horizontal.
No aparecio excepcion en este tramo. R04 sigue abierto.
Continue de r04-wallace-sky-pillar PASS, archivo sin modificar
(t27-wallace-reload.log). setup.ps1 tambien termina idempotente con 47 parches
(t27-setup-47-idempotent.log). ROM y save originales conservan sus hashes.

### R04: Sky Pillar y Rayquaza completos hasta el regreso de la paz

Viaje natural por Route127 -> 128 -> 129 -> 130 -> 131, con combates originales
por el camino; r04-route131-entry (95340), equipo 49/38/21/25 y dinero 46571.
Desde (36,7), UP entra a SkyPillar_Entrance; escalera (14,4) inicia el evento
original de Wallace/terremotos. Ciudad=4, r04-sky-pillar-open (102020).
--phase r04-sky-open PASS. Primera subida por los layouts de historia,
sin Mach Bike ni modificacion de tiles: 1F(10,1), 2F(3,1), 3F(11,1).
En 4F la escalera occidental esta aislada. Caminar hacia (7,4) pisa el suelo
agrietado de (6,4) y cae realmente a 3F (6,4). Desde el compartimento central,
escalera (7,1), 4F(3,1) y 5F(10,1) llevan a la cima. No se fuerza el warp.
--phase r04-sky-climb PASS, incluido el agujero original.

r04-rayquaza-ready se guarda antes del disparador; caminar a (14,9) despierta
al legendario y usa las camaras de 0046. Ciudad=5 y SkyPillar=1;
r04-rayquaza-awakened (113464). --phase r04-rayquaza-awaken PASS.
Fly por menu a Sootopolis ejecuta los cinco loaders de la escena completa,
exactamente una vez cada uno; las cinco esperas de 0047 devuelven control.
--phase r04-rayquaza-peace PASS con cinco capturas de frames visibles.
r04-sootopolis-peace (120352), (43,32), SkyPillar=3 y flag0x53=0.
Continue valida todo el manifiesto y deja el archivo igual: PASS.
No hay nueva excepcion. La entrega de Waterfall y octava medalla siguen
pendientes. R04-R15 y T27 permanecen abiertos.

### R04/R05: regalo de Waterfall y rompecabezas de hielo por teclas

Tras Fly a Sootopolis se cura realmente en el Centro Pokemon; desde la orilla
(40,38), LEFT activa Surf y cruza a la isla central. Hablar con Maxie desde
(33,36), UP, y Archie desde (34,36), UP, activa flag0x9e y el warp silencioso
original a (31,34). Wallace entrega HM07/Waterfall: item345 pasa 0->1 y flag138
0->1. r04-waterfall-gift (131008). Entrar por (31,33), UP lleva al gimnasio;
r04-sootopolis-gym-entry (132436). --phase r04-waterfall-gift PASS, incluida la
curacion, Surf, despedida de ambos equipos, regalo, entrada y guardados reales.
No se ha ensenado ni usado Waterfall todavia.

El driver propio lee el hielo fino (behavior26) y colision para calcular un
camino que visite una vez cada casilla. Los tres tableros tienen 7/19/38
casillas. Solo se emiten teclas a casillas adyacentes y se verifica su conversion
a hielo agrietado (27), sin escribir tiles/variables. Una pulsacion corta puede
solo girar al jugador: se reintenta un maximo de cuatro veces exclusivamente
si las coordenadas no cambiaron. Los umbrales nativos de VAR_ICE_STEP_COUNT
(4022) acaban en 9,29,68 al abrir cada escalera por su script original.
La campana llega a Juan (8,3), r04-juan-ready (139908).
--phase r04-sootopolis-ice PASS desde la entrada intacta: los tres tableros,
guardado por menu y salida normal (t27-sootopolis-ice-replay.log).
Captura privada r04-juan-ready.png muestra a Juan y el acceso despejado.
El combate y la octava medalla aun no se declaran verificados.

### R04: Juan, dos derrotas reales y victoria tras preparacion por UI

El primer intento solo con HMs pierde contra Kingdra: outcome2, regreso original
al Centro de Sootopolis (43,32), siete medallas, sin trainer272 ni recompensas.
r04-juan-loss (235332), Continue PASS sin modificar archivo (t27-juan-loss-reload.log).
Se conserva la entrada anterior como r04-juan-hms-ready; no se acredita victoria
al replay de ese equipo. GDB interrumpio voluntariamente la batalla para leer
el turno27/PP/estadisticas; se continuo desde el mismo checkpoint host, sin
saltar funciones nativas ni cambiar la partida. No era un bloqueo.

Se volo a Lilycove y se uso el Quita-Movimientos real para borrar Dive del slot1
de Swampert. Movimientos 249/291/70/57 -> 249/70/57/0; la MT26 de Seafloor (314)
se consumio 1->0 y enseno Earthquake89. r04-earthquake-learned (243392).
--phase r04-earthquake-prep PASS desde el guardado de derrota, incluida la
seleccion de Pokemon/movimiento, confirmacion, bolsa, aprendizaje y guardado.
Tras comprar siete Hyper Potions, curar y repetir el hielo, r04-juan-earthquake-ready.
Ese segundo intento tambien pierde; tampoco se acredita victoria al replay.
r04-juan-earthquake-loss (352336): equipo 50/39/21/25, siete medallas, ciudad5,
sin trainer/recompensas de Juan; dinero7442 y Hyper Potions0. Se conservan los
logs de ambos intentos (t27-juan-replay.log y t27-juan-earthquake-replay.log).
Son derrotas normales, no excepciones del port.

La tienda original de Lilycove vende cuatro Hyper Potions, dos X Attack75,
un X Speed77 y un X Accuracy78 por 7100 en total; quedan342. --phase r04-tactical-shop
PASS comprueba todas las compras por menus y guardado (t27-tactical-shop-replay.log).
Se vuelve por Fly, cura y tres tableros de hielo hasta r04-juan-tactical-ready.
La estrategia nueva acepta el cambio opcional tras Luvdisc, saca a Pelipper y
vuelve a Swampert desde el menu Pokemon: se observan sus ocho etapas en6,
restablecidas por el motor. Usa dos X Attack y un X Speed desde la bolsa real.
No escribe etapas, PS, PP ni resultados. La primera version del guion pulsaba
UP mientras aun estaba el anuncio anterior al cursor Yes/No; se corrigio para
cerrar el anuncio con A. Se reinicio desde el MISMO archivo de guardado previo,
cuya igualdad se comprobo byte a byte. No fue un bloqueo del juego.

Con esa secuencia, campana y --phase r04-juan-tactical ganan: outcome1,
trainer272=1, ocho medallas, flag4F7/AC=1, ciudad6 y Water Pulse291=1.
R04-juan-win (35464, nuevo proceso): equipo 50/40/21/25, dinero4942, cuatro
Hyper Potions intactas; XAttack/XSpeed pasan2/1->0/0 y XAccuracy sigue1.
El replay exige esas postcondiciones y sale normalmente (t27-juan-tactical-replay.log).
Las fases publicas de victoria usan esta estrategia comprobada; las dos pruebas
anteriores fallidas se conservan como evidencia privada de intentos perdidos.
Continue de r04-juan-win PASS, con equipo/movimientos, ocho medallas,
recompensas, flags, variables, consumibles y dinero intactos; el archivo no
se reescribe (t27-juan-win-reload.log). R04 queda cubierto. T27/Checkpoint E
siguen abiertos para R05-R15, incluida la Liga y las actividades posteriores.

### R05: captura real, HM07 aprendido y ascenso original de Waterfall

Tras salir del gimnasio cayendo al sotano por hielo agrietado, se toma la
escalera (11,22) y se sale al exterior; los entrenadores del gimnasio ya estan
resueltos por el script de la medalla. Fly a Dewford: r05-dewford-entry (40236).
En Mossdeep se compran tres Ultra Balls por3600 (la tienda no ofrece Great
Balls), se cura y se vuelve por Fly. --phase r05-ball-supplies PASS.
Se anade CATCH_BALL al driver: por defecto Poke Ball4, eleccion explicita del
stack y rechazo si se agota; nunca cambia a otra Ball automaticamente.
La regresion de captura R02 Wingull pasa y sale normalmente con esta politica
(t27-explicit-ball-wingull-regression.log, log GDB completo).

Desde el agua de Dewford (13,9), RIGHT, se patrulla (16/18,8) por teclas para
un encuentro de Tentacool72. Captura natural con Ultra Ball2: party4->5,
MasterBall1 y PokeBalls4 intactas. Nivel18, sin construir Pokemon ni cambiar
sus datos. r05-tentacool-caught (60668). Se ensena Waterfall127 desde HM07/345,
que permanece en la bolsa; r05-waterfall-learned (63980).
--phase r05-waterfall-catch PASS y Continue del aprendido PASS, archivo intacto
(t27-waterfall-catch-replay.log, t27-waterfall-learned-reload.log).

Gloom aprende Flash148 por HM05/343; r05-hm-team-ready (68516). Fly a Mossdeep,
Surf y conexiones Route127 ->128 -> EverGrandeCity, con combates originales:
llegada (0,67), r05-ever-grande-waterfall-bottom (90432). El recorrido se
repite con --phase r05-road-trip. Para llegar al lado norte hay que usar el
movimiento: el planificador deja de considerar Waterfall13 como Surf normal.
Pisar esas casillas antes del efecto fuerza el deslizamiento hacia el sur;
se corrigio la aproximacion del guion, sin modificar el juego.

Se llega mirando al norte desde (18,69) a (18,68), y A/Yes inicia el efecto
original. FldEff_UseWaterfall se observa exactamente una vez con monId4
(Tentacool capturado). Termina en (18,59), Surf activo y control desbloqueado;
r05-waterfall-used (112836). Se cura en el Centro de Ever Grande y entra a
VictoryRoad_1F (15,40), r05-victory-road-entry (119168).
--phase r05-waterfall PASS, incluida observacion/ascenso/curacion/entrada/save
(t27-waterfall-use-replay.log). No aparecio una excepcion nativa nueva.
R05 sigue abierto para Wally, el resto de Calle Victoria, Liga y Hall of Fame.

## T27 R05: Wally y segundo sotano de Calle Victoria

Wally se derrota por combate original: trainer519, flag7E y Var40C3=2.
Replay r05-wally y Continue r05-wally-verified PASS. Se entra al primer sotano
por la escalera (9,14), no por una ruta inaccesible. Flash usa a Gloom desde
Party: FldEff_UseFlash una vez, flag888=1 y GetFlashLevel()=1 (radio ampliado,
no luminosidad completa). Replay r05-flash PASS; capturas antes/despues privadas.

Fuerza desplaza realmente las rocas locales3 (4,7)->(3,7) y4 (9,10)->(10,10).
Golpe Roca elimina el obstaculo10 en (18,12). Los replays r05-upper-boulders
y r05-smash-corridor pasan, verificando posiciones/ausencia de obstaculos.
La escalera (30,25) conduce al segundo sotano, con combates originales durante
el recorrido. r05-second-basement PASS y checkpoint r05-victory-road-b2f-entry.
Los manifiestos y Continue ahora incluyen Var40C3, FlashLevel y Ultra/Great Balls.

No ha aparecido otro fallo nativo en estos tramos. No se han escrito banderas,
posiciones, objetos ni equipo: solo teclas y guardados del juego. El build ARM
continua verificado con 0047 (sin cambios nativos posteriores). R05 sigue abierto:
faltan el resto de Calle Victoria, Liga, creditos y Hall of Fame. Sin push.

## T27 R05: salida de Calle Victoria y acceso real a Liga

B2F: Surf desde (33,17), cascada central (26,12)->(26,8), cruce al oeste
y bajada forzada original (8,10)->(8,14). La escalera (19,12) llega a B1F
(17,16). La escalera del este es una zona lateral: se comprobo sin forzar
warps y su replay separado tambien pasa. r05-cave-waterfalls PASS.

En B1F se rompen rocas11/12 y empuja roca5 al norte una vez; la escalera
(20,21) lleva a 1F(21,32). r05-central-puzzle PASS. La salida norte llega
a EverGrande(18,28): incluye el paso automatico tras la puerta, que faltaba
en la primera asercion del guion. El replay corregido r05-victory-exit PASS.
La enfermera de Liga se alcanza desde (3,4), no desde el mostrador (3,3).
Todos los HP se verifican al maximo. r05-league-lobby PASS y Continue del
checkpoint r05-league-lobby-rested PASS, archivo sin cambios.

Capturas privadas revisadas: r05-victory-road-exit.png,
r05-league-lobby-rested.png y r05-sidney-ready.png, dentro de build/.
El build GBA vuelve a dar pokeemerald.gba: OK (t27-league-gba-compare.log).
Sin nuevo fallo nativo ni cambios en upstream. R05 sigue abierto para Alto
Mando, Campeon, creditos y Hall of Fame. No se da T27 por terminado.

El control original de medallas desplaza ambos guardias y activa flag107;
r05-league-gate PASS desde el guardado del lobby. Se entra por Hall5 al cuarto
de Sidney. El primer intento con el equipo de campana termina en derrota
normal (gBattleOutcome=2), no en excepcion: reaparece fuera de Liga y permite
guardar. Cuatro Hyper Potions consumidas y dinero14642->7321; no se cuenta
como victoria ni se da el Alto Mando por cubierto. r05-sidney-result privado.

## T27 R05: Sidney, Torment y recarga del primer Alto Mando

Tras la derrota se compran cinco Hyper Potions por UI (6000), sin reponer
objetos por el depurador. r05-sidney-supplies PASS. El guion de combate elige
Pelipper contra Grass y Swampert contra el resto, usando Pokemon/Send Out y
las pociones reales. r05-sidney-tactical PASS: outcome1, flag4FB=1 y tres
cambios observados. No se alteran stats, PP, rivales ni reglas de combate.

Se encontro una espera propia de la automatizacion: Pelipper bajo Torment
(status2=80000000, gLastMoves=19) intentaba repetir Fly. GDB lo situa en
BattleScript_SelectingTormentedMove+3 / CompleteOnInactiveTextPrinter2.
El selector ahora omite ese ultimo movimiento mientras Torment esta activo;
solo lee estado y pulsa teclas. La misma batalla antes detenida termina en
outcome1 tras recargar el helper, sin reiniciar ni editar progreso del juego.

Tambien se limita Continue a frame1181 al estar frente a Sidney: los pulsos
hasta8000 podian iniciar la pelea antes de instalar la politica de pruebas.
Se conservan logs del replay anterior, y el replay corregido sale normalmente.
Continue de r05-sidney-win-verified PASS, archivo sin cambios; el manifiesto
incluye flag107, victorias del Alto Mando y game-clear. Captura privada
r05-sidney-win-verified.png. Se ha llegado al cuarto de Phoebe por las puertas
originales; R05 sigue abierto para los otros combates, creditos y Hall of Fame.

## T27 R05: derrota normal ante Phoebe y Bici Carrera por UI

El intento siguiente llega a Phoebe sin Pelipper y sin Hyper Potions. Termina
con outcome2, flag4FC=0 y regreso normal a EverGrande(18,6), dinero6221->3110.
No hay senal ni excepcion; se puede guardar. r05-phoebe-loss reproduce el
blackout y conserva ocho medallas. Las victorias temporales del Alto Mando
se reinician por el juego; la victoria de Sidney queda probada en su propio
checkpoint/replay, no se presenta este intento como una Liga completada.

Se vuela a Mauville, se habla con Rydel desde (3,5) mirando izquierda y se
elige Mach Bike por dialogo. Item259 pasa0->1. Se cura por enfermera real;
r05-mach-bike PASS. Desde Bag/Key Items se usa la bicicleta, comprobando bit2
de gPlayerAvatar, se guarda, y se desmonta por el mismo menu. El contexto de
Key Items tiene dos columnas (MultipleRows): se corrigio la suposicion de
SingleRow del guion. r05-bike-toggle PASS y Continue r05-mach-bike-tested PASS,
guardado intacto. El manifiesto ahora incluye la propiedad del item259.

Fly a Mossdeep, Surf y conexiones Route127/128/129/130/131, entrada normal
al Pilar, puertas/escaleras hasta1F: r05-pillar-return PASS. Escalera10,1 a2F
(10,2), estadoSkyPillar3 y casilla13,5 con comportamientoD2 (piso agrietado
real, no layout limpio de la primera visita): r05-broken-floor-entry PASS.
Continue r05-sky-pillar-broken-floor PASS, archivo intacto. Este es el punto
actual de continuacion: falta resolver el recorrido con Bici Carrera, preparar
un nuevo intento de Liga y completar el final; R05 y T27 siguen abiertos.

Capturas privadas: r05-mach-bike-mounted.png, r05-sky-pillar-broken-floor.png.
El proceso principal termina normalmente al salir del checkpoint del host.
ROM original SHA1 f3ae088181bf583e55daf962a92bb46f4f1d07b7 y save del usuario
SHA256 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
conservados. Solo cambios en helpers/documentacion; GBA sin cambios desde0047,
ultima verificacion pokeemerald.gba: OK. Sin push; planes del usuario intactos.

## T27 R05: cruce real del piso agrietado de Pilar Celeste 2F

Desde r05-sky-pillar-broken-floor se monta la Bici Carrera por Bag/Key Items.
El recorrido usa (12,2)->(12,13)->(1,13)->(1,7)->(3,7)->(3,2) y la escalera
original hasta 3F(3,2). ride_to observa cada dos frames sin soltar la direccion.
El helper advance permite hold==frames; no cambia input ni comportamiento
fuera del ejecutable de diagnostico. No se escriben velocidad ni coordenadas.

Los intentos iniciales cayeron normalmente por frenar contra el muro en
(13,7), o arrancar demasiado cerca de las grietas al subir desde (0,13).
GetPlayerSpeed y bikeFrameCounter observados con GDB: llegar a un giro con
contador2/velocidad3 conserva el impulso; detenerse reinicia el contador.
No hubo excepcion nativa. No se modifica la fisica ni el callback del suelo.

Replay r05-broken-floor-crossing PASS; Continue r05-sky-pillar-3f-mach PASS,
guardado intacto. Captura privada r05-sky-pillar-3f-mach.png en build/.
La repeticion arranca de Continue en frame2000, con pulsos solo hasta1800;
fallos de control, cambio inesperado de mapa y deadline son aserciones.
Queda resolver 4F, preparar el nuevo intento de Liga y completar R05; T27
sigue abierto. No hay cambios nativos ni nuevos parches upstream.

## T27 R05: puzzle de 4F, caida central y llegada a 5F

Desde el checkpoint 3F se desmonta por Bag y se sube por (11,1). Bici en
4F(12,2), recorrido continuo (12,6)->(10,6)->(10,12)->(3,12)->(3,4)->(4,4).
Al soltar la direccion, la inercia termina rompiendo el suelo en (6,4): el
script original hace caer a 3F(6,4), plataforma central inaccesible caminando.
La escalera (7,1) vuelve al centro de 4F y (3,1) lleva a 5F(3,2).
No se cambia ningun tile, warp, posicion, callback ni velocidad por GDB.

Replay r05-upper-floor PASS y Continue r05-sky-pillar-5f-mach PASS, save
intacto. Capturas privadas de la caida central y 5F bajo build/natural-campaign/.
Un intento por la columna13 quedo contra el muro13,3 y fallo por deadline del
helper; el recorrido correcto usa columna12. No es bloqueo ni excepcion del
juego y no requiere parche nativo. Captura de Rayquaza/final aun no acreditan
R05; se verifican en el siguiente incremento. T27 sigue abierto.

## T27 R05: captura natural de Rayquaza nivel70 con Master Ball

Desde 5F se sube por (10,1) a SkyPillar_Top y se llega a (14,7) andando.
La conversacion mirando arriba inicia BattleSetup_StartLegendaryBattle.
El helper selecciona Bag/Poke Balls/Master Ball, conservando las reglas del
combate. Outcome7, equipo5->6, especie406/nivel70/PokeBall1 y HP240/240.
La Master Ball obtenida por UI en el escondite Aqua pasa1->0. No se crean
Pokemon ni se conceden objetos, niveles, movimientos o resultados con GDB.

Replay r05-rayquaza-catch PASS y Continue r05-rayquaza-caught PASS; save
sin cambios. Se comprueban especie, nivel, movimientos, objetos equipados,
medallas y cantidades de inventario tras la recarga. Capturas antes/despues
privadas en build/natural-campaign/. No hubo excepcion nativa.
La captura habilita una nueva preparacion legal para Liga, pero no acredita
las victorias pendientes. R05, R06-R15 y Checkpoint E siguen abiertos.

## T27 R05: regreso preparado a Liga, Sidney/Phoebe y derrota ante Glacia

Rayquaza se pone primero mediante Pokemon/Switch. Fly a Mossdeep, Mart real:
compra de tres Hyper Potions por3600 (dinero4742->1142), enfermera del Centro,
Fly a EverGrande(18,6) y enfermera de Liga. Entrada por (9,1) al Hall5 y su
puerta (5,2) al cuarto de Sidney. No se conceden dinero, objetos ni curaciones.
Replay r05-rayquaza-league-prep PASS y r05-rayquaza-sidney PASS.
Sidney: outcome1/flag4FB1, dinero6042, tres pociones conservadas, Rayquaza92HP.

Puertas originales de Sidney/Hall1 a Phoebe: outcome1/flag4FC1, tres Hyper
Potions consumidas y dinero11142. Replay r05-rayquaza-phoebe y Continue de
r05-rayquaza-phoebe-win PASS, save intacto. El combate no se omite ni se
alteran movimientos, PP, enemigos o resultados. Se conserva ese checkpoint
antes de seguir: una derrota posterior no borra la evidencia de esta victoria.

El intento siguiente termina en derrota normal ante Glacia: outcome2, regreso
a EverGrande(18,6), dinero11142->5571 y flags temporales4FB-4FE todos0.
Ocho medallas y Rayquaza70 siguen presentes. Ya no habia Hyper Potions al
iniciar ese tramo; quedan pendientes preparacion y estrategia para ganarlo.
No es una excepcion ni espera infinita del host. El proceso principal sale
normalmente desde su checkpoint de frame127732. R05 NO esta completo: Glacia,
Drake, Wallace, creditos y Hall of Fame naturales siguen pendientes.

Pruebas finales: ejecutables normal/diagnostico, 21 suites host y verify-normal
PASS; ARM Binutils2.43.1, make compare -> pokeemerald.gba: OK. Sin cambios
en upstream ni nuevos parches. ROM SHA1 f3ae088181bf583e55daf962a92bb46f4f1d07b7
y save original SHA256 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
sin cambios. Capturas/checkpoints/replays privados bajo build/. Sin push.

La primera repeticion exploratoria de Glacia produjo outcome1, mientras la
prueba esperaba2: fallo una asercion del harness, sin guardar esa victoria.
No se presenta ese intento como checkpoint verificado. El runner ahora
registra el desenlace real (1 o 2) y valida los flags correspondientes; no
fuerza RNG ni resultados. Las repeticiones nuevas conservan los logs, guion,
inputs y save anteriores en history/<timestamp>/ dentro del scratch privado.
La conservacion de bytes y dos archivos sucesivos se verifico con fixtures
temporales propios. Ese intento exploratorio quedo sin checkpoint; la repeticion final se verifica abajo.


## T27 R05: victoria guardada sobre Glacia y Continue

La repeticion final desde el mismo guardado natural r05-rayquaza-phoebe-win
gana a Glacia: outcome1, flags Sidney/Phoebe/Glacia=1, Drake=0 y game_clear=0.
El runner registra el desenlace real; no modifica RNG, enemigos, objetos ni
progreso. El intento previo perdido permanece como evidencia independiente.
Replay r05-rayquaza-glacia PASS; checkpoint r05-rayquaza-glacia-win guardado
en build/natural-campaign/ y Continue --continue-until1181 PASS, save intacto.
Este es el punto de continuacion actual. Drake, Wallace, creditos y Hall of
Fame siguen pendientes; R05, R06-R15, T27 y Checkpoint E no se cierran.
Capturas, saves y logs siguen privados en build/. No hay push de estos cambios.


## T27 R05: derrota ante Drake y reabastecimiento natural

Desde r05-rayquaza-glacia-win se cruzan Glacia/Hall3/Drake por las puertas
(6,2)/(5,2) y se inicia el combate por dialogo. El intento termina en outcome2:
EverGrande(18,6), dinero16442->8221, ocho medallas conservadas y flags del
Alto Mando reiniciados. No hay excepcion nativa. Replay r05-rayquaza-drake PASS;
checkpoint r05-rayquaza-drake-loss y Continue --continue-until1181 PASS.
La inspeccion de los recursos del guardado anterior muestra Rayquaza0/240PS,
los otros cuatro companeros debilitados y Swampert73/188PS: el checkpoint
prueba una victoria sobre Glacia, pero deja un equipo agotado para Drake.

Desde ese blackout se vuela a Mossdeep y se compran cuatro Hyper Potions
(4800) y dos Revive(3000): dinero8221->421. Enfermera real, Fly de regreso y
puertas normales hasta Sidney. No se conceden dinero, objetos, PP ni PS por
el debugger. Replay r05-league-restock PASS y Continue del checkpoint
r05-league-restocked PASS. Los nuevos intentos usan las medicinas mediante
Bag/Use/seleccion del Pokemon, con verificaciones de consumo y PS.

Verificacion de esta continuacion: normal/diagnostico, 21 suites host y
verify-normal PASS; make compare -> pokeemerald.gba: OK. ROM legal SHA1
f3ae088181bf583e55daf962a92bb46f4f1d07b7 y save del usuario SHA256
b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260 intactos.
Upstream no se modifica; evidencias y capturas permanecen privadas en build/.


El segundo recorrido desde r05-league-restocked vuelve a ganar Sidney,
Phoebe y Glacia, pero pierde ante Drake de forma normal. Se conservan todos
sus checkpoints con prefijo r05-league-retry-; no sustituyen la evidencia
del primer recorrido. Las Hyper Potions usadas fuera del combate restauran
Rayquaza158->240 y154->245PS y descuentan una unidad por uso; el resto se
consume durante las peleas. Al llegar a Drake quedan Rayquaza47/245PS y
0PP de Outrage, Fly5PP, ExtremeSpeed5PP, Rest10PP; Pelipper47 y Swampert53
estan sanos. Quedan dos Revive sin consumir. No es un bloqueo del host:
la politica automatica solo elige ataques y no aprovecha Rest o Revive.
Drake, Wallace y el final de R05 continuan pendientes.


## T27 R05: recursos verificados, Rest/Revive y cosecha de Leppa

El replay r05-drake-rest selecciona Rest por teclado cuando Rayquaza tiene
pocos PS y usa los dos Revive comprados al debilitarse. Tambien acaba en
derrota normal, outcome2; no se cambia el juego para ganar. Los nuevos
checkpoints incluyen PS/maximos, estado, PP por movimiento y cantidades de
Revive/Leppa. Continue compara esos valores cuando estan presentes, con
compatibilidad para checkpoints anteriores sin estos campos.

Desde el blackout, Fly a Rustboro y conexion real a Route104. El dialogo
del arbol(36,6), abordado desde(36,7), entrega dos Leppa: cantidad0->2.
Luego compra de tres Hyper Potions y dos Revive por6600, enfermera real y
regreso hasta Sidney: r05-leppa-prep PASS. Checkpoint r05-league-leppa-ready
y Continue PASS, incluyendo PS/PP/estado e inventario de ambas medicinas.

El primer recorrido desde esa preparacion gana Sidney/Phoebe/Glacia. Sin
embargo, la politica gasta ambos Revive contra Glacia y Rayquaza queda
sin PS; una asercion de recursos detiene el harness antes de Drake. No es
una excepcion del ejecutable ni una victoria de Liga. Se conserva el log.
Se retoma r05-leppa-phoebe-win (Continue con recursos PASS), reservando
Revive para Drake y evitando Rest frente a movimientos de hielo conocidos.
El primer arranque de esta continuacion reabre dialogo por demasiados
pulsos A de Continue; el harness lo detecta antes de usar objetos. Se corrige
ese guion para terminar las pulsaciones en1181, sin modificar el juego.
Los logs previos quedan archivados en history/ dentro del scratch privado.


Prueba aislada r05-leppa-use PASS: Mochila/Berries/Use, Rayquaza y su cuarto
movimiento seleccionados por teclado. Leppa2->1 y Enfado8->15PP; el limite
se calcula con los PP maximos del movimiento y sus bonus, no se asume10.
Checkpoint r05-phoebe-leppa-restored y Continue PASS con PS/estado/PP y
ambas cantidades de consumibles intactos. La captura privada muestra la
sala de Phoebe, el jugador y el NPC visibles tras volver del menu.
El intento r05-leppa-finish corregido pierde ante Glacia normalmente;
no acredita completar el Alto Mando. Se conserva para reproduccion.


## Cierre de este incremento T27: limites y siguiente preparacion

r05-leppa-precharged vuelve a perder ante Glacia; recuperar PP por si solo
no resuelve la debilidad a hielo. r05-glacia-ground-lead cambia realmente
Swampert del slot5 al primero mediante Pokemon/Switch, pero tambien acaba
en outcome2. Sus ataques quedan registrados en battle-choices.jsonl, ahora
tanto para combates individuales como dobles. No se modifican stats, tipos,
enemigos, movimientos ni resultados para aprobar el recorrido.

Checkpoint exterior mas reciente: r05-glacia-ground-lead-loss, frame53764,
EverGrande(18,6), dinero5630, Swampert54 primero, Pelipper49 y Rayquaza71 en
slot5; Hyper Potions0, Revive2 y Leppa1. El equipo queda curado por el blackout
y los cuatro flags del Alto Mando vuelven a0. La recarga final comprueba
mapa, orden del equipo, PS, estados, PP, inventario, dinero y eventos.
El checkpoint previo r05-phoebe-leppa-restored conserva Enfado15PP y la
victoria de Phoebe; los checkpoints anteriores de Glacia siguen intactos.
Ninguno acredita una victoria sobre Drake ni la Liga completa.

Siguiente trabajo: preparar cobertura electrica y mas curacion mediante
obtencion/compra/ensenanza reales, luego repetir Glacia/Drake/Wallace desde
la misma partida. No seguir repitiendo la misma estrategia agotada. R05,
R06-R15, T27 y Checkpoint E permanecen abiertos. Este incremento cambia
solo helpers y documentacion; el codigo del juego y los parches no cambian.

Continue final de r05-glacia-ground-lead-loss: PASS; save sin reescribir.


## T27: cobertura electrica obtenida sin conceder progreso (17-10-2026)

Wattson entrego la Llave del Sotano por dialogo. Se entro a New Mauville
con Surf y la llave, se resolvieron los interruptores por desplazamiento,
se recogieron Escape Rope y Full Heal y se apago el generador. Continue
conserva var 0x40BA=2; el parche 0048 corrige la recarga descrita en
first-run-report.md. Se consumio Escape Rope por Bolsa y se regreso a Wattson:
regalo TM24, flag 0xD1 y aprendizaje de Rayo por menu verificados; TM consumida.
Rayquaza conserva Vuelo/Rayo/Velocidad Extrema/Enfado; no se concedieron
movimientos, dinero, objetos, experiencia ni flags desde GDB.

Se compraron cuatro Hiper Pociones (4800, saldo 5630->830), se curo el equipo
y se volvio a la Liga por Fly/puertas reales. El replay r05-thunderbolt-league
vence a Sidney (frame27448), Phoebe (49216), Glacia (75544) y Drake (95920).
Save de Drake (96952): cuatro flags del Alto Mando=1, game-clear=0,
Rayquaza72 PS75/249, PP12/12/5/2; dos Revivir, Full Heal1, Leppa1,
saldo21630. Continue de Drake PASS, incluida integridad PS/PP/estado/inventario.
Se uso la ultima Leppa por Bolsa (Enfado2->12PP) y se guardo delante de Wallace
(Hall4,5,3). Esto no acredita aun victoria sobre Wallace ni el final.

Replays PASS: r05-new-mauville-key/entry/generator/reward,
r05-thunderbolt-league-prep/league y r05-champion-door. Evidencia y capturas
privadas en build/natural-campaign/ y build/natural-campaign-replay-r05-*;
resumenes build/t27-thunderbolt-league-replay.log,
build/t27-thunderbolt-drake-win-reload.log y build/t27-champion-door-replay.log.
R05 sigue abierto; R06-R15 y Checkpoint E siguen abiertos.


## T27: final natural y cierre de R05 (17-10-2026)

Desde r05-wallace-door-ready, la entrada real a la sala inicia el combate
contra Wallace. La observacion de CB2_EndTrainerBattle registra outcome1;
ningun resultado, objeto, experiencia o flag se escribe desde el debugger.
Se usan los menus para movimientos/cambios y los Revivir adquiridos antes.
Dos ejecuciones llegan al Hall of Fame. La segunda verifica el registro de
los seis miembros y continua sin pulsaciones durante los creditos hasta
Task_CreditsTheEnd6: The End capturado en frame68624.

Equipo del Hall of Fame: Rayquaza73, Pelipper52, Gloom21, Castform25,
Tentacool18 y Swampert54. Ocho medallas y game-clear=1. Capturas y saves
privados: build/natural-campaign/r05-hall-of-fame.* y r05-the-end.*.
La captura del Hall of Fame muestra al entrenador, su equipo y
LEAGUE CHAMPION / CONGRATULATIONS. La pantalla final coincide en los
38400 pixeles con una referencia derivada de las tablas originales de
letras, sus flips y los graficos/paleta generados por GBA (expansion RGB5).
Una sospecha visual inicial de trazos ausentes no se confirma: 0 diferencias
(build/t27-the-end-reference-check.json); no se hizo ningun cambio por ella.

Otro proceso carga ese save mediante Continue: dormitorio de Brendan 2F,
control de campo libre, ocho medallas, game-clear y seis especies/niveles
conservados. LoadGameSave(SAVE_HALL_OF_FAME) devuelve SAVE_STATUS_OK y los
seis registros persistidos coinciden. El save queda identico byte a byte.
No hubo una nueva excepcion del host en el tramo del Campeon/final.

Reproduccion MINGW32, con los checkpoints naturales previos en build/:
python port/tests/natural_campaign_smoke.py --phase r05-wallace-champion
Conservar r05-hall-of-fame y r05-the-end en build/natural-campaign/ y ejecutar:
python port/tests/natural_ending_reload.py
Logs: build/t27-wallace-champion-replay.log,
build/natural-campaign-replay-r05-wallace-champion/campaign.log,
build/t27-natural-ending-reload.log y build/natural-campaign-ending-reload/reload.log.

R05 completo; T27 y Checkpoint E siguen abiertos. Siguiente cobertura:
R06 (crianza/huevo/eclosion natural), despues Safari y Battle Frontier
R07-R14, y los gates finales R15. Los fixtures preparados anteriores no
sustituyen estos criterios. Normal/diagnostico y 21 suites PASS; GBA compare
OK con ARM Binutils2.43.1, como consta en los logs del parche0048.


## T27 / R06: preparacion natural (21-10-2026)

Se continua el save real del Hall of Fame. La salida de casa recorre la
secuencia posterior a los creditos (SS Ticket/television/laboratorio de Birch),
despues sale por la puerta del laboratorio, vuela a Mauville y camina hasta
la guarderia en Route117 (51,6). Replay r06-daycare PASS y checkpoint privado
r06-daycare-arrival. Dos intentos anteriores del harness asumian terminar
junto a la puerta de casa: el evento legitimo acaba en el laboratorio. Se
corrigio solo la ruta de prueba; no hubo excepcion nativa ni parche upstream.

Lectura de generos: Rayquaza sin genero; Pelipper/Gloom/Tentacool/Swampert
hembras, Castform macho. La tabla real da Planta/Planta a Gloom y Hada/Amorfo
a Castform: no son compatibles. Se prepara la captura natural de un Oddish
macho para Gloom; todavia no se acredita huevo, eclosion ni cierre de R06.

Normal/diagnostico, 21 suites y verify-normal PASS (build/t27-r06-host.log).
GBA compare: pokeemerald.gba: OK con ARM Binutils2.43.1
(build/t27-r06-gba.log). El recorrido usa copias privadas en build/.


R06, deposito materno: replay r06-mother PASS. Se compraron 20 Poke Balls
por tienda y se dejo Gloom hembra mediante el menu de la guarderia.
Checkpoint r06-mother-deposited: equipo5, Gloom44 en guarderia, segundo
hueco vacio, offspring=0, flag0x86=0 y compatibilidad0. La instantanea registra
identidad/pasos de los padres, personalidad de cada miembro y estado de huevo.
Layout medido con GCC i686: DayCare288, DaycareMon140, steps136,
offspring280, contador284; SaveBlock1.daycare=0x2EE8, confirmado en el getter
del ejecutable. No se usan los offsets comentados del header GBA para el host.
Ajustes del harness: aproximacion/entrada por puerta, hablar desde el lado
del mostrador y nombre real GetBoxMonData3. Ningun cambio nativo requerido.


R06, padre y produccion del huevo: captura natural de Oddish macho13 PASS,
con Poke Balls compradas y seleccion por genero mediante huida/menus normales.
Se dejo el padre en la guarderia: pareja Gloom44/Oddish43, compatibilidad20.
El replay r06-generate produjo el huevo caminando/corriendo: pasos padre4->2560,
madre110->2666; offspring0->1496255074 y flag0x86 0->1. Checkpoints privados
r06-parents-deposited y r06-egg-pending. No se modifican contadores, flags,
experiencia, especies ni personalidad desde GDB. El cambio de filtro de genero
es optativo y solo afecta la eleccion de teclas en el harness de diagnostico.
Continue de r06-mother-deposited PASS: identidad/pasos/contador/inventario/equipo
conservados y save intacto. Recogida/eclosion y sus recargas siguen pendientes.


## T27 / R06 completo: huevo y eclosion naturales (21-10-2026)

La partida procede del Hall of Fame ganado en R05. Se compraron 20 Poke Balls,
se deposito Gloom hembra y se capturo Oddish macho13 mediante Bolsa/huida.
La pareja real Gloom/Oddish tiene compatibilidad20. Los padres se dejaron por
UI y el huevo aparecio con pasos del padre4->2560, personalidad1496255074 y
flag pendiente0->1. No se invocaron rutinas para producir huevos ni se
escribieron readiness, pasos, especie, experiencia o personalidad desde GDB.

Se entro/salio de la guarderia para que el script colocara al cuidador fuera,
y se recogio el huevo por dialogo. Equipo5->6, especie43, is_egg=1, ciclos20,
personalidad1496255074; pending y offspring se limpian mediante el script.
Despues se recorrieron 5375 pasos medidos por el contador materno2677->8052.
Los ciclos bajan por el juego; la animacion y el texto ODDISH hatched from
the EGG aparecen. Oddish hembra5 conserva su personalidad, is_egg pasa a0,
friendship=120 y no es Bad Egg. Regreso al campo y guardado en Route117(53,6).
Mientras se caminaba, los padres generaron un segundo huevo pendiente; se
conserva ese estado normal, sin confundir su personalidad2442798564 con la
del primer huevo ya eclosionado.

Cuatro Continue en procesos nuevos PASS: madre depositada, huevo pendiente,
huevo recogido y Oddish nacido. Se comparan padres/identidades/pasos,
compatibilidad, pending/offspring/contador y especie/nivel/genero/personalidad/
is_egg/friendship-ciclos de todo el equipo, ademas de PS/PP/movimientos/estado,
inventario, dinero y progreso. Cada recarga deja el archivo save intacto.
No aparecio una excepcion nativa: solo se ajustaron rutas y simbolos del
harness. No hace falta parche0049; los 48 parches existentes no cambian.

Evidencia privada: build/t27-r06-{daycare,mother,father-catch,generate,receive,hatch}.log;
build/t27-r06-{mother,pending,received,hatched}-reload.log.
Checkpoints en build/natural-campaign/r06-*. Capturas PNG de
r06-hatch-animation y r06-oddish-hatched bajo ese mismo directorio, fuera de Git.
Reproduccion MINGW32, con los checkpoints previos obtenidos naturalmente:
python port/tests/natural_campaign_smoke.py --phase r06-daycare
Continuar con --phase r06-mother, r06-father-catch, r06-generate, r06-receive y
r06-hatch; conservar sus checkpoints en build/natural-campaign/ entre fases.
python port/tests/natural_campaign_reload.py r06-oddish-hatched --continue-until 1181

Normal/diagnostico, 21 suites y verify-normal PASS (build/t27-r06-host.log).
ARM Binutils2.43.1, make compare -> pokeemerald.gba: OK (build/t27-r06-gba.log).
R06 completo. T27/Checkpoint E siguen abiertos para R07-R15; el siguiente
recorrido es Safari por bolas agotadas y por 500 pasos reales.


## T27 / R07: preparacion de Safari (21-10-2026)

Desde el Oddish nacido en R06, se obtuvo la Cana Vieja del pescador movil
de Dewford y el Tubo Pokecubos de la recepcion de concursos de Lilycove,
por dialogos/menus reales. Salida y conexion caminada a Ruta121; un entrenador
intercepto el recorrido y fue resuelto mediante el combate normal. Llegada
a recepcion de Safari y guardado r07-safari-reception PASS. ModoSafari=0,
bolas=0, pasos=0. El inventario registrado incluye Cana262 y Tubo273.
No se declara todavia admision ni agotamiento de cuotas. Sin cambios nativos.


## T27 / R07 completo: cuotas naturales y Continue (22-10-2026)

Dos admisiones reales, 500 de dinero cada una. Pesca en SafariZone_Southwest
(8,31), Cana Vieja por Bolsa, capturas/escapadas originales: observador de
HandleAction_SafariZoneBallThrow registra exactamente [30,29,...,1]. La ultima
bola captura y el script devuelve a recepcion (9,4), modo/bolas/pasos=0.
Segundo recorrido alterna teclas entre (32,35)/(31,35): observador de
SafariZoneTakeStep registra [500,499,...,1], sin llamar la rutina desde GDB.
TimesUp devuelve a recepcion; las 30 bolas permanecen durante el paseo.

Checkpoints r07-balls-exhausted y r07-steps-exhausted: Continue PASS con estado
Safari cero, equipo, PS/PP, inventario y dinero persistidos, save intacto.
Evidencia privada: build/t27-r07-{balls,steps}.log,
build/t27-r07-{balls,steps}-reload.log y build/natural-campaign/r07-*.
No cambio nativo ni parche upstream; R08-R15 siguen abiertos.


## T27 / R08: acceso natural y admision a Torre (22-10-2026)

Viaje desde Lilycove a Slateport con SS Ticket: escena Scott, flag 0x1D0=1,
dos descansos en camarote y llegada por script PASS. Nuevo ferry selecciona
Battle Frontier del menu real; llegada y Continue (save intacto) PASS.
Recepcion entrega Frontier Pass por script. Desplazamiento desde el muelle,
puerta de recepcion, conexion este y entrada a Torre: PASS.

Nivel Abierto seleccionado por multichoice24, equipo real [5,2,3]:
Swampert54, Pelipper52 y Castform25. Rayquaza excluido por las reglas.
Seleccion, guardado obligatorio, ascensor y primera batalla al frame6400 PASS.
No se acredita aun victoria, racha, recompensa ni suspension/reanudacion.
Evidencia: build/t27-r08-access.log, t27-r08-arrival-reload.log,
t27-r08-tower-lobby.log, t27-r08-tower-enter.log; checkpoints privados
r08-frontier-arrival y r08-tower-reception. R08-R15 abiertos.


## T27 / R08: seis victorias y derrota normal (22-10-2026)

Primer intento Torre Nivel Abierto: resultados observados en
HandleSpecialTrainerBattleEnd [1,1,1,1,1,1,2]. Swampert54/Pelipper52/Castform25
vencen seis rivales, pierden ante el septimo; lobby restaura y cura los seis
miembros originales, streak/record=6, BP=0. Sin excepcion ni bloqueo nativo.
Checkpoint r08-tower-loss y Continue PASS: records, equipo, PS/PP, inventario
y dinero conservados, save intacto. R08 no completo: faltan siete victorias,
recompensa y suspension/reanudacion. Nuevo intento desde la derrota en curso.

Se agrega probe C propio frontier_layout.c para medir offsets de SaveBlock2
con GCC MINGW32 en cada replay R08, en vez de comentarios del layout GBA.
Evidencia privada: build/t27-r08-tower-round.log,
build/t27-r08-tower-loss-reload.log y t27-r08-tower-live.png.
GBA original: make compare KEEP_TEMPS=1 NODEP=1 -> pokeemerald.gba: OK
(build/t27-r08-gba.log), ARM Binutils 2.43.1. No parche nativo nuevo.


## T27 / R08: ronda completa y recompensa (22-10-2026)

Segundo intento desde r08-tower-loss: siete resultados [1,1,1,1,1,1,1],
record/streak=7, batallas acumuladas14 y PB0->1. Guardado r08-tower-seven-wins
por menu y Continue PASS, conserva records/PB y equipo completo, save intacto.
El primer arranque de este retry no interactuaba con la recepcionista: el
harness ahora camina hasta (6,6) y se orienta arriba antes de pulsar A,
en vez de depender de la direccion heredada del checkpoint. No fallo nativo.
Evidencia: build/t27-r08-tower-retry.log y t27-r08-seven-wins-reload.log.
R08 sigue abierto solo por suspension/reanudacion; derrota/recarga, seleccion,
ronda de siete, registro y recompensa ya verificados.


## T27 / R08 completo: suspension y reanudacion (23-10-2026)

Copia de r08-tower-reception: primera victoria natural, Rest en menu103,
guardado real challengeStatus2, curChallengeBattleNum1 y selectedPartyMons
[5,2,3,0]. SoftReset diagnostico termina limpio; no se invoca reset desde GDB.
Continue del archivo r08-tower-paused recupera esos mismos contadores y
seleccion, native resume status1, ascensor y segunda batalla al frame4016 PASS.
Prueba independiente de la ronda ganada/derrota anteriores, como permiten
los criterios R06-R14. Intento previo de pausa tras siete pierde el siguiente
combate normalmente (historial); no se acredita como suspension.
R08 completo por conjunto de pruebas. Logs build/t27-r08-tower-pause.log,
t27-r08-tower-resume.log; capturas/checkpoints privados en build/.

R09, alquileres: tres seleccionados mediante bolas/Rent/Yes, equipo realmente
prestado [247,202,333] nivel50; traslado y primer combate PASS
(build/t27-r09-factory-rent.log). La eleccion lee las seis fichas generadas;
no crea Pokemon ni modifica datos. Falta intercambio y ronda/recompensa.


## T27 / R09-R11: diagnosticos naturales pendientes (26-10-2026)

Fabrica: seleccion real de seis fichas, Rent/Yes y primer intercambio PASS
en el historial de r09-factory-exchange. Parche0050 corrige NULL al entrar
al intercambio; parche0051 corrige division por cero al terminar animacion
VerticalShakeLowTwice. Compare GBA OK y objetos de clon limpio identicos,
detalle en first-run-report.md. Ronda nivel50 termina en derrota normal
[2], guardado r09-factory-loss. Nivel Abierto tambien [2], conserva salida
normal y equipo; siguiente intento recibe Rhydon/Gyarados/Porygon2 nivel100
y vence primer combate35599 despues del0051. Ronda/recompensa aun pendientes.

Palacio: ruta desde Torre/puerta/recepcion y Nivel Abierto/seleccion legal
PASS. Primer intento [2],120 callbacks automaticos, cero elecciones manuales.
Continue de r10-palace-loss PASS con equipo, record/PB y save intacto.
Retry [1,1,1,2],464 callbacks automaticos, cero manuales. No se acredita
ronda completa ni recompensa; los intentos interrumpidos anteriores tampoco
son PASS. Evidencia build/t27-r10-palace-{round,retry,loss-reload}.log.

Arena: desplazamiento a recepcion y guardado r11-arena-reception PASS.
Entrada legal y apertura de Pokemon en combate: PARTY_ACTION_CANT_SWITCH2.
Segundo Pokemon ofrece Summary/Cancel; la segunda opcion vuelve a lista,
no abre Summary como ocurriria si hubiera Shift. Cancelar devuelve al combate
con el mismo indice activo0 al frame9356. Sin cambio de Pokemon.
Evidencia build/t27-r11-arena-{lobby,restriction}.log. Faltan juicio, ronda
y recompensa. R09-R15 y T27 permanecen abiertos.


## T27 / R15: corregir verificacion de recarga obsoleta (26-10-2026)

El wrapper Continue copiaba el diagnostico del directorio canonico de
fixtures; ese binario era distinto al build actual. Ahora usa build/ actual
por defecto y permite --exe para comprobar un reenlace limpio concreto.
Cada recarga Frontier mide offsets en su propio directorio de prueba, con
escritura atomica del JSON; evita compartir el ejecutable/JSON del probe.
El driver acepta la ruta explicita FRONTIER_LAYOUT, con fallback para
experimentos anteriores. owned_enter permite una condicion de parada para
inspeccionar menus previos al combate, sin alterar los controles normales.

Recarga r11-arena-loss con binario actual PASS y save intacto; SHA256 del
exe copiado coincide con build/:37dabf5bc0254cf4fe7d2108a833f260c139020dd50304845e3f8e102f75d75c.
La copia antigua era distinta, confirmado por comparacion de bytes.
Evidencia: build/t27-r11-arena-loss-reload.log. R15 no se cierra hasta
completar las facilities y los gates finales restantes.


## T27 / R09: ronda Factory completa (27-10-2026)

Nivel Abierto: cuatro victorias naturales y Rest por menu; Continue
recupera los tres alquileres con personalidad, nivel y movimientos intactos.
Despues otras tres victorias; seis intercambios reales en total. Resultado
[1,1,1,1,1,1,1], racha7, alquileres7 y PB0->3. Guardado desde el menu y
Continue verifican registros, equipo e inventario sin alterar el archivo.
Los anteriores intentos perdidos permanecen en el historial.
Evidencia build/t27-r09-factory-open-pause.log,
build/t27-r09-factory-resume.log y build/t27-r09-factory-seven-reload.log.
El ejecutable de la ronda reanudada reenlaza dos objetos del clon limpio;
los demas objetos se reutilizan del build principal: no es build limpio total.


## T27 / R12: campeonato Dome completo (27-10-2026)

Inscripcion de tres participantes, cuadro de 16 y seleccion de dos mediante
interfaz nativa; cuatro victorias [1,1,1,1], campeonato1, racha1 y PB1->2.
Guardado desde menu y Continue verifican registros, equipo e inventario sin
alterar el archivo. Evidencia build/t27-r12-dome-round.log y
build/t27-r12-dome-champion-reload.log; captura del cuadro en build/.


## T27 / R14: Pyramid completo (27-10-2026)

Equipo legal preparado por menu, bolsa especial abre y cierra tras parche0053.
Siete pisos naturales [0,1,2,3,4,5,6], encuentros y desplazamientos por teclas,
cima, racha7 y PB1->6. Guardado por menu y Continue preservan registros,
equipo e inventario sin modificar el save. Evidencia: 
build/t27-r14-pyramid-round-retry.log y t27-r14-pyramid-complete-reload.log.


## T27 / R13: circuito Pike completo (28-10-2026)

Las elecciones reales atraviesan salas 1 a 14, incluyendo encuentros
salvajes, paralisis64 y curacion; racha14, PB1->2 y regreso al lobby.
El guardado por menu y Continue conservan equipo, inventario y registros
sin modificar el save. Evidencia build/t27-r13-pike-sixth-attempt.log,
build/natural-campaign-replay-r13-pike-retry/campaign.log y
build/t27-r13-pike-complete-reload.log. Los intentos perdidos siguen en
checkpoints privados y en history/.


## T27 / R11: ronda Arena completa (28-10-2026)

Restriccion de cambio comprobada en menu real; juicio observa estados0-10.
Siete victorias [1,1,1,1,1,1,1], racha7 y PB1->2; guardar y Continue
conservan equipo y registros sin modificar save. Evidencia
build/t27-r11-arena-third-loss-isolated.log y t27-r11-arena-seven-reload.log.


## T27 / R10: entrenamiento adicional (30-10-2026)

El intento desde r10-palace-trained-loss3 termino con cuatro victorias y
una derrota ([1,1,1,1,2]); 464 callbacks automaticos y ninguna seleccion
manual. PB permanece en 1: no acredita recompensa ni circuito. Evidencia:
build/t27-r10-palace-trained-retry3.log y campaign.log de
build/natural-campaign-replay-r10-palace-retry/ (history/ tras otro intento).

Entrenamiento natural independiente llevo a Castform de nivel30 a 40 con
Repartir Exp., combates y curacion por UI. Checkpoint real guardado en
build/natural-campaign/r10-castform-level40.*; evidencia
build/t27-r10-training-level40.log y
build/natural-campaign-replay-r10-training-advanced/campaign.log.
R10 sigue pendiente de siete victorias, recompensa y Continue. No se
alteraron niveles ni resultados con GDB.
