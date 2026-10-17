# Lista de ejecución: completar emerald-pc

Plan y reglas comunes: [plan.md](plan.md). Nada marcado está implementado
por este documento. Tamaño S: 1–2 archivos; M: 3–5. Una tarea que crezca se
divide antes de editar. Las rutas siguientes son relativas al proyecto;
los fuentes upstream se entregan públicamente solo como parches.

## Hito 21 — integrar la base actual

### T01 — revisar la cadena de hitos (M)

- [x] Actualizar referencias remotas y revisar diferencias main → hito 20,
  incluyendo el historial saliente y los 16 parches.
- [x] Resolver hallazgos de revisión en commits propios; registrar cuáles
  afectan código, comportamiento GBA, datos o documentación.
- [x] Reproducir setup y build en checkout aislado y conservar evidencia.

Dependencias: ninguna. Archivos: `setup.ps1`, `port/Makefile`, informe nuevo
en `port/docs/`. Verificación: gates comunes, compare OK y árbol parcheado
idéntico. No tocar el plan anterior del usuario.

### T02 — consolidar main (S)

- [x] Integrar únicamente la cadena revisada; usar fast-forward si sigue
  siendo posible y revisar cualquier divergencia antes de resolverla.
- [x] Comprobar que main contiene el arreglo 0016 y todos los módulos reales,
  sin ROMs, saves, recursos ni binarios en archivos o historial saliente.
- [x] Registrar hash integrado y ramas incluidas; mostrar ls-files antes de una
  publicación solicitada. No hacer force-push ni borrar ramas de respaldo.

Dependencias: T01. Archivos: historial Git e informe de integración.
Verificación: misma batería en main; revisión previa a merge.

### Checkpoint A

- [x] Base integrada verificable; GBA compare OK; test host y combate PASS.

## Hito 22 — estabilidad y aviso de descompresión

### T03 — diagnóstico de fallos útil (M)

- [x] Registrar frame, callbacks, mapa/estado de batalla y registros relevantes
  en builds de diagnóstico, sin volcar ROM/save ni contenido de assets.
- [x] Añadir timeout y detección de falta de avance a los recorridos;
  distinguir espera válida de bloqueo.
- [x] Mantener el ejecutable normal sin scripts ni volcados diagnósticos.

Dependencias: T02. Archivos: `port/frame.c`, `port/input_script.c`, harness
de `port/tests/`, `first-run-report.md`. Verificación: timeout inducido en
fixture propio; recorrido normal sin regresión.

### T04 — resolver `expected 0x10` (M)

- [x] Detener GDB en el rechazo de la cabecera, registrar fuente/destino,
  dirección, consumidor y recurso esperado; identificar la causa real.
- [x] Corregir productor, tabla o consumidor bajo PORT_PC según la evidencia;
  no silenciar ni aceptar cualquier cabecera para ocultar el fallo.
- [x] Repetir el mismo combate sin ese aviso y con sprites/fondos visibles.

Dependencias: T03. Archivos posibles: `port/bios.c`, pipeline de
`port/Makefile` o un parche upstream (elegir después del diagnóstico), test
focalizado e informe. Verificación: stream válido, fallo malformado
controlado, combate y capturas locales; compare si hay parche.

### T05 — revisar vidas útiles y cargas síncronas (M por lote)

- [x] Inventariar callbacks registrados que retienen datos liberables y loops
  de carga que dependen de DMA/VBlank, con archivos y ruta alcanzable.
- [x] Corregir una ruta comprobada por commit, limitando cada lote a cinco
  archivos; conservar naming, bolsa y transición ya corregidos.
- [x] Añadir regresión de entrada/salida del menú o transición afectada.

Dependencias: T03. Archivos: informe + parches de los consumidores hallados
+ harness focalizado. Verificación: repetición de abrir/cerrar la ruta,
timeout y GDB sin acceso a datos liberados.

Evidencia T05: `callback-inventory.md` (67 archivos, 136 registros y 17
loops candidatos), `callback-lifetime-audit.md` y parches 0018–0020.
Almacenamiento, equipo y resumen tienen fixtures de regresión PASS;
los demás candidatos no se declaran libres de fallos por el inventario.

### Checkpoint B

- [x] Aviso actual explicado/resuelto; mapa y combate estables; sin nuevas
  guardas que simplemente omitan operaciones necesarias del juego.

