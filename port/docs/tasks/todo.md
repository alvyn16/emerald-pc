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
- [ ] Añadir timeout y detección de falta de avance a los recorridos;
  distinguir espera válida de bloqueo.
- [x] Mantener el ejecutable normal sin scripts ni volcados diagnósticos.

Dependencias: T02. Archivos: `port/frame.c`, `port/input_script.c`, harness
de `port/tests/`, `first-run-report.md`. Verificación: timeout inducido en
fixture propio; recorrido normal sin regresión.

### T04 — resolver `expected 0x10` (M)

- [ ] Detener GDB en el rechazo de la cabecera, registrar fuente/destino,
  dirección, consumidor y recurso esperado; identificar la causa real.
- [ ] Corregir productor, tabla o consumidor bajo PORT_PC según la evidencia;
  no silenciar ni aceptar cualquier cabecera para ocultar el fallo.
- [ ] Repetir el mismo combate sin ese aviso y con sprites/fondos visibles.

Dependencias: T03. Archivos posibles: `port/bios.c`, pipeline de
`port/Makefile` o un parche upstream (elegir después del diagnóstico), test
focalizado e informe. Verificación: stream válido, fallo malformado
controlado, combate y capturas locales; compare si hay parche.

### T05 — revisar vidas útiles y cargas síncronas (M por lote)

- [ ] Inventariar callbacks registrados que retienen datos liberables y loops
  de carga que dependen de DMA/VBlank, con archivos y ruta alcanzable.
- [ ] Corregir una ruta comprobada por commit, limitando cada lote a cinco
  archivos; conservar naming, bolsa y transición ya corregidos.
- [ ] Añadir regresión de entrada/salida del menú o transición afectada.

Dependencias: T03. Archivos: informe + parches de los consumidores hallados
+ harness focalizado. Verificación: repetición de abrir/cerrar la ruta,
timeout y GDB sin acceso a datos liberados.

### Checkpoint B

- [ ] Aviso actual explicado/resuelto; mapa y combate estables; sin nuevas
  guardas que simplemente omitan operaciones necesarias del juego.

## Hito 23 — datos del jugador y reinicio

### T06 — guardado completo y recuperación (M)

- [ ] Guardar desde el juego, cerrar, reabrir y comprobar mapa, equipo,
  objetos, dinero y progreso en una partida de prueba aislada.
- [ ] Simular fallo de escritura/tamaño inválido/corrupción de un slot en
  copias, verificar errores y recuperación del slot válido si corresponde.
- [ ] Probar cierre/reset alrededor del guardado sin truncar el original;
  documentar garantías y límites reales de flush/recuperación.

Dependencias: T04. Archivos: `port/host_flash.c`, `port/tests/host_flash_test.c`,
harness de juego, `flash-save.md`. Verificación: reapertura con checksums
y campos semánticos, no solo tamaño del archivo.

### T07 — reinicio real del ejecutable (M)

- [ ] Verificar la combinación de reset y un reset solicitado por el juego,
  con ruta que tenga espacios y cwd fuera del proyecto.
- [ ] Confirmar un único proceso nuevo, cierre de audio/save, carga válida
  y velocidad reiniciada a 1×.
- [ ] Comprobar fallo de CreateProcess con error útil y recursos cerrados.

Dependencias: T06. Archivos: `port/port_reset.c`, `port/main.c`, test/harness,
informe. Verificación: test con spawner y prueba de subprocess real aislado.

## Hito 24 — registros, eventos e interrupciones

### T08 — inventario MMIO y contrato de escrituras (S)

- [ ] Enumerar reads/writes usados por Emerald: IE/IME/IF, timers, DMA,
  vídeo, sonido, GPIO y serie; separar sondeo de efectos secundarios.
- [ ] Proponer hooks para writes que el sondeo no puede observar; definir
  ancho, orden, ownership y comportamiento de reset.
- [ ] Definir eventos y pruebas esperadas sin introducir un emulador ARM.

Dependencias: T02. Archivos: nuevo `port/docs/register-model.md`, headers
host si hace falta. Verificación: referencias concretas a consumidores
upstream y revisión del contrato antes de implementarlo.

### T09 — despacho IRQ correcto (M)

- [ ] Modelar solicitudes pendientes, habilitación IE/IME y acknowledgements
  IF con side effects observables, respetando prioridades documentadas.
