# Revisión y resultados de los hitos 13–19

Fecha: 2026-10-10. Plataforma: MSYS2 MINGW32, GCC i686 16.2.0.
Las ramas se encadenan desde `milestone-13-test-target` hasta
`milestone-19-readme`. No se hizo push.

## Revisión del plan antes de implementarlo

La secuencia es adecuada: pruebas → temporizadores/reinicio → líneas y DMA
→ efectos gráficos → sonido → documentación. Se mantuvieron los límites
de `PORT_PC` y los parches, sin incorporar recursos al repositorio.
Se corrigieron estos detalles durante la implementación:

- El temporizador normal escala los ciclos por la velocidad elegida; la
  primera llamada y el tiempo máximo admitido usan también el multiplicador.
  El diagnóstico conserva 280.896 ciclos por frame.
- El ejemplo musical `N24, W24, FINE` termina en el tick 25 a tempo 75;
  nota y espera avanzan conjuntamente, no suman 48 ticks. `TrackStop`
  detiene inmediatamente; la envolvente de liberación se prueba por separado.
- La tabla m4a necesita un callback C para borrar 64 bytes con la firma
  host correcta; una rutina ARM con convención especial no puede sustituirse
  directamente por una función C de firma distinta.
- El backend usa remuestreo lineal propio, alternativa del plan detallado,
  en lugar de `SDL_AudioStream`. Reinicia la fase al cambiar la velocidad;
  la cola se limita a 150 ms. Ambas decisiones tienen pruebas con backend falso.
- Los objetos del enlace se enumeran explícitamente: un `.o` antiguo de
  audio silencioso no puede reaparecer por un `find` del directorio de build.
- El plan proponía un archivo común de stubs; se conservaron stubs locales
  de cada suite para que sus dependencias sean visibles.

## Resultados medidos

| Hito | Resultado |
| --- | --- |
| 13 | Objetivo `make -C port test`, fuentes explícitas, fallo del objetivo si falla cualquier suite. |
| 14 | Temporizadores con prescaler, recarga, cascada y desbordamiento; regresión adicional con `UINT32_MAX` ciclos. |
| 15 | Relanzamiento con ruta y línea de comandos Unicode; prueba que el save se cierra antes de crear el proceso. |
| 16 | Render por línea; DMA HBlank/VBlank, repetición y recarga; IRQ HBlank y VCount condicionadas por los registros. |
| 17 | OBJWIN y mosaico en texto, afines y sprites; máscaras y tamaños 1×1/4×4 probados. |
| 18 | m4a upstream + motor C propio PCM/PSG + salida SDL; WAV del recorrido completo y RMS del título distinto de cero. |
| 19 | README, controles, entorno, pruebas y límites actualizados. |

Son **13 suites host aprobadas**, compiladas con `-Wall -Wextra -Werror`.
Los ejecutables normal y de diagnóstico enlazan. El build GBA de referencia
verificó **`pokeemerald.gba: OK`** con ARM Binutils 2.43.1.

### Rendimiento del render por líneas

Comparación secuencial en esta máquina, mismo guion de 614 rangos,
30.500 frames y `EMERALD_PC_FAST=1`:

| Fuentes host | Tiempo | Salida |
| --- | ---: | ---: |
| Hito 15, `f8bdb60` | 60,087 s | 0 |
| Hito 16, `7db0873` | 70,477 s | 0 |

Relación: **1,173×**, menor que el límite 1,5× del plan. Se exportaron las
fuentes host históricas a `build/perf15` y `build/perf16`, se enlazaron con
los mismos objetos del juego/datos (omitiendo el nuevo `m4a.o`) y su audio
silencioso histórico. Es una comparación del cambio host, no dos builds
históricos completos independientes. Una medición por versión, sin GDB;
no es una garantía de rendimiento en otros equipos.

### Capturas revisadas

GDB detuvo cada proceso al salir por su límite de frames y volcó el buffer
ARGB a archivos de `build/`, convertidos localmente a PNG:

- `perf15-intro-2400.png` y `perf16-intro-2400.png`: **0 píxeles distintos**.
  Ambos están en el destello blanco de la intro con audio silencioso; esto
  valida ese frame, no toda la escena.
- `hito18-intro-2400.png`: acantilado con bandas negras de la intro.
  El secuenciador real cambia su temporización respecto al audio silencioso;
  no se exige equivalencia de escena al mismo número de frame entre ellos.
- `hito18-title-1100.png`: logotipo completo, Rayquaza de fondo y texto del
  título, sin recorte visible.
- `hito18-world-30500.png`: protagonista fuera de su casa en Villa Raíz;
  casas, árboles y NPC visibles. El proceso salió normalmente en GDB.

Los archivos son evidencias locales ignoradas por Git; no se distribuyen.

El recorrido final con audio tardó **78,606 s**, terminó con código 0 y
produjo `build/hito18-audio.wav`: estéreo S16, 48.000 Hz,
24.511.249 frames de audio (510,651 s). Fragmento del título correspondiente
a frames 1.000–1.100: RMS **2.374,8695** (normalizado **0,0724753**), pico
**18.915**, **0** muestras saturadas de 160.730. Esto prueba salida no vacía
y ausencia de clipping en ese fragmento; no prueba fidelidad al hardware.

### Parches reproducibles

Se creó un checkout limpio de la base
`731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` dentro de `build/`, se aplicaron
`0001`–`0015` con `setup.ps1` y se repitió el script sin aplicar duplicados.
Su árbol y el del checkout de trabajo coinciden:
`0e1297df733a73e688c8bd6448982e8f479d4dec`.
El checkout temporal se retiró tras verificarlo. El único parche nuevo es
`0015-Run-m4a-sound-driver-on-host.patch`, con guardas `PORT_PC` en `m4a.c`.

## Límites que siguen abiertos

- El recorrido de 30.500 frames cubre intro, título y comienzo de partida;
  no certifica todos los mapas, combates, menús o créditos.
- No hay precisión por ciclo, HBlank durante VBlank ni IRQ de timers/serie.
  Escribir de nuevo el mismo valor en un registro mapeado puede ser invisible
  al sondeo; los timers documentan esta limitación.
- El mosaico de objetos es aproximado. Faltan modos bitmap 3–5 y RTC real.
  Enlace/RFU/multiboot permanecen deshabilitados.
- PSG guarda el banco de onda observado una vez por frame; no intercepta
  varias escrituras de banco realizadas entre dos llamadas. El uso actual
  m4a de ondas de 32 muestras funciona con ese modelo; el banco doble no
  está certificado con todos los patrones de escritura del hardware.
- El sonido usa remuestreo lineal y síntesis aproximada. La escucha del
  título, efectos de menú y gritos de Pokémon por el usuario sigue pendiente.
- El relanzamiento de reset tiene pruebas con spawner sustituido; la
  combinación de teclas y relanzamiento real requieren comprobación manual.

La implementación del plan está realizada; las comprobaciones humanas
indicadas arriba quedan identificadas como pendientes, sin darlas por hechas.