Repetición tras 0019/0020: victoria frame 33.365, mapa y salida limpia en
37.000 (`build/wild-battle-regression/gdb.log`). Esto cubre el fixture
documentado, no todos los combates ni los 67 candidatos de callbacks.

## Hito 23 — datos del jugador y reinicio

### T06 — guardado completo y recuperación (M)

- [x] Guardar desde el juego, cerrar, reabrir y comprobar mapa, equipo,
  objetos, dinero y progreso en una partida de prueba aislada.
- [x] Simular fallo de escritura/tamaño inválido/corrupción de un slot en
  copias, verificar errores y recuperación del slot válido si corresponde.
- [x] Probar cierre/reset alrededor del guardado sin truncar el original;
  documentar garantías y límites reales de flush/recuperación.

Dependencias: T04. Archivos: `port/host_flash.c`, `port/tests/host_flash_test.c`,
harness de juego, `flash-save.md`. Verificación: reapertura con checksums
y campos semánticos, no solo tamaño del archivo.

T06: `save_game_smoke.py`, `host_flash_test.c` y `flash-save.md` documentan
dos diálogos, reapertura, corrupción, escritura interrumpida y rechazo de
save no disponible. Cierre e interrupción PASS; T07 verifica reset real
tras los guardados completos. No se prometen garantías frente a cortes
eléctricos ni reset inyectado durante cada byte de escritura.

### T07 — reinicio real del ejecutable (M)

- [x] Verificar la combinación de reset y un reset solicitado por el juego,
  con ruta que tenga espacios y cwd fuera del proyecto.
- [x] Confirmar un único proceso nuevo, cierre de audio/save, carga válida
  y velocidad reiniciada a 1×.
- [x] Comprobar fallo de CreateProcess con error útil y recursos cerrados.

Dependencias: T06. Archivos: `port/port_reset.c`, `port/main.c`, test/harness,
informe. Verificación: test con spawner y prueba de subprocess real aislado.

T07: `reset_game_smoke.py`, `reset.md`, parche 0022; dos rutas de reset
normal PASS, 1× y save intacto; fallo CreateProcess real con error 2 y
cleanup atexit. La entrada DoSoftReset se prepara en GDB, no con un evento
de historia. Cwd externo y ruta con espacios comprobados.

## Hito 24 — registros, eventos e interrupciones

### T08 — inventario MMIO y contrato de escrituras (S)

- [x] Enumerar reads/writes usados por Emerald: IE/IME/IF, timers, DMA,
  vídeo, sonido, GPIO y serie; separar sondeo de efectos secundarios.
- [x] Proponer hooks para writes que el sondeo no puede observar; definir
  ancho, orden, ownership y comportamiento de reset.
- [x] Definir eventos y pruebas esperadas sin introducir un emulador ARM.

Dependencias: T02. Archivos: nuevo `port/docs/register-model.md`, headers
host si hace falta. Verificación: referencias concretas a consumidores
upstream y revisión del contrato antes de implementarlo.

T08: `register-model.md`, `register-inventory.md` y `audit_registers.py`:
75 nombres de registros, consumidores indirectos revisados y contrato IRQ/
MMIO. Incluye bootstrap y matriz de pruebas. Fue la base del modelo implementado en T09–T13; los contratos y límites
actuales están en register-model.md, video-calendar.md y dma-model.md.

### T09 — despacho IRQ correcto (M)

- [x] Modelar solicitudes pendientes, habilitación IE/IME y acknowledgements
  IF con side effects observables, respetando prioridades documentadas.
- [x] Separar flag de espera cooperativa de entrega de callbacks enmascarados;
  evitar callbacks duplicados o reentrada de juego desde otro hilo.
- [x] Probar IRQ habilitada, enmascarada, pendiente y reconocida.

Dependencias: T08, T05. Archivos: nuevo módulo `port/port_irq.*`, `frame.c`,
test, parche de writes si el inventario lo exige. Verificación: suite IRQ
y regresiones; no asumir que RAM normal implementa IF.

T09: `port_irq.*`, suites irq/frame, parches 0023/0024. Sin VBlank
incondicional ni flags BIOS ficticios bajo IME=0. Bootstrap forced blank;
14 suites PASS, combate con victoria/regreso y compare OK. Reproducción
con 24 parches y árbol idéntico. T10 y el calendario de
líneas/eventos timer/DMA se verifican en los apartados siguientes.

### T10 — IntrWait/Halt con máscaras (M)

