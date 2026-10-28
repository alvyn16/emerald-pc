# T27: cerrar toda la cobertura pendiente

T27 y Checkpoint E no se cierran ni se avanza a otra tarea hasta verificar
todos los puntos siguientes. Los recorridos anteriores son evidencia parcial.
Cada incremento añade pruebas propias; un fallo del juego se diagnostica con
GDB y se corrige en port/ o mediante un parche PORT_PC numerado.

## Orden y criterios de aceptación

- [x] R01: intro, elección real del inicial, rescate de Birch, rival y entrega
  de Pokédex/bolas. Sin CreateMon, warps, flags, objetos o experiencia concedidos
  por el debugger. Guardar y reabrir: especie, nivel, mapa y progreso coinciden.
  Evidencia: `build/natural-campaign/r01-birch-dex.json` y
  `build/natural-campaign-reload/reload.log`; recorrido y lectura descritos
  en `campaign-progress.md`. R05–R15 siguen abiertos.
- [x] R02: desplazamientos reales y puzzles para los primeros cuatro gimnasios;
  Devon/Peeko/Briney, Aqua en Slateport, meteorito y Magma en Mt. Chimney.
  Comprobar rechazo de pasos bloqueados antes de completar su requisito y
  acceso después; obtener medallas mediante NPC, conservando el mismo save.
  Evidencia: checkpoints de Roxanne/Brawly/Wattson/Flannery y sus recargas;
  `r02-maxie-meteorite`, gating del museo/teleférico y regresiones naturales
  de Rock Smash, Meteor Falls, Jagged Pass y el puzzle/combate de Flannery.
  Detalle y límites de los intentos: `campaign-progress.md`. R05–R15 abiertos.
- [x] R03: Norman/Surf, Weather Institute/Castform, rival/Fly y Fortree/Devon
  Scope. Cruzar los obstáculos con input y los movimientos/herramientas reales.
  Norman/quinta medalla y entrega/enseñanza/cruce de Surf naturales: PASS;
  Fuerza obtenida en Rusturf y puertas del gimnasio antes/después: PASS.
  Recarga de Norman y repeticiones `r03-strength`, `r03-norman`, `r03-surf`
  documentadas en `campaign-progress.md`. Instituto/Castform, cama, puente
  bloqueado/abierto y recarga: PASS (`r03-weather` y sus checkpoints).
  Rival/entrega y enseñanza de Fly, bloqueo previo a sexta medalla, Devon Scope
  y puzzle de puertas giratorias: PASS con repeticiones y recargas. Alana fue
  derrotada tras comprar/enseñar Blizzard por UI; Fly confirma ida/vuelta y
  cancelación con el parche 0043. Continue de r03-fly-roundtrip: PASS.
- [x] R04: Mt. Pyre, escondites Aqua/Magma, Mossdeep/Space Center, Dive,
  Seafloor Cavern, Sky Pillar/Rayquaza, Sootopolis y octava medalla. Eventos y
  desbloqueos deben proceder de scripts; verificar sus condiciones previas.
  Monte Pírico/Emblema Magma por evento, repetición y Continue: PASS; el resto
  de R04 se completó (detalle en campaign-progress.md). Magma/Fuerza,
  Tatiano, despertar de Groudon y Maxie: PASS; replay/Continue de Maxie PASS.
  Aqua: robo, paneles/Master Ball, Mat�as y salida mar�tima antes/despu�s PASS;
  repeticiones y recarga de la victoria PASS. Mossdeep: circuito completo, victoria original y Continue PASS; repeticion
  de derrota normal documentada. Centro Espacial y entrega/ensenanza de Dive
  por UI, replays y Continue PASS. Buceo/emerger y Continue submarino PASS tras
  0044/0045. Seafloor: Fuerza, corrientes, Shelly, Archie y salida de Kyogre
  por scripts/replays/Continue PASS. Llegada Sootopolis/camaras/escena abreviada
  y dialogo Steven/Wallace por UI y replay PASS (0046/0047). Sky Pillar,
  caida/subida, despertar y cinco segmentos de Rayquaza por replay PASS;
  paz y Continue PASS. Waterfall por regalo/UI/replay y tres tableros de hielo
  por teclado/replay PASS. Juan gana con cambio/objetos comprados por UI;
  ocho medallas, recompensas, replay y Continue PASS. R05-R15 pendientes.
