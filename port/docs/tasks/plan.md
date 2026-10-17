# Plan: integrar, revisar y completar emerald-pc

Fecha: 2026-10-10. Estado: ejecución autorizada por el usuario mediante
«go and complete everything». El estado de publicación descrito abajo
corresponde a la base inicial.
Lista operativa: [todo.md](todo.md). Estado vigente: 21 suites host, 47
parches y campaña natural R01–R04 completa; R05 parcial, T27 y Checkpoint E
abiertos. Véase [cobertura pendiente](t27-remaining.md).

## Objetivo

Consolidar el trabajo existente, resolver los fallos conocidos y completar
la compatibilidad necesaria para jugar Emerald en Windows i686 con
gráficos, audio, guardado y eventos de tiempo fiables. Después abordar
enlace y otras plataformas mediante diseños separados. «Completar» exige
evidencia por subsistema y por recorrido; no se asignará un porcentaje de
avance a partir del número de archivos que compilan.

## Base comprobada al iniciar el plan (histórica)

- Rama actual: `codex/milestone-20-wild-battle`, commit `1f83350`.
- `main` local: `07207e9`; es ancestro de la rama actual y está atrasado.
- Última rama publicada comprobada: `origin/milestone-19-readme`, `8940376`.
  El arreglo del combate del hito 20 permanece local.
- Upstream fijado: `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`.
- 16 parches; árbol upstream parcheado:
  `e990d9cea5ae60d66b293bff35b6c5f2725b5a49`.
- 13 suites host PASS; ejecutables normal/diagnóstico enlazan; GBA compare OK.
- Recorrido sintético: partida nueva → mapa → combate salvaje → victoria →
  regreso al mapa. El usuario también probó inicial y conversación con Birch.
- PPU 0–2, afines, ventanas/OBJWIN, mezcla, mosaico, DMA inmediato/HBlank/
  VBlank, timers, flash a disco, audio PCM/PSG, velocidad y reset existen.

Estos datos describen el checkout local, no garantizan que `main` remoto
contenga todas esas funciones. T01 actualizará la información remota antes
de integrar. No sobrescribir el plan anterior no versionado de hitos 13–19.

## Inventario inicial y prioridad

| Área | Evidencia actual | Trabajo pendiente | Prioridad |
| --- | --- | --- | --- |
| Integración Git | Hitos encadenados; main atrasado | Revisión y consolidación de la cadena, incluido 0016 | P0 |
| Descompresión | Aviso `expected 0x10` durante combate | Encontrar fuente, consumidor y longitud; corregir causa | P0 |
| Callbacks | Fallos reales en naming/transición corregidos | Auditar otras liberaciones y bucles que requieren VBlank | P0 |
| Guardado | Sectores/flush y persistencia probados | Guardado real, reapertura, fallo de escritura y recuperación | P0 |
| MMIO/IRQ | Memoria mapeada; HBlank/VCount parciales | IE/IME/IF, efectos de escrituras, espera de máscaras | P1 |
| Timers | Conteo/prescaler/cascada | IRQ y escrituras repetidas del mismo valor | P1 |
| DMA | Solo canales armados por PortDma_Set | Escrituras directas, máscaras/IRQ, intervalos de VBlank | P1 |
| PPU | Modos 0–2 y efectos implementados | Modos 3–5 y comparación de prioridades, mosaico y bordes | P1 |
| BIOS | Cálculo/copia/descompresión propios | Exactitud numérica, reset por flags; IntrWait aún ignora argumentos | P1 |
| RTC | Se informa ausente | Reloj y eventos diarios con persistencia y pruebas | P1 |
| Audio | PCM/PSG y SDL; salida WAV medida | Fidelidad, bancos de onda, mezcla y calidad a 1×–4× | P1 |
| Cobertura del juego | Inicio y un combate sintético | Captura, entrenadores, menús, evolución y progresión | P1 |
| Entrada | Teclado fijo | Mandos/remapeo y persistencia de configuración | P2 |
| Enlace | RFU/serie/multiboot deshabilitados | Diseñar y probar dos instancias; separar protocolos | P3 |
| Portabilidad | Windows i686 con direcciones fijas | x86-64 y Linux/macOS requieren nuevos formatos/backend | P3 |
| Documentación | README actual; informes históricos | BIOS/ARM todavía describen audio silencioso/reset antiguo | P0 |

