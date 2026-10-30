# T27 y Checkpoint E: auditoria de cierre

Fecha: 30-10-2026. Alcance: R01-R15 de tasks/t27-remaining.md y la matriz
individual de Checkpoint E. T29 y tareas posteriores no se acreditan aqui.
Los logs, ROM, saves y capturas citados permanecen en build/, ignorado.

## Evidencia y alcance

| Criterio | Evidencia inspeccionada | Resultado |
| --- | --- | --- |
| R01-R04: historia continua, ocho medallas, desplazamientos y requisitos por scripts | Checkpoints y replays catalogados en campaign-progress.md; r05-the-end.json conserva las ocho medallas. Los desbloqueos y puzzles tienen pruebas previas/posteriores descritas por tramo | PASS; la partida continua conserva su procedencia, sin conceder flags, niveles ni objetos por GDB |
| R05: Liga, Hall of Fame, creditos y recarga | t27-wallace-champion-replay.log; t27-natural-ending-reload.log comprueba game-clear, equipo y checksums Hall of Fame | PASS; save sin reescribir |
| R06: crianza natural | t27-r06-hatch.log, t27-r06-hatched-reload.log; checkpoint r06-oddish-hatched | PASS; huevo/eclosion por pasos y cuatro recargas documentadas |
| R07: Safari | t27-r07-balls.log, t27-r07-steps.log y sus recargas; checkpoints de ambas salidas | PASS; 30 bolas y 500 pasos agotados |
| R08: Torre | r08-tower-seven-wins.json; t27-r08-seven-wins-current-reload.log; pausa/reanudacion y derrota catalogadas | PASS; racha7 y PB0->1 |
| R09: Factory | t27-r09-factory-resume.log, t27-r09-factory-seven-reload.log; r09-factory-open-seven-wins.json | PASS; siete victorias, seis intercambios, pausa/reanudacion y PB0->3 |
| R10: Palace | t27-r10-palace-level40-retry.log; natural-campaign-replay-r10-palace-retry/campaign.log; t27-r10-palace-seven-reload.log | PASS; siete victorias, 864 callbacks automaticos, cero movimientos manuales, racha7 y PB1->5 |
| R11: Arena | t27-r11-arena-third-loss-isolated.log; t27-r11-arena-seven-reload.log; checkpoint final | PASS; restriccion de cambio, juicio, racha7 y PB1->2 |
| R12: Dome | t27-r12-dome-round.log; t27-r12-dome-champion-reload.log; checkpoint final | PASS; cuadro, dos elegidos, cuatro victorias, campeonato y PB1->2 |
| R13: Pike | t27-r13-pike-sixth-attempt.log; t27-r13-pike-complete-reload.log; checkpoint final | PASS; 14 salas, encuentros, paralisis/curacion y PB1->2 |
| R14: Pyramid | t27-r14-pyramid-round-retry.log; t27-r14-pyramid-complete-reload.log; checkpoint final | PASS; bolsa propia, siete pisos, cima y PB1->6 |
| Concursos | t27-final-contest-regression.log y content-contest/gdb.log | PASS dirigido: cinco apelaciones y retorno; no prueba inscripcion natural |
| R15: reproduccion | t27-clean-series53-setup.log, t27-clean-series53-gba-build.log, t27-clean-series53-pc-resume.log, t27-clean-series53-boot.log | Base + 53 parches reproduce arbol upstream; compare OK, exe/diagnostic/test/verify-normal, 21 suites y arranque 2000 frames con salida limpia |
| Regresiones afectadas | t27-final-animation-regression.log y recorrido Pyramid actual | PASS: finales de animacion y bolsa Pyramid; save privado intacto |
| Guardado / PC | t26-pc-{deposit,withdraw,box,items}.log y recargas naturales de campaña/Frontier | PASS; contenidos comprobados tras reiniciar, no solo cierre sin error |
| RTC | review-rtc-game.log; rtc-game-regression/gdb.log; suite rtc en reproduccion limpia | Reloj, crecimiento de baya, evento diario, retroceso y fecha invalida; limites en rtc.md |
| Graficos | Suites ppu/bitmap/ppu_priority/ppu_affine en build limpio; escenas y capturas catalogadas en ppu-model.md | PASS para vectores y escenas descritos; no equivalencia exhaustiva contra hardware |
| Audio | t21-arm-reference.log, t23-output.log, suites limpias; escucha confirmada por usuario en T21/T23 | 1134 muestras ARM de referencia; 16 escenas/velocidades con salida SDL; audio reconocible confirmado |

Las pruebas de Frontier distinguen derrota normal de circuito completado.
Un wrapper que imprime PASS no basta: se inspeccionaron outcomes, contadores,
recompensas y checkpoints finales. Palace registra [1,1,1,1,1,1,1], y el
verificador Continue compara todos los campos Frontier guardados, equipo,
HP, PP, movimientos, objetos e inventario y exige que el archivo no cambie.
El equipo de Palace fue Swampert54, Pelipper52 y Castform40, elegido por UI.
El entrenamiento adicional hasta nivel50 se detuvo al conseguir la victoria:
solo se alcanzo/preservo nivel42; nivel41 tuvo su propia recarga verificada.

## Integridad y reproduccion

El checkout upstream actual conserva el arbol
6cf424548d69a4926deceeea9bd0f7ff36ff6dcb, identico a la reproduccion de
53 parches; no hay modificaciones seguidas sin exportar. Herramientas y logs
locales no seguidos permanecen dentro del checkout ignorado. La reproduccion
reutilizo agbcc instalado y una copia de la ROM propia, todo bajo build/.
La ROM original conserva SHA256
a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af.
La lista de archivos seguidos no incluye ROMs, saves, assets ni binarios.
roms/, saves/, build/ y pokeemerald/ siguen ignorados. No se hizo push.

## Restricciones que permanecen

- No cubre cada mapa, evento opcional, equipo, movimiento o combinacion. Las
  rondas de Frontier no acreditan todos los simbolos ni rachas ilimitadas.
- Concursos tiene fixture dirigido, no una admision natural recorrida.
- Enlace/RFU/multiboot no implementados. El objetivo validado es individual.
- PPU/calendario host sin CPU ARM ni precision por ciclo, open bus o limites
  exactos de tiempo OBJ; no hay comparacion exhaustiva con capturas hardware.
- Audio sin filtros analogicos ni equivalencia completa de todas las canciones;
  los vectores ARM y la escucha prueban solo los casos descritos.
- RTC sin IRQ de alarma; limites de fechas y rutas Windows en rtc.md.
- Mandos probados con backend y dispositivo SDL virtual; hardware fisico pendiente.
- Plataforma Windows i686. x86-64 sigue como trabajo futuro.

T27 y Checkpoint E quedan cerrados dentro de estos criterios verificables.
Las secciones cronologicas antiguas de los informes conservan sus estados
historicos; el resumen actual y esta auditoria determinan el estado final.
