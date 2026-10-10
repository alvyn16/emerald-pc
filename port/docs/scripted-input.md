# Entrada reproducible para diagnóstico

Solo `make -C port diagnostic-exe` habilita el guion. El ejecutable normal
`build/emerald-pc.exe` no incluye este código. La ROM y el guion local pueden
estar en `roms/` y `build/`, respectivamente; ambas rutas están ignoradas.

La ventana de diagnóstico se identifica como **DIAGNOSTIC - TEST ONLY** y
usa `saves/emerald-pc-diagnostic.sav`. El juego normal usa
`saves/emerald-pc.sav`. Las regresiones GDB trabajan en subcarpetas propias
de `build/` y usan los drivers SDL dummy, sin abrir una ventana de juego.
No ejecutes guiones GDB de prueba sobre una partida normal.

Defina `EMERALD_PC_INPUT_SCRIPT` con una ruta a un archivo de texto. Cada línea
tiene `primer_frame ultimo_frame botones`. Los límites son inclusivos, empiezan
en 1 y deben estar ordenados sin solapamiento. Separe botones simultáneos con
`+`: `A+START`, `RIGHT`, `DOWN`, `NONE`. Se admiten A, B, SELECT, START,
RIGHT, LEFT, UP, DOWN, R y L. Una línea que empieza por `#` es comentario.
Cuando hay guion, los frames no enumerados no pulsan ningún botón y el guion
sustituye el teclado. Sin guion, el teclado sigue funcionando.

```
# Salta la intro y camina hacia la salida del camión
1000 1001 A
1045 1046 A
12001 12120 RIGHT
12121 12280 DOWN
```

Desde el shell MINGW32 de MSYS2:

```sh
make -C port diagnostic-exe
export EMERALD_PC_INPUT_SCRIPT=build/prueba.inputs
export EMERALD_PC_FAST=1
export EMERALD_PC_STOP_FRAME=14000
build/emerald-pc-diagnostic.exe
```

`EMERALD_PC_FAST=1` omite la espera del temporizador para diagnósticos; el
orden de frames y las llamadas VBlank permanecen. `EMERALD_PC_STOP_FRAME`
cierra el proceso limpiamente tras el frame indicado. Para inspeccionar un
fallo, ejecute el mismo programa y entorno bajo GDB de MINGW32.

Cada 600 frames, el diagnóstico escribe en stderr el frame, mapa, callbacks,
flags/resultado de batalla e IE/IME/DISPSTAT. Se vacía el buffer después de
cada línea para conservar el último estado si el proceso se bloquea. No
incluye contenido de ROM, recursos ni save. Es un registro periódico de
frames completados; no es un watchdog ni una traza por instrucción.

Para repetir el recorrido completo hasta Villa Raíz después de ajustar el
reloj, genere el guion sin guardar datos del juego en Git:

```sh
python port/tests/gameplay_smoke.py build/gameplay-smoke.inputs
export EMERALD_PC_INPUT_SCRIPT=build/gameplay-smoke.inputs
export EMERALD_PC_FAST=1
export EMERALD_PC_STOP_FRAME=30500
build/emerald-pc-diagnostic.exe
```