- [ ] Separar flag de espera cooperativa de entrega de callbacks enmascarados;
  evitar callbacks duplicados o reentrada de juego desde otro hilo.
- [ ] Probar IRQ habilitada, enmascarada, pendiente y reconocida.

Dependencias: T08, T05. Archivos: nuevo módulo `port/port_irq.*`, `frame.c`,
test, parche de writes si el inventario lo exige. Verificación: suite IRQ
y regresiones; no asumir que RAM normal implementa IF.

### T10 — IntrWait/Halt con máscaras (M)

- [ ] Implementar discard y máscaras de IntrWait sobre el modelo IRQ;
  VBlankIntrWait y Halt conservan eventos SDL y salida limpia.
- [ ] Una IRQ diferente no satisface una espera específica; se conserva una
  IRQ previa solo cuando corresponde al argumento discard.
- [ ] Probar eventos diferidos, cierre de ventana durante espera y evitar
  que una IRQ enmascarada ejecute su callback.

Dependencias: T09. Archivos: `bios.c`, `port_irq.*`, tests BIOS/IRQ.
Verificación: fixtures de eventos, sin esperas infinitas en test.

### T11 — calendario completo de líneas (M)

- [ ] Definir y ejecutar líneas visibles y VBlank, transiciones VCOUNT/
  DISPSTAT y eventos HBlank sin renderizar fuera del área visible.
- [ ] Comparar el orden DMA/IRQ/callback con referencias de hardware y los
  consumidores upstream; no asumir HBlank activo igual en toda región.
- [ ] Mantener cadencia y velocidad, y medir coste frente a la base integrada.

Dependencias: T09. Archivos: `frame.c`, `port_dma.c`, `frame_test.c`, informe.
Verificación: traza de un frame entero, scanline effects y combate a 1×/4×.

### T12 — timers observables e IRQ (M)

- [ ] Reescribir recarga, incluso con el mismo valor, mediante hooks de los
  consumidores identificados; conservar prescaler/cascada.
- [ ] Solicitar IRQ de overflow cuando corresponde y probar enable/disable,
  cambios de recarga/control y overflow múltiple.
- [ ] Mantener diagnóstico determinista y documentar granularidad nativa.

Dependencias: T08–T11. Archivos: `port_timer.*`, `timer_test.c`, `frame.c`,
parche de consumidores. Verificación: timers/IRQ y RNG/recorrido conocidos.

### Checkpoint C

- [ ] IRQ, waits y calendario pasan; las rutas ya jugables siguen funcionando;
  el informe explica qué precisión temporal se garantiza.

## Hito 25 — completar DMA usado por el juego

### T13 — DMA y control de canales (M por lote)

- [ ] Auditar escrituras directas a DMA; capturar armado/desarmado observables,
  conteo cero, máscaras y recarga en los canales realmente usados.
- [ ] Probar IRQ de fin, repetición, incrementos/decrementos/fijos y triggers
  NOW/VBlank/HBlank según el calendario de T11.
- [ ] Determinar si FIFO/special timing requiere emulación o queda sustituido
  correctamente por la ruta m4a host; dejar contrato explícito.

Dependencias: T08–T12. Archivos: `port_dma.*`, `dma_test.c`, `frame.c`, parche
de writes. Verificación: matriz por canal + transiciones/sonido sin regresión.

## Hito 26 — fidelidad gráfica

### T14 — modos bitmap 3 y 4 (M)

- [ ] Dibujar sus formatos de color y selección de página según registros,
  usando fixtures sintéticos y BG2 afín cuando corresponda.
- [ ] Integrar prioridad, ventanas, color y objetos; comprobar índice/color
  cero según el modo, no asumir transparencia de fondos de texto.
- [ ] Probar extremos de VRAM y cambio de página entre frames.

Dependencias: T11, T13. Archivos: `port_ppu.c`, `ppu_test.c`, informe PPU.
Verificación: fixtures exactos por píxel y comparación local de escenas que
realmente usen esos modos; no afirmar que Emerald usa todos ellos.

### T15 — modo bitmap 5 (M)

- [ ] Implementar dimensiones, página y color directo con clipping/backdrop.
- [ ] Comprobar transformaciones de BG2 y restricciones de tiles OBJ en
  bitmap mediante referencia, no reutilizar límites de texto a ciegas.
- [ ] Probar coordenadas negativas/bordes y combinación con efectos.

Dependencias: T14. Archivos: PPU, pruebas e informe. Verificación: fixtures
exactos y ninguna lectura fuera de la región VRAM modelada.