- [x] Implementar discard y máscaras de IntrWait sobre el modelo IRQ;
  VBlankIntrWait y Halt conservan eventos SDL y salida limpia.
- [x] Una IRQ diferente no satisface una espera específica; se conserva una
  IRQ previa solo cuando corresponde al argumento discard.
- [x] Probar eventos diferidos, cierre de ventana durante espera y evitar
  que una IRQ enmascarada ejecute su callback.

Dependencias: T09. Archivos: `bios.c`, `port_irq.*`, tests BIOS/IRQ.
Verificación: fixtures de eventos, sin esperas infinitas en test.

T10: bios/irq suites prueban masks/discard, evento distinto, IRQ enmascarada,
Halt con IME=0 y wake ya reconocido. El cierre durante espera usa un pump
sintético; frame suite verifica SDL_QUIT real en el servicio. 14 suites,
normal sin combate al salir, batalla y recuperación de save PASS. Esta fue la base
de T11–T13, ahora verificados abajo con precisión temporal limitada.

### T11 — calendario completo de líneas (M)

- [x] Definir y ejecutar líneas visibles y VBlank, transiciones VCOUNT/
  DISPSTAT y eventos HBlank sin renderizar fuera del área visible.
- [x] Comparar el orden DMA/IRQ/callback con referencias de hardware y los
  consumidores upstream; no asumir HBlank activo igual en toda región.
- [x] Mantener cadencia y velocidad, y medir coste frente a la base integrada.

Dependencias: T09. Archivos: `frame.c`, `port_dma.c`, `frame_test.c`, informe.
Verificación: traza de un frame entero, scanline effects y combate a 1×/4×.

### T12 — timers observables e IRQ (M)

- [x] Reescribir recarga, incluso con el mismo valor, mediante hooks de los
  consumidores identificados; conservar prescaler/cascada.
- [x] Solicitar IRQ de overflow cuando corresponde y probar enable/disable,
  cambios de recarga/control y overflow múltiple.
- [x] Mantener diagnóstico determinista y documentar granularidad nativa.

Dependencias: T08–T11. Archivos: `port_timer.*`, `timer_test.c`, `frame.c`,
parche de consumidores. Verificación: timers/IRQ y RNG/recorrido conocidos.

### Checkpoint C

- [x] IRQ, waits y calendario pasan; las rutas ya jugables siguen funcionando;
  el informe explica qué precisión temporal se garantiza.

## Hito 25 — completar DMA usado por el juego

### T13 — DMA y control de canales (M por lote)

- [x] Auditar escrituras directas a DMA; capturar armado/desarmado observables,
  conteo cero, máscaras y recarga en los canales realmente usados.
- [x] Probar IRQ de fin, repetición, incrementos/decrementos/fijos y triggers
  NOW/VBlank/HBlank según el calendario de T11.
- [x] Determinar si FIFO/special timing requiere emulación o queda sustituido
  correctamente por la ruta m4a host; dejar contrato explícito.

Dependencias: T08–T12. Archivos: `port_dma.*`, `dma_test.c`, `frame.c`, parche
de writes. Verificación: matriz por canal + transiciones/sonido sin regresión.

## Hito 26 — fidelidad gráfica

### T14 — modos bitmap 3 y 4 (M)

- [x] Dibujar sus formatos de color y selección de página según registros,
  usando fixtures sintéticos y BG2 afín cuando corresponda.
- [x] Integrar prioridad, ventanas, color y objetos; comprobar índice/color
  cero según el modo, no asumir transparencia de fondos de texto.
- [x] Probar extremos de VRAM y cambio de página entre frames.

Dependencias: T11, T13. Archivos: `port_ppu.c`, `ppu_test.c`, informe PPU.
Verificación: fixtures exactos por píxel y comparación local de escenas que
realmente usen esos modos; no afirmar que Emerald usa todos ellos.

### T15 — modo bitmap 5 (M)

- [x] Implementar dimensiones, página y color directo con clipping/backdrop.
- [x] Comprobar transformaciones de BG2 y restricciones de tiles OBJ en
  bitmap mediante referencia, no reutilizar límites de texto a ciegas.
- [x] Probar coordenadas negativas/bordes y combinación con efectos.

Dependencias: T14. Archivos: PPU, pruebas e informe. Verificación: fixtures
exactos y ninguna lectura fuera de la región VRAM modelada.

### T16 — prioridades, ventanas y mezcla (M)

