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
  en `campaign-progress.md`. R02–R15 siguen abiertos.
- [x] R02: desplazamientos reales y puzzles para los primeros cuatro gimnasios;
  Devon/Peeko/Briney, Aqua en Slateport, meteorito y Magma en Mt. Chimney.
  Comprobar rechazo de pasos bloqueados antes de completar su requisito y
  acceso después; obtener medallas mediante NPC, conservando el mismo save.
  Evidencia: checkpoints de Roxanne/Brawly/Wattson/Flannery y sus recargas;
  `r02-maxie-meteorite`, gating del museo/teleférico y regresiones naturales
  de Rock Smash, Meteor Falls, Jagged Pass y el puzzle/combate de Flannery.
  Detalle y límites de los intentos: `campaign-progress.md`. R03–R15 abiertos.
- [ ] R03: Norman/Surf, Weather Institute/Castform, rival/Fly y Fortree/Devon
  Scope. Cruzar los obstáculos con input y los movimientos/herramientas reales.
- [ ] R04: Mt. Pyre, escondites Aqua/Magma, Mossdeep/Space Center, Dive,
  Seafloor Cavern, Sky Pillar/Rayquaza, Sootopolis y octava medalla. Eventos y
  desbloqueos deben proceder de scripts; verificar sus condiciones previas.
- [ ] R05: Waterfall, Victory Road, acceso a Liga, ocho medallas y créditos
  desde esa misma partida; sin warps del harness ni equipo preparado. Recarga
  final: game-clear, equipo y Hall of Fame válidos. Capturas privadas.
- [ ] R06: crianza por pasos reales, generación de huevo, recogida por diálogo,
  eclosión mediante desplazamientos y conservación tras save/reload. No marcar
  readiness, contador de huevo ni especie manualmente.
- [ ] R07: Safari con agotamiento real de sus 30 bolas y salida correcta;
  paseo que consuma los 500 pasos, además del test previo de la rutina de pasos.
- [ ] R08: Battle Tower: admisión, selección legal, racha completa, registro
  y recompensa; reanudación/recarga y salida de una derrota.
- [ ] R09: Factory: alquileres, intercambios y racha/recompensa mediante UI.
- [ ] R10: Palace: selección automática de movimientos y racha/recompensa.
- [ ] R11: Arena: juicio, restricciones de cambio y racha/recompensa.
- [ ] R12: Dome: inscripción, cuadro/elección del equipo y torneo/recompensa.
- [ ] R13: Pike: elecciones de salas, encuentros/estados y circuito/recompensa.
- [ ] R14: Pyramid: exploración de pisos, bolsa propia, ascenso y recompensa.
- [ ] R15: repetición de regresiones afectadas, build normal/diagnóstico,
  suites host, compare GBA OK y reproducción limpia de cualquier parche nuevo.
  Revisar matriz/informes y cerrar únicamente lo que tenga evidencia.

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