### T16 — prioridades, ventanas y mezcla (M)

- [ ] Revisar empates BG/OBJ, orden OAM, transparencia y elección de segunda
  capa con más de dos candidatos.
- [ ] Cubrir OBJ semitransparente, OBJWIN, efectos dentro/fuera de ventanas,
  bordes invertidos y clipping/forced blank con pruebas combinadas.
- [ ] Comparar escenas de intro y combate; corregir diferencias concretas.

Dependencias: T14–T15. Archivos: PPU, `ppu_test.c`, informe visual.
Verificación: fixtures de capas y capturas alineadas por estado de escena.

### T17 — afines y mosaico (M)

- [ ] Medir mosaico OBJ respecto a origen/posición, tamaños y clipping;
  reemplazar aproximaciones cuando una referencia demuestre diferencia.
- [ ] Cubrir afines con matriz negativa, doble tamaño, wraparound y cambios
  de referencia/matriz entre líneas.
- [ ] Conservar selección del inicial centrada y scanline effects existentes.

Dependencias: T16. Archivos: PPU, prueba PPU, informe.
Verificación: fixtures signed/overflow/bordes y escenas antes/después.

### Checkpoint D

- [ ] Los modos y efectos implementados tienen pruebas por píxel; la matriz
  visual distingue errores conocidos de escenas todavía no comparadas.

## Hito 27 — completar BIOS requerida

### T18 — exactitud de copia, cálculo y descompresión (M por lote)

- [ ] Inventariar las llamadas BIOS usadas, incluidas variantes actualmente
  ausentes o stubs, y priorizar consumidores alcanzables.
- [ ] Comparar divisiones/extremos, raíces/ángulos/matrices y alineación/
  conteos de copias con vectores de referencia obtenidos legalmente.
- [ ] Corregir una familia por commit con fixtures propios; jamás incorporar
  implementación de BIOS al repo público.

Dependencias: T04, T09. Archivos: `bios.c`, `bios_test.c`, `bios.md` y patch
del consumidor solo si hace falta. Verificación: resultados numéricos, no
solo ausencia de excepción.

### T19 — RegisterRamReset por flags (M)

- [ ] Resetear regiones/registros GBA solicitados con la exclusión que
  requieren pila/estado host; no borrar heap/stack nativos ni ROM original.
- [ ] Restablecer módulos internos coherentemente (DMA/IRQ/timers/PSG),
  sin introducir referencias a un modelo anterior al reset.
- [ ] Probar cada flag y combinaciones usadas en arranque/reinicio.

Dependencias: T12, T13, T18. Archivos: `bios.c`, módulo coordinador de reset,
pruebas y documento. Verificación: canarios de regiones y reset real de T07.

## Hito 28 — RTC y tiempo del juego

### T20 — RTC host (M por incremento)

- [ ] Proporcionar fecha/hora, presencia y errores mediante capa host de RTC
  compatible con las funciones siirtc usadas por el juego.
- [ ] Persistir desfase/configuración en saves/; pruebas con reloj inyectado,
  avance de días y retroceso del reloj sin acelerar con 2×–4×.
- [ ] Verificar reloj del dormitorio y un evento diario/berries real;
  documentar desfases/zonas horarias y compatibilidad con saves anteriores.

Dependencias: T06, T08, T19. Archivos: nuevo `port/port_rtc.*`, test RTC,
parche siirtc, informe. Separar API y eventos reales en commits distintos.
Verificación: fecha/hora deterministas y recorrido diario aislado.

## Hito 29 — sonido fiable

### T21 — PCM/secuenciador m4a (M por familia)

- [ ] Comparar música/efectos/gritos en fixtures y referencias locales:
  tempo, pitch, pan, ADSR, bucles, compresión y reverberación.
- [ ] Revisar límites, fin de muestras y comandos de patrones; corregir
  discrepancias sin copiar código ARM al repositorio.
- [ ] Guardar WAV/mediciones solo en build/ y registrar resultado de escucha.

Dependencias: T04, T12, T18. Archivos: `m4a_engine.*`, prueba m4a, informe.
Verificación: vectores sintéticos y escenas musicales identificadas.

### T22 — PSG y bancos de onda (M)

- [ ] Capturar writes de bancos y triggers, incluidos cambios múltiples
  entre frames; conservar ambos bancos según comportamiento documentado.