- [x] Revisar empates BG/OBJ, orden OAM, transparencia y elección de segunda
  capa con más de dos candidatos.
- [x] Cubrir OBJ semitransparente, OBJWIN, efectos dentro/fuera de ventanas,
  bordes invertidos y clipping/forced blank con pruebas combinadas.
- [x] Comparar escenas de intro y combate; corregir diferencias concretas.

Dependencias: T14–T15. Archivos: PPU, `ppu_test.c`, informe visual.
Verificación: fixtures de capas y capturas alineadas por estado de escena.

### T17 — afines y mosaico (M)

- [x] Medir mosaico OBJ respecto a origen/posición, tamaños y clipping;
  reemplazar aproximaciones cuando una referencia demuestre diferencia.
- [x] Cubrir afines con matriz negativa, doble tamaño, wraparound y cambios
  de referencia/matriz entre líneas.
- [x] Conservar selección del inicial centrada y scanline effects existentes.

Dependencias: T16. Archivos: PPU, prueba PPU, informe.
Verificación: fixtures signed/overflow/bordes y escenas antes/después.

### Checkpoint D

- [x] Los modos y efectos implementados tienen pruebas por píxel; la matriz
  visual distingue errores conocidos de escenas todavía no comparadas.

## Hito 27 — completar BIOS requerida

### T18 — exactitud de copia, cálculo y descompresión (M por lote)

- [x] Inventariar las llamadas BIOS usadas, incluidas variantes actualmente
  ausentes o stubs, y priorizar consumidores alcanzables.
- [x] Comparar divisiones/extremos, raíces/ángulos/matrices y alineación/
  conteos de copias con vectores de referencia obtenidos legalmente.
- [x] Corregir una familia por commit con fixtures propios; jamás incorporar
  implementación de BIOS al repo público.

Dependencias: T04, T09. Archivos: `bios.c`, `bios_test.c`, `bios.md` y patch
del consumidor solo si hace falta. Verificación: resultados numéricos, no
solo ausencia de excepción.

Evidencia T11–T18 (2026-10-11): video-calendar.md, dma-model.md,
ppu-model.md, bios-inventory.md y bios.md. 17 suites host PASS; normales y
recorridos de combate 1×/4× PASS; recuperación de save PASS; compare GBA OK.
Reproducción aislada de 29 parches con árbol idéntico y build/tests PASS.
Revisión y logs en milestones-24-27-review.md. Capturas solo en build/.
Los contratos son de un port cooperativo: no se declara precisión de CPU ARM,
conformidad universal BIOS ni comparación física de todas las escenas.
T19 y las tareas posteriores continúan abiertas; no se declara completo el
hito 27 entero ni todo el juego.

### T19 — RegisterRamReset por flags (M)

- [x] Resetear regiones/registros GBA solicitados con la exclusión que
  requieren pila/estado host; no borrar heap/stack nativos ni ROM original.
- [x] Restablecer módulos internos coherentemente (DMA/IRQ/timers/PSG),
  sin introducir referencias a un modelo anterior al reset.
- [x] Probar cada flag y combinaciones usadas en arranque/reinicio.

Dependencias: T12, T13, T18. Archivos: `bios.c`, módulo coordinador de reset,
pruebas y documento. Verificación: canarios de regiones y reset real de T07.

## Hito 28 — RTC y tiempo del juego

### T20 — RTC host (M por incremento)

- [x] Proporcionar fecha/hora, presencia y errores mediante capa host de RTC
  compatible con las funciones siirtc usadas por el juego.
- [x] Persistir desfase/configuración en saves/; pruebas con reloj inyectado,
  avance de días y retroceso del reloj sin acelerar con 2×–4×.
- [x] Verificar reloj del dormitorio y un evento diario/berries real;
  documentar desfases/zonas horarias y compatibilidad con saves anteriores.

Dependencias: T06, T08, T19. Archivos: nuevo `port/port_rtc.*`, test RTC,
parche siirtc, informe. Separar API y eventos reales en commits distintos.
Verificación: fecha/hora deterministas y recorrido diario aislado.

## Hito 29 — sonido fiable

### T21 — PCM/secuenciador m4a (M por familia)

- [x] Comparar música/efectos/gritos en fixtures y referencias locales:
  tempo, pitch, pan, ADSR, bucles, compresión y reverberación.
- [x] Revisar límites, fin de muestras y comandos de patrones; corregir
  discrepancias sin copiar código ARM al repositorio.