- [x] R05: Waterfall, Victory Road, acceso a Liga, ocho medallas y créditos
  desde esa misma partida; sin warps del harness ni equipo preparado. Recarga
  final: game-clear, equipo y Hall of Fame válidos. Capturas privadas.
  Cascadas, Wally, Flash, Fuerza, Golpe Roca y salida de Calle Victoria:
  replays PASS; enfermera de Liga y Continue PASS. Alto Mando y final pendientes.
  Sidney: victoria original, replay y Continue PASS. Resto del Alto Mando pendiente.
  Blackout ante Phoebe y Bici Carrera por UI/replay PASS. Recarga del regreso
  a Pilar Celeste PASS; cruce de 2F con Bici Carrera, replay y Continue 3F PASS.
  Puzzle de 4F/caida central, llegada a 5F, replay y Continue PASS.
  Captura real de Rayquaza70/Master Ball, replay y Continue PASS.
  Regreso preparado a Liga y victorias de Sidney/Phoebe/Glacia, replays y Continue PASS.
  Derrota previa ante Glacia conservada; Drake, Wallace y final pendientes.
  Derrota normal ante Drake, Continue y reabastecimiento por tienda/enfermera PASS.
  Cosecha Leppa, uso por menu (Enfado8->15PP), PS/estado/PP/consumibles
  persistidos y Continue PASS. Nuevos intentos ante Glacia terminan en derrota
  normal (historial). New Mauville/Llave/generador/Rayo por UI y Continue PASS.
  Replay con Rayo vence Sidney/Phoebe/Glacia/Drake; Continue de Drake PASS.
  Ultima Leppa consumida por UI; checkpoint Hall4 ante Wallace PASS.
  Wallace, Hall of Fame y The End: replay PASS. Continue final devuelve
  al dormitorio, conserva ocho medallas, game-clear y seis especies/niveles;
  registros/checksums Hall of Fame validos y save intacto. R05 completo.
  Evidencia: build/t27-wallace-champion-replay.log y
  build/t27-natural-ending-reload.log. R06-R15 siguen abiertos.
- [x] R06: crianza por pasos reales, generación de huevo, recogida por diálogo,
  eclosión mediante desplazamientos y conservación tras save/reload. No marcar
  readiness, contador de huevo ni especie manualmente.
  Gloom hembra/Oddish macho capturado; compatibilidad20, huevo producido tras
  pasos reales, recogida por cuidador y eclosion despues de 5375 pasos PASS.
  Oddish hembra5 conserva personalidad1496255074; cuatro Continue PASS
  (madre/pending/huevo/nacido), incluyendo contadores/estado/equipo y save
  intacto. Evidencia: build/t27-r06-*.log y campaign-progress.md.
- [x] R07: Safari con agotamiento real de sus 30 bolas y salida correcta;
  paseo que consuma los 500 pasos, además del test previo de la rutina de pasos.
  30 lanzamientos observados [30..1] y 500 pasos por teclado [500..1]: PASS.
  Ambas salidas limpian modo/bolas/pasos a cero; Continue de ambos checkpoints
  PASS, conserva equipo/inventario/dinero y no reescribe el save.
- [x] R08: Battle Tower: admisión, selección legal, racha completa, registro
  y recompensa; reanudación/recarga y salida de una derrota.
  Ronda [1,1,1,1,1,1,1], record7 y PB0->1; Continue PASS. Derrota
  previa [1,1,1,1,1,1,2], salida/restauracion/equipo y Continue PASS.
  Copia de recepcion: victoria1, Rest por menu, PAUSED2 guardado y reset
  diagnostico limpio; Continue reanuda batalla2 con mismos contadores/equipo.
