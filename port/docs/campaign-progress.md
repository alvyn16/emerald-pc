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