- [x] Guardar WAV/mediciones solo en build/ y registrar resultado de escucha.

Dependencias: T04, T12, T18. Archivos: `m4a_engine.*`, prueba m4a, informe.
Verificación: vectores sintéticos y escenas musicales identificadas.

### T22 — PSG y bancos de onda (M)

- [x] Capturar writes de bancos y triggers, incluidos cambios múltiples
  entre frames; conservar ambos bancos según comportamiento documentado.
- [x] Verificar square/sweep/envelope/length/noise y routing, más secuencias
  reales de escrituras usadas por m4a.
- [x] Probar que apagar/encender/resetear canales no conserva estado espurio.

Dependencias: T08, T12, T21. Archivos: `port_psg.*`, test PSG, patch de writes,
informe. Verificación: wave banks y fases con datos propios.

Evidencia T19–T22 (2026-10-11): `bios.md` T19, `rtc.md`,
`audio-model.md` y `milestones-27-29-review.md`. 19 suites, reset real,
reloj del dormitorio/berry/evento diario, 1.134 muestras PCM contra ARM,
PSG con writes reales y dos bancos, WAV locales y escucha del usuario.
Builds normal/diagnóstico y reproducción de 31 parches PASS; compare OK.
T23 se verifica por separado en audio-output.md; no se declara equivalencia
por ciclo ni campaña completa.

### T23 — salida SDL, pausa y velocidad (M)

- [x] Probar silencio sin dispositivo, reconexión/errores y cierre/reset;
  resolver comportamiento de audio al abrir el menú de velocidad.
- [x] Medir duración, clipping, discontinuidades y cola a 1×–4×; audio rápido
  conserva la decisión de subir el tono.
- [x] Validar escucha de título, menú, combate y gritos; registrar fallos
  restantes sin confundir RMS distinto de cero con fidelidad.

Dependencias: T07, T21–T22. Archivos: `port_audio.*`, tests audio/frame,
informe. Verificación: backend falso + dispositivo real.

Evidencia T23 (2026-10-11): audio-output.md; backend falso, 16 escenas/velocidades
con SDL real, escucha confirmada por el usuario, reset real, 19 suites y compare OK.
Hot-unplug físico no probado; límites de interpolación/driver documentados.

## Hito 30 — ampliar cobertura de juego

Cada escenario se convierte en una subprueba y commit; no implementar
toda la matriz de una vez. Los fixes encontrados respetan PORT_PC.

### T24 — variantes de combate salvaje (M por escenario)

- [x] Cubrir victoria, derrota, huida y captura con Pokémon/recursos distintos.
- [x] Exigir outcome correcto y retorno al mapa o centro correspondiente,
  equipo/HP/items coherentes y cierre limpio.
- [x] Convertir cada excepción nueva en repro, diagnóstico GDB y regresión.

Dependencias: T04–T06, T13, T16–T23. Archivos: harness de `port/tests/`,
informe y patch del fallo hallado. Verificación: no basta `exit=0`.

Evidencia T24: gameplay-matrix.md; cuatro outcomes y estado semántico PASS,
parche 0032 Master Ball, compare OK y árbol limpio idéntico.

### T25 — entrenadores y mecánicas de combate (M por escenario)

- [x] Cubrir entrenador, rival, gimnasio y doble combate offline.
- [x] Probar cambio de Pokémon, estados, habilidades y selección de objetos/
  movimientos; añadir un caso de batalla larga.
- [x] Registrar dinero/experiencia/evolución y progreso esperado tras victoria.

Dependencias: T24. Archivos: harness, informe y fixes localizados.
Verificación: fixtures controlados y observación semántica de resultados.

Evidencia T25: gameplay-matrix.md y trainer_battle_smoke.py (9 escenarios),
parches 0033–0035, compare OK, XP/dinero/flags/retorno comprobados.

### T26 — menús, PC y almacenamiento (M por escenario)

- [x] Probar depósito/retiro de objetos y Pokémon, cambio de caja/equipo,
  resumen, Pokédex, bolsa y opciones con abrir/cerrar repetido.
- [x] Cubrir evolución, aprendizaje de movimiento y cambio de nombre sin
  callbacks o sprites reteniendo datos liberados.
- [x] Guardar/reabrir tras operaciones de PC y comprobar los contenidos.

Dependencias: T05–T07, T24–T25. Archivos: harness por escenario, informes y
fixes. Verificación: datos antes/después y timeout en transiciones.

