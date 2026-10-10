# Reset host — T07

El ejecutable normal usa CreateProcessW para relanzar su propia ruta y
línea de comandos. PortReset_Restart cierra la flash antes de crearlo;
el padre termina y su handler atexit libera audio, renderer, ventana,
SDL y memoria GBA. Ese handler también se ejecuta si falla el relanzamiento
o AgbMain retorna. El diagnóstico termina su prueba en SoftReset y no
crea otro proceso.

## Fallo corregido

A+B+Start+Select provocaba SIGSEGV en AgbRFU_SoftReset, antes de DoSoftReset:
AgbMain → rfu_REQ_stopMode → AgbRFU_SoftReset. La instrucción leía
`gSTWIStatus->timerSelect` con estado RFU NULL (EAX=0). InitRFU no inicializa
el adaptador en el host. El parche 0022 omite únicamente las dos llamadas
de apagado RFU en esa ruta bajo PORT_PC. GBA conserva ambas llamadas.
Log/backtrace: `build/save reset regression/keyboard-before.log`.

## Prueba reproducible

Desde MINGW32 con GDB, PowerShell y Python, tras preparar los slots de T06:

```sh
make -C port exe diagnostic-exe
python port/tests/save_game_smoke.py
python port/tests/reset_game_smoke.py
```

La segunda prueba ejecuta el **binario normal**, en una ruta con espacios
(`build/save reset regression/build/`) y cwd en `outside cwd/`. Drivers SDL
dummy evitan ventanas/audio visibles. GDB modifica solo memoria del proceso:
pone 4× y solicita la combinación mediante REG_KEYINPUT, o entra en
DoSoftReset. No cambia el archivo ejecutable ni incorpora entrada de prueba
al juego normal. La ruta de función es un fixture, no un evento narrativo.

Ambos casos PASS: padre sale limpio, exactamente un reemplazo con ese
parent PID; otro GDB se adjunta al hijo, espera LoadGameSave si hace falta,
comprueba velocidad 1×, contador 2, Torchic y dinero 23.456, y lo cierra.
No sobrevive ningún proceso de la ruta aislada y el save permanece idéntico.
La consulta de procesos y limpieza se restringen a esa ruta exacta, que se
comprueba sin procesos antes de comenzar.

El caso de fallo cambia solo el argumento de SpawnProcess en GDB hacia una
ruta inexistente. CreateProcessW real devuelve **Windows error 2**;
SoftReset informa el fallo, ShutdownHost se alcanza por atexit, el proceso
sale con código 1 y no crea reemplazo. Save intacto. La suite reset también
comprueba que el archivo se puede abrir exclusivamente al invocar el spawner,
confirmando que el mapeo ya se cerró.

Logs: `keyboard-parent/child.log`, `game-parent/child.log`, `spawn-failure.log`
en `build/save reset regression/`. GBA compare OK en
`build/reset-gba-compare.log`; 13 suites host PASS. Checkout de reproducción
con los 22 parches y main host actualizado recompilado/enlazado, árbol:
`b55fa9c92f3f8e4b8ec83911bef75951698612cb`.

Límites: reinicio después de guardados completos y recuperación de escritura
interrumpida se prueban por separado. No se inyecta reset durante cada byte
de una escritura ni se simula un corte eléctrico. El cierre por terminación
forzada no ejecuta handlers atexit.
