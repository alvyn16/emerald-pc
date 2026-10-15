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
