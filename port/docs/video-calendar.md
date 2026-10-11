# Calendario de vídeo y timers (T11–T12)

El servicio cooperativo comienza en 160, recorre 160–227 y después 0–159.
La siguiente llamada vuelve a 160. Solo se renderizan 0–159; al retornar se
publica línea 0 para los consumidores nativos fuera del servicio. Esto no
simula el tiempo que consume cada instrucción del juego entre llamadas.

En 160: estado de línea, DMA VBlank, solicitudes VBlank/VCount y despacho
según el orden de Emerald; después audio. En 0 comienza la referencia afín.
Cada línea: VCount, render si es visible, avance timer de la fase de dibujo,
HBlank, DMA si visible, solicitudes y despacho, avance timer de HBlank y
despacho. DISPSTAT mantiene VBlank en 160–226, no en 227. HBlank se publica
en todas las líneas. Una fuente IRQ enmascarada permanece pendiente.

Referencias: [GBATEK, estado LCD y timers](https://rust-console.github.io/gbatek-gbaonly/)
y [implementación de eventos de mGBA](https://github.com/mgba-emu/mgba/blob/master/src/gba/video.c).
GBATEK contiene una nota contradictoria sobre IRQ HBlank durante VBlank;
se sigue su tabla de DISPSTAT y el despacho de mGBA: IRQ en las 228 líneas,
DMA HBlank en las 160 visibles. No se afirma una medición en hardware físico.

Las fases son 1006 y 226 ciclos, total 1232 por línea y 280896 por frame
diagnóstico. Los timers se despachan en esos límites, no en cada overflow
individual ni en cada instrucción ARM. Varias solicitudes de la misma fuente
se agrupan en IF. En el exe normal se conserva la variación acotada del reloj
host usada por el RNG, distribuida sin pérdida entre las fases. A 4x el tiempo
emulado por frame sigue siendo un frame GBA, mientras se reduce la espera SDL.

`frame_test` verifica el orden completo, 228 IRQ HBlank, 160 render/DMA,
DMA antes de callback VBlank, VCount visible/227 y cadencia de 1000 frames
a 1x/4x. SDL y PPU son fixtures. Medición local de 1000 frames: base e1ff772
6,781 ms; calendario/fases nuevas 23,534 ms (~16,8 microsegundos extra/frame).
La comparación usa el mismo timer host nuevo en ambos binarios. No mide PPU,
audio ni FPS de una escena real. Artefacto base local: `build/calendar-baseline/`.

`timer_test` verifica recarga sin cambiar contador, write igual al contador,
enable/disable, prescalers, cascada, overflow múltiple y solicitudes IRQ.
Write16 observa cada write; Write32 escribe recarga y luego control. El
sondeo de writes distintos se mantiene como compatibilidad de fixtures, no
como sustituto de los hooks en los consumidores inventariados del juego.

Los parches 0025–0027 observan writes de arranque, m4a, flash, link,
e-Reader y RFU, incluidas variantes indirectas de 16/32 bits. Esto no
habilita transporte link/RFU ni sus busy loops dependientes de hardware.

Revisión de control: cambiar de divisor 64 a 1 tras 63 ciclos no convierte
el resto viejo en 63 ticks nuevos. Los prescalers se alinean al contador
común de ciclos del dispositivo, incluido enable/control entre fases.
`build/t12-control-before.log` reproduce el fallo; `timer_test` verifica
la corrección y cambio posterior a divisor 256. Se contrastó con el
[recalendario de timers de mGBA](https://github.com/mgba-emu/mgba/blob/master/src/gba/timer.c).
No se simula el retraso de enable de instrucciones ARM ni fases sublínea
entre dos instrucciones del juego nativo.