### T27 — campaña y contenidos posteriores (M por tramo)

- [x] Crear matriz de rutas/ciudades, interiores, cuevas, surf/bici,
  scripts de historia y cargas de mapas; usar saves locales de prueba.
- [ ] Completar un recorrido hasta Liga/créditos y revisar Concursos,
  crianza, Safari y Battle Frontier por tramos separados.
- [x] Mantener catálogo de casos cubiertos y pendientes, sin versionar saves
  ni afirmar cobertura exhaustiva de todas las combinaciones del juego.

Dependencias: T20, T24–T26. Archivos: `port/tests/` y matriz en `port/docs/`.
Verificación: checkpoints de progreso y regresiones por cada fallo nuevo.

Evidencia T27: [matriz](../gameplay-matrix.md),
[campaña](../campaign-progress.md) y [pendientes](t27-remaining.md).
La campaña continua natural completa R01–R04 y las ocho medallas. R05 es
parcial: Wally, Calle Victoria, Liga y Sidney PASS; Phoebe derrota al equipo.
La partida volvió con Bicicleta Carrera a Pilar Celeste 2F; piso agrietado,
resto del Alto Mando y créditos pendientes. R06–R15 siguen abiertos.
Los segmentos anteriores de Liga/Hall of Fame con equipo preparado no
cierran la campaña natural. No se cierra Checkpoint E.

### Checkpoint E — juego individual

- [ ] Matriz de campaña, save, RTC, gráficos y audio completada con evidencia;
  lista explícita de restricciones todavía presentes.

## Hito 31 — experiencia y reproducción local

### T28 — mandos y remapeo (M por incremento)

- [x] Añadir backend SDL de mandos con hotplug/foco y asignación clara.
- [x] Persistir remapeo fuera de Git y evitar teclas pegadas/conflictos con P.
- [x] Probar teclado, mando, desconexión y reset sin romper input de diagnóstico.

Dependencias: T23–T26. Archivos: módulo input host, frame, SDL loader, test
input y configuración; dividir UI/configuración si supera cinco archivos.
Verificación: backend falso y mando disponible; declarar manual pendiente
si no hay hardware, sin inventar aprobación.

Evidencia T28: controller-input.md, 21 suites, mando virtual SDL real y
reset/normal/PC PASS. SDL enumera 0 mandos físicos; validación física pendiente.

### T29 — arranque reproducible y documentación actual (M)

- [ ] Probar setup repetido, instalación limpia, paths con espacios y ejecución
  fuera del cwd; distinguir dependencias de build y ejecución.
- [ ] Actualizar bios.md/arm-replacements.md y matriz de soporte con lo real;
  detectar runtime equivocado, ROM/save inválidos con mensajes útiles.
- [ ] Preparar script local de verificación/restauración del entorno; ningún
  paquete publicado incluirá ROM, assets ni ejecutable enlazado del juego.

Dependencias: checkpoint E. Archivos: `setup.ps1`, script propio de checks,
`toolchain.md`, docs BIOS/ARM. Verificación: arranque normal en entorno
reproducido; no añadir `.github/` ni otras rutas fuera del contrato del repo.

## Hito 32 — enlace y funciones externas

### T30 — especificar backend de enlace (S)

- [ ] Inventariar consumidores serie/RFU, formatos, sincronización y casos
  de trade/batalla; separar cable, wireless y multiboot/GameCube.
- [ ] Diseñar transporte de dos instancias y protocolo con timeouts, validación
  y desconexión; definir qué sigue siendo stub hasta pasar pruebas.
- [ ] Descomponer implementación en lotes concretos de hasta cinco archivos.

Dependencias: T09–T12, T25–T27. Archivos: spec de enlace e inventario de ARM.
Verificación: revisión del protocolo; sin falsificar éxito de hardware.

### T31 — intercambio entre dos instancias (M por lote)

- [ ] Implementar el caso local mínimo de trade con saves separados.
- [ ] Verificar Pokémon enviados/recibidos, desconexión y persistencia.
- [ ] Mantener juego individual funcional sin backend activo.

Dependencias: T30. Archivos: transporte propio, stubs/loader y parches/tests
identificados en T30. Verificación: dos procesos y validación de ambos saves.

### T32 — batalla enlazada (M por lote)

- [ ] Implementar flujo de entrada, comandos y cierre de batalla de dos hosts.
- [ ] Detectar divergencia, pérdida de conexión y timeouts sin colgar el juego.
- [ ] Comprobar resultado y regreso de ambas instancias.