- [x] R09: Factory: alquileres, intercambios y racha/recompensa mediante UI.
  Siete victorias reales, seis intercambios, racha7 y PB0->3. Rest tras
  cuatro victorias y Continue conservan alquileres, personalidad y movimientos.
  Continue final PASS conserva equipo, registros y save intacto. Evidencia:
  build/t27-r09-factory-resume.log y build/t27-r09-factory-seven-reload.log.
- [ ] R10: Palace: selección automática de movimientos y racha/recompensa.
- [x] R11: Arena: juicio, restricciones de cambio y racha/recompensa.
  Restriccion de cambio, juicio estados0-10, siete victorias, racha7 y PB1->2:
  PASS. Continue conserva equipo y registros sin modificar el save. Evidencia:
  build/t27-r11-arena-third-loss-isolated.log y t27-r11-arena-seven-reload.log.
- [x] R12: Dome: inscripción, cuadro/elección del equipo y torneo/recompensa.
  Inscripcion legal, cuadro de 16 y eleccion de dos: PASS. Cuatro victorias,
  campeonato1, racha1 y PB1->2: PASS; Continue conserva equipo y registros.
  Evidencia: build/t27-r12-dome-round.log y t27-r12-dome-champion-reload.log.
- [x] R13: Pike: elecciones de salas, encuentros/estados y circuito/recompensa.
  14 salas, encuentros salvajes, paralisis64 y curacion observados; racha14,
  PB1->2. Guardado y Continue conservan equipo y registros sin modificar save.
  Evidencia: build/t27-r13-pike-sixth-attempt.log y
  build/t27-r13-pike-complete-reload.log; derrotas previas conservadas.
- [x] R14: Pyramid: exploración de pisos, bolsa propia, ascenso y recompensa.
  Bolsa especial, siete pisos [0..6], cima, racha7 y PB1->6: PASS.
  Continue conserva registros y equipo sin modificar el save: PASS.
  Evidencia: build/t27-r14-pyramid-round-retry.log y
  build/t27-r14-pyramid-complete-reload.log.
- [ ] R15: repetición de regresiones afectadas, build normal/diagnóstico,
  suites host, compare GBA OK y reproducción limpia de cualquier parche nuevo.
  Revisar matriz/informes y cerrar únicamente lo que tenga evidencia.
  Clon limpio desde base + 53 parches via setup.ps1 reproduce el mismo arbol;
  GBA limpio compare OK y PC limpio exe/diagnostic/test/verify-normal PASS
  (21 suites). Compilador agbcc ya instalado y ROM propia copiados solo a
  build/. Evidencia build/t27-clean-series53-{setup,gba-build,pc-resume}.log.
  Falta auditoria final y regresiones especificas de los ultimos cambios.

R01–R05 forman una campaña continua con checkpoints guardados. R06–R14 pueden
usar copias de esa partida en directorios independientes bajo build/; se
documentan los preparativos y se evita acreditar requisitos omitidos.

## Disciplina de verificación

- Registrar checkpoints, controles utilizados, flags/variables leídos,
  inventario/equipo y callbacks esperados; señales, waits y deadlines fallan
  explícitamente, nunca cuentan como PASS por cerrar el proceso.
- Las pruebas de desplazamiento utilizan REG_KEYINPUT, no teletransportes ni
  cambios de coordenadas. Se pueden leer los mapas locales para planear rutas.
- Proteger ROM/save originales mediante hashes; todos los saves, logs y
  capturas de pruebas quedan en build/, ignorado. No publicar assets/binarios.
- Mostrar git status antes de cada commit y añadir archivos por nombre.
- Commits pequeños en la rama de T27; no push en esta fase.

Reproducción base: MINGW32, make -C port exe diagnostic-exe test verify-normal
(builds secuenciales). Python del entorno para harness; GDB MINGW32.
Compare: MINGW64 con ARM Binutils 2.43.1, make -C pokeemerald compare
KEEP_TEMPS=1 NODEP=1. Ajustar las pruebas focalizadas por incremento.
