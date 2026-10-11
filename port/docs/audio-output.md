# T23 — salida SDL, pausa y velocidad

Fecha: 2026-10-11. Rama: codex/milestone-30-audio-output.

## Comportamiento implementado

- P pausa el juego y el dispositivo de audio; vacía la cola al abrir el menú.
  Los callbacks, PSG y nuevas muestras permanecen detenidos. Al cerrar el menú
  se reinicia la posición de remuestreo y se envía audio nuevo. Las teclas de
  navegación siguen suprimidas hasta soltarse. Cerrar la ventana en pausa termina.
- Si no hay dispositivo, el juego continúa en silencio y el PSG avanza con el
  tiempo emulado. Se reintenta abrir cada 120 frames de juego (~2 s a 1×,
  ~0,5 s a 4×). En pausa los reintentos quedan detenidos.
- SDL_AUDIO_STOPPED detecta una salida perdida; se cierra y reabre la salida
  predeterminada. Un fallo de QueueAudio cierra el dispositivo y espera 120 frames
  antes de reintentar. No hay bucle bloqueante ni spam de fallo por frame.
- Shutdown es idempotente y detiene envíos posteriores. Reset crea el proceso
  nuevo con velocidad 1× y un dispositivo/cola nuevos.
- Se mantiene audio con tono más alto a mayor velocidad: frecuencia efectiva
  de entrada pcmFreq × multiplicador. La cola tiene un máximo de 7.200 frames
  stereo (150 ms a 48 kHz). Un cambio de velocidad o exceso de cola la vacía.
- Diagnóstico registra pico de cola, descartes, errores y reconexiones. Los WAV,
  mediciones, ROM y saves de los fixtures viven únicamente bajo build/ ignorado.

## Pruebas

Backend falso: ausencia inicial y recuperación, desconexión, fallo de cola y
recuperación, exceso de cola, velocidades 1–4 (1.000 bloques cada una, error de
longitud ≤1 muestra), pausa idempotente sin PSG/envíos, cierre en pausa y shutdown
repetido. Frame falso: no callback durante menú, silencio, reanudación y cierre.

Dispositivo real: audio_output_smoke.py ejecutó 16 procesos aislados con el
SDL_AUDIODRIVER predeterminado, sin dummy audio. Device ID 2, sin errores ni
reconexiones en estos recorridos. Callbacks visuales se sustituyen en GDB por
DummyFunc para aislar m4a; las secuencias son título 413, selección de menú 5,
combate salvaje 474 y grito Torchic 280. No es una prueba de campaña completa.
Cada captura contiene 241 bloques de 224 muestras a 13.379 Hz, PCM16 stereo 48k.
La duración medida es 4,035 / 2,0175 / 1,345 / 1,00875 s para 1× / 2× / 3× / 4×.

| Escena/velocidad | Pico | Saturadas | Cola máxima (frames) | Delta máx. adyacente / borde de bloque |
| --- | ---: | ---: | ---: | ---: |
| title-1x | 18942 | 0 | 2204 | 7764 / 7764 |
| title-2x | 18942 | 0 | 1763 | 8329 / 8329 |
| title-3x | 18800 | 0 | 1672 | 9721 / 9721 |
| title-4x | 18659 | 0 | 1608 | 11133 / 11133 |
| menu-1x | 2304 | 0 | 2203 | 3584 / 3584 |
| menu-2x | 2304 | 0 | 1802 | 3584 / 3584 |
| menu-3x | 2304 | 0 | 1607 | 3853 / 3584 |
| menu-4x | 2304 | 0 | 1607 | 4608 / 3584 |
| battle-1x | 15355 | 0 | 2230 | 6294 / 6294 |
| battle-2x | 15355 | 0 | 1802 | 6993 / 6319 |
| battle-3x | 15220 | 0 | 1607 | 9029 / 7220 |
| battle-4x | 15355 | 0 | 1608 | 11744 / 8148 |
| torchic-1x | 9978 | 0 | 2204 | 3907 / 3907 |
| torchic-2x | 9905 | 0 | 1802 | 3943 / 3943 |
| torchic-3x | 9730 | 0 | 1672 | 4547 / 3979 |
| torchic-4x | 9730 | 0 | 1607 | 5423 / 3943 |

Todas las capturas: cero descartes de cola y errores; pico global de cola 2.230
frames = 46,46 ms. RMS y medidas completas en
build/audio-output-regression/measurements.json; no se versionan los WAV.
Delta mide diferencia absoluta entre muestras PCM16 vecinas; bordes calculados
por ceil(n × 224 × 48000 / (13379 × velocidad)). Los ataques/transiciones propios
de las ondas también producen deltas: no se interpreta un delta como click ni
RMS como fidelidad. El remuestreador limita el último vecino al bloque actual;
no implementa interpolación con lookahead entre bloques ni fundido al cambiar
velocidad/pausa. Estas discontinuidades se cuantifican, no se promete ausencia
universal de clicks ni equivalencia a audio de hardware.

Escucha: en T21 el usuario confirmó título, selección y grito reconocibles.
En T23 escuchó combate 1× y título 4× y respondió **«Sí, se oyen bien»**, sin
ruido/cortes molestos en esas muestras. No se extiende esa aprobación a todas
las canciones ni a todos los dispositivos.

## Gates y reproducción

- Builds normal/diagnóstico y 19 suites: PASS, t23-final-build.log y t23-suites.log.
- Checkout limpio existente con 31 parches, actualizado con código propio T23:
  ambos ejecutables y 19 suites PASS, build/t23-clean-build.log.
- GBA: pokeemerald.gba: OK, build/t23-gba.log; upstream tracked intacto.
- Reset real teclado/juego y CreateProcess fallido: PASS, build/t23-reset-game.log.
- Salida SDL real a 1×–4×: PASS, build/t23-output.log.

Desde MINGW32, en la raíz:

```sh
make -j4 -C port exe
make -C port diagnostic-exe test
python port/tests/audio_output_smoke.py
python port/tests/reset_game_smoke.py # requiere fixture de save_game_smoke.py
```

Se probó reconexión/errores con backend falso, y salida/cierre con dispositivo
real; no se simuló una desconexión física del hardware de Windows. SDL puede
conservar un buffer ya entregado al sistema: ClearQueuedAudio no retira muestras
que el driver ya tiene. Durante juego pesado aún puede haber underrun o descarte
por exceso de cola. No se mide precisión de callbacks del driver por ciclo.
T23 cierra su contrato de backend/mediciones/escucha; T24 y campaña siguen pendientes.