Dependencias: T31. Archivos: backend, parches/tests según spec.
Verificación: dos procesos con seed y traza de comandos.

### T33 — RFU/multiboot/GameCube (S de diseño; M por piloto)

- [ ] Determinar qué funciones usan datos/protocolos y cuáles descargan código
  ARM; identificar las que un port nativo no puede ejecutar directamente.
- [ ] Especificar un piloto RFU y una decisión explícita para ejecución ARM:
  backend separado o soporte deshabilitado documentado.
- [ ] Implementar solo capacidades con contrato y test real; conservar error
  seguro para accesorios aún no soportados y mantener pendientes visibles.

Dependencias: T30–T32. Archivos: spec, backend/patch/tests del piloto.
Verificación: no marcar «compatible» a partir de stubs. La ejecución de
programas ARM externos necesita diseño adicional antes de programar.

## Hito 33 — migración futura a 64 bits

### T34 — inventario de direcciones y layouts (S)

- [ ] Enumerar casts puntero/u32, `.4byte`, asserts/sizeof y datos serializados
  con consumidores concretos; conservar resultados medidos de i686/x64.
- [ ] Definir representación GBA de 32 bits y resolución a punteros host,
  sin convertir el save en estructuras de 64 bits accidentalmente.
- [ ] Generar lotes pequeños con riesgo/archivo/prueba explícitos.

Dependencias: checkpoint E, T29. Archivos: nueva spec y decisión de punteros.
Verificación: inventario reproducible; reservar memoria baja no se acepta
como solución a layouts de 64 bits.

### T35 — piloto de datos x86-64 (M)

- [ ] Convertir/resolver una tabla representativa y adaptar sus consumidores,
  sin publicar la tabla ni assets originales.
- [ ] Probar referencias, alineación, navegación y save sin cambios de formato.
- [ ] Conservar i686 pasando las mismas pruebas.

Dependencias: T34. Archivos: herramienta propia de conversión/resolución,
test y parches de consumidores definidos por el piloto.
Verificación: resultados equivalentes entre arquitecturas, no solo enlace.

### T36 — migración por lotes (M por lote)

- [ ] Adaptar máximo cinco archivos/consumidores por lote inventariado.
- [ ] Eliminar truncamientos y supuestos de ancho con tests de datos reales
  locales y fixtures sintéticos públicos propios.
- [ ] Llegar a enlace/arranque x64 y repetir la matriz de juego individual;
  no declarar terminada la migración con el piloto de una sola tabla.

Dependencias: T35. Archivos: lotes que genere T34; Makefile/patches/informes.
Verificación: suites de ambos hosts + regresiones semánticas equivalentes.

## Hito 34 — Linux/macOS

### T37 — backends y plataformas (M por piloto/lote)

- [ ] Aislar memoria, archivos, carga SDL y relanzamiento de Win32 con contratos
  mínimos; compartir juego, PPU y audio.
- [ ] Crear primero piloto Linux y después macOS con toolchain y arquitectura
  verificadas; no asumir disponibilidad de i686 en cada sistema.
- [ ] Repetir matriz de juego, save y reset por plataforma; documentar soporte
  únicamente cuando se ejecute allí.

Dependencias: T29, T35–T36 si la plataforma requiere 64 bits.
Archivos: un backend y su test por lote, Makefile, documento del entorno.
Verificación: pruebas en host real y compatibilidad de saves; separar pilotos.

## Hito 35 — cierre del plan

### T38 — matriz final y mantenimiento (M)

- [ ] Revisar cada tarea y sublote con su evidencia; marcar implementado,
  aproximado, pendiente o deshabilitado con motivo y próximo paso.
- [ ] Repetir gates finales, auditar archivos e historial a publicar y
  confirmar reproducción desde setup con la versión upstream fijada.
- [ ] Actualizar README/controles/limitaciones y conservar plan de regresión
  para futuras modificaciones; no declarar probado lo que falta verificar.

Dependencias: checkpoint E y todos los hitos adicionales que se declaren
soportados. Archivos: README, toolchain, matriz de compatibilidad e informe.
Verificación: review final, compare OK, suites y recorridos seleccionados.

### Checkpoint F

- [ ] Estado final revisable, reproducible y con límites explícitos; cualquier
  tarea no ejecutada sigue abierta en esta lista.