- [ ] Verificar square/sweep/envelope/length/noise y routing, más secuencias
  reales de escrituras usadas por m4a.
- [ ] Probar que apagar/encender/resetear canales no conserva estado espurio.

Dependencias: T08, T12, T21. Archivos: `port_psg.*`, test PSG, patch de writes,
informe. Verificación: wave banks y fases con datos propios.

### T23 — salida SDL, pausa y velocidad (M)

- [ ] Probar silencio sin dispositivo, reconexión/errores y cierre/reset;
  resolver comportamiento de audio al abrir el menú de velocidad.
- [ ] Medir duración, clipping, discontinuidades y cola a 1×–4×; audio rápido
  conserva la decisión de subir el tono.
- [ ] Validar escucha de título, menú, combate y gritos; registrar fallos
  restantes sin confundir RMS distinto de cero con fidelidad.

Dependencias: T07, T21–T22. Archivos: `port_audio.*`, tests audio/frame,
informe. Verificación: backend falso + dispositivo real.

## Hito 30 — ampliar cobertura de juego

Cada escenario se convierte en una subprueba y commit; no implementar
toda la matriz de una vez. Los fixes encontrados respetan PORT_PC.

### T24 — variantes de combate salvaje (M por escenario)

- [ ] Cubrir victoria, derrota, huida y captura con Pokémon/recursos distintos.
- [ ] Exigir outcome correcto y retorno al mapa o centro correspondiente,
  equipo/HP/items coherentes y cierre limpio.
- [ ] Convertir cada excepción nueva en repro, diagnóstico GDB y regresión.

Dependencias: T04–T06, T13, T16–T23. Archivos: harness de `port/tests/`,
informe y patch del fallo hallado. Verificación: no basta `exit=0`.

### T25 — entrenadores y mecánicas de combate (M por escenario)

- [ ] Cubrir entrenador, rival, gimnasio y doble combate offline.
- [ ] Probar cambio de Pokémon, estados, habilidades y selección de objetos/
  movimientos; añadir un caso de batalla larga.
- [ ] Registrar dinero/experiencia/evolución y progreso esperado tras victoria.

Dependencias: T24. Archivos: harness, informe y fixes localizados.
Verificación: fixtures controlados y observación semántica de resultados.

### T26 — menús, PC y almacenamiento (M por escenario)

- [ ] Probar depósito/retiro de objetos y Pokémon, cambio de caja/equipo,
  resumen, Pokédex, bolsa y opciones con abrir/cerrar repetido.
- [ ] Cubrir evolución, aprendizaje de movimiento y cambio de nombre sin
  callbacks o sprites reteniendo datos liberados.
- [ ] Guardar/reabrir tras operaciones de PC y comprobar los contenidos.

Dependencias: T05–T07, T24–T25. Archivos: harness por escenario, informes y
fixes. Verificación: datos antes/después y timeout en transiciones.

### T27 — campaña y contenidos posteriores (M por tramo)

- [ ] Crear matriz de rutas/ciudades, interiores, cuevas, surf/bici,
  scripts de historia y cargas de mapas; usar saves locales de prueba.
- [ ] Completar un recorrido hasta Liga/créditos y revisar Concursos,
  crianza, Safari y Battle Frontier por tramos separados.
- [ ] Mantener catálogo de casos cubiertos y pendientes, sin versionar saves
  ni afirmar cobertura exhaustiva de todas las combinaciones del juego.

Dependencias: T20, T24–T26. Archivos: `port/tests/` y matriz en `port/docs/`.
Verificación: checkpoints de progreso y regresiones por cada fallo nuevo.

### Checkpoint E — juego individual

- [ ] Matriz de campaña, save, RTC, gráficos y audio completada con evidencia;
  lista explícita de restricciones todavía presentes.

## Hito 31 — experiencia y reproducción local

### T28 — mandos y remapeo (M por incremento)

- [ ] Añadir backend SDL de mandos con hotplug/foco y asignación clara.
- [ ] Persistir remapeo fuera de Git y evitar teclas pegadas/conflictos con P.
- [ ] Probar teclado, mando, desconexión y reset sin romper input de diagnóstico.

Dependencias: T23–T26. Archivos: módulo input host, frame, SDL loader, test
input y configuración; dividir UI/configuración si supera cinco archivos.
Verificación: backend falso y mando disponible; declarar manual pendiente
si no hay hardware, sin inventar aprobación.

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