P0: fallos e integridad del trabajo/datos; P1: compatibilidad de juego;
P2: comodidad y mantenimiento; P3: proyectos de compatibilidad adicionales.
Los números de hito siguientes organizan trabajo nuevo; no sustituyen
los hitos generales de AGENTS.md.

## Decisiones de arquitectura

1. Mantener **i686/MINGW32** durante la estabilización. No mezclar una
   migración a x86-64 con arreglos del juego.
2. Código nuevo propio en `port/`. Fuentes upstream solo en la carpeta
   ignorada. Cada cambio upstream bajo `PORT_PC` y exportado con
   `git format-patch`; el siguiente número disponible hoy es `0017`.
3. Conservar memoria GBA mapeada, pero introducir acceso observable **solo
   donde el inventario demuestre que hace falta**: writes de timer, IF,
   DMA y bancos de onda. Un sondeo de RAM no detecta escrituras idénticas.
4. Diseñar un despacho cooperativo de eventos por línea, con orden definido,
   sin invocar callbacks de juego de forma concurrente desde el hilo SDL.
   No se promete precisión de instrucciones ARM para código nativo x86.
5. Corregir la causa de cada fallo; no silenciar avisos de descompresión ni
   introducir retornos globales que salten lógica del juego.
6. Conservar los formatos originales de datos y save mientras se use i686.
   La migración a 64 bits separará direcciones GBA `u32` de punteros host.
7. RTC basado por defecto en tiempo civil del host, independiente de 2×–4×;
   un reloj inyectable permitirá pruebas deterministas. Cualquier desfase
   configurado se guardará dentro de `saves/`, no en la ROM.
8. Las comparaciones de imagen/audio se almacenan **solo en build/**. No
   publicar capturas, muestras, fixtures de ROM/save ni ejecutables que
   incorporen código o recursos del juego.

## Fases y dependencias

| Hito nuevo | Tareas | Entrega y dependencia |
| --- | --- | --- |
| 21: base integrada | T01–T02 | Revisión del historial → main consistente |
| 22: diagnóstico y datos | T03–T05 | Logs útiles → descompresión → vida útil de callbacks |
| 23: save/reset | T06–T07 | Base de juego estable → pruebas reales y fallos controlados |
| 24: registros/IRQ | T08–T12 | Inventario MMIO → IRQ → esperas, líneas y timers |
| 25: DMA | T13 | Eventos de T09/T11 → controles y escrituras observables |
| 26: gráficos | T14–T17 | Líneas/MMIO → bitmap → prioridades y mosaico |
| 27: BIOS | T18–T19 | IRQ y memoria → cálculo/reset compatible |
| 28: RTC | T20 | Save fiable y acceso host controlado |
| 29: audio | T21–T23 | Writes observables → PCM/PSG → salida y escucha |
| 30: juego | T24–T27 | Compatibilidad anterior → ampliar recorridos verificables |
| 31: uso local | T28–T29 | Entrada configurable y arranque reproducible |
| 32: enlace | T30–T33 | Diseño → trade → batalla → RFU/multiboot |
| 33: x86-64 | T34–T36 | Inventario de formatos → piloto → migración por lotes |
| 34: otros sistemas | T37 | Abstracciones estabilizadas → Linux/macOS por separado |
| 35: cierre | T38 | Matriz de soporte, límites y verificación final |

T30–T37 se descomponen aquí en investigación/piloto y lotes limitados,
porque afirmar que «todo enlace» o «todo x86-64» cabe en una sesión sería
irreal. Su inventario debe generar tareas hijas con archivos concretos antes
de implementar cada lote. No se darán por completados con un stub nuevo.

## Verificación común y reglas de integración

Para cada cambio de código, usar MINGW32 desde la raíz:

```sh
make -C port exe
make -C port test
make -C port diagnostic-exe
python port/tests/wild_battle_smoke.py
```

La regresión larga se ejecuta tras cambios que afecten frames, juego,
audio o datos; para ajustes aislados usar primero la suite focalizada.
`test` no necesita ROM para ejecutar sus fixtures sintéticos, aunque el
build de algunas suites requiere herramientas/recursos upstream locales.

Para cada parche upstream, usar MINGW64 con ARM Binutils 2.43.1:

```sh
PATH="$PWD/pokeemerald/.toolchains/arm-binutils-2.43.1/mingw64/bin:$PATH" \
make -C pokeemerald compare
```

Exigir `pokeemerald.gba: OK`, aplicación de los parches a checkout limpio
y árbol idéntico. Conservar el original de roms/ y comprobar su hash y el
del save del usuario; pruebas destructivas usan copias aisladas en build/.

- Una rama `codex/milestone-NN-*` por hito desde la base integrada.
- Explicar el incremento antes de editar; commit por arreglo/capacidad.
- Mostrar `git status` antes de cada commit; añadir nombres explícitos.
- Revisión de calidad antes de merge: correctness, límites, errores,
  formato de datos, efectos en GBA y pruebas necesarias.
- Antes de push mostrar `git ls-files` y revisar también los nombres del
  historial saliente. Publicar únicamente cuando se solicite en esa fase.
- Una regresión exige estado esperado, no solo `exit=0`: victoria/captura,
  mapa esperado, datos guardados y restaurados, timeout y ausencia de señales.
- Actualizar informes tras cada fallo con función, frame, dirección,
  causa, arreglo y evidencia; distinguir verificación automática de escucha
  o prueba humana pendiente.

## Criterio de cierre

La primera meta es **Windows i686 estable para juego individual**: la matriz
T24–T27 pasa, save/reset/RTC están probados, los avisos actuales tienen causa
y tratamiento, y gráficos/audio tienen referencias reproducibles. Esto no
equivale a probar todas las combinaciones de movimientos y eventos.

La meta ampliada incluye enlace y otros hosts solo cuando sus respectivos
pilotos y lotes pasen. Funciones que requieran ejecutar programas descargados
ARM (multiboot/ciertos accesorios) necesitan decidir un backend específico;
no se afirmará soporte nativo sin esa solución. La matriz final distinguirá
implementado, aproximado, deshabilitado y pendiente, con enlaces a evidencia.

## Riesgos y decisiones futuras

| Riesgo | Tratamiento |
| --- | --- |
| Escribir mismo valor en MMIO resulta invisible | Hooks pequeños en writes usados; tests que repiten valores |
| Cambiar orden IRQ rompe rutas que hoy funcionan | Orden especificado y prueba de juego antes/después |
| Fuente de aviso comprimido aún desconocida | Diagnosticar en T04 antes de cambiar gráficos o datos a ciegas |
| RNG/historia vuelven frágiles los guiones | Fixtures controlados, checkpoints semánticos y seeds registradas |
| Daño al save por tests o reset | Copias aisladas, checksums y simulación de fallos |
| Recursos del juego aparecen en respaldo | Solo texto propio/parches en Git; artefactos locales ignorados |
| Enlace o 64 bits crece demasiado | Diseño/piloto primero; lotes de hasta cinco archivos |
| Disponibilidad futura de MINGW32 | Registrar versiones/hashes y restauración local; mantener plan x64 separado |

No hay estimación de fechas sin medir los primeros incrementos. Los tamaños
de tarea indican superficie de cambio, no horas garantizadas. Mandos,
transporte de enlace, RTC configurable y otros sistemas se detallarán al
llegar a su hito; no bloquean corregir los fallos actuales.
